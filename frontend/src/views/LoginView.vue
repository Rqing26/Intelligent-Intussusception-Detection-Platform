<template>
  <main class="login-page" :class="{ 'is-warm': currentTheme === 'medieval' }">
    <div class="login-shell">
      <section class="brand-panel" aria-labelledby="platform-title">
        <router-link class="hospital-brand" to="/login" aria-label="肠套叠 AI 辅助诊断平台登录页">
          <span class="hospital-mark">
            <img src="/newlogo.png" alt="弋矶山医院院徽" />
          </span>
          <span class="hospital-wordmark">
            <strong>皖南医学院第一附属医院</strong>
            <span>弋矶山医院 · Yijishan Hospital</span>
          </span>
        </router-link>

        <div class="brand-introduction">
          <div class="section-kicker"><span /> CLINICAL INTELLIGENCE</div>
          <h1 id="platform-title">让每一次判断，<br /><span>更有依据。</span></h1>
          <p>肠套叠 AI 辅助诊断平台</p>
          <div class="introduction-detail">连接超声影像与智能分析，<br />为临床诊疗提供清晰、有序的工作空间。</div>
        </div>

        <div class="scan-art" aria-hidden="true">
          <div class="scan-topline"><span>ULTRASOUND INTELLIGENCE</span><span>01 / 03</span></div>
          <svg viewBox="0 0 500 280" fill="none" class="scan-visual">
            <defs>
              <linearGradient id="login-contour" x1="108" y1="20" x2="377" y2="266" gradientUnits="userSpaceOnUse">
                <stop stop-color="#b6ddd0" stop-opacity="0.85" />
                <stop offset="0.5" stop-color="#72b8aa" stop-opacity="0.22" />
                <stop offset="1" stop-color="#d6e8a6" stop-opacity="0.75" />
              </linearGradient>
              <radialGradient id="login-scan-glow">
                <stop stop-color="#65bbaa" stop-opacity="0.11" />
                <stop offset="1" stop-color="#65bbaa" stop-opacity="0" />
              </radialGradient>
            </defs>
            <ellipse cx="250" cy="141" rx="199" ry="138" fill="url(#login-scan-glow)" />
            <g stroke="#b4d4ca" opacity="0.13" stroke-width="0.6">
              <path d="M28 70H472M28 140H472M28 210H472M110 24V256M250 24V256M390 24V256" />
              <path d="M56 34V246M444 34V246" stroke-dasharray="2 7" />
            </g>
            <g stroke="url(#login-contour)" stroke-width="1.1">
              <path d="M239 22C298 13 365 49 385 102C410 163 361 232 292 253C221 277 145 241 121 182C96 123 127 55 180 31C196 24 219 25 239 22Z" />
              <path d="M240 39C294 31 350 58 368 106C390 161 348 218 287 238C225 259 159 227 138 177C116 126 142 68 188 47C202 40 221 42 240 39Z" />
              <path d="M239 57C286 48 335 69 351 112C371 160 335 205 282 221C229 239 172 215 155 171C138 128 159 82 199 65C211 60 223 60 239 57Z" />
              <path d="M241 74C281 66 321 84 334 118C350 158 321 193 278 207C233 221 187 203 172 166C158 130 176 97 209 82C219 78 228 77 241 74Z" />
              <path d="M242 91C275 84 306 97 317 124C329 154 309 181 273 193C239 204 201 190 190 162C178 134 192 110 219 99C226 95 231 94 242 91Z" />
              <path d="M244 107C269 101 292 110 300 130C310 151 295 169 268 179C243 188 217 179 207 158C199 138 208 121 229 114C235 111 238 109 244 107Z" />
              <path d="M247 123C263 119 278 123 284 136C290 149 280 159 265 164C250 170 232 167 226 155C220 143 230 133 240 129C242 128 245 124 247 123Z" />
            </g>
            <g stroke="#d6e8a6" stroke-width="1.4">
              <path d="M173 70H155V88M333 70H351V88M155 197V215H173M351 197V215H333" />
            </g>
            <g stroke="#b9d5cb" opacity="0.55" stroke-width="0.8">
              <path d="M241 141H259M250 132V150M63 38H72M63 59H68M63 80H72M63 101H68M63 122H72M63 143H68M63 164H72M63 185H68M63 206H72M63 227H68M63 248H72" />
              <path d="M358 181H410L428 198M104 88H122" />
            </g>
            <circle cx="358" cy="181" r="2.5" fill="#c4dfb0" />
            <text x="402" y="215" fill="#91b5aa" font-size="8" letter-spacing="1.4">AI ASSIST</text>
          </svg>
          <div class="scan-bottomline"><span>影像分析工作流示意</span><span>以影像为依据，以临床为核心</span></div>
        </div>

        <div class="workflow-strip" aria-label="平台工作流程">
          <span><i>01</i> 影像上传</span>
          <span class="workflow-divider" />
          <span><i>02</i> 智能分析</span>
          <span class="workflow-divider" />
          <span><i>03</i> 病例管理</span>
        </div>
      </section>

      <section class="login-panel" aria-labelledby="login-title">
        <div class="panel-topbar">
          <span class="workspace-label">临床工作空间</span>
          <button
            type="button"
            class="theme-button"
            @click="handleToggleTheme"
            :title="currentTheme === 'modern' ? '切换至暖色主题' : '切换至标准主题'"
            :aria-label="currentTheme === 'modern' ? '切换至暖色主题' : '切换至标准主题'"
          >
            <el-icon :size="15"><Sunny v-if="currentTheme === 'modern'" /><Monitor v-else /></el-icon>
            <span>{{ currentTheme === 'modern' ? '标准主题' : '暖色主题' }}</span>
          </button>
        </div>

        <div class="form-card">
          <div class="form-heading">
            <span class="form-eyebrow">WELCOME BACK</span>
            <h2 id="login-title">欢迎回来</h2>
            <p>登录您的账号，开始今天的诊疗工作。</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="login-form"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <label class="input-label" for="login-username">用户名 <span>USERNAME</span></label>
              <el-input
                id="login-username"
                v-model="form.username"
                name="username"
                autocomplete="username"
                placeholder="请输入院内账号"
                size="large"
                :prefix-icon="User"
                class="login-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <label class="input-label" for="login-password">密码 <span>PASSWORD</span></label>
              <el-input
                id="login-password"
                v-model="form.password"
                name="password"
                type="password"
                autocomplete="current-password"
                show-password
                placeholder="请输入登录密码"
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
                :disabled="loading"
                size="large"
                class="login-button"
              >
                <span>{{ loading ? '正在登录' : '进入工作台' }}</span>
                <el-icon v-if="!loading" :size="18"><ArrowRight /></el-icon>
              </el-button>
            </el-form-item>
          </el-form>

          <div class="account-notice">
            <el-icon :size="16"><Lock /></el-icon>
            <p>仅限授权医务人员使用<br /><span>如需开通账号或重置密码，请联系系统管理员。</span></p>
          </div>
        </div>

        <footer class="login-footer">
          <div class="footer-rule" />
          <span>肠套叠 AI 辅助诊断平台</span>
          <span class="footer-english">Designed for better clinical care.</span>
        </footer>
      </section>
    </div>
  </main>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Sunny, Monitor, ArrowRight } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { toggleTheme, getCurrentTheme } from '../utils/theme'

