/**
 * 界面截图核查脚本（临时工具，核查完可删）
 * 用机器上已存在的 chromium，逐页截图并收集控制台报错。
 *   node .ui-verify.mjs
 */
import { chromium } from 'playwright'
import fs from 'node:fs'

const EXE = String.raw`C:\Users\卿\AppData\Local\ms-playwright\chromium-1228\chrome-win64\chrome.exe`
const BASE = 'http://[::1]:5173'          // 你本机的 vite 只监听 ::1
const OUT = String.raw`C:\Users\卿\workspace\.ui-shots`
fs.mkdirSync(OUT, { recursive: true })

const problems = []

const browser = await chromium.launch({ executablePath: EXE, headless: true })
const ctx = await browser.newContext({
  viewport: { width: 1600, height: 1000 },
  deviceScaleFactor: 1.5,
})
const page = await ctx.newPage()
page.on('console', (m) => {
  if (m.type() === 'error') problems.push('[console] ' + m.text())
})
page.on('pageerror', (e) => problems.push('[pageerror] ' + e.message))

async function shot(name, selector) {
  try {
    if (selector) await page.locator(selector).first().screenshot({ path: `${OUT}/${name}.png` })
    else await page.screenshot({ path: `${OUT}/${name}.png` })
    console.log('  shot ->', name)
  } catch (e) {
    console.log('  SHOT FAIL', name, e.message.split('\n')[0])
  }
}

async function goHash(hash, wait = 2500) {
  await page.evaluate((h) => { window.location.hash = h }, hash)
  await page.waitForTimeout(wait)
}

async function login(user, pass) {
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1200)
  // 已登录时路由守卫会把 /login 重定向到 /patients，先清 token 才能回到登录页
  await page.evaluate(() => localStorage.clear())
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1800)
  const userInput = page
    .locator('input[placeholder*="用户"], input[placeholder*="账号"], input[placeholder*="工号"]')
    .first()
  const passInput = page.locator('input[placeholder*="密码"]').first()
  await userInput.fill(user)
  await passInput.fill(pass)
  // 登录按钮文案随版本变过：旧版「登录」、新版「进入工作台」
  await page
    .getByRole('button', { name: /进入工作台|登\s*录/ })
    .first()
    .click()
  await page.waitForTimeout(4500)
}

console.log('— 登录页 —')
await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2500)
await shot('01-login')

console.log('— 医生账号登录 —')
await login('doctor', 'doctor123')
console.log('  url =', page.url())

console.log('— 主界面：患者管理 —')
await shot('02-patients-main')
await shot('02b-stats-row', '.stats-row')
await shot('02c-toolbar-table', '.data-card')

// 取一个真实的 result id 用来访问结果页
const resultId = await page.evaluate(async () => {
  const t = localStorage.getItem('access_token')
  const r = await fetch('/api/results?page=1&size=1', {
    headers: { Authorization: 'Bearer ' + t },
  })
  const j = await r.json()
  const items = j.items || j.data || j
  return Array.isArray(items) && items.length ? items[0].id : null
})
console.log('  resultId =', resultId)

const patientId = await page.evaluate(async () => {
  const t = localStorage.getItem('access_token')
  const r = await fetch('/api/patients?page=1&size=1', {
    headers: { Authorization: 'Bearer ' + t },
  })
  const j = await r.json()
  const items = j.items || j.data || j
  return Array.isArray(items) && items.length ? items[0].id : null
})
console.log('  patientId =', patientId)

if (patientId) {
  console.log('— 患者详情 —')
  await goHash(`#/patients/${patientId}`, 3500)
  await shot('03-patient-detail')
  await shot('03b-mini-stats', '.stats-grid')

  console.log('— 上传影像 —')
  await goHash(`#/patients/${patientId}/upload`, 3000)
  await shot('04-upload')
}

console.log('— 检测记录 —')
await goHash('#/history', 3500)
await shot('05-history')
await shot('05b-history-stats', '.stats-row')

if (resultId) {
  console.log('— 检测结果 —')
  await goHash(`#/results/${resultId}`, 4500)
  await shot('06-result')
}

console.log('— 管理员：审计日志 —')
await login('admin', 'admin123')
await goHash('#/audit', 3500)
await shot('07-audit')

console.log('\n=== 控制台问题 ===')
if (!problems.length) console.log('（无）')
else [...new Set(problems)].slice(0, 25).forEach((p) => console.log(p))

await browser.close()
console.log('\n输出目录:', OUT)
