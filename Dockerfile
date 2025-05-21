FROM public.ecr.aws/docker/library/python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install newrelic

ENV NEW_RELIC_APP_NAME="application"
ENV NEW_RELIC_LOG=stdout
ENV NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
ENV NEW_RELIC_LOG_LEVEL=info
# NO pongas la license aquí, ponla como variable de entorno en ECS/Fargate

EXPOSE 5000

CMD ["newrelic-admin", "run-program", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "application:app"]
