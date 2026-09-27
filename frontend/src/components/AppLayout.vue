<template>
  <div class="app-layout" :class="{ 'nav-collapsed': isCollapse }">
    <aside class="app-aside" aria-label="主导航">
      <router-link to="/patients" class="sidebar-brand" aria-label="返回患者管理">
        <span class="brand-mark"><img src="/newlogo.png" alt="弋矶山医院院徽" /></span>
        <span class="brand-copy"><strong>弋矶山医院</strong><small>智能辅助诊断平台</small></span>
      </router-link>

      <div class="nav-section-label">临床工作空间 <span>WORKSPACE</span></div>
      <nav class="app-nav">
        <router-link to="/patients" class="nav-item" :class="{ 'is-active': route.path.startsWith('/patients') || route.path.startsWith('/results') }" active-class="is-active" title="患者管理">
          <el-icon><User /></el-icon><span class="nav-label">患者管理</span><span class="nav-indicator" />
        </router-link>
        <router-link to="/history" class="nav-item" active-class="is-active" title="检测记录">
          <el-icon><DataAnalysis /></el-icon><span class="nav-label">检测记录</span><span class="nav-indicator" />
        </router-link>
        <router-link v-if="isAdmin" to="/audit" class="nav-item" active-class="is-active" title="审计日志">
          <el-icon><Document /></el-icon><span class="nav-label">审计日志</span><span class="nav-indicator" />
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <div class="clinical-note">
          <span class="note-symbol"><el-icon><FirstAidKit /></el-icon></span>
          <strong>以影像为依据，以关怀为本</strong>
          <p>AI 辅助影像分析<br />诊断结果请结合临床复核</p>
          <span class="note-line" />
        </div>
        <div class="hospital-signature"><span class="signature-line" /><strong>皖南医学院第一附属医院</strong><small>YIJISHAN HOSPITAL · 1888</small></div>
      </div>
    </aside>

    <div class="app-workspace">
      <header class="app-header">
        <div class="header-left">
          <button class="icon-button nav-toggle" :aria-label="isCollapse ? '展开导航栏' : '折叠导航栏'" :aria-expanded="!isCollapse" @click="toggleNav">
            <el-icon><Expand v-if="isCollapse" /><Fold v-else /></el-icon>
          </button>
          <div class="breadcrumb"><span>临床工作台</span><el-icon><ArrowRight /></el-icon><strong>{{ pageLabel }}</strong></div>
          <span class="mobile-brand">弋矶山 · 智能诊断</span>
        </div>
        <div class="header-actions">
          <button class="theme-button" @click="handleToggleTheme" :aria-label="currentTheme === 'modern' ? '切换暖色主题' : '切换标准主题'" :title="currentTheme === 'modern' ? '切换暖色主题' : '切换标准主题'">
            <el-icon><Sunny v-if="currentTheme === 'modern'" /><Moon v-else /></el-icon><span>{{ currentTheme === 'modern' ? '标准主题' : '暖色主题' }}</span>
          </button>
          <span class="header-divider" />
          <div class="user-profile"><span class="user-avatar">{{ userName.slice(0, 1) }}</span><span class="user-copy"><strong>{{ userName }}</strong><small>{{ isAdmin ? '系统管理员' : '临床医生' }}</small></span></div>
          <button class="icon-button logout-button" title="退出登录" aria-label="退出登录" @click="handleLogout"><el-icon><SwitchButton /></el-icon></button>
        </div>
      </header>
      <main id="main-content" class="app-main">
        <div class="app-content"><slot /></div>
        <footer class="workspace-footer"><span>肠套叠 AI 辅助诊断平台</span><span>专注影像 · 关爱儿童健康</span></footer>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, DataAnalysis, Document, FirstAidKit, Expand, Fold, ArrowRight, Sunny, Moon, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { toggleTheme, getCurrentTheme } from '../utils/theme'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const settings = useSettingsStore()
