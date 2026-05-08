# HA Integration: Dev Environment

Status: draft

## Context

A Custom Integration is code that lives inside a running HA instance. Local development without a real HA instance in the loop produces friction — pytest covers structural tests (see `ha/test-harness`), but frontend behaviour, lifecycle bugs, setup race conditions, and Lovelace card rendering need the real instance. The nolte portfolio uses a **Kubernetes-based dev loop** for that: a local Kind cluster with the `homeassistant` Helm chart, into which Custom Integration code is mirrored via `kubectl cp`.

`nolte/kamerplanter-ha` extracted the deploy choreography into `Taskfile.yml` targets (`task deploy-ha`, `task verify-ha`) in commit `f4c24fb (2026-04-24 "refactor(skills): extract HA deploy/verify steps into Taskfile")`. The critical insight behind it: **`kubectl exec ... -- kill 1` is the correct restart mechanism, NOT `kubectl delete pod`**. On `delete pod`, the init container runs again and overwrites the files copied via `kubectl cp` — the change disappears silently. `kill 1` only restarts the HA main process inside the existing container, so the copied files survive.

This spec lifts the pattern into a generic obligation. It defines the deploy choreography, the verify choreography (pod-status check, log scan, error detection), the mandatory cache cleanup (`__pycache__`), and the variables a skill expects for `task deploy-ha` / `task verify-ha` by default.

Quality scale marker: **unscaled** (dev environment is not part of the HA quality scale; the pattern is nolte-portfolio-specific).

## Goals

- Establish Kind cluster + `homeassistant` Helm chart as the standard dev stack — fast iteration without real-HA restart trauma
- Establish `kubectl cp` as the deployment mechanism — files land directly in the container, no image builds required
- Mandate `kill 1` instead of `kubectl delete pod` as the restart mechanism — prevents silent overwrite by the init container
- Make bytecode-cache cleanup (`__pycache__`) a mandatory step before every restart, so Python does not load stale `.pyc` files
- Define a verify choreography that runs pod status, log tail, and error detection automatically after every deploy
- Establish Taskfile-based choreography as the only entry point — no ad-hoc `kubectl` commands in onboarding docs

## Non-Goals

- Container-image build / Helm-chart authoring — external building blocks, not skill output
- HA configuration of the test instance itself (`configuration.yaml`, integrations YAML, etc.) — user-specific, beyond the Custom Integration
- Production deployment — the `kubectl cp` mechanism is explicitly for local dev loops; production runs through regular HA add-on distribution or HACS
- Local Python-venv setup for pytest — see `ha/test-harness` and `nolte-shared:project-structure`
- Multi-cluster workflows (staging cluster, cloud cluster) — separate follow-up spec once the first integration concretely needs them
- VS Code / IDE integrations — tooling-specific

## Requirements

### Cluster precondition

- **MUST** assume a local Kind cluster (or equivalent local K8s cluster) with the `homeassistant` Helm chart installed — the spec does not address cluster setup, only the dev loop on top
- **MUST** locate the HA pod via label selector — typical convention: `app.kubernetes.io/name=homeassistant` or a comparable Helm-chart-standard selector
- **SHOULD** expose cluster, namespace, and pod-selector values as `Taskfile.yml` variables, so users can override them per cluster

### Taskfile variables

- **MUST** set the following variables in `Taskfile.yml` (or an included tasks file) by default:
  - `NAMESPACE` — typically `default`
  - `POD_SELECTOR` — typically `app.kubernetes.io/name=homeassistant`
  - `LOCAL_PATH` — the local Custom Integration path, typically `custom_components/<domain>/`
  - `REMOTE_PATH` — the HA `/config` path, typically `/config/custom_components/<domain>`
- **SHOULD** resolve the pod name dynamically from the selector (`kubectl get pod -n {{.NAMESPACE}} -l {{.POD_SELECTOR}} -o jsonpath='{.items[0].metadata.name}'`) — hard-coded pod names break as soon as the pod is restarted
- **MAY** introduce additional variables for convention extensions (for example `CONTEXT` for multi-cluster setup, `LOG_TAIL_LINES` for verify variant)

### Deploy choreography (`task deploy-ha`)

- **MUST** run the deploy in this order:
  1. **Pre-lint**: `task lint` — prevents deploys of broken code
  2. **Local cache cleanup**: delete local `__pycache__` if present — otherwise stale bytecode lands during the copy
  3. **File copy**: `kubectl cp <LOCAL_PATH> <NAMESPACE>/<POD>:<REMOTE_PATH>` — files land directly in the running container
  4. **Remote cache cleanup**: `kubectl exec <POD> -n <NAMESPACE> -- rm -rf <REMOTE_PATH>/__pycache__` — mandatory step; otherwise Python loads stale bytecode on restart
  5. **HA-process restart**: `kubectl exec <POD> -n <NAMESPACE> -- kill 1` — restarts only the HA main process without destroying the container
  6. **Wait-on-ready**: short wait until HA responds again (typically 5–15 s; via health endpoint or simple sleep)
  7. **Log tail**: `kubectl logs <POD> -n <NAMESPACE> --tail=200` — directly after the restart so setup errors surface immediately
