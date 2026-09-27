/**
 * 界面截图 / 冒烟核查工具
 * ============================================================
 * 逐页打开平台，截图并收集浏览器控制台报错，用于：
 *   1) 改完界面后自查（有没有报错、有没有跑版）
 *   2) 重新生成 docs/screenshots/ 里的文档配图
 *
 * 依赖（**故意不写进 package.json**，避免每个队友 npm install 都被拖一个浏览器）：
 *   npm i -D playwright
 *   npx playwright install chromium
 *
 * 用法（在 frontend/ 目录下）：
 *   node scripts/ui-screenshots.mjs                          # 核查用 png 组，输出到 ./.ui-shots
 *   node scripts/ui-screenshots.mjs --doc --out ../docs/screenshots   # 生成文档配图（jpg）
 *
 * 可选参数：
 *   --base <url>       前端地址，默认 http://localhost:5173
 *   --out  <dir>       输出目录，默认 ./.ui-shots
 *   --chromium <path>  指定浏览器可执行文件；不传则用 playwright 自带的 chromium
 *                      （也可用环境变量 PW_CHROMIUM 指定，适合机器上已有 chromium 的情况）
 *   --user / --pass    医生账号，默认 doctor / doctor123
 *   --admin-user / --admin-pass  管理员账号，默认 admin / admin123
 * ============================================================
 */
import fs from 'node:fs'
import path from 'node:path'

// ---------- 参数 ----------
const argv = process.argv.slice(2)
const arg = (name, fallback) => {
  const i = argv.indexOf(`--${name}`)
  return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : fallback
}
const flag = (name) => argv.includes(`--${name}`)

const BASE = (arg('base', 'http://localhost:5173')).replace(/\/$/, '')
const OUT = path.resolve(arg('out', './.ui-shots'))
const DOC = flag('doc') // 文档配图模式：写 jpg、用 docs 里的固定文件名
const USER = arg('user', 'doctor')
const PASS = arg('pass', 'doctor123')
const ADMIN_USER = arg('admin-user', 'admin')
const ADMIN_PASS = arg('admin-pass', 'admin123')
const CHROMIUM = arg('chromium', process.env.PW_CHROMIUM || '')

fs.mkdirSync(OUT, { recursive: true })

// ---------- 依赖与浏览器 ----------
let chromium
try {
  ;({ chromium } = await import('playwright'))
} catch {
  console.error(
    '\n[缺少依赖] 本脚本需要 playwright：\n' +
      '  npm i -D playwright\n' +
      '  npx playwright install chromium\n',
  )
  process.exit(1)
}

let browser
try {
  browser = await chromium.launch(
    CHROMIUM ? { executablePath: CHROMIUM, headless: true } : { headless: true },
  )
} catch (e) {
  console.error(
    `\n[无法启动浏览器] ${e.message.split('\n')[0]}\n` +
      '按下面任一种方式解决：\n' +
      '  1) npx playwright install chromium\n' +
      '  2) 指定已有浏览器：node scripts/ui-screenshots.mjs --chromium "C:\\path\\to\\chrome.exe"\n' +
      '     或设置环境变量 PW_CHROMIUM\n',
  )
  process.exit(1)
}

const ctx = await browser.newContext({
  viewport: { width: 1600, height: 1000 },
  deviceScaleFactor: 1.5,
})
const page = await ctx.newPage()

const problems = []
page.on('console', (m) => {
  if (m.type() === 'error') problems.push('[console] ' + m.text())
})
page.on('pageerror', (e) => problems.push('[pageerror] ' + e.message))

// ---------- 小工具 ----------
/** DOC 模式写 ${name}.jpg（文档配图），否则写 ${name}.png */
async function shot(name, selector) {
  const target = path.join(OUT, DOC ? `${name}.jpg` : `${name}.png`)
  const options = DOC ? { path: target, type: 'jpeg', quality: 90 } : { path: target }
  try {
    if (selector) await page.locator(selector).first().screenshot(options)
    else await page.screenshot(options)
    console.log('  shot ->', path.relative(process.cwd(), target))
  } catch (e) {
    console.log('  SHOT FAIL', name, e.message.split('\n')[0])
  }
}

async function goHash(hash, wait = 2500) {
  await page.evaluate((h) => {
    window.location.hash = h
  }, hash)
  await page.waitForTimeout(wait)
}

async function login(user, pass) {
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1200)
  // 已登录时路由守卫会把 /login 重定向回工作台，先清 token 才能回到登录页
  await page.evaluate(() => localStorage.clear())
  await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1800)
  await page
    .locator('input[placeholder*="用户"], input[placeholder*="账号"], input[placeholder*="工号"]')
    .first()
    .fill(user)
  await page.locator('input[placeholder*="密码"]').first().fill(pass)
  // 登录按钮文案随版本变过：旧版「登录」、新版「进入工作台」
  await page
    .getByRole('button', { name: /进入工作台|登\s*录/ })
    .first()
    .click()
  await page.waitForTimeout(4500)
}

