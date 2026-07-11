# Cloud Run Service Configs

Populated incrementally as workers come online: `agent-worker` config stub in Sprint 8, `document-worker`/`embedding-worker` stubs in Sprint 5, full production configs for all five services (`revnara-api`, `revnara-agent-worker`, `revnara-connector-worker`, `revnara-document-worker`, `revnara-notification-worker`) in Sprint 15. All five share the backend's one Docker image with different startup commands (`docs/Revnara_Implementation_Plan.md` §14).

Requires a GCP project (§4 Environment Prerequisites) — not provisioned yet.
