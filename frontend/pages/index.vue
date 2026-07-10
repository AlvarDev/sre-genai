<template>
  <div class="assistant-page">
    <!-- Header -->
    <header class="navbar">
      <div class="navbar-container">
        <div class="brand-logo">
          <svg class="google-wordmark-logo" viewBox="0 0 74 24" width="74" height="24">
            <path fill="#3186FF" d="M9.24 8.19v2.46h5.88c-.18 1.38-.64 2.39-1.34 3.1-.86.86-2.2 1.8-4.54 1.8-3.62 0-6.45-2.92-6.45-6.54s2.83-6.54 6.45-6.54c1.95 0 3.38.77 4.43 1.76L15.4 2.5C13.94 1.08 11.98 0 9.24 0 4.28 0 .11 4.04.11 9s4.17 9 9.13 9c2.68 0 4.7-.88 6.28-2.52 1.62-1.62 2.13-3.91 2.13-5.75 0-.57-.04-1.1-.13-1.54H9.24z" />
            <path fill="#FC413D" d="M25 6.19c-3.21 0-5.83 2.44-5.83 5.81 0 3.34 2.62 5.81 5.83 5.81s5.83-2.46 5.83-5.81c0-3.37-2.62-5.81-5.83-5.81zm0 9.33c-1.76 0-3.28-1.45-3.28-3.52 0-2.09 1.52-3.52 3.28-3.52s3.28 1.43 3.28 3.52c0 2.07-1.52 3.52-3.28 3.52z" />
            <path fill="#FEC700" d="M38 6.19c-3.21 0-5.83 2.44-5.83 5.81 0 3.34 2.62 5.81 5.83 5.81s5.83-2.46 5.83-5.81c0-3.37-2.62-5.81-5.83-5.81zm0 9.33c-1.76 0-3.28-1.45-3.28-3.52 0-2.09 1.52-3.52 3.28-3.52s3.28 1.43 3.28 3.52c0 2.07-1.52 3.52-3.28 3.52z" />
            <path fill="#3186FF" d="M53.58 7.49h-.09c-.57-.68-1.67-1.3-3.06-1.3C47.53 6.19 45 8.72 45 12c0 3.26 2.53 5.81 5.43 5.81 1.39 0 2.49-.62 3.06-1.32h.09v.81c0 2.22-1.19 3.41-3.1 3.41-1.56 0-2.53-1.12-2.93-2.07l-2.22.92c.64 1.54 2.33 3.43 5.15 3.43 2.99 0 5.52-1.76 5.52-6.05V6.49h-2.42v1zm-2.93 8.03c-1.76 0-3.1-1.5-3.1-3.52 0-2.05 1.34-3.52 3.1-3.52 1.74 0 3.1 1.5 3.1 3.54.01 2.03-1.36 3.5-3.1 3.5z" />
            <path fill="#00AF57" d="M58 .24h2.51v17.57H58z" />
            <path fill="#FC413D" d="M68.26 15.52c-1.3 0-2.22-.59-2.82-1.76l7.77-3.21-.26-.66c-.48-1.3-1.96-3.7-4.97-3.7-2.99 0-5.48 2.35-5.48 5.81 0 3.26 2.46 5.81 5.76 5.81 2.66 0 4.2-1.63 4.84-2.57l-1.98-1.32c-.66.96-1.56 1.6-2.86 1.6zm-.18-7.15c1.03 0 1.91.53 2.2 1.28l-5.25 2.17c0-2.44 1.73-3.45 3.05-3.45z" />
          </svg>
          <span class="brand-title">Store Assistant</span>
        </div>
        <div class="connection-status">
          <span class="status-dot animate-pulse"></span>
          <span class="status-text">Online</span>
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
              <path fill="url(#gemini-gradient)" d="M12 2C12 2 12.3 9 18.5 12.2C18.5 12.2 12 12 12 22C12 22 11.7 15 5.5 11.8C5.5 11.8 12 12 12 2Z" />
            </svg>
          </div>
          <h2 class="gemini-greeting">Olá! Como posso ajudar você hoje?</h2>
          <p class="hero-subtitle">Pergunte-me sobre os celulares Pixel, fones de ouvido, termostatos Nest ou roupas da marca Google.</p>
          

        </div>

        <!-- Messages List -->
        <div class="messages-list" v-else>
          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            :class="['message-row', msg.role === 'user' ? 'user-row' : 'agent-row']"
          >
            <!-- Agent Avatar -->
            <div class="avatar agent-avatar" v-if="msg.role === 'agent'">
              <svg viewBox="0 0 24 24" class="avatar-svg">
                <path fill="var(--google-blue)" d="M21.35 11.1H12v2.7h5.35C17 15.35 14.85 16.5 12 16.5c-2.9 0-5.25-2.35-5.25-5.25S9.1 6 12 6c1.45 0 2.75.55 3.75 1.5l2-2C16.05 3.8 14.15 3 12 3 7.05 3 3 7.05 3 12s4.05 9 9 9c5.2 0 8.65-3.65 8.65-8.8 0-.6-.05-1.2-.3-1.6z"/>
              </svg>
            </div>

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

            <!-- User Avatar -->
            <div class="avatar user-avatar" v-if="msg.role === 'user'">
              <span class="user-initial">U</span>
            </div>
          </div>

          <!-- Loading / Typing Indicator -->
          <div class="message-row agent-row" v-if="isTyping">
            <div class="avatar agent-avatar">
              <svg viewBox="0 0 24 24" class="avatar-svg">
                <path fill="var(--google-blue)" d="M21.35 11.1H12v2.7h5.35C17 15.35 14.85 16.5 12 16.5c-2.9 0-5.25-2.35-5.25-5.25S9.1 6 12 6c1.45 0 2.75.55 3.75 1.5l2-2C16.05 3.8 14.15 3 12 3 7.05 3 3 7.05 3 12s4.05 9 9 9c5.2 0 8.65-3.65 8.65-8.8 0-.6-.05-1.2-.3-1.6z"/>
              </svg>
            </div>
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
        <div class="input-bar">
          <!-- Hidden File input -->
          <input 
            type="file" 
            ref="imageInput" 
            accept="image/*" 
            style="display: none" 
            @change="onImageSelected"
          />
          
          <button class="input-action-btn file-btn" @click="triggerImageUpload" title="Buscar por imagem">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M4 4h3l2-2h6l2 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm8 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z"/>
            </svg>
          </button>
          
          <input 
            type="text" 
            v-model="inputText" 
            @keydown.enter="submitMessage"
            placeholder="Escreva sua pergunta sobre a Google Store..."
            :disabled="isTyping"
            ref="messageInput"
          />
          
          <button class="input-action-btn send-btn" @click="submitMessage" :disabled="!inputText.trim() && !selectedImage || isTyping" title="Enviar mensagem">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>

        <p class="input-notice">
          Demonstração de Inteligência Artificial integrada com Google Cloud Operations Suite & Firebase.
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
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { initializeApp } from 'firebase/app'
import { getAuth, signInAnonymously, connectAuthEmulator } from 'firebase/auth'

