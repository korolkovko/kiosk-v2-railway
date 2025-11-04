# syntax=docker/dockerfile:1
FROM node:18-alpine AS build
WORKDIR /app

# Keep npm updated for better workspace handling
RUN npm i -g npm@latest

# Copy only manifest files first to leverage Docker layer caching
COPY package*.json ./
COPY shared/package.json ./shared/
COPY apps/kiosk/package.json ./apps/kiosk/

# Install workspace deps (tolerant to peer deps during containerized builds)
RUN npm install --force || npm install --legacy-peer-deps || true

# Copy full workspace
COPY . .

# Accept build arguments for Vite environment variables
# These will be embedded in the build at compile time
ARG VITE_API_URL
ARG VITE_WS_URL
ARG VITE_STORAGE_PROVIDER
ARG VITE_LOCAL_MEDIA_BASE_PATH
ARG VITE_LOCAL_PATH_ITEMS
ARG VITE_LOCAL_PATH_CATEGORIES_OPEN
ARG VITE_LOCAL_PATH_CATEGORIES_SORRY
ARG VITE_LOCAL_PATH_CATEGORIES_PROMOTED
ARG VITE_LOCAL_PATH_SCREENSAVER
ARG VITE_LOCAL_PATH_ORDER_HANDLING
ARG VITE_LOCAL_PATH_SERVICE_MODE
ARG VITE_S3_ENDPOINT
ARG VITE_S3_BUCKET
ARG VITE_S3_REGION
ARG VITE_SERVICE_MODE_MEDIA_NAMES
ARG VITE_SCREENSAVER_MEDIA_NAMES
ARG VITE_ORDER_HANDLING_MEDIA_NAMES

# Make args available as environment variables during build
# Vite will embed these into the JavaScript bundle
ENV VITE_API_URL=$VITE_API_URL \
    VITE_WS_URL=$VITE_WS_URL \
    VITE_STORAGE_PROVIDER=$VITE_STORAGE_PROVIDER \
    VITE_LOCAL_MEDIA_BASE_PATH=$VITE_LOCAL_MEDIA_BASE_PATH \
    VITE_LOCAL_PATH_ITEMS=$VITE_LOCAL_PATH_ITEMS \
    VITE_LOCAL_PATH_CATEGORIES_OPEN=$VITE_LOCAL_PATH_CATEGORIES_OPEN \
    VITE_LOCAL_PATH_CATEGORIES_SORRY=$VITE_LOCAL_PATH_CATEGORIES_SORRY \
    VITE_LOCAL_PATH_CATEGORIES_PROMOTED=$VITE_LOCAL_PATH_CATEGORIES_PROMOTED \
    VITE_LOCAL_PATH_SCREENSAVER=$VITE_LOCAL_PATH_SCREENSAVER \
    VITE_LOCAL_PATH_ORDER_HANDLING=$VITE_LOCAL_PATH_ORDER_HANDLING \
    VITE_LOCAL_PATH_SERVICE_MODE=$VITE_LOCAL_PATH_SERVICE_MODE \
    VITE_S3_ENDPOINT=$VITE_S3_ENDPOINT \
    VITE_S3_BUCKET=$VITE_S3_BUCKET \
    VITE_S3_REGION=$VITE_S3_REGION \
    VITE_SERVICE_MODE_MEDIA_NAMES=$VITE_SERVICE_MODE_MEDIA_NAMES \
    VITE_SCREENSAVER_MEDIA_NAMES=$VITE_SCREENSAVER_MEDIA_NAMES \
    VITE_ORDER_HANDLING_MEDIA_NAMES=$VITE_ORDER_HANDLING_MEDIA_NAMES

# Build only the kiosk app
# Vite will embed VITE_* environment variables into the build
RUN npm run build:kiosk

# ---- Runtime ----
FROM nginx:alpine

# SPA nginx config with history fallback
COPY apps/kiosk/nginx.conf /etc/nginx/nginx.conf

# Static assets
COPY --from=build /app/apps/kiosk/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
