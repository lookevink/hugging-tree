/**
 * API route definitions
 */

import { Router } from "express";
import { userHandlers } from "./handlers/userHandlers";
import { productHandlers } from "./handlers/productHandlers";
import { orderHandlers } from "./handlers/orderHandlers";

const router = Router();

// User routes
router.post("/users", (req, res) => userHandlers.createUser(req, res));
router.get("/users", (req, res) => userHandlers.listUsers(req, res));
router.get("/users/:id", (req, res) => userHandlers.getUserById(req, res));
router.put("/users/:id", (req, res) => userHandlers.updateUser(req, res));
router.delete("/users/:id", (req, res) => userHandlers.deleteUser(req, res));

// Product routes
router.post("/products", (req, res) => productHandlers.createProduct(req, res));
router.get("/products", (req, res) => productHandlers.listProducts(req, res));
router.get("/products/search", (req, res) => productHandlers.searchProducts(req, res));
router.get("/products/:id", (req, res) => productHandlers.getProductById(req, res));
router.put("/products/:id", (req, res) => productHandlers.updateProduct(req, res));
router.delete("/products/:id", (req, res) => productHandlers.deleteProduct(req, res));

// Order routes
router.post("/orders", (req, res) => orderHandlers.createOrder(req, res));
router.get("/orders", (req, res) => orderHandlers.listOrders(req, res));
router.get("/orders/user/:userId", (req, res) => orderHandlers.getOrdersByUserId(req, res));
router.get("/orders/:id", (req, res) => orderHandlers.getOrderById(req, res));
router.put("/orders/:id/status", (req, res) => orderHandlers.updateOrderStatus(req, res));

export default router;