const currentTheme = ref(getCurrentTheme())
const isAdmin = computed(() => auth.user?.role === 'admin')
const userName = computed(() => auth.user?.full_name || auth.user?.username || '医生')
const pageLabel = computed(() => ({ PatientList: '患者管理', PatientDetail: '患者档案', ImageUpload: '上传影像', DetectionResult: '检测结果', History: '检测记录', Audit: '审计日志' }[route.name] || '工作台'))
const NAV_COLLAPSED_KEY = 'nav_collapsed'
const isCollapse = ref(false)
let mediaQuery
function readPref() {
  try { return localStorage.getItem(NAV_COLLAPSED_KEY) === '1' } catch { return false }
}
function toggleNav() {
  isCollapse.value = !isCollapse.value
  try { localStorage.setItem(NAV_COLLAPSED_KEY, isCollapse.value ? '1' : '0') } catch { /* Optional preference. */ }
}
function handleNarrowChange(event) { isCollapse.value = event.matches || readPref() }
onMounted(() => {
  mediaQuery = window.matchMedia('(max-width: 1100px)')
  handleNarrowChange(mediaQuery)
  mediaQuery.addEventListener('change', handleNarrowChange)
})
onUnmounted(() => mediaQuery?.removeEventListener('change', handleNarrowChange))
function handleToggleTheme() {
  currentTheme.value = toggleTheme()
  if (auth.user) settings.updateTheme(currentTheme.value).catch(() => {})
}
function handleLogout() { auth.logout(); router.push('/login') }
</script>

