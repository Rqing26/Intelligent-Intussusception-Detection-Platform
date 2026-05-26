<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>
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

<style>
/* 页面切换动画 (微交互) */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
