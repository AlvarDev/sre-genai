# Stage 1: Build llama-server binary from source
FROM debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libcurl4-openssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp.git .

# Build only the llama-server target for CPU (CUDA off)
RUN cmake -B build \
    -DBUILD_SHARED_LIBS=OFF \
    -DGGML_CUDA=OFF \
    -DLLAMA_CURL=ON \
    && cmake --build build --config Release -j $(nproc) --target llama-server

# Stage 2: Minimal, secure runtime
FROM debian:bookworm-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4 \
    libgomp1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 10001 appgroup && adduser --system --uid 10001 --ingroup appgroup appuser

WORKDIR /app
COPY --from=builder /app/build/bin/llama-server /usr/local/bin/llama-server

USER appuser

EXPOSE 11434
ENTRYPOINT ["/usr/local/bin/llama-server"]
