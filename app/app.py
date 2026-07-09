import random
import time

from flask import Flask, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_requests_total", "Total number of requests received", ["endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds", "Request latency in seconds", ["endpoint"]
)
ACTIVE_SESSIONS = Gauge(
    "app_active_sessions", "Number of currently active sessions"
)


@app.route("/")
def index():
    start = time.time()
    ACTIVE_SESSIONS.set(random.randint(1, 50))
    REQUEST_LATENCY.labels(endpoint="/").observe(time.time() - start)
    REQUEST_COUNT.labels(endpoint="/", status="200").inc()
    return "hello from sample-app"


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
