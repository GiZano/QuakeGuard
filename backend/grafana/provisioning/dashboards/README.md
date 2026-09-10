# QuakeGuard Grafana Dashboards

Place your exported Grafana dashboard `.json` files in this directory. 
Grafana will automatically read them and provision them on startup thanks to `dashboards.yml`.

Make sure your dashboard JSON uses the `TimescaleDB` datasource explicitly by name or UID.
