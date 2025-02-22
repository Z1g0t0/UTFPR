"use client"

import { useState, useEffect } from "react"

const host: string = "http://localhost:"
const notifyPort: string = process.env.NEXT_PUBLIC_notificacaoPORT!;
console.log("notificacaoPORT: ", notifyPort);

export default function Notification() {

    const [messages, setMessages] = useState([])

    useEffect(() => {
        const sse = 
			new EventSource(
				host + notifyPort + "/stream", { 
					withCredentials: true, } )

        sse.onmessage = (event) => {
            //console.log(JSON.stringify(event.data))
            const data = JSON.parse(event.data.replace("Event: ", ""))

            setMessages((prev) => [...prev, data]) } 
			
			return () => { sse.close() } }, [] )

    return (
        <pre>{JSON.stringify(messages, null, 2)}</pre>
    ) 
}
