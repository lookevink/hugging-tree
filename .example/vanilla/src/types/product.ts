/**
 * Product domain types and interfaces
 */

import { User } from "./user";

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  category: ProductCategory;
  inStock: boolean;
  stockCount: number;
  createdBy: string; // User ID
  createdAt: Date;
  updatedAt: Date;
}

export enum ProductCategory {
  ELECTRONICS = "electronics",
  CLOTHING = "clothing",
  FOOD = "food",
  BOOKS = "books",
}

export interface CreateProductInput {
  name: string;
  description: string;
  price: number;
  category: ProductCategory;
  stockCount: number;
  createdBy: string;
}

export interface UpdateProductInput {
  name?: string;
  description?: string;
  price?: number;
  category?: ProductCategory;
  stockCount?: number;
}

export interface ProductWithCreator extends Product {
  creator: User;
}

