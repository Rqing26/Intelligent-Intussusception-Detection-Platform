<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="header-brand">
        <span class="brand-icon">+</span>
        <span class="brand-title">肠套叠AI辅助诊断平台</span>
      </div>
      <div class="header-actions">
        <button class="theme-toggle" @click="handleToggleTheme" :title="currentTheme === 'modern' ? '切换至中世纪风格' : '切换至现代风格'">
          <span v-if="currentTheme === 'modern'">🏛</span>
          <span v-else>⚡</span>
          <span class="toggle-label">{{ currentTheme === 'modern' ? '手稿' : '现代' }}</span>
        </button>
        <div class="user-divider" />
        <span class="app-user">{{ auth.user?.display_name || auth.user?.username }}</span>
        <el-button text class="logout-btn" @click="handleLogout">
          退出登录
        </el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="220px" class="app-aside">
        <el-menu
          :default-active="route.path"
          router
          class="app-menu"
        >
          <el-menu-item index="/patients">
            <el-icon><User /></el-icon>
            <span>患者管理</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>检测记录</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { toggleTheme, getCurrentTheme } from '../utils/theme'
import { ref, onMounted } from 'vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const settings = useSettingsStore()
const currentTheme = ref(getCurrentTheme())

function handleToggleTheme() {
  const next = toggleTheme()
  currentTheme.value = next
  if (auth.user) {
    settings.updateTheme(next)
  }
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
  background: var(--bg-page);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0 28px;
  box-shadow: var(--shadow-sm);
  z-index: 10;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  width: 28px;
  height: 28px;
  border: 1.5px solid var(--gold);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  border-radius: var(--radius-sm);
}

.brand-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all 0.2s;
  font-family: var(--font-sans);
}

.theme-toggle:hover {
  border-color: var(--gold-dim);
  color: var(--text-primary);
}

.toggle-label {
  font-size: 12px;
}

.user-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
}

.app-user {
  font-size: 13px;
  color: var(--text-secondary);
}

.logout-btn {
  color: var(--text-muted) !important;
  font-size: 13px;
}
.logout-btn:hover {
  color: var(--text-primary) !important;
}

.app-aside {
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  transition: background 0.35s ease;
}

.app-menu {
  background: transparent !important;
  border-right: none !important;
  padding: 16px 12px;
}

:deep(.el-menu-item) {
  border-radius: var(--radius-sm);
  margin: 4px 0;
  height: 46px;
  line-height: 46px;
  color: var(--text-sidebar);
  transition: all 0.2s;
  font-family: var(--font-sans);
}

:deep(.el-menu-item .el-icon) {
  color: inherit;
}

:deep(.el-menu-item:hover) {
  background: var(--bg-sidebar-hover) !important;
  color: var(--text-inverse) !important;
}

:deep(.el-menu-item.is-active) {
  background: rgba(184, 148, 31, 0.12) !important;
  color: var(--text-sidebar-active) !important;
  font-weight: 700;
  box-shadow: inset 3px 0 0 var(--gold);
}

.app-main {
  background: var(--bg-main);
  padding: 24px 28px;
  overflow-y: auto;
}
</style>
