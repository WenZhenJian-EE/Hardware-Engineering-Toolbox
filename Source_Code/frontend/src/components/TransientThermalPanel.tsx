import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import {
  ArrowLeft,
  Plus,
  ShieldAlert,
  CheckCircle2,
  Trash2
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
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-xs text-slate-350" : "inline-block text-xs"} />;
};

const E24 = [
  1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
];

const E96 = [
  1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43,
  1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10,
  2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
  3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53,
  4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
  6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
];

function findClosestStandard(val: number, series: number[]): { value: number; error: number } {
  if (!val || val <= 0) return { value: 0, error: 0 };
  const log10 = Math.log10(val);
  const decade = Math.floor(log10);
  const normVal = val / Math.pow(10, decade);
  let closestNorm = series[0];
  let minDiff = Math.abs(normVal - closestNorm);
  for (let i = 1; i < series.length; i++) {
    const diff = Math.abs(normVal - series[i]);
    if (diff < minDiff) {
      minDiff = diff;
      closestNorm = series[i];
    }
  }
  const standardVal = closestNorm * Math.pow(10, decade);
  const error = ((standardVal - val) / val) * 100;
  return { value: parseFloat(standardVal.toFixed(3)), error: parseFloat(error.toFixed(2)) };
}

interface RcRow {
  r: number;
  tau: number;
}

interface CustomPulse {
  time: number;
  power: number;
}

interface BomItem {
  designator: string;
  calcValue: string;
  stdValue: string;
  error: string;
  type: string;
  desc: string;
}

