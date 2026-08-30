// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  runtimeConfig: {
    // Private keys (only available server-side)
    backendUrl: process.env.NUXT_BACKEND_URL || "http://localhost:8080",
    public: {
      // Standard Firebase Project keys
      firebaseApiKey: process.env.NUXT_PUBLIC_FIREBASE_API_KEY || "",
      firebaseProjectId: process.env.NUXT_PUBLIC_FIREBASE_PROJECT_ID || "sre-genai",
      firebaseAuthDomain: process.env.NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "sre-genai.firebaseapp.com"
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
        { rel: "icon", type: "image/webp", href: "https://www.gstatic.com/marketing-cms/assets/images/68/a8/c5cfedc44b8195ae82b92ad87f1c/fevicon.webp" },
        { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&display=swap" }
      ]
    }
  },
  devtools: { enabled: false }
})
