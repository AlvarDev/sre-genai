<template>
  <div :class="['assistant-page', isDarkMode ? 'theme-dark' : 'theme-light']">
    <!-- Header -->
    <header class="navbar">
      <div class="navbar-container">
        <div class="brand-logo" @click="handleLogoClick">
          <svg class="google-wordmark-logo" viewBox="0 0 74 24" width="74" height="24">
            <path fill="#3186FF" d="M9.24 8.19v2.46h5.88c-.18 1.38-.64 2.39-1.34 3.1-.86.86-2.2 1.8-4.54 1.8-3.62 0-6.45-2.92-6.45-6.54s2.83-6.54 6.45-6.54c1.95 0 3.38.77 4.43 1.76L15.4 2.5C13.94 1.08 11.98 0 9.24 0 4.28 0 .11 4.04.11 9s4.17 9 9.13 9c2.68 0 4.7-.88 6.28-2.52 1.62-1.62 2.13-3.91 2.13-5.75 0-.57-.04-1.1-.13-1.54H9.24z" />
            <path fill="#FC413D" d="M25 6.19c-3.21 0-5.83 2.44-5.83 5.81 0 3.34 2.62 5.81 5.83 5.81s5.83-2.46 5.83-5.81c0-3.37-2.62-5.81-5.83-5.81zm0 9.33c-1.76 0-3.28-1.45-3.28-3.52 0-2.09 1.52-3.52 3.28-3.52s3.28 1.43 3.28 3.52c0 2.07-1.52 3.52-3.28 3.52z" />
            <path fill="#FEC700" d="M38 6.19c-3.21 0-5.83 2.44-5.83 5.81 0 3.34 2.62 5.81 5.83 5.81s5.83-2.46 5.83-5.81c0-3.37-2.62-5.81-5.83-5.81zm0 9.33c-1.76 0-3.28-1.45-3.28-3.52 0-2.09 1.52-3.52 3.28-3.52s3.28 1.43 3.28 3.52c0 2.07-1.52 3.52-3.28 3.52z" />
            <path fill="#3186FF" d="M53.58 7.49h-.09c-.57-.68-1.67-1.3-3.06-1.3C47.53 6.19 45 8.72 45 12c0 3.26 2.53 5.81 5.43 5.81 1.39 0 2.49-.62 3.06-1.32h.09v.81c0 2.22-1.19 3.41-3.1 3.41-1.56 0-2.53-1.12-2.93-2.07l-2.22.92c.64 1.54 2.33 3.43 5.15 3.43 2.99 0 5.52-1.76 5.52-6.05V6.49h-2.42v1zm-2.93 8.03c-1.76 0-3.1-1.5-3.1-3.52 0-2.05 1.34-3.52 3.1-3.52 1.74 0 3.1 1.5 3.1 3.54.01 2.03-1.36 3.5-3.1 3.5z" />
            <path fill="#00AF57" d="M58 .24h2.51v17.57H58z" />
            <path fill="#FC413D" d="M68.26 15.52c-1.3 0-2.22-.59-2.82-1.76l7.77-3.21-.26-.66c-.48-1.3-1.96-3.7-4.97-3.7-2.99 0-5.48 2.35-5.48 5.81 0 3.26 2.46 5.81 5.76 5.81 2.66 0 4.2-1.63 4.84-2.57l-1.98-1.32c-.66.96-1.56 1.6-2.86 1.6zm-.18-7.15c1.03 0 1.91.53 2.2 1.28l-5.25 2.17c0-2.44 1.73-3.45 3.05-3.45z" />
          </svg>
          <span class="brand-title">Store Assistant</span>
          <transition name="fade">
            <span v-if="selectedEngine !== 'gemini'" class="model-indicator">[Gemma 4]</span>
          </transition>
        </div>
        <div class="navbar-actions">
          <button class="theme-toggle-btn" @click="toggleTheme" title="Alternar tema">
            <svg v-if="!isDarkMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-toggle-icon">
              <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
            </svg>
            <svg v-if="isDarkMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-toggle-icon">
              <circle cx="12" cy="12" r="4"/>
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41-1.41"/>
            </svg>
          </button>
          <transition name="admin-btn-slide">
            <button 
              v-if="isAdmin" 
              type="button" 
              class="admin-menu-btn" 
              @click="showSettingsModal = true" 
              title="Mais opções"
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
              </svg>
            </button>
          </transition>
        </div>
      </div>
    </header>

    <!-- Main Chat Workspace -->
    <main class="chat-workspace">
      <div class="chat-feed-container" ref="historyContainer">
        
        <!-- Welcome Hero Section -->
        <div class="welcome-hero" v-if="messages.length === 0">
          <div class="welcome-avatar-wrapper">
            <svg viewBox="0 0 24 24" class="gemini-logo-icon">
              <defs>
                <linearGradient id="gemini-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#3186FF" />
                  <stop offset="45%" stop-color="#9B51E0" />
                  <stop offset="90%" stop-color="#FC413D" />
                </linearGradient>
              </defs>
              <path fill="url(#gemini-gradient)" d="M12 2c0 5.5-4.5 10-10 10 5.5 0 10 4.5 10 10 0-5.5 4.5-10 10-10-5.5 0-10-4.5-10-10z" />
            </svg>
          </div>
          <h2 class="gemini-greeting">Olá! Como posso ajudar você hoje?</h2>
        </div>

        <!-- Messages List -->
        <div class="messages-list" v-else>
          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            :class="['message-row', msg.role === 'user' ? 'user-row' : 'agent-row']"
          >
            <!-- Message Bubble -->
            <div class="message-bubble-wrapper">

              <div class="message-bubble">
                <!-- Image attachment if user sent an image -->
                <div class="image-attachment" v-if="msg.imageUrl">
                  <img :src="msg.imageUrl" alt="Visual query preview" />
                </div>
                
                <div class="message-text" v-html="formatText(msg.content)"></div>
              </div>

              <!-- Product Grid/Carousel Attachment -->
              <div class="product-results-container" v-if="msg.products && msg.products.length > 0">
                <div class="product-carousel">
                  <div 
                    v-for="prod in msg.products" 
                    :key="prod.parent_sku" 
                    class="product-card"
                  >
                    <div class="product-img-wrapper">
                      <img :src="getValidImageUrl(prod.img_url)" :alt="prod.title" />
                    </div>
                    <div class="product-info">
                      <h4 class="product-title" :title="prod.title">{{ prod.title }}</h4>
                      <div class="product-price">R$ {{ parseFloat(prod.retail_price).toFixed(2) }}</div>
                      <p class="product-desc">{{ prod.shortdesc }}</p>
                      <button class="buy-btn" @click="simulatePurchase(prod)">
                        Comprar Agora
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading / Typing Indicator -->
          <div class="message-row agent-row" v-if="isTyping">
            <div class="message-bubble-wrapper">
              <div class="message-bubble typing-bubble">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Bottom Input Container & Overlay -->
    <div class="bottom-input-container">
      <div class="input-bar-wrapper">
        
        <!-- Image Preview Bar (Visual Search) -->
        <transition name="slide-up">
          <div class="preview-bar" v-if="selectedImage">
            <div class="preview-img-container">
              <img :src="selectedImagePreview" alt="Selected image" />
              <button class="remove-preview-btn" @click="cancelImage">✕</button>
            </div>
            <div class="preview-text">
              <strong>Imagem pronta.</strong> Escreva uma mensagem ou envie para buscar produtos parecidos.
            </div>
          </div>
        </transition>

        <!-- Main Pill Input Bar -->
        <form class="input-bar" @submit.prevent="submitMessage">
          <!-- Hidden File input -->
          <input 
            type="file" 
            ref="imageInput" 
            accept="image/*" 
            style="display: none" 
            @change="onImageSelected"
          />
          
          <button type="button" class="input-action-btn file-btn" @click="triggerImageUpload" title="Buscar por imagem">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M4 4h3l2-2h6l2 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm8 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z"/>
            </svg>
          </button>
          
          <input 
            type="text" 
            v-model="inputText" 
            :placeholder="dynamicPlaceholder"
            :disabled="isTyping"
            ref="messageInput"
          />
          
          <button type="submit" class="input-action-btn send-btn" :disabled="!inputText.trim() && !selectedImage || isTyping || !authReady" title="Enviar mensagem">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </form>

        <p class="input-notice">
          Google Store Assistant (Demo) • Telemetria & IA com Google Cloud
        </p>
      </div>
    </div>

    <!-- Purchase Simulation Modal -->
    <transition name="fade">
      <div class="purchase-modal" v-if="activePurchase" @click.self="activePurchase = null">
        <div class="modal-content">
          <div class="modal-success-icon">
            <svg viewBox="0 0 24 24" width="32" height="32">
              <path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          </div>
          <h3>Simulação de Compra Efetuada!</h3>
          <p>Você adquiriu o seguinte item da Google Store:</p>
          
          <div class="modal-product-detail">
            <strong class="modal-prod-title">{{ activePurchase.title }}</strong>
            <div class="modal-prod-sku">SKU: <code>{{ activePurchase.parent_sku }}</code></div>
            <div class="modal-prod-price">Valor: <strong>R$ {{ parseFloat(activePurchase.retail_price).toFixed(2) }}</strong></div>
          </div>
          
          <p class="modal-sre-notice">
            ℹ️ <strong>Métrica SRE</strong>: Esta ação simula um checkout com HTTP 200 OK. Nenhuma cobrança real foi efetuada. Os logs de monitoramento foram reportados para o Cloud Operations Suite.
          </p>
          <button class="modal-close-btn" @click="activePurchase = null">Fechar Janela</button>
        </div>
      </div>
    </transition>

    <!-- Admin Settings Right Drawer -->
    <transition name="sheet-slide">
      <div class="sheet-overlay" v-if="showSettingsModal" @click.self="showSettingsModal = false">
        <div class="sheet-content">
          <div class="sheet-header">
            <h3 class="sheet-title">Configurações da Demonstração</h3>
            <button class="sheet-close-btn" @click="showSettingsModal = false" title="Fechar">✕</button>
          </div>

          <div class="sheet-body">
            <div class="settings-group-label">MOTOR DE IA</div>
            
            <div class="settings-list">
              <div 
                class="settings-item" 
                :class="{ active: selectedEngine === 'gemini' }"
                @click="selectEngine('gemini')"
              >
                <div class="settings-item-info">
                  <div class="settings-item-title">Gemini 3.8 Flash</div>
                  <div class="settings-item-subtitle">Vertex AI (Cloud Run)</div>
                </div>
                <div class="radio-indicator">
                  <span class="radio-inner" v-if="selectedEngine === 'gemini'"></span>
                </div>
              </div>

              <div 
                class="settings-item" 
                :class="{ active: selectedEngine === 'gemma' }"
                @click="selectEngine('gemma')"
              >
                <div class="settings-item-info">
                  <div class="settings-item-title">Gemma 4 E2B</div>
                  <div class="settings-item-subtitle">llama-server (Inference Sidecar)</div>
                </div>
                <div class="radio-indicator">
                  <span class="radio-inner" v-if="selectedEngine === 'gemma'"></span>
                </div>
              </div>
            </div>
          </div>

          <!-- Drawer Footer with Admin Status & Logout -->
          <div class="drawer-footer" v-if="adminUserEmail">
            <div class="drawer-user-info">
              <span class="drawer-user-label">Logged in as</span>
              <span class="drawer-user-email" :title="adminUserEmail">{{ adminUserEmail }}</span>
            </div>
            <button class="drawer-logout-btn" @click="logoutAdmin" :disabled="isAuthLoading" title="Sign out of Admin Mode">
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Admin Authentication Modal (Triggered by 7 Logo Clicks) -->
    <transition name="fade">
      <div class="admin-auth-overlay" v-if="showAdminAuthModal" @click.self="showAdminAuthModal = false">
        <div class="admin-auth-card">
          <div class="admin-auth-header">
            <h3 class="admin-auth-title">Admin Access</h3>
            <button class="sheet-close-btn" @click="showAdminAuthModal = false" title="Close">✕</button>
          </div>

          <div class="admin-auth-body">
            <div v-if="!isAdmin">
              <p class="admin-auth-desc">
                Sign in with an authorized Google account to enable presenter controls and switch inference models.
              </p>
              <div v-if="authError" class="admin-auth-error">{{ authError }}</div>
              <button class="google-signin-btn" @click="loginWithGoogle" :disabled="isAuthLoading">
                <svg viewBox="0 0 24 24" width="18" height="18">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                </svg>
                <span>{{ isAuthLoading ? 'Signing in...' : 'Sign in with Google' }}</span>
              </button>
            </div>

            <div v-else class="admin-logged-in-box">
              <div class="admin-badge">✓ Active Administrator</div>
              <div class="admin-email-display">{{ adminUserEmail }}</div>
              <div class="admin-modal-actions">
                <button class="primary-btn" @click="showAdminAuthModal = false; showSettingsModal = true">
                  Open Settings
                </button>
                <button class="secondary-btn" @click="logoutAdmin" :disabled="isAuthLoading">
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Android Developer Mode Easter Egg Toast -->
    <transition name="fade">
      <div class="android-toast" v-if="devToastMessage">
        {{ devToastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { initializeApp } from 'firebase/app'
import { getAuth, signInAnonymously, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth'

// 1. Config & Runtime Env
const config = useRuntimeConfig()
const backendUrl = "/api"

// Shared Theme State (Default to dark mode)
const isDarkMode = useState('darkMode', () => true)
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
}

// State Variables
const route = useRoute()
const isMobile = ref(false)
// Admin mode: true enables the demo settings button in the header
const isAdmin = ref(false)
const adminUserEmail = ref('')
const showSettingsModal = ref(false)
const showAdminAuthModal = ref(false)
const isAuthLoading = ref(false)
const authError = ref('')
const logoClickCount = ref(0)
const devToastMessage = ref('')
let logoClickTimeout = null
let devToastTimeout = null

const showDevToast = (msg, duration = 1800) => {
  if (devToastTimeout) clearTimeout(devToastTimeout)
  devToastMessage.value = msg
  devToastTimeout = setTimeout(() => {
    devToastMessage.value = ''
  }, duration)
}

const handleLogoClick = () => {
  if (logoClickTimeout) clearTimeout(logoClickTimeout)
  logoClickCount.value++
  
  if (logoClickCount.value >= 4 && logoClickCount.value < 7) {
    const remaining = 7 - logoClickCount.value
    showDevToast(`You are now ${remaining} step${remaining > 1 ? 's' : ''} away from being a developer.`)
  } else if (logoClickCount.value >= 7) {
    logoClickCount.value = 0
    showDevToast('You are now a developer! 🎉', 2000)
    showAdminAuthModal.value = true
  }
  
  logoClickTimeout = setTimeout(() => {
    logoClickCount.value = 0
  }, 2500)
}

const loginWithGoogle = async () => {
  if (!authInstance) return
  try {
    isAuthLoading.value = true
    authError.value = ''
    const provider = new GoogleAuthProvider()
    const result = await signInWithPopup(authInstance, provider)
    const user = result.user
    const tokenResult = await user.getIdTokenResult(true)
    if (tokenResult.claims && tokenResult.claims.sre_genai_admin === true) {
      adminUserEmail.value = user.email || ''
      isAdmin.value = true
      showAdminAuthModal.value = false
    } else {
      isAdmin.value = false
      authError.value = 'Access Denied: Missing sre_genai_admin role claim.'
      await logoutAdmin()
    }
  } catch (err) {
    console.error('Google Sign-In failed:', err)
    authError.value = err.message || 'Failed to authenticate with Google.'
  } finally {
    isAuthLoading.value = false
  }
}

const logoutAdmin = async () => {
  if (!authInstance) return
  try {
    isAuthLoading.value = true
    await signOut(authInstance)
    isAdmin.value = false
    adminUserEmail.value = ''
    showSettingsModal.value = false
    showAdminAuthModal.value = false
    await signInAnonymously(authInstance)
  } catch (err) {
    console.error('Sign out failed:', err)
  } finally {
    isAuthLoading.value = false
  }
}

const selectedEngine = ref('gemini') // 'gemini' | 'gemma'

const selectEngine = (engine) => {
  selectedEngine.value = engine
  setTimeout(() => {
    showSettingsModal.value = false
  }, 180)
}

const dynamicPlaceholder = computed(() => {
  return isMobile.value 
    ? 'Faça sua pergunta...' 
    : 'Escreva sua pergunta sobre a Google Store...'
})
const sessionId = ref('')
const userUid = ref('')
const authReady = ref(false)
const messages = ref([])
const inputText = ref('')
const isTyping = ref(false)
const selectedImage = ref(null)
const selectedImagePreview = ref(null)
const activePurchase = ref(null)

// Auth Instance
let authInstance = null

// UI Refs
const historyContainer = ref(null)
const imageInput = ref(null)
const messageInput = ref(null)

// 2. Firebase Auth Setup (Anonymous for Guests, Google for Admins)
const initAuth = async () => {
  const firebaseConfig = {
    apiKey: config.public.firebaseApiKey,
    authDomain: config.public.firebaseAuthDomain,
    projectId: config.public.firebaseProjectId
  }
  
  try {
    const app = initializeApp(firebaseConfig)
    authInstance = getAuth(app)
    
    onAuthStateChanged(authInstance, async (user) => {
      if (user && !user.isAnonymous) {
        const tokenResult = await user.getIdTokenResult(true)
        if (tokenResult.claims && tokenResult.claims.sre_genai_admin === true) {
          userUid.value = user.uid
          adminUserEmail.value = user.email || ''
          isAdmin.value = true
          authReady.value = true
          console.log(`Admin authenticated with UID: ${userUid.value}, email: ${adminUserEmail.value}`)
        } else {
          userUid.value = user.uid
          adminUserEmail.value = ''
          isAdmin.value = false
          authReady.value = true
          console.log(`Non-admin Google user signed in, keeping admin mode disabled.`)
        }
      } else if (user) {
        userUid.value = user.uid
        adminUserEmail.value = ''
        isAdmin.value = false
        authReady.value = true
        console.log(`Guest authenticated anonymously with UID: ${userUid.value}`)
      } else {
        const userCredential = await signInAnonymously(authInstance)
        userUid.value = userCredential.user.uid
        adminUserEmail.value = ''
        isAdmin.value = false
        authReady.value = true
        console.log(`Authenticated silently with UID: ${userUid.value}`)
      }
    })
  } catch (err) {
    console.error('Firebase Auth setup failed:', err)
  }
}

// 3. Lifecycle Hooks
onMounted(() => {
  // Detect mobile viewport dynamically for responsive placeholder
  if (typeof window !== 'undefined') {
    const mq = window.matchMedia('(max-width: 640px)')
    isMobile.value = mq.matches
    mq.addEventListener('change', (e) => {
      isMobile.value = e.matches
    })
  }

  // Generate a cryptographically secure UUID for this chat instance
  sessionId.value = crypto.randomUUID()
  initAuth()
})

// Scroll chat history to bottom
const scrollToBottom = async (force = false) => {
  // 1. Check window scroll metrics BEFORE Vue updates the DOM
  const threshold = 150
  const scrollPosition = window.scrollY || window.pageYOffset || document.documentElement.scrollTop
  const viewportHeight = window.innerHeight
  const oldTotalHeight = document.documentElement.scrollHeight
  const isNearBottom = oldTotalHeight - (scrollPosition + viewportHeight) < threshold

  // 2. Wait for Vue to render the new message block
  await nextTick()

  // 3. Scroll browser window if forced (user query) or if they were already at the bottom
  if (force || isNearBottom) {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    })
  }
}

