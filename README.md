[![CI](https://github.com/vturrojas/quota-ledger/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/vturrojas/quota-ledger/actions/workflows/tests.yml)

# QuotaLedger (event-sourced)

A small, production-style event-sourced service for **account quotas & rate plans**.

---

## What this is

QuotaLedger is a small, production-style **event-sourced** service that models a boring-but-real domain:
an account’s plan + usage over time, with explicit invariants and an append-only event log.

It’s intentionally modest in scope. The goal is to demonstrate correctness, auditability, and replayable state
— not to build distributed streaming infrastructure.

---

## Non-goals

- Kafka/CDC/distributed streaming
- microservices sprawl
- billing, proration, invoices, payments
- async projector workers (kept transactional for clarity)

---

## Why event sourcing (here)

This domain benefits from an immutable history:

- **Auditability:** every state change (create, usage, suspend, reinstate) is recorded as an event.
- **Correctness over time:** current state is derived from events, not overwritten in-place.
- **Safe retries:** commands can be retried without duplicating writes (idempotency).
- **Rebuildable reads:** projections can be rebuilt from the event log.

In a real system, I would not default to event sourcing. I’m using it here because the project’s purpose
is to show clear reasoning about invariants and state reconstruction.

---

## When event sourcing is a bad idea

Event sourcing adds real complexity. I would avoid it when:

- You don’t need an audit trail or historical reconstruction.
- The domain rules are simple and CRUD is sufficient.
- The team isn’t prepared to own event versioning and projection maintenance.
- You need ad-hoc relational queries over the “current state” and don’t want projections.
- The performance profile doesn’t justify the additional moving parts.

For many applications, a conventional relational model with carefully designed tables, constraints, and
audit columns is simpler and more maintainable.

---

## Architecture (scaled down)

- **Source of truth:** `events` table (append-only).
- **Writes:** command → decide() → append events (optimistic concurrency + idempotency).
- **Reads:**
  - `GET /v1/accounts/{id}` prefers a projection (`account_current`) for fast reads
  - falls back to replay for correctness and rebuildability.
- **Projection:** updated transactionally in the same DB transaction as event append (small-scale choice).
- **Idempotency:** write operations support safe retries via an Idempotency-Key scoped to an account stream.

---

## Invariants

This service enforces a few explicit domain rules:

- You cannot record usage for an account that does not exist.
- You cannot record usage when the account is **suspended**.
- (More rules could be added later: plan limits, period rollover, etc.)

---

## Design decisions

- Commands raise domain-specific errors (`NotFound`, `InvariantViolation`)
  instead of generic exceptions.
- Invariants are enforced in the domain layer, not the API layer.
- Projections are updated transactionally for simplicity and correctness.

---

## What this does NOT demonstrate

This project does not attempt to demonstrate horizontal scalability, cross-service messaging,
or distributed consistency. It focuses deliberately on correctness, clarity, and maintainability
within a single service boundary.

---

## API quickstart

Create an account:

```bash
curl -s -X POST http://127.0.0.1:8001/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"account_id":"a1","initial_plan_id":"basic","period":"2026-01"}' | jq
```

Record usage (idempotent via Idempotency-Key):

```bash
curl -s -X POST http://127.0.0.1:8001/v1/accounts/a1/usage \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: u1" \
  -d '{"meter":"api_calls","units":5,"occurred_at":"2026-01-28T01:10:00Z"}' | jq
```

Suspend and verify invariant:

```bash
curl -s -X POST http://127.0.0.1:8001/v1/accounts/a1/suspend \
  -H "Content-Type: application/json" \
  -d '{"reason":"manual"}' | jq

curl -i -s -X POST http://127.0.0.1:8001/v1/accounts/a1/usage \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: u2" \
  -d '{"meter":"api_calls","units":1,"occurred_at":"2026-01-28T01:12:00Z"}'
```

List events (audit trail):

```bash
curl -s http://127.0.0.1:8001/v1/accounts/a1/events | jq
```

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
make test

---

## Tradeoffs

- **Projection maintenance:** This demo updates projections transactionally during writes. This keeps the system
  simple and consistent, but couples write throughput to projection work.
- **Replay fallback:** Reads can always fall back to replay, which is correct but slower for long streams.
- **No distributed infra:** No Kafka, no CDC, no async projection workers. This is a deliberate choice to keep the
  project small and readable.
