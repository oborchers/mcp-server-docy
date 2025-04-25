# Makefile for Docy MCP Server

# Configuration
IMAGE_NAME := oborchers/mcp-server-docy:latest
CACHE_DIR := $(shell pwd)/.docy.cache
CONTAINER_NAME := docy-local
URLS_FILE := $(shell pwd)/.docy.urls
PORT := 8001

# Ensure cache directory exists
$(shell mkdir -p $(CACHE_DIR))

.PHONY: run stop restart reload-urls help

# Run the Docy container, mounting cache and .docy.urls file
run:
	@echo "Starting Docy container..."
	docker pull $(IMAGE_NAME)
	docker run -d --name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		-e DOCY_TRANSPORT=sse \
		-e DOCY_HOST=0.0.0.0 \
		-e DOCY_PORT=$(PORT) \
		-v $(CACHE_DIR):/cache \
		-v $(URLS_FILE):/app/.docy.urls \
		$(IMAGE_NAME)
	@echo "Docy is running at http://localhost:$(PORT)"

# Stop and remove the Docy container
stop:
	@echo "Stopping Docy container..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)
	@echo "Docy container stopped and removed"

# Restart the Docy container
restart: stop run
	@echo "Docy container restarted"

# Reload URLs file without full restart
reload-urls:
	@echo "Reloading URLs file..."
	docker stop $(CONTAINER_NAME)
	docker start $(CONTAINER_NAME)
	@echo "URLs file reloaded"

# Display help information
help:
	@echo "Docy MCP Server Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make run         - Start Docy container"
	@echo "  make stop        - Stop and remove Docy container"
	@echo "  make restart     - Restart Docy container"
	@echo "  make reload-urls - Reload URLs file without full restart"
	@echo "  make help        - Display this help message"