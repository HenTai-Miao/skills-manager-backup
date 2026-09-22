# Analytics and Monitoring Core

- Layer instrumentation deliberately from event definition to emission points.
- Enforce consent and opt-out behavior.
- Keep canonical event schemas and payload builders.
- Ensure telemetry failures never block primary workflows.
- Prefer server-side capture for key business events; use client events only when UI context is required.
