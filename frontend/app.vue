<script setup>
const isDarkMode = useState('darkMode', () => true)
</script>

<template>
  <div :class="['app-container', isDarkMode ? 'theme-dark' : 'theme-light']">
    <NuxtPage />
  </div>
</template>

<style>
/* Root CSS Variables (Google Brand Palette & Styling Tokens) */
:root {
  --font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  
  /* Brand Colors (Common) */
  --google-blue: #3186FF;
  --google-red: #FC413D;
  --google-yellow: #FEC700;
  --google-green: #00AF57;
  
  /* Layout Spaces */
  --header-height: 64px;
  --max-content-width: 860px;
  
  /* Border Radii */
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-pill: 100px;
  
  /* Shadows (Common) */
  --shadow-subtle: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3.1px rgba(60,64,67,0.15);
  --shadow-card: 0 1px 3px 0 rgba(60,64,67,0.12), 0 4px 8px 3px rgba(60,64,67,0.08);
  --shadow-hover: 0 4px 12px 0 rgba(60,64,67,0.16);
  --shadow-input: 0 1px 2px 0 rgba(60,64,67,0.3), 0 2px 6px 2px rgba(60,64,67,0.15);
}

/* Light Theme Variables */
.app-container.theme-light {
  --bg-color: #FFFFFF;
  --bg-color-alt: #FFFFFF;
  --panel-color: #FFFFFF;
  --text-primary: #202124;
  --text-secondary: #4e5256;
  --border-color: #DADCE0;
  --border-color-light: #F1F3F4;
  
  --google-blue-soft: #E8F1FF;
  --google-blue-text: #3186FF;
  --google-red-soft: #FFF1F0;
  --google-red-text: #FC413D;
  --google-yellow-soft: #FFFBE6;
  --google-yellow-text: #D48E00;
  --google-green-soft: #F6FFED;
  --google-green-text: #00AF57;
  
  --theme-gradient: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, #ffffff 35%, #ffffff 100%);
  --card-inner-bg: #F8F9FA;
  --user-bubble-border: transparent;
}

/* Dark Theme Variables */
.app-container.theme-dark {
  --bg-color: #131314;
  --bg-color-alt: #131314;
  --panel-color: #1e1e20;
  --text-primary: #e3e3e3;
  --text-secondary: #a8a8a8;
  --border-color: #3c4043;
  --border-color-light: #2e3032;
  
  --google-blue-soft: rgba(49, 134, 255, 0.15);
  --google-blue-text: #8ab4f8;
  --google-red-soft: rgba(252, 65, 61, 0.15);
  --google-red-text: #f89492;
  --google-yellow-soft: rgba(254, 199, 0, 0.15);
  --google-yellow-text: #ffe082;
  --google-green-soft: rgba(0, 175, 87, 0.15);
  --google-green-text: #81c784;
  
  --theme-gradient: linear-gradient(180deg, rgba(19, 19, 20, 0) 0%, #131314 35%, #131314 100%);
  --card-inner-bg: #131314;
  --user-bubble-border: rgba(49, 134, 255, 0.25);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-family);
  background-color: var(--bg-color-alt);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
