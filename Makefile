# Makefile
.PHONY: help install dev build prod clean

help:
	@echo "Kenya Election Tracker - Available Commands"
	@echo ""
	@echo "make install     - Install all dependencies"
	@echo "make dev         - Start development environment"
	@echo "make build       - Build for production"
	@echo "make prod        - Start production environment"
	@echo "make clean       - Clean build artifacts"
	@echo "make test        - Run tests"
	@echo "make migrate     - Run database migrations"
	@echo "make seed        - Seed database with sample data"

install:
	@echo "Installing dependencies..."
	./setup.sh

dev:
	@echo "Starting development environment..."
	@echo "Starting backend..."
	cd backend && source venv/bin/activate && python manage.py runserver &
	@echo "Starting frontend..."
	cd frontend && npm start &

build:
	@echo "Building for production..."
	cd frontend && npm run build
	cd backend && python manage.py collectstatic --noinput

prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d --build

clean:
	@echo "Cleaning build artifacts..."
	rm -rf frontend/build
	rm -rf backend/static
	rm -rf backend/media
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	rm -rf .venv

migrate:
	@echo "Running migrations..."
	cd backend && python manage.py makemigrations && python manage.py migrate

seed:
	@echo "Seeding database..."
	cd backend && python manage.py loaddata ../data/seed/initial_data.json

test:
	@echo "Running tests..."
	cd backend && python manage.py test
	cd frontend && npm test

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down