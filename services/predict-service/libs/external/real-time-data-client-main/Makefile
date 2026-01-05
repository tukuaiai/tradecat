.PHONY: build
build:
	@echo "Building ts code..."
	rm -rf dist
	yarn tsc --module commonjs

.PHONY: lint
lint:
	@echo "Linting code..."
	./node_modules/.bin/eslint ./src --ext .js,.ts