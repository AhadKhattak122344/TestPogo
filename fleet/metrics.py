"""Prometheus metrics."""

from prometheus_client import Counter, Gauge, start_http_server

instances_running = Gauge("fleet_instances_running", "running instances")
instances_attested = Gauge("fleet_instances_attested", "attested instances")
keybox_pool_size = Gauge("fleet_keybox_pool_size", "keyboxes in pool")
keybox_pool_available = Gauge(
    "fleet_keybox_pool_available", "keyboxes available"
)
provision_failures = Counter(
    "fleet_provision_failures_total", "provision failures"
)
attestation_checks = Counter(
    "fleet_attestation_checks_total", "attestation checks", ["result"]
)


def start(port: int = 9100) -> None:
    start_http_server(port)
