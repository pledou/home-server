FROM golang:1.26-alpine AS builder

ARG OLLAMA_METRICS_REPO_URL="{{ ollama_metrics_repo_url }}"
ARG OLLAMA_METRICS_REPO_REF="{{ ollama_metrics_repo_ref }}"
ARG OLLAMA_METRICS_BUCKETS="{{ ollama_metrics_request_duration_buckets | join(', ') }}"

WORKDIR /src

RUN apk add --no-cache git sed
RUN git clone --depth 1 --branch "${OLLAMA_METRICS_REPO_REF}" "${OLLAMA_METRICS_REPO_URL}" /src/ollama-metrics

WORKDIR /src/ollama-metrics
RUN sed -E -i "s/Buckets:[[:space:]]*\[\]float64\{[^}]*\},/Buckets: []float64{ ${OLLAMA_METRICS_BUCKETS} },/" main.go

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /ollama-metrics .

FROM alpine:3.23

RUN addgroup -S ollama && adduser -S -G ollama -h /home/ollama ollama

COPY --from=builder /ollama-metrics /usr/local/bin/ollama-metrics

USER ollama

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
	CMD wget -qO- "http://127.0.0.1:${PORT:-8080}/metrics" >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/ollama-metrics"]
