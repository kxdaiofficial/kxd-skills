#!/usr/bin/env node
// prototype-qa — Lane 1, ตัวเทียบ
//   node compare.mjs dom.json figma.json [--tol 2] [--scale 1] [--json]
//
// จับคู่ 2 ฝั่งด้วย "ข้อความ" เป็น join key แล้วเรียงลำดับด้วย LCS
// (จับคู่ด้วยตำแหน่งไม่ได้ เพราะถ้า layout เพี้ยนตั้งแต่ต้น ทุกอย่างจะเลื่อนตามกันหมด
//  แล้วรายงานจะกลายเป็น "ผิดทุกบรรทัด" ซึ่งไม่บอกอะไรเลย)
//
// exit 1 = เจอ defect

import { readFileSync } from 'node:fs'

const argv = process.argv.slice(2)
const opt = (n, d) => (argv.includes(n) ? argv[argv.indexOf(n) + 1] : d)
const files = argv.filter((a) => !a.startsWith('--') && !/^\d+(\.\d+)?$/.test(a))
if (files.length < 2) {
  console.error('usage: node compare.mjs <dom.json> <figma.json> [--tol 2] [--scale 1] [--json]')
  process.exit(2)
}
const TOL = parseFloat(opt('--tol', '2'))
const SCALE = parseFloat(opt('--scale', '1'))
const dom = JSON.parse(readFileSync(files[0], 'utf8'))
const fig = JSON.parse(readFileSync(files[1], 'utf8'))

const norm = (s) => String(s || '').replace(/\s+/g, ' ').trim()
const key = (s) => norm(s).toLowerCase()
const WEIGHT = { thin: 100, extralight: 200, ultralight: 200, light: 300, regular: 400, normal: 400, book: 400, medium: 500, semibold: 600, demibold: 600, bold: 700, extrabold: 800, black: 900, heavy: 900 }
const weightOf = (v) => {
  if (v === undefined || v === null) return undefined
  const n = parseFloat(v)
  if (!Number.isNaN(n) && String(v).trim() === String(n)) return n
  const s = String(v).toLowerCase().replace(/[^a-z]/g, '')
  return WEIGHT[s] ?? (s.includes('italic') ? WEIGHT[s.replace('italic', '')] : undefined)
}
const colorNorm = (c) => {
  if (!c) return undefined
  const m = String(c).match(/rgba?\(([^)]+)\)/)
  if (!m) return String(c).toLowerCase()
  const p = m[1].split(',').map((x) => parseFloat(x))
  const a = p[3] === undefined ? 1 : Math.round(p[3] * 100) / 100
  return a === 1 ? `rgb(${p[0]},${p[1]},${p[2]})` : `rgba(${p[0]},${p[1]},${p[2]},${a})`
}
const lhPx = (lh, fs) => {
  if (lh === undefined || lh === null || lh === 'normal') return undefined
  if (typeof lh === 'string' && lh.endsWith('%')) return fs ? Math.round(parseFloat(lh) / 100 * fs * 100) / 100 : undefined
  return Math.round(parseFloat(lh) * 100) / 100
}

// ---------- 1. ดึงเฉพาะแถวที่มีข้อความ (join key) ----------
const dText = dom.rows.filter((r) => norm(r.text)).map((r) => ({ ...r, k: key(r.text) }))
const fText = fig.rows.filter((r) => norm(r.text)).map((r) => ({ ...r, k: key(r.text) }))

// ---------- 2. LCS บนลำดับข้อความ — รักษาลำดับการอ่าน จัดการข้อความซ้ำได้ถูก ----------
function lcs(a, b) {
  const n = a.length, m = b.length
  if (!n || !m) return []
  const dp = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1))
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      dp[i][j] = a[i].k === b[j].k ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1])
  const out = []
  let i = 0, j = 0
  while (i < n && j < m) {
    if (a[i].k === b[j].k) { out.push([i, j]); i++; j++ }
    else if (dp[i + 1][j] >= dp[i][j + 1]) i++
    else j++
  }
  return out
}
const pairs = lcs(dText, fText)
const matchedD = new Set(pairs.map((p) => p[0]))
const matchedF = new Set(pairs.map((p) => p[1]))

// ---------- 3. offset กลาง: DOM เป็นพิกัด viewport, Figma เป็นพิกัดของจอ ----------
const med = (a) => (a.length ? a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)] : 0)
const offX = med(pairs.map(([d, f]) => fText[f].x - dText[d].x * SCALE))
const offY = med(pairs.map(([d, f]) => fText[f].y - dText[d].y * SCALE))

// ---------- 4. เทียบ property ----------
const D = []
const add = (sev, kind, where, expected, actual, note) =>
  D.push({ sev, kind, where, expected, actual, note })