/** 用当前登录态的 token 调接口，返回数组（兼容分页/裸数组两种返回） */
async function apiList(page, url) {
  return page.evaluate(async (u) => {
    const t = localStorage.getItem('access_token')
    const r = await fetch(u, { headers: { Authorization: 'Bearer ' + t } })
    const j = await r.json()
    const items = j.items || j.data || j
    return Array.isArray(items) ? items.map((x) => ({ id: x.id, name: x.name })) : []
  }, url)
}

// ---------- 开始 ----------
console.log(`目标: ${BASE}\n输出: ${OUT}${DOC ? '（文档配图 jpg）' : ''}\n`)

console.log('— 登录页 —')
await page.goto(`${BASE}/#/login`, { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2500)
await shot('login')

console.log('— 医生登录 —')
await login(USER, PASS)
console.log('  url =', page.url())

console.log('— 主界面：患者管理 —')
await shot('patient-list')
if (!DOC) {
  await shot('02b-stats-row', '.stats-row')
  await shot('02c-toolbar-table', '.data-card')
}

const patients = await apiList(page, '/api/patients?page=1&size=50')
const patientId = patients.length ? patients[0].id : null
const results = await apiList(page, '/api/results?page=1&size=1')
const resultId = results.length ? results[0].id : null
console.log(`  患者数: ${patients.length}，首个患者 id=${patientId}，首个结果 id=${resultId}`)

if (patientId) {
  console.log('— 患者详情（含检测历史时间线）—')
  await goHash(`#/patients/${patientId}`, 3500)
  await shot('history-timeline')
  if (!DOC) await shot('03b-mini-stats', '.stats-grid')

  console.log('— 上传影像 —')
  await goHash(`#/patients/${patientId}/upload`, 3000)
  await shot('upload')
}

console.log('— 检测记录 —')
await goHash('#/history', 3500)
if (!DOC) await shot('05-history')
if (!DOC) await shot('05b-history-stats', '.stats-row')

if (resultId) {
  console.log('— 检测结果 —')
  await goHash(`#/results/${resultId}`, 4500)
  await shot('result')

  console.log('— 打印报告（弹窗）—')
  await page
    .getByRole('button', { name: /打印报告/ })
    .first()
    .click()
    .catch(() => {})
  await page.waitForTimeout(3500)
  await shot('report')
  await page.keyboard.press('Escape')
  await page.waitForTimeout(800)
}

// ── 同患者影像翻页：真点一次「下一张」，再试键盘 → ──
console.log('— 翻页功能核查 —')
let target = null
for (const p of patients) {
  const list = await apiList(page, `/api/results?patient_id=${p.id}&page=1&size=100`)
  if (list.length >= 3) {
    target = { pid: p.id, name: p.name, ids: list.map((r) => r.id).sort((a, b) => a - b) }
    break
  }
}
if (!target) {
  console.log('  跳过：没有找到影像数 >= 3 的患者')
} else {
  console.log(`  目标患者: ${target.name} (id=${target.pid})，结果 id: ${target.ids.join(', ')}`)
  await goHash(`#/results/${target.ids[0]}`, 3500)
  const readCount = async () =>
    (await page
      .locator('.shot-pager-count')
      .first()
      .innerText()
      .catch(() => '(无翻页控件)'))
      .replace(/\s+/g, ' ')
      .trim()
  console.log('  首个结果计数:', await readCount())
  if (!DOC) await shot('08-pager-first')

  const before = page.url()
  const prevDisabled = await page
    .getByRole('button', { name: '上一张' })
    .first()
    .isDisabled()
    .catch(() => 'n/a')
  await page.getByRole('button', { name: '下一张' }).first().click()
  await page.waitForTimeout(3200)
  const afterClick = page.url()
  console.log(`  第一张时「上一张」是否禁用: ${prevDisabled}（应为 true）`)
  console.log(`  点「下一张」: ${before.split('#')[1]} → ${afterClick.split('#')[1]}`)
  console.log(`  计数变为: ${await readCount()}`)
  if (!DOC) await shot('08b-pager-next')

  await page.keyboard.press('ArrowRight')
  await page.waitForTimeout(3200)
  console.log(`  键盘 → 之后: ${page.url().split('#')[1]}`)
  console.log(
    `  判定: ${afterClick !== before && page.url() !== afterClick ? 'PASS 按钮与键盘均生效' : 'FAIL 请检查'}`,
  )
}

console.log('— 管理员：审计日志 —')
await login(ADMIN_USER, ADMIN_PASS)
await goHash('#/audit', 3500)
await shot('audit')

console.log('\n=== 控制台报错 ===')
if (!problems.length) console.log('（无）')
else [...new Set(problems)].slice(0, 25).forEach((p) => console.log(p))

await browser.close()
console.log(`\n完成，输出目录: ${OUT}`)
