#!/bin/bash

# Docker cleanup script for discord_sezar_bot
# This script helps free up disk space by removing unused Docker resources

echo "Starting Docker cleanup process..."

# Remove all stopped containers
echo "Removing stopped containers..."
docker container prune -f

# Remove unused images
echo "Removing dangling images..."
docker image prune -f

# Remove unused volumes (careful with this one)
echo "Removing unused volumes..."
docker volume prune -f

# Remove build cache
echo "Removing build cache..."
docker builder prune -f

# System prune (use with caution as it removes all unused containers, networks, images, and cache)
echo "Performing system prune..."
docker system prune -f

echo "Cleanup complete!"

# Show the current Docker disk usage
echo "Current Docker disk usage:"
docker system df

# Instructions for further cleanup if needed
echo ""
echo "If you still have disk space issues, try:"
echo "1. docker system prune --all --volumes -f (WARNING: This will remove ALL unused data)"
echo "2. Verify other applications aren't consuming disk space"
echo ""
echo "Now you can start your Discord bot with docker-compose up -d"