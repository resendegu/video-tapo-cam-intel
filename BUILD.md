# syntax=docker/dockerfile:1
# Build script for multi-platform images.
# Run from repo root:
#
#   docker buildx create --use --name multibuilder
#   docker buildx build \
#     --platform linux/amd64,linux/arm64,linux/arm/v7 \
#     --tag tapo-intel:latest \
#     --push \
#     ./backend
#
# For local single-platform (dev):
#   docker compose up --build
