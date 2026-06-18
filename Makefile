SHELL := /bin/bash

.PHONY: quality-precommit quality-backend quality-user quality-agency quality-admin quality-workers quality-model-service quality-ci quality-rag-eval docker-quality-backend docker-quality-admin docker-quality-workers docker-quality-model-service

quality-precommit:
	./scripts/quality/precommit.sh

quality-backend:
	./scripts/quality/backend.sh

quality-user:
	./scripts/quality/user.sh

quality-agency:
	./scripts/quality/agency.sh

quality-admin:
	./scripts/quality/admin.sh

quality-workers:
	./scripts/quality/workers.sh

quality-model-service:
	./scripts/quality/model_service.sh

quality-ci:
	./scripts/quality/ci.sh

quality-rag-eval:
	./scripts/quality/rag_eval.sh

docker-quality-backend:
	./scripts/quality/docker_backend.sh

docker-quality-admin:
	./scripts/quality/docker_admin.sh

docker-quality-workers:
	./scripts/quality/docker_workers.sh

docker-quality-model-service:
	./scripts/quality/docker_model_service.sh
