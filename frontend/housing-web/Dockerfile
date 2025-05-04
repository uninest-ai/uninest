# Development Node image
FROM node:19.1.0

# Set working directory
WORKDIR /app

# Copy dependency manifest
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Expose development port (Vite default is 5173)
EXPOSE 5173

# Default run Vite development server
CMD ["npm", "run", "dev", "--", "--host"]