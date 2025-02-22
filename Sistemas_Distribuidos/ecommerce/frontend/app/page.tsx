"use client";

import React, { useState, useEffect } from 'react';

// === STRIPE ===
import { loadStripe } from '@stripe/stripe-js';

import { Elements, CardElement, 
		 useStripe, useElements } from '@stripe/react-stripe-js'
// === || ===

// === CSS ===
import MaxWidthWrapper from "@/components/common/MaxWidthWrapper";

import { Button } from "@/components/ui/button";

import { Card } from "@/components/ui/card"

import { Sheet, SheetContent, 
		 SheetHeader, SheetTitle, 
		 SheetTrigger } from "@/components/ui/sheet"

import { Table, TableBody, 
		 TableCell, TableHead, 
		 TableHeader, TableRow } from "@/components/ui/table"

import { createColumnHelper, flexRender, 
		 getCoreRowModel, useReactTable } from "@tanstack/react-table"

import { ArrowLeft, ArrowRight, 
		 List, ShoppingCart, 
		 SquarePlus, X } from "lucide-react"
// === || ===

import Request from "@/app/request"

// === GLOBALS ===
const host: string = "http://localhost:"

const mainPort: string = process.env.principalPORT!;
console.log("PRINCIPAL_PORT: ", mainPort);

const paymentPort: string = process.env.pagamentoPORT!;
console.log("PAYMENT_PORT: ", paymentPort)

const stripeAPIKey = process.env.STRIPE_API_KEY!;
const stripePromise = loadStripe(stripeAPIKey);
// === || ===

const PaymentSection = ({ total, setPaymentSucceeded, }: { 
						  total: number, 
			setPaymentSucceeded: (value: boolean) => void } ) => {

	const stripe = useStripe();
	const elements = useElements();
	const isStripeReady = stripe && elements;
	
	if (!isStripeReady) {
		return <div>Carregando pagamento...</div>;
	}

	const handlePayment = async (orderId: number) => {

		try {
			const valor = (total * 100).toFixed(2)
			console.log("VALOR: ", valor);

			const payload = {
				method: "POST",
				headers: { "Content-Type": "application/json", },
				body: JSON.stringify({ amount: valor })
			};

			const url = host + paymentPort + "/create-payment-intent";
			console.log("REQUESTING URL: ", url);

			const res = await fetch(url, payload);
			if (!res.ok) {
				alert("Error ao enviar pagamento")
				return }
			const response = await res.json();

			const secret: 
				string | undefined = response["client_secret"];

			//console.log("SECRET: ", secret)

			if(!secret) {
				alert("Dados invalidos, verifique novamente")
				return
			}

			const cardElement = elements.getElement(CardElement);
			const { error, paymentIntent } = 
				await stripe.confirmCardPayment(
					secret, { 
						payment_method: { 
							card: cardElement } } );
			
			if (error) {
				console.log('Falha no pagamento:', error);
				alert('Falha no pagamento: ' + error.message);
			} else if (paymentIntent?.status === 'succeeded') {
				alert('Pagamento confirmado!');

				//updateOrderStatus(orderId, "Pago");
				//closePaymentModal();
				setPaymentSucceeded(true)
			}
		} catch (error) {
			console.error('Erro:', error);
			alert('Ops, aconteceu um erro.');
		}
	};

	return (
		<div className="p-4 bg-white rounded-lg 
						shadow-lg w-full max-w-lg 
						mx-auto">
		<CardElement />
		<Button 
			onClick={handlePayment}
			disabled={!isStripeReady} 
			className="relative -bottom-4 h-24 
					   bg-green-800 text-xl w-full 
					   hover:bg-green-300">
		Pagar
		</Button>
		</div>
	)
}

export default function StripeWrap() {
	return (
		<Elements stripe={stripePromise}>
			<Home />
		</Elements>
	);
}

// Interface de produto
interface Product {
	id: number;
	nome: string;
	preco: number;
	estoque: number;
}