// Format markdown bold text inside LLM replies
const formatText = (text) => {
  if (!text) return ''
  // 1. Escape HTML special characters to prevent script injection
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')

  // 2. Safely apply our own formatting tags
  return escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br/>')
}

// Handle unsplash fallbacks if store urls are offline placeholders
const getValidImageUrl = (url) => {
  if (!url) {
    return 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=300' // Generic premium gadget placeholder
  }

  // Translate legacy/broken Google Merchandise Store links to the active GCS bucket
  if (url.includes('shop.googlemerchandisestore.com/store/')) {
    const filename = url.substring(url.lastIndexOf('/') + 1)
    return `https://storage.googleapis.com/github-repo/embeddings/getting_started_embeddings/gms_images/${filename}`
  }

  if (url.startsWith('http')) return url
  return 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=300'
}

// Trigger hidden file picker
const triggerImageUpload = () => {
  if (imageInput.value) {
    imageInput.value.click()
  }
}

// Parse picked image
const onImageSelected = (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  selectedImage.value = file
  
  // Create preview URL
  const reader = new FileReader()
  reader.onload = (event) => {
    selectedImagePreview.value = event.target.result
  }
  reader.readAsDataURL(file)
}

// Cancel visual search preview
const cancelImage = () => {
  selectedImage.value = null
  selectedImagePreview.value = null
  if (imageInput.value) {
    imageInput.value.value = ''
  }
}

