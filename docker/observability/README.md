# Observability stack

The config files in this directory go together with
`docker-compose.observability.yml` and provide a reference for a potential
observability stack.

**Disclaimer**

The chosen vendors/technologies here merely serve as an example - it's simply a
stack we're somewhat comfortable with. Open Inwoner itself is vendor agnostic
and the principles demonstrated apply to competing vendors too.

## Bringing up the services

From the root of the repository:

```bash
docker compose up -d
bin/start_observability.sh
```

(the second command is a thin wrapper around
`docker compose -f docker/docker-compose.observability.yml up` -- see that
script for why it's not called directly)

You can now navigate to:

- http://localhost:3000 for Grafana
- http://localhost:3100/ready for Loki readiness
- http://localhost:3100/metrics for Loki metrics
- http://localhost:9090 for the Prometheus web interface

## Logging

For log scraping, parsing and querying we've set up Promtail as scraper, Loki as
storage and Grafana as visualization tool.

### Sample queries

In the Grafana menu, navigate to "Explore" to create ad-hoc queries.

**Web service logs**

```logql
{job="docker", app="openinwoner"} | json | __error__ = ""
```

This ignores logs that cannot be parsed as JSON (such as container/server
startup logs).

**Logs for a single request**

You can filter application logs based on a request ID:

```logql
{job="docker", app="openinwoner"} | json | __error__ = "" | request_id=`1e9e1b9d-4d34-4657-99e4-88673d824724`
```

## Metrics

Metrics can be sent using OTLP to the collector at http://localhost:4317 (gRPC).

The `maykin_common.otel` module takes care of setting everything up, just make
sure to set the environment variable `OTEL_SDK_DISABLED=false` in development
(it's disabled by default).

The collector ingests the metrics, and they are then scraped by Prometheus.
They're also printend to stdout.

A pre-provisioned Grafana dashboard ("Open Inwoner metrics") visualizes all of
the application-defined metrics (see `open_inwoner/*/metrics.py` and
`open_inwoner/utils/metrics.py`) -- it's loaded automatically from
`grafana/dashboards/open-inwoner-metrics.json` and shows up in Grafana's
dashboard list. Regenerate/edit it by hand or export changes made in the UI
back into that file (Dashboard settings -> JSON Model).

## Traces

Traces can be sent using OTLP to the collector at http://localhost:4317 (gRPC).

The `maykin_common.otel` module takes care of setting everything up, just make
sure to set the environment variable `OTEL_SDK_DISABLED=false` in development
(it's disabled by default).

The collector ingests the traces and exports them to Grafana Tempo, queryable
from Grafana's "Tempo" datasource (or via trace-ID links from Loki logs
containing a `trace_id` field, wired up as a derived field -- see
`grafana/datasources/ds.yml`).