const router = useRouter()
const authStore = useAuthStore()
const currentTheme = ref(getCurrentTheme())
const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function handleToggleTheme() {
  currentTheme.value = toggleTheme()
}

async function handleLogin() {
  if (loading.value) return
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
  --login-ink: #102e35;
  --login-teal: #15746f;
  --login-paper: #fbfcf9;
  --login-muted: #748783;
  --login-line: #dde6e0;
  --login-accent: #d6e8a6;
  min-height: 100vh;
  min-height: 100svh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #edf1ec;
  color: var(--login-ink);
}

.login-page.is-warm {
  --login-ink: #303b31;
  --login-teal: #626f4d;
  --login-paper: #fcfaf4;
  --login-muted: #848677;
  --login-line: #e4e3d5;
  --login-accent: #e7d5a8;
  background: #eeece3;
}

.login-shell {
  width: 100%;
  max-width: 1440px;
  min-height: min(824px, calc(100svh - 48px));
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid rgba(16, 46, 53, 0.05);
  border-radius: 24px;
  overflow: hidden;
  background: var(--login-paper);
  box-shadow: 0 20px 70px -40px rgba(21, 54, 49, 0.24);
}

.brand-panel {
  display: flex;
  flex-direction: column;
  padding: 44px 50px 32px;
  color: #f5f8ef;
  background: var(--login-ink);
  position: relative;
  isolation: isolate;
  overflow: hidden;
}

.brand-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(145deg, transparent 35%, rgba(75, 125, 98, 0.15));
}

.hospital-brand {
  display: flex;
  align-items: center;
  gap: 13px;
  color: inherit;
  text-decoration: none;
  align-self: flex-start;
}

.hospital-mark {
  width: 49px;
  height: 49px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 50%;
  background: #fff;
  padding: 3px;
}

