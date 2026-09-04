# 11. Exhaustive Bilingual Architecture & Visual Verification Record

**Date**: 2026-09-03  
**Status**: Resolved & Verified  
**Scope**: Full Desktop Application Internationalization (Bilingual Chinese / English)

---

## 1. Problem Definition & Root Cause Analysis

### 1.1 Symptoms Reported by User
When users toggled the application language from Chinese (`zh`) to English (`en`):
- While the top-level navigation and some titles changed to English, inside engineering workstation calculation panels (e.g. `MagTransformerPanel`, `FlybackPanel`, `BuckDesignPanel`), large amounts of residual Chinese remained.
- Fragmented or hybrid phrases appeared, such as:
  - `"• 磁芯Loss"` (partial replacement of `"损耗"`)
  - `"工作Frequency fsw (kHz)"` (partial replacement of `"频率"`)
  - `"设计Calculation Results"` (partial replacement of `"计算结果"`)
  - `"最 Min输 In Vin_min (V)"` (fragmented replacement from single-character fallbacks)
  - Unmatched tabs and buttons: `"• 正激/桥式"`, `"• 填充率与层高"`, `"• Steinmetz拟合"`, `"重置卡片布局"`
  - The top-left header badge still showed `"中文"`.

### 1.2 Root Cause Analysis
1. **Compound Word Fragmentation**:
   Generic short-word replacement dictionaries (e.g. `'损耗' -> 'Loss'`, `'输入' -> 'Input'`) match substrings inside composite engineering terms before or in absence of specific compound keys. For instance, `"磁芯损耗"` was partially modified into `"磁芯Loss"`.
2. **Subtle Typography and Case Variations**:
   Terms like `"SteinMetz拟合"` (capital M in dictionary) failed to match `"Steinmetz拟合"` (lowercase m in JSX).
3. **Absence of Domain-Specific Compounds in Dictionary**:
   Specific power electronics terms such as `"正激/桥式"`, `"填充率与层高"`, `"工作磁密"`, `"磁芯截面积"`, `"重置卡片布局"` were not present in the dictionary.
4. **Single-Character Fallback Hazard**:
   Blindly replacing single Chinese characters character-by-character led to awkward, broken terms (such as turning `"最低输入"` into `"最 Min 输 In"`).
5. **Static / Ambiguous Language Toggle Labels**:
   Single-button labels showing only the target language (e.g. showing `"中文"` when in English mode to indicate "click to switch to Chinese") caused users to believe the app was still stuck in Chinese mode.

---

## 2. Engineering Solution Architecture

### 2.1 Hierarchical Translation Mapping (`autoTranslateDict.ts`)
The translation dictionary was restructured into three explicit hierarchical tiers:
1. **Tier 1: Full Sentences, Explanations & 40 Module Titles**:
   Complete sentences (e.g. design guidelines, mathematical notes, and the 40 toolbox flagship modules) are matched in full to ensure natural, idiomatic phrasing.
2. **Tier 2: Engineering Compound Terms & Form Labels**:
   Exact domain phrases (e.g. `"正激/桥式" -> "Forward / Bridge"`, `"填充率与层高" -> "Fill Factor & Layer Height"`, `"磁芯截面积" -> "Core Cross-Section Area"`, `"重置卡片布局" -> "Reset Card Layout"`).
3. **Tier 3: Atomic Engineering Vocabulary**:
   Core nouns and adjectives provided with trailing spaces to facilitate clean composite formation without word butchering.

### 2.2 Strict Sorting by Length Descending (`b.length - a.length`)
In `useAutoTranslator.ts`, dictionary keys are strictly sorted by length descending before replacement:
```typescript
const sortedKeys = Object.keys(dict).sort((a, b) => b.length - a.length);
```
This guarantees that longer compound phrases match and replace first before any individual sub-words can be touched.

### 2.3 Comprehensive DOM Traversal & Mutation Observer
`useAutoTranslator.ts` intercepts:
- DOM text nodes (`Node.TEXT_NODE`)
- Input placeholders (`el.placeholder`)
- Tooltip attributes (`el.title`)
- Select dropdown options (`<option>` tags)
- Mathematical protection: Spans with `.katex` or math equations are strictly shielded from translation.
- `MutationObserver` ensures dynamically added cards, asynchronous calculation results, and tab changes are translated instantly.

### 2.4 Two-State Clear Language Toggle Indicators
The UI toggles in the sidebar and header were updated to show two-state indicators with the active language highlighted:
- Sidebar: `中 / EN` (with active language highlighted in cyan).
- Header: `中文 / English` (with active language highlighted in cyan).

---

## 3. Visual Verification Results

Live verification via DevTools and headless browser inspection:
1. **Navigation Sidebar**: All categories and 40 modules render in clean English.
2. **Panel Header & Description**: Fully translated into English.
3. **Subtabs**: All tabs (`Forward / Bridge`, `Isolated Flyback`, `LLC Integrated`, `Core Sizing (AP)`, `Fill Factor & Layer Height`, `Core Loss`, `AC Resistance Factor Fr`, `Primary Leakage Inductance`, `Steinmetz Fitting`) are 100% English.
4. **Card Headers & Controls**: `Forward / Bridge Input Parameters`, `Design Calculation Results`, `Design Analytical Equations`, `Reset Card Layout` all render cleanly.
5. **Form Labels & Select Options**: `Topology Structure`, `Full Bridge`, `Minimum Input Vin_min (V)`, `Maximum Duty Cycle Dmax`, `Operating Flux Density Bac (T)`, etc. render without any residual Chinese.
6. **Reversibility**: Toggling back to Chinese instantly restores full native Chinese labels and equations without state distortion.