// 1. Config & Runtime Env
const config = useRuntimeConfig()
const backendUrl = "/api"

// State Variables
const sessionId = ref('')
const userUid = ref('anonymous')
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

// 2. Firebase Anonymous Auth Setup
const initAuth = async () => {
  const firebaseConfig = {
    apiKey: config.public.firebaseApiKey,
    authDomain: config.public.firebaseAuthDomain,
    projectId: config.public.firebaseProjectId
  }
  
  try {
    const app = initializeApp(firebaseConfig)
    authInstance = getAuth(app)
    
    // Connect to Auth emulator if configured in local development
    if (config.public.firebaseAuthEmulatorUrl) {
      console.log(`Connecting to Firebase Auth emulator: ${config.public.firebaseAuthEmulatorUrl}`)
      connectAuthEmulator(authInstance, config.public.firebaseAuthEmulatorUrl)
    }
    
    const userCredential = await signInAnonymously(authInstance)
    userUid.value = userCredential.user.uid
    console.log(`Authenticated silently with UID: ${userUid.value}`)
  } catch (err) {
    console.error('Firebase Anonymous Auth failed:', err)
  }
}

// 3. Lifecycle Hooks
onMounted(() => {
  // Generate a random session ID for this chat instance
  sessionId.value = 'session_' + Math.random().toString(36).substr(2, 9)
  initAuth()
})