- **MUST NOT** use `kubectl delete pod` as the restart mechanism — the init container would run again and overwrite the files copied via `kubectl cp`; the change would silently disappear
- **MUST NOT** skip the cache cleanup step — Python bytecode caching can load stale `.pyc` files, which leads to false positives during bug hunts

### Verify choreography (`task verify-ha`)

- **MUST** carry a separate Taskfile target `task verify-ha` that diagnoses status without deploying
- **MUST** run in this order:
  1. **Pod status**: `kubectl get pod <POD> -n <NAMESPACE> -o wide` — shows phase, restarts, age
  2. **Log tail (last 5 min)**: `kubectl logs <POD> -n <NAMESPACE> --since=5m` — fresh output without boilerplate
  3. **Error scan**: filter the log for `ERROR`, `Traceback`, `Exception`, `Failed to set up` and emit only matches — typically via `kubectl logs ... | grep -E "ERROR|Traceback|Exception|Failed to set up"`
  4. **Installed files**: `kubectl exec <POD> -n <NAMESPACE> -- ls -la <REMOTE_PATH>` — confirms that the last `kubectl cp` placed the right files in the right location
- **SHOULD** additionally run a health endpoint check when HA exposes one (`/api/`, `/`, `/auth/providers`)

### Bytecode-cache discipline

- **MUST** delete local `<LOCAL_PATH>/__pycache__` and `<LOCAL_PATH>/**/__pycache__` before every deploy — otherwise stale `.pyc` files land in the container
- **MUST** delete remote `<REMOTE_PATH>/__pycache__` after `kubectl cp` and before `kill 1` — the Python import machinery caches aggressively and otherwise loads old bytecode
- **MAY** use a targeted mtime-check-based cleanup instead of `rm -rf __pycache__` if the cleanup action becomes slow; the simple `rm -rf` is enough at the size of a Custom Integration

### Restart mechanism

- **MUST** use `kubectl exec <POD> -n <NAMESPACE> -- kill 1` as the only restart command in the deploy loop
- **MUST NOT** use `kubectl delete pod`, `kubectl rollout restart`, or Helm `upgrade --force` — all three destroy the running container and trigger the init container, which typically re-populates `/config` from a different mount and loses the Custom Integration files copied via `kubectl cp` in the process
- **SHOULD** explicitly document the `kill 1` vs. `delete pod` distinction in skill-output docs (for example the consuming integration's `CLAUDE.md`) — new contributors otherwise fall into the same trap regularly

### CI delineation

- **MUST NOT** run the Kind-cluster loop in CI — CI uses the pytest-based test harness (see `ha/test-harness`); the Kind loop is intended for interactive dev
- **MAY** carry a separate CI job for E2E tests against an ephemeral Kind cluster — separate follow-up spec

## Acceptance Criteria

- [ ] `Taskfile.yml` (or an included tasks file) carries a `deploy-ha` target
- [ ] `Taskfile.yml` carries a `verify-ha` target
- [ ] Variables `NAMESPACE`, `POD_SELECTOR`, `LOCAL_PATH`, `REMOTE_PATH` are defined as top-level `vars:`
- [ ] `deploy-ha` runs in this order: lint → local cache cleanup → `kubectl cp` → remote cache cleanup → `kill 1` → wait → log tail
- [ ] `deploy-ha` contains **no** `kubectl delete pod` invocation
- [ ] `verify-ha` runs: pod status → log tail (`--since=5m`) → error scan → installed-files check
- [ ] `CLAUDE.md` (or equivalent dev docs) of the consuming integration documents the `kill 1` vs. `delete pod` rule
- [ ] CI pipeline does **not** invoke the Kind-cluster loop — pytest test harness runs separately
- [ ] Quality scale marker: **unscaled** (portfolio-specific)

## Open Questions

- **Helm-chart convention**: Which concrete `homeassistant` Helm chart is preferred portfolio-wide? Currently referenced as "the Helm chart"; a concrete source (for example `bjw-s/app-template` with a values-yaml snippet) would make the spec more concrete.
- **Wait-on-ready mechanics**: `sleep 10` is primitive but reliable; health-endpoint polling would be more elegant but is HA-version-dependent. Should the spec pin a variant?
- **Multi-pod setups**: What happens when the HA pod is a StatefulSet with multiple replicas? Currently assumed single-pod; rare in practice but conceptually open.
- **Linux / macOS / Windows platform dependency**: `kubectl cp` and `kubectl exec ... -- kill 1` work cross-platform, but the wait mechanic (for example `sleep`) varies. Currently not addressed.
- **`docker compose` variant**: Some users develop against a `docker-compose`-based HA instead of Kind. Should the spec address a second variant or stay Kind-only?