// Send quick-suggestion query
const sendSuggestion = (text) => {
  inputText.value = text
  submitMessage()
}

// Simulate product purchase
const simulatePurchase = (prod) => {
  activePurchase.value = prod
}

// 4. Submit Chat Message (Text RAG or Visual Search)
const submitMessage = async () => {
  const queryText = inputText.value.trim()
  const imageFile = selectedImage.value
  
  if (!queryText && !imageFile) return
  
  isTyping.value = true
  inputText.value = ''
  
  // Acknowledge user input locally in chat list
  const userMsg = {
    role: 'user',
    content: queryText || 'Busca por imagem'
  }
  
  if (imageFile) {
    userMsg.imageUrl = selectedImagePreview.value
  }
  
  messages.value.push(userMsg)
  cancelImage()
  await scrollToBottom(true)
  
  try {
    let responseData
    
    // Get Firebase ID Token dynamically to authorize the request
    const token = authInstance && authInstance.currentUser ? await authInstance.currentUser.getIdToken() : ''
    
    // Headers to isolate session and verify identity
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    // Select direct backend URL based on toggle
    const targetBackendUrl = selectedEngine.value === 'gemma' 
      ? config.public.backendGemmaUrl 
      : config.public.backendGeminiUrl
    
    if (imageFile) {
      // Execute Visual Search upload via Multipart
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('message', queryText)
      formData.append('session_id', sessionId.value)
      
      const response = await fetch(`${targetBackendUrl}/visual-search`, {
        method: 'POST',
        headers: headers,
        body: formData
      })
      
      if (!response.ok) throw new Error('Visual search API failure')
      responseData = await response.json()
    } else {
      // Execute Text-based Chat via JSON
      const response = await fetch(`${targetBackendUrl}/chat`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: queryText,
          session_id: sessionId.value
        })
      })
      
      if (!response.ok) throw new Error('Chat API failure')
      const json = await response.json()
      responseData = {
        text: json.text,
        products: json.products || []
      }
    }
    
    // Append agent reply
    messages.value.push({
      role: 'agent',
      content: responseData.text,
      products: responseData.products || []
    })
    
  } catch (err) {
    console.error('Request failed:', err)
    messages.value.push({
      role: 'agent',
      content: 'Erro de comunicação com o assistente. Verifique se o backend está online.'
    })
  } finally {
    isTyping.value = false
    await scrollToBottom()
    
    // Focus back on text input
    if (messageInput.value) {
      messageInput.value.focus()
    }
  }
}
</script>

