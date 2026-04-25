# Docker Packaging Notes

- Each service has its own Dockerfile alongside the service code.
- `docker-compose.yml` at the repository root wires the services together for local deployment.
- The images are built from the repo root so shared `libs/` code is available in every container.

