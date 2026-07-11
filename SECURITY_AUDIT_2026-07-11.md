# Road Hawk Security Audit — 2026-07-11

## Scope

Static security review of the active Road Hawk FastAPI, SQLite, document-intake, authentication, and network-deployment paths on branch `Road-Hawk`.

## Validated findings

### RH-RH-001 — Unauthenticated all-interface API exposure

**Severity:** High

The default API host was `0.0.0.0`, while authentication was disabled unless `ROAD_HAWK_AUTH_REQUIRED` was explicitly enabled. A normal launch could therefore expose trip, driver, truck, maintenance, document, export, chain-user, and compensation-plan endpoints to the local network without authentication.

**Fix:** The default bind is now `127.0.0.1`. Authentication is automatically required whenever Road Hawk runs in server mode or binds to a non-loopback address. An explicit false-like environment value cannot override that fail-closed boundary.

### RH-RH-002 — Remote first-user bootstrap takeover

**Severity:** High

The first-user bootstrap endpoint was public and accepted a caller-selected administrative role. On a fresh remotely exposed instance, the first requester could create the initial administrator and take control of the application.

**Fix:** First-user creation through the API is blocked whenever authentication is required. Remote servers must provision the first administrator through `ROAD_HAWK_ADMIN_USER` and `ROAD_HAWK_ADMIN_PASSWORD` before accepting logins.

### RH-RH-003 — Development reloader enabled in normal starts

**Severity:** Medium

The Uvicorn development reloader was enabled unconditionally. Reload mode is inappropriate for a remotely reachable or production-like deployment and expands process and file-watching behavior.

**Fix:** Reload is disabled by default, requires `ROAD_HAWK_RELOAD=1`, and is refused on non-loopback binds.

### RH-RH-004 — Uploaded document processing is not size bounded

**Severity:** Medium

Document and CSV upload endpoints do not currently impose a hard application-level byte limit before storage and PDF/OCR processing. Large or adversarial uploads can consume disk, memory, CPU, and OCR/PDF-processing time.

**Status:** Open. Add request and decompressed-document limits, PDF page limits, image dimension limits, and cleanup of partial records/files before exposing document intake beyond a trusted local environment.

### RH-RH-005 — Roles are recorded but not enforced per operation

**Severity:** Medium

Road Hawk defines driver, broker, dispatcher, spouse, accountant, and administrator roles, but the HTTP middleware currently checks only whether a token is valid. Any authenticated role can reach all protected API operations, including exports, document access, chain-user changes, and deletions.

**Status:** Open pending an explicit authorization matrix. Do not expose multi-user server mode to untrusted users until route-level role rules are defined and tested.

### RH-RH-006 — Login endpoint lacks application rate limiting

**Severity:** Medium when remotely exposed

The username/password login endpoint has no application or documented edge rate limit. Remote deployments should enforce rate limiting and failed-login monitoring.

**Status:** Open. Add an application limiter or a reverse-proxy/edge rule before Internet exposure.

## Verification added

Focused tests now verify:

- the default bind is loopback;
- non-loopback binds force authentication;
- server mode forces authentication even when the bind is loopback;
- remote first-user API bootstrap is rejected;
- environment-provisioned administrators can log in and access protected endpoints;
- development reload is local-only and opt-in.

GitHub Actions runs these tests on pull requests and pushes to `Road-Hawk`.

## Deployment rule

Road Hawk is safe by default for local standalone use. Remote/server operation requires deliberate administrator provisioning, trusted CORS origins, TLS through a reverse proxy or secure tunnel, upload limits, rate limiting, and a defined role-authorization matrix.
