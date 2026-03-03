# =============================================================================
# Makefile for apidev
# =============================================================================

.PHONY: help menu install-deps format lint test test-length-report architecture-test docs-check build-binary package-binary smoke-binary release

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

test-length-report: ## Report large test files/functions (non-blocking)
	@python scripts/test_length_report.py

architecture-test: ## Run architecture guardrail tests only
	@echo "$(YELLOW)Running architecture tests...$(NC)"
	@if [ ! -d .venv ]; then \
		echo "$(RED)Virtual environment not found. Run: uv venv$(NC)"; \
		exit 1; \
	fi
	@if [ -f .venv/bin/pytest ]; then \
		.venv/bin/pytest tests/unit/architecture tests/contract/architecture -v; \
	elif [ -f .venv/Scripts/pytest.exe ]; then \
		.venv/Scripts/pytest.exe tests/unit/architecture tests/contract/architecture -v; \
	else \
		echo "$(RED)pytest not found. Install: uv pip install -r requirements/test.txt$(NC)"; \
		echo "  (if test.txt missing: uv pip compile requirements/test.in -o requirements/test.txt)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Architecture tests passed$(NC)"

docs-check: ## Run documentation consistency checks
	@echo "$(YELLOW)Running documentation checks...$(NC)"
	@if [ ! -d .venv ]; then \
		echo "$(RED)Virtual environment not found. Run: uv venv$(NC)"; \
		exit 1; \
	fi
	@if [ -f .venv/bin/pytest ]; then \
		.venv/bin/pytest tests/unit/test_documentation_conventions.py tests/unit/test_documentation_quality.py -v; \
	elif [ -f .venv/Scripts/pytest.exe ]; then \
		.venv/Scripts/pytest.exe tests/unit/test_documentation_conventions.py tests/unit/test_documentation_quality.py -v; \
	else \
		echo "$(RED)pytest not found. Install: uv pip install -r requirements/test.txt$(NC)"; \
		echo "  (if test.txt missing: uv pip compile requirements/test.in -o requirements/test.txt)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Documentation checks passed$(NC)"

##@ Packaging

build-binary: ## Build standalone CLI binary with PyInstaller
	@if [ ! -d .venv ]; then \
		echo "$(RED)Virtual environment not found. Run: make install-deps$(NC)"; \
		exit 1; \
	fi
	@uv pip install pyinstaller==6.18.0 --quiet 2>/dev/null || true
	@if [ -f .venv/bin/python ]; then \
		.venv/bin/python scripts/release/build_binary.py; \
	elif [ -f .venv/Scripts/python.exe ]; then \
		.venv/Scripts/python.exe scripts/release/build_binary.py; \
	else \
		echo "$(RED)Could not find .venv Python$(NC)"; exit 1; \
	fi

package-binary: ## Package release artifacts and checksums (auto-detects OS/arch if not provided)
	@runner_os="$${RUNNER_OS:-$$(python -c 'import platform; print(platform.system())')}"; \
	 runner_arch="$${RUNNER_ARCH:-$$(python -c 'import platform; print(platform.machine())')}"; \
	 python scripts/release/package_binary.py --runner-os "$$runner_os" --runner-arch "$$runner_arch"

smoke-binary: ## Smoke test built binary (auto-detects OS if not provided)
	@python scripts/release/smoke_binary.py

release: ## Create git tag + GitHub release using gh (TAG=v0.1.0 required)
	@if [ -z "$$TAG" ]; then \
		echo "$(RED)TAG is required. Example: make release TAG=v0.1.0$(NC)"; \
		exit 1; \
	fi; \
	git tag "$$TAG" && gh release create "$$TAG" --generate-notes
