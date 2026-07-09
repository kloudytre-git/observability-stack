# observability-stack

Transform black-box systems into observable infrastructure. This stack deploys Prometheus for metrics, Grafana for visualization, and Loki for log aggregation to gain deep insights into system performance.

## Start the stack

> docker compose up -d --build

This brings up:

| Service | URL | Purpose |
|---|---|---|
| Prometheus | http://localhost:9090 | Metrics collection, alert/recording rules |
| Alertmanager | http://localhost:9093 | Alert routing/notifications |
| Grafana | http://localhost:3000 | Dashboards (`admin` / `changeme`) |
| Loki | http://localhost:3100 | Log aggregation (queried via Grafana) |
| sample-app | http://localhost:8000 | Example app with custom Prometheus metrics |
| nginx | http://localhost:8080 | Demo target for nginx-exporter |
| mysql | localhost:3306 | Demo target for mysqld-exporter |
| mongo | localhost:27017 | Demo target for mongodb-exporter |

Exporters (node-exporter, nginx-exporter, mysqld-exporter, mongodb-exporter) run alongside these and are scraped automatically — see **Service discovery** below.

## Configuration

- **Scrape intervals & retention**: [prometheus.yml](prometheus.yml) sets a 15s global scrape interval; retention is `--storage.tsdb.retention.time=15d`, set on the `prometheus` service command in [docker-compose.yml](docker-compose.yml).
- **Rule files**: [prometheus/rules/](prometheus/rules/) — loaded via `rule_files` in prometheus.yml.

## Service discovery

Instead of hardcoding scrape targets, Prometheus uses `docker_sd_configs` against the Docker socket (`/var/run/docker.sock`, mounted read-only). Any container labeled with:

```yaml
labels:
  - "prometheus.io/scrape=true"
  - "prometheus.io/port=<metrics-port>"
  - "prometheus.io/job=<job-name>"
```

is picked up automatically within 15s — no Prometheus restart needed. See the `node-exporter`, `nginx-exporter`, `mysqld-exporter`, `mongodb-exporter`, and `sample-app` services in [docker-compose.yml](docker-compose.yml) for examples. Promtail uses the same discovery mechanism to tail logs from every container.

## Recording rules

[prometheus/rules/recording.yml](prometheus/rules/recording.yml) precomputes expensive/frequently-used queries (CPU/memory utilisation, request rate, p95 latency) so dashboards and alerts query a cheap precomputed series instead of re-running the raw `rate()`/`histogram_quantile()` expression each time.

## Alerting

[prometheus/rules/alerts.yml](prometheus/rules/alerts.yml) defines: `InstanceDown`, `HighCpuUsage`, `HighMemoryUsage`, `LowDiskSpace`, `HighRequestLatency`. Alerts route through Alertmanager ([alertmanager/alertmanager.yml](alertmanager/alertmanager.yml)), which groups by `alertname`/`job` and separates `critical` severity into its own route.

Slack and email notification channels are scaffolded but commented out — they need real credentials that can't be set for you:

1. Open [alertmanager/alertmanager.yml](alertmanager/alertmanager.yml).
2. Uncomment `slack_configs` and replace the webhook URL with a real one from your Slack workspace (Slack App → Incoming Webhooks).
3. Uncomment `smtp_*` fields under `global` and `email_configs` under each receiver, filling in real SMTP credentials.
4. `docker compose restart alertmanager`.

## Dashboards

Provisioned automatically into Grafana on startup (no manual import needed) from [grafana/dashboards/](grafana/dashboards/):

- **System Overview** — CPU, memory, disk, and network usage from node-exporter.
- **Application Metrics** — request rate, p95 latency, and active sessions from sample-app, plus MySQL/nginx panels and a correlated Loki logs panel (same dashboard, filtered to `sample-app`'s container logs, so a latency spike and the logs around it are visible together).

Both are plain JSON dashboard definitions — edit them directly or add new ones to that folder; Grafana picks up changes every 30s (see [grafana/provisioning/dashboards/dashboards.yml](grafana/provisioning/dashboards/dashboards.yml)). Panels query PromQL directly, so you can add ad-hoc panels with any expression Prometheus supports.

## Authentication

Grafana starts with anonymous access and self-signup disabled ([docker-compose.yml](docker-compose.yml), `GF_AUTH_ANONYMOUS_ENABLED=false`, `GF_USERS_ALLOW_SIGN_UP=false`). Default admin login is `admin` / `changeme` — **change this** (`GF_SECURITY_ADMIN_PASSWORD` env var, or from the Grafana UI under Administration → Users) before exposing this stack beyond localhost. For team use, add more users under Administration → Users, or wire up an OAuth/LDAP provider in `grafana/provisioning`.

## Log aggregation (Loki)

Promtail ([promtail/promtail-config.yml](promtail/promtail-config.yml)) discovers every running container via the Docker socket and ships its logs to Loki, tagged with a `container` label. Loki is added as a Grafana datasource alongside Prometheus, so you can:

- Use **Explore** in Grafana, switch between the Prometheus and Loki datasources, and filter both by the same time range/label to correlate a metric spike with the logs around it.
- Query directly, e.g. `{container="sample-app"}`.

## Custom application metrics

[app/app.py](app/app.py) is a small Flask app instrumented with the `prometheus_client` library, exposing `/metrics` with custom application-specific series: `app_requests_total` (Counter), `app_request_latency_seconds` (Histogram), `app_active_sessions` (Gauge). This is the pattern to follow for instrumenting your own services — import the client library, define metrics for the things specific to your app's business logic, and expose them on `/metrics`. It's auto-discovered by Prometheus the same way as the other exporters (see **Service discovery**), and it doubles as the custom exporter for the stack's own sample service.

## Repo layout

```
docker-compose.yml           # the whole stack
prometheus.yml               # scrape config, rule_files, alerting
prometheus/rules/            # recording + alerting rules
alertmanager/                # notification routing
grafana/provisioning/        # datasources + dashboard provider config
grafana/dashboards/          # dashboard JSON
loki/, promtail/             # log aggregation config
nginx/, mysqld-exporter/     # config for demo exporter targets
app/                         # sample instrumented application
```
