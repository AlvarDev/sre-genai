FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json yarn.lock ./
# Run yarn install
RUN yarn install --frozen-lockfile
COPY . .
# Run production build (yarn build compiles Nuxt)
RUN yarn build

FROM gcr.io/distroless/nodejs22-debian13:nonroot
WORKDIR /app
COPY --from=builder --chown=0:65532 /app/.output ./.output
USER nonroot
EXPOSE 3000
ENV PORT=3000
CMD [".output/server/index.mjs"]