<style scoped>
.app-layout { --sidebar-width: 240px; display: flex; min-height: 100vh; height: 100dvh; background: var(--bg-page); }
.app-layout.nav-collapsed { --sidebar-width: 80px; }
.app-aside { width: var(--sidebar-width); flex-shrink: 0; background: var(--bg-sidebar); color: #fff; display: flex; flex-direction: column; overflow: hidden; transition: width .24s ease; position: relative; z-index: 20; }
.sidebar-brand { min-height: 104px; padding: 24px 22px; display: flex; gap: 12px; align-items: center; text-decoration: none; color: #fff; box-sizing: border-box; }
.brand-mark { width: 44px; height: 44px; padding: 3px; flex-shrink: 0; border-radius: 50%; background: #fff; display: grid; place-items: center; }
.brand-mark img { width: 100%; height: 100%; object-fit: contain; }
.brand-copy { white-space: nowrap; display: flex; flex-direction: column; gap: 7px; }
.brand-copy strong { font-size: 19px; font-weight: 600; letter-spacing: 2px; }
.brand-copy small { font-size: 10px; color: #a3c2bf; letter-spacing: 1.1px; }
.nav-section-label { color: #739894; font-size: 10px; letter-spacing: 1.4px; padding: 25px 27px 16px; white-space: nowrap; }
.nav-section-label span { display: block; font-size: 8px; letter-spacing: 2.2px; margin-top: 7px; opacity: .65; }
.app-nav { padding: 0 14px; display: flex; flex-direction: column; gap: 8px; }
.nav-item { height: 50px; padding: 0 17px; border-radius: 10px; color: var(--text-sidebar); display: flex; align-items: center; gap: 13px; font-size: 13px; text-decoration: none; white-space: nowrap; position: relative; transition: background .18s, color .18s; }
.nav-item .el-icon { font-size: 20px; flex-shrink: 0; }
.nav-item:hover { background: var(--bg-sidebar-hover); color: #fff; }
.nav-item.is-active { background: #25534f; color: #fff; }
.nav-item.is-active .el-icon { color: #a2d9c8; }
.nav-indicator { display: none; margin-left: auto; width: 5px; height: 5px; border-radius: 50%; background: #b5d8b6; }
.is-active .nav-indicator { display: block; }
.sidebar-bottom { margin-top: auto; padding: 40px 22px 25px; }
.clinical-note { border: 1px solid rgba(172,209,196,.13); background: rgba(255,255,255,.025); padding: 18px 15px 16px; border-radius: 12px; position: relative; overflow: hidden; }
.note-symbol { color: #afc8a9; display: block; font-size: 22px; margin-bottom: 16px; }
.clinical-note strong { font-size: 11px; color: #dbe7de; font-weight: 500; white-space: nowrap; }
.clinical-note p { font-size: 10px; line-height: 1.9; color: #87aaa6; margin: 8px 0 0; }
.note-line { position: absolute; right: -20px; bottom: -33px; height: 100px; width: 100px; border: 1px solid #3e6258; border-radius: 50%; opacity: .4; }
.hospital-signature { padding: 25px 1px 0; white-space: nowrap; }
.signature-line { display: block; width: 25px; height: 1px; background: #b5a57e; margin-bottom: 13px; }
.hospital-signature strong { font-size: 10px; font-weight: 400; color: #93b2ad; display: block; }
.hospital-signature small { display: block; font-size: 8px; letter-spacing: 1.15px; color: #628983; margin-top: 7px; }
.app-workspace { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.app-header { height: 78px; flex-shrink: 0; padding: 0 36px; background: var(--bg-header); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.header-left, .header-actions { display: flex; align-items: center; gap: 20px; }
.header-left { min-width: 0; }
.icon-button { width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; border: none; color: var(--text-secondary); background: transparent; border-radius: 8px; cursor: pointer; font-size: 18px; flex-shrink: 0; }
.icon-button:hover { background: var(--bg-hover); color: var(--primary); }
.breadcrumb { display: flex; align-items: center; gap: 13px; font-size: 12px; white-space: nowrap; }
.breadcrumb > span { color: var(--text-muted); }
.breadcrumb .el-icon { color: var(--border-strong); font-size: 11px; }
.breadcrumb strong { font-weight: 500; color: var(--text-primary); }
.theme-button { display: flex; align-items: center; gap: 7px; background: transparent; border: 0; cursor: pointer; color: var(--text-secondary); font-size: 11px; padding: 8px; border-radius: 8px; font-family: inherit; }
.theme-button:hover { background: var(--bg-hover); }
.theme-button .el-icon { font-size: 17px; }
.header-divider { width: 1px; height: 25px; background: var(--border-color); }
.user-profile { display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 35px; height: 35px; display: grid; place-items: center; background: #e4eee8; border: 3px solid #f4f7f4; color: #3f6a5d; border-radius: 50%; font-size: 13px; font-weight: 600; }
.user-copy { display: flex; flex-direction: column; gap: 4px; }
.user-copy strong { font-size: 12px; font-weight: 600; }
.user-copy small { font-size: 9px; color: var(--text-muted); }
.logout-button { font-size: 16px; }
.app-main { flex: 1; overflow-y: auto; padding: 35px 36px 0; display: flex; flex-direction: column; }
.app-content { width: 100%; max-width: 1600px; margin: 0 auto; flex: 1; min-width: 0; }
.workspace-footer { max-width: 1600px; width: 100%; margin: 26px auto 0; padding: 19px 0; border-top: 1px solid var(--border-color); display: flex; justify-content: space-between; gap: 14px; color: var(--text-muted); font-size: 10px; letter-spacing: .4px; }
.mobile-brand { display: none; }
.nav-collapsed .brand-copy, .nav-collapsed .nav-section-label, .nav-collapsed .nav-label, .nav-collapsed .nav-indicator, .nav-collapsed .sidebar-bottom { display: none; }
.nav-collapsed .sidebar-brand { padding: 24px 18px; }
.nav-collapsed .brand-mark { width: 38px; height: 38px; }
.nav-collapsed .app-nav { margin-top: 29px; padding: 0 12px; }
.nav-collapsed .nav-item { padding: 0; justify-content: center; }
@media (max-width: 1200px) { .app-header { padding: 0 26px; } .app-main { padding: 28px 26px 0; } }
@media (max-width: 760px) {
  .app-layout { min-height: 100dvh; height: auto; }
  .app-aside { position: fixed; bottom: 0; left: 0; right: 0; width: 100%; height: calc(66px + env(safe-area-inset-bottom)); padding-bottom: env(safe-area-inset-bottom); background: var(--bg-card); border-top: 1px solid var(--border-color); }
  .sidebar-brand, .nav-section-label, .sidebar-bottom { display: none; }
  .app-nav, .nav-collapsed .app-nav { flex-direction: row; gap: 8px; padding: 7px 18px; margin: 0; justify-content: center; }
  .nav-item, .nav-collapsed .nav-item { flex: 1; max-width: 160px; height: 50px; padding: 5px; gap: 4px; flex-direction: column; justify-content: center; font-size: 10px; color: var(--text-muted); }
  .nav-collapsed .nav-label { display: block; }
  .nav-item .el-icon { font-size: 20px; }
  .nav-item.is-active { background: var(--primary-glow); color: var(--primary); }
  .nav-item.is-active .el-icon { color: var(--primary); }
  .nav-item:hover { color: var(--primary); background: var(--bg-hover); }
  .nav-indicator, .is-active .nav-indicator { display: none; }
  .app-header { padding: 0 18px; height: 65px; }
  .nav-toggle, .breadcrumb, .header-divider, .user-copy, .theme-button span { display: none; }
  .mobile-brand { display: block; font-size: 14px; font-weight: 600; letter-spacing: .4px; }
  .header-actions { gap: 8px; }
  .app-main { overflow: visible; padding: 24px 18px calc(82px + env(safe-area-inset-bottom)); }
  .workspace-footer { flex-direction: column; font-size: 9px; gap: 7px; }
}
</style>
