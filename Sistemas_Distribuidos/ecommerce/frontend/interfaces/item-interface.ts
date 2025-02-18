export interface ItemInterface {
  id: string
  title: string
  imageUrl: string
  description: string
  rating: 0 | 1 | 2 | 3 | 4 | 5
  price: number
  bestSelection: boolean
  available: boolean
}