// O mesmo produto x quantidade
interface sameItem {
	produto: Product;
	quantidade: number;
	preco: number;
}

function Home() {

	const [data, setData] = useState<Product[]>([]);
	const [currentPage, setCurrentPage] = useState(1);
	const [totalPages, setTotalPages] = useState(111);

	//Request dos produtos
	useEffect(() => {
		const fetchData = async () => {
			const url = host + mainPort + "/produtos?skip=" + (currentPage-1)*12;
			try {
				const result = await Request(url);
				setData(result);
			} catch (err) {
				console.error("Falha na busca de produtos")
			}
		}
		fetchData();
	}, [currentPage])

	// Carrinho
	const [ isCartOpen, 
			setIsCartOpen ] = useState(false);

	const [ cartItems, 
			setCartItems ] = useState<sameItem[]>([]);

	// Totais	
	const [ quantidadeTotal, 
		    setQuantidadeTotal ] = useState<number>(0);

	const [ precoTotal, 
			setPrecoTotal ] = useState<number>(0);

	
	const addToCart = (product: Product, quantity: number) => {
		console.log("ADD: " + JSON.stringify(product, null, 4));

		const newItem: sameItem = {
			produto: product,
			quantidade: quantity,
			preco: product.preco * quantity,
		};

		const index = cartItems.findIndex( (item) => 
			item.produto.id === product.id );

		// Verifica se o produto ja esta no carrinho
		if (index !== -1) 
		{
			const newCartItems = [...cartItems];
			newCartItems[index] = {
				...newCartItems[index],
				quantidade: 
					newCartItems[index].quantidade + 
					quantity,
				preco: 
					newCartItems[index].preco + 
					product.preco * 
					quantity
			}

			setCartItems(newCartItems);

		} else { setCartItems( [ ...cartItems, 
							     newItem ] ) }

		setQuantidadeTotal( quantidadeTotal + 
							quantity )

		setPrecoTotal( parseFloat( 
			(precoTotal + product.preco * quantity).toFixed(2) ) )

		setData( (prevData) =>
				prevData.map( (item) => {
					if (item.id === product.id) {
						return { ...item, 
								 estoque: 
									 item.estoque - quantity } }
					return item } ) )

	   console.log( "CART: " +
					JSON.stringify(cartItems, null, 4) )
	   console.log( "TOTALS: " + quantidadeTotal + 
					" " + precoTotal )
	}

	const removeFromCart = (product: Product) => 
	{
		console.log( "DEL: " + 
					 JSON.stringify(product, null, 4) )

		const index = cartItems.findIndex( (item) => 
			item.produto.id === product.id )

		if (index !== -1) 
		{
			setCartItems(cartItems.filter( (item) => 
				item.produto.id !== product.id) )

			const removedItem = cartItems[index]

			setQuantidadeTotal(
				quantidadeTotal - removedItem.quantidade )

			setPrecoTotal( parseFloat(
				(precoTotal - removedItem.preco).toFixed(2) ) )

			setData( (prevData) =>
				prevData.map( (item) => {
					if (item.id === product.id) {
						return { ...item, 
								 estoque: 
									 item.estoque + 
									 removedItem.quantidade } }
						return item } ) )
		}
	}

	const cleanCart = () =>
	{
		setCartItems([])
		setIsCartOpen(false)
		setQuantidadeTotal(0)
		setPrecoTotal(0)
	}

	// Pedidos salvos
	const [ isOrderSidebarOpen, 
		 	setIsOrderSidebarOpen ] = useState(false)

	const [ expandedOrderId, 
			setExpandedOrderId ] = useState<number | null>(null)

	const [ orderCreated, 
			setOrderCreated ] = useState(false);

	const [ orders, 
			setOrders ] = useState<{ id: number; 
				   					 items: sameItem[]; 
				   					 total: number; 
				   					 status: string }[]>([]);

	const createOrder = async () => {

		if (cartItems.length === 0) {
			alert("Seu carrinho está vazio!");
			return }

		setOrderCreated(true)
		setTimeout(() => { setOrderCreated(false) }, 333)

		setCurrentOrderId(orders.length+1)

		const newOrder = 
		{
			id: orders.length + 1,
			items: cartItems,
			quantidade: quantidadeTotal,
			total: precoTotal,
			status: "Criado"
		}
		
		console.log("ORDER: " + JSON.stringify(newOrder))

		try 
		{
			const req = host + mainPort + "/pedido"
			const opts = { method: "POST", 
						   headers: { 
						       "Content-Type": 
								   "application/json", },
                           body: JSON.stringify(newOrder) }

			const response = await fetch(req, opts)

			if (!response.ok) {
				throw new Error("Falha ao criar pedido!") }

			const result = await response.json();
			console.log("Pedido criado:", result);

			setOrders((prevOrders) => [...prevOrders, newOrder])

		} catch (error) {
			console.error("Erro na criacao do pedido:", error) }
	}


	const deleteOrder = async ( orderID: number, 
							    orderITEMS: List<sameItem> ) => 
	{
		const confirm = window.confirm( "Tem certeza " +
									    "que deseja excluir " +
									    "este pedido?" )
		if (!confirm) return

		setTimeout(() => { setOrderCreated(false) }, 333)

		const delOrder = 
		{
			id: orderID,
			items: orderITEMS,
			quantidade: -1,
			total: -1,
			status: "Excluido"
		}
		
		try 
		{
			const req = host + mainPort + "/pedido"
			const opts = { method: "POST", 
						   headers: { 
						       "Content-Type": 
								   "application/json" },
						   body: JSON.stringify(delOrder), }

			const response = await fetch(req, opts)

			if (!response.ok) {
				throw new Error("Falha ao excluir pedido!") }

			const result = await response.json();
			console.log("Pedido excluido:", result);

			setOrders( (prevOrders) => 
				prevOrders.filter( (order) => 
					order.id !== orderID ) )

			alert("Pedido excluído!");

		} catch (error) {
			console.error("Erro ao excluir pedido: ", error)
			alert("Erro ao excluir pedido.") }
	}

	const [ currentOrderId, 
		    setCurrentOrderId ] = useState(-1)

	const updateOrderStatus = ( orderId: number, 
							    status: string ) => 
	{
		orders.map( (order) => 
		{
			const upOrder = {
				id: orderId,
				items: order.items,
				//quantidade: order.quantidade,
				total: order.total,
				status: status }

			setOrders( (prevOrders) => 
				prevOrders.filter( (order) => 
					order.id !== orderId ) )

			setOrders( (prevOrders) => 
				[...prevOrders, upOrder] )
		} )
	}

	//Pagamento
	const [ paymentSucceeded, 
			setPaymentSucceeded ] = useState(false);

	useEffect(() => 
	{
		if (paymentSucceeded !== undefined) {
			const newStatus = paymentSucceeded ? 
				"Pago" : "Falha no pagamento"

			updateOrderStatus(currentOrderId, newStatus)
		}
	}, [paymentSucceeded])


	const [ showPaymentModal, 
			setShowPaymentModal ] = useState(false)

	const openPaymentModal = () => 
	{
		setIsCartOpen(false)
		setIsOrderSidebarOpen(false)
		setShowPaymentModal(true)
	}

	const closePaymentModal = () => 
	{
		if (paymentSucceeded) 
		{
			setCartItems([])
			setQuantidadeTotal(0)
			setPrecoTotal(0)
			setCurrentOrderId(-1)
			setPaymentSucceeded(false)
		}

		setShowPaymentModal(false)
		setIsCartOpen(false)
	}

	// Tabela de produtos
	const columnHeaders: 
		Array<keyof Product> = [ "id", "nome", 
								 "preco", "estoque" ]

	const columnHelper = createColumnHelper<Product>()
	const columns = columnHeaders.map( (columnName) => 
	{
		return columnHelper.accessor(
			columnName, { id: columnName,
						  header: columnName, } )
	} )

	const table = useReactTable( { data, columns,
								   getCoreRowModel: 
								       getCoreRowModel(), } )

	return (
		<MaxWidthWrapper>
		<Elements stripe={stripePromise}>
		<section>
		<main className="flex-1 overflow-y-auto">
		<header className="bg-gray-300 shadow-lg p-4 sticky top-0 z-10">
		<div className="flex items-center justify-between">
		<div className="flex items-center space-x-4">
		<Sheet open={isCartOpen} onOpenChange={setIsCartOpen}>

		<SheetTrigger asChild>
			<Button variant="ghost" className="absolute right-4">
				<ShoppingCart className="h-5 w-5" />
				{cartItems.length > 0 && (
					<span className="absolute -top-1 -right-1 bg-red-500 
									 text-white text-xs rounded-full h-5 w-5 
									 flex items-center justify-center">
					{quantidadeTotal} </span>
				) }
			</Button>
		</SheetTrigger>

		<SheetContent>

		<SheetHeader>
			<SheetTitle>Carrinho</SheetTitle>
		</SheetHeader>

		<div className="relative flex justify-between items-center 
						px-4 py-2 border-b">
			<div className="items-center space-x-8"></div>
			<Button
			onClick={() => {
				createOrder()
				cleanCart() } }
			className="items-center flex right-8 top-0 h-8 right-8 
					   bg-white-300 text-black-800 text-xl 
					   hover:bg-yellow-400 hover:text-pink-800 
					   transistion-colors duration-300">
				<SquarePlus/>Salvar Pedido{cartItems.length > 0 && orderCreated}
			</Button>
		</div>

		<div className="mt-4 space-y-4">
			{cartItems.map((item) => (
				<div key={item.produto.id} className="flex items-center 
													  justify-between">
					<span>{item.produto.nome}</span>
					<span>${item.preco.toFixed(2)}</span>
					<span>{item.quantidade}</span>
					<Button variant="destructive" size="sm" 
					onClick={() => removeFromCart(item.produto)}>
						<X className="h-4 w-4" />
					</Button>
				</div>
			) ) }
		</div>

		<div className="mt-8">
			<Card className="flex items-center justify-center 
							 w-full h-12 bg-black text-white b4">
				Total: R${precoTotal}
			</Card>
		</div>

		<footer>
			<Button
			onClick={() => {
				createOrder() 
				openPaymentModal() } }
			className="relative -bottom-4 h-24 bg-green-800 text-xl 
					   w-full hover:bg-green-300 hover:text-green-800 
					   transition-colors duration-300">
				Pagamento
			</Button>
		</footer>

		</SheetContent>
		</Sheet>

		<div className="items-center space-x-8"></div>

		<Sheet open={isOrderSidebarOpen} onOpenChange={setIsOrderSidebarOpen}>
		<SheetTrigger asChild>
			<Button onClick={() => {
				setIsOrderSidebarOpen(true),
				setOrders((p) => p.filter((order) => order.id !== -1)) } }
			variant="ghost"
			className="relative border-b -left-1">
				<List className="w-4 h-4" />
			</Button>
		</SheetTrigger>

		<SheetContent side="left" className="w-80">

			<SheetHeader>
				<SheetTitle>Pedidos</SheetTitle>
			</SheetHeader>

			<div className="mt-4 space-y-4">
				{orders.length === 0 ? (
				<p>Nenhum pedido feito ainda!</p> ) : (
				orders.map((order) => (
				<div key={order.id} className="flex flex-col">

					<div className="flex items-center justify-between">
						<h3 className="font-semibold 
									   text-xl">
							Pedido #{order.id}</h3>
						<span className="font-bold 
										 text-gray-800"> 
							({order.status})</span>
						<Button onClick={() => 
								setExpandedOrderId(
									expandedOrderId === order.id ? 
									null : order.id ) }
								variant="ghost"
								className="font-bold text-xl 
								 		   text-green-800">
							{expandedOrderId === order.id ? "[-]" : "[+]"}
						</Button>
					</div>

					{expandedOrderId === order.id && (

						<div className="mt-2"> {
							order.items.map((item) => (
							<div key={item.produto.id} 
							className="flex items-center justify-between text-sm">
								<span>{item.produto.nome} [{item.quantidade}]</span>
								<span>R$ {item.preco.toFixed(2)} </span>
							</div>
							) ) }

							<div className="flex items-center justify-between">
								<span className="font-semibold text-xl">
									Total [{order.quantidade}] </span>
								<span className="mt-2 font-bold text-xl">
									R$ {order.total} </span>
							</div>

							<footer>
							<div className="flex items-center justify-between">
								<Button onClick={() => {
									openPaymentModal()
									setPrecoTotal(order.total),
									setCurrentOrderId(order.id)
								} }
								disabled={order.status !== "Criado"}
								className="relative bg-green-800 w-48
										   hover:bg-green-300 
										   hover:text-green-800 
										   transition-colors duration-300">
									Pagamento
								</Button>
								<Button
								onClick={() => deleteOrder(order.id, order.items)}
								disabled={order.status !== "Criado"}
								variant="destructive"
								className={`relative w-12 hover:bg-red-300 
										   hover:text-red-800 transition-colors 
										   duration-300 ${order.status === "Pago" ?
												"opacity-50 cursor-not-allowed": "" } ` }
								title="Excluir pedido">
									<X className="h-4 w-4" />
								</Button>
							</div>
							</footer>
						</div> ) }
				</div> ) ) ) }
			</div>
		</SheetContent>
		</Sheet>

		</div>
		</div>

		</header>
		</main>
		</section>

		{showPaymentModal && (
			<div className="fixed inset-0 bg-white-100 bg-opacity-50 
							z-50 flex justify-center items-center">
				<div className="bg-white p-6 rounded-lg shadow-lg 
								w-full max-w-lg">
					<Button onClick={closePaymentModal} 
						className="absolute top-2 right-2">
						<X className="h-5 w-5" />
					</Button>

					<h2 className="text-xl font-semibold mb-4">Pagamento</h2>
					<PaymentSection 
						total={precoTotal} 
						setPaymentSucceeded={setPaymentSucceeded} />
				</div>
			</div>
		) }

		<div className="mt-4 rounded-lg overflow-hidden border border-border">
		<Table className="border">
		<TableHeader>
		{table.getHeaderGroups().map((headerGroup) => (
			<TableRow key={headerGroup.id}>
			{headerGroup.headers.map((header) => (
				<TableHead key={header.id} className="bg-secondary border">
				<div>{header.isPlaceholder ?
					null :
					flexRender(header.column.columnDef.header, header.getContext())}</div>
				</TableHead>
			))}
			</TableRow>
		))}
		</TableHeader>

		<TableBody>
		{table.getRowModel().rows.map((row) => {
			const product = row.original;
			const isOutOfStock = product.estoque === 0;

			return (
				<TableRow
				key={row.id}
				className={`cursor-pointer hover:bg-border/25 
					${isOutOfStock ? "opacity-50 pointer-events-none" : ""}`}
				onClick={() => {
					if (!isOutOfStock) {
						addToCart(product, 1);
					}
				}}
				>
				{row.getVisibleCells().map((cell) => (
					<TableCell key={cell.id} className="border">
					{flexRender(cell.column.columnDef.cell, cell.getContext())}
					</TableCell>
				))}
				</TableRow>
			);
		})}
		</TableBody>
		</Table>
		</div>

		<div className="flex justify-center space-x-4 mt-4">

		<Button
			variant="ghost"
			disabled={currentPage === 1}
			onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
			className="flex items-center justify-center">
		<ArrowLeft className="w-4 h-4" />
		</Button>

		<span>[ {currentPage} ]</span>

		<Button
			variant="ghost"
			disabled={currentPage !== 1 && currentPage === totalPages}
			onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
			className="flex items-center justify-center">
		<ArrowRight className="w-4 h-4" />
		</Button>

		</div>

		</Elements>
		</MaxWidthWrapper>
	);
}
