#!/bin/bash
# Setup script for Sezar Discord Bot

echo "Setting up Sezar Discord Bot..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Installing Docker Compose..."
    pip install docker-compose
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "DISCORD_BOT_TOKEN=your_token_here" > .env
    echo "STEAM_API_KEY=your_steam_api_key_here" >> .env
    echo "Please edit the .env file with your actual tokens."
fi

# Build and start the containers
echo "Building and starting containers..."
docker-compose up -d --build

echo "Setup complete. Your bot should now be running!"
echo "Check the logs with: docker-compose logs -f"