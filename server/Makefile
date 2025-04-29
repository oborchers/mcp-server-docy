# Makefile for Docy SSE Server

# Configuration
IMAGE_NAME := oborchers/mcp-server-docy:latest
CACHE_DIR := $(shell pwd)/.docy.cache
CONTAINER_NAME := docy-sse-server
URLS_FILE := $(shell pwd)/.docy.urls
PORT := 6274
LOCAL_PATH := $(shell cd .. && pwd)

# Ensure cache directory exists
$(shell mkdir -p $(CACHE_DIR))

.PHONY: run run-debug stop restart restart-debug build-local help

# Run the Docy container, mounting cache and .docy.urls file
run:
	@echo "Starting Docy SSE server..."
	docker pull $(IMAGE_NAME)
	docker run -d --name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		-e DOCY_TRANSPORT=sse \
		-e DOCY_HOST=0.0.0.0 \
		-e DOCY_PORT=$(PORT) \
		-e DOCY_DEBUG=false \
		-e DOCY_CACHE_DIRECTORY=/cache \
		-e DOCY_DOCUMENTATION_URLS_FILE=/app/.docy.urls \
		-v $(CACHE_DIR):/cache \
		-v $(URLS_FILE):/app/.docy.urls \
		$(IMAGE_NAME)
	@echo "Docy SSE server is running at http://localhost:$(PORT)"
	@echo "Add this to your project's .mcp.json:"
	@echo ""
	@echo '{'
	@echo '  "mcp": {'
	@echo '    "servers": {'
	@echo '      "docy": {'
	@echo '        "type": "sse",'
	@echo '        "url": "http://localhost:$(PORT)/sse"'
	@echo '      }'
	@echo '    }'
	@echo '  }'
	@echo '}'

# Run in debug mode - builds locally and enables debug logging
run-debug: build-local
	@echo "Starting Docy SSE server in DEBUG mode (locally built image)..."
	docker run -d --name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		-e DOCY_TRANSPORT=sse \
		-e DOCY_HOST=0.0.0.0 \
		-e DOCY_PORT=$(PORT) \
		-e DOCY_DEBUG=true \
		-e DOCY_CACHE_DIRECTORY=/cache \
		-e DOCY_DOCUMENTATION_URLS_FILE=/app/.docy.urls \
		-v $(CACHE_DIR):/cache \
		-v $(URLS_FILE):/app/.docy.urls \
		$(IMAGE_NAME)
	@echo "Docy SSE server (DEBUG MODE) is running at http://localhost:$(PORT)"

# Build the image locally
build-local:
	@echo "Building Docy image locally..."
	docker build -t $(IMAGE_NAME) $(LOCAL_PATH)
	@echo "Local build complete"

# Stop and remove the Docy container
stop:
	@echo "Stopping Docy SSE server..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)
	@echo "Docy SSE server stopped and removed"

# Restart the Docy container (depends on stop and run targets)
restart:
	@$(MAKE) stop
	@$(MAKE) run
	@echo "Docy SSE server restarted"

# Restart in debug mode - builds locally and enables debug logging
restart-debug:
	@$(MAKE) stop
	@$(MAKE) run-debug
	@echo "Docy SSE server restarted in DEBUG mode"

# Display help information
help:
	@echo "Docy SSE Server Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make run           - Start Docy SSE server"
	@echo "  make run-debug     - Start Docy SSE server in debug mode (builds locally)"
	@echo "  make build-local   - Build the image locally without running it"
	@echo "  make stop          - Stop and remove Docy SSE server"
	@echo "  make restart       - Restart Docy SSE server"
	@echo "  make restart-debug - Restart Docy SSE server in debug mode"
	@echo "  make help          - Display this help message"