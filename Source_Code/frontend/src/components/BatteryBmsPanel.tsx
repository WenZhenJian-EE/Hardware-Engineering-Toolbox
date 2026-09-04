import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import {
  ArrowLeft,
  CheckCircle2,
  Compass,
  FileSpreadsheet,
  ShieldAlert,
  BookOpen
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
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-xs text-slate-355" : "inline-block text-xs"} />;
};

const E96_VALUES = [
  1.0, 1.02, 1.05, 1.07, 1.1, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.3, 1.33, 1.37, 1.4, 1.43,
  1.47, 1.5, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.0, 2.05, 2.1,
  2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.8, 2.87, 2.94, 3.01, 3.09,
  3.16, 3.24, 3.32, 3.4, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53,
  4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.9, 6.04, 6.19, 6.34, 6.49, 6.65,
  6.81, 6.98, 7.15, 7.32, 7.5, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
];

function getNearestE96Res(targetOhm: number): { value: number; errorPct: number } {
  if (targetOhm <= 0) return { value: 1.0, errorPct: 0 };
  
  const exponent = Math.floor(Math.log10(targetOhm));
  const baseValue = targetOhm / Math.pow(10, exponent);
  
  let minDiff = Infinity;
  let bestBase = E96_VALUES[0];
  
  for (const v of E96_VALUES) {
    const diff = Math.abs(v - baseValue);
    if (diff < minDiff) {
      minDiff = diff;
      bestBase = v;
    }
  }
  
  const finalValue = bestBase * Math.pow(10, exponent);
  const errorPct = ((finalValue - targetOhm) / targetOhm) * 100;
  return { value: finalValue, errorPct };
}

