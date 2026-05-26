<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="login-bg">
      <div class="bg-blob bg-blob-1" />
      <div class="bg-blob bg-blob-2" />
      <div class="bg-grid" />

      <!-- 全页淡色几何医学背景 -->
      <svg class="bg-pattern bg-pattern-target" viewBox="0 0 400 400" fill="none">
        <circle cx="200" cy="200" r="180" stroke="currentColor" stroke-width="0.6" />
        <circle cx="200" cy="200" r="140" stroke="currentColor" stroke-width="0.6" />
        <circle cx="200" cy="200" r="100" stroke="currentColor" stroke-width="0.6" />
        <circle cx="200" cy="200" r="60" stroke="currentColor" stroke-width="0.8" />
        <line x1="200" y1="20" x2="200" y2="380" stroke="currentColor" stroke-width="0.3" />
        <line x1="20" y1="200" x2="380" y2="200" stroke="currentColor" stroke-width="0.3" />
        <line x1="60" y1="60" x2="340" y2="340" stroke="currentColor" stroke-width="0.3" />
        <line x1="340" y1="60" x2="60" y2="340" stroke="currentColor" stroke-width="0.3" />
      </svg>

      <svg class="bg-pattern bg-pattern-radial" viewBox="0 0 400 400" fill="none">
        <circle cx="200" cy="200" r="190" stroke="currentColor" stroke-width="0.5" />
        <circle cx="200" cy="200" r="150" stroke="currentColor" stroke-width="0.5" />
        <circle cx="200" cy="200" r="110" stroke="currentColor" stroke-width="0.5" />
        <circle cx="200" cy="200" r="70" stroke="currentColor" stroke-width="0.5" />
        <line x1="200" y1="10" x2="200" y2="390" stroke="currentColor" stroke-width="0.4" />
        <line x1="10" y1="200" x2="390" y2="200" stroke="currentColor" stroke-width="0.4" />
        <line x1="60" y1="60" x2="340" y2="340" stroke="currentColor" stroke-width="0.4" />
        <line x1="340" y1="60" x2="60" y2="340" stroke="currentColor" stroke-width="0.4" />
        <line x1="106" y1="32" x2="294" y2="368" stroke="currentColor" stroke-width="0.3" />
        <line x1="294" y1="32" x2="106" y2="368" stroke="currentColor" stroke-width="0.3" />
        <line x1="32" y1="106" x2="368" y2="294" stroke="currentColor" stroke-width="0.3" />
        <line x1="368" y1="106" x2="32" y2="294" stroke="currentColor" stroke-width="0.3" />
      </svg>

      <svg class="bg-pattern bg-pattern-intestine" viewBox="0 0 500 320" fill="none">
        <g transform="translate(100,160)">
          <circle r="70" stroke="currentColor" stroke-width="0.6" />
          <circle r="55" stroke="currentColor" stroke-width="0.5" />
          <circle r="40" stroke="currentColor" stroke-width="0.6" />
          <circle r="25" stroke="currentColor" stroke-width="0.5" />
          <circle r="10" stroke="currentColor" stroke-width="0.6" />
        </g>
        <g transform="translate(250,100)">
          <circle r="60" stroke="currentColor" stroke-width="0.6" />
          <circle r="45" stroke="currentColor" stroke-width="0.5" />
          <circle r="30" stroke="currentColor" stroke-width="0.6" />
          <circle r="15" stroke="currentColor" stroke-width="0.5" />
        </g>
        <g transform="translate(250,220)">
          <circle r="55" stroke="currentColor" stroke-width="0.6" />
          <circle r="42" stroke="currentColor" stroke-width="0.5" />
          <circle r="28" stroke="currentColor" stroke-width="0.6" />
          <circle r="14" stroke="currentColor" stroke-width="0.5" />
        </g>
        <g transform="translate(400,160)">
          <circle r="65" stroke="currentColor" stroke-width="0.6" />
          <circle r="50" stroke="currentColor" stroke-width="0.5" />
          <circle r="35" stroke="currentColor" stroke-width="0.6" />
          <circle r="20" stroke="currentColor" stroke-width="0.5" />
        </g>
        <line x1="170" y1="160" x2="190" y2="100" stroke="currentColor" stroke-width="0.3" />
        <line x1="170" y1="160" x2="190" y2="220" stroke="currentColor" stroke-width="0.3" />
        <line x1="310" y1="100" x2="310" y2="160" stroke="currentColor" stroke-width="0.3" />
        <line x1="310" y1="220" x2="310" y2="160" stroke="currentColor" stroke-width="0.3" />
        <line x1="335" y1="160" x2="335" y2="160" stroke="currentColor" stroke-width="0.3" />
      </svg>
    </div>

    <!-- 主题切换 -->
    <div
      class="theme-float-btn"
      @click="handleToggleTheme"
      :title="currentTheme === 'modern' ? '切换至中世纪风格' : '切换至现代风格'"
    >
      <span v-if="currentTheme === 'modern'">🏛</span>
      <span v-else>⚡</span>
    </div>

    <div class="login-wrap">
      <!-- 左侧品牌区 -->
      <div class="login-visual">
        <!-- 医学线性图案背景 — 肠套叠超声特征几何化 -->
        <!-- 同心圆靶环征 -->
        <svg class="medical-pattern pattern-target" viewBox="0 0 240 240" fill="none">
          <circle cx="120" cy="120" r="110" stroke="currentColor" stroke-width="0.8" />
          <circle cx="120" cy="120" r="90" stroke="currentColor" stroke-width="0.8" />
          <circle cx="120" cy="120" r="70" stroke="currentColor" stroke-width="0.8" />
          <circle cx="120" cy="120" r="50" stroke="currentColor" stroke-width="1.2" />
          <circle cx="120" cy="120" r="30" stroke="currentColor" stroke-width="0.8" />
          <circle cx="120" cy="120" r="10" stroke="currentColor" stroke-width="0.8" />
          <line x1="120" y1="10" x2="120" y2="230" stroke="currentColor" stroke-width="0.4" />
          <line x1="10" y1="120" x2="230" y2="120" stroke="currentColor" stroke-width="0.4" />
          <line x1="36" y1="36" x2="204" y2="204" stroke="currentColor" stroke-width="0.4" />
          <line x1="204" y1="36" x2="36" y2="204" stroke="currentColor" stroke-width="0.4" />
        </svg>

        <!-- 套筒征侧视 — 梯形套叠 -->
        <svg class="medical-pattern pattern-telescope" viewBox="0 0 200 300" fill="none">
          <path d="M60 20 L140 20 L150 80 L50 80 Z" stroke="currentColor" stroke-width="1" />
          <path d="M55 80 L145 80 L155 140 L45 140 Z" stroke="currentColor" stroke-width="1" />
          <path d="M50 140 L150 140 L160 200 L40 200 Z" stroke="currentColor" stroke-width="1" />
          <path d="M45 200 L155 200 L165 260 L35 260 Z" stroke="currentColor" stroke-width="1" />
          <line x1="100" y1="20" x2="100" y2="260" stroke="currentColor" stroke-width="0.4" stroke-dasharray="4 4" />
          <line x1="70" y1="50" x2="130" y2="50" stroke="currentColor" stroke-width="0.4" />
          <line x1="65" y1="110" x2="135" y2="110" stroke="currentColor" stroke-width="0.4" />
          <line x1="60" y1="170" x2="140" y2="170" stroke="currentColor" stroke-width="0.4" />
          <line x1="55" y1="230" x2="145" y2="230" stroke="currentColor" stroke-width="0.4" />
        </svg>

        <!-- 放射状网格 — 超声扫描线 -->
        <svg class="medical-pattern pattern-radial" viewBox="0 0 300 300" fill="none">
          <circle cx="150" cy="150" r="130" stroke="currentColor" stroke-width="0.6" />
          <circle cx="150" cy="150" r="100" stroke="currentColor" stroke-width="0.6" />
          <circle cx="150" cy="150" r="70" stroke="currentColor" stroke-width="0.6" />
          <circle cx="150" cy="150" r="40" stroke="currentColor" stroke-width="0.6" />
          <line x1="150" y1="20" x2="150" y2="280" stroke="currentColor" stroke-width="0.5" />
          <line x1="20" y1="150" x2="280" y2="150" stroke="currentColor" stroke-width="0.5" />
          <line x1="46" y1="46" x2="254" y2="254" stroke="currentColor" stroke-width="0.5" />
          <line x1="254" y1="46" x2="46" y2="254" stroke="currentColor" stroke-width="0.5" />
          <line x1="91" y1="25" x2="209" y2="275" stroke="currentColor" stroke-width="0.4" />
          <line x1="209" y1="25" x2="91" y2="275" stroke="currentColor" stroke-width="0.4" />
          <line x1="25" y1="91" x2="275" y2="209" stroke="currentColor" stroke-width="0.4" />
          <line x1="275" y1="91" x2="25" y2="209" stroke="currentColor" stroke-width="0.4" />
        </svg>

        <!-- 肠道横切面阵列 — 多个同心圆组 -->
        <svg class="medical-pattern pattern-intestine" viewBox="0 0 320 200" fill="none">
          <g transform="translate(60,100)">
            <circle r="45" stroke="currentColor" stroke-width="0.8" />
            <circle r="35" stroke="currentColor" stroke-width="0.6" />
            <circle r="25" stroke="currentColor" stroke-width="0.8" />
            <circle r="15" stroke="currentColor" stroke-width="0.6" />
            <circle r="5" stroke="currentColor" stroke-width="0.8" />
          </g>
          <g transform="translate(160,60)">
            <circle r="40" stroke="currentColor" stroke-width="0.8" />
            <circle r="30" stroke="currentColor" stroke-width="0.6" />
            <circle r="20" stroke="currentColor" stroke-width="0.8" />
            <circle r="10" stroke="currentColor" stroke-width="0.6" />
          </g>
          <g transform="translate(160,140)">
            <circle r="38" stroke="currentColor" stroke-width="0.8" />
            <circle r="28" stroke="currentColor" stroke-width="0.6" />
            <circle r="18" stroke="currentColor" stroke-width="0.8" />
            <circle r="8" stroke="currentColor" stroke-width="0.6" />
          </g>
          <g transform="translate(260,100)">
            <circle r="42" stroke="currentColor" stroke-width="0.8" />
            <circle r="32" stroke="currentColor" stroke-width="0.6" />
            <circle r="22" stroke="currentColor" stroke-width="0.8" />
            <circle r="12" stroke="currentColor" stroke-width="0.6" />
          </g>
          <line x1="105" y1="100" x2="120" y2="60" stroke="currentColor" stroke-width="0.4" />
          <line x1="105" y1="100" x2="120" y2="140" stroke="currentColor" stroke-width="0.4" />
          <line x1="200" y1="60" x2="200" y2="102" stroke="currentColor" stroke-width="0.4" />
          <line x1="200" y1="140" x2="200" y2="98" stroke="currentColor" stroke-width="0.4" />
          <line x1="218" y1="100" x2="218" y2="100" stroke="currentColor" stroke-width="0.4" />
        </svg>

        <div class="visual-content">
          <div class="brand-header">
            <div class="logo-ring">
              <img src="/newlogo.png" alt="logo" class="brand-logo" />
            </div>
            <div class="brand-text">
              <div class="brand-name">皖南医学院</div>
              <div class="brand-sub">第一附属医院（弋矶山医院）</div>
            </div>
          </div>

          <div class="hero">
            <h1 class="hero-title">
              肠套叠 AI<br />
              <span class="hero-accent">辅助诊断平台</span>
            </h1>
            <p class="hero-desc">
              基于深度学习的超声影像智能分析<br />
              为儿科医生提供精准、高效的辅助诊断支持
            </p>
          </div>
        </div>

        <!-- 装饰圆环 -->
        <div class="deco-ring deco-ring-1" />
        <div class="deco-ring deco-ring-2" />
        <div class="deco-dots" />
      </div>

      <!-- 右侧表单区 -->
      <div class="login-form-area">
        <div class="form-card">
          <div class="form-header">
            <div class="form-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <h2 class="form-title">医生登录</h2>
            <p class="form-subtitle">请使用院内账号登录系统</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="login-form"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <div class="input-label">用户名</div>
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
                class="login-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <div class="input-label">密码</div>
              <el-input
                v-model="form.password"
                type="password"
                show-password
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                class="login-input"
              />
            </el-form-item>

            <el-form-item class="submit-item">
              <el-button
                type="primary"
                native-type="submit"
                :loading="loading"
                size="large"
                class="login-btn"
              >
                <span class="btn-text">登 录</span>
                <svg class="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </el-button>
            </el-form-item>
          </el-form>

          <div class="form-footer">
            <div class="divider">
              <span class="divider-line" />
              <span class="divider-text">院内系统</span>
              <span class="divider-line" />
            </div>
            <p class="copyright">皖南医学院第一附属医院（弋矶山医院）</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { toggleTheme, getCurrentTheme } from '../utils/theme'

