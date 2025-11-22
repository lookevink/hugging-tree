# Sample TypeScript Project

This is a sample TypeScript project designed to demonstrate code scanning, graph building, and vectorization capabilities.

## Project Structure

```
src/
├── types/           # Domain types and interfaces
│   ├── user.ts
│   ├── product.ts
│   ├── order.ts
│   └── index.ts
├── services/        # Business logic layer
│   ├── userService.ts
│   ├── productService.ts
│   ├── orderService.ts
│   └── index.ts
├── api/             # API layer
│   ├── handlers/    # Request handlers
│   │   ├── userHandlers.ts
│   │   ├── productHandlers.ts
│   │   └── orderHandlers.ts
│   └── routes.ts    # Route definitions
├── utils/           # Utility functions
│   ├── validation.ts
│   ├── idGenerator.ts
│   ├── errors.ts
│   └── index.ts
└── index.ts         # Application entry point
```

## Features

- **Type-safe domain models**: User, Product, and Order entities with TypeScript interfaces
- **Service layer**: Business logic separated into service classes
- **RESTful API**: Express.js handlers for CRUD operations
- **Cross-file dependencies**: Services import from types, handlers import from services
- **Utility functions**: Reusable validation and ID generation utilities
- **Test files**: Example test structure for unit testing

## Relationships

This project demonstrates various code relationships that are ideal for graph building:

1. **Type dependencies**: Services depend on types, handlers depend on services
2. **Import relationships**: Clear import chains across modules
3. **Function calls**: Services call other services (e.g., OrderService uses UserService and ProductService)
4. **Type composition**: Types reference other types (e.g., OrderWithDetails includes User and Product)

## Installation

```bash
npm install
```

## Build

```bash
npm run build
```

## Run

```bash
npm run dev
```

## Test

```bash
npm test
```

