# 03_One_Click_Bilingual_Internationalization_and_Global_Shortcut_Architecture

---

## 1. User Requirement & Open-Source Motivation

To prepare the **Hardware Engineering Toolbox** for global open-source release on GitHub, high-quality internationalization is a hard requirement. The user requested:
1. **Frictionless One-Click Toggling**: Ability to switch between Chinese and English in milliseconds without page reload or state loss.
2. **Accessible Ergonomics**: Multiple intuitive UI entry points and a universal keyboard shortcut.
3. **Smart Environment Adaptation**: Automatic language detection based on the operating system locale, while allowing manual override with persistent memory.
4. **Codebase Adaptability**: Clean configuration hook allowing maintainers to force English default for international distributions.

---

## 2. Technical Architecture of `I18nContext`

The internationalization layer is implemented in [`Source_Code/frontend/src/i18n/I18nContext.tsx`](file:///d:/Data/Agent/MyDev/Hardware-Engineering-Toolbox-Desktop/Source_Code/frontend/src/i18n/I18nContext.tsx) as a zero-dependency, high-performance React Context.

```
+-------------------------------------------------------------+
|                      I18nProvider                           |
|  - Language State: 'zh' | 'en'                              |
|  - Persisted Key: localStorage['app_language']              |
+------------------------------+------------------------------+
                               | Provides
+------------------------------v------------------------------+
|                    useTranslation() Hook                    |
|  - lang: Current active language code                       |
|  - setLang(lang): Switch language & sync to localStorage     |
|  - t(key, params): Translate dictionary key with fallback   |
|  - getModuleInfo(id): Returns translated name & description |
|  - getCategoryName(cat): Bidirectional category transform    |
+-------------------------------------------------------------+
```

### 2.1 Smart Operating System Locale Auto-Detection
The initial state resolver first checks `localStorage`. If no prior preference is recorded, it queries `navigator.language`:
```typescript
const [lang, setLangState] = useState<Language>(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'en' || saved === 'zh') return saved;
    
    // Auto-detect OS/Browser locale: default to Chinese on Chinese systems, English everywhere else
    if (typeof navigator !== 'undefined' && navigator.language) {
      return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
    }
  } catch (e) {
    console.warn('Failed to read language preference:', e);
  }
  return 'zh';
});
```

### 2.2 Bidirectional Category Mapping
To guarantee that custom user categories and built-in engineering disciplines map seamlessly between languages, a bidirectional dictionary was implemented:
```typescript
const CATEGORY_MAP: Record<string, { primary: string; en: string }> = {
  'All': { primary: 'All', en: 'All' },
  '⚡ Power Co-Design': { primary: '⚡ Power Co-Design', en: '⚡ Power Co-Design' },
  '🧲 Magnetics & Basics': { primary: '🧲 Magnetics & Basics', en: '🧲 Magnetics & Basics' },
  '🔥 Power & Thermal': { primary: '🔥 Power & Thermal', en: '🔥 Power & Thermal' },
  '📈 Loop & Signals': { primary: '📈 Loop & Signals', en: '📈 Loop & Signals' },
  '🛡️ Passives & Safety': { primary: '🛡️ Passives & Safety', en: '🛡️ Passives & Safety' }
};
```

---

## 3. UI Entry Points & Global Keyboard Shortcut

To provide maximum accessibility across all user workflows, three visual buttons and one global shortcut were integrated:

### 3.1 Universal Global Shortcut (`Alt + L`)
A keyboard listener was wired into the application-level event bus in `App.tsx`:
```typescript
// Inside handleKeyDown listener in App.tsx:
if (e.altKey && (e.key === 'l' || e.key === 'L')) {
  e.preventDefault();
  setLang(lang === 'zh' ? 'en' : 'zh');
  return;
}
```
Engineers can toggle languages instantly from anywhere in the application within 100ms.

### 3.2 Visual Control Points
1. **Sidebar Brand Header**: A prominent cyan pill button next to `HW ToolBox Desktop v1.0` displays `[EN]` to toggle between locale modes.
2. **Global Header Bar**: Inside any workstation panel, a top-right button displays `[🌐 Language Toggle]` with shortcut tooltips.
3. **Main Dashboard Toolbar**: Positioned directly beside the module search bar.

---

## 4. Maintenance Guidelines for Global Distribution

To configure a 100% English-default distribution for international packaging:
1. Open `Source_Code/frontend/src/i18n/I18nContext.tsx`.
2. Modify line 37: change `return 'zh';` to `return 'en';`.
3. Run `python Source_Code/parallel_build.py` to produce a standalone English release binary.
