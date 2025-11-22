/**
 * Product service - handles business logic for product operations
 */

import {
  Product,
  CreateProductInput,
  UpdateProductInput,
  ProductCategory,
} from "../types/product";
import { generateId } from "../utils/idGenerator";
import { userService } from "./userService";

/**
 * In-memory product store (in a real app, this would be a database)
 */
const products: Map<string, Product> = new Map();

export class ProductService {
  /**
   * Creates a new product
   */
  async createProduct(input: CreateProductInput): Promise<Product> {
    // Verify the creator exists
    const creator = await userService.getUserById(input.createdBy);
    if (!creator) {
      throw new Error("Creator user not found");
    }

    const now = new Date();
    const product: Product = {
      id: generateId(),
      name: input.name,
      description: input.description,
      price: input.price,
      category: input.category,
      inStock: input.stockCount > 0,
      stockCount: input.stockCount,
      createdBy: input.createdBy,
      createdAt: now,
      updatedAt: now,
    };

    products.set(product.id, product);
    return product;
  }

  /**
   * Retrieves a product by ID
   */
  async getProductById(id: string): Promise<Product | null> {
    return products.get(id) || null;
  }

  /**
   * Updates an existing product
   */
  async updateProduct(id: string, input: UpdateProductInput): Promise<Product> {
    const product = await this.getProductById(id);
    if (!product) {
      throw new Error("Product not found");
    }

    const updated: Product = {
      ...product,
      ...input,
      inStock: (input.stockCount ?? product.stockCount) > 0,
      updatedAt: new Date(),
    };

    products.set(id, updated);
    return updated;
  }

  /**
   * Deletes a product
   */
  async deleteProduct(id: string): Promise<boolean> {
    return products.delete(id);
  }

  /**
   * Lists all products, optionally filtered by category
   */
  async listProducts(category?: ProductCategory): Promise<Product[]> {
    let result = Array.from(products.values());

    if (category) {
      result = result.filter((p) => p.category === category);
    }

    return result;
  }

  /**
   * Searches products by name or description
   */
  async searchProducts(query: string): Promise<Product[]> {
    const queryLower = query.toLowerCase();
    return Array.from(products.values()).filter(
      (p) =>
        p.name.toLowerCase().includes(queryLower) ||
        p.description.toLowerCase().includes(queryLower)
    );
  }

  /**
   * Updates stock count for a product
   */
  async updateStock(productId: string, newStockCount: number): Promise<Product> {
    if (newStockCount < 0) {
      throw new Error("Stock count cannot be negative");
    }

    return this.updateProduct(productId, {
      stockCount: newStockCount,
    });
  }
}

// Export singleton instance
export const productService = new ProductService();

