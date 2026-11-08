# Skill: Figma → prototype ที่กดได้ (design-to-code)

**ใช้กับ:** Claude Code (หรือ agent ที่อ่าน SKILL.md ได้ เช่น Codex, Cursor) + **Figma MCP ตัวทางการ** ต่อไว้แล้ว
**ที่มา:** สกิลที่ผมใช้ทำงานจริง ปรับให้ใช้กับไฟล์ Figma ของใครก็ได้ ไม่ต้องมี design system
**ได้อะไร:** prototype เป็นโค้ด (HTML/CSS/JS ไฟล์เดียว) หน้าตาตามดีไซน์ กดไปตามโฟลว์ได้ เปิดบนมือถือไปคุยกับ stakeholder หรือเทสกับผู้ใช้ · **ไม่ใช่โค้ดส่ง production** (ปุ่มทุกปุ่ม AI สร้างเอง ไม่ได้มาจาก library)

## วิธีติดตั้ง

1. ต่อ Figma MCP ให้ Claude Code ตามหน้า Figma MCP server ของ Figma (เช็คว่าใช้ได้: ถาม Claude ว่า "อ่านเฟรมนี้ให้หน่อย" แล้วแปะลิงก์)
2. สร้างโฟลเดอร์ `~/.claude/skills/design-to-code/` แล้ววางไฟล์ [`SKILL.md`](SKILL.md) ในโฟลเดอร์นี้ลงไป (หรือก๊อปกล่องข้างล่างไปเซฟเป็นไฟล์ `SKILL.md` ก็ได้)
3. เปิด Claude Code ใหม่ แล้วพิมพ์ เช่น "ทำ prototype จาก section นี้ [ลิงก์ Figma]"

## SKILL.md (ก๊อปทั้งกล่อง)

