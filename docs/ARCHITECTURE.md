# Architecture

## Layers

- `backend/app/api`: HTTP contracts for public and worker traffic
- `backend/app/services`: business rules, auth, seeding, and orchestration support
- `backend/app/repositories`: persistence boundaries
- `backend/app/models`: relational entities
- `worker/app/pipelines`: modular AI stages
- `frontend/src`: operational dashboard UI

## Scale Pattern

- API and worker replicas scale independently
- Queue state is persisted in the database
- Internal worker endpoints are protected by a shared internal API key
- Frontend is statically served and can sit behind an ingress or CDN

