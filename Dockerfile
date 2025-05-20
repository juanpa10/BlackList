FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "application:app"]

RUN pip install newrelic
ENV NEW_RELIC_APP_NAME="application"
ENV NEW_RELIC_LOG=stdout
ENV NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
ENV NEW_RELIC_LICENSE_KEY=7B3FE90F578CF5834E0EB4FF0E824834FE19F2A19BD20720F76151C2A4770B9D
ENV NEW_RELIC_LOG_LEVEL=info


ENTRYPOINT ["newrelic-admin", "run-program"]