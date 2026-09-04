import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
import {
  ArrowLeft,
  ShieldAlert,
  Compass
} from 'lucide-react';

const Latex: React.FC<{ math: string; block?: boolean }> = ({ math, block = false }) => {
  const containerRef = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (containerRef.current) {
      try {
        katex.render(math, containerRef.current, {
          displayMode: block,
          throwOnError: false,
        });
      } catch (err) {
        console.error(err);
      }
    }
  }, [math, block]);
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-slate-300" : "inline-block"} />;
};

interface MaterialGrade {
  name: string;
  manufacturer: string;
  bs: number; // T
  curie_temp: number; // °C
  k: number;
  alpha: number;
  beta: number;
  pv_100k_100m: number; // kW/m3
}

const defaultMaterialGrades: MaterialGrade[] = [
  { name: 'PC95', manufacturer: 'TDK', bs: 0.51, curie_temp: 215, k: 0.012, alpha: 1.55, beta: 2.55, pv_100k_100m: 290 },
  { name: 'PC40', manufacturer: 'TDK', bs: 0.49, curie_temp: 210, k: 0.035, alpha: 1.63, beta: 2.68, pv_100k_100m: 350 },
  { name: '3C95', manufacturer: 'Ferroxcube', bs: 0.50, curie_temp: 220, k: 0.015, alpha: 1.58, beta: 2.58, pv_100k_100m: 310 },
  { name: 'N87', manufacturer: 'Epcos', bs: 0.48, curie_temp: 210, k: 0.027, alpha: 1.60, beta: 2.70, pv_100k_100m: 380 },
  { name: 'DMR44', manufacturer: 'DMEGC', bs: 0.50, curie_temp: 215, k: 0.032, alpha: 1.61, beta: 2.72, pv_100k_100m: 360 }
];