for (const [di, fi] of pairs) {
  const d = dText[di], f = fText[fi]
  const at = `"${norm(f.text).slice(0, 40)}" · ${f.name || f.type}`
  const cmp = (kind, exp, act, tol = 0) => {
    if (exp === undefined || act === undefined) return
    if (typeof exp === 'number' && typeof act === 'number') {
      if (Math.abs(exp - act) > tol) add('error', kind, at, exp, act)
    } else if (String(exp) !== String(act)) add('error', kind, at, exp, act)
  }
  cmp('font-size', f.fs, parseFloat(d.fs), 0.5)
  cmp('font-weight', weightOf(f.fw), weightOf(d.fw))
  cmp('line-height', lhPx(f.lh, f.fs), lhPx(d.lh, parseFloat(d.fs)), 0.5)
  cmp('letter-spacing', typeof f.letterSpacing === 'number' ? f.letterSpacing : undefined,
      d.letterSpacing === undefined ? 0 : parseFloat(d.letterSpacing), 0.1)
  cmp('color', colorNorm(f.color), colorNorm(d.color))
  if (f.ff && d.ff && key(f.ff) !== key(d.ff)) add('error', 'font-family', at, f.ff, d.ff)
  // ตำแหน่ง — เทียบกับ offset กลาง ไม่ใช่พิกัดดิบ
  const dx = Math.round((d.x * SCALE + offX) - f.x), dy = Math.round((d.y * SCALE + offY) - f.y)
  if (Math.abs(dx) > TOL || Math.abs(dy) > TOL)
    add('error', 'position', at, `x${f.x} y${f.y}`, `x${Math.round(d.x * SCALE + offX)} y${Math.round(d.y * SCALE + offY)}`, `Δ ${dx > 0 ? '+' : ''}${dx}, ${dy > 0 ? '+' : ''}${dy}`)
  if (f.textStyleId === '' || f.textStyleId === undefined)
    add('info', 'no-text-style', at, 'ผูก text style', 'ไม่ผูก (ค่าพิมพ์มือในบอร์ด)')
}

// ---------- 5. ระยะห่างระหว่างคู่ที่ติดกัน — จับ padding/gap ผิดโดยไม่ต้องจับคู่ container ----------
for (let n = 1; n < pairs.length; n++) {
  const [d0, f0] = pairs[n - 1], [d1, f1] = pairs[n]
  const fGap = Math.round(fText[f1].y - (fText[f0].y + fText[f0].h))
  const dGap = Math.round(dText[d1].y * SCALE - (dText[d0].y * SCALE + dText[d0].h * SCALE))
  if (fGap >= 0 && Math.abs(dGap - fGap) > TOL)
    add('error', 'spacing', `ระหว่าง "${norm(fText[f0].text).slice(0, 22)}" → "${norm(fText[f1].text).slice(0, 22)}"`,
        `${fGap}px`, `${dGap}px`, `Δ ${dGap - fGap > 0 ? '+' : ''}${dGap - fGap}`)
}

// ---------- 6. จับคู่ไม่ได้ = ต้องขึ้นรายงาน ห้ามเงียบ ----------
fText.forEach((f, i) => { if (!matchedF.has(i)) add('error', 'missing-text', `"${norm(f.text).slice(0, 48)}"`, 'มีในบอร์ด', 'ไม่พบใน DOM') })
dText.forEach((d, i) => { if (!matchedD.has(i)) add('warn', 'extra-text', `"${norm(d.text).slice(0, 48)}"`, 'ไม่มีในบอร์ด', 'มีใน DOM') })

// overflow — วัดสองแกนเสมอ
dom.rows.forEach((r) => {
  if (r.overflowX) add('error', 'overflow-x', `${r.tag}.${(r.cls || '').split(' ')[0]}`, 'ไม่ล้น', `ล้น ${r.overflowX}px`)
})

// ---------- 7. รายงาน ----------
const order = { blocker: 0, error: 1, warn: 2, info: 3 }
D.sort((a, b) => order[a.sev] - order[b.sev] || a.kind.localeCompare(b.kind))
const counts = D.reduce((m, x) => ((m[x.sev] = (m[x.sev] || 0) + 1), m), {})

if (argv.includes('--json')) {
  console.log(JSON.stringify({ matched: pairs.length, domText: dText.length, figmaText: fText.length, offX, offY, counts, defects: D }, null, 2))
} else {
  console.log(`\nจับคู่ได้ ${pairs.length} / บอร์ด ${fText.length} ข้อความ / DOM ${dText.length} ข้อความ   (offset x${offX} y${offY}, tol ${TOL}px)`)
  console.log(`ผล: ${Object.entries(counts).map(([k, v]) => `${k} ${v}`).join(' · ') || 'ไม่พบส่วนต่าง'}\n`)
  console.log('| sev | อะไร | ที่ไหน | บอร์ด | ที่ build ได้ | note |')
  console.log('|---|---|---|---|---|---|')
  for (const x of D) console.log(`| ${x.sev} | ${x.kind} | ${x.where} | ${x.expected} | ${x.actual} | ${x.note || ''} |`)
  if (pairs.length < fText.length * 0.6)
    console.log(`\n⚠️ จับคู่ได้ต่ำกว่า 60% — อย่าเชื่อตาราง ให้เช็คว่าเลือกจอ/node ถูกตัวไหม ก่อนรายงานเป็น defect`)
}
process.exit(D.some((x) => x.sev === 'error' || x.sev === 'blocker') ? 1 : 0)
