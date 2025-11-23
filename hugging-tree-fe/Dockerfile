FROM node:20-alpine

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files first
COPY package.json pnpm-lock.yaml ./

# Install dependencies (will be preserved in named volume)
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
# Reinstall dependencies if node_modules is missing/empty OR if lockfile hash changed
# Store lockfile hash in node_modules/.lockfile-hash and compare on startup
CMD ["sh", "-c", "export CI=true && LOCKFILE_HASH=$(sha256sum pnpm-lock.yaml 2>/dev/null | cut -d' ' -f1 || echo '') && STORED_HASH=$(cat node_modules/.lockfile-hash 2>/dev/null || echo '') && if [ ! -d node_modules ] || [ -z \"$(ls -A node_modules 2>/dev/null)\" ] || [ \"$LOCKFILE_HASH\" != \"$STORED_HASH\" ]; then echo 'Installing/updating dependencies...' && pnpm install --frozen-lockfile && echo \"$LOCKFILE_HASH\" > node_modules/.lockfile-hash 2>/dev/null || true; fi && pnpm run dev"]

