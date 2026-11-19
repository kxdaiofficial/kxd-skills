// prototype-qa — Lane 1, ฝั่ง DOM
// paste ทั้งไฟล์นี้เข้า javascript_tool ครั้งเดียว แล้วเรียก:  __qaMeasure('#root')
// คืน { url, viewport, n, rows: [...] }  — rows แต่ละแถวคือ element ที่ "มองเห็นจริง"
//
// ทุกค่ามาจาก getComputedStyle + getBoundingClientRect เท่านั้น ไม่มีค่าไหนเดา
// ค่าที่เท่ากับ default ของเบราว์เซอร์จะถูกตัดออกเพื่อให้ payload เล็ก
// (ค่าที่ "ไม่มีในแถว" = ค่า default ไม่ใช่ "วัดไม่ได้")

window.__qaMeasure = function (rootSel, opts) {
  opts = opts || {}
  const LIMIT = opts.limit || 1200
  const root = document.querySelector(rootSel || '#root') || document.body
  const DEFAULTS = {
    letterSpacing: 'normal', opacity: '1', borderRadius: '0px',
    borderTopWidth: '0px', backgroundColor: 'rgba(0, 0, 0, 0)',
    paddingTop: '0px', paddingRight: '0px', paddingBottom: '0px', paddingLeft: '0px',
    rowGap: 'normal', columnGap: 'normal',
  }
  const px = (v) => (typeof v === 'string' && v.endsWith('px') ? Math.round(parseFloat(v) * 100) / 100 : v)
  const rows = []
  let seq = 0

  // ข้อความตรง ๆ ของ element (ไม่รวมของลูก) — ใช้เป็น join key กับฝั่ง Figma
  const ownText = (el) => {
    let t = ''
    for (const n of el.childNodes) if (n.nodeType === 3) t += n.nodeValue
    return t.replace(/\s+/g, ' ').trim()
  }
  const pathOf = (el) => {
    const p = []
    for (let n = el; n && n !== root && p.length < 8; n = n.parentElement) {
      const i = n.parentElement ? [...n.parentElement.children].indexOf(n) : 0
      p.unshift(n.tagName.toLowerCase() + '[' + i + ']')
    }
    return p.join('>')
  }

  const walk = (el) => {
    if (rows.length >= LIMIT) return
    const cs = getComputedStyle(el)
    if (cs.display === 'none' || cs.visibility === 'hidden') return   // ลูกก็ไม่ต้องเดิน
    const r = el.getBoundingClientRect()
    const text = ownText(el)
    const paints = cs.backgroundColor !== DEFAULTS.backgroundColor || parseFloat(cs.borderTopWidth) > 0
    if (r.width > 0 && r.height > 0 && (text || paints || el.tagName === 'IMG' || el.tagName === 'SVG')) {
      const row = {
        i: seq++,
        tag: el.tagName.toLowerCase(),
        path: pathOf(el),
        cls: (el.getAttribute('class') || '').slice(0, 120) || undefined,
        text: text || undefined,
        x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100,
        ff: cs.fontFamily.split(',')[0].replace(/["']/g, ''),
        fs: px(cs.fontSize), fw: cs.fontWeight, lh: px(cs.lineHeight),
        color: cs.color,
      }
      for (const [k, d] of Object.entries(DEFAULTS)) {
        const v = cs[k]
        if (v !== d) row[k] = px(v)
      }
      // สองแกน: กว้างล้นเงียบ ๆ เป็น defect ที่ height check จับไม่ได้
      if (el.scrollWidth - el.clientWidth > 1) row.overflowX = el.scrollWidth - el.clientWidth
      if (el.scrollHeight - el.clientHeight > 1) row.overflowY = el.scrollHeight - el.clientHeight
      rows.push(row)
    }
    for (const c of el.children) walk(c)
  }
  walk(root)

  return {
    url: location.href,
    viewport: [innerWidth, innerHeight],
    theme: document.documentElement.dataset || {},
    n: rows.length,
    truncated: rows.length >= LIMIT,
    rows,
  }
}

// สลับ mode axis แล้ววัดซ้ำ — ค่าไหนไม่ขยับ = ไม่ได้มาจาก token จริง (Lane 3)
window.__qaModeFlip = function (attr, a, b, sel) {
  const el = document.documentElement
  const before = el.getAttribute(attr)
  const pick = (v) => {
    el.setAttribute(attr, v)
    const nodes = [...document.querySelectorAll(sel || '#root *')].slice(0, 400)
    return nodes.map((n) => {
      const c = getComputedStyle(n)
      return [c.borderRadius, c.paddingLeft, c.color, c.backgroundColor, c.fontSize].join('|')
    })
  }
  const A = pick(a), B = pick(b)
  if (before === null) el.removeAttribute(attr); else el.setAttribute(attr, before)
  const frozen = A.map((v, i) => (v === B[i] ? i : -1)).filter((i) => i >= 0)
  return { attr, a, b, checked: A.length, frozen: frozen.length, frozenIdx: frozen.slice(0, 40) }
}
'ready: __qaMeasure(sel) / __qaModeFlip(attr,a,b,sel)'