<style scoped>
/* Main Layout */
.assistant-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-color-alt);
}

/* Navbar */
.navbar {
  position: sticky;
  top: 0;
  height: var(--header-height);
  background-color: var(--panel-color);
  border-bottom: 1px solid var(--border-color-light);
  box-shadow: var(--shadow-subtle);
  display: flex;
  align-items: center;
  z-index: 100;
}

.navbar-container {
  width: 100%;
  max-width: var(--max-content-width);
  margin: 0 auto;
  padding: 0 12px 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-logo {
  display: flex;
  align-items: center;
  user-select: none;
  -webkit-user-select: none;
  cursor: default;
}

.google-wordmark-logo {
  flex-shrink: 0;
  display: block;
  transition: transform 0.08s ease, opacity 0.08s ease;
}

.brand-logo:active .google-wordmark-logo {
  transform: scale(0.95);
  opacity: 0.85;
}

.brand-title {
  font-size: 18px;
  font-weight: 400;
  color: var(--text-secondary);
  border-left: 1px solid var(--border-color);
  padding-left: 12px;
  margin-left: 12px;
  line-height: 1.2;
}

.model-indicator {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: 8px;
  line-height: 1.2;
  white-space: nowrap;
  opacity: 0.85;
}

.navbar-actions {
  display: flex;
  align-items: center;
}

.admin-menu-btn {
  margin-left: 12px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
}

.admin-menu-btn:hover {
  background-color: var(--border-color-light);
  color: var(--text-primary);
}

/* Admin Settings Right Drawer */
.sheet-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  z-index: 1100;
  display: flex;
  align-items: stretch;
  justify-content: flex-end;
}

