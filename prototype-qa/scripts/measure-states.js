// prototype-qa — Lane 1 ส่วน interaction state
// paste เข้า javascript_tool แล้วเรียก:  __qaStates()
//
// วิธีคิด: อย่าไล่ hover ทีละตัว 157 ครั้ง — ให้ถอด selector ที่มี :hover / :focus /
// :active ออกจาก stylesheet แล้วถาม element ว่า `matches(base)` ไหม
// ได้คำตอบครบทุก control ในการยิงครั้งเดียว แล้วค่อย hover จริงเฉพาะตัวที่จะยืนยัน
//
// ⚠️ ต้อง recurse เข้า nested rules — Tailwind v4 ซ้อน rule เป็นชั้น
//    อ่านชั้นบนอย่างเดียวได้ hover = 0 ทั้งที่มี 12 (พลาดมาแล้ว 2026-08-28)
// ⚠️ ห้ามจับเวลา animation ด้วย setTimeout — Browser pane ยุบ timer เป็นถัง ~1s
//    ให้อ่านค่า transition-duration / animation-* เป็นค่า CSS แทน

window.__qaStates = function (rootSel, opts) {
  opts = opts || {}
  // เกณฑ์พื้นที่กด: เดสก์ท็อปใช้ WCAG 2.2 SC 2.5.8 (24) · มือถือใช้ 2.5.5 Enhanced (44)
  // ⚠️ ใช้ 44 กับ console 1920 แล้วได้ "defect" 103 ตัวที่ไม่ใช่ defect (วัดจริง 2026-08-28)
  const MIN_TARGET = opts.minTarget || (innerWidth >= 768 ? 24 : 44)
  const root = document.querySelector(rootSel || '#root') || document.body

  // ---------- 1. เก็บ selector ของทุก state จาก stylesheet (recurse) ----------
  const buckets = { hover: [], focus: [], active: [], disabled: [], reducedMotion: 0 }
  let rulesRead = 0, blockedSheets = 0
  const scan = (list, inReduced) => {
    for (const rl of list) {
      rulesRead++
      const cond = rl.conditionText || rl.media?.mediaText || ''
      const red = inReduced || /prefers-reduced-motion/.test(cond)
      if (red && rl.style) buckets.reducedMotion++
      const t = rl.selectorText
      if (t) {
        for (const sel of t.split(',')) {
          const s = sel.trim()
          if (/:hover/.test(s)) buckets.hover.push(s)
          if (/:focus(-visible|-within)?/.test(s)) buckets.focus.push(s)
          if (/:active/.test(s)) buckets.active.push(s)
          if (/:disabled|\[disabled\]|\[aria-disabled/.test(s)) buckets.disabled.push(s)
        }
      }
      if (rl.cssRules) scan(rl.cssRules, red)
    }
  }
  for (const ss of document.styleSheets) { try { scan(ss.cssRules, false) } catch (e) { blockedSheets++ } }

  // ถอด pseudo ออกให้เหลือ selector ฐาน เพื่อถาม element ว่าโดน rule นั้นไหม
  const bases = (arr) => [...new Set(arr.map((s) =>
    s.replace(/::?(hover|focus-visible|focus-within|focus|active|disabled)/g, '')
     .replace(/:is\(\s*\)/g, '').trim()).filter(Boolean))]
  const B = { hover: bases(buckets.hover), focus: bases(buckets.focus), active: bases(buckets.active), disabled: bases(buckets.disabled) }
  const hits = (el, list) => list.some((s) => { try { return el.matches(s) } catch (e) { return false } })

  // ---------- 2. ไล่ทุก control ----------
  const SEL = 'button, a[href], input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="tab"], [role="menuitem"], [tabindex]:not([tabindex="-1"])'
  const controls = [...root.querySelectorAll(SEL)]
  const out = []
  controls.forEach((el, i) => {
    const cs = getComputedStyle(el)
    const r = el.getBoundingClientRect()
    if (r.width === 0 || r.height === 0 || cs.visibility === 'hidden') return
    const isDisabled = el.disabled === true || el.getAttribute('aria-disabled') === 'true'
    const label = (el.innerText || el.getAttribute('aria-label') || el.placeholder || '').replace(/\s+/g, ' ').trim().slice(0, 32)
    out.push({
      i, tag: el.tagName.toLowerCase(), role: el.getAttribute('role') || undefined, label: label || undefined,
      w: Math.round(r.width), h: Math.round(r.height),
      disabled: isDisabled || undefined,
      cursor: cs.cursor,
      pointerEvents: cs.pointerEvents === 'auto' ? undefined : cs.pointerEvents,
      hasHover: hits(el, B.hover),
      hasFocus: hits(el, B.focus),
      hasActive: hits(el, B.active),
      hasDisabledStyle: hits(el, B.disabled),
      transition: cs.transitionDuration === '0s' ? null : cs.transitionDuration,
      animation: cs.animationName === 'none' ? undefined : cs.animationName + ' ' + cs.animationDuration,
      outline: cs.outlineStyle === 'none' ? null : `${cs.outlineWidth} ${cs.outlineStyle} ${cs.outlineColor}`,
      tabindex: el.getAttribute('tabindex') || undefined,
      name: el.getAttribute('aria-label') || el.innerText?.trim() ? undefined : 'ไม่มีชื่อให้ screen reader',
    })
  })

  // ---------- 3. ลำดับ Tab เทียบลำดับ DOM ----------
  const focusables = controls.filter((el) => {
    const r = el.getBoundingClientRect()
    return r.width && r.height && !el.disabled && el.tabIndex >= 0 && getComputedStyle(el).visibility !== 'hidden'
  })
  const positive = focusables.filter((el) => el.tabIndex > 0).length   // tabindex > 0 ทำให้ลำดับเพี้ยน

  // ---------- 4. สรุปเป็น defect ----------
  const D = []
  const push = (sev, kind, where, detail) => D.push({ sev, kind, where, detail })
  const at = (c) => `${c.tag}${c.role ? `[${c.role}]` : ''}${c.label ? ` "${c.label}"` : ` #${c.i}`}`

  for (const c of out) {
    if (c.disabled) {
      if (c.cursor !== 'not-allowed' && c.cursor !== 'default') push('warn', 'disabled-cursor', at(c), `cursor: ${c.cursor}`)
      continue
    }
    if (!c.hasHover) push('error', 'no-hover', at(c), 'ไม่มี rule :hover ครอบ element นี้')
    if (!c.hasFocus) push('error', 'no-focus', at(c), `ไม่มี :focus style — เหลือแค่ outline ${c.outline || 'none'} ของเบราว์เซอร์`)
    if (!c.hasActive) push('warn', 'no-active', at(c), 'ไม่มี :active / pressed')
    if (c.cursor !== 'pointer' && c.tag !== 'input' && c.tag !== 'textarea' && c.tag !== 'select')
      push('error', 'cursor', at(c), `cursor: ${c.cursor} บนของที่กดได้`)
    if (Math.min(c.w, c.h) < MIN_TARGET)
      push('error', 'touch-target', at(c), `${c.w}×${c.h} < ${MIN_TARGET} (เกณฑ์ ${innerWidth >= 768 ? 'desktop WCAG 2.5.8' : 'mobile WCAG 2.5.5'})`)
    if (!c.transition && c.hasHover)
      push('warn', 'no-transition', at(c), 'มี :hover แต่ transition-duration = 0s (สลับทันที)')
    if (c.name) push('error', 'no-accessible-name', at(c), c.name)
  }
  if (positive) push('error', 'tabindex-positive', 'ทั้งหน้า', `${positive} element ใช้ tabindex > 0 — ลำดับ Tab จะไม่ตรงลำดับที่เห็น`)
  if (!buckets.reducedMotion && out.some((c) => c.animation))
    push('warn', 'no-reduced-motion', 'ทั้งหน้า', 'มี animation แต่ไม่มี @media (prefers-reduced-motion)')

  const by = (k) => D.filter((d) => d.kind === k).length
  return {
    harness: { minTarget: MIN_TARGET, viewport: innerWidth, rulesRead, blockedSheets, hoverSelectors: buckets.hover.length, focusSelectors: buckets.focus.length, activeSelectors: buckets.active.length },
    controls: out.length, focusables: focusables.length,
    summary: { noHover: by('no-hover'), noFocus: by('no-focus'), noActive: by('no-active'), cursor: by('cursor'), touchTarget: by('touch-target') },
    defects: D, rows: out,
  }
}

// ยืนยันด้วยการ hover จริง — ใช้คู่กับ computer{action:'hover', ref}
// 1) __qaHoverIdle(i)  2) computer hover  3) __qaHoverDiff()
window.__qaHoverIdle = function (i, rootSel) {
  const SEL = 'button, a[href], input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="tab"], [role="menuitem"], [tabindex]:not([tabindex="-1"])'
  const el = [...(document.querySelector(rootSel || '#root') || document.body).querySelectorAll(SEL)][i]
  if (!el) return { error: 'no element at index ' + i }
  const c = getComputedStyle(el)
  window.__qaIdle = { el, snap: [c.backgroundColor, c.color, c.borderColor, c.boxShadow, c.transform, c.opacity, c.outlineColor] }
  return { i, label: (el.innerText || '').trim().slice(0, 32), idle: window.__qaIdle.snap }
}
window.__qaHoverDiff = function () {
  const { el, snap } = window.__qaIdle || {}
  if (!el) return { error: 'เรียก __qaHoverIdle ก่อน' }
  const c = getComputedStyle(el)
  const now = [c.backgroundColor, c.color, c.borderColor, c.boxShadow, c.transform, c.opacity, c.outlineColor]
  const names = ['background', 'color', 'border', 'shadow', 'transform', 'opacity', 'outline']
  const changed = names.filter((_, i) => now[i] !== snap[i])
  return { hovering: el.matches(':hover'), changed, before: snap, after: now, verdict: el.matches(':hover') && !changed.length ? 'DEFECT: hover ติดแล้วแต่ไม่มีอะไรเปลี่ยน' : changed.length ? 'ok' : 'hover ไม่ติด — ตรวจ harness ก่อนกล่าวหาโค้ด' }
}
'ready: __qaStates() / __qaHoverIdle(i) → computer hover → __qaHoverDiff()'
