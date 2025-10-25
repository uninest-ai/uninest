# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

# Accept build arguments
ARG VITE_API_BASE_URL
ARG VITE_GOOGLE_API_KEY

# Set environment variables for build
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_GOOGLE_API_KEY=${VITE_GOOGLE_API_KEY}

# Copy package files
COPY frontend/housing-web/package*.json ./

# Clean install dependencies (without package-lock to avoid version conflicts)
RUN npm install --legacy-peer-deps

# Copy source code (excluding node_modules)
COPY frontend/housing-web/src ./src
COPY frontend/housing-web/pages ./pages
COPY frontend/housing-web/public ./public
COPY frontend/housing-web/index.html ./
COPY frontend/housing-web/vite.config.js ./
COPY frontend/housing-web/tailwind.config.js ./
COPY frontend/housing-web/postcss.config.js ./
COPY frontend/housing-web/eslint.config.js ./

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]