.sheet-content {
  width: 100%;
  max-width: 360px;
  height: 100%;
  background-color: var(--panel-color);
  border-left: 1px solid var(--border-color);
  border-radius: 16px 0 0 16px;
  padding: 20px 24px;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light);
  margin-bottom: 16px;
}

.sheet-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.sheet-close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.settings-group-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.8px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
}

.settings-list {
  display: flex;
  flex-direction: column;
}

.settings-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.settings-item:hover {
  background-color: var(--bg-color-alt);
}

.settings-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.settings-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.settings-item-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
}

.radio-indicator {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s;
}

.settings-item.active .radio-indicator {
  border-color: #3186FF;
}

.radio-inner {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #3186FF;
}

/* Sheet Slide Transition */
.sheet-slide-enter-active, .sheet-slide-leave-active {
  transition: opacity 0.35s ease;
}
.sheet-slide-enter-active .sheet-content, .sheet-slide-leave-active .sheet-content {
  transition: transform 0.42s cubic-bezier(0.4, 0, 0.2, 1);
}
.sheet-slide-enter-from, .sheet-slide-leave-to {
  opacity: 0;
}
.sheet-slide-enter-from .sheet-content, .sheet-slide-leave-to .sheet-content {
  transform: translateX(100%);
}

/* Drawer Footer (Admin status & Sign out) */
.drawer-footer {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid var(--border-color-light);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.drawer-user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.drawer-user-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  font-weight: 500;
}

.drawer-user-email {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  word-break: break-all;
}

.drawer-logout-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
}

.drawer-logout-btn:hover {
  background-color: var(--bg-color-alt);
  color: #ea4335;
  border-color: #ea4335;
}

/* Admin Auth Modal (Triggered by 7 taps) */
.admin-auth-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.admin-auth-card {
  width: 100%;
  max-width: 400px;
  background-color: var(--panel-color);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
  animation: fadeIn 0.25s ease-out;
}

.admin-auth-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.admin-auth-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.admin-auth-desc {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.admin-auth-error {
  background-color: rgba(234, 67, 53, 0.1);
  color: #ea4335;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  margin-bottom: 16px;
  border: 1px solid rgba(234, 67, 53, 0.3);
}

.google-signin-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 10px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--panel-color);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.google-signin-btn:hover:not(:disabled) {
  background-color: var(--bg-color-alt);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.google-signin-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.admin-logged-in-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: center;
}

.admin-badge {
  display: inline-block;
  align-self: center;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  background-color: rgba(49, 134, 255, 0.12);
  color: #3186ff;
}

.admin-email-display {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.admin-modal-actions {
  display: flex;
  gap: 10px;
}

.admin-modal-actions .primary-btn {
  flex: 1;
  padding: 9px 16px;
  background-color: #3186ff;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.admin-modal-actions .primary-btn:hover {
  opacity: 0.9;
}

.admin-modal-actions .secondary-btn {
  flex: 1;
  padding: 9px 16px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.admin-modal-actions .secondary-btn:hover {
  background-color: var(--bg-color-alt);
  color: #ea4335;
  border-color: #ea4335;
}

/* Smooth Unfolding Transition for Admin Icon */
.admin-btn-slide-enter-active, .admin-btn-slide-leave-active {
  transition: opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
              max-width 0.35s cubic-bezier(0.16, 1, 0.3, 1),
              margin-left 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  max-width: 40px;
  overflow: hidden;
}
.admin-btn-slide-enter-from, .admin-btn-slide-leave-to {
  opacity: 0;
  transform: scale(0.8);
  max-width: 0;
  margin-left: 0;
}

/* Android Toast Pill Easter Egg */
.android-toast {
  position: fixed;
  bottom: 90px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(32, 33, 36, 0.92);
  color: #ffffff;
  font-size: 13px;
  font-weight: 500;
  padding: 10px 22px;
  border-radius: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.28);
  z-index: 1300;
  pointer-events: none;
  white-space: nowrap;
}

.theme-toggle-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
}

.theme-toggle-btn:hover {
  background-color: var(--border-color-light);
  color: var(--text-primary);
}

.theme-toggle-icon {
  width: 20px;
  height: 20px;
}

