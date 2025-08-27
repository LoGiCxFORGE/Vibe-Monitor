
import os
import time
import random
import asyncio
import logging
from fastapi import FastAPI, Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/app.log")],
)
logger = logging.getLogger("fastapi-app")

app = FastAPI()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Histogram of request latency (seconds)",
    ["endpoint"],
    buckets=(0.1, 0.25, 0.5, 1, 2, 5),
)

trace.set_tracer_provider(
    TracerProvider(resource=Resource.create({"service.name": "fastapi-app"}))
)
tracer = trace.get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

FastAPIInstrumentor.instrument_app(app)

@app.get("/hello")
async def hello(request: Request):
    start = time.perf_counter()
    delay = random.uniform(0.1, 1.0)
    await asyncio.sleep(delay)  # non-blocking

    duration = time.perf_counter() - start
    status_code = 200

    REQUEST_COUNT.labels(request.method, "/hello", status_code).inc()
    REQUEST_LATENCY.labels("/hello").observe(duration)

    logger.info(f"/hello delay={delay:.3f}s duration={duration:.3f}s")

    span = trace.get_current_span()
    span.set_attribute("app.delay_seconds", delay)
    span.set_attribute("app.duration_seconds", duration)

    return {"message": "Hello, Observability!", "delay": delay}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)