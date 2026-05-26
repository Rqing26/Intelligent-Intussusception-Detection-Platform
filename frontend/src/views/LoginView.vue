<template>
  <div class="login-page">
    <div class="theme-float-btn" @click="handleToggleTheme" :title="currentTheme === 'modern' ? '切换至中世纪风格' : '切换至现代风格'">
      <span v-if="currentTheme === 'modern'">🏛</span>
      <span v-else>⚡</span>
    </div>
    <div class="login-wrap">
      <div class="login-visual">
        <div class="brand-mark">+</div>
        <h3>肠套叠 AI<br>辅助诊断平台</h3>
        <div class="divider" />
        <p>基于深度学习的超声影像智能分析，为儿科医生提供精准、高效的辅助诊断支持</p>
        <ul class="feature-list">
          <li>智能超声影像分析</li>
          <li>患者全周期管理</li>
          <li>诊断报告一键生成</li>
          <li>检测历史追溯查询</li>
        </ul>
      </div>
      <div class="login-form-area">
        <h4>医生登录</h4>
        <p class="sub">请使用院内账号登录系统</p>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="请输入密码"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
              style="width: 100%"
            >
              登 录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="login-footer">皖南医学院第一附属医院（弋矶山医院）</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
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
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: var(--bg-page);
  position: relative;
}

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
  transition: all 0.2s;
}
.theme-float-btn:hover {
  transform: scale(1.1);
  box-shadow: var(--shadow-md);
}

.login-wrap {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 0;
  width: 100%;
  max-width: 1080px;
  min-height: 640px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-book);
  position: relative;
}

.login-visual {
  background: var(--primary);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  padding: 64px;
  position: relative;
  overflow: hidden;
  color: var(--text-inverse);
}

.login-visual::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.08) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 80%, rgba(184,148,31,0.08) 0%, transparent 50%);
}

.login-visual::after {
  content: '';
  position: absolute;
  top: 40px;
  right: 40px;
  bottom: 40px;
  left: 40px;
  border: 1px solid rgba(212,176,74,0.15);
  pointer-events: none;
}

.login-visual .brand-mark {
  width: 56px;
  height: 56px;
  border: 2px solid var(--gold);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 32px;
  z-index: 1;
  color: var(--gold);
  font-family: var(--font-display);
  position: relative;
}
.login-visual .brand-mark::before {
  content: '';
  position: absolute;
  inset: -8px;
  border: 1px solid rgba(212,176,74,0.2);
}

.login-visual h3 {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 16px;
  z-index: 1;
  line-height: 1.3;
  letter-spacing: 0.04em;
}
.login-visual .divider {
  width: 40px;
  height: 2px;
  background: var(--gold);
  margin: 4px 0 20px;
  z-index: 1;
}
.login-visual p {
  font-size: 15px;
  opacity: 0.8;
  max-width: 320px;
  line-height: 1.8;
  z-index: 1;
}
.login-visual .feature-list {
  margin-top: 32px;
  z-index: 1;
}
.login-visual .feature-list li {
  list-style: none;
  font-size: 13px;
  opacity: 0.7;
  margin-bottom: 10px;
  padding-left: 18px;
  position: relative;
}
.login-visual .feature-list li::before {
  content: '◆';
  position: absolute;
  left: 0;
  color: var(--gold);
  font-size: 7px;
  top: 3px;
}

.login-form-area {
  padding: 64px 52px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 1;
  background: var(--bg-card);
}
.login-form-area h4 {
  font-family: var(--font-display);
  font-size: 26px;
  margin-bottom: 8px;
  color: var(--text-primary);
  font-weight: 700;
}
.login-form-area .sub {
  color: var(--text-muted);
  font-size: 14px;
  margin-bottom: 36px;
  font-style: italic;
}

.login-footer {
  margin-top: 28px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  letter-spacing: 0.04em;
}

@media (max-width: 860px) {
  .login-wrap {
    grid-template-columns: 1fr;
    max-width: 420px;
  }
  .login-visual {
    display: none;
  }
}
</style>