export default function BatteryBmsPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useState<'pack' | 'load' | 'balance'>(() => {
    const saved = localStorage.getItem('battery_active_tab');
    return (saved as any) || 'pack';
  });
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);

  const getTabConfig = (tab: 'pack' | 'load' | 'balance') => {
    if (tab === 'pack') {
      return {
        defaultCards: ['input', 'results', 'ocv_chart', 'drc'],
        defaultColumns: { input: 'left', drc: 'left', results: 'right', ocv_chart: 'right' } as Record<string, 'left' | 'right'>,
        defaultSpans: { input: 4, drc: 4, results: 8, ocv_chart: 8 },
        defaultHeights: { input: 480, drc: 180, results: 240, ocv_chart: 300 }
      };
    } else if (tab === 'load') {
      return {
        defaultCards: ['input', 'results', 'temp_chart', 'drc'],
        defaultColumns: { input: 'left', drc: 'left', results: 'right', temp_chart: 'right' } as Record<string, 'left' | 'right'>,
        defaultSpans: { input: 4, drc: 4, results: 8, temp_chart: 8 },
        defaultHeights: { input: 480, drc: 180, results: 240, temp_chart: 300 }
      };
    } else {
      return {
        defaultCards: ['input', 'results', 'schematic', 'bom', 'drc'],
        defaultColumns: { input: 'left', drc: 'left', results: 'right', schematic: 'right', bom: 'right' } as Record<string, 'left' | 'right'>,
        defaultSpans: { input: 4, drc: 4, results: 8, schematic: 8, bom: 8 },
        defaultHeights: { input: 480, drc: 180, results: 240, schematic: 200, bom: 200 }
      };
    }
  };

  const tabConfig = getTabConfig(activeTab);

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
    handleHeightResizeStartTop,
    handleResetCardHeight,
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: `layout_batterybms_v4_${activeTab}`,
    activeTab: activeTab,
    defaultCards: tabConfig.defaultCards,
    defaultColumns: tabConfig.defaultColumns,
    defaultSpans: tabConfig.defaultSpans,
    defaultHeights: tabConfig.defaultHeights
  });

  const [error, setError] = useState<string | null>(null);

  // Tab 1: Pack Config State
  const [cellType, setCellType] = useState<string>('nmc');
  const [cellVNom, setCellVNom] = useState<number>(3.7);
  const [cellVMin, setCellVMin] = useState<number>(2.8);
  const [cellVMax, setCellVMax] = useState<number>(4.2);
  const [cellCap, setCellCap] = useState<number>(2.5);
  const [cellIr, setCellIr] = useState<number>(20.0); // mOhm
  const [packMode, setPackMode] = useState<'sp' | 'target'>('sp');
  const [sVal, setSVal] = useState<number>(10);
  const [pVal, setPVal] = useState<number>(4);
  const [targetV, setTargetV] = useState<number>(36.0);
  const [targetWh, setTargetWh] = useState<number>(360.0);

  // Tab 2: Load Analysis State
  const [loadMode, setLoadMode] = useState<'current' | 'power'>('current');
  const [loadCurr, setLoadCurr] = useState<number>(5.0);
  const [loadPower, setLoadPower] = useState<number>(200.0);
  const [rBusbar, setRBusbar] = useState<number>(10.0); // mOhm

  // Tab 3: Balance State
  const [balQDiff, setBalQDiff] = useState<number>(3.0); // %
  const [balTime, setBalTime] = useState<number>(8.0); // hours
  const [balVCell, setBalVCell] = useState<number>(4.2); // V

  // Results
  const [packRes, setPackRes] = useState<any>(null);
  const [loadRes, setLoadRes] = useState<any>(null);
  const [balRes, setBalRes] = useState<any>(null);

  const handleCellTypeChange = (type: string) => {
    setCellType(type);
    if (type === 'nmc') {
      setCellVNom(3.7);
      setCellVMin(2.8);
      setCellVMax(4.2);
    } else if (type === 'lfp') {
      setCellVNom(3.2);
      setCellVMin(2.5);
      setCellVMax(3.65);
    } else if (type === 'lead') {
      setCellVNom(12.0);
      setCellVMin(10.5);
      setCellVMax(14.4);
    } else if (type === 'lto') {
      setCellVNom(2.3);
      setCellVMin(1.5);
      setCellVMax(2.8);
    }
  };

  const executeCalculations = async () => {
    setError(null);
    let currentPackRes = packRes;
    
    try {
      const res = await apiFetch('/api/calculate/battery_pack/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cell_v_nom: cellVNom,
          cell_v_min: cellVMin,
          cell_v_max: cellVMax,
          cell_cap: cellCap,
          cell_ir_mohm: cellIr,
          mode: packMode,
          s: sVal,
          p: pVal,
          target_v: targetV,
          target_wh: targetWh
        })
      });
      if (!res.ok) throw new Error('Battery pack series-parallel configuration calculation failed');
      const data = await res.json();
      setPackRes(data);
      currentPackRes = data;
    } catch (e: any) {
      setError(e.message);
      return;
    }

    if (activeTab === 'load') {
      if (!currentPackRes) return;
      try {
        const res = await apiFetch('/api/calculate/battery_pack/load', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            v_nom: currentPackRes.pack_v_nom,
            v_min: currentPackRes.pack_v_min,
            ir_ohm: currentPackRes.pack_ir_mohm / 1000.0,
            ah: currentPackRes.pack_ah,
            r_busbar_mohm: rBusbar,
            mode: loadMode,
            load_curr: loadCurr,
            load_power: loadPower
          })
        });
        if (!res.ok) throw new Error('Load voltage drop and thermal estimation failed');
        const data = await res.json();
        setLoadRes(data);
      } catch (e: any) {
        setError(e.message);
      }
    } else if (activeTab === 'balance') {
      try {
        const res = await apiFetch('/api/calculate/battery_pack/balance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            cap: cellCap,
            q_diff_pct: balQDiff,
            time_h: balTime,
            v_cell: balVCell
          })
        });
        if (!res.ok) throw new Error('BMS balancing calculation failed; balancing time window cannot be zero.');
        const data = await res.json();
        setBalRes(data);
      } catch (e: any) {
        setError(e.message);
      }
    }
  };

  useEffect(() => {
    executeCalculations();
  }, [
    activeTab, cellVNom, cellVMin, cellVMax, cellCap, cellIr, packMode, sVal, pVal, targetV, targetWh,
    loadMode, loadCurr, loadPower, rBusbar,
    balQDiff, balTime, balVCell
  ]);

  const handleTabChange = (val: 'pack' | 'load' | 'balance') => {
    setActiveTab(val);
    localStorage.setItem('battery_active_tab', val);
  };

  const getSohChartOption = () => {
    if (!packRes) return {};
    const seriesData = [];
    for (let soc = 0; soc <= 100; soc += 5) {
      const soc_factor = soc / 100.0;
      let voltage = packRes.pack_v_min + (packRes.pack_v_max - packRes.pack_v_min) * (0.1 + 0.9 * soc_factor);
      seriesData.push([soc, parseFloat(voltage.toFixed(2))]);
    }
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', formatter: 'SOC: {b}%<br/>Open Circuit Voltage: {c} V' },
      grid: { top: '15%', left: '12%', right: '10%', bottom: '20%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'SOC (%)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
      },
      yAxis: {
        type: 'value',
        name: 'Pack Voltage (V)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
      },
      series: [
        {
          name: 'Discharge OCV',
          type: 'line',
          data: seriesData,
          smooth: true,
          lineStyle: { color: '#22c55e', width: 2.5 }
        }
      ]
    };
  };

  const getTempChartOption = () => {
    if (!loadRes) return {};
    const points: [number, number][] = [];
    const numPoints = 100;
    
    const t_amb = 25.0;
    const r_th = 0.25; // Thermal resistance in K/W
    const dt_max = loadRes.p_loss_w * r_th;
    
    for (let i = 0; i <= numPoints; i++) {
      const t = (i / numPoints) * 7200; // 2 hours
      const temp = t_amb + dt_max * (1 - Math.exp(-t / 1800)); // Time constant 30min
      points.push([parseFloat((t / 60).toFixed(1)), parseFloat(temp.toFixed(1))]);
    }
    
    return {
      backgroundColor: 'transparent',
      title: { text: 'Pack Self-Heating Temperature Rise Profile', textStyle: { color: '#e2e8f0', fontSize: 11 }, left: 'center' },
      tooltip: { trigger: 'axis', formatter: 'Time: {b} min<br/>Estimated Temp: {c} °C' },
      grid: { top: '18%', left: '12%', right: '10%', bottom: '20%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Time (min)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      yAxis: {
        type: 'value',
        name: 'Estimated Temp (°C)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      series: [
        {
          name: 'Thermal Rise Trajectory',
          type: 'line',
          data: points,
          smooth: true,
          lineStyle: { color: '#f43f5e', width: 2.5 }
        }
      ]
    };
  };

  const getDrcWarningsLocal = () => {
    const warnings: string[] = [];
    if (activeTab === 'pack') {
      if (cellVNom < 1.0 || cellVNom > 15.0) {
        warnings.push("Cell nominal voltage deviates from typical lithium cell values (3.2V~3.7V). Please verify inputs.");
      }
      if (cellCap <= 0.1 || cellCap > 500) {
        warnings.push("Cell capacity abnormal: Please check capacity in Ah (e.g. 2.5Ah to 200Ah), avoiding mA units.");
      }
    } else if (activeTab === 'load' && loadRes) {
      if (loadRes.drc_warnings) {
        warnings.push(...loadRes.drc_warnings);
      }
      const t_amb = 25.0;
      const r_th = 0.25;
      const dt_max = loadRes.p_loss_w * r_th;
      const t_end = t_amb + dt_max * (1 - Math.exp(-7200 / 1800));
      if (t_end > 60.0) {
        warnings.push(`Continuous 2h discharge temperature reaches ${t_end.toFixed(1)}°C (exceeding 60°C safety limit)! Forced cooling or load reduction required.`);
      } else if (t_end > 45.0) {
        warnings.push(`Self-heating elevated: Continuous 2h discharge reaches approx ${t_end.toFixed(1)}°C. Ensure sufficient convection airflow.`);
      }
    } else if (activeTab === 'balance' && balRes) {
      if (balRes.drc_warnings) {
        warnings.push(...balRes.drc_warnings);
      }
      if (balRes.i_bal_ma > 150) {
        warnings.push(`Balancing discharge current reaches ${balRes.i_bal_ma.toFixed(1)} mA. High shunt heating; consider keeping bypass current under 100 mA.`);
      }
      if (balTime > 48.0) {
        warnings.push("Extended balancing period: Balancing requires >48h due to large capacity delta or narrow time window.");
      }
    }
    return warnings;
  };

  const localWarnings = getDrcWarningsLocal();
  const matchedRes = activeTab === 'balance' && balRes ? getNearestE96Res(balRes.r_bleed_ohm) : null;

  return (
    <div className="w-full h-full flex flex-col text-slate-100 bg-slate-950 p-3 overflow-hidden">
      <div className="flex justify-between items-center gap-4 bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex-shrink-0 mb-3">
        <div className="flex items-center gap-3">
          <Button
            onClick={onBack}
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Battery Pack & BMS Sizing Tool
            </h1>
            <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">
              Supports series-parallel cell configuration, continuous discharge dynamic drop & thermal loss, passive balancing current and bleeder resistor sizing.
            </p>
          </div>
        </div>
        <Button
          onClick={handleResetLayout}
          variant="outline"
          size="sm"
          className="text-[10px] px-2.5 py-1 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-lg cursor-pointer"
        >
          Reset Layout
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2.5 text-xs text-rose-300 flex-shrink-0 mb-3 animate-fade-in">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>Calculation Error: {error}</span>
        </div>
      )}

      <div className="flex gap-2 bg-slate-900/60 p-1 rounded-xl border border-slate-800 flex-shrink-0 mb-3">
        {([
          { id: 'pack', label: '1. Series-Parallel Configuration' },
          { id: 'load', label: '2. Load Drop & Heating' },
          { id: 'balance', label: '3. BMS Passive Balancing' }
        ] as const).map(tab => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`px-3 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
              activeTab === tab.id
                ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pr-1 pb-3">
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
              onHeightResizeStartTop={handleHeightResizeStartTop}
              onResetHeight={() => handleResetCardHeight(key)}
            >
              {key === 'input' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Input Operating Specifications</span>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/10 space-y-2">
                    <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1.5 mb-2">Step 1: Cell Chemistry, Resistance & Capacity</span>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex flex-col gap-1 col-span-2">
                        <label className="text-[9px] text-slate-400">Cell Chemistry</label>
                        <select value={cellType} onChange={e => handleCellTypeChange(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-xs text-slate-300 outline-none cursor-pointer">
                          <option value="nmc">NMC Lithium-Ion - 3.7V</option>
                          <option value="lfp">LiFePO4 (LFP) - 3.2V</option>
                          <option value="lead">Lead-Acid - 12.0V</option>
                          <option value="lto">Lithium Titanate (LTO) - 2.3V</option>
                        </select>
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] text-slate-400">Nominal Capacity (Ah)</label>
                        <input type="number" value={cellCap} onChange={e => setCellCap(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] text-slate-400">Internal Resistance (mΩ)</label>
                        <input type="number" value={cellIr} onChange={e => setCellIr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                      </div>
                    </div>
                  </div>

                  {activeTab === 'pack' && (
                    <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-850 pb-1.5">
                        <span className="text-[10px] font-bold text-slate-300">Step 2: Configuration Mode</span>
                        <select value={packMode} onChange={e => setPackMode(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[9px] text-slate-300 outline-none cursor-pointer">
                          <option value="sp">Specify S / P Counts</option>
                          <option value="target">Solve from Target Voltage & Energy</option>
                        </select>
                      </div>

                      {packMode === 'sp' ? (
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Series Count (S)</label>
                            <input type="number" value={sVal} onChange={e => setSVal(parseInt(e.target.value) || 1)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Parallel Count (P)</label>
                            <input type="number" value={pVal} onChange={e => setPVal(parseInt(e.target.value) || 1)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-[8px] text-slate-500 block">Standard ESS Presets:</span>
                            <button
                              onClick={() => { handleCellTypeChange('lfp'); setTargetV(51.2); setPackMode('sp'); setSVal(16); }}
                              className="px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded text-[9px] cursor-pointer"
                            >
                              48V 16S LFP
                            </button>
                            <button
                              onClick={() => { handleCellTypeChange('lfp'); setTargetV(64.0); setPackMode('sp'); setSVal(20); }}
                              className="px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded text-[9px] cursor-pointer"
                            >
                              60V 20S LFP
                            </button>
                            <button
                              onClick={() => { handleCellTypeChange('nmc'); setTargetV(74.0); setPackMode('sp'); setSVal(20); }}
                              className="px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded text-[9px] cursor-pointer"
                            >
                              72V 20S NMC
                            </button>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Target Voltage (V)</label>
                              <input type="number" value={targetV} onChange={e => setTargetV(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Target Energy (Wh)</label>
                              <input type="number" value={targetWh} onChange={e => setTargetWh(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'load' && (
                    <>
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-850 pb-1.5">
                          <span className="text-[10px] font-bold text-slate-300">Step 2: Pack Discharge Load Mode</span>
                          <select value={loadMode} onChange={e => setLoadMode(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[9px] text-slate-300 outline-none cursor-pointer">
                            <option value="current">Constant Current (CC)</option>
                            <option value="power">Constant Power (CP)</option>
                          </select>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Discharge Current (A)</label>
                            <input type="number" value={loadCurr} onChange={e => setLoadCurr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" disabled={loadMode === 'power'} />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Discharge Power (W)</label>
                            <input type="number" value={loadPower} onChange={e => setLoadPower(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" disabled={loadMode === 'current'} />
                          </div>
                        </div>
                      </div>

                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/10 space-y-2">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1.5 mb-1">Step 3: Busbar Parasitic Resistance</span>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-400">Total Loop Busbar Resistance (mΩ)</label>
                          <input type="number" value={rBusbar} onChange={e => setRBusbar(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                        </div>
                      </div>
                    </>
                  )}

                  {activeTab === 'balance' && (
                    <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
                      <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1.5 mb-1">Step 2: Imbalance Delta & Balancing Window</span>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-400">Capacity Imbalance Q_diff (%)</label>
                          <input type="number" value={balQDiff} onChange={e => setBalQDiff(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-400">Target Balancing Window (h)</label>
                          <input type="number" value={balTime} onChange={e => setBalTime(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                        </div>
                        <div className="flex flex-col gap-1 col-span-2">
                          <label className="text-[9px] text-slate-400">Cell Open Circuit Voltage at Balancing (V)</label>
                          <input type="number" value={balVCell} onChange={e => setBalVCell(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'theory' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-3">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
                    <BookOpen className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold text-white">BMS Physical Equations</span>
                  </div>
                  <div className="text-[11px] text-slate-400 space-y-2 leading-relaxed">
                    {activeTab === 'pack' && (
                      <>
                        <p>Pack Nominal Voltage & Capacity Equations:</p>
                        <Latex math={"V_{nom} = S \\cdot V_{cell,nom}"} block />
                        <Latex math={"C_{ah} = P \\cdot C_{cell,ah} ,\\quad E_{wh} = V_{nom} \\cdot C_{ah}"} block />
                      </>
                    )}
                    {activeTab === 'load' && (
                      <>
                        <p>Discharge Loop Total Impedance & Copper Drop:</p>
                        <Latex math={"R_{total} = R_{pack,ir} + R_{busbar}"} block />
                        <Latex math={"V_{drop} = I \\cdot R_{total} ,\\quad P_{loss} = I^2 \\cdot R_{total}"} block />
                      </>
                    )}
                    {activeTab === 'balance' && (
                      <>
                        <p>Passive Bleed Charge & Resistor Matching:</p>
                        <Latex math={"Q_{bleed} = C_{cell,ah} \\cdot Q_{diff}\\%"} block />
                        <Latex math={"I_{bal} = \\frac{Q_{bleed}}{Time_{hour}} ,\\quad R_{bal} = \\frac{V_{cell}}{I_{bal}}"} block />
                      </>
                    )}
                  </div>
                </div>
              )}

              {key === 'drc' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-3">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
                    <ShieldAlert className="w-4 h-4 text-amber-500" />
                    <span className="text-xs font-bold text-white">DRC Safety Checks</span>
                  </div>

                  {localWarnings.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-[70%] text-slate-500 text-xs">
                      <CheckCircle2 className="w-6 h-6 text-emerald-500 mb-1" />
                      <span>All parameters within safe operating limits</span>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {localWarnings.map((w, idx) => (
                        <div key={idx} className="p-2.5 bg-yellow-950/20 border border-yellow-500/20 rounded-lg flex gap-2 text-[10px] text-yellow-250 leading-normal">
                          <ShieldAlert className="w-3.5 h-3.5 text-yellow-400 shrink-0 mt-0.5" />
                          <span>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
                    <span className="text-xs font-bold text-white">Pack System Results</span>
                  </div>

                  {activeTab === 'pack' && packRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200">
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Nominal Voltage V_nom</span>
                        <span className="text-sm font-bold text-cyan-400 font-mono">{packRes.pack_v_nom.toFixed(2)} V</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Total Energy Wh</span>
                        <span className="text-sm font-bold text-slate-100 font-mono">{packRes.pack_wh.toFixed(1)} Wh</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Total Capacity Ah</span>
                        <span className="text-sm font-bold text-slate-100 font-mono">{packRes.pack_ah.toFixed(1)} Ah</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Pack Internal Resistance</span>
                        <span className="text-sm font-bold text-emerald-400 font-mono">{packRes.pack_ir_mohm.toFixed(2)} mΩ</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Actual Series (S)</span>
                        <span className="text-sm font-bold text-purple-400 font-mono">{packRes.s} S</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Actual Parallel (P)</span>
                        <span className="text-sm font-bold text-rose-400 font-mono">{packRes.p} P</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'load' && loadRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Discharge Current</span>
                        <span className="text-sm font-bold text-cyan-400 font-mono">{loadRes.current_a.toFixed(2)} A</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Discharge C-Rate</span>
                        <span className="text-sm font-bold text-slate-350 font-mono">{loadRes.c_rate.toFixed(2)} C</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Loop Parasitic Drop V_drop</span>
                        <span className="text-sm font-bold text-slate-300 font-mono">{loadRes.v_drop_v.toFixed(3)} V</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Terminal Voltage</span>
                        <span className="text-sm font-bold text-emerald-400 font-mono">{loadRes.v_terminal_v.toFixed(2)} V</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[9px] text-slate-400">Dissipation Power Ploss</span>
                        <span className="text-sm font-bold text-purple-400 font-mono">{loadRes.p_loss_w.toFixed(2)} W</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'balance' && balRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="p-2 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[8px] text-slate-400">Max Balancing Current I_bal</span>
                        <span className="text-xs font-bold text-cyan-400 font-mono">{balRes.i_bal_ma.toFixed(1)} mA</span>
                      </div>
                      <div className="p-2 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[8px] text-slate-400">Bleeder Resistance R_bal</span>
                        <span className="text-xs font-bold text-slate-300 font-mono">{balRes.r_bleed_ohm.toFixed(2)} Ω</span>
                      </div>
                      <div className="p-2 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[8px] text-slate-400">Resistor Dissipation Ploss</span>
                        <span className="text-xs font-bold text-rose-350 font-mono">{balRes.p_res_w.toFixed(3)} W</span>
                      </div>
                      <div className="p-2 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[8px] text-slate-400">Imbalance Capacity</span>
                        <span className="text-xs font-bold text-slate-300 font-mono">{(cellCap * balQDiff / 100.0).toFixed(3)} Ah</span>
                      </div>
                      <div className="p-2 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[8px] text-slate-400">Delta Charge Q</span>
                        <span className="text-xs font-bold text-purple-400 font-mono">{(cellCap * balQDiff * 36.0).toFixed(0)} C</span>
                      </div>
                      <div className="p-2 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col">
                        <span className="text-[8px] text-slate-400">Balancing Time Window</span>
                        <span className="text-xs font-bold text-slate-200 font-mono">{balTime.toFixed(1)} h</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'ocv_chart' && activeTab === 'pack' && (
                <div className="h-full overflow-hidden p-4 flex flex-col justify-between">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2 flex-shrink-0">
                    <span className="text-xs font-bold text-white">Pack Open Circuit Voltage vs SOC (OCV)</span>
                  </div>
                  <div className="flex-1 min-h-0 mt-3">
                    <ReactECharts notMerge={true} option={getSohChartOption()} style={{ height: '100%', width: '100%' }} />
                  </div>
                </div>
              )}

              {key === 'temp_chart' && activeTab === 'load' && (
                <div className="h-full overflow-hidden p-4 flex flex-col justify-between">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2 flex-shrink-0">
                    <span className="text-xs font-bold text-white">Continuous Discharge Self-Heating Thermal Profile</span>
                  </div>
                  <div className="flex-1 min-h-0 mt-3">
                    <ReactECharts notMerge={true} option={getTempChartOption()} style={{ height: '100%', width: '100%' }} />
                  </div>
                </div>
              )}

              {key === 'schematic' && activeTab === 'balance' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-3">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
                    <Compass className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold text-white">BMS Passive Balancing Channel Schematic</span>
                  </div>
                  <div className="p-1 flex flex-col items-center bg-slate-950/10">
                    <svg width="100%" height="110" viewBox="0 0 280 110" className="text-slate-350">
                      <text x="140" y="15" textAnchor="middle" fill="#94a3b8" className="text-[7.5px] font-bold">Single-Cell Passive Bleeder Balancing Circuit</text>
                      <rect x="35" y="30" width="10" height="4" fill="#cbd5e1" />
                      <rect x="25" y="34" width="30" height="2" fill="#10b981" />
                      <rect x="30" y="36" width="20" height="2" fill="#cbd5e1" />
                      <rect x="25" y="38" width="30" height="2" fill="#cbd5e1" />
                      <text x="70" y="38" fill="#10b981" className="text-[6.5px] font-bold">Cell = {balVCell}V</text>
                      <line x1="40" y1="30" x2="40" y2="20" stroke="#64748b" strokeWidth="1.2" />
                      <line x1="40" y1="20" x2="110" y2="20" stroke="#64748b" strokeWidth="1.2" />
                      <path d="M 110,20 L 110,32 L 106,34 L 114,37 L 106,40 L 114,43 L 110,45 L 110,55" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                      <text x="128" y="38" fill="#ef4444" className="text-[6.5px] font-mono">R_bal = {balRes ? balRes.r_bleed_ohm.toFixed(1) : '--'} Ω</text>
                      <line x1="110" y1="55" x2="110" y2="65" stroke="#64748b" strokeWidth="1.2" />
                      <rect x="100" y="65" width="20" height="12" fill="#a78bfa" fillOpacity="0.2" stroke="#a78bfa" strokeWidth="1" rx="1.5" />
                      <text x="110" y="73" textAnchor="middle" fill="#a78bfa" className="text-[6px] font-bold">MOS</text>
                      <line x1="110" y1="77" x2="110" y2="85" stroke="#64748b" strokeWidth="1.2" />
                      <line x1="40" y1="38" x2="40" y2="85" stroke="#64748b" strokeWidth="1.2" />
                      <line x1="40" y1="85" x2="110" y2="85" stroke="#64748b" strokeWidth="1.2" />
                      <line x1="100" y1="71" x2="80" y2="71" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2,2" />
                      <text x="75" y="68" fill="#38bdf8" className="text-[6px] font-mono font-bold">BMS ON</text>
                      <path d="M 116,22 C 145,28 145,52 116,58" fill="none" stroke="#eab308" strokeWidth="1.2" strokeDasharray="3,2" markerEnd="url(#bal_heat_arrow2)" className="animate-pulse" />
                      <text x="156" y="44" textAnchor="middle" fill="#eab308" className="text-[6px] font-bold">Bleed Current I_bal</text>
                    </svg>
                    <defs>
                      <marker id="bal_heat_arrow2" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3" markerHeight="3" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#eab308" />
                      </marker>
                    </defs>
                  </div>
                </div>
              )}

              {key === 'bom' && activeTab === 'balance' && matchedRes && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-3">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
                    <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold text-white">E96 Bleeder Resistor BOM Recommendations</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-[10px] text-slate-350 border-collapse">
                      <thead>
                        <tr className="bg-slate-900/60 border-b border-slate-800/80 text-left text-slate-400 font-semibold">
                          <th className="p-2 pl-3">Designator</th>
                          <th className="p-2">Target (Ω)</th>
                          <th className="p-2 text-cyan-400">E96 Value (Ω)</th>
                          <th className="p-2">Tolerance</th>
                          <th className="p-2">Dissipation (W)</th>
                          <th className="p-2">Recommended Rating</th>
                          <th className="p-2 pr-3">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b border-slate-900 bg-cyan-500/5">
                          <td className="p-2 pl-3 font-mono font-bold text-slate-200">R_BAL_CH1</td>
                          <td className="p-2 font-mono">{(balRes?.r_bleed_ohm ?? 0).toFixed(2)}</td>
                          <td className="p-2 font-mono text-cyan-300 font-bold">{(matchedRes?.value ?? 0).toFixed(2)}</td>
                          <td className="p-2 font-mono text-emerald-400">{(matchedRes?.errorPct ?? 0) > 0 ? '+' : ''}{(matchedRes?.errorPct ?? 0).toFixed(2)}%</td>
                          <td className="p-2 font-mono text-rose-300">{(balRes?.p_res_w ?? 0).toFixed(3)} W</td>
                          <td className="p-2">{((balRes?.p_res_w ?? 0) * 2.0).toFixed(2)}W (2.0x Derating)</td>
                          <td className="p-2 pr-3"><span className="text-emerald-400 font-semibold">Primary Pick</span></td>
                        </tr>
                        <tr className="border-b border-slate-900 text-slate-400">
                          <td className="p-2 pl-3 font-mono">R_BAL_ALT1</td>
                          <td className="p-2 font-mono">{((balRes?.r_bleed_ohm ?? 0) * 1.2).toFixed(2)}</td>
                          <td className="p-2 font-mono">{((matchedRes?.value ?? 0) * 1.2).toFixed(2)}</td>
                          <td className="p-2 font-mono">+20.0%</td>
                          <td className="p-2 font-mono">{((balRes?.p_res_w ?? 0) * 0.83).toFixed(3)} W</td>
                          <td className="p-2">{((balRes?.p_res_w ?? 0) * 0.83 * 2.0).toFixed(2)}W</td>
                          <td className="p-2 pr-3">Alternative (Lower Heat)</td>
                        </tr>
                        {(balRes?.p_res_w ?? 0) > 0.5 && (
                          <tr className="border-b border-slate-900 bg-amber-500/10 text-amber-300">
                            <td className="p-2 pl-3 font-mono font-bold">R_BAL_PAR (Thermal Split)</td>
                            <td className="p-2 font-mono">2x {((balRes?.r_bleed_ohm ?? 0) * 2.0).toFixed(2)}</td>
                            <td className="p-2 font-mono font-bold">2x {((matchedRes?.value ?? 0) * 2.0).toFixed(2)}</td>
                            <td className="p-2 font-mono">Split</td>
                            <td className="p-2 font-mono">2x {((balRes?.p_res_w ?? 0) / 2.0).toFixed(3)} W</td>
                            <td className="p-2">2x 1206 / 2512 SMD</td>
                            <td className="p-2 pr-3 font-bold text-amber-400">Recommended (&gt;0.5W)</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
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
