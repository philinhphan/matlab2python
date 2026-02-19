"""Logfire + Jaeger OpenTelemetry tracing configuration."""

from __future__ import annotations
from openai import AsyncOpenAI


def configure_logfire(service_name: str, openai_client: AsyncOpenAI | None = None) -> None:
    import os
    import logfire

    # Jaeger supports only traces (not metrics). Set only the traces endpoint
    # to avoid export errors for metrics. Port 4318 = OTLP/HTTP (not gRPC 4317).
    os.environ['OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'] = 'http://localhost:4318/v1/traces'

    logfire.configure(
        service_name=service_name,
        send_to_logfire=False,   # Jaeger only; skip Logfire cloud backend
        scrubbing=False,         # Don't redact MATLAB source in span attributes
    )

    # Instrument pydantic-ai globally: produces span tree for each agent.run()
    # (model calls, tool invocations, retries). Must run before create_agent().
    logfire.instrument_pydantic_ai()

    # Instrument the AsyncOpenAI client: captures individual HTTP requests,
    # token counts, latencies.
    if openai_client is not None:
        logfire.instrument_openai(openai_client)
