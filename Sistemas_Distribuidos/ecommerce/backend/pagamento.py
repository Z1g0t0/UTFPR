from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pika
import stripe

from dotenv import dotenv_values

# RabbitMQ 
params = pika.ConnectionParameters('localhost', heartbeat=720)
connection = pika.BlockingConnection(params)
channel = connection.channel()

env_vars = dotenv_values("../.env")
stripe.api_key = env_vars.get("STRIPE_SECRET_KEY")
webhook_secret = env_vars.get("STRIPE_WEBHOOK_SECRET")

# FastAPI e Stripe
app = FastAPI()
origins = [ "http://localhost", "http://127.0.0.1", ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"{origin}:{port}" 
                   for origin in origins 
                   for port in range(3000, 3333)],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PaymentIntentRequest(BaseModel):
    amount: int  # Total em centavos

@app.post("/create-payment-intent")
async def create_payment_intent(request: PaymentIntentRequest):

    print(f"[MS]Pagamento -> Pagamento Solicitado: {request}")
    
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=request.amount,  
            currency="brl",  
            automatic_payment_methods={"enabled": True}, )

        return {"client_secret": payment_intent.client_secret}

    except Exception as e:
        print("ERROR: " + str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):

    #print(f"STRIPE_SECRET_KEY: {stripe.api_key} | WEBHOOK_SECRET: {webhook_secret}")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    intent = event.data.object
    print(f"[MS]PAGAMENTO -> {intent.id}: {intent.status}")

    if event.type == "payment_intent.succeeded":
        
        message = {
            "id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": "Aprovado",
        }

        channel.basic_publish( exchange = 'Pagamentos_Aprovados', 
            routing_key = f'Pagamento.{intent.id}.Aprovado',
                               body = str(message) )

    elif event.type == "payment_intent.payment_failed":

        message = {
            "id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": "Recusado",
        }

        channel.basic_publish( exchange = 'Pagamentos_Recusados', 
            routing_key = f'Pagamento.{intent.id}.Recusado',
                               body = str(message) )

    else:
        print("Unhandled event type:", event.type)

    return {"status": "success"}

def consume():
    pass

if __name__ == "__main__":

    print("[MS]PAGAMENTO -> Inicializado.")
    channel.start_consuming()