export default function TransientThermalPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: (mod: string | null) => void }) {
  const [pulseMode, setPulseMode] = useState<string>('periodic');

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
    panelKey: 'layout_transientthermalpanel_v3_' + pulseMode,
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 800, results: 920 }
  });
  const [preset, setPreset] = useState<string>('SiC_650V');
  const [tCase, setTCase] = useState<number>(60.0);
  const [tSimMax, setTSimMax] = useState<number>(0.2);
  const [simSteps, setSimSteps] = useState<number>(500);

  // Periodic pulse params
  const [pPeak, setPPeak] = useState<number>(150.0);
  const [duty, setDuty] = useState<number>(0.1);
  const [period, setPeriod] = useState<number>(0.02);
  const [cycles, setCycles] = useState<number>(5);

  // Custom pulse params
  const [customPulses, setCustomPulses] = useState<CustomPulse[]>([
    { time: 0.0, power: 0.0 },
    { time: 0.02, power: 300.0 },
    { time: 0.03, power: 300.0 },
    { time: 0.04, power: 0.0 },
    { time: 0.1, power: 500.0 },
    { time: 0.105, power: 500.0 },
    { time: 0.12, power: 0.0 },
    { time: 0.2, power: 0.0 }
  ]);

  // Foster RC ladder rows
  const [rcRows, setRcRows] = useState<RcRow[]>([
    { r: 0.08, tau: 0.0005 },
    { r: 0.15, tau: 0.005 },
    { r: 0.22, tau: 0.06 },
    { r: 0.35, tau: 0.4 }
  ]);

  const [calcResult, setCalcResult] = useState<any>(null);
  const [calcError, setCalcError] = useState<string | null>(null);
  const [chartOption, setChartOption] = useState<any>({});
  const [hoveredSymbol, setHoveredSymbol] = useState<string | null>(null);

  const API_BASE = '/api/calculate/thermal/foster_transient';

  const devicePresets: Record<string, { desc: string; rows: RcRow[] }> = {
    'SiC_650V': {
      desc: 'Typical 650V/40A SiC MOSFET (TO-247)',
      rows: [
        { r: 0.05, tau: 0.0002 },
        { r: 0.12, tau: 0.002 },
        { r: 0.28, tau: 0.03 },
        { r: 0.35, tau: 0.25 }
      ]
    },
    'SiC_1200V': {
      desc: 'Typical 1200V/80A SiC MOSFET (TO-247-4L)',
      rows: [
        { r: 0.03, tau: 0.0001 },
        { r: 0.08, tau: 0.001 },
        { r: 0.15, tau: 0.015 },
        { r: 0.24, tau: 0.18 }
      ]
    },
    'GaN_Power': {
      desc: 'Typical 650V GaN HEMT Power Device (DFN 8x8)',
      rows: [
        { r: 0.12, tau: 0.0003 },
        { r: 0.32, tau: 0.004 },
        { r: 0.58, tau: 0.05 },
        { r: 0.48, tau: 0.3 }
      ]
    },
    'IGBT_1200V': {
      desc: 'High-Power 1200V/150A IGBT Discrete',
      rows: [
        { r: 0.015, tau: 0.0005 },
        { r: 0.045, tau: 0.008 },
        { r: 0.09, tau: 0.09 },
        { r: 0.12, tau: 0.6 }
      ]
    }
  };

  useEffect(() => {
    if (preset !== 'Custom' && devicePresets[preset]) {
      setRcRows([...devicePresets[preset].rows]);
    }
  }, [preset]);

  const addRcRow = () => {
    setPreset('Custom');
    setRcRows([...rcRows, { r: 0.1, tau: 0.1 }]);
  };

  const deleteRcRow = (index: number) => {
    setPreset('Custom');
    if (rcRows.length > 1) {
      setRcRows(rcRows.filter((_, i) => i !== index));
    }
  };

  const updateRcCell = (index: number, field: 'r' | 'tau', value: number) => {
    setPreset('Custom');
    const updated = [...rcRows];
    updated[index][field] = value;
    setRcRows(updated);
  };

  const addPulsePoint = () => {
    setCustomPulses([...customPulses, { time: tSimMax, power: 0.0 }]);
  };

  const deletePulsePoint = (index: number) => {
    if (customPulses.length > 1) {
      setCustomPulses(customPulses.filter((_, i) => i !== index));
    }
  };

  const updatePulsePoint = (index: number, field: 'time' | 'power', value: number) => {
    const updated = [...customPulses];
    updated[index][field] = value;
    setCustomPulses(updated);
  };

  const performSimulation = async () => {
    setCalcError(null);
    try {
      const r_vals = rcRows.map(row => row.r);
      const tau_vals = rcRows.map(row => row.tau);

      const payload: any = {
        r_vals,
        tau_vals,
        pulse_mode: pulseMode,
        t_case: tCase,
        t_sim_max: tSimMax,
        sim_steps: simSteps
      };

      if (pulseMode === 'periodic') {
        payload.p_peak = pPeak;
        payload.duty = duty;
        payload.period = period;
        payload.cycles = cycles;
      } else {
        const sortedPulses = [...customPulses].sort((a, b) => a.time - b.time);
        payload.custom_pulses = sortedPulses;
      }

      const response = await apiFetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Transient simulation solver failed');
      }

      const data = await response.json();
      setCalcResult(data);
      renderChart(data);
    } catch (err: any) {
      setCalcError(err.message);
    }
  };

  const renderChart = (data: any) => {
    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['Junction Temp Tj (℃)', 'Overload Power P (W)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.t_s.map((t: number) => parseFloat(t.toFixed(4))),
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 't (s)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Tj (℃)',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 },
          axisLine: { lineStyle: { color: '#1e293b' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }
        },
        {
          type: 'value',
          name: 'Power (W)',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 },
          axisLine: { lineStyle: { color: '#1e293b' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Junction Temp Tj (℃)',
          type: 'line',
          data: data.tj_c.map((v: number) => parseFloat(v.toFixed(1))),
          smooth: true,
          lineStyle: { color: '#ef4444', width: 2 },
          showSymbol: false
        },
        {
          name: 'Overload Power P (W)',
          type: 'line',
          yAxisIndex: 1,
          data: data.p_w.map((v: number) => parseFloat(v.toFixed(1))),
          step: 'end',
          lineStyle: { color: '#38bdf8', width: 1.5 },
          areaStyle: { color: 'rgba(56, 189, 248, 0.06)' },
          showSymbol: false
        }
      ]
    };
    setChartOption(option);
  };

  useEffect(() => {
    performSimulation();
  }, [pulseMode, preset, rcRows, tCase, tSimMax, simSteps, pPeak, duty, period, cycles, customPulses]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('target_transient_thermal_data');
      if (raw) {
        const data = JSON.parse(raw);
        if (data.tab === 'transient' && data.params) {
          const p = data.params;
          if (p.p_shock !== undefined) setPPeak(p.p_shock);
          if (p.t_start !== undefined) setTCase(p.t_start);
          setPulseMode('periodic');
        }
        localStorage.removeItem('target_transient_thermal_data');
      }
    } catch (e) {
      console.error("Failed to parse target transient thermal data", e);
    }
  }, []);

  const isOverTemp = calcResult && calcResult.max_tj_c > 150.0;

  const getMatchedBom = (): BomItem[] => {
    const items: BomItem[] = [];
    rcRows.forEach((row, i) => {
      const rMatch = findClosestStandard(row.r, E96);
      items.push({
        designator: `Rth_${i + 1}`,
        calcValue: `${row.r.toFixed(3)} K/W`,
        stdValue: `${rMatch.value.toFixed(3)} K/W`,
        error: `${rMatch.error > 0 ? '+' : ''}${rMatch.error}%`,
        type: 'Resistor (E96)',
        desc: `Stage ${i + 1} thermal sensor equivalent resistance (simulated via resistor)`
      });

      if (row.r > 0) {
        const cVal = row.tau / row.r;
        const cMatch = findClosestStandard(cVal, E24);
        items.push({
          designator: `Cth_${i + 1}`,
          calcValue: cVal >= 1.0 ? `${cVal.toFixed(3)} J/K` : `${(cVal * 1000).toFixed(2)} mJ/K`,
          stdValue: cVal >= 1.0 ? `${cMatch.value.toFixed(3)} J/K` : `${(cMatch.value * 1000).toFixed(2)} mJ/K`,
          error: `${cMatch.error > 0 ? '+' : ''}${cMatch.error}%`,
          type: 'Capacitor (E24)',
          desc: `Stage ${i + 1} thermal sensor equivalent capacitance (simulated via capacitor)`
        });
      }
    });
    return items;
  };

  const matchedBom = getMatchedBom();

  const renderFosterSvg = () => {
    const n = rcRows.length;
    const startX = 40;
    const stageWidth = 90;
    const totalWidth = startX + 20 + n * stageWidth + 60;

    return (
      <svg 
        viewBox={`0 0 ${totalWidth} 120`} 
        className="w-full h-auto max-w-4xl text-slate-350 mx-auto select-none"
      >
        {/* Power source P(t) input */}
        <circle cx={startX} cy={60} r="4" fill="#ef4444" />
        <text x={startX - 8} y={56} textAnchor="end" fill="#ef4444" className="text-[9px] font-bold font-mono">P(t)</text>
        <line x1={startX} y1={60} x2={startX + 20} y2={60} stroke="#64748b" strokeWidth="1.5" />

        {rcRows.map((row, idx) => {
          const x = startX + 20 + idx * stageWidth;
          const cVal = row.r > 0 ? (row.tau / row.r) : 0;
          const cText = cVal >= 1.0 
            ? `${cVal.toFixed(2)} J/K` 
            : cVal >= 0.001 
              ? `${(cVal * 1000).toFixed(1)} mJ/K` 
              : `${(cVal * 1e6).toFixed(0)} μJ/K`;

          return (
            <g 
              key={idx} 
              className={hoveredSymbol === `stage_${idx}` ? 'text-cyan-400' : ''} 
              onMouseEnter={() => setHoveredSymbol(`stage_${idx}`)} 
              onMouseLeave={() => setHoveredSymbol(null)}
            >
              {/* Branching Node */}
              <circle cx={x} cy={60} r="2" fill="#cbd5e1" />
              <line x1={x} y1={60} x2={x} y2={35} stroke="#64748b" strokeWidth="1.2" />
              <line x1={x} y1={60} x2={x} y2={85} stroke="#64748b" strokeWidth="1.2" />

              {/* Top: Resistor */}
              <line x1={x} y1={35} x2={x + 12} y2={35} stroke="#64748b" strokeWidth="1.2" />
              <path 
                d={`M ${x + 12},35 L ${x + 14},35 L ${x + 17},27 L ${x + 21},43 L ${x + 25},27 L ${x + 29},43 L ${x + 33},27 L ${x + 36},35 L ${x + 38},35`} 
                fill="none" 
                stroke="#ef4444" 
                strokeWidth="1.5" 
              />
              <line x1={x + 38} y1={35} x2={x + 50} y2={35} stroke="#64748b" strokeWidth="1.2" />
              <text x={x + 25} y={20} textAnchor="middle" fill="#ef4444" className="text-[9px] font-mono font-bold">R{idx + 1}={row.r.toFixed(2)} K/W</text>

              {/* Bottom: Capacitor */}
              <line x1={x} y1={85} x2={x + 18} y2={85} stroke="#64748b" strokeWidth="1.2" />
              <line x1={x + 18} y1={75} x2={x + 18} y2={95} stroke="#38bdf8" strokeWidth="2" />
              <line x1={x + 22} y1={75} x2={x + 22} y2={95} stroke="#38bdf8" strokeWidth="2" />
              <line x1={x + 22} y1={85} x2={x + 50} y2={85} stroke="#64748b" strokeWidth="1.2" />
              <text x={x + 25} y={106} textAnchor="middle" fill="#38bdf8" className="text-[9px] font-mono font-bold">{cText}</text>

              {/* Merging Node */}
              <line x1={x + 50} y1={35} x2={x + 50} y2={60} stroke="#64748b" strokeWidth="1.2" />
              <line x1={x + 50} y1={85} x2={x + 50} y2={60} stroke="#64748b" strokeWidth="1.2" />
              <circle cx={x + 50} cy={60} r="2" fill="#cbd5e1" />
              <line x1={x + 50} y1={60} x2={x + stageWidth} y2={60} stroke="#64748b" strokeWidth="1.5" />
            </g>
          );
        })}

        {/* Case junction node */}
        {(() => {
          const caseX = startX + 20 + n * stageWidth;
          return (
            <g>
              <circle cx={caseX} cy={60} r="4" fill="#10b981" />
              <text x={caseX + 8} y={56} fill="#10b981" className="text-[9px] font-bold font-mono">Case</text>
              <line x1={caseX} y1={60} x2={caseX} y2={80} stroke="#64748b" strokeWidth="1.2" />
              
              {/* Ground reference lines */}
              <line x1={caseX - 12} y1={80} x2={caseX + 12} y2={80} stroke="#10b981" strokeWidth="1.5" />
              <line x1={caseX - 8} y1={84} x2={caseX + 8} y2={84} stroke="#10b981" strokeWidth="1.5" />
              <line x1={caseX - 4} y1={88} x2={caseX + 4} y2={88} stroke="#10b981" strokeWidth="1.5" />
              <text x={caseX + 16} y={85} fill="#10b981" className="text-[9px] font-mono font-bold">Tc={tCase}℃</text>
            </g>
          );
        })()}
      </svg>
    );
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      <div className="flex-shrink-0 space-y-3">
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
              <h1 className="text-base font-bold text-white tracking-tight">Transient Thermal Network & Junction Temp Simulation</h1>
              <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
                Simulates and predicts semiconductor switch dynamic junction temperature under transient overload using Foster RC thermal state equations.
              </p>
            </div>
          </div>
        </div>

        {/* Subtab selector */}
        <div className="flex border-b border-slate-800 gap-1 overflow-x-auto pb-1">
          {(['periodic', 'custom'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => { setPulseMode(mode); }}
              className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 ${
                pulseMode === mode
                  ? 'border-b-blue-500 text-blue-400 font-bold bg-slate-950/40'
                  : 'border-b-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {mode === 'periodic' ? 'Periodic Switch Pulse Simulation' : 'Custom Surge Pulse Profile'}
            </button>
          ))}
        </div>

        {/* Errors / Warnings */}
        {calcError && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>{calcError}</span>
          </div>
        )}

        {/* DRC Alerts */}
        {isOverTemp && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400">
            <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-bold block">⚠️ Junction Transient Overtemperature Thermal Runaway Risk</span>
              <span className="mt-1 block">Simulation indicates maximum peak junction temperature reached {calcResult?.max_tj_c.toFixed(1)} ℃, exceeding typical semiconductor limit of 150.0 ℃! Risk of thermal destruction. Reduce overload power, increase pulse period, or select lower thermal resistance packages.</span>
            </div>
          </div>
        )}

        {calcResult && !isOverTemp && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
            <span>✅ Transient Temperature Margin Safe: Maximum junction temperature is {calcResult.max_tj_c.toFixed(1)} ℃, with {(150.0 - calcResult.max_tj_c).toFixed(1)} ℃ margin remaining.</span>
          </div>
        )}
      </div>

      {/* DragDeck area container */}
      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 p-3 pt-0 min-h-0">
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
              onResetLayout={handleResetLayout}
            >
              {key === 'input' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md space-y-4">
                  <div className="flex items-center justify-between mb-3 border-b border-slate-800/60 pb-2">
                    <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wide flex items-center gap-2">
                      Pulse & Thermal Network Configuration
                    </h3>
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Load Foster Thermal Network Preset</label>
                    <select value={preset} onChange={(e) => setPreset(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs w-full text-white focus:outline-none">
                      <option value="Custom">Custom RC Network</option>
                      <option value="SiC_650V">650V/40A SiC MOSFET (TO-247)</option>
                      <option value="SiC_1200V">1200V/80A SiC MOSFET (TO-247-4L)</option>
                      <option value="GaN_Power">650V GaN HEMT Power Device (DFN 8x8)</option>
                      <option value="IGBT_1200V">High-Power IGBT Discrete</option>
                    </select>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                      Case Temperature & Simulation Duration
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Case Temperature Tc [℃]</label>
                        <input type="number" value={tCase} onChange={(e) => setTCase(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Total Sim Duration t_sim [s]</label>
                        <input type="number" value={tSimMax} onChange={(e) => setTSimMax(parseFloat(e.target.value) || 0.01)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                    </div>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                      Power Pulse & Overload Dissipation
                    </div>
                    {pulseMode === 'periodic' ? (
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Peak Power P_peak [W]</label>
                          <input type="number" value={pPeak} onChange={(e) => setPPeak(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Pulse Duty Cycle D</label>
                          <input type="number" step="0.05" min="0.01" max="0.99" value={duty} onChange={(e) => setDuty(parseFloat(e.target.value) || 0.1)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Pulse Period T [s]</label>
                          <input type="number" value={period} onChange={(e) => setPeriod(parseFloat(e.target.value) || 0.001)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Pulse Cycles</label>
                          <input type="number" value={cycles} onChange={(e) => setCycles(parseInt(e.target.value) || 1)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-500 italic text-[11px] block">In custom mode, configure the time-power breakpoint profile below.</span>
                    )}
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1 flex justify-between items-center">
                      <span>Multi-Stage Foster RC Ladder Network</span>
                      <Button size="sm" className="h-5 px-1.5 text-[9px]" onClick={addRcRow}>
                        <Plus className="w-3 h-3 mr-0.5" /> Add Stage
                      </Button>
                    </div>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                      {rcRows.map((row, idx) => (
                        <div key={idx} className="flex gap-2 items-center bg-slate-900/60 p-1.5 rounded border border-slate-800/60">
                          <span className="font-mono text-[9px] w-4 text-slate-400">#{idx + 1}</span>
                          <div className="flex-1">
                            <label className="text-[8px] text-slate-500 block">Rth (K/W)</label>
                            <input type="number" step="0.01" value={row.r} onChange={(e) => updateRcCell(idx, 'r', parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-850 rounded p-1 text-[10px] text-white focus:outline-none focus:border-blue-500" />
                          </div>
                          <div className="flex-1">
                            <label className="text-[8px] text-slate-500 block">Tau (s)</label>
                            <input type="number" step="0.0001" value={row.tau} onChange={(e) => updateRcCell(idx, 'tau', parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-850 rounded p-1 text-[10px] text-white focus:outline-none focus:border-blue-500" />
                          </div>
                          <button onClick={() => deleteRcRow(idx)} className="p-1 rounded bg-red-950/20 text-red-400 hover:text-red-300 hover:bg-red-950/40 border-0 cursor-pointer">
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1 flex justify-between items-center">
                      <span>Custom Waveform & Simulation Resolution</span>
                    </div>
                    {pulseMode === 'custom' && (
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-slate-400 font-semibold">Time-Domain Power Breakpoint Profile</span>
                          <Button size="sm" className="h-5 px-1.5 text-[9px]" onClick={addPulsePoint}>
                            <Plus className="w-3 h-3 mr-0.5" /> Add Breakpoint
                          </Button>
                        </div>
                        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                          {customPulses.map((pt, idx) => (
                            <div key={idx} className="flex gap-2 items-center bg-slate-900/60 p-1 rounded border border-slate-800/60">
                              <div className="flex-1">
                                <label className="text-[8px] text-slate-500 block">Time (s)</label>
                                <input type="number" step="0.005" value={pt.time} onChange={(e) => updatePulsePoint(idx, 'time', parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-850 rounded p-1 text-[9px] text-white focus:outline-none focus:border-blue-500" />
                              </div>
                              <div className="flex-1">
                                <label className="text-[8px] text-slate-500 block">Power (W)</label>
                                <input type="number" step="10" value={pt.power} onChange={(e) => updatePulsePoint(idx, 'power', parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-850 rounded p-1 text-[9px] text-white focus:outline-none focus:border-blue-500" />
                              </div>
                              <button onClick={() => deletePulsePoint(idx)} className="p-0.5 rounded bg-red-950/20 text-red-400 hover:text-red-300 hover:bg-red-950/40 border-0 cursor-pointer">
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-1">Simulation Steps</label>
                      <input type="number" value={simSteps} onChange={(e) => setSimSteps(parseInt(e.target.value) || 100)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                    </div>
                  </div>
                </div>
              )}

              {key === 'results' && (
                <div className="overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md flex flex-col gap-4" style={{ height: cardHeights[key] ? cardHeights[key] - 50 : '100%' }}>
                  {/* Card 1: Foster thermal impedance ladder network SVG */}
                  <Card className="bg-slate-900/40 border-slate-800/80">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2">
                        Multi-Stage Equivalent Foster Model Schematic
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col items-center bg-slate-950/20 py-4 border-t border-slate-900/50 overflow-x-auto">
                      {renderFosterSvg()}
                      <p className="text-[10px] text-slate-400 mt-2 italic">* Note: Foster network parameters are directly extracted from datasheets. Total junction temperature is the algebraic sum of all stage responses.</p>
                    </CardContent>
                  </Card>

                  {/* Card 2: ECharts transient simulation graph */}
                  {calcResult && (
                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2">
                          Transient Junction Temperature & Input Power Waveforms
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="h-72 border-t border-slate-900/50">
                        <ReactECharts option={chartOption} notMerge={true} style={{ height: '100%', width: '100%' }} />
                      </CardContent>
                    </Card>
                  )}

                  {/* Card 3: Math and physics equations */}
                  <Card className="bg-slate-900/40 border-slate-800/80">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2">
                        Foster State-Space Thermal Impedance Mathematical Formulation
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="text-slate-400 text-xs space-y-2 leading-relaxed p-4 border-t border-slate-900/50">
                      <p>Foster differential equation (FDM discretization): Each RC cell represents an equivalent thermal impedance stage. The temperature rise across each stage is governed by:</p>
                      <Latex math={"\\frac{d\\Delta T_i(t)}{dt} = \\frac{P_{loss}(t)}{C_i} - \\frac{\\Delta T_i(t)}{R_i C_i} = \\frac{1}{\\tau_i} \\left( R_i P_{loss}(t) - \\Delta T_i(t) \\right)"} block />
                      <p>Junction temperature summation: The total transient junction temperature is the sum of all RC cell temperature rises plus the case temperature:</p>
                      <Latex math={"T_j(t) = T_c + \\sum_{i=1}^{n} \\Delta T_i(t)"} block />
                      <p>Difference between Cauer and Foster: Foster parameters do not strictly map to physical layers (silicon, solder, baseplate), but because each node responds independently, Foster models allow extremely fast convolution or discrete solver performance and are standard in semiconductor datasheet Zth(j-c) curves.</p>
                    </CardContent>
                  </Card>

                  {/* Card 4: Recommended BOM */}
                  {matchedBom.length > 0 && (
                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2">
                          Equivalent Electrical Simulation Component Reference
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="border-t border-slate-900/50 p-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-left border-collapse">
                            <thead>
                              <tr className="bg-slate-950/50 text-[10px] text-slate-400 border-b border-slate-800/60 uppercase tracking-wider">
                                <th className="p-2 font-medium">Designator</th>
                                <th className="p-2 font-medium">Type</th>
                                <th className="p-2 font-medium">Calc Value</th>
                                <th className="p-2 font-medium">Std Value</th>
                                <th className="p-2 font-medium">Error</th>
                                <th className="p-2 font-medium">Description</th>
                              </tr>
                            </thead>
                            <tbody className="text-[10px] text-slate-300">
                              {matchedBom.map((item, idx) => (
                                <tr key={idx} className="border-b border-slate-800/40 last:border-0 hover:bg-slate-900/30 transition-colors">
                                  <td className="p-2 pl-3 font-mono text-blue-400">{item.designator}</td>
                                  <td className="p-2 text-slate-400">{item.type}</td>
                                  <td className="p-2 font-mono">{item.calcValue}</td>
                                  <td className="p-2 font-mono text-emerald-400 font-bold">{item.stdValue}</td>
                                  <td className={`p-2 font-mono ${item.error.includes('+') ? 'text-amber-400' : 'text-emerald-400'}`}>{item.error}</td>
                                  <td className="p-2 pr-3 text-slate-500" title={item.desc}>{item.desc}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  )}
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
