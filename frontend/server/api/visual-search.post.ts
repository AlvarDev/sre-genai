export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const target = getHeader(event, 'x-backend-target') || 'gemini'
  const backendUrl = target === 'gemma' ? config.backendGemmaUrl : config.backendGeminiUrl
  return proxyRequest(event, `${backendUrl}/visual-search`)
})
