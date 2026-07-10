export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  return proxyRequest(event, `${config.backendUrl}/visual-search`)
})