const router = useRouter()
const authStore = useAuthStore()
const currentTheme = ref(getCurrentTheme())

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function handleToggleTheme() {
  currentTheme.value = toggleTheme()
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/patients')
  } catch {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
})
</script>

<style scoped>
/* ========== 页面基础 ========== */
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: var(--bg-page);
  overflow: hidden;
}

/* ========== 背景装饰 ========== */
.login-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: blobFloat 8s ease-in-out infinite;
}
.bg-blob-1 {
  width: 500px;
  height: 500px;
  top: -10%;
  left: -5%;
  background: var(--primary);
  animation-delay: 0s;
}
.bg-blob-2 {
  width: 400px;
  height: 400px;
  bottom: -10%;
  right: -5%;
  background: var(--gold);
  opacity: 0.2;
  animation-delay: -4s;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 1px 1px, var(--border-strong) 1px, transparent 0);
  background-size: 28px 28px;
  opacity: 0.35;
  mask-image: radial-gradient(ellipse at center, black 25%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 25%, transparent 75%);
}

/* 全页淡色几何背景图案 */
.bg-pattern {
  position: absolute;
  color: var(--border-strong);
  pointer-events: none;
  z-index: 0;
}
.bg-pattern-target {
  width: 500px;
  height: 500px;
  top: -8%;
  left: -6%;
  opacity: 0.25;
}
.bg-pattern-radial {
  width: 480px;
  height: 480px;
  bottom: -10%;
  right: -8%;
  opacity: 0.2;
}
.bg-pattern-intestine {
  width: 400px;
  height: 260px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0.12;
}

