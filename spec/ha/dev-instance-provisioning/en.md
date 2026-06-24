# HA Integration: Dev Instance Provisioning

Status: draft

## Context

`ha/dev-environment` governs the dev loop (deploy via `kubectl cp`, `kill 1` restart, verify) but **presupposes a running HA instance** — cluster setup and provisioning the instance are explicitly its non-goals. In practice that instance is regularly missing: a fresh Kind cluster has no HA pod, and not every setup ships a pre-installed `homeassistant` Helm chart. Without an instance the whole deploy choreography fails at its first precondition.

`nolte/kamerplanter-ha` first solved this project-specifically via a local skill plus a raw StatefulSet manifest. This spec lifts the pattern to the plugin level: **provisioning a disposable dev HA instance** via a raw Kubernetes manifest, generic across HA integrations, as the prerequisite for `ha/dev-environment`.

Quality-scale marker: **unscaled** (dev tooling is not part of the HA quality scale; the pattern is nolte-portfolio-specific).

## Goals

- Provision a disposable HA dev instance in the local cluster **without** presupposing a pre-installed Helm chart — a raw manifest as the default
- Shape the instance so the deploy/verify choreography from `ha/dev-environment` runs on it unchanged (same label selector, stable pod name, `/config` layout)
- Prepare the `kubectl cp` destination path so the first deploy does not fail on a missing directory
- Define idempotent provisioning and a clean teardown

## Non-Goals

- The dev loop itself (deploy, `kill 1` restart, verify) — governed by `ha/dev-environment`
- Helm chart authoring and production deployment — the raw manifest mechanic is explicitly for local dev loops
- Cluster setup (installing/configuring Kind) — a prerequisite, not output
- HA configuration content (`configuration.yaml`, integration YAML) beyond first-start bootstrap — user-specific
- Reverse proxy / ingress / TLS for the dev instance — access runs through `kubectl port-forward`

## Requirements

### Workload shape

- **MUST** provision the instance as a **StatefulSet** with a stable pod name (`<name>-0`) — the stable name allows `kubectl cp`/`kubectl exec` without dynamic pod resolution and survives `kill 1` restarts
- **MUST** set the label `app.kubernetes.io/name=homeassistant` (or the portfolio-conventional selector) so the deploy/verify choreography from `ha/dev-environment` finds the pod
- **MUST** persist `/config` via a `volumeClaimTemplate`, so onboarding state and the copied integration survive restarts
- **MUST** provide a ClusterIP service on port 8123 — UI access via `kubectl port-forward`
- **SHOULD** use the official image `ghcr.io/home-assistant/home-assistant:stable`, overridable via input
- **SHOULD** derive the `storageClassName` at runtime from the cluster's default StorageClass, overridable via input

### Minimal configuration

- **MUST NOT** pre-populate a `configuration.yaml` — HA generates a default configuration with `default_config:` on first start, which suffices for config flow and entities
- **MUST NOT** set up ingress, auth providers or TLS — dev access runs through `kubectl port-forward`
- **MAY** set convenience env (e.g. `TZ`)

### Bootstrap for the deploy loop

- **MUST** create the directory `/config/custom_components` (`mkdir -p`) once the instance is ready — otherwise the deploy choreography's first `kubectl cp <…>:/config/custom_components/<domain>` fails on the missing parent directory
- **SHOULD** print the `port-forward` command and the follow-up step (deploy choreography from `ha/dev-environment`) as a hint after provisioning

### Idempotency and teardown

- **MUST** keep provisioning idempotent (`kubectl apply`) — a re-run leaves a running instance and its `/config` PVC untouched
- **MUST** offer a teardown path that removes the StatefulSet, the service **and** the `/config` PVC — the PVC is not deleted automatically when the StatefulSet is removed
- **MUST NOT** delete the pod for a mere code refresh — that is `kill 1` from `ha/dev-environment`; `kubectl delete` is reserved for the full teardown

### Restart compatibility

- **MUST** presuppose an image whose PID 1 (s6-overlay in the official image) cleanly restarts the HA process on `SIGTERM` — the precondition for `kubectl exec <pod> -- kill 1` from `ha/dev-environment` to work as a restart without losing pod and PVC

## Acceptance Criteria

- [ ] Provision creates a StatefulSet `<name>` (pod `<name>-0`), a service and a `/config` PVC
- [ ] The pod carries the label `app.kubernetes.io/name=homeassistant`
- [ ] `/config` survives `kill 1` restarts
- [ ] `/config/custom_components` exists after provisioning
- [ ] A repeated provision run is idempotent (no data loss)
- [ ] Teardown removes the StatefulSet, service and PVC
- [ ] No Helm chart is presupposed
- [ ] Quality-scale marker: **unscaled** (portfolio-specific)

## Open Questions

- **Helm variant**: should a Helm-based variant be addressed alongside the raw manifest once a portfolio standard chart is settled (see the open question in `ha/dev-environment`)?
- **Multiple parallel instances**: how are several dev loops run side by side — via namespace separation or a name suffix? Currently assumed single-instance.
- **Readiness robustness**: the HTTP readiness probe on `/` is HA-version-dependent; a more stable endpoint contract is open.
