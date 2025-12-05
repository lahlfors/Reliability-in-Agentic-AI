# Telemetry Manager for OpenTelemetry

import logging
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from vacp.processor import VACPSpanProcessor  # Import the Nervous System

# Configure local logger
logger = logging.getLogger(__name__)

class PIIFilteringExporter(SpanExporter):
    def __init__(self, delegate: SpanExporter):
        self.delegate = delegate

    def export(self, spans):
        for span in spans:
            sanitized_attrs = {}
            for key, value in span.attributes.items():
                if "password" in key.lower() or "token" in key.lower() or "api_key" in key.lower():
                    sanitized_attrs[key] = "[REDACTED]"
                elif isinstance(value, str) and "email" in key.lower():
                     sanitized_attrs[key] = "[REDACTED_EMAIL]"
                else:
                    sanitized_attrs[key] = value

            if hasattr(span, "_attributes"):
                 span._attributes = sanitized_attrs

        return self.delegate.export(spans)

    def shutdown(self):
        self.delegate.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self.delegate.force_flush(timeout_millis)


def setup_telemetry(service_name: str = "financial-advisor-agent"):
    """
    Configures OpenTelemetry with VACP Nervous System (Processor).
    """
    resource = Resource(attributes={
        ResourceAttributes.SERVICE_NAME: service_name
    })

    provider = TracerProvider(resource=resource)

    # 1. Add VACP Processor (The Nervous System)
    # This must run synchronously to block unsafe actions.
    vacp_processor = VACPSpanProcessor()
    provider.add_span_processor(vacp_processor)

    # 2. Add Exporters
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
    filtered_otlp_exporter = PIIFilteringExporter(otlp_exporter)
    provider.add_span_processor(BatchSpanProcessor(filtered_otlp_exporter))

    if os.getenv("OTEL_CONSOLE_EXPORTER", "true").lower() == "true":
        console_exporter = ConsoleSpanExporter()
        filtered_console_exporter = PIIFilteringExporter(console_exporter)
        provider.add_span_processor(BatchSpanProcessor(filtered_console_exporter))

    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry configured with VACP Processor and Exporters.")

    return trace.get_tracer(__name__)