// Scroll chat history to bottom
const scrollToBottom = async () => {
  await nextTick()
  if (historyContainer.value) {
    historyContainer.value.scrollTop = historyContainer.value.scrollHeight
  }
}

// Format markdown bold text inside LLM replies
const formatText = (text) => {
  if (!text) return ''
  // Basic replacement for **bold** text
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
             .replace(/\n/g, '<br/>')
}

// Handle unsplash fallbacks if store urls are offline placeholders
const getValidImageUrl = (url) => {
  if (url && url.startsWith('http')) return url
  return 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=300' // Generic premium gadget placeholder
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
  await scrollToBottom()
  
  try {
    let responseData
    
    // Get Firebase ID Token dynamically to authorize the request
    const token = authInstance && authInstance.currentUser ? await authInstance.currentUser.getIdToken() : ''
    
    // Headers to isolate session and verify identity
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    if (imageFile) {
      // Execute Visual Search upload via Multipart
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('message', queryText)
      formData.append('session_id', sessionId.value)
      
      const response = await fetch(`${backendUrl}/visual-search`, {
        method: 'POST',
        headers: headers,
        body: formData
      })
      
      if (!response.ok) throw new Error('Visual search API failure')
      responseData = await response.json()
    } else {
      // Execute Text-based Chat via JSON
      const response = await fetch(`${backendUrl}/chat`, {
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
        products: [] // Text API is basic, but ADK answers directly in context
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
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-logo {
  display: flex;
  align-items: center;
}

.google-wordmark-logo {
  flex-shrink: 0;
  display: block;
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

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--google-green-soft);
  padding: 6px 14px;
  border-radius: var(--radius-pill);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--google-green);
  display: inline-block;
}

.status-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--google-green-text);
  letter-spacing: 0.2px;
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



/* Messages List */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.message-row {
  display: flex;
  gap: 16px;
  width: 100%;
  max-width: 85%;
  animation: messageSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
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
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.agent-avatar {
  background-color: var(--panel-color);
  border: 1px solid var(--border-color-light);
  box-shadow: var(--shadow-subtle);
}

.avatar-svg {
  width: 20px;
  height: 20px;
}

.user-avatar {
  background-color: var(--google-blue);
  color: white;
  font-weight: 700;
  font-size: 14px;
}

.user-initial {
  display: inline-block;
  line-height: 1;
}

/* Bubbles */
.message-bubble-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 100%;
}

.message-bubble {
  padding: 16px 20px;
  border-radius: var(--radius-md);
  line-height: 1.6;
  font-size: 15px;
}

.user-row .message-bubble {
  background-color: var(--google-blue-soft);
  color: var(--google-blue-text);
  border-top-right-radius: 4px;
}

.agent-row .message-bubble {
  background-color: var(--panel-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color-light);
  border-top-left-radius: 4px;
  box-shadow: var(--shadow-subtle);
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
  padding: 16px 24px;
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
  height: 130px;
  background-color: #F8F9FA;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-color-light);
  overflow: hidden;
}

.product-img-wrapper img {
  max-width: 80%;
  max-height: 80%;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.product-card:hover .product-img-wrapper img {
  transform: scale(1.06);
}

.product-info {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  gap: 6px;
}

.product-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-price {
  font-size: 15px;
  font-weight: 700;
  color: var(--google-blue-text);
}

.product-desc {
  font-size: 12px;
  color: var(--text-secondary);
  height: 36px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
}

.buy-btn {
  margin-top: 10px;
  background-color: var(--google-blue);
  color: white;
  border: none;
  border-radius: var(--radius-pill);
  padding: 8px 16px;
  font-family: var(--font-family);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.buy-btn:hover {
  background-color: #1557b0;
}

.buy-btn:active {
  transform: scale(0.97);
}

/* Floating Bottom Input Area */
.bottom-input-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, #ffffff 35%, #ffffff 100%);
  padding: 24px;
  z-index: 90;
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
  background-color: #F8F9FA;
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: left;
  font-size: 14px;
  border: 1px solid var(--border-color-light);
  margin-bottom: 20px;
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
  .welcome-hero h2 {
    font-size: 26px;
  }
  
  .chat-feed-container {
    padding: 24px 16px 150px 16px;
    gap: 20px;
  }
  
  .message-row {
    max-width: 90%;
    gap: 12px;
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
