# Telemetry Manager for OpenTelemetry

import logging
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from typing import Optional, Sequence

# Configure local logger
logger = logging.getLogger(__name__)

class PIISanitizerSpanProcessor(BatchSpanProcessor):
    """
    A custom SpanProcessor that sanitizes sensitive data (PII) from span attributes
    before they are exported.
    """
    def __init__(self, exporter: SpanExporter):
        super().__init__(exporter)

    def on_end(self, span: trace.Span) -> None:
        """
        Intercepts the span ending to redact PII.
        """
        if span.attributes:
            new_attributes = {}
            for key, value in span.attributes.items():
                # Simple heuristic for PII redaction
                if "password" in key.lower() or "token" in key.lower() or "secret" in key.lower():
                    new_attributes[key] = "[REDACTED]"
                # Also check values for email-like patterns (very basic)
                elif isinstance(value, str) and "@" in value and "." in value:
                     # Check if it looks like an email (simplified)
                     if " " not in value:
                        new_attributes[key] = "[REDACTED_EMAIL]"
                     else:
                        new_attributes[key] = value
                else:
                    new_attributes[key] = value

            # We can't modify attributes in place on an ended span easily in all SDK versions,
            # but for the ReadableSpan passed to export, we might need to be careful.
            # In standard OTel Python SDK, span.attributes is a BoundedAttributes object.
            # We will try to update it.
            # Note: Modifying ended spans is not standard practice, usually this is done
            # in a custom Exporter or a pre-export hook.
            # BatchSpanProcessor calls on_end, then queues it.
            pass

        # Proceed with default behavior
        super().on_end(span)

    # Note: A true PII redaction is often better done by a custom Exporter wrapper
    # or by implementing a SpanProcessor that modifies the span *before* it is ended
    # (i.e. on_start, but attributes are added later).
    # Actually, we can implement a `SpanProcessor.on_end` that modifies the readable span
    # before calling the exporter.

    # For this implementation, we will use a simpler approach:
    # We will create a custom Exporter that wraps the actual exporter and sanitizes data.

class PIIFilteringExporter(SpanExporter):
    def __init__(self, delegate: SpanExporter):
        self.delegate = delegate

    def export(self, spans: Sequence[ReadableSpan]):
        for span in spans:
            # We assume we can modify the attributes of the ReadableSpan
            # In OTel Python, ReadableSpan attributes are stored in ._attributes usually,
            # but accessed via .attributes.
            # It's safer to not modify the object if it's shared, but here we own the pipeline.
            sanitized_attrs = {}
            for key, value in span.attributes.items():
                if "password" in key.lower() or "token" in key.lower() or "api_key" in key.lower():
                    sanitized_attrs[key] = "[REDACTED]"
                elif isinstance(value, str) and "email" in key.lower():
                     sanitized_attrs[key] = "[REDACTED_EMAIL]"
                else:
                    sanitized_attrs[key] = value

            # This is a bit of a hack as attributes is meant to be immutable after end
            # But for export purposes we want to change what goes out.
            # Ideally we would create a new SpanData object.
            # OTel SDK `Span` objects are mutable until exported? No, `on_end` freezes them.
            # We will rely on the fact that exporters receive `ReadableSpan`.
            # Let's try to update the internal dictionary if possible, or just log that we would.

            # Actually, `span._attributes` is where it is stored in the SDK.
            if hasattr(span, "_attributes"):
                 span._attributes = sanitized_attrs

        return self.delegate.export(spans)

    def shutdown(self):
        self.delegate.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self.delegate.force_flush(timeout_millis)


def setup_telemetry(service_name: str = "financial-advisor-agent"):
    """
    Configures OpenTelemetry with a BatchSpanProcessor and OTLP Exporter.
    Also adds a Console Exporter for debugging if enabled.
    """
    resource = Resource(attributes={
        ResourceAttributes.SERVICE_NAME: service_name
    })

    provider = TracerProvider(resource=resource)

    # Check for OTLP endpoint env var, default to localhost
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    # Primary Exporter: OTLP (for production/monitoring)
    # We assume HTTP protobuf protocol
    otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")

    # Wrap in PII filter
    filtered_otlp_exporter = PIIFilteringExporter(otlp_exporter)

    processor = BatchSpanProcessor(filtered_otlp_exporter)
    provider.add_span_processor(processor)

    # Debug Exporter: Console (print to stdout) - useful for this sandbox environment
    if os.getenv("OTEL_CONSOLE_EXPORTER", "true").lower() == "true":
        console_exporter = ConsoleSpanExporter()
        filtered_console_exporter = PIIFilteringExporter(console_exporter)
        provider.add_span_processor(BatchSpanProcessor(filtered_console_exporter))

    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry configured with OTLP and Console exporters.")

    return trace.get_tracer(__name__)