@keyframes blobFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.05); }
  66% { transform: translate(-15px, 15px) scale(0.95); }
}

/* ========== 主题切换按钮 ========== */
.theme-float-btn {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  z-index: 100;
  transition: all 0.25s ease;
}
.theme-float-btn:hover {
  transform: scale(1.1) rotate(8deg);
  box-shadow: var(--shadow-md);
}

/* ========== 登录卡片主体 ========== */
.login-wrap {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  max-width: 1024px;
  min-height: 600px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-book);
  animation: cardEnter 0.6s ease-out;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ========== 左侧品牌区 ========== */
.login-visual {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 56px 52px;
  background: var(--primary);
  color: var(--text-inverse);
  overflow: hidden;
}

/* 左侧背景纹理 */
.login-visual::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 30%, rgba(255,255,255,0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 70%, rgba(184,148,31,0.06) 0%, transparent 40%);
}

/* 医学线性图案 */
.medical-pattern {
  position: absolute;
  color: rgba(255,255,255,0.07);
  pointer-events: none;
  z-index: 1;
}
.pattern-target {
  width: 180px;
  height: 180px;
  top: 12%;
  right: 6%;
  opacity: 0.45;
}
.pattern-telescope {
  width: 120px;
  height: 180px;
  bottom: 15%;
  left: 6%;
  opacity: 0.4;
}
.pattern-radial {
  width: 220px;
  height: 220px;
  top: 50%;
  right: 2%;
  opacity: 0.35;
  transform: translateY(-50%);
}
.pattern-intestine {
  width: 260px;
  height: 160px;
  bottom: 6%;
  right: 12%;
  opacity: 0.3;
}