.hospital-mark img { display: block; width: 100%; height: 100%; object-fit: contain; }
.hospital-wordmark { display: grid; gap: 6px; }
.hospital-wordmark strong { font-size: 14px; letter-spacing: 1px; font-weight: 600; }
.hospital-wordmark > span { font-size: 10px; color: #a9c3bd; letter-spacing: 0.6px; }
.brand-introduction { padding-top: 65px; }
.section-kicker { display: flex; align-items: center; gap: 9px; font-size: 9px; letter-spacing: 2.5px; color: #b4ccc0; }
.section-kicker > span { width: 5px; height: 5px; border-radius: 50%; background: var(--login-accent); }
.brand-introduction h1 { margin: 24px 0 22px; font-size: clamp(36px, 3.2vw, 49px); line-height: 1.5; letter-spacing: 1px; font-weight: 550; }
.brand-introduction h1 > span { color: var(--login-accent); }
.brand-introduction > p { margin: 0 0 12px; font-size: 15px; font-weight: 500; letter-spacing: 1.2px; }
.introduction-detail { color: #a8c0ba; font-size: 12px; line-height: 1.95; letter-spacing: 0.2px; }

.scan-art { margin-top: 32px; flex: 1; display: flex; flex-direction: column; justify-content: center; }
.scan-topline, .scan-bottomline { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: #88a79e; font-size: 8px; letter-spacing: 1.3px; }
.scan-topline { padding-top: 16px; border-top: 1px solid rgba(187, 216, 202, 0.12); }
.scan-visual { width: 100%; max-height: 257px; display: block; margin: 0 auto; }
.scan-bottomline { margin-top: -3px; font-size: 9px; letter-spacing: 0.6px; }
.workflow-strip { display: flex; align-items: center; gap: 16px; margin-top: 28px; padding-top: 23px; border-top: 1px solid rgba(187, 216, 202, 0.16); }
.workflow-strip > span:not(.workflow-divider) { display: flex; align-items: center; gap: 7px; white-space: nowrap; font-size: 11px; color: #ccdbd1; letter-spacing: 0.3px; }
.workflow-strip i { font-size: 9px; font-style: normal; color: #88a69a; }
.workflow-divider { flex: 1; height: 1px; background: rgba(187, 216, 202, 0.2); }

.login-panel { display: flex; flex-direction: column; padding: 37px 52px 31px; min-width: 0; }
.panel-topbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.workspace-label { font-size: 11px; color: var(--login-muted); letter-spacing: 1.3px; }
.theme-button { display: flex; align-items: center; gap: 7px; padding: 8px 10px; border: 1px solid var(--login-line); border-radius: 7px; background: transparent; font: inherit; font-size: 11px; color: var(--login-muted); cursor: pointer; transition: background 160ms, color 160ms; }
.theme-button:hover { color: var(--login-ink); background: rgba(21, 116, 111, 0.045); }
.theme-button:focus-visible, .hospital-brand:focus-visible { outline: 2px solid var(--login-teal); outline-offset: 5px; }
.form-card { width: 100%; max-width: 367px; margin: auto; padding: 68px 0 65px; }
.form-eyebrow { font-size: 10px; color: var(--login-teal); letter-spacing: 2.2px; font-weight: 600; }
.form-heading h2 { margin: 15px 0 12px; font-size: 35px; font-weight: 600; letter-spacing: 1px; line-height: 1.4; color: var(--login-ink); }
.form-heading p { margin: 0; font-size: 12px; color: var(--login-muted); line-height: 1.8; }
.login-form { margin-top: 38px; }
.login-form :deep(.el-form-item) { margin-bottom: 27px; }
.login-form :deep(.el-form-item__content) { display: flex; flex-direction: column; align-items: stretch; line-height: normal; }
.input-label { display: flex; align-items: center; justify-content: space-between; margin-bottom: 11px; color: var(--login-ink); font-size: 12px; font-weight: 550; }
.input-label span { font-size: 8px; color: #91a19b; letter-spacing: 1.2px; font-weight: 400; }
.login-input :deep(.el-input__wrapper) { min-height: 51px; padding: 1px 16px; border-radius: 8px; background: rgba(255, 255, 255, 0.65); box-shadow: 0 0 0 1px var(--login-line) inset; transition: box-shadow 160ms, background 160ms; }
.login-input :deep(.el-input__wrapper:hover) { box-shadow: 0 0 0 1px #a9bdb5 inset; }
.login-input :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px var(--login-teal) inset, 0 0 0 3px rgba(21, 116, 111, 0.07); background: #fff; }
.login-input :deep(.el-input__inner) { height: 49px; color: var(--login-ink); font-size: 12px; }
.login-input :deep(.el-input__inner::placeholder) { color: #9aa9a2; }
.login-input :deep(.el-input__prefix) { color: #8a9f94; margin-right: 4px; font-size: 16px; }
.login-form :deep(.el-form-item__error) { padding-top: 5px; font-size: 11px; }
.login-form :deep(.submit-item) { margin-top: 34px; margin-bottom: 0; }
.login-button { width: 100%; height: 52px; border: 1px solid var(--login-teal); border-radius: 8px; background: var(--login-teal); box-shadow: 0 5px 12px -7px rgba(12, 86, 76, 0.4); color: #fff; font-size: 13px; font-weight: 550; letter-spacing: 1px; transition: transform 160ms, box-shadow 160ms, filter 160ms; }
.login-button:hover { background: var(--login-teal); border-color: var(--login-teal); filter: brightness(1.08); transform: translateY(-1px); box-shadow: 0 7px 17px -7px rgba(12, 86, 76, 0.3); }
.login-button:focus-visible { outline: 2px solid var(--login-teal); outline-offset: 4px; }
.login-button.is-disabled { background: var(--login-teal); border-color: var(--login-teal); opacity: 0.75; }
.login-button :deep(> span) { width: 100%; display: flex; align-items: center; justify-content: center; gap: 18px; }
.login-button .el-icon { flex-shrink: 0; }
.account-notice { display: flex; align-items: flex-start; gap: 10px; padding-top: 25px; color: var(--login-muted); }
.account-notice > .el-icon { margin-top: 3px; color: #8a9f94; flex-shrink: 0; }
.account-notice p { margin: 0; font-size: 10px; line-height: 1.9; }
.account-notice p > span { color: #94a099; }
.login-footer { display: grid; gap: 8px; color: var(--login-muted); font-size: 10px; letter-spacing: 0.3px; }
.footer-rule { width: 28px; height: 2px; background: #cbd7cb; margin-bottom: 7px; }
.footer-english { color: #9ba79e; font-size: 9px; letter-spacing: 0.5px; }

@media (min-width: 1550px) {
  .login-page { padding: 42px; }
  .login-shell { min-height: 824px; }
  .brand-panel { padding: 48px 60px 36px; }
  .login-panel { padding: 42px 64px 35px; }
}

@media (max-width: 1100px) {
  .login-page { padding: 16px; }
  .login-shell { min-height: calc(100svh - 32px); }
  .brand-panel { padding: 33px 30px 27px; }
  .login-panel { padding: 31px 34px 27px; }
  .hospital-wordmark strong { font-size: 12px; letter-spacing: 0.3px; }
  .hospital-wordmark > span { font-size: 9px; letter-spacing: 0; }
  .hospital-mark { width: 43px; height: 43px; }
  .brand-introduction { padding-top: 59px; }
  .brand-introduction h1 { font-size: 36px; }
  .workflow-strip { gap: 10px; }
  .workflow-strip > span:not(.workflow-divider) { font-size: 10px; gap: 4px; }
}

@media (max-width: 800px) {
  .login-page { padding: 16px; }
  .login-shell { grid-template-columns: 1fr; max-width: 560px; border-radius: 18px; }
  .brand-panel { padding: 26px 32px 28px; }
  .brand-introduction { padding-top: 29px; }
  .brand-introduction h1 { font-size: 31px; line-height: 1.45; margin: 14px 0 14px; }
  .brand-introduction h1 br { display: none; }
  .brand-introduction > p { font-size: 13px; margin-bottom: 0; }
  .section-kicker { font-size: 8px; letter-spacing: 2px; }
  .introduction-detail, .scan-art, .workflow-strip { display: none; }
  .login-panel { padding: 24px 32px 27px; }
  .form-card { max-width: none; padding: 37px 0 40px; }
  .form-heading h2 { font-size: 29px; margin-top: 10px; }
  .login-form { margin-top: 28px; }
  .login-footer { display: flex; align-items: center; flex-wrap: wrap; gap: 7px 14px; font-size: 9px; }
  .footer-rule { display: none; }
  .footer-english { font-size: 8px; }
}

@media (max-width: 420px) {
  .login-page { padding: 0; align-items: start; }
  .login-shell { border: 0; border-radius: 0; min-height: 100svh; }
  .brand-panel { padding: 23px 25px 25px; }
  .brand-introduction h1 { font-size: 27px; }
  .login-panel { padding: 20px 25px 24px; }
  .form-card { padding-top: 34px; }
}

@media (prefers-reduced-motion: reduce) {
  .theme-button, .login-button, .login-input :deep(.el-input__wrapper) { transition: none; }
}
</style>
