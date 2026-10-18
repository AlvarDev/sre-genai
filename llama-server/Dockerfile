# Stage 1: Build llama-server binary from source
FROM debian:trixie-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp.git .

# Build only the llama-server target for CPU (CUDA off)
RUN cmake -B build \
    -DBUILD_SHARED_LIBS=OFF \
    -DGGML_CUDA=OFF \
    -DLLAMA_CURL=OFF \
    && cmake --build build --config Release -j $(nproc) --target llama-server

# Stage 2: Minimal, secure Google Distroless C++ runtime
FROM gcr.io/distroless/cc-debian13:nonroot AS runner

WORKDIR /app
COPY --from=builder /app/build/bin/llama-server /usr/local/bin/llama-server

USER nonroot

EXPOSE 11434
ENTRYPOINT ["/usr/local/bin/llama-server"]
