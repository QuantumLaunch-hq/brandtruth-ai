# Frontend Dockerfile for BrandTruth AI
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm ci

# Generate Prisma client
RUN npx prisma generate

# Copy application code
COPY . .

EXPOSE 3000

# Run in development mode
CMD ["npm", "run", "dev"]
