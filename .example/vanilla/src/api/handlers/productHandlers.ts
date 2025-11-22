/**
 * Product API handlers
 */

import { Request, Response } from "express";
import { productService } from "../services/productService";
import {
  CreateProductInput,
  UpdateProductInput,
  ProductCategory,
} from "../types/product";

export class ProductHandlers {
  /**
   * POST /api/products - Create a new product
   */
  async createProduct(req: Request, res: Response): Promise<void> {
    try {
      const input: CreateProductInput = req.body;
      const product = await productService.createProduct(input);
      res.status(201).json(product);
    } catch (error) {
      res.status(400).json({ error: (error as Error).message });
    }
  }

  /**
   * GET /api/products/:id - Get product by ID
   */
  async getProductById(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const product = await productService.getProductById(id);

      if (!product) {
        res.status(404).json({ error: "Product not found" });
        return;
      }

      res.json(product);
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }

  /**
   * PUT /api/products/:id - Update product
   */
  async updateProduct(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const input: UpdateProductInput = req.body;
      const product = await productService.updateProduct(id, input);
      res.json(product);
    } catch (error) {
      const message = (error as Error).message;
      if (message.includes("not found")) {
        res.status(404).json({ error: message });
      } else {
        res.status(400).json({ error: message });
      }
    }
  }

  /**
   * DELETE /api/products/:id - Delete product
   */
  async deleteProduct(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const deleted = await productService.deleteProduct(id);

      if (!deleted) {
        res.status(404).json({ error: "Product not found" });
        return;
      }

      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }

  /**
   * GET /api/products - List products, optionally filtered by category
   */
  async listProducts(req: Request, res: Response): Promise<void> {
    try {
      const category = req.query.category as ProductCategory | undefined;
      const products = await productService.listProducts(category);
      res.json(products);
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }

  /**
   * GET /api/products/search - Search products
   */
  async searchProducts(req: Request, res: Response): Promise<void> {
    try {
      const query = req.query.q as string;
      if (!query) {
        res.status(400).json({ error: "Query parameter 'q' is required" });
        return;
      }

      const products = await productService.searchProducts(query);
      res.json(products);
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }
}

export const productHandlers = new ProductHandlers();

