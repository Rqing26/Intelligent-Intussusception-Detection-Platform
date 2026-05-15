<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <span class="app-title">肠套叠AI辅助诊断平台</span>
      <div class="app-header-right">
        <span class="app-user">{{ auth.user?.display_name || auth.user?.username }}</span>
        <el-button text @click="handleLogout" style="color: #fff">退出登录</el-button>
      </div>
    </el-header>
    <el-container>
      <el-aside width="200px" class="app-aside">
        <el-menu
          :default-active="route.path"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
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

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1a73e8;
  color: #fff;
  padding: 0 20px;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
}

.app-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-aside {
  background: #304156;
}

.el-menu {
  border-right: none;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>
