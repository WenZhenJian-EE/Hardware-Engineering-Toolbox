# 11. Exhaustive Bilingual Architecture & Visual Verification Record

**Date**: 2026-09-03  
**Status**: Resolved & Verified  
**Scope**: Full Desktop Application Internationalization (Bilingual Chinese / English)

---

## 1. Problem Definition & Root Cause Analysis

### 1.1 Symptoms Reported by User
When users toggled the application language from default locale to English (`en`):
- While the top-level navigation and some titles changed to English, inside engineering workstation calculation panels (e.g. `MagTransformerPanel`, `FlybackPanel`, `BuckDesignPanel`), large amounts of residual non-English strings remained.
- Fragmented or hybrid phrases appeared due to partial word replacements, such as:
  - Hybrid terms mixing English with untranslated characters (e.g., partial replacement of "Loss" or "Frequency").
  - Fragmented phrases resulting from single-character substring matches (e.g., distorted input labels like "Min Input").
  - Unmatched tabs and buttons: Forward/Bridge mode tabs, Fill Factor & Layer Height tabs, Steinmetz Fitting tabs, and Card Layout Reset buttons.
  - The top-left header badge failed to reflect the active English state accurately.

### 1.2 Root Cause Analysis
1. **Compound Word Fragmentation**:
   Generic short-word replacement dictionaries (e.g. mapping "Loss" or "Input" individually) matched substrings inside composite engineering terms before specific compound keys could be evaluated, creating corrupted hybrid words.
2. **Subtle Typography and Case Variations**:
   Terms with case differences (such as capital 'M' in dictionary vs. lowercase 'm' in JSX) failed to match strict equality lookups.
3. **Absence of Domain-Specific Compounds in Dictionary**:
   Specific power electronics terms such as Forward/Bridge topologies, winding fill factor, working flux density, core cross-sectional area, and layout reset triggers were missing from the initial dictionary.
4. **Single-Character Fallback Hazard**:
   Blindly replacing individual characters character-by-character led to distorted, fragmented terms.
5. **Static / Ambiguous Language Toggle Labels**:
   Single-button labels showing only the target language caused ambiguity about whether English mode was currently active.

---

## 2. Engineering Solution Architecture

### 2.1 Hierarchical Translation Mapping (`autoTranslateDict.ts`)
The translation dictionary was restructured into three explicit hierarchical tiers:
1. **Tier 1: Full Sentences, Explanations & 40 Module Titles**:
   Complete sentences (e.g. design guidelines, mathematical notes, and the 40 toolbox flagship modules) are matched in full to ensure natural, idiomatic phrasing.
2. **Tier 2: Engineering Compound Terms & Form Labels**:
   Exact domain phrases (e.g. Forward / Bridge, Fill Factor & Layer Height, Core Cross-Section Area, Reset Card Layout).
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
- Sidebar: `ZH / EN` (with active language highlighted in cyan).
- Header: `Locale / English` (with active language highlighted in cyan).

---

## 3. Visual Verification Results

Live verification via DevTools and headless browser inspection:
1. **Navigation Sidebar**: All categories and 40 modules render in clean English.
2. **Panel Header & Description**: Fully translated into English.
3. **Subtabs**: All tabs (`Forward / Bridge`, `Isolated Flyback`, `LLC Integrated`, `Core Sizing (AP)`, `Fill Factor & Layer Height`, `Core Loss`, `AC Resistance Factor Fr`, `Primary Leakage Inductance`, `Steinmetz Fitting`) are 100% English.
4. **Card Headers & Controls**: `Forward / Bridge Input Parameters`, `Design Calculation Results`, `Design Analytical Equations`, `Reset Card Layout` all render cleanly.
5. **Form Labels & Select Options**: `Topology Structure`, `Full Bridge`, `Minimum Input Vin_min (V)`, `Maximum Duty Cycle Dmax`, `Operating Flux Density Bac (T)`, etc. render without any residual non-English characters.
6. **Reversibility**: Toggling between locales instantly updates all labels and equations without state distortion.
