/**
 * Order service - handles business logic for order operations
 */

import {
  Order,
  CreateOrderInput,
  OrderStatus,
  OrderItem,
  OrderWithDetails,
} from "../types/order";
import { generateId } from "../utils/idGenerator";
import { userService } from "./userService";
import { productService } from "./productService";

/**
 * In-memory order store (in a real app, this would be a database)
 */
const orders: Map<string, Order> = new Map();

export class OrderService {
  /**
   * Creates a new order
   */
  async createOrder(input: CreateOrderInput): Promise<Order> {
    // Verify user exists
    const user = await userService.getUserById(input.userId);
    if (!user) {
      throw new Error("User not found");
    }

    // Verify all products exist and calculate total
    let total = 0;
    for (const item of input.items) {
      const product = await productService.getProductById(item.productId);
      if (!product) {
        throw new Error(`Product ${item.productId} not found`);
      }

      if (!product.inStock || product.stockCount < item.quantity) {
        throw new Error(`Insufficient stock for product ${product.name}`);
      }

      total += item.price * item.quantity;
    }

    const now = new Date();
    const order: Order = {
      id: generateId(),
      userId: input.userId,
      items: input.items,
      total,
      status: OrderStatus.PENDING,
      shippingAddress: input.shippingAddress,
      createdAt: now,
      updatedAt: now,
    };

    orders.set(order.id, order);

    // Update stock counts
    for (const item of input.items) {
      const product = await productService.getProductById(item.productId);
      if (product) {
        await productService.updateStock(
          item.productId,
          product.stockCount - item.quantity
        );
      }
    }

    return order;
  }

  /**
   * Retrieves an order by ID
   */
  async getOrderById(id: string): Promise<Order | null> {
    return orders.get(id) || null;
  }

  /**
   * Retrieves an order with full details (user and products)
   */
  async getOrderWithDetails(id: string): Promise<OrderWithDetails | null> {
    const order = await this.getOrderById(id);
    if (!order) {
      return null;
    }

    const user = await userService.getUserById(order.userId);
    if (!user) {
      throw new Error("User not found for order");
    }

    const products = await Promise.all(
      order.items.map((item) => productService.getProductById(item.productId))
    );

    const validProducts = products.filter(
      (p): p is NonNullable<typeof p> => p !== null
    );

    return {
      ...order,
      user,
      products: validProducts,
    };
  }

  /**
   * Updates order status
   */
  async updateOrderStatus(
    id: string,
    status: OrderStatus
  ): Promise<Order> {
    const order = await this.getOrderById(id);
    if (!order) {
      throw new Error("Order not found");
    }

    const updated: Order = {
      ...order,
      status,
      updatedAt: new Date(),
    };

    orders.set(id, updated);
    return updated;
  }

  /**
   * Lists orders for a specific user
   */
  async getOrdersByUserId(userId: string): Promise<Order[]> {
    return Array.from(orders.values()).filter((o) => o.userId === userId);
  }

  /**
   * Lists all orders, optionally filtered by status
   */
  async listOrders(status?: OrderStatus): Promise<Order[]> {
    let result = Array.from(orders.values());

    if (status) {
      result = result.filter((o) => o.status === status);
    }

    return result;
  }
}

// Export singleton instance
export const orderService = new OrderService();

