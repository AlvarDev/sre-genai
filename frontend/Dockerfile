FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
# Run yarn install
RUN yarn install --frozen-lockfile
COPY . .
# Run production build (yarn build compiles Nuxt)
RUN yarn build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.output ./.output
EXPOSE 3000
ENV PORT=3000
CMD ["node", ".output/server/index.mjs"]