/* Chat Workspace */
.chat-workspace {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow-y: visible;
}

.chat-feed-container {
  width: 100%;
  max-width: var(--max-content-width);
  margin: 0 auto;
  padding: 40px 24px 160px 24px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

/* Welcome Hero Section */
.welcome-hero {
  text-align: center;
  margin: auto 0;
  padding: 40px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.welcome-avatar-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(49, 134, 255, 0.08) 0%, rgba(155, 81, 224, 0.08) 50%, rgba(252, 65, 61, 0.08) 100%);
  border: 1px solid rgba(155, 81, 224, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(155, 81, 224, 0.05);
}

.gemini-logo-icon {
  width: 36px;
  height: 36px;
}

.gemini-greeting {
  font-size: 36px;
  font-weight: 500;
  background: linear-gradient(74deg, #3186FF 0%, #9B51E0 55%, #FC413D 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  letter-spacing: -0.8px;
  padding-bottom: 4px;
}

.hero-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 480px;
  line-height: 1.6;
}



/* Chat Message Stream (Minimalist, Box-free & Bubble-free) */
.messages-list {
  display: flex;
  flex-direction: column;
  margin-top: auto;
  width: 100%;
}

.message-row {
  display: flex;
  gap: 24px;
  width: 100%;
  max-width: 85%;
  animation: messageSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
  margin-bottom: 24px; /* Reduced vertical spacing on desktop */
}

.user-row {
  align-self: flex-end;
  justify-content: flex-end;
}

.agent-row {
  align-self: flex-start;
  justify-content: flex-start;
}

/* Avatars */
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px; /* align with text header */
}

.agent-avatar {
  background-color: transparent; /* no background card */
  border: none;
  box-shadow: none;
}

.avatar-svg {
  width: 24px;
  height: 24px;
}

.user-avatar {
  background: linear-gradient(135deg, var(--google-blue) 0%, var(--google-green) 100%) !important;
  color: white !important;
}

/* Content Container */
.message-bubble-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 100%;
  width: 100%;
}

.user-row .message-bubble-wrapper {
  align-items: flex-end;
}

.agent-row .message-bubble-wrapper {
  align-items: flex-start;
}

.message-sender-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.sender-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.sender-tag {
  font-size: 9px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sender-tag.user {
  background-color: var(--google-blue-soft);
  color: var(--google-blue-text);
}

.sender-tag.agent {
  background-color: var(--google-green-soft);
  color: var(--google-green-text);
}

/* Minimalist pure text containers */
.message-bubble {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  line-height: 1.65;
  font-size: 15px;
  color: var(--text-primary);
}

.user-row .message-bubble {
  background-color: var(--border-color-light) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-color-light) !important;
  border-radius: 18px 18px 4px 18px !important; /* Elegant rounded bubble shape */
  padding: 12px 18px !important;
  text-align: left;
  display: inline-block !important;
  max-width: 100% !important;
  box-shadow: var(--shadow-subtle) !important;
}

.agent-row .message-bubble {
  color: var(--text-primary) !important;
  border-left: none !important;
  padding: 0 !important;
  text-align: left;
}

.image-attachment img {
  max-width: 100%;
  max-height: 260px;
  border-radius: var(--radius-sm);
  margin-bottom: 12px;
  display: block;
}

.message-text {
  word-break: break-word;
}

.message-text :deep(strong) {
  font-weight: 600;
}

/* Typing Indicator */
.typing-bubble {
  padding: 8px 0 !important;
  display: flex;
  align-items: center;
}

.typing-indicator {
  display: flex;
  gap: 6px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background-color: var(--text-secondary);
  border-radius: 50%;
  display: inline-block;
  animation: bounce 1.4s infinite ease-in-out both;
  opacity: 0.6;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

/* Product grid cards inside chat */
.product-results-container {
  width: 100%;
  margin-top: 24px; /* Give breathing room between text and carousel */
}

.product-carousel {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  width: 100%;
}

.product-card {
  background-color: var(--panel-color);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-subtle);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
  border-color: var(--border-color);
}

.product-img-wrapper {
  height: 200px; /* Much larger image canvas */
  background-color: var(--card-inner-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-color-light);
  overflow: hidden;
  transition: background-color 0.3s ease;
}

.product-img-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* Cover the entire container, removing side color blocks! */
  transition: transform 0.3s ease;
}

.product-card:hover .product-img-wrapper img {
  transform: scale(1.06);
}

.product-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  gap: 4px;
}

.product-title {
  font-size: 13px; /* Clean, smaller title */
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.2px;
}

.product-price {
  font-size: 13px; /* Elegant, matching font size */
  font-weight: 600;
  color: var(--google-blue-text); /* Restored blue accent color */
}


.product-desc {
  font-size: 11px; /* Subtle, small description */
  color: var(--text-secondary);
  height: 32px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.45;
  margin-top: 2px;
  opacity: 0.8;
}

.buy-btn {
  display: none !important; /* Hide buy button for now */
}

