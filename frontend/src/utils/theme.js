const THEME_KEY = 'app_theme'
const DEFAULT_THEME = 'modern'

export function getCurrentTheme() {
  return document.documentElement.getAttribute('data-theme') || DEFAULT_THEME
}

export function setTheme(theme) {
  const valid = theme === 'modern' || theme === 'medieval' ? theme : DEFAULT_THEME
  document.documentElement.setAttribute('data-theme', valid)
  localStorage.setItem(THEME_KEY, valid)
  // Sync Element Plus primary color variable to current theme
  const rootStyles = getComputedStyle(document.documentElement)
  const primary = rootStyles.getPropertyValue('--el-color-primary').trim()
  if (primary) {
    document.documentElement.style.setProperty('--el-color-primary', primary)
  }
}

export function toggleTheme() {
  const current = getCurrentTheme()
  const next = current === 'modern' ? 'medieval' : 'modern'
  setTheme(next)
  return next
}

export function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) || DEFAULT_THEME
  setTheme(saved)
}

export async function syncThemeFromBackend(settingsStore) {
  try {
    await settingsStore.fetchSettings()
    const backendTheme = settingsStore.theme
    if (backendTheme && (backendTheme === 'modern' || backendTheme === 'medieval')) {
      setTheme(backendTheme)
    }
  } catch {
    // ignore
  }
}

export async function saveThemeToBackend(settingsStore, theme) {
  try {
    await settingsStore.updateTheme(theme)
  } catch {
    // ignore
  }
}
