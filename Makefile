.PHONY: install-backend install-frontend install run-backend run-frontend dev-backend dev-frontend dev clean help

# Default target
.DEFAULT_GOAL := help

# Help
help:
	@echo "Deep Research Agent - Available Commands"
	@echo ""
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make install-backend  Install Python backend dependencies"
	@echo "  make install-frontend Install Node.js frontend dependencies"
	@echo ""
	@echo "  make dev              Run both backend and frontend (requires terminal multiplexer)"
	@echo "  make run-backend      Run the FastAPI backend server"
	@echo "  make run-frontend     Run the Vite frontend dev server"
	@echo "  make dev-backend      Alias for run-backend"
	@echo "  make dev-frontend     Alias for run-frontend"
	@echo ""
	@echo "  make clean            Remove build artifacts and dependencies"
	@echo ""

# Install dependencies
install-backend:
	@echo "Installing backend dependencies..."
	cd services/backend && pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd services/frontend && npm install

install: install-backend install-frontend
	@echo ""
	@echo "All dependencies installed!"
	@echo "Run 'make dev' to start the application."

# Run services
run-backend:
	@echo "Starting backend server on http://localhost:8000..."
	cd services/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "Starting frontend dev server on http://localhost:3000..."
	cd services/frontend && npm run dev

# Aliases
dev-backend: run-backend
dev-frontend: run-frontend

# Run both services
dev:
	@echo "Starting Deep Research Agent..."
	@echo ""
	@echo "This will run both servers. Use Ctrl+C to stop."
	@echo ""
	@if command -v concurrently >/dev/null 2>&1; then \
		concurrently --names "BACKEND,FRONTEND" --prefix-colors "blue,green" \
			"cd services/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000" \
			"cd services/frontend && npm run dev"; \
	elif command -v npx >/dev/null 2>&1; then \
		npx concurrently --names "BACKEND,FRONTEND" --prefix-colors "blue,green" \
			"cd services/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000" \
			"cd services/frontend && npm run dev"; \
	else \
		echo "To run both servers together, install concurrently:"; \
		echo "  npm install -g concurrently"; \
		echo ""; \
		echo "Or run in separate terminals:"; \
		echo "  Terminal 1: make run-backend"; \
		echo "  Terminal 2: make run-frontend"; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete!"