.bottom-input-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--theme-gradient);
  padding: 24px;
  z-index: 90;
  transition: background 0.3s ease;
}

.input-bar-wrapper {
  width: 100%;
  max-width: var(--max-content-width);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-bar {
  background-color: var(--panel-color);
  border: 1px solid var(--border-color);
  border-radius: 28px;
  display: flex;
  align-items: center;
  padding: 6px 8px 6px 18px;
  gap: 12px;
  box-shadow: var(--shadow-subtle);
  transition: all 0.25s ease;
}

.input-bar:focus-within {
  border-color: transparent;
  box-shadow: var(--shadow-input);
}

.input-bar input {
  flex-grow: 1;
  border: none;
  outline: none;
  font-family: var(--font-family);
  font-size: 15px;
  color: var(--text-primary);
  background-color: transparent;
  padding: 10px 0;
}

.input-bar input::placeholder {
  color: var(--text-secondary);
  opacity: 0.8;
}

.input-action-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-btn {
  color: var(--text-secondary);
}

.file-btn:hover {
  background-color: var(--border-color-light);
  color: var(--text-primary);
}

.send-btn {
  background-color: var(--google-blue);
  color: white;
}

.send-btn:hover:not(:disabled) {
  background-color: #1557b0;
  transform: scale(1.04);
}

.send-btn:disabled {
  background-color: var(--border-color-light);
  color: #9aa0a6;
  cursor: not-allowed;
}

.input-notice {
  text-align: center;
  font-size: 11px;
  color: #9aa0a6;
  margin-top: 4px;
}

/* Selected Image Preview */
.preview-bar {
  background-color: var(--panel-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-subtle);
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.preview-img-container {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}

.preview-img-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-preview-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.preview-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Purchase Modal */
.purchase-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(32, 33, 36, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 24px;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--panel-color);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 420px;
  padding: 32px;
  text-align: center;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2);
  animation: popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-success-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background-color: var(--google-green-soft);
  color: var(--google-green-text);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px auto;
}

.modal-content h3 {
  font-size: 22px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12px;
  letter-spacing: -0.4px;
}

.modal-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.5;
}

.modal-product-detail {
  background-color: var(--card-inner-bg);
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: left;
  font-size: 14px;
  border: 1px solid var(--border-color-light);
  margin-bottom: 20px;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.modal-prod-title {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.modal-prod-sku {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.modal-prod-sku code {
  background: #e8eaed;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.modal-prod-price {
  font-size: 14px;
  color: var(--text-primary);
}

.modal-sre-notice {
  font-size: 12px;
  color: var(--google-yellow-text);
  background-color: var(--google-yellow-soft);
  border: 1px solid #FFE0B2;
  border-radius: var(--radius-sm);
  padding: 12px;
  text-align: left;
  margin-bottom: 24px;
  line-height: 1.5;
}

.modal-close-btn {
  background-color: var(--google-blue);
  color: white;
  border: none;
  border-radius: var(--radius-pill);
  padding: 12px 24px;
  font-family: var(--font-family);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  transition: background-color 0.2s;
}

.modal-close-btn:hover {
  background-color: #1557b0;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes popIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes messageSlideIn {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .5; }
}

/* Slide & Fade Transitions for Vue */
.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Responsive Overrides */
@media (max-width: 640px) {
  .navbar-container {
    padding: 0 8px 0 16px;
    gap: 8px;
  }
  
  .brand-title {
    font-size: 15px;
    margin-left: 8px;
    padding-left: 8px;
  }

  .model-indicator {
    font-size: 12px;
    margin-left: 6px;
  }
  
  .theme-toggle-btn,
  .admin-menu-btn {
    width: 36px;
    height: 36px;
  }

  .admin-menu-btn {
    margin-left: 8px;
  }

  .sheet-content {
    max-width: 85vw;
    border-radius: 12px 0 0 12px;
  }

  .welcome-hero h2 {
    font-size: 26px;
  }
  
  .chat-feed-container {
    padding: 24px 28px 150px 28px;
    gap: 20px;
  }
  
  .message-row {
    max-width: 100%;
    gap: 12px;
    margin-bottom: 16px; /* Tighter spacing on mobile */
  }
  
  .message-bubble {
    padding: 12px 16px;
    font-size: 14px;
  }
  
  .product-carousel {
    display: flex;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    gap: 12px;
    padding-bottom: 8px;
    width: 100%;
    scrollbar-width: none; /* Firefox */
  }
  
  .product-carousel::-webkit-scrollbar {
    display: none; /* Chrome/Safari */
  }
  
  .product-card {
    flex: 0 0 200px;
    scroll-snap-align: start;
  }
  
  .bottom-input-container {
    padding: 16px;
  }
  
  .input-bar {
    padding: 4px 6px 4px 14px;
    gap: 8px;
  }
  
  .input-bar input {
    font-size: 14px;
    padding: 8px 0;
  }
  
  .input-action-btn {
    width: 36px;
    height: 36px;
  }
}
</style>
