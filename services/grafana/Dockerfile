FROM grafana/grafana:10.4.0

USER root

RUN mkdir -p /etc/grafana/provisioning/datasources \
    /etc/grafana/provisioning/dashboards

RUN chown -R 472:472 /etc/grafana

USER 472