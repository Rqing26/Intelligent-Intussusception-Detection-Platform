<template><router-view /></template>
<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { syncThemeFromBackend } from './utils/theme'
import { useSettingsStore } from './stores/settings'

const auth = useAuthStore()
const settings = useSettingsStore()

onMounted(async () => {
  await auth.fetchUser()
  if (auth.user) {
    await syncThemeFromBackend(settings)
  }
})
</script>
