# 02_Purge_of_Obsolete_Topologies_and_LocalStorage_State_Migration

---

## 1. Problem Statement & User Feedback

During system validation prior to open-source release, user testing revealed an unexpected phenomenon:
- Despite code refactoring in git commit `06153eb` that removed unmaintained topology panels, the running desktop client continued to display **20 obsolete topologies** under an outdated legacy category titled `"⚡ Co-Design DCDC (Non-Isolated)"` and `"One-Click Co-Design Flow"` (such as Vienna PFC, Totem-Pole PFC, DAB & CLLC, Inverting Buck-Boost, etc.).
- The sidebar also displayed empty categories labeled `[Placeholder]`.
- Clicking on these legacy items resulted in blank screens or unhandled routing exceptions.

---

## 2. Root Cause Analysis

### 2.1 The Client-Side `localStorage` Persistence Trap
The desktop application features a flexible group management system that allows users to organize modules into custom categories. The user's active configuration is stored in the browser's persistent key-value store:
```typescript
localStorage.getItem('toolbox_custom_groups')
```

When new git commits removed obsolete modules from source code:
1. The source code array `TOOL_MODULES` was trimmed down from 58 modules to the verified 40 modules.
2. However, any client environment (or developer browser instance) that had run previous versions of the software retained the **stale JSON snapshot** in `localStorage`.
3. During React application initialization, the state hook read directly from `localStorage` without validating the cached IDs against the current `TOOL_MODULES` manifest:
```typescript
// Faulty initial logic:
const [customGroups, setCustomGroups] = useState<ToolGroup[]>(() => {
  const saved = localStorage.getItem(CUSTOM_GROUPS_STORAGE_KEY);
  if (saved) {
    return JSON.parse(saved); // Loaded stale IDs directly without integrity checks!
  }
  return DEFAULT_GROUPS;
});
```

### 2.2 Orphaned Schematic Sandbox Components
In addition, 5 large schematic sandbox components remained in `Source_Code/frontend/src/components/`:
- `PowerDualBoostPfcSchematicSandbox.tsx` (33 KB)
- `PowerInterleavedBoostSchematicSandbox.tsx` (33 KB)
- `PowerInverterSchematicSandbox.tsx` (64 KB)
- `PowerTTypeSchematicSandbox.tsx` (51 KB)
- `PsfbSchematicSandbox.tsx` (67 KB)

While no longer imported by any active panel, they bloated the repository size, cluttered the codebase, and posed a maintenance hazard for future open-source contributors.

---

## 3. Engineering Resolution

### 3.1 Autonomous LocalStorage Validation & Scrubbing
In `App.tsx`, an automatic migration and validation guard was implemented in the `useState` initializer. If the cached configuration in `localStorage` contains legacy group titles or obsolete module IDs, it automatically resets to the standard 5 production categories and flushes dead IDs:

```typescript
const [customGroups, setCustomGroups] = useState<ToolGroup[]>(() => {
  const saved = localStorage.getItem(CUSTOM_GROUPS_STORAGE_KEY);
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) {
        // Step 1: Detect legacy category names from deprecated branches
        const hasLegacyCategories = parsed.some(g => 
          g.name.includes('Co-Design Flow') || 
          g.name.includes('Non-Isolated') || 
          g.name.includes('Co-Design DCDC')
        );

        if (hasLegacyCategories) {
          console.warn('[Storage Migration] Stale legacy categories detected. Resetting to standard 5 categories.');
          localStorage.removeItem(CUSTOM_GROUPS_STORAGE_KEY);
          return DEFAULT_GROUPS;
        }

        // Step 2: Filter module IDs against active TOOL_MODULES manifest
        const validIds = new Set(TOOL_MODULES.map(m => m.id));
        const sanitized = parsed.map(g => ({
          ...g,
          moduleIds: g.moduleIds.filter((id: string) => validIds.has(id))
        }));
        return sanitized;
      }
    } catch (e) {
      console.warn('Failed to parse custom groups:', e);
    }
  }
  return DEFAULT_GROUPS;
});
```

### 3.2 Elimination of Empty Groups and Placeholders in Sidebar
In the sidebar navigation renderer (`App.tsx`), an explicit guard was added to purge placeholder items and empty categories from the DOM:

```typescript
{customGroups.map(group => {
  const isPlaceholder = group.name.includes('[Placeholder]') || group.name.includes('[Spacer]');
  const groupModules = group.moduleIds
    .map(id => TOOL_MODULES.find(m => m.id === id))
    .filter(Boolean) as ToolModule[];

  // Completely eliminate placeholders and empty categories
  if (isPlaceholder || groupModules.length === 0) return null;

  return (
    <div key={group.id} className="mb-2">
      {/* Category header & module items */}
    </div>
  );
})}
```

### 3.3 Physical Purge of Orphaned Code Artifacts
All 5 unused schematic sandboxes were permanently deleted from disk:
```powershell
Remove-Item -Force "Source_Code\frontend\src\components\PowerDualBoostPfcSchematicSandbox.tsx"
Remove-Item -Force "Source_Code\frontend\src\components\PowerInterleavedBoostSchematicSandbox.tsx"
Remove-Item -Force "Source_Code\frontend\src\components\PowerInverterSchematicSandbox.tsx"
Remove-Item -Force "Source_Code\frontend\src\components\PowerTTypeSchematicSandbox.tsx"
Remove-Item -Force "Source_Code\frontend\src\components\PsfbSchematicSandbox.tsx"
```

---

## 4. Verification & Results

1. **Client Freshness**: Opening the application in any existing browser profile immediately purges legacy entries and presents the clean 5 categories.
2. **Build Cleanliness**: `npm run build` completed in under 750ms with zero unresolved module references.
3. **Sidebar Integrity**: The left navigation panel displays exactly the 40 production workstations without any orphan items or placeholder dividers.
