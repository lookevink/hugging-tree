/**
 * User service - handles business logic for user operations
 */

import { User, CreateUserInput, UpdateUserInput, UserQueryFilters, UserRole } from "../types/user";
import { validateEmail } from "../utils/validation";
import { generateId } from "../utils/idGenerator";

/**
 * In-memory user store (in a real app, this would be a database)
 */
const users: Map<string, User> = new Map();

export class UserService {
  /**
   * Creates a new user
   */
  async createUser(input: CreateUserInput): Promise<User> {
    if (!validateEmail(input.email)) {
      throw new Error("Invalid email address");
    }

    // Check if user already exists
    const existingUser = Array.from(users.values()).find(
      (u) => u.email === input.email
    );
    if (existingUser) {
      throw new Error("User with this email already exists");
    }

    const now = new Date();
    const user: User = {
      id: generateId(),
      email: input.email,
      name: input.name,
      role: input.role || UserRole.USER,
      createdAt: now,
      updatedAt: now,
    };

    users.set(user.id, user);
    return user;
  }

  /**
   * Retrieves a user by ID
   */
  async getUserById(id: string): Promise<User | null> {
    return users.get(id) || null;
  }

  /**
   * Retrieves a user by email
   */
  async getUserByEmail(email: string): Promise<User | null> {
    return Array.from(users.values()).find((u) => u.email === email) || null;
  }

  /**
   * Updates an existing user
   */
  async updateUser(id: string, input: UpdateUserInput): Promise<User> {
    const user = await this.getUserById(id);
    if (!user) {
      throw new Error("User not found");
    }

    const updated: User = {
      ...user,
      ...input,
      updatedAt: new Date(),
    };

    users.set(id, updated);
    return updated;
  }

  /**
   * Deletes a user
   */
  async deleteUser(id: string): Promise<boolean> {
    return users.delete(id);
  }

  /**
   * Lists users with optional filters
   */
  async listUsers(filters?: UserQueryFilters): Promise<User[]> {
    let result = Array.from(users.values());

    if (filters?.role) {
      result = result.filter((u) => u.role === filters.role);
    }

    if (filters?.email) {
      result = result.filter((u) =>
        u.email.toLowerCase().includes(filters.email!.toLowerCase())
      );
    }

    if (filters?.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (u) =>
          u.name.toLowerCase().includes(searchLower) ||
          u.email.toLowerCase().includes(searchLower)
      );
    }

    return result;
  }
}

// Export singleton instance
export const userService = new UserService();

