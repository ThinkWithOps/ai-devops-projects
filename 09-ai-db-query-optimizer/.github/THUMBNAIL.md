# Thumbnail Guide — AI Database Query Optimizer

## Concept

**The contrast story in a single image:**
- LEFT (dark red/danger): Query log showing 847 repeated SELECTs, clock showing 3.1s
- CENTER (electric yellow): "AI FOUND IT" with lightning bolt
- RIGHT (dark green/success): Clean terminal "1 QUERY | 48ms"
- TOP TEXT (white, bold): "YOUR APP HAS BEEN LYING TO YOU"
- BOTTOM (subtle): "847 HIDDEN QUERIES → 1"

---

## AI Image Generation Prompt

Use with Midjourney, DALL-E 3, or Stable Diffusion:

```
Split-screen dark terminal dashboard, professional tech YouTube thumbnail style.

LEFT SIDE (deep red #1A0000 background, danger mood):
- Dark terminal window showing repeating SQL queries in red monospace font:
  SELECT * FROM orders WHERE user_id = 1
  SELECT * FROM orders WHERE user_id = 2
  SELECT * FROM orders WHERE user_id = 3
  ... (847 more lines, fading into background)
- Digital clock overlay showing "3.1s" in large red numbers
- Subtle red glow/vignette effect

CENTER (narrow strip):
- Large neon yellow/white lightning bolt icon
- Text below: "AI FOUND IT" in bold white

RIGHT SIDE (deep green #001A00 background, success mood):
- Clean dark terminal window showing:
  INDEX SCAN: idx_orders_user_id
  Rows: 14 (not 500,000)
  Time: 48ms
- Large green "48ms" number
- Green checkmark icon

TOP BANNER:
- Full-width black bar with white bold text (Impact or similar heavy font):
  "YOUR APP HAS BEEN LYING TO YOU"

BOTTOM:
- Small text: "847 QUERIES → 1"

Overall style: High contrast, cinematic dark tech aesthetic, professional YouTube thumbnail,
8K sharp text, no blur, clean layout, no stock photos, terminal/code only.
```

---

## ASCII Concept Layout

```
┌─────────────────────────────────────────────────────────────┐
│         YOUR APP HAS BEEN LYING TO YOU                       │
│                  (white bold, black bar)                      │
├──────────────────────┬──────┬──────────────────────────────┤
│  🔴 DARK RED SIDE    │  ⚡  │  🟢 DARK GREEN SIDE          │
│                      │      │                                 │
│  SELECT * FROM       │  AI  │  Index Scan ✅                 │
│  orders WHERE        │FOUND │  idx_orders_user_id            │
│  user_id = 1         │  IT  │  Rows: 14                      │
│  SELECT * FROM       │      │                                 │
│  orders WHERE        │      │  ██████                        │
│  user_id = 2         │      │  48ms                          │
│  SELECT * FROM       │      │  (big green text)               │
│  ... (847 more)      │      │                                 │
│                      │      │                                 │
│  ⏱️  3.1s            │      │                                 │
│  (big red clock)     │      │                                 │
├──────────────────────┴──────┴──────────────────────────────┤
│              847 QUERIES → 1   |   $2,400/year → $37        │
└─────────────────────────────────────────────────────────────┘
```

---

## Color Scheme

| Element | Hex | Usage |
|---------|-----|-------|
| Left background | `#1A0000` | Danger/crime side |
| Right background | `#001A00` | Success/fixed side |
| Top banner | `#000000` | Title bar |
| Title text | `#FFFFFF` | "YOUR APP HAS BEEN LYING TO YOU" |
| Left SQL text | `#FF4444` | Repeated bad queries |
| Right terminal text | `#00FF88` | Success output |
| Clock "3.1s" | `#FF2200` | Before time |
| Speed "48ms" | `#00FF44` | After time |
| Lightning bolt | `#FFD700` | Center divider |
| "AI FOUND IT" | `#FFFF00` | Center text |
| "847 QUERIES → 1" | `#CCCCCC` | Bottom subtitle |

---

## Manual Canva Guide

### Canvas Setup
- Size: **1280 × 720 px** (YouTube standard 16:9)
- Background: solid black `#000000`

### Step 1 — Top Banner
- Add rectangle: full width, 80px tall, black fill `#000000`
- Add text: "YOUR APP HAS BEEN LYING TO YOU"
  - Font: Impact or Anton (Google Fonts)
  - Size: 52pt
  - Color: white `#FFFFFF`
  - Align: center

### Step 2 — Left Side (Danger Zone)
- Add rectangle: 500×600px at x=0, y=80
- Fill: `#1A0000` (very dark red)
- Add text block — monospace font (Courier New or Source Code Pro):
  ```
  SELECT * FROM orders
  WHERE user_id = 1;
  SELECT * FROM orders
  WHERE user_id = 2;
  SELECT * FROM orders
  WHERE user_id = 3;
  [... 847 times]
  ```
- Text color: `#FF4444`
- Size: 16pt
- Add large text "3.1s" — font Impact, size 80pt, color `#FF2200`
- Add clock emoji or icon above "3.1s"

### Step 3 — Center Divider
- Add narrow rectangle: 80×600px, x=500, y=80
- Fill: `#111111`
- Add lightning bolt emoji or SVG icon: centered at x=540, y=300
  - Size: 80px, color `#FFD700`
- Add text "AI FOUND IT" below:
  - Font: Impact, size 22pt
  - Color: `#FFFF00`
  - Centered

### Step 4 — Right Side (Success Zone)
- Add rectangle: 700×600px at x=580, y=80
- Fill: `#001A00` (very dark green)
- Add text block — monospace font:
  ```
  Index Scan ✓
  idx_orders_user_id
  Rows: 14 (not 500,000)
  ```
- Text color: `#00FF88`
- Size: 18pt
- Add large text "48ms" — font Impact, size 80pt, color `#00FF44`
- Add checkmark icon above "48ms"

### Step 5 — Bottom Strip
- Add rectangle: full width, 40px tall at y=680
- Fill: `#111111`
- Add text: "847 QUERIES → 1    |    $2,400/year → $37"
  - Font: Bold sans-serif
  - Size: 18pt
  - Color: `#AAAAAA`
  - Centered

### Step 6 — Final Polish
- Add subtle red glow behind the "3.1s" text (drop shadow effect, red)
- Add subtle green glow behind "48ms" text
- Export as PNG 1280×720

---

## Alternative Simple Version (10 minutes)

If the split-screen is too complex:

**Background:** Dark gradient (black → very dark navy)

**Large centered text (3 lines):**
```
847 QUERIES
↓
1 (with index)
```

**Top left corner:** "BEFORE: 3.1s" in red
**Top right corner:** "AFTER: 48ms" in green
**Bottom center:** "AI FOUND THE $2,400/YEAR BUG" in yellow