```
---
name: design-to-code
description: Turn a finished Figma design (a frame or a section of frames, with or without connectors) into a clickable coded prototype for stakeholder reviews and usability tests. Trigger on "ทำ prototype จาก figma", "design to code", "แปลงดีไซน์เป็นโค้ด", "build this frame", or a Figma link with a request to make it clickable.
---

# Design to code

เป้าหมาย: prototype ที่ "หน้าตาเหมือนในดีไซน์" และ "กดตามโฟลว์ได้" เปิดบนมือถือได้ ไม่ใช่โค้ด production

## กฎเหล็ก
1. ค่าทุกค่ามาจาก Figma ไม่ใช่จากสายตา: ระยะ สี ฟอนต์ ขนาด มุมโค้ง อ่านจาก node ผ่าน Figma MCP ถ้าอ่านไม่ได้ ให้บอกว่าอ่านไม่ได้ ห้ามเดา
2. ห้ามเติมของที่ดีไซน์ไม่มี: ไม่เพิ่มจอ ไม่เพิ่มปุ่ม ไม่เปลี่ยนคำ ข้อความบนจอใช้ตามดีไซน์ทุกตัวอักษร
3. รูปและไอคอนใช้ไฟล์จริงจาก Figma (export / download asset) ห้ามวาดใหม่ ห้ามใช้ emoji แทน
4. โฟลว์มาจากบอร์ด: ใช้ prototype link หรือเส้น connector ในไฟล์ ถ้าไฟล์ไม่มีทั้งสองอย่าง ให้ถามลำดับจอก่อนเริ่ม 1 ครั้ง

## ขั้นตอน
0. อ่านภาพรวม: get_metadata ของลิงก์ที่ได้ → รายชื่อเฟรม (จอ) · get_metadata และ get_design_context **ไม่ส่ง prototype link มาให้** ต้องอ่านด้วย use_figma แบบอ่านอย่างเดียว (ไม่แก้ไฟล์) ด้วยสคริปต์นี้ โดยแทน SECTION_ID ด้วย node id ของ section:
   const sec = await figma.getNodeByIdAsync("SECTION_ID"); const out = [];
   for (const n of sec.findAll(n => "reactions" in n && n.reactions.length)) for (const r of n.reactions) for (const a of (r.actions || [r.action]).filter(Boolean)) {
     const dest = a.destinationId ? await figma.getNodeByIdAsync(a.destinationId) : null; let s = n;
     while (s.parent && s.parent.type !== "SECTION" && s.parent.type !== "PAGE") s = s.parent;
     out.push({ from: s.name, tap: n.name, trigger: r.trigger && r.trigger.type, to: dest && dest.name }); }
   return out;
   บอร์ด user flow / wireframe ที่โยงจอด้วยเส้นลูกศรวาดเอง (line / vector ไม่ใช่ prototype link) ใช้สคริปต์นี้ (อ่านอย่างเดียว) หาว่าปลายเส้นแตะจอไหน:
   const sec = await figma.getNodeByIdAsync("SECTION_ID");
   const frames = sec.children.filter(n => n.type === "FRAME").map(f => ({ name: f.name, b: f.absoluteBoundingBox }));
   const near = (p) => { let best = null, bd = 1e9; for (const f of frames) { const { x, y, width: w, height: h } = f.b;
     const d = Math.hypot(Math.max(x - p.x, 0, p.x - (x + w)), Math.max(y - p.y, 0, p.y - (y + h))); if (d < bd) { bd = d; best = f.name; } } return { frame: best, gap: Math.round(bd) }; };
   const out = [];
   for (const n of sec.findAll(n => n.type === "LINE" || n.type === "VECTOR")) { const t = n.absoluteTransform; let a, b;
     if (n.type === "LINE") { a = { x: t[0][2], y: t[1][2] }; b = { x: t[0][2] + t[0][0] * n.width, y: t[1][2] + t[1][0] * n.width }; }
     else { const v = n.vectorNetwork.vertices, p = (q) => ({ x: t[0][0] * q.x + t[0][1] * q.y + t[0][2], y: t[1][0] * q.x + t[1][1] * q.y + t[1][2] }); a = p(v[0]); b = p(v[v.length - 1]); }
     const s = near(a), e = near(b); out.push({ line: n.name, from: s.frame, to: e.frame, startGap: s.gap, endGap: e.gap }); }
   return out;
   gap = ระยะจากปลายเส้นถึงขอบจอ (px) · gap มากกว่า ~40 หรือเส้นที่มีกล่องเงื่อนไข (diamond) / ป้าย Yes-No คั่น ให้ติดป้าย [ต้องยืนยัน] แล้วถามก่อน · ถ้า use_figma ใช้ไม่ได้ ให้ถามลำดับจอ
   แล้วเขียนเป็นตาราง "จอ → ปุ่มที่กด → ไปจอไหน" ให้ผู้ใช้ดูก่อน
1. ทีละจอ: get_screenshot (ภาพไว้เทียบ) + get_design_context (โครง + ค่า) + get_variable_defs (ถ้าไฟล์มี variable) จดค่าที่ใช้ซ้ำไว้เป็น CSS variables ด้านบนไฟล์ (สี ฟอนต์ ระยะ) แล้วใช้ตัวแปรนั้นทั้งไฟล์
2. สร้าง `prototype/index.html` ไฟล์เดียว: แต่ละเฟรม = 1 section ซ่อน/แสดงด้วย JS · ขนาดจอตามเฟรมใน Figma (เช่น 390 หรือ 393 กว้าง) · มี `<meta name="viewport" content="width=device-width, initial-scale=1">`
3. ต่อโฟลว์: ทุกแถวในตารางขั้น 0 ต้องกดได้จริง · bottom sheet / popup แสดงทับจอเดิม · ปุ่ม Back กลับจอก่อนหน้า
4. ตรวจก่อนบอกว่าเสร็จ: เปิดในเบราว์เซอร์ กดครบทุกเส้นทางในตาราง · วางภาพแต่ละจอคู่กับ screenshot จาก Figma ที่ความกว้างเท่ากัน เทียบทีละบล็อก จุดไหนไม่ตรง แก้ หรือรายงานว่าไม่ตรงเพราะอะไร
5. ส่งต่อ: บอกวิธีเปิดบนมือถือ (เช่น deploy ขึ้น Vercel / Netlify แบบ static หรือเปิดผ่าน Wi-Fi เดียวกัน) แล้วสรุปสั้นๆ ว่า จอไหนตรง 100% จอไหนมีจุดต่าง และอะไรที่ไม่ได้ทำ

## สิ่งที่ตัวนี้ไม่ทำ (บอกผู้ใช้ตรงๆ)
- ไม่ใช้ component จาก design system หรือ library ของทีม ทุกปุ่มสร้างขึ้นใหม่ในไฟล์ → ถ้าจะส่งให้ dev ใช้ต่อ ต้องต่อ design system เพิ่ม (Level 4)
- ไม่ทำ state ที่ดีไซน์ไม่ได้วาด (error, loading, empty) ถ้าไม่มีในไฟล์
```

---

ลองแล้วติดตรงไหน ทักมาที่เพจ KXD.ai ได้เลยครับ
facebook.com/kxdai.official · IG @kxd.ai
