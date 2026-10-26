"""Export a steplot Run as OpenTelemetry spans.

Requires the optional ``opentelemetry-sdk`` package — not a steplot runtime
dependency. Install it separately (``pip install opentelemetry-sdk``) to use
this module; everything else in steplot works without it.
"""

from __future__ import annotations

from typing import Any

from .models import Run, Step


def _nanos(dt: Any) -> int:
    return int(dt.timestamp() * 1_000_000_000)


def to_otel_spans(run: Run, tracer: Any = None) -> None:
    """Export every Step in ``run`` as an OpenTelemetry span.

    Builds one root span for the run and one child span per Step, preserving
    the same parent/child nesting and using each Step's recorded start/end
    timestamps (rather than the current time). Failed steps get their error
    recorded as a span attribute. Requires a configured OpenTelemetry
    TracerProvider with an exporter attached — this function does not set
    one up; it only emits spans through the ``tracer`` you provide (or the
    globally configured one).

    Args:
        run: The Run to export.
        tracer: An OpenTelemetry tracer. Defaults to
            ``trace.get_tracer("steplot")`` using the global TracerProvider.

    Raises:
        RuntimeError: If ``opentelemetry-sdk`` is not installed.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.trace import set_span_in_context
    except ImportError as exc:
        raise RuntimeError(
            "to_otel_spans requires the 'opentelemetry-sdk' package: pip install opentelemetry-sdk"
        ) from exc

    tracer = tracer or trace.get_tracer("steplot")

    def walk(step: Step, parent_ctx: Any) -> None:
        span = tracer.start_span(step.name, context=parent_ctx, start_time=_nanos(step.started_at))
        span.set_attribute("steplot.status", step.status.value)
        if step.error:
            span.set_attribute("steplot.error", step.error)
        if step.skip_reason:
            span.set_attribute("steplot.skip_reason", step.skip_reason)
        ctx = set_span_in_context(span)
        for child in step.children:
            walk(child, ctx)
        span.end(end_time=_nanos(step.ended_at) if step.ended_at else None)

    root_start = _nanos(run.started_at)
    root = tracer.start_span(f"run:{run.name}", start_time=root_start)
    root_ctx = set_span_in_context(root)
    for step in run.steps:
        walk(step, root_ctx)
    root.end(end_time=_nanos(run.ended_at) if run.ended_at else None)
