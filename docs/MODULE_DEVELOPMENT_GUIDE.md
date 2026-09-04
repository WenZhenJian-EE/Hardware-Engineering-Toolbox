# 🔌 Module Development Guide

Welcome to the **Hardware Engineering Toolbox Desktop** development guide!
This guide provides standardized workflows and engineering specifications for developers looking to implement new power topologies, analytical calculation workstations, or physical modeling algorithms.

---

## 🏗️ 1. Platform Architecture Overview

```
+------------------------------------------------------------------------+
|                          Electron 30.0 Main Process                    |
|                (Process Lifecycle & IPC Port Negotiation)              |
+-----------------------------------+------------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-----------------------------------+   +------------------------------------+
|   Frontend: React 19 + TypeScript  |   |    Backend: FastAPI + Python 3.11  |
|                                   |   |                                    |
| - Workbench Shell (App.tsx)       |   | - RESTful Endpoints (app.py)       |
| - DragDeck Layout Engine          |   | - White-Box Physics (formula.py)   |
| - Interactive Schematic Sandbox   |   | - SQLite Components (database.py)  |
| - Unified API Client (lib/api.ts) |   | - Automated Pytest Test Suite      |
+-----------------------------------+   +------------------------------------+
          |                                                   ^
          +================= HTTP JSON REST ==================+
```

- **Dynamic Port Negotiation**: The Electron main process discovers an available TCP port via `findFreePort` and passes it to the frontend via IPC. All frontend network calls route through `lib/api.ts` (`apiFetch`), strictly avoiding hardcoded URLs.
- **Analytical White-Box Physics**: All electrical formulas, Bode sweeps, and transient thermal models are implemented in pure analytical equations in `formula.py`.
- **Neon Tech Layout Engine**: Multi-column DragDeck layout with resizable cards, high-contrast neon ECharts visualizations, and KaTeX mathematical typography.

---

## 🚀 2. Adding a New Workstation (5-Step Pipeline)

Example scenario: Implementing a new workstation for a **`buck_boost_sync` (Synchronous Buck-Boost Converter)**.

### Step 1: Implement Analytical Physics & Unit Tests in `formula.py`

Add the core mathematical model in `Source_Code/backend/formula.py`:

```python
def calc_buck_boost_sync(vin: float, vout: float, iout: float, fsw_khz: float, lir_pct: float = 30.0) -> dict:
    """
    Synchronous Buck-Boost nominal steady-state calculations.
    """
    if vin <= 0 or vout <= 0 or iout <= 0 or fsw_khz <= 0:
        raise ValueError("Input physical parameters must be greater than zero.")
    
    fsw = fsw_khz * 1000.0
    duty = vout / (vin + vout)
    delta_il = iout * (lir_pct / 100.0)
    l_min_h = (vin * duty) / (fsw * delta_il)
    
    return {
        "duty": duty,
        "l_min_uh": l_min_h * 1e6,
        "delta_il_a": delta_il,
        "i_peak_a": iout / (1.0 - duty) + delta_il / 2.0
    }
```

Create unit tests in `Source_Code/backend/test_buck_boost_sync.py`:

```python
from formula import calc_buck_boost_sync

def test_buck_boost_sync_nominal():
    res = calc_buck_boost_sync(vin=12.0, vout=12.0, iout=2.0, fsw_khz=100.0)
    assert abs(res["duty"] - 0.5) < 1e-4
    assert res["l_min_uh"] > 0
```

Execute unit tests:
```bash
python -m pytest backend/test_buck_boost_sync.py
```

---

### Step 2: Register FastAPI Endpoint & Pydantic Schema in `app.py`

In `Source_Code/backend/app.py`:

```python
class BuckBoostSyncRequest(BaseModel):
    vin: float = Field(..., gt=0, description="Input Voltage Vin (V)")
    vout: float = Field(..., gt=0, description="Output Voltage Vout (V)")
    iout: float = Field(..., gt=0, description="Load Current Iout (A)")
    fsw_khz: float = Field(100.0, gt=0, description="Switching Frequency (kHz)")
    lir_pct: float = Field(30.0, gt=0, description="Inductor Ripple Ratio (%)")

@app.post("/api/calculate/buck_boost_sync")
def calculate_buck_boost_sync(req: BuckBoostSyncRequest):
    try:
        res = calc_buck_boost_sync(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lir_pct=req.lir_pct
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

### Step 3: Develop Frontend Panel in `frontend/src/components/`

Create `Source_Code/frontend/src/components/BuckBoostSyncPanel.tsx`:

```tsx
import React, { useState } from 'react';
import { apiFetch } from '../lib/api';
import { useDragDeckLayout, DragDeck, DragCard } from './ui/LayoutEngine';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Button } from './ui/Button';
import { ArrowLeft, Play, ShieldAlert } from 'lucide-react';

