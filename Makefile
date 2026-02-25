# =============================================================================
# Makefile for apidev
# =============================================================================

.PHONY: help menu install-deps format lint test

.DEFAULT_GOAL := help

BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m

help: ## Show this help message
	@echo ""
	@echo "$(BLUE)apidev — Contract-driven API code generator CLI$(NC)"
	@echo ""
	@python scripts/make_help.py
	@echo ""

menu: ## Interactive command menu (select and run a target)
	@python scripts/make_menu.py

install-deps: ## Create venv and install all dependencies (runtime + code + test)
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@uv venv
	@uv pip install -e .
	@uv pip compile requirements/code.in -o requirements/code.txt && uv pip install -r requirements/code.txt
	@uv pip compile requirements/test.in -o requirements/test.txt 2>/dev/null || true; \
	[ -f requirements/test.txt ] && uv pip install -r requirements/test.txt || true
	@echo "$(GREEN)Dependencies installed$(NC)"

##@ Development

format: ## Format code (Black)
	@echo "$(YELLOW)Formatting code...$(NC)"
	@if [ ! -d .venv ]; then \
		echo "$(RED)Virtual environment not found. Run: uv venv$(NC)"; \
		exit 1; \
	fi
	@if [ -f .venv/bin/black ]; then \
		.venv/bin/black src/ tests/; \
	elif [ -f .venv/Scripts/black.exe ]; then \
		.venv/Scripts/black.exe src/ tests/; \
	else \
		echo "$(RED)black not found. Install: uv pip install -r requirements/code.txt$(NC)"; \
		echo "  (if code.txt missing: uv pip compile requirements/code.in -o requirements/code.txt)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Format done$(NC)"

lint: ## Static analysis (Flake8 + Pyright)
	@echo "$(YELLOW)Running lint...$(NC)"
	@if [ ! -d .venv ]; then \
		echo "$(RED)Virtual environment not found. Run: uv venv$(NC)"; \
		exit 1; \
	fi
	@if [ -f .venv/bin/flake8 ]; then \
		echo "$(BLUE)[Flake8]$(NC)"; \
		.venv/bin/flake8 src/ tests/ --count --select=E9,F63,F7,F82,F401,F841 --show-source --statistics && \
		echo "$(GREEN)Flake8 passed$(NC)"; \
	elif [ -f .venv/Scripts/flake8.exe ]; then \
		echo "$(BLUE)[Flake8]$(NC)"; \
		.venv/Scripts/flake8.exe src/ tests/ --count --select=E9,F63,F7,F82,F401,F841 --show-source --statistics && \
		echo "$(GREEN)Flake8 passed$(NC)"; \
	else \
		echo "$(RED)flake8 not found. Install: uv pip install -r requirements/code.txt$(NC)"; \
		echo "  (if code.txt missing: uv pip compile requirements/code.in -o requirements/code.txt)"; \
		exit 1; \
	fi
	@if [ -f .venv/bin/pyright ]; then \
		echo "$(BLUE)[Pyright]$(NC)"; \
		.venv/bin/pyright && echo "$(GREEN)Pyright passed$(NC)"; \
	elif [ -f .venv/Scripts/pyright.exe ]; then \
		echo "$(BLUE)[Pyright]$(NC)"; \
		.venv/Scripts/pyright.exe && echo "$(GREEN)Pyright passed$(NC)"; \
	else \
		echo "$(RED)pyright not found. Install: uv pip install -r requirements/code.txt$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Lint passed$(NC)"

test: ## Run tests (pytest)
	@echo "$(YELLOW)Running tests...$(NC)"
	@if [ ! -d .venv ]; then \
		echo "$(RED)Virtual environment not found. Run: uv venv$(NC)"; \
		exit 1; \
	fi
	@if [ -f .venv/bin/pytest ]; then \
		.venv/bin/pytest tests/ -v; \
	elif [ -f .venv/Scripts/pytest.exe ]; then \
		.venv/Scripts/pytest.exe tests/ -v; \
	else \
		echo "$(RED)pytest not found. Install: uv pip install -r requirements/test.txt$(NC)"; \
		echo "  (if test.txt missing: uv pip compile requirements/test.in -o requirements/test.txt)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Tests passed$(NC)"
