<template>
  <div class="app-container">
    <NuxtPage />
  </div>
</template>

<style>
/* Root CSS Variables (Google Brand Palette & Styling Tokens) */
:root {
  --font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  
  /* Brand Colors */
  --google-blue: #1A73E8;
  --google-red: #EA4335;
  --google-yellow: #FBBC05;
  --google-green: #34A853;
  
  /* Neutral Palette */
  --bg-color: #F8F9FA;
  --panel-color: #FFFFFF;
  --text-primary: #202124;
  --text-secondary: #5F6368;
  --border-color: #DADCE0;
  
  /* Layout Spaces */
  --header-height: 64px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-family);
  background-color: var(--bg-color);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
