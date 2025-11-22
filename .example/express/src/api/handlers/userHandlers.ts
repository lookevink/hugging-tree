/**
 * User API handlers
 */

import { Request, Response } from "express";
import { userService } from "../../services/userService";
import { CreateUserInput, UpdateUserInput, UserQueryFilters } from "../../types/user";

export class UserHandlers {
  /**
   * POST /api/users - Create a new user
   */
  async createUser(req: Request, res: Response): Promise<void> {
    try {
      const input: CreateUserInput = req.body;
      const user = await userService.createUser(input);
      res.status(201).json(user);
    } catch (error) {
      res.status(400).json({ error: (error as Error).message });
    }
  }

  /**
   * GET /api/users/:id - Get user by ID
   */
  async getUserById(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const user = await userService.getUserById(id);

      if (!user) {
        res.status(404).json({ error: "User not found" });
        return;
      }

      res.json(user);
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }

  /**
   * PUT /api/users/:id - Update user
   */
  async updateUser(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const input: UpdateUserInput = req.body;
      const user = await userService.updateUser(id, input);
      res.json(user);
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
   * DELETE /api/users/:id - Delete user
   */
  async deleteUser(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const deleted = await userService.deleteUser(id);

      if (!deleted) {
        res.status(404).json({ error: "User not found" });
        return;
      }

      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }

  /**
   * GET /api/users - List users with optional filters
   */
  async listUsers(req: Request, res: Response): Promise<void> {
    try {
      const filters: UserQueryFilters = {
        role: req.query.role as any,
        email: req.query.email as string,
        search: req.query.search as string,
      };

      const users = await userService.listUsers(filters);
      res.json(users);
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  }
}

export const userHandlers = new UserHandlers();

