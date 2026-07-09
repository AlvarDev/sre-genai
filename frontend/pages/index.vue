<template>
  <div class="chat-container">
    <!-- Header -->
    <header class="store-header">
      <div class="logo-container">
        <span class="g-blue">G</span>
        <span class="g-red">o</span>
        <span class="g-yellow">o</span>
        <span class="g-blue">g</span>
        <span class="g-green">l</span>
        <span class="g-red">e</span>
        <span class="header-subtitle">Store Assistant</span>
      </div>
      <div class="connection-status">
        <span class="status-dot"></span>
        <span class="status-text">Online</span>
      </div>
    </header>

    <!-- Message History Area -->
    <main class="chat-history" ref="historyContainer">
      <div class="welcome-box" v-if="messages.length === 0">
        <div class="welcome-icon">💬</div>
        <h2>Olá! Como posso ajudar você hoje?</h2>
        <p>Pergunte-me sobre os celulares Pixel, fones de ouvido, termostatos Nest ou roupas da marca Google.</p>
        <div class="suggestions">
          <button @click="sendSuggestion('Você tem o celular Pixel 9 Pro?')">"Você tem o Pixel 9 Pro?"</button>
          <button @click="sendSuggestion('Qual o preço do Nest Thermostat?')">"Qual o preço do Nest?"</button>
          <button @click="triggerImageUpload">"Buscar por Imagem 📷"</button>
        </div>
      </div>

      <div 
        v-for="(msg, index) in messages" 
        :key="index" 
        :class="['message-row', msg.role === 'user' ? 'user-row' : 'agent-row']"
      >
        <!-- Message Panel -->
        <div class="message-bubble">
          <!-- Image attachment if user sent an image -->
          <div class="image-attachment" v-if="msg.imageUrl">
            <img :src="msg.imageUrl" alt="Visual query preview" />
          </div>
          
          <div class="message-text" v-html="formatText(msg.content)"></div>
          
          <!-- Structured Product Carousel if attached to message -->
          <div class="product-carousel" v-if="msg.products && msg.products.length > 0">
            <div 
              v-for="prod in msg.products" 
              :key="prod.parent_sku" 
              class="product-card"
            >
              <div class="product-img-wrapper">
                <!-- If placeholder image URL, render a nice CSS mockup container -->
                <img :src="getValidImageUrl(prod.img_url)" :alt="prod.title" />
              </div>
              <div class="product-info">
                <h4 class="product-title">{{ prod.title }}</h4>
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

      <!-- Loading / Typing Indicator -->
      <div class="message-row agent-row" v-if="isTyping">
        <div class="message-bubble typing-bubble">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </main>

    <!-- Visual Search Image Preview Bar -->
    <div class="preview-bar" v-if="selectedImage">
      <div class="preview-img-container">
        <img :src="selectedImagePreview" alt="Selected image" />
        <button class="remove-preview-btn" @click="cancelImage">✕</button>
      </div>
      <div class="preview-text">
        Pronto para buscar com esta imagem. Adicione um comentário abaixo se desejar.
      </div>
    </div>

    <!-- Input Bar -->
    <footer class="input-area">
      <!-- Hidden File input for Visual Search -->
      <input 
        type="file" 
        ref="imageInput" 
        accept="image/*" 
        style="display: none" 
        @change="onImageSelected"
      />
      
      <button class="action-btn file-btn" @click="triggerImageUpload" title="Buscar por imagem">
        📷
      </button>
      
      <input 
        type="text" 
        v-model="inputText" 
        @keydown.enter="submitMessage"
        placeholder="Escreva sua mensagem..."
        :disabled="isTyping"
        ref="messageInput"
      />
      
      <button class="action-btn send-btn" @click="submitMessage" :disabled="!inputText.trim() && !selectedImage || isTyping">
        ➤
      </button>
    </footer>

    <!-- Mock Purchase Success Modal -->
    <div class="purchase-modal" v-if="activePurchase">
      <div class="modal-content">
        <div class="modal-success-icon">✓</div>
        <h3>Simulação de Compra Efetuada!</h3>
        <p>Você adquiriu o produto:</p>
        <div class="modal-product-detail">
          <strong>{{ activePurchase.title }}</strong><br/>
          SKU: <code>{{ activePurchase.parent_sku }}</code><br/>
          Valor: <strong>R$ {{ parseFloat(activePurchase.retail_price).toFixed(2) }}</strong>
        </div>
        <p class="modal-sre-notice">
          ℹ️ <strong>Métrica SRE</strong>: Esta ação simula um checkout com HTTP 200 OK. Nenhuma cobrança real foi efetuada.
        </p>
        <button class="modal-close-btn" @click="activePurchase = null">Fechar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { initializeApp } from 'firebase/app'
import { getAuth, signInAnonymously, connectAuthEmulator } from 'firebase/auth'

// 1. Config & Runtime Env
const config = useRuntimeConfig()
const backendUrl = config.public.backendUrl

// State Variables
const sessionId = ref('')
const userUid = ref('anonymous')
const messages = ref([])
const inputText = ref('')
const isTyping = ref(false)
const selectedImage = ref(null)
const selectedImagePreview = ref(null)
const activePurchase = ref(null)

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
    const auth = getAuth(app)
    
    // Connect to Auth emulator if configured in local development
    if (config.public.firebaseAuthEmulatorUrl) {
      console.log(`Connecting to Firebase Auth emulator: ${config.public.firebaseAuthEmulatorUrl}`)
      connectAuthEmulator(auth, config.public.firebaseAuthEmulatorUrl)
    }
    
    const userCredential = await signInAnonymously(auth)
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
    
    // Headers to isolate session
    const headers = {
      'x-user-uid': userUid.value
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
/* Main Chat Container CSS */
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  max-width: 600px;
  margin: 0 auto;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.05);
  border-left: 1px solid var(--border-color);
  border-right: 1px solid var(--border-color);
}

