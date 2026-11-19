// prototype-qa — Lane 1, ฝั่ง Figma
// รันผ่าน figma-console bridge:  mcp__figma-console__figma_execute  (โฟกัสหน้าต่าง Figma ก่อน)
// เรียก:  await __qaFigma('1:74069')     // node id ของจอ จาก docs/screen-inventory.md
// คืน object รูปแบบเดียวกับ __qaMeasure ของฝั่ง DOM เพื่อให้ compare.mjs จับคู่ได้
//
// ยิงหลาย node พร้อมกันได้ ผลลัพธ์ใหญ่จะถูก spill เป็นไฟล์ — ตั้งใจให้เป็นแบบนั้น
// แล้วไป process ไฟล์ด้วย python/node อย่าลากผ่าน context

async function __qaFigma(nodeId) {
  const root = await figma.getNodeByIdAsync(nodeId)
  if (!root) return { error: 'node not found: ' + nodeId }
  const ox = root.absoluteBoundingBox.x, oy = root.absoluteBoundingBox.y

  const hex = (p) => {
    if (!p || !p.length) return undefined
    const f = p.find((x) => x.visible !== false && x.type === 'SOLID')
    if (!f) return undefined
    const c = f.color, n = (v) => Math.round(v * 255)
    const a = f.opacity === undefined ? 1 : f.opacity
    return a === 1 ? `rgb(${n(c.r)}, ${n(c.g)}, ${n(c.b)})` : `rgba(${n(c.r)}, ${n(c.g)}, ${n(c.b)}, ${Math.round(a * 100) / 100})`
  }
  const num = (v) => (typeof v === 'number' ? Math.round(v * 100) / 100 : undefined)
  const lh = (v) => (!v || v.unit === 'AUTO' ? undefined : v.unit === 'PIXELS' ? num(v.value) : num(v.value) + '%')
  const ls = (v) => (!v || !v.value ? undefined : v.unit === 'PIXELS' ? num(v.value) : num(v.value) + '%')

  const rows = []
  let seq = 0
  const walk = (n, depth) => {
    if (n.visible === false || depth > 24 || rows.length > 3000) return
    const b = n.absoluteBoundingBox
    if (!b) { if (n.children) n.children.forEach((c) => walk(c, depth + 1)); return }
    const isText = n.type === 'TEXT'
    const paints = n.fills && n.fills !== figma.mixed && n.fills.some((f) => f.visible !== false)
    if (isText || paints || n.type === 'VECTOR' || n.type === 'RECTANGLE') {
      const row = {
        i: seq++,
        type: n.type,
        name: n.name,
        text: isText ? String(n.characters).replace(/\s+/g, ' ').trim() || undefined : undefined,
        x: Math.round(b.x - ox), y: Math.round(b.y - oy),
        w: num(b.width), h: num(b.height),
      }
      if (isText) {
        const f = n.fontName
        if (f && f !== figma.mixed) { row.ff = f.family; row.fw = f.style }
        if (n.fontSize !== figma.mixed) row.fs = num(n.fontSize)
        row.lh = lh(n.lineHeight !== figma.mixed ? n.lineHeight : null)
        row.letterSpacing = ls(n.letterSpacing !== figma.mixed ? n.letterSpacing : null)
        row.color = hex(n.fills !== figma.mixed ? n.fills : null)
        row.textStyleId = n.textStyleId && n.textStyleId !== figma.mixed ? String(n.textStyleId) : undefined
      } else {
        row.backgroundColor = hex(n.fills !== figma.mixed ? n.fills : null)
      }
      const r = n.cornerRadius
      if (typeof r === 'number' && r > 0) row.borderRadius = r
      if (n.layoutMode && n.layoutMode !== 'NONE') {
        row.layout = n.layoutMode
        row.paddingTop = n.paddingTop; row.paddingRight = n.paddingRight
        row.paddingBottom = n.paddingBottom; row.paddingLeft = n.paddingLeft
        row.gap = n.itemSpacing
        // ⚠️ ลูกที่เป็น LINE หมุน -90° กินความกว้าง 0 ใน auto-layout แต่วาด 1px
        //    อย่าเอา w ของมันไปเป็น spacing — ให้บวกความกว้างลูกเองเทียบกับ w ของ frame
      }
      if (n.strokes && n.strokes.length && n.strokeWeight) {
        row.borderTopWidth = num(n.strokeWeight); row.borderColor = hex(n.strokes)
      }
      // ตัวแปรที่ผูกอยู่จริง — ใช้พิสูจน์ว่าค่ามาจาก token ไม่ใช่พิมพ์เอง
      if (n.boundVariables && Object.keys(n.boundVariables).length) row.bound = Object.keys(n.boundVariables)
      rows.push(row)
    }
    if (n.children) n.children.forEach((c) => walk(c, depth + 1))
  }
  walk(root, 0)

  return { node: nodeId, name: root.name, w: num(root.absoluteBoundingBox.width), h: num(root.absoluteBoundingBox.height), n: rows.length, rows }
}
