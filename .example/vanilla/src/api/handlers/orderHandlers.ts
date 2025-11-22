/**
 * Order API handlers
 */

import { Request, Response } from "express";
import { orderService } from "../services/orderService";
import { CreateOrderInput, OrderStatus } from "../types/order";

export class OrderHandlers {
  /**
   * POST /api/orders - Create a new order
   */
  async createOrder(req: Request, res: Response): Promise<void> {
    try {
      const input: CreateOrderInput = req.body;
      const order = await orderService.createOrder(input);
      res.status(201).json(order);
    } catch (error) {
      res.status(400).json({ error: (error as Error).message });
    }
  }

  /**
   * GET /api/orders/:id - Get order by ID
   */
  async getOrderById(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const includeDetails = req.query.details === "true";
      
      if (includeDetails) {
        const order = await orderService.getOrderWithDetails(id);
        if (!order) {
          res.status(404).json({ error: "Order not found" });
          return;
        }
        res.json(order);
      } else {
        const order = await orderService.getOrderById(id);
        if (!order) {
          res.status(404).json({ error: "Order not found" });
          return;
        }
        res.json(order);
      }
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }

  /**
   * PUT /api/orders/:id/status - Update order status
   */
  async updateOrderStatus(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { status } = req.body;

      if (!Object.values(OrderStatus).includes(status)) {
        res.status(400).json({ error: "Invalid order status" });
        return;
      }

      const order = await orderService.updateOrderStatus(id, status);
      res.json(order);
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
   * GET /api/orders/user/:userId - Get orders for a user
   */
  async getOrdersByUserId(req: Request, res: Response): Promise<void> {
    try {
      const { userId } = req.params;
      const orders = await orderService.getOrdersByUserId(userId);
      res.json(orders);
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }

  /**
   * GET /api/orders - List all orders, optionally filtered by status
   */
  async listOrders(req: Request, res: Response): Promise<void> {
    try {
      const status = req.query.status as OrderStatus | undefined;
      const orders = await orderService.listOrders(status);
      res.json(orders);
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }
}

export const orderHandlers = new OrderHandlers();

