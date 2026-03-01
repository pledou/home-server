FROM golang:1.23-alpine AS builder

ARG OLLAMA_METRICS_REPO_URL="{{ ollama_metrics_repo_url }}"
ARG OLLAMA_METRICS_REPO_REF="{{ ollama_metrics_repo_ref }}"
ARG OLLAMA_METRICS_BUCKETS="{{ ollama_metrics_request_duration_buckets | join(', ') }}"

WORKDIR /src

RUN apk add --no-cache git sed
RUN git clone --depth 1 --branch "${OLLAMA_METRICS_REPO_REF}" "${OLLAMA_METRICS_REPO_URL}" /src/ollama-metrics

WORKDIR /src/ollama-metrics
RUN sed -E -i "s/Buckets:[[:space:]]*\[\]float64\{[^}]*\},/Buckets: []float64{ ${OLLAMA_METRICS_BUCKETS} },/" main.go

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /ollama-metrics .

FROM scratch

COPY --from=builder /ollama-metrics /ollama-metrics
ENTRYPOINT ["/ollama-metrics"]
