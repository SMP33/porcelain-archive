import { chromium } from 'playwright'

const SCREEN_DIR = 'C:\\Users\\user\\AppData\\Local\\Temp\\claude\\d--workspace-project-archive\\4230ea63-e0c5-498b-9a71-85b318efc3aa\\scratchpad\\screens'
const BASE = 'http://localhost:5173'

const browser = await chromium.launch({ headless: true, args: ['--no-proxy-server'] })
const page = await browser.newPage()

const errors = []
page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(`[console] ${msg.text()}`)
})
page.on('pageerror', (err) => errors.push(`[pageerror] ${err.message}`))
page.on('response', (res) => {
  if (res.status() >= 400) errors.push(`[http ${res.status()}] ${res.url()}`)
})

async function shot(name) {
  await page.screenshot({ path: `${SCREEN_DIR}\\${name}.png`, fullPage: true })
  console.log(`screenshot: ${name}`)
}

console.log('--- login ---')
await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
await page.waitForSelector('text=Авторизация')
await shot('01-login')

// Поля логина/пароля уже предзаполнены значениями по умолчанию (admin/admin)
await page.click('button[type="submit"]')
await page.waitForURL(`${BASE}/`, { timeout: 5000 }).catch(() => {})
await page.waitForTimeout(500)
await shot('02-after-login')
console.log('url after login:', page.url())

console.log('--- document list ---')
await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
await page.waitForSelector('text=Документы')
await shot('03-document-list')

console.log('--- branch list ---')
await page.goto(`${BASE}/branches`, { waitUntil: 'networkidle' })
await page.waitForSelector('text=Наборы изменений')
await shot('04-branch-list')

console.log('--- task list ---')
await page.goto(`${BASE}/tasks`, { waitUntil: 'networkidle' })
await page.waitForSelector('text=Задачи')
await page.waitForTimeout(1000)
await shot('05-task-list')

console.log('--- user list ---')
await page.goto(`${BASE}/users`, { waitUntil: 'networkidle' })
await page.waitForSelector('text=Пользователи')
await shot('06-user-list')

// Try to find a document/branch to open, via the already-authenticated cookies.
const docsResp = await page.evaluate(async () => {
  const r = await fetch('/api/documents/', { credentials: 'include' })
  return r.json()
})
console.log('documents:', JSON.stringify(docsResp).slice(0, 300))

if (docsResp.items && docsResp.items.length) {
  const docId = docsResp.items[0].id
  console.log('--- document view', docId, '---')
  await page.goto(`${BASE}/document/${docId}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  await shot('07-document-view')
}

const branchesResp = await page.evaluate(async () => {
  const r = await fetch('/api/documents/branches/', { credentials: 'include' })
  return r.json()
})
console.log('branches:', JSON.stringify(branchesResp).slice(0, 300))

if (branchesResp.items && branchesResp.items.length) {
  const branchId = branchesResp.items[0].id
  console.log('--- edit view', branchId, '---')
  await page.goto(`${BASE}/edit/${branchId}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await shot('08-edit-view')

  console.log('--- page gallery dialog ---')
  await page.click('.gallery-thumb >> nth=0')
  await page.waitForTimeout(800)
  await shot('08b-page-gallery-dialog')
  await page.keyboard.press('Escape')
  await page.waitForTimeout(300)

  console.log('--- remove pages panel ---')
  await page.click('text=Удалить страницы')
  await page.waitForTimeout(300)
  await shot('08c-remove-panel')

  console.log('--- set text panel ---')
  await page.click('text=Задать текст')
  await page.waitForTimeout(300)
  await shot('08d-set-text-panel')

  console.log('--- merge dialog ---')
  await page.click('text=Завершить правки')
  await page.waitForTimeout(300)
  await shot('08e-merge-dialog')
  await page.keyboard.press('Escape')
}

console.log('--- not found ---')
await page.goto(`${BASE}/nonexistent-page`, { waitUntil: 'networkidle' })
await shot('09-not-found')

console.log('--- console errors ---')
console.log(errors.length ? errors.join('\n') : 'none')

await browser.close()
