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
  --google-blue: #3186FF;
  --google-red: #FC413D;
  --google-yellow: #FEC700;
  --google-green: #00AF57;
  
  /* Brand Soft Colors (Google Startups Palette) */
  --google-blue-soft: #E8F1FF;
  --google-blue-text: #3186FF;
  --google-red-soft: #FFF1F0;
  --google-red-text: #FC413D;
  --google-yellow-soft: #FFFBE6;
  --google-yellow-text: #D48E00;
  --google-green-soft: #F6FFED;
  --google-green-text: #00AF57;
  
  /* Neutral Palette */
  --bg-color: #FFFFFF;
  --bg-color-alt: #FFFFFF;
  --panel-color: #FFFFFF;
  --text-primary: #202124;
  --text-secondary: #4e5256;
  --border-color: #DADCE0;
  --border-color-light: #F1F3F4;
  
  /* Layout Spaces */
  --header-height: 64px;
  --max-content-width: 860px;
  
  /* Border Radii */
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-pill: 100px;
  
  /* Shadows */
  --shadow-subtle: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3.1px rgba(60,64,67,0.15);
  --shadow-card: 0 1px 3px 0 rgba(60,64,67,0.12), 0 4px 8px 3px rgba(60,64,67,0.08);
  --shadow-hover: 0 4px 12px 0 rgba(60,64,67,0.16);
  --shadow-input: 0 1px 2px 0 rgba(60,64,67,0.3), 0 2px 6px 2px rgba(60,64,67,0.15);
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
