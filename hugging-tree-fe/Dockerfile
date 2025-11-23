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
# If node_modules is empty OR if react-markdown is missing (package.json changed), reinstall dependencies
CMD ["sh", "-c", "export CI=true && if [ ! -d node_modules ] || [ -z \"$(ls -A node_modules)\" ] || [ ! -d \"node_modules/react-markdown\" ]; then pnpm install --frozen-lockfile; fi && pnpm run dev"]

