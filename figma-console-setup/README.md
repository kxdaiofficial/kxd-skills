# Prompt ติดตั้ง Figma Console MCP

**ทำอะไร:** วาง prompt นี้ใน Claude แล้วมันจะพาติดตั้ง [Figma Console MCP](https://github.com/southleft/figma-console-mcp) (open source ของ Southleft) ทีละขั้น ให้ AI อ่านและเขียนลงไฟล์ Figma ได้ผ่าน plugin ที่เปิดในเครื่องเรา ไม่กินโควต้า MCP ตัวทางการของ Figma
**ใช้กับ:** Claude Code หรือ Claude Desktop
**ต้องมี:** Mac หรือ Windows, Figma Desktop app, บัญชี Figma (ฟรีก็ได้)

## วิธีใช้

1. เปิด Claude Code หรือ Claude Desktop
2. ก๊อป prompt ในกล่องข้างล่างทั้งก้อนไปวาง แล้วส่ง
3. ทำตามที่มันบอกทีละขั้น มันจะรอให้เราตอบก่อนไปขั้นต่อไป

## Prompt (ก๊อปทั้งกล่อง)

```
ช่วยติดตั้ง Figma Console MCP (npm package: figma-console-mcp) ให้เครื่องนี้ พาทำทีละขั้น และรอให้ฉันตอบก่อนไปขั้นต่อไป

1. เช็คว่ามี Node.js 18 ขึ้นไป (node --version) ถ้าไม่มี บอกวิธีลงที่ตรงกับ OS ของฉัน
2. ถามว่าฉันใช้ Claude Code หรือ Claude Desktop แล้วเช็คว่ามี MCP ชื่อ figma-console อยู่แล้วหรือยัง ถ้ามีให้ถามก่อนเขียนทับ
3. สอนสร้าง Figma Personal Access Token (help.figma.com หัวข้อ "Manage personal access tokens")
   scope เป็น Read ทั้งหมด: File content, File versions, Library content, Library assets, Current user
   ยกเว้น Comments = Read and write · Variables ข้ามได้ (ใช้ได้เฉพาะ Enterprise)
   token ขึ้นต้นด้วย figd_ ถ้าไม่ใช่ให้ขอใหม่
   ห้ามพิมพ์ token กลับมาในแชต และห้ามบันทึกลงที่อื่นนอกจาก config ของ MCP
4. เพิ่ม MCP ชื่อ figma-console:
   - Claude Code: claude mcp add figma-console -s user -e FIGMA_ACCESS_TOKEN=<token> -e ENABLE_MCP_APPS=true -- npx -y figma-console-mcp@latest
   - Claude Desktop: merge เข้า claude_desktop_config.json (Mac: ~/Library/Application Support/Claude/ · Windows: %APPDATA%\Claude\) โดยไม่ลบ MCP ตัวอื่น
     command: npx  args: ["-y", "figma-console-mcp@latest"]  env: FIGMA_ACCESS_TOKEN, ENABLE_MCP_APPS="true"
5. บอกให้ฉัน restart Claude หนึ่งครั้ง (server จะสร้างไฟล์ plugin ให้เองตอนเริ่มทำงาน)
6. ติดตั้ง Desktop Bridge plugin:
   - หา path ของ manifest ด้วย npx figma-console-mcp --print-path (ปกติคือ ~/.figma-console-mcp/plugin/manifest.json)
   - สอนฉันใน Figma Desktop: Plugins > Development > Import plugin from manifest... เลือกไฟล์นั้น (Mac: ในหน้าต่างเลือกไฟล์ กด Cmd+Shift+G แล้ววาง path เพราะโฟลเดอร์นี้ซ่อนอยู่)
   - เปิดไฟล์ Figma แล้วรัน Plugins > Development > Figma Desktop Bridge (มันจะต่อกับ server เอง)
7. ทดสอบด้วย figma_get_status ว่าต่อกับไฟล์และบัญชี Figma ที่ถูกต้อง
8. สรุปท้ายเป็นตาราง: Node, Token, Config, Bridge plugin, สถานะการเชื่อมต่อ
```

## ใช้ยังไงต่อ

- เปิด plugin Figma Desktop Bridge ค้างไว้ตอนทำงาน แล้วสั่ง Claude โดยแปะลิงก์ไฟล์ Figma ได้เลย
- จะใช้คู่กับ Figma MCP ตัวทางการก็ได้: อ่านด้วยตัวทางการ เขียนลง canvas ด้วย Console
- ถ้าอัปเดตเวอร์ชันแล้ว plugin ขึ้นเตือน ให้ import manifest ไฟล์เดิมซ้ำอีกครั้ง

อ้างอิงจาก README ของ figma-console-mcp v1.46.0 (พ.ย. 2026) ขั้นตอนอาจเปลี่ยนตามเวอร์ชัน ลองแล้วติดตรงไหน ทักมาที่เพจได้เลยครับ
