# รูปแบบรายงาน QA

ไฟล์: `docs/QA-REPORT-YYYY-MM-DD.md` ในโปรเจกต์ · ในแชทสรุปแค่ 5 บรรทัด พร้อมชื่อไฟล์

---

```markdown
# QA Report: <ชื่อ prototype>
วันที่ · ผู้ตรวจ: Claude (prototype-qa) · build: <git sha หรือวันที่แก้ล่าสุด>

**Ground truth**
| ส่วน | แหล่ง | ครบไหม |
|---|---|---|
| UI | Figma `<fileKey>` node `<id>` | ✅ / ❌ ตรวจไม่ได้เพราะ… |
| Flow | docs/flow-spec.md · N transitions | ✅ |
| Design System | <ชื่อ Design System + เวอร์ชัน> | ✅ |

**สรุป**
| | blocker | error | warn | info |
|---|---|---|---|---|
| 1a UI จอนิ่ง (ตรง Figma) | 0 | 4 | 3 | 0 |
| 1b Interaction | 0 | 2 | 1 | 0 |
| 2 Flow | 1 | 0 | 0 | 0 |
| 3 Design System | 0 | 1 | 0 | 0 |

Flow coverage: เดินได้ 4 / 4 transitions (100%) · ผ่าน 3 ไม่ผ่าน 1
UI matching: จับคู่ข้อความได้ 20 / 20 (100%)

---

## ส่วน 1a: UI จอนิ่ง (ตรง Figma ไหม)
> ค่าทั้งหมดจาก `getComputedStyle` เทียบกับ node จริง ไม่มีค่าไหนมาจากการมองภาพ
> ความกว้างหน้าจอตอนวัด: 402 (= ความกว้างเฟรม) · จับคู่ข้อความได้ 20/20

| # | ระดับ | อะไร | จอ / ที่ไหน | design | build | ต่าง |
|---|---|---|---|---|---|---|
| U1 | error | font-size | Card · ยอดเงิน | 24px | 28px | +4 |
| U2 | warn | color | Card · ข้อความใต้บัตร | #87888C | #8C8C8C | |
| U3 | warn | border-radius | Card · ปุ่ม Freeze | 20 | 18 | −2 |

## ส่วน 1b: Interaction (hover / focus / pressed / motion)
> `__qaStates()` · เกณฑ์พื้นที่กดที่ใช้: **44** (มือถือ, `harness.minTarget`)

| # | ระดับ | อะไร | control | design / เกณฑ์ | build |
|---|---|---|---|---|---|
| I1 | error | พื้นที่กดเล็ก | ปุ่มย้อนกลับ | ≥ 44×44 | 24×24 |
| I2 | warn | focus ring | ทั้งหน้า | 2px solid ตาม design | ค่า default ของ browser |

## ส่วน 2: Flow
| TC | Given | When | Then | ผล | หลักฐาน |
|---|---|---|---|---|---|
| TC-1 | Card | กด Freeze | เปิด sheet "Freeze card" | pass | sheet ขึ้น |
| TC-4 | Card | กด Transactions | ไปจอ Transactions | blocker | ยังอยู่จอ Card, ไม่มี handler |

## ส่วน 3: Design System
| # | ระดับ | อะไร | ที่ไหน | หลักฐาน |
|---|---|---|---|---|
| D1 | error | วาดเอง | src/screens/Card.tsx | Design System มี `ActionTile` แต่ไม่ได้ import |
| D2 | error | ค่าตายตัว | src/screens/Card.tsx:88 | `#1F7A37` ต้องเป็น token |
| D3 | error | ไม่ตามโหมด | Card | สลับ `data-theme` แล้ว radius นิ่ง 18px ทั้งสองโหมด |

## Known (ตกลงกันไว้แล้ว ไม่นับเป็น defect ใหม่)
- …

## ตรวจไม่ได้ / ต้องให้คนดู
- element ที่ไม่มีข้อความ N ตัว จับคู่อัตโนมัติไม่ได้

## ข้อเสนอ (ยังไม่ทำ)
- …
```

---

## เกณฑ์ระดับความรุนแรง

| ระดับ | เงื่อนไข |
|---|---|
| `blocker` | flow ตัน · จอที่สเปกมีแต่ไปไม่ถึง · หน้าพัง |
| `error` | ต่างจากสเปกแบบวัดได้ · component ที่ Design System มีแต่วาดเอง · ค่าตายตัว · ข้อความหาย |
| `warn` | ต่างไม่เกินค่าที่ยอมได้ · จับคู่ไม่ได้ · ข้อความเกินมาจาก design |
| `info` | สเปกขัดกันเอง · design ไม่ผูก text style · ข้อสังเกต |

**แถวที่ไม่มีหลักฐานเป็นตัวเลขหรือ path = ความเห็น ตัดทิ้ง**

## ตัวเลขที่ต้องมีทุกใบ
1. flow coverage (เดินได้ / ทั้งหมด) บอกว่ารายงานเชื่อได้แค่ไหน
2. อัตราจับคู่ข้อความ ถ้าต่ำกว่า 60% แปลว่าเลือกจอผิด อย่ารายงานเป็น defect
3. จำนวนที่ตรวจต่อส่วน "ไม่เจอ defect" ต้องมาคู่กับ "จากที่ตรวจ N รายการ"
