# setup/Makefile
.PHONY: up down restart logs

# List of service directories
SERVICES = lorawan-server persistence Monitor_Atlas Monitor_Hermes

up:
	@echo "🚀 Starting all services..."
	@for service in $(SERVICES); do \
		echo "➡️  Starting $$service..."; \
		docker compose -f $$service/docker-compose.yml up -d || exit 1; \
	done
	@echo "✅ All services are up and running!"

down:
	@echo "🛑 Stopping all services..."
	@for service in $(SERVICES); do \
		echo "⬇️  Stopping $$service..."; \
		docker compose -f $$service/docker-compose.yml down || true; \
	done
	@echo "✅ All services stopped."

restart:
	@$(MAKE) down
	@$(MAKE) up

logs:
	@for service in $(SERVICES); do \
		echo "📜 Logs for $$service:"; \
		docker compose -f $$service/docker-compose.yml logs --tail=20; \
	done

