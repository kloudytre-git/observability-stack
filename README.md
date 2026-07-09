# observability-stack
Transform black-box systems into observable infrastructure. I will deploy Prometheus for metrics, Grafana for visualization, and Loki for log aggregation to gain deep insights into system performance.

## Install Prometheus
> sudo apt update

> docker run -d --name prometheus -p 9090:9090 prom/prometheus

> prometheus --version

## Install Node Exporter
