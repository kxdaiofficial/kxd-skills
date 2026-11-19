# สกิล prototype-qa (KXD.ai #23) · ใช้กับ Claude Code + Figma

ให้ AI เป็น QA tester ตรวจ prototype ที่เป็น code เทียบกับ design ใน Figma แล้วออกรายงาน defect อย่างเดียว ไม่แก้โค้ดให้

## ติดตั้ง (ครั้งเดียว)
1. ต่อ Figma MCP เข้ากับ Claude Code (ตัวทางการของ Figma)
2. ให้ Claude Code คุม browser ได้ (Claude in Chrome, Playwright MCP หรือ browser ในแอป Claude)
3. ก๊อปทั้งโฟลเดอร์นี้ (`SKILL.md`, `references/`, `scripts/`) ไปไว้ที่ `~/.claude/skills/prototype-qa/`
   (Windows: `%USERPROFILE%\.claude\skills\prototype-qa\`) แล้วเปิด Claude Code ใหม่

## ใช้
1. เปิด Claude Code ในโฟลเดอร์ prototype แล้วรัน prototype ไว้
2. ส่งลิงก์ Figma ของจอที่จะตรวจ (ลิงก์ที่มี `node-id`)
3. ถ้ามี flow ให้พิมพ์เป็นบรรทัด เช่น `Card --กด Freeze--> Freeze sheet`
4. พิมพ์ "ตรวจ prototype ให้หน่อย"
5. ได้ไฟล์ `docs/QA-REPORT-<วันที่>.md`: จอไหน ผิดตรงไหน design เป็นเท่าไหร่ ของจริงเป็นเท่าไหร่ test case ผ่านกี่ข้อ และใช้ Design System จริงไหม

## มีอะไรในโฟลเดอร์
| ไฟล์ | ทำอะไร |
|---|---|
| `SKILL.md` | ขั้นตอนและกฎของ QA |
| `references/report-format.md` | รูปแบบรายงาน |
| `scripts/measure-dom.js` | วัดค่า CSS จริงของทุก element บนหน้า |
| `scripts/measure-states.js` | หา hover / focus / pressed / พื้นที่กด ครบทุก control ในครั้งเดียว |
| `scripts/figma-measure.js` | วัดค่าใน node ของ Figma ให้อยู่ในรูปเดียวกับฝั่ง DOM (ใช้ได้เมื่อ MCP ที่ต่อรัน JavaScript ใน Figma ได้) |
| `scripts/compare.mjs` | จับคู่สองฝั่งด้วยข้อความ แล้วออกตารางส่วนต่าง |
