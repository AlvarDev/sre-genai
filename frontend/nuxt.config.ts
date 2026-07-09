// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      // API Backend URL (Cloud Run or local)
      backendUrl: process.env.NUXT_PUBLIC_BACKEND_URL || "http://localhost:8080",
      // Firebase Emulator Endpoint (if running local development)
      firebaseAuthEmulatorUrl: process.env.NUXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL || "",
      // Standard Firebase Project keys
      firebaseApiKey: process.env.FIREBASE_API_KEY || "fake-api-key-for-anonymous-auth",
      firebaseProjectId: process.env.FIREBASE_PROJECT_ID || "sre-genai",
      firebaseAuthDomain: process.env.FIREBASE_AUTH_DOMAIN || "sre-genai.firebaseapp.com"
    }
  },
  app: {
    head: {
      title: "Google Store Assistant",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" },
        { name: "description", content: "Google Store Virtual Shopping Assistant" }
      ],
      link: [
        { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&display=swap" }
      ]
    }
  },
  devtools: { enabled: false }
})
