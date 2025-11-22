/**
 * Tests for UserService
 */

import { UserService } from "./userService";
import { UserRole } from "../types/user";

describe("UserService", () => {
  let service: UserService;

  beforeEach(() => {
    service = new UserService();
  });

  describe("createUser", () => {
    it("should create a user with valid input", async () => {
      const input = {
        email: "test@example.com",
        name: "Test User",
      };

      const user = await service.createUser(input);

      expect(user).toBeDefined();
      expect(user.email).toBe(input.email);
      expect(user.name).toBe(input.name);
      expect(user.role).toBe(UserRole.USER);
      expect(user.id).toBeDefined();
    });

    it("should throw error for invalid email", async () => {
      const input = {
        email: "invalid-email",
        name: "Test User",
      };

      await expect(service.createUser(input)).rejects.toThrow();
    });
  });

  describe("getUserById", () => {
    it("should return user if exists", async () => {
      const user = await service.createUser({
        email: "test@example.com",
        name: "Test User",
      });

      const found = await service.getUserById(user.id);
      expect(found).toEqual(user);
    });

    it("should return null if user does not exist", async () => {
      const found = await service.getUserById("non-existent-id");
      expect(found).toBeNull();
    });
  });
});

