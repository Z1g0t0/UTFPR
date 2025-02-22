"use client";

import React, { createContext, useContext, useState } from "react"

//import { ItemInterface } from "@/interfaces/item-interface"
//
//interface CartItemProps {
//  id: string,
//  imageUrl: string,
//  title: string,
//  price: number,
//  quantity: number,
//}
//
//interface CartContextProps {
//  items: CartItemProps[],
//  addCartItem: (id: ItemInterface) => void
//  removeCartItem: (id: string) => void
//  updateCartItem: (id: string, quantity: number) => void
//  clearCartItem: () => void
//  getTotalPrice: () => void
//}

export const CartContext = createContext()
//export const CartContext = <CartContextProps | undefined>(undefined)

export const CartProvider = ({ children }) => {

    const [cartItems, setCartItems] = useState([])

    const addToCart = () => {}
    const removeFromCart = () => {}
    const clearCart = () => {}
    const getCartTotal = () => {}

    return(
        <CartContext.Provider value={{ addToCart, removeFromCart, clearCart, getCartTotal }}>
        {children}
        </CartContext.Provider> )
}