/* Header */
.store-header {
  height: var(--header-height);
  background-color: var(--panel-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  z-index: 10;
}

.logo-container {
  font-weight: 700;
  font-size: 20px;
  letter-spacing: -0.5px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.g-blue { color: var(--google-blue); }
.g-red { color: var(--google-red); }
.g-yellow { color: var(--google-yellow); }
.g-green { color: var(--google-green); }

.header-subtitle {
  font-weight: 400;
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 8px;
  border-left: 1px solid var(--border-color);
  padding-left: 8px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #E6F4EA;
  padding: 4px 10px;
  border-radius: 16px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--google-green);
}

.status-text {
  font-size: 11px;
  font-weight: 500;
  color: #137333;
}

/* Chat History Area */
.chat-history {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Welcome Box */
.welcome-box {
  text-align: center;
  margin: auto 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.welcome-icon {
  font-size: 48px;
}

.welcome-box h2 {
  font-weight: 500;
  font-size: 22px;
  color: var(--text-primary);
}

.welcome-box p {
  font-size: 14px;
  color: var(--text-secondary);
  max-width: 320px;
  line-height: 1.5;
}

.suggestions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 280px;
  margin-top: 10px;
}

.suggestions button {
  background-color: var(--panel-color);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 10px 16px;
  font-family: var(--font-family);
  font-size: 13px;
  color: var(--google-blue);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestions button:hover {
  background-color: #f1f3f4;
  border-color: #cbd0d4;
  transform: translateY(-1px);
}

/* Message Rows */
.message-row {
  display: flex;
  width: 100%;
}

.user-row {
  justify-content: flex-end;
}

.agent-row {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.5;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.user-row .message-bubble {
  background-color: var(--google-blue);
  color: white;
  border-bottom-right-radius: 4px;
}

.agent-row .message-bubble {
  background-color: var(--panel-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
}

.image-attachment img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 12px;
  margin-bottom: 8px;
  display: block;
}

/* Typing indicator animation */
.typing-bubble {
  padding: 12px 20px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background-color: var(--text-secondary);
  border-radius: 50%;
  animation: bounce 1.3s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

/* Swipable Carousel */
.product-carousel {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 12px 0 4px 0;
  width: 100%;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
}

/* Hide scrollbars but keep functionality */
.product-carousel::-webkit-scrollbar {
  display: none;
}

.product-card {
  flex: 0 0 180px;
  scroll-snap-align: start;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background-color: var(--panel-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.product-img-wrapper {
  height: 110px;
  background-color: #f1f3f4;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-color);
  overflow: hidden;
}

.product-img-wrapper img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.product-info {
  padding: 10px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  gap: 4px;
}

.product-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-price {
  font-size: 14px;
  font-weight: 700;
  color: var(--google-blue);
}

.product-desc {
  font-size: 11px;
  color: var(--text-secondary);
  height: 32px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
}

.buy-btn {
  margin-top: 6px;
  background-color: var(--google-blue);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 6px 0;
  font-family: var(--font-family);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.buy-btn:hover {
  opacity: 0.9;
}

/* Preview Bar */
.preview-bar {
  background-color: var(--panel-color);
  border-top: 1px solid var(--border-color);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  flex-shrink: 0;
}

.preview-img-container {
  position: relative;
  width: 50px;
  height: 50px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-color);
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
  font-size: 9px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-text {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Input Area */
.input-area {
  height: 70px;
  background-color: var(--panel-color);
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 10px 15px;
  gap: 10px;
  flex-shrink: 0;
}

.input-area input[type="text"] {
  flex-grow: 1;
  height: 44px;
  border-radius: 22px;
  border: 1px solid var(--border-color);
  padding: 0 20px;
  font-family: var(--font-family);
  font-size: 14px;
  outline: none;
  background-color: var(--bg-color);
  transition: border-color 0.2s;
}

.input-area input[type="text"]:focus {
  border-color: var(--google-blue);
  background-color: white;
}

.action-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  background-color: var(--panel-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.2s;
}

.file-btn:hover {
  background-color: #f1f3f4;
  transform: scale(1.03);
}

.send-btn {
  background-color: var(--google-blue);
  color: white;
  border: none;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.95;
  transform: scale(1.03);
}

.send-btn:disabled {
  background-color: #e8eaed;
  color: #9aa0a6;
  cursor: not-allowed;
}

/* Purchase Modal */
.purchase-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 380px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
  animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes popIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-success-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #E6F4EA;
  color: var(--google-green);
  font-size: 28px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px auto;
}

.modal-content h3 {
  font-weight: 500;
  font-size: 18px;
  margin-bottom: 8px;
}

.modal-content p {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.modal-product-detail {
  background-color: var(--bg-color);
  border-radius: 8px;
  padding: 12px;
  text-align: left;
  font-size: 13px;
  border: 1px solid var(--border-color);
  margin-bottom: 16px;
}

.modal-product-detail code {
  background: #e8eaed;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.modal-sre-notice {
  font-size: 11px !important;
  color: var(--text-secondary);
  background: #FEF7E0;
  border: 1px solid #FFE0B2;
  border-radius: 6px;
  padding: 8px;
  text-align: left;
  margin-bottom: 20px;
  line-height: 1.4;
}

.modal-close-btn {
  background-color: var(--google-blue);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-family: var(--font-family);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
}
</style>