.visual-content {
  position: relative;
  z-index: 2;
}

/* 品牌头部 */
.brand-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 56px;
}

.logo-ring {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  padding: 3px;
  background: linear-gradient(135deg, rgba(255,255,255,0.3), rgba(184,148,31,0.3));
  flex-shrink: 0;
}
.logo-ring::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  padding: 2px;
  background: linear-gradient(135deg, rgba(255,255,255,0.5), transparent);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

.brand-logo {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  background: var(--text-inverse);
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.06em;
  line-height: 1.3;
  font-family: var(--font-display);
}
.brand-sub {
  font-size: 12px;
  opacity: 0.65;
  font-weight: 500;
  margin-top: 2px;
  letter-spacing: 0.02em;
}

/* Hero 区域 */
.hero {
  animation: slideUp 0.7s ease-out 0.15s both;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.04em;
  margin: 0 0 20px;
}
.hero-accent {
  position: relative;
  display: inline-block;
}
.hero-accent::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 0;
  right: 0;
  height: 8px;
  background: var(--gold);
  opacity: 0.35;
  border-radius: 2px;
}

.hero-desc {
  font-size: 14px;
  line-height: 1.9;
  opacity: 0.7;
  max-width: 300px;
  margin: 0;
  font-weight: 400;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 装饰元素 */
.deco-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.08);
  pointer-events: none;
}
.deco-ring-1 {
  width: 300px;
  height: 300px;
  bottom: -80px;
  right: -80px;
}
.deco-ring-2 {
  width: 200px;
  height: 200px;
  bottom: -30px;
  right: -30px;
  border-color: rgba(255,255,255,0.04);
}

