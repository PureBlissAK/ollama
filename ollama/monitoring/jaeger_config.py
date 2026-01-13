"""
Jaeger Tracing Configuration and Integration
Distributes tracing context across microservices
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


class JaegerConfig:
    """Jaeger tracing configuration"""

    def __init__(
        self,
        service_name: str = "ollama-api",
        jaeger_host: str = "jaeger",
        jaeger_port: int = 6831,
        jaeger_udp_port: int = 6831,
        trace_sample_rate: float = 0.1,
    ):
        """
        Initialize Jaeger configuration

        Args:
            service_name: Service name for traces
            jaeger_host: Jaeger agent host
            jaeger_port: Jaeger agent port
            jaeger_udp_port: Jaeger UDP port (for Thrift protocol)
            trace_sample_rate: Fraction of traces to sample (0.0-1.0)
        """
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.jaeger_udp_port = jaeger_udp_port
        self.trace_sample_rate = trace_sample_rate
        self._tracer_provider: Optional[TracerProvider] = None

    def initialize_tracer(self) -> TracerProvider:
        """
        Initialize Jaeger tracer provider

        Returns:
            Configured TracerProvider
        """
        try:
            # Create Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_udp_port,
            )

            # Create tracer provider
            trace_provider = TracerProvider()

            # Add Jaeger exporter
            trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

            # Set global tracer provider
            trace.set_tracer_provider(trace_provider)

            self._tracer_provider = trace_provider
            logger.info(f"✅ Jaeger tracer initialized: {self.jaeger_host}:{self.jaeger_port}")

            return trace_provider

        except Exception as e:
            logger.error(f"❌ Failed to initialize Jaeger tracer: {e}")
            raise

    def instrument_fastapi(self, app):
        """
        Instrument FastAPI app for tracing

        Args:
            app: FastAPI application instance
        """
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("✅ FastAPI instrumented for tracing")
        except Exception as e:
            logger.error(f"⚠️  Failed to instrument FastAPI: {e}")

    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy for tracing

        Args:
            engine: SQLAlchemy engine
        """
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine, service=self.service_name)
            logger.info("✅ SQLAlchemy instrumented for tracing")
        except Exception as e:
            logger.error(f"⚠️  Failed to instrument SQLAlchemy: {e}")

    def instrument_httpx(self):
        """
        Instrument httpx for tracing
        """
        try:
            HTTPXClientInstrumentor().instrument()
            logger.info("✅ httpx instrumented for tracing")
        except Exception as e:
            logger.error(f"⚠️  Failed to instrument httpx: {e}")

    def instrument_redis(self):
        """
        Instrument Redis for tracing
        """
        try:
            RedisInstrumentor().instrument()
            logger.info("✅ Redis instrumented for tracing")
        except Exception as e:
            logger.error(f"⚠️  Failed to instrument Redis: {e}")

    def get_tracer(self, name: str) -> trace.Tracer:
        """
        Get tracer instance

        Args:
            name: Tracer name (usually __name__)

        Returns:
            Tracer instance
        """
        if self._tracer_provider is None:
            self.initialize_tracer()

        return trace.get_tracer(name)


# Global Jaeger config instance
_jaeger_config: Optional[JaegerConfig] = None


def init_jaeger(
    service_name: str = "ollama-api",
    jaeger_host: str = "jaeger",
    jaeger_port: int = 6831,
    trace_sample_rate: float = 0.1,
) -> JaegerConfig:
    """
    Initialize Jaeger configuration

    Args:
        service_name: Service name
        jaeger_host: Jaeger host
        jaeger_port: Jaeger port
        trace_sample_rate: Sample rate

    Returns:
        JaegerConfig instance
    """
    global _jaeger_config
    _jaeger_config = JaegerConfig(
        service_name=service_name,
        jaeger_host=jaeger_host,
        jaeger_port=jaeger_port,
        trace_sample_rate=trace_sample_rate,
    )
    return _jaeger_config


def get_jaeger_config() -> Optional[JaegerConfig]:
    """
    Get global Jaeger config instance

    Returns:
        JaegerConfig or None if not initialized
    """
    return _jaeger_config