export default function MagCoreLossPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: (mod: string | null) => void }) {
  const {
    isDesktop,
    leftSpan,
    rightSpan,
    leftCards,
    rightCards,
    draggedKey,
    cardHeights,
    handleDragStart,
    handleDragEnter,
    handleDragEnd,
    handleResizeStart,
    handleHeightResizeStart,
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_magcoreloss_v3',
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 820, results: 890 }
  });
  const calcVersionRef = useRef(0);
  const [activeResultTab, setActiveResultTab] = useTabHistoryState<string>('sweep', 'activeResultTab');
  const activeResultTabRef = useRef(activeResultTab);
  useEffect(() => { activeResultTabRef.current = activeResultTab; }, [activeResultTab]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // States
  const [material, setMaterial] = useState<string>('PC40');
  const [fswKHz, setFswKHz] = useState<number>(100.0);
  const [deltaB, setDeltaB] = useState<number>(0.1);
  const [duty, setDuty] = useState<number>(0.4);
  const [veCm3, setVeCm3] = useState<number>(3.1);
  const [asCm2, setAsCm2] = useState<number>(12.5);
  const [pCopperW, setPCopperW] = useState<number>(1.0);
  const [tAmbient, setTAmbient] = useState<number>(25.0);
  const [windSpeed, setWindSpeed] = useState<number>(0.0);

  // Custom coefficients
  const [customK, setCustomK] = useState<number>(0.035);
  const [customAlpha, setCustomAlpha] = useState<number>(1.63);
  const [customBeta, setCustomBeta] = useState<number>(2.68);

  const [calcResult, setCalcResult] = useState<any>(null);
  const [scanChartOption, setScanChartOption] = useState<any>({});
  const [scanType, setScanType] = useState<'deltaB' | 'duty'>('deltaB');

  const API_BASE = '/api/calculate/mag_core_loss';

  useEffect(() => {
    try {
      const raw = localStorage.getItem('target_mag_core_loss_data');
      if (raw) {
        const data = JSON.parse(raw);
        if (data.material !== undefined) setMaterial(data.material);
        if (data.fsw_khz !== undefined) setFswKHz(data.fsw_khz);
        if (data.delta_b !== undefined) setDeltaB(data.delta_b);
        if (data.ve_cm3 !== undefined) setVeCm3(data.ve_cm3);
        if (data.as_cm2 !== undefined) setAsCm2(data.as_cm2);
        localStorage.removeItem('target_mag_core_loss_data');
      }
    } catch (e) {}
  }, []);

  const performCalculation = async () => {
    calcVersionRef.current += 1;
    const localVersion = calcVersionRef.current;
    setError(null);
    try {
      const payload: any = {
        material,
        fsw_hz: fswKHz * 1000.0,
        delta_b: deltaB,
        duty,
        ve_cm3: veCm3,
        as_cm2: asCm2,
        p_copper_w: pCopperW,
        t_ambient_c: tAmbient,
        cooling_wind_speed: windSpeed,
      };

      if (material === 'Custom') {
        payload.custom_k = customK;
        payload.custom_alpha = customAlpha;
        payload.custom_beta = customBeta;
      }

      const response = await apiFetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (localVersion !== calcVersionRef.current) return;

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to calculate core loss');
      }

      const data = await response.json();
      if (localVersion !== calcVersionRef.current) return;
      setCalcResult(data);
      await generateScanChartData(payload, localVersion);
    } catch (err: any) {
      if (localVersion === calcVersionRef.current) {
        setError(err.message);
      }
    }
  };

  const generateScanChartData = async (currentPayload: any, localVersion: number) => {
    const xVals: number[] = [];
    const yCoreLoss: number[] = [];
    const yTotalLoss: number[] = [];
    const yTemp: number[] = [];

    try {
      const response = await apiFetch(`${API_BASE}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...currentPayload, scan_type: scanType }),
      });
      if (localVersion !== calcVersionRef.current) return;

      if (response.ok) {
        const res = await response.json();
        if (localVersion !== calcVersionRef.current) return;
        
        const results = res.results || [];
        for (const item of results) {
          xVals.push(item.val);
          yCoreLoss.push(parseFloat((item.p_core_w ?? 0).toFixed(2)));
          yTotalLoss.push(parseFloat((item.p_total_w ?? 0).toFixed(2)));
          yTemp.push(parseFloat((item.t_core_c ?? 0).toFixed(1)));
        }
      }

      if (localVersion !== calcVersionRef.current) return;

      setScanChartOption({
        backgroundColor: 'transparent',
        tooltip: { 
          trigger: 'axis', 
          backgroundColor: 'rgba(15, 23, 42, 0.85)', 
          textStyle: { color: '#f1f5f9', fontSize: 10 },
          extraCssText: 'backdrop-filter: blur(8px); border: 1px solid rgba(6, 182, 212, 0.3); box-shadow: 0 0 10px rgba(6, 182, 212, 0.15);'
        },
        legend: { data: ['Core Loss (W)', 'Total Loss (W)', 'Core Steady Temperature (℃)'], textStyle: { color: '#94a3b8', fontSize: 8 }, top: 0 },
        grid: { left: '10%', right: '10%', bottom: '15%', top: '18%', containLabel: true },
        xAxis: { type: 'category', data: xVals, name: scanType === 'deltaB' ? 'Flux Swing ΔB (T)' : 'Duty Cycle D', axisLabel: { color: '#94a3b8', fontSize: 8 } },
        yAxis: [
          { type: 'value', name: 'Loss (W)', axisLabel: { color: '#38bdf8', fontSize: 8 }, splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.05)' } } },
          { type: 'value', name: 'Temperature (℃)', axisLabel: { color: '#f87171', fontSize: 8 }, splitLine: { show: false } }
        ],
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          { type: 'slider', height: 12, bottom: 5, start: 0, end: 100, textStyle: { color: '#94a3b8', fontSize: 7 } }
        ],
        series: [
          { 
            name: 'Core Loss (W)', 
            type: 'line', 
            data: yCoreLoss, 
            smooth: true, 
            lineStyle: { color: '#06b6d4', width: 3, shadowBlur: 8, shadowColor: 'rgba(6, 182, 212, 0.4)' },
            itemStyle: { color: '#06b6d4' }
          },
          { 
            name: 'Total Loss (W)', 
            type: 'line', 
            data: yTotalLoss, 
            smooth: true, 
            lineStyle: { color: '#818cf8', width: 3, shadowBlur: 8, shadowColor: 'rgba(129, 140, 248, 0.4)' },
            itemStyle: { color: '#818cf8' }
          },
          { 
            name: 'Core Steady Temperature (℃)', 
            type: 'line', 
            yAxisIndex: 1, 
            data: yTemp, 
            smooth: true, 
            lineStyle: { color: '#f43f5e', width: 3, shadowBlur: 8, shadowColor: 'rgba(244, 63, 94, 0.4)' },
            itemStyle: { color: '#f43f5e' }
          }
        ]
      });
    } catch (e) {}
  };

  useEffect(() => {
    performCalculation();
  }, [material, fswKHz, deltaB, duty, veCm3, asCm2, pCopperW, tAmbient, windSpeed, customK, customAlpha, customBeta, scanType]);

  const getLossPieOption = () => {
    if (!calcResult) return {};
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      series: [
        {
          name: 'Loss Breakdown',
          type: 'pie',
          radius: ['45%', '70%'],
          avoidLabelOverlap: false,
          label: { show: true, color: '#e2e8f0', fontSize: 9 },
          data: [
            { value: parseFloat((calcResult.p_core_w ?? 0).toFixed(3)), name: 'Core Loss P_core', itemStyle: { color: '#38bdf8' } },
            { value: pCopperW, name: 'Copper Loss P_copper', itemStyle: { color: '#818cf8' } }
          ]
        }
      ]
    };
  };

  const filteredGrades = [...defaultMaterialGrades].sort((a, b) => a.pv_100k_100m - b.pv_100k_100m);

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Top Header */}
      <div className="flex-shrink-0 flex justify-between items-center gap-4 py-2">
        <div className="flex items-center gap-3">
          <Button
            onClick={onBack}
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer shrink-0"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">High-Frequency Core Loss Assessment</h1>
            <p className="text-[10px] text-slate-400 leading-relaxed mt-0.5">
              Evaluates core losses in ferrites and powder cores under non-sinusoidal excitation using the improved Generalized Steinmetz Equation (iGSE), coupled with thermal steady-state models.
            </p>
          </div>
        </div>
        <Button
          onClick={handleResetLayout}
          variant="outline"
          size="sm"
          className="text-[10px] px-2.5 py-1 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-350 rounded-lg cursor-pointer"
        >
          Reset Layout
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2.5 text-xs text-rose-300">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>Calculation error: {error}</span>
        </div>
      )}

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 min-h-0">
        <DragDeck
          isDesktop={isDesktop}
          leftSpan={leftSpan}
          rightSpan={rightSpan}
          leftCards={leftCards}
          rightCards={rightCards}
          draggedKey={draggedKey}
          renderCard={(key) => (
            <DragCard
              cardKey={key}
              height={cardHeights[key]}
              onDragStart={(e) => handleDragStart(e, key)}
              onDragEnter={(e) => handleDragEnter(e, key)}
              onDragEnd={handleDragEnd}
              onResizeStart={handleResizeStart}
              onHeightResizeStart={handleHeightResizeStart}
            >
              {key === 'input' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Core Operating Conditions</span>
                  </div>

                  {/* Section 1: Core Material */}
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                    <span className="text-[10px] font-bold text-slate-355 block">Magnetic Material Selection</span>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[8px] text-slate-550">Material Grade</label>
                      <select
                        value={material}
                        onChange={(e) => setMaterial(e.target.value)}
                        className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-300 outline-none w-full"
                      >
                        <option value="PC40">PC40 (MnZn ferrite - TDK)</option>
                        <option value="PC95">PC95 (MnZn low loss, wide temp - TDK)</option>
                        <option value="DMR44">DMR44 (MnZn ferrite - DMEGC)</option>
                        <option value="Sendust_60u">Sendust 60u (Kool Mμ / Sendust)</option>
                        <option value="FeSi_60u">Fe-Si 60u (Silicon Iron Powder)</option>
                        <option value="Custom">Custom Parameters...</option>
                      </select>
                    </div>

                    {material === 'Custom' && (
                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/60">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">K Fitting Constant (W/cm³)</label>
                          <input type="number" step="0.001" value={customK} onChange={(e) => setCustomK(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-xs text-slate-200 outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">α Frequency Exponent</label>
                          <input type="number" step="0.01" value={customAlpha} onChange={(e) => setCustomAlpha(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-xs text-slate-200 outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">β Flux Exponent</label>
                          <input type="number" step="0.01" value={customBeta} onChange={(e) => setCustomBeta(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-xs text-slate-200 outline-none" />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Section 2: Excitation */}
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                    <span className="text-[10px] font-bold text-slate-355 block">Excitation Parameters</span>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[8px] text-slate-550">Switching Frequency fsw (kHz)</label>
                      <input type="number" value={fswKHz} onChange={(e) => setFswKHz(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Flux Swing ΔB (T)</label>
                        <input type="number" step="0.01" value={deltaB} onChange={(e) => setDeltaB(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Excitation Duty Cycle d (0~1)</label>
                        <input type="number" step="0.05" value={duty} onChange={(e) => setDuty(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                    </div>
                  </div>

                  {/* Section 3: Core Geometry */}
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                    <span className="text-[10px] font-bold text-slate-355 block">Core Geometry & Loss</span>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Effective Volume Ve (cm³)</label>
                        <input type="number" value={veCm3} onChange={(e) => setVeCm3(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Surface Area As (cm²)</label>
                        <input type="number" value={asCm2} onChange={(e) => setAsCm2(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[8px] text-slate-550">High-Frequency Winding Loss Pcu (W)</label>
                      <input type="number" value={pCopperW} onChange={(e) => setPCopperW(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                  </div>

                  {/* Section 4: Heat Dissipation */}
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                    <span className="text-[10px] font-bold text-slate-355 block">Cooling & Convection</span>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Ambient Temp Ta (℃)</label>
                        <input type="number" value={tAmbient} onChange={(e) => setTAmbient(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Cooling Air Speed v (m/s)</label>
                        <input type="number" step="0.5" value={windSpeed} onChange={(e) => setWindSpeed(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-6">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white">Core Loss & Steinmetz Results</span>
                  </div>

                  {/* Grid of 6 Key Values */}
                  {calcResult && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3.5">
                      <div className="p-3.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Core Loss P_core (Iron)</span>
                        <div className="text-xl font-bold text-cyan-400 font-mono">
                          {(calcResult.p_core_w ?? 0.0).toFixed(3)} <span className="text-[9px] text-slate-500 font-normal">W</span>
                        </div>
                        <span className="text-[8px] text-slate-500">iGSE non-sinusoidal integral loss</span>
                      </div>
                      <div className="p-3.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Winding Copper Loss Pcu</span>
                        <div className="text-xl font-bold text-slate-200 font-mono">
                          {(pCopperW ?? 0.0).toFixed(2)} <span className="text-[9px] text-slate-500 font-normal">W</span>
                        </div>
                        <span className="text-[8px] text-slate-500">High-frequency winding self-heating</span>
                      </div>
                      <div className="p-3.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Total Heat Loss P_total</span>
                        <div className="text-xl font-bold text-emerald-400 font-mono">
                          {(calcResult.p_total_w ?? 0.0).toFixed(3)} <span className="text-[9px] text-slate-500 font-normal">W</span>
                        </div>
                        <span className="text-[8px] text-slate-500">Overall component heat dissipation</span>
                      </div>
                      <div className="p-3.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Predicted Temp Rise ΔT</span>
                        <div className="text-xl font-bold text-rose-450 font-mono">
                          {(calcResult.delta_t ?? 0.0).toFixed(1)} <span className="text-[9px] text-slate-500 font-normal">K</span>
                        </div>
                        <span className="text-[8px] text-slate-500">Thermal resistance & convection rise</span>
                      </div>
                      <div className={`p-3.5 rounded-lg border bg-slate-900/30 flex flex-col gap-0.5 ${
                        (calcResult.t_core_c ?? 0.0) > 100 ? 'border-yellow-500/40 bg-yellow-950/10' : 'border-slate-850'
                      }`}>
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Core Steady Temperature</span>
                        <div className="text-xl font-bold text-purple-400 font-mono">
                          {(calcResult.t_core_c ?? 0.0).toFixed(1)} <span className="text-[9px] text-slate-500 font-normal">℃</span>
                        </div>
                        <span className="text-[8px] text-slate-500">Total predicted core temperature</span>
                      </div>
                      <div className="p-3.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Core Loss Density Pv</span>
                        <div className="text-xl font-bold text-slate-200 font-mono">
                          {((calcResult.pv_w_m3 ?? 0.0) / 1000.0).toFixed(1)} <span className="text-[9px] text-slate-500 font-normal">kW/m³</span>
                        </div>
                        <span className="text-[8px] text-slate-500">Volumetric core loss density</span>
                      </div>
                    </div>
                  )}

                  {calcResult?.drc_warnings && calcResult.drc_warnings.length > 0 && (
                    <div className="space-y-1.5">
                      {calcResult.drc_warnings.map((warn: string, idx: number) => (
                        <div key={idx} className="p-2.5 bg-red-950/40 border border-red-800/80 rounded-lg text-xs text-red-300 font-bold">
                          ⚠️ {warn}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* B-H loop SVG diagram */}
                  <Card className="bg-[#0b0f19]/30 border-slate-800/80">
                    <CardHeader className="py-2.5 border-b border-slate-800/80">
                      <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                        <Compass className="w-3.5 h-3.5 text-cyan-400" />
                        Core Hysteresis B-H Loop Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 flex justify-center items-center bg-slate-950/10">
                      {(() => {
                        const db_visual = Math.min(deltaB ?? 0.1, 0.42);
                        const h_b = 80 * db_visual * 2.0;
                        const pCore = calcResult?.p_core_w ?? 0.05;
                        const h_c = Math.min(5 + pCore * 6, 45);
                        return (
                          <svg viewBox="0 0 720 180" className="w-full max-w-2xl h-auto text-slate-400 bg-transparent">
                            <line x1="360" y1="10" x2="360" y2="170" stroke="#475569" strokeWidth="1.2" strokeDasharray="3" />
                            <line x1="40" y1="90" x2="680" y2="90" stroke="#475569" strokeWidth="1.2" strokeDasharray="3" />
                            <path 
                              d={`M ${360 - 150} 90 C ${360 - 100} ${90 - h_b + h_c}, ${360 - 50} ${90 - h_b}, 360 ${90 - h_b} C ${360 + 50} ${90 - h_b}, ${360 + 100} ${90 - h_b - h_c}, ${360 + 150} 90 C ${360 + 100} ${90 + h_b - h_c}, ${360 + 50} ${90 + h_b}, 360 ${90 + h_b} C ${360 - 50} ${90 + h_b}, ${360 - 100} ${90 + h_b + h_c}, ${360 - 150} 90`} 
                              fill="rgba(6, 182, 212, 0.08)" 
                              stroke="#06b6d4" 
                              strokeWidth="2" 
                            />
                            <text x="375" y="25" fill="#94a3b8" fontSize="9" fontWeight="bold">Flux Density B (T)</text>
                            <text x="610" y="80" fill="#94a3b8" fontSize="9" fontWeight="bold">Field Strength H (A/m)</text>
                            <circle cx={360} cy={90 - h_b} r="3" fill="#ef4444" />
                            <text x={375} y={95 - h_b} fill="#ef4444" fontSize="9" fontWeight="bold">ΔB = {(deltaB ?? 0.1).toFixed(2)} T</text>
                            <text x="60" y="35" fill="#64748b" fontSize="8">Ferrite iGSE Integration Area</text>
                          </svg>
                        );
                      })()}
                    </CardContent>
                  </Card>

                  {/* Simulation charts */}
                  <Card className="border-slate-800 bg-[#0b0f19]/30">
                    <CardHeader className="pb-3 border-b border-slate-800 flex flex-row items-center justify-between p-4">
                      <CardTitle className="text-xs font-bold text-slate-350">
                        Parameter Sweep & Loss Breakdown
                      </CardTitle>
                      <Tabs value={activeResultTab} onValueChange={(val: any) => setActiveResultTab(val)} className="w-auto">
                        <TabsList className="bg-[#020617] border border-slate-800 h-7 p-0.5">
                          <TabsTrigger value="sweep" className="text-[9px] h-6 px-2.5">Parametric Sweep</TabsTrigger>
                          <TabsTrigger value="pie" className="text-[9px] h-6 px-2.5">Loss Breakdown Pie</TabsTrigger>
                        </TabsList>
                      </Tabs>
                    </CardHeader>
                    <CardContent className="p-4 bg-slate-950/10">
                      <div className="w-full h-[250px]">
                        {activeResultTab === 'sweep' ? (
                          <div className="flex flex-col gap-2 w-full h-full">
                            <div className="flex justify-end gap-2 mb-1">
                              <Button 
                                size="sm" 
                                variant={scanType === 'deltaB' ? 'default' : 'outline'} 
                                onClick={() => setScanType('deltaB')}
                                className="text-[8px] h-5 px-2 cursor-pointer"
                              >
                                Sweep Flux ΔB
                              </Button>
                              <Button 
                                size="sm" 
                                variant={scanType === 'duty' ? 'default' : 'outline'} 
                                onClick={() => setScanType('duty')}
                                className="text-[8px] h-5 px-2 cursor-pointer"
                              >
                                Sweep Duty D
                              </Button>
                            </div>
                            <div className="flex-1 w-full h-full">
                              <ReactECharts option={scanChartOption} notMerge={true} style={{ height: '100%', width: '100%' }} />
                            </div>
                          </div>
                        ) : (
                          <ReactECharts option={getLossPieOption()} notMerge={true} style={{ height: '100%', width: '100%' }} />
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Ferrite Recommended BOM */}
                  <Card className="bg-[#0b0f19]/30 border-slate-800/80 shadow-lg text-slate-200">
                    <CardHeader className="p-4 pb-2">
                      <CardTitle className="text-xs font-bold text-white">
                        Recommended Low-Loss Ferrite Materials (Ascending Loss Density Pv)
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0 overflow-x-auto">
                      <table className="w-full text-left text-[10px] border-collapse text-slate-350">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40 font-mono">
                            <th className="px-4 py-2">Material Grade</th>
                            <th className="px-3 py-2">Manufacturer</th>
                            <th className="px-3 py-2">Saturation Flux Bs</th>
                            <th className="px-3 py-2">Curie Temp Tc</th>
                            <th className="px-3 py-2">Steinmetz k Factor</th>
                            <th className="px-4 py-2">Loss Density Pv (100k/100mT)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredGrades.map((item, idx) => (
                            <tr 
                              key={idx} 
                              className={`border-b border-slate-900 hover:bg-slate-800/10 transition-colors ${idx === 0 ? 'bg-cyan-500/[0.03] text-cyan-200 font-semibold' : 'text-slate-300'}`}
                            >
                              <td className="px-4 py-2 flex items-center gap-1">
                                {item.name} 
                                {idx === 0 && <span className="text-[8px] bg-cyan-500/10 text-cyan-400 px-1 py-0.2 rounded border border-cyan-500/20 font-bold uppercase tracking-wider">Preferred</span>}
                              </td>
                              <td className="px-3 py-2 text-slate-500">{item.manufacturer}</td>
                              <td className="px-3 py-2">{item.bs} T</td>
                              <td className="px-3 py-2">{item.curie_temp} °C</td>
                              <td className="px-3 py-2 font-mono">{(item.k ?? 0).toFixed(3)}</td>
                              <td className="px-4 py-2 font-mono">{(item.pv_100k_100m ?? 0)} kW/m³</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </CardContent>
                  </Card>
                </div>
              )}
            </DragCard>
          )}
          onDropOnColumn={handleDropOnColumn}
        />
      </div>
    </div>
  );
}