.deco-dots {
  position: absolute;
  top: 40px;
  right: 40px;
  width: 80px;
  height: 80px;
  background-image: radial-gradient(circle, rgba(255,255,255,0.15) 1.5px, transparent 1.5px);
  background-size: 12px 12px;
  opacity: 0.6;
}

/* ========== 右侧表单区 ========== */
.login-form-area {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 56px;
  background: var(--bg-card);
  position: relative;
}

.form-card {
  width: 100%;
  max-width: 340px;
  animation: slideUp 0.7s ease-out 0.25s both;
}

/* 表单头部 */
.form-header {
  text-align: center;
  margin-bottom: 36px;
}

.form-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: var(--radius-md);
  background: var(--primary-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}
.form-icon svg {
  width: 26px;
  height: 26px;
}

.form-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px;
  letter-spacing: 0.02em;
}
.form-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
  font-weight: 400;
}

/* 输入框标签 */
.input-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

/* 表单样式覆盖 */
.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}
.login-form :deep(.el-form-item__label) {
  display: none;
}
.login-form :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
  border-radius: var(--radius-sm) !important;
  background: var(--bg-input) !important;
  padding: 4px 12px !important;
  transition: all 0.2s ease !important;
}
.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--border-strong) inset !important;
}
.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--primary) inset, 0 0 0 3px var(--primary-glow) !important;
}
.login-form :deep(.el-input__inner) {
  height: 42px;
  font-size: 14px;
}
.login-form :deep(.el-input__icon) {
  color: var(--text-muted);
  font-size: 16px;
}

/* 登录按钮 */
.submit-item {
  margin-top: 8px;
  margin-bottom: 0 !important;
}

.login-btn {
  width: 100%;
  height: 46px;
  border-radius: var(--radius-sm) !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: 0.08em !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  position: relative;
  overflow: hidden;
}
.login-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}
.login-btn:hover::before {
  transform: translateX(100%);
}

.btn-text {
  position: relative;
  z-index: 1;
}
.btn-arrow {
  width: 16px;
  height: 16px;
  position: relative;
  z-index: 1;
  transition: transform 0.25s ease;
}
.login-btn:hover .btn-arrow {
  transform: translateX(3px);
}

/* 表单底部 */
.form-footer {
  margin-top: 32px;
  text-align: center;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.divider-line {
  flex: 1;
  height: 1px;
  background: var(--border-color);
}
.divider-text {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.copyright {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
  letter-spacing: 0.04em;
}

/* ========== 响应式 ========== */
@media (max-width: 860px) {
  .login-wrap {
    grid-template-columns: 1fr;
    max-width: 420px;
    min-height: auto;
  }
  .login-visual {
    display: none;
  }
  .login-form-area {
    padding: 40px 32px;
  }
  .form-card {
    max-width: 100%;
  }
  .bg-blob {
    opacity: 0.2;
  }
}

@media (max-width: 400px) {
  .login-page {
    padding: 16px;
  }
  .login-form-area {
    padding: 32px 24px;
  }
}
</style>