export default function BuckBoostSyncPanel({ onBack }: { onBack: () => void }) {
  const [vin, setVin] = useState<number>(12);
  const [vout, setVout] = useState<number>(12);
  const [iout, setIout] = useState<number>(2);
  const [fsw, setFsw] = useState<number>(100);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const {
    isDesktop, leftSpan, rightSpan, leftCards, rightCards, draggedKey, cardHeights,
    handleDragStart, handleDragEnter, handleDragEnd, handleResizeStart, handleHeightResizeStart,
    handleDropOnColumn, handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_buck_boost_sync_v1',
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 600, results: 600 }
  });

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch('/api/calculate/buck_boost_sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vin, vout, iout, fsw_khz: fsw })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#070a13] text-slate-200 p-4 gap-4 overflow-hidden">
      <div className="flex items-center gap-3 bg-[#0f172a]/80 p-3 rounded-xl border border-slate-800">
        <Button variant="outline" size="icon" onClick={onBack}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h1 className="text-sm font-bold text-white">Synchronous Buck-Boost Converter</h1>
      </div>

      {error && (
        <div className="p-3 bg-red-950/40 border border-red-500/30 text-red-200 text-xs rounded-lg flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        <DragDeck
          isDesktop={isDesktop}
          leftSpan={leftSpan}
          rightSpan={rightSpan}
          leftCards={leftCards}
          rightCards={rightCards}
          draggedKey={draggedKey}
          onDragStart={handleDragStart}
          onDragEnter={handleDragEnter}
          onDragEnd={handleDragEnd}
          onDropOnColumn={handleDropOnColumn}
          renderCard={(key) => (
            <DragCard
              cardKey={key}
              height={cardHeights[key]}
              onDragStart={(e) => handleDragStart(e, key)}
              onDragEnter={(e) => handleDragEnter(e, key)}
              onDragEnd={handleDragEnd}
              onResizeStart={handleResizeStart}
              onHeightResizeStart={handleHeightResizeStart}
              onResetLayout={handleResetLayout}
            >
              {key === 'input' && (
                <Card className="bg-[#0f172a]/95 border-slate-800 h-full flex flex-col">
                  <CardHeader className="p-4 border-b border-slate-800">
                    <CardTitle className="text-xs font-bold text-white">Electrical Specifications</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 flex-1 space-y-4">
                    <div>
                      <label className="text-[10px] text-slate-400">Input Voltage Vin (V)</label>
                      <input type="number" value={vin} onChange={e => setVin(Number(e.target.value))} className="w-full bg-[#020617] border border-slate-800 p-2 rounded text-xs text-white" />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-400">Output Voltage Vout (V)</label>
                      <input type="number" value={vout} onChange={e => setVout(Number(e.target.value))} className="w-full bg-[#020617] border border-slate-800 p-2 rounded text-xs text-white" />
                    </div>
                    <Button onClick={handleCalculate} disabled={loading} className="w-full bg-cyan-600 hover:bg-cyan-500 text-white text-xs">
                      <Play className="w-3.5 h-3.5 mr-1" />
                      {loading ? 'Calculating...' : 'Calculate'}
                    </Button>
                  </CardContent>
                </Card>
              )}

              {key === 'results' && (
                <Card className="bg-[#0f172a]/95 border-slate-800 h-full flex flex-col">
                  <CardHeader className="p-4 border-b border-slate-800">
                    <CardTitle className="text-xs font-bold text-white">Calculation Results</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 flex-1">
                    {result ? (
                      <div className="space-y-2 text-xs">
                        <div>Duty Cycle: {(result.duty * 100).toFixed(1)}%</div>
                        <div>Recommended Min Inductance: {result.l_min_uh.toFixed(2)} µH</div>
                        <div>Peak Current: {result.i_peak_a.toFixed(2)} A</div>
                      </div>
                    ) : (
                      <div className="text-slate-500 text-xs">Awaiting calculation input...</div>
                    )}
                  </CardContent>
                </Card>
              )}
            </DragCard>
          )}
        />
      </div>
    </div>
  );
}
```

---

### Step 4: Register Module in `App.tsx`

In `Source_Code/frontend/src/App.tsx`:

1. Lazy-load the component:
```tsx
const BuckBoostSyncPanel = lazy(() => import('./components/BuckBoostSyncPanel'));
```

2. Add metadata to the `TOOL_MODULES` array:
```tsx
{
  id: 'buck_boost_sync',
  name: 'Synchronous Buck-Boost',
  description: 'Steady-state CCM analysis and component sizing for synchronous buck-boost converter.',
  category: '⚡ Power Co-Design',
  isImplemented: true
}
```

3. Add routing branch in main content deck:
```tsx
{activeModule === 'buck_boost_sync' && (
  <BuckBoostSyncPanel onBack={() => setActiveModule(null)} />
)}
```

---

### Step 5: Run Automated Tests & Build Verification

1. **Backend Unit Tests**:
   ```bash
   cd Source_Code
   python -m pytest
   ```
2. **Frontend Production Compilation**:
   ```bash
   cd Source_Code/frontend
   npm run build
   ```
3. **Packaging Standalone Executable**:
   ```bash
   cd Source_Code
   python package_backend.py
   npm run dist
   ```

---

## 💡 3. Engineering Best Practices

1. **Unified API Fetch**: Always route HTTP requests through `import { apiFetch } from '../lib/api'`. Never hardcode `http://localhost:8000` to ensure automatic port negotiation works across environments.
2. **Mathematical Formulas**: Render equations with `<Latex math="..." />` using KaTeX syntax.
3. **ECharts Lifecycle Management**: Always set `notMerge={true}` and `lazyUpdate={true}` on ECharts options to prevent waveform overlap across tab changes.
4. **Layout Persistence**: Use unique storage keys for `useDragDeckLayout` (e.g. `layout_buck_boost_sync_v1`) to prevent card position collisions.
5. **Component Database Integration**: Query semiconductors or core materials using `ComponentDatabase` (`Source_Code/backend/database.py`) or the `/api/database/*` endpoints.
