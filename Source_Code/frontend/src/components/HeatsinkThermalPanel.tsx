import React, { useState, useEffect, useRef } from 'react';
import { apiFetch } from '../lib/api';
import { 
  ShieldAlert, 
  CheckCircle2, 
  ArrowLeft, 
  Info
} from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

import { Card, CardContent } from './ui/Card';
import { Button } from './ui/Button';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
import { useDragDeckLayout, DragDeck, DragCard } from './ui/LayoutEngine';

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

interface HeatsinkExtrusion {
  name: string;
  width: number;
  height: number;
  length: number;
  material: string;
  r_sa: number;
  type: string;
}

const defaultHeatsinkExtrusions: HeatsinkExtrusion[] = [
  { name: 'AL-Extrusion E150', width: 150, height: 60, length: 250, material: '6063-T5', r_sa: 0.18, type: 'Dense Skived-Fin' },
  { name: 'AL-Extrusion E120', width: 120, height: 50, length: 200, material: '6063-T5', r_sa: 0.32, type: 'Dense Extrusion' },
  { name: 'AL-Extrusion E100', width: 100, height: 40, length: 150, material: '6063-T5', r_sa: 0.45, type: 'Standard Comb' },
  { name: 'AL-Extrusion E80', width: 80, height: 30, length: 100, material: '6063-T5', r_sa: 0.85, type: 'Standard Comb' },
  { name: 'AL-Extrusion E60', width: 60, height: 25, length: 80, material: '6063-T5', r_sa: 1.65, type: 'Micro-Channel' }
];

export default function HeatsinkThermalPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: (mod: string | null) => void }) {
  const [activeTab, setActiveTab] = useState<string>(() => {
    const saved = localStorage.getItem('thermal_active_tab');
    return saved || 'steady';
  });

  const getTabConfig = (tab: string) => {
    switch (tab) {
      case 'steady':
        return {
          defaultCards: ['input', 'results', 'schematic', 'bom'],
          defaultColumns: { input: 'left', results: 'right', schematic: 'right', bom: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, results: 8, schematic: 8, bom: 8 },
          defaultHeights: { input: 820, results: 250, schematic: 300, bom: 450 }
        };
      case 'forced':
        return {
          defaultCards: ['input', 'results', 'chart'],
          defaultColumns: { input: 'left', results: 'right', chart: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, results: 8, chart: 8 },
          defaultHeights: { input: 820, results: 250, chart: 400 }
        };
      case 'enclosure':
        return {
          defaultCards: ['input', 'results'],
          defaultColumns: { input: 'left', results: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, results: 8 },
          defaultHeights: { input: 820, results: 500 }
        };
      case 'transient':
        return {
          defaultCards: ['input', 'results', 'chart'],
          defaultColumns: { input: 'left', results: 'right', chart: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, results: 8, chart: 8 },
          defaultHeights: { input: 820, results: 300, chart: 400 }
        };
      case 'sysair':
      default:
        return {
          defaultCards: ['input', 'results', 'chart'],
          defaultColumns: { input: 'left', results: 'right', chart: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, results: 8, chart: 8 },
          defaultHeights: { input: 820, results: 250, chart: 400 }
        };
    }
  };

  const currentTabConfig = getTabConfig(activeTab);

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
    handleHeightResizeStart,
    handleHeightResizeStartTop,
    handleResetCardHeight,
    handleResizeStart,
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_heatsinkthermalpanel_v3_' + activeTab,
    activeTab: activeTab,
    defaultCards: currentTabConfig.defaultCards,
    defaultColumns: currentTabConfig.defaultColumns,
    defaultSpans: currentTabConfig.defaultSpans,
    defaultHeights: currentTabConfig.defaultHeights
  });

  const handleTabChange = (val: string) => {
    setActiveTab(val);
    localStorage.setItem('thermal_active_tab', val);
  };

  const [steadyIn, setSteadyIn] = useState({ p_diss: 15, t_j_max: 150, t_amb: 50, r_jc: 1.0, r_cs: 0.5 });
  const [steadyOut, setSteadyOut] = useState<{ r_sa_max: number; t_case: number } | null>(null);

  const [forcedIn, setForcedIn] = useState({ cfm: 10, duct_w: 50, duct_h: 30, r_nat: 5.0, air_vel: 2.0 });
  const [forcedOut, setForcedOut] = useState<{ lfm: number; air_vel_ms: number; r_forced: number } | null>(null);

  const [encIn, setEncIn] = useState({ length_mm: 100, width_mm: 50, height_mm: 30, p_in: 2.0, k_factor: 450, t_amb: 25 });
  const [encOut, setEncOut] = useState<{ area_m2: number; temp_rise: number; t_internal: number } | null>(null);

  const [transIn, setTransIn] = useState({ c_spec: 900, mass_g: 200, p_shock: 500, duration_s: 10, t_start: 25 });
  const [transOut, setTransOut] = useState<{ energy_j: number; c_th: number; temp_rise: number; t_end: number } | null>(null);

  const [sysAirIn, setSysAirIn] = useState({ p_loss: 500, dt_allowed: 15, altitude_m: 2000, margin_pct: 20 });
  const [sysAirOut, setSysAirOut] = useState<{ cfm_total: number; cmm_total: number; alt_factor: number } | null>(null);

  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const calcSteady = async () => {
    try {
      const response = await apiFetch('/api/calculate/thermal/heatsink_rth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          p_diss: steadyIn.p_diss,
          t_j_max: steadyIn.t_j_max,
          t_amb: steadyIn.t_amb,
          r_jc: steadyIn.r_jc,
          r_cs: steadyIn.r_cs
        })
      });
      if (response.ok) {
        const data = await response.json();
        setSteadyOut({ r_sa_max: data.r_sa_max, t_case: data.t_case });
      }
    } catch (e) {}
  };

  const calcForced = async () => {
    try {
      const response = await apiFetch('/api/calculate/thermal/forced_air', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cfm: forcedIn.cfm,
          duct_w_mm: forcedIn.duct_w,
          duct_h_mm: forcedIn.duct_h,
          r_nat: forcedIn.r_nat,
          air_vel_ms: forcedIn.air_vel
        })
      });
      if (response.ok) {
        const data = await response.json();
        setForcedOut({ lfm: data.lfm, air_vel_ms: data.air_vel_ms, r_forced: data.r_forced });
      }
    } catch (e) {}
  };

  const calcEnclosure = async () => {
    try {
      const response = await apiFetch('/api/calculate/thermal/enclosure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          length_mm: encIn.length_mm,
          width_mm: encIn.width_mm,
          height_mm: encIn.height_mm,
          p_in: encIn.p_in,
          k_factor: encIn.k_factor,
          t_amb: encIn.t_amb
        })
      });
      if (response.ok) {
        const data = await response.json();
        setEncOut({ area_m2: data.area_m2, temp_rise: data.temp_rise, t_internal: data.t_internal });
      }
    } catch (e) {}
  };

  const calcTransient = async () => {
    try {
      const response = await apiFetch('/api/calculate/thermal/transient', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          c_spec: transIn.c_spec,
          mass_g: transIn.mass_g,
          p_shock: transIn.p_shock,
          duration_s: transIn.duration_s,
          t_start: transIn.t_start
        })
      });
      if (response.ok) {
        const data = await response.json();
        setTransOut({ energy_j: data.energy_j, c_th: data.c_th, temp_rise: data.temp_rise, t_end: data.t_end });
      }
    } catch (e) {}
  };

  const calcSysAir = async () => {
    try {
      const response = await apiFetch('/api/calculate/thermal/system_airflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          p_loss: sysAirIn.p_loss,
          altitude_m: sysAirIn.altitude_m,
          dt_allowed: sysAirIn.dt_allowed,
          margin_pct: sysAirIn.margin_pct
        })
      });
      if (response.ok) {
        const data = await response.json();
        setSysAirOut({ cfm_total: data.cfm_total, cmm_total: data.cmm_total, alt_factor: data.alt_factor });
      }
    } catch (e) {}
  };

  useEffect(() => {
    calcSteady();
  }, [steadyIn]);

  useEffect(() => {
    calcForced();
  }, [forcedIn]);

  useEffect(() => {
    calcEnclosure();
  }, [encIn]);

  useEffect(() => {
    calcTransient();
  }, [transIn]);

  useEffect(() => {
    calcSysAir();
  }, [sysAirIn]);

  const getForcedChartOption = () => {
    if (!forcedOut) return {};
    const velVals = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0];
    const rVals = velVals.map(v => {
      const scale = Math.sqrt(forcedIn.air_vel / v);
      return parseFloat((forcedOut.r_forced * scale).toFixed(3));
    });

    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155', textStyle: { color: '#f1f5f9', fontSize: 11 } },
      grid: { left: '10%', right: '10%', bottom: '8%', top: '20%', containLabel: true },
      xAxis: { type: 'category', data: velVals.map(v => `${v} m/s`), name: 'Air Velocity', axisLine: { lineStyle: { color: '#1e293b' } }, axisLabel: { color: '#94a3b8', fontSize: 9 } },
      yAxis: { type: 'value', name: 'Thermal Resistance Rth (K/W)', axisLine: { lineStyle: { color: '#1e293b' } }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }, axisLabel: { color: '#94a3b8', fontSize: 9 } },
      series: [
        { name: 'Forced Convection Rth', type: 'line', data: rVals, smooth: true, lineStyle: { color: '#06b6d4', width: 2 } }
      ]
    };
  };

  const getTransientChartOption = () => {
    if (!transOut) return {};
    const tVals = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0];
    const tempRiseVals = tVals.map(t => {
      const ratio = 1 - Math.exp(-t / (transIn.mass_g * transIn.c_spec * 1e-3 / (steadyIn.r_jc + steadyIn.r_cs + (steadyOut?.r_sa_max || 0.5))));
      return parseFloat((transOut.temp_rise * ratio).toFixed(1));
    });

    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155', textStyle: { color: '#f1f5f9', fontSize: 11 } },
      grid: { left: '10%', right: '10%', bottom: '8%', top: '20%', containLabel: true },
      xAxis: { type: 'category', data: tVals.map(t => `${t}s`), name: 'Shock Duration', axisLine: { lineStyle: { color: '#1e293b' } }, axisLabel: { color: '#94a3b8', fontSize: 9 } },
      yAxis: { type: 'value', name: 'Junction Temp Rise (°C)', axisLine: { lineStyle: { color: '#1e293b' } }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }, axisLabel: { color: '#94a3b8', fontSize: 9 } },
      series: [
        { name: 'Transient Temp Response', type: 'line', data: tempRiseVals, smooth: true, lineStyle: { color: '#ec4899', width: 2 } }
      ]
    };
  };

  const getSysAirChartOption = () => {
    if (!sysAirOut) return {};
    const dtVals = [5, 10, 15, 20, 25, 30, 35, 40];
    const cfmVals = dtVals.map(dt => {
      const baseCfm = (1.756 * sysAirIn.p_loss) / dt;
      const marginCfm = baseCfm * (1 + sysAirIn.margin_pct / 100);
      const finalCfm = marginCfm * sysAirOut.alt_factor;
      return parseFloat(finalCfm.toFixed(2));
    });

    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155', textStyle: { color: '#f1f5f9', fontSize: 11 } },
      grid: { left: '10%', right: '10%', bottom: '8%', top: '20%', containLabel: true },
      xAxis: { type: 'category', data: dtVals.map(dt => `${dt} K`), name: 'Allowed Temp Rise', axisLine: { lineStyle: { color: '#1e293b' } }, axisLabel: { color: '#94a3b8', fontSize: 9 } },
      yAxis: { type: 'value', name: 'Required Airflow CFM', axisLine: { lineStyle: { color: '#1e293b' } }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }, axisLabel: { color: '#94a3b8', fontSize: 9 } },
      series: [
        { name: 'Required Airflow', type: 'line', data: cfmVals, smooth: true, lineStyle: { color: '#10b981', width: 2 } }
      ]
    };
  };

  const heatsinkVal = steadyOut?.r_sa_max || 0.5;
  const filteredExtrusions = defaultHeatsinkExtrusions
    .filter(item => item.r_sa <= heatsinkVal)
    .sort((a, b) => a.r_sa - b.r_sa);

  const Tj = steadyIn.t_j_max;
  const Tc = steadyOut ? parseFloat(steadyOut.t_case.toFixed(1)) : 80;
  const Ts = steadyOut ? parseFloat((steadyOut.t_case - steadyIn.p_diss * steadyIn.r_cs).toFixed(1)) : 65;
  const Ta = steadyIn.t_amb;

  return (
    <div className="h-full w-full flex flex-col overflow-hidden text-slate-100 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Top Header */}
      <div className="flex-shrink-0 p-3 pb-0">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Button 
              onClick={onBack} 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                Heatsink Sizing & Thermal Resistance Analysis
              </h1>
              <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
                Computes natural convection and forced-air thermal resistance, modeling 1D and 3D multi-node thermal networks.
              </p>
            </div>
          </div>

          <Tabs value={activeTab} onValueChange={handleTabChange} className="w-auto">
            <TabsList className="bg-[#020617] border border-slate-800 h-9 p-0.5">
              <TabsTrigger value="steady" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">1. Steady Rth</TabsTrigger>
              <TabsTrigger value="forced" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">2. Forced Air</TabsTrigger>
              <TabsTrigger value="enclosure" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">3. Enclosure</TabsTrigger>
              <TabsTrigger value="transient" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">4. Transient Shock</TabsTrigger>
              <TabsTrigger value="sysair" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">5. System Airflow</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      {/* DragDeck area */}
      <div className="max-w-[1600px] mx-auto w-full flex-grow flex-1 overflow-y-auto scrollbar-thin p-3 pb-6">
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
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Operating Input Conditions</span>
                  </div>

                  {activeTab === 'steady' && (
                    <>
                      {/* Device power input */}
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Active Power Loss & Junction Limits</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Device Loss Pdiss (W)</label>
                            <input type="number" value={steadyIn.p_diss} onChange={e => setSteadyIn({ ...steadyIn, p_diss: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Ambient Temp Tamb (°C)</label>
                            <input type="number" value={steadyIn.t_amb} onChange={e => setSteadyIn({ ...steadyIn, t_amb: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Max Allowed Junction Temp Tj_max (°C)</label>
                          <input type="number" value={steadyIn.t_j_max} onChange={e => setSteadyIn({ ...steadyIn, t_j_max: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                      </div>

                      {/* Pkg thermal input */}
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Package Conduction Thermal Resistance</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Junction-to-Case Rjc (K/W)</label>
                            <input type="number" step="0.05" value={steadyIn.r_jc} onChange={e => setSteadyIn({ ...steadyIn, r_jc: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Case-to-Heatsink Rcs (K/W)</label>
                            <input type="number" step="0.05" value={steadyIn.r_cs} onChange={e => setSteadyIn({ ...steadyIn, r_cs: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {activeTab === 'forced' && (
                    <div className="space-y-4">
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Forced-Air Airflow & Duct Geometry</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Fan Airflow (CFM)</label>
                            <input type="number" value={forcedIn.cfm} onChange={e => setForcedIn({ ...forcedIn, cfm: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Natural Convection R_nat (K/W)</label>
                            <input type="number" step="0.1" value={forcedIn.r_nat} onChange={e => setForcedIn({ ...forcedIn, r_nat: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Duct Width W (mm)</label>
                            <input type="number" value={forcedIn.duct_w} onChange={e => setForcedIn({ ...forcedIn, duct_w: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Duct Height H (mm)</label>
                            <input type="number" value={forcedIn.duct_h} onChange={e => setForcedIn({ ...forcedIn, duct_h: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Base Air Velocity V_air (m/s)</label>
                          <input type="number" step="0.1" value={forcedIn.air_vel} onChange={e => setForcedIn({ ...forcedIn, air_vel: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'enclosure' && (
                    <div className="space-y-4">
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Enclosure Dimensions & Internal Heat Dissipation</span>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Length (mm)</label>
                            <input type="number" value={encIn.length_mm} onChange={e => setEncIn({ ...encIn, length_mm: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Width (mm)</label>
                            <input type="number" value={encIn.width_mm} onChange={e => setEncIn({ ...encIn, width_mm: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Height (mm)</label>
                            <input type="number" value={encIn.height_mm} onChange={e => setEncIn({ ...encIn, height_mm: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Internal Heat Pin (W)</label>
                            <input type="number" step="0.5" value={encIn.p_in} onChange={e => setEncIn({ ...encIn, p_in: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Convection Coeff k_factor</label>
                            <input type="number" value={encIn.k_factor} onChange={e => setEncIn({ ...encIn, k_factor: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Ambient Temp Ta (°C)</label>
                          <input type="number" value={encIn.t_amb} onChange={e => setEncIn({ ...encIn, t_amb: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'transient' && (
                    <div className="space-y-4">
                      {/* Foster params */}
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800/60 pb-1.5">
                          <span className="text-[10px] font-bold text-slate-300">Heatsink Thermal Mass & Specific Heat</span>
                          <select
                            className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[9px] text-cyan-400 focus:outline-none cursor-pointer"
                            onChange={(e) => {
                              const val = parseFloat(e.target.value);
                              if (val) setTransIn({ ...transIn, c_spec: val });
                            }}
                            defaultValue="900"
                          >
                            <option value="900">Aluminum (AL 6063: 900 J/kg·K)</option>
                            <option value="385">Pure Copper (385 J/kg·K)</option>
                          </select>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Specific Heat C_spec (J/kg·K)</label>
                            <input type="number" value={transIn.c_spec} onChange={e => setTransIn({ ...transIn, c_spec: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Heatsink Mass (g)</label>
                            <input type="number" value={transIn.mass_g} onChange={e => setTransIn({ ...transIn, mass_g: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>

                      {/* Shock power */}
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Transient Overload Shock Profile</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Overload Power P_shock (W)</label>
                            <input type="number" value={transIn.p_shock} onChange={e => setTransIn({ ...transIn, p_shock: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Shock Duration (s)</label>
                            <input type="number" value={transIn.duration_s} onChange={e => setTransIn({ ...transIn, duration_s: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Initial Temp T_start (°C)</label>
                          <input type="number" value={transIn.t_start} onChange={e => setTransIn({ ...transIn, t_start: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'sysair' && (
                    <div className="space-y-4">
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">System Airflow Sizing Requirements</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Total Heat Loss P_loss (W)</label>
                            <input type="number" value={sysAirIn.p_loss} onChange={e => setSysAirIn({ ...sysAirIn, p_loss: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Max Allowed Temp Rise ΔT (K)</label>
                            <input type="number" value={sysAirIn.dt_allowed} onChange={e => setSysAirIn({ ...sysAirIn, dt_allowed: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Altitude (m)</label>
                            <input type="number" value={sysAirIn.altitude_m} onChange={e => setSysAirIn({ ...sysAirIn, altitude_m: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Airflow Safety Margin (%)</label>
                            <input type="number" value={sysAirIn.margin_pct} onChange={e => setSysAirIn({ ...sysAirIn, margin_pct: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-6 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white">Simulation & Physical Limit Results</span>
                  </div>

                  {/* Tab 1: Steady Results */}
                  {activeTab === 'steady' && steadyOut && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Steady Case Temp Tc</span>
                          <span className={`text-xl font-bold font-mono ${Tc >= steadyIn.t_j_max ? 'text-red-400' : 'text-pink-400'}`}>
                            {Tc} <span className="text-xs text-slate-400">°C</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Max Allowed Heatsink Rsa</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {steadyOut.r_sa_max.toFixed(3)} <span className="text-xs text-slate-400">K/W</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Heatsink Surface Temp Ts</span>
                          <span className="text-xl font-bold text-emerald-400 font-mono">
                            {Ts} <span className="text-xs text-slate-400">°C</span>
                          </span>
                        </div>
                      </div>

                      {/* DRC Alert Panel */}
                      <div className="space-y-2">
                        {steadyOut.r_sa_max <= 0 ? (
                          <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2.5 text-xs text-red-400">
                            <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="font-bold block">⚠️ Thermal Runaway DRC Critical Violation</span>
                              <span className="mt-1 block">With {steadyIn.p_diss}W dissipation, even with an ideal 0 K/W heatsink, the sum of Rjc and Rcs causes junction temperature to reach {(steadyIn.t_amb + steadyIn.p_diss * (steadyIn.r_jc + steadyIn.r_cs)).toFixed(1)}°C, exceeding max allowable {steadyIn.t_j_max}°C! Reduce power dissipation or switch to a lower-resistance package.</span>
                            </div>
                          </div>
                        ) : steadyOut.r_sa_max > 0 && steadyOut.r_sa_max < 0.2 ? (
                          <div className="p-3.5 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-2.5 text-xs text-amber-400">
                            <ShieldAlert className="w-4.5 h-4.5 text-amber-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="font-bold block">⚠️ Tight Heatsink Margin Warning</span>
                              <span className="mt-1 block">Requires heatsink thermal resistance Rsa &lt; {steadyOut.r_sa_max.toFixed(3)} K/W. Natural convection heatsinks would be excessively bulky; forced-air or liquid cooling is required.</span>
                            </div>
                          </div>
                        ) : (
                          <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-2.5 text-xs text-emerald-400">
                            <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                            <span>✅ Thermal design margin compliant: Heatsink resistance Rsa ≤ {steadyOut.r_sa_max.toFixed(3)} K/W can be met with standard natural-convection aluminum extrusions.</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Tab 2: Forced Air Results */}
                  {activeTab === 'forced' && forcedOut && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Linear Air Velocity LFM</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {forcedOut.lfm.toFixed(0)} <span className="text-xs text-slate-400">ft/min</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Duct Linear Velocity</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {forcedOut.air_vel_ms.toFixed(2)} <span className="text-xs text-slate-400">m/s</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Forced Convective R_forced</span>
                          <span className="text-xl font-bold text-emerald-400 font-mono">
                            {forcedOut.r_forced.toFixed(3)} <span className="text-xs text-slate-400">K/W</span>
                          </span>
                        </div>
                      </div>

                      {/* DRC Alert Panel */}
                      <div className="space-y-2">
                        {forcedOut.air_vel_ms < 1.0 ? (
                          <div className="p-3.5 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-2.5 text-xs text-amber-400">
                            <ShieldAlert className="w-4.5 h-4.5 text-amber-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="font-bold block">⚠️ Low Air Velocity Warning</span>
                              <span className="mt-1 block">Actual air velocity is {forcedOut.air_vel_ms.toFixed(2)} m/s. Below 1.0 m/s, forced convection efficiency is reduced. Narrow the duct cross-section or use a higher static-pressure fan.</span>
                            </div>
                          </div>
                        ) : (
                          <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-2.5 text-xs text-emerald-400">
                            <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                            <span>✅ Forced convection conditions optimal: Duct air velocity is {forcedOut.air_vel_ms.toFixed(2)} m/s, providing strong convective cooling.</span>
                          </div>
                        )}
                      </div>
                      
                      <Card className="bg-slate-900/40 border-slate-800/80">
                        <CardContent className="pt-4 text-xs text-slate-400 leading-relaxed space-y-3">
                          <div className="flex items-center gap-1.5 font-bold text-slate-350">
                            <Info className="w-3.5 h-3.5 text-cyan-400" />
                            <span>Forced Convection Physical Formulation:</span>
                          </div>
                          <p>
                            Linear air velocity is computed from duct dimensions, scaling convection resistance:
                          </p>
                          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                            <Latex math={"V_{air} = \\frac{CFM \\cdot 1.699}{W_{duct} \\cdot H_{duct} \\cdot 10^{-6}} \\cdot \\frac{1}{3600}"} block />
                            <Latex math={"R_{forced} = \\frac{R_{nat}}{\\sqrt{1.0 + V_{air}}}"} block />
                          </div>
                          <div className="text-[10px] text-slate-400 space-y-1 bg-slate-950/10 p-2.5 rounded-lg border border-slate-800/40 mt-2">
                            <div className="font-semibold text-slate-300">Symbol Definitions:</div>
                            <div>• <Latex math={"CFM"} />: Volumetric flow rate (Cubic Feet per Minute)</div>
                            <div>• <Latex math={"W_{duct}, H_{duct}"} />: Duct width and height (mm)</div>
                            <div>• <Latex math={"V_{air}"} />: Calculated linear air velocity in duct (m/s)</div>
                            <div>• <Latex math={"LFM"} />: Linear Feet per Minute</div>
                            <div>• <Latex math={"R_{forced}"} />: Effective forced-air convection resistance (K/W)</div>
                            <div>• <Latex math={"R_{nat}"} />: Baseline natural-convection thermal resistance (K/W)</div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* Tab 3: Enclosure Results */}
                  {activeTab === 'enclosure' && encOut && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Total Enclosure Area A_enc</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {encOut.area_m2.toFixed(4)} <span className="text-xs text-slate-400">m²</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Internal Average Rise ΔT_rise</span>
                          <span className="text-xl font-bold text-orange-400 font-mono">
                            {encOut.temp_rise.toFixed(1)} <span className="text-xs text-slate-400">K</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Internal Ambient Tint</span>
                          <span className={`text-xl font-bold font-mono ${encOut.t_internal > 85 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {encOut.t_internal.toFixed(1)} <span className="text-xs text-slate-400">°C</span>
                          </span>
                        </div>
                      </div>

                      {/* DRC Alert Panel */}
                      <div className="space-y-2">
                        {encOut.t_internal > 85.0 ? (
                          <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2.5 text-xs text-red-400">
                            <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="font-bold block">⚠️ Enclosure Overtemperature Warning</span>
                              <span className="mt-1 block">Predicted enclosure internal ambient temperature reached {encOut.t_internal.toFixed(1)}°C, exceeding typical industrial component rating of 85°C. Risk of thermal shutdown or accelerated capacitor degradation. Add venting louvers or fan.</span>
                            </div>
                          </div>
                        ) : (
                          <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-2.5 text-xs text-emerald-400">
                            <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                            <span>✅ Enclosure temperature compliant: Internal average temperature is {encOut.t_internal.toFixed(1)}°C, within normal electronic operating bounds.</span>
                          </div>
                        )}
                      </div>

                      <Card className="bg-slate-900/40 border-slate-800/80">
                        <CardContent className="pt-4 text-xs text-slate-400 space-y-3 leading-relaxed">
                          <div className="flex items-center gap-1.5 font-bold text-slate-350">
                            <Info className="w-3.5 h-3.5 text-cyan-400" />
                            <span>Natural Radiation & Heat Convection Analysis:</span>
                          </div>
                          <p>
                            In sealed non-ventilated enclosures, heat escapes via surface convection and radiation:
                          </p>
                          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                            <Latex math={"\\Delta T_{rise} = \\frac{P_{in}}{A_{enc} \\cdot K_{eff}}"} block />
                            <Latex math={`\\Delta T_{rise} = \\frac{${encIn.p_in}}{${encOut.area_m2.toFixed(4)} \\cdot \\left(\\frac{${encIn.k_factor}}{1000}\\right)} = ${encOut.temp_rise.toFixed(1)} \\text{ K}`} block />
                          </div>
                          <div className="text-[10px] text-slate-400 space-y-1 bg-slate-950/10 p-2.5 rounded-lg border border-slate-800/40 mt-2">
                            <div className="font-semibold text-slate-300">Symbol Definitions:</div>
                            <div>• <Latex math={"\\Delta T_{rise}"} />: Average temperature rise over external ambient (K)</div>
                            <div>• <Latex math={"P_{in}"} />: Total internal heat dissipation (W)</div>
                            <div>• <Latex math={"A_{enc}"} />: Total exterior enclosure surface area (m²)</div>
                            <div>• <Latex math={"K_{eff}"} />: Effective overall heat transfer coefficient (W/m²·K)</div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* Tab 4: Transient Shock Results */}
                  {activeTab === 'transient' && transOut && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Total Shock Energy E_shock</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {transOut.energy_j.toFixed(0)} <span className="text-xs text-slate-400">J</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Heatsink Thermal Cap C_th</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {transOut.c_th.toFixed(2)} <span className="text-xs text-slate-400">J/K</span>
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Adiabatic Temp Rise ΔT_trans</span>
                          <span className="text-xl font-bold text-pink-400 font-mono">
                            +{transOut.temp_rise.toFixed(1)} <span className="text-xs text-slate-400">K</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Shock End Peak Temp T_end</span>
                          <span className="text-xl font-bold text-orange-400 font-mono">
                            {transOut.t_end.toFixed(1)} <span className="text-xs text-slate-400">°C</span>
                          </span>
                        </div>
                      </div>

                      {/* DRC Alert Panel */}
                      <div className="space-y-2">
                        {transOut.t_end > steadyIn.t_j_max ? (
                          <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2.5 text-xs text-red-400">
                            <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="font-bold block">⚠️ Transient Overload Overtemperature DRC Alert</span>
                              <span className="mt-1 block">After a {transIn.duration_s}s pulse of {transIn.p_shock}W, predicted peak temperature will reach {transOut.t_end.toFixed(1)}°C, exceeding max allowable {steadyIn.t_j_max}°C! Heatsink thermal mass ({transOut.c_th.toFixed(2)} J/K) is insufficient. Increase heatsink mass or restrict pulse duration.</span>
                            </div>
                          </div>
                        ) : (
                          <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-2.5 text-xs text-emerald-400">
                            <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                            <span>✅ Transient overload safe: Peak end temperature is {transOut.t_end.toFixed(1)}°C, within allowable limits.</span>
                          </div>
                        )}
                      </div>

                      <Card className="bg-slate-900/40 border-slate-800/80">
                        <CardContent className="pt-4 text-xs text-slate-400 leading-relaxed space-y-3">
                          <div className="flex items-center gap-1.5 font-bold text-slate-350">
                            <Info className="w-3.5 h-3.5 text-cyan-400" />
                            <span>Transient Overload Thermal Formulation:</span>
                          </div>
                          <p>
                            Under short duration pulses, thermal mass absorbs energy adiabatically:
                          </p>
                          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                            <Latex math={"\\Delta T_{trans} = \\frac{E_{shock}}{C_{th}} = \\frac{P_{shock} \\cdot t_{duration}}{C_{spec} \\cdot m_{mass} \\cdot 10^{-3}}"} block />
                            <Latex math={`\\Delta T_{trans} = \\frac{${transOut.energy_j.toFixed(0)}}{${transOut.c_th.toFixed(2)}} = ${transOut.temp_rise.toFixed(1)} \\text{ K}`} block />
                          </div>
                          <div className="text-[10px] text-slate-400 space-y-1 bg-slate-950/10 p-2.5 rounded-lg border border-slate-800/40 mt-2">
                            <div className="font-semibold text-slate-300">Symbol Definitions:</div>
                            <div>• <Latex math={"\\Delta T_{trans}"} />: Adiabatic temperature rise (K)</div>
                            <div>• <Latex math={"E_{shock}"} />: Energy injected during overload (J)</div>
                            <div>• <Latex math={"C_{th}"} />: Heatsink heat capacity (J/K) = <Latex math={"C_{spec} \\cdot m"} /></div>
                            <div>• <Latex math={"T_{end}"} />: Peak temperature at end of shock (°C)</div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* Tab 5: System Airflow Results */}
                  {activeTab === 'sysair' && sysAirOut && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Required Airflow CFM_total</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {sysAirOut.cfm_total.toFixed(2)} <span className="text-xs text-slate-400">CFM</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Required Airflow CMM_total</span>
                          <span className="text-xl font-bold text-cyan-300 font-mono">
                            {sysAirOut.cmm_total.toFixed(2)} <span className="text-xs text-slate-400">CMM</span>
                          </span>
                        </div>
                        <div className="glass-card p-4 rounded-xl border border-slate-850/80 bg-slate-900/30 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-400 font-medium">Altitude Derating Factor Kp</span>
                          <span className="text-xl font-bold text-emerald-400 font-mono">
                            {sysAirOut.alt_factor.toFixed(3)}
                          </span>
                        </div>
                      </div>

                      <Card className="bg-slate-900/40 border-slate-800/80">
                        <CardContent className="pt-4 text-xs text-slate-400 leading-relaxed space-y-3">
                          <p>
                            At high altitude, air density <Latex math="\rho" /> decreases, reducing thermal mass per unit volume. The calculated airflow is compensated by the **Kp Altitude Correction Factor**.
                          </p>
                          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 text-[11px]">
                            <Latex math={"CFM = \\frac{1.756 \\cdot P_{loss}}{\\Delta T_{allowed}} \\cdot (1 + f_{margin}) \\cdot K_p"} block />
                          </div>
                          <div className="text-[10px] text-slate-400 space-y-1 bg-slate-950/10 p-2.5 rounded-lg border border-slate-800/40 mt-2">
                            <div className="font-semibold text-slate-300">Symbol Definitions:</div>
                            <div>• <Latex math={"CFM"} />: Required airflow (Cubic Feet per Minute)</div>
                            <div>• <Latex math={"P_{loss}"} />: Total heat dissipated by internal hardware (W)</div>
                            <div>• <Latex math={"\\Delta T_{allowed}"} />: Max allowable intake-to-exhaust temperature delta (K)</div>
                            <div>• <Latex math={"f_{margin}"} />: Design airflow margin (e.g. 20% = 0.20)</div>
                            <div>• <Latex math={"K_p"} />: Altitude density correction multiplier</div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </div>
              )}

              {key === 'schematic' && activeTab === 'steady' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <Info className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold text-white">1D Equivalent Thermal Circuit Schematic</span>
                  </div>
                  <div className="flex justify-center bg-slate-950/20 py-4 rounded-lg">
                    <svg viewBox="0 0 720 180" className="w-full max-w-xl h-auto text-slate-450">
                      <line x1="80" y1="90" x2="640" y2="90" stroke="#334155" strokeWidth="2.5" />
                      <circle cx="80" cy="90" r="6" fill="#f43f5e" className={hoveredNode === 'tj' ? 'stroke-white stroke-2' : ''} onMouseEnter={() => setHoveredNode('tj')} onMouseLeave={() => setHoveredNode(null)} />
                      <text x="80" y="70" textAnchor="middle" fill="#f43f5e" className="text-[11px] font-bold">Node Tj ({Tj}°C)</text>

                      {/* R_jc resistor */}
                      <path d="M 120 90 L 130 75 L 145 105 L 160 75 L 175 105 L 190 75 L 200 90" fill="none" stroke="#e11d48" strokeWidth="1.8" />
                      <text x="160" y="60" textAnchor="middle" fill="#e11d48" className="text-[10px] font-bold">R_jc = {steadyIn.r_jc} K/W</text>

                      <circle cx="240" cy="90" r="6" fill="#ec4899" className={hoveredNode === 'tc' ? 'stroke-white stroke-2' : ''} onMouseEnter={() => setHoveredNode('tc')} onMouseLeave={() => setHoveredNode(null)} />
                      <text x="240" y="70" textAnchor="middle" fill="#ec4899" className="text-[11px] font-bold">Case Tc ({Tc}°C)</text>

                      {/* R_cs resistor */}
                      <path d="M 280 90 L 290 75 L 305 105 L 320 75 L 335 105 L 350 75 L 360 90" fill="none" stroke="#f59e0b" strokeWidth="1.8" />
                      <text x="320" y="60" textAnchor="middle" fill="#f59e0b" className="text-[10px] font-bold">R_cs = {steadyIn.r_cs} K/W</text>

                      <circle cx="400" cy="90" r="6" fill="#eab308" className={hoveredNode === 'ts' ? 'stroke-white stroke-2' : ''} onMouseEnter={() => setHoveredNode('ts')} onMouseLeave={() => setHoveredNode(null)} />
                      <text x="400" y="70" textAnchor="middle" fill="#eab308" className="text-[11px] font-bold">Heatsink Ts ({Ts}°C)</text>

                      {/* R_sa resistor */}
                      <path d="M 440 90 L 450 75 L 465 105 L 480 75 L 495 105 L 510 75 L 520 90" fill="none" stroke="#06b6d4" strokeWidth="1.8" />
                      <text x="480" y="60" textAnchor="middle" fill="#06b6d4" className="text-[10px] font-bold">R_sa ≤ {steadyOut?.r_sa_max.toFixed(3)} K/W</text>

                      <circle cx="560" cy="90" r="6" fill="#10b981" className={hoveredNode === 'ta' ? 'stroke-white stroke-2' : ''} onMouseEnter={() => setHoveredNode('ta')} onMouseLeave={() => setHoveredNode(null)} />
                      <text x="560" y="70" textAnchor="middle" fill="#10b981" className="text-[11px] font-bold">Ambient Ta ({Ta}°C)</text>

                      <text x="320" y="145" textAnchor="middle" fill="#64748b" className="text-[10px]">Heat Dissipation Flow: Pd = {steadyIn.p_diss} W</text>
                    </svg>
                  </div>
                </div>
              )}

              {key === 'bom' && activeTab === 'steady' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white">Commercial Standard Extrusion Heatsink Recommendations</span>
                  </div>
                  {filteredExtrusions.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-[11px] text-slate-300">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400">
                            <th className="py-2">Part Number</th>
                            <th className="py-2">Dimensions (W x H x L mm)</th>
                            <th className="py-2">Material</th>
                            <th className="py-2 text-right">Thermal R_sa</th>
                            <th className="py-2">Type Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredExtrusions.map((item, idx) => (
                            <tr key={idx} className="border-b border-slate-850 hover:bg-slate-900/30 transition-colors">
                              <td className="py-2 font-bold text-cyan-400">{item.name}</td>
                              <td className="py-2">{item.width} x {item.height} x {item.length}</td>
                              <td className="py-2">{item.material}</td>
                              <td className="py-2 text-right font-mono text-green-400 font-semibold">{item.r_sa.toFixed(2)} K/W</td>
                              <td className="py-2 text-[10px] text-slate-400">{item.type}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-6 text-xs text-slate-500 italic">
                      ⚠️ Current power dissipation exceeds natural convection limits (requires Rsa ≤ {steadyOut?.r_sa_max.toFixed(3)} K/W)! Forced air or liquid cooling strongly recommended.
                    </div>
                  )}

                  <div className="mt-4 pt-3 border-t border-slate-850 flex flex-col gap-1.5 text-[10px] text-slate-400">
                    <div className="font-semibold text-slate-300">Physical Thermal Equation Derivation:</div>
                    <Latex math={"T_J = T_A + P_D \\cdot (R_{jc} + R_{cs} + R_{sa})"} block />
                    {steadyOut && <Latex math={`R_{sa} \\le \\frac{T_{J,max} - T_A}{P_D} - R_{jc} - R_{cs} = \\frac{${Tj} - ${Ta}}{${steadyIn.p_diss}} - ${steadyIn.r_jc} - ${steadyIn.r_cs} = ${steadyOut.r_sa_max.toFixed(3)} \\text{ K/W}`} block />}
                    
                    <div className="text-[9px] text-slate-400 space-y-1 bg-slate-950/10 p-2.5 rounded-lg border border-slate-800/40 mt-2">
                      <div className="font-semibold text-slate-300">Symbol Definitions:</div>
                      <div className="grid grid-cols-2 gap-x-4">
                        <div>• <Latex math={"T_J"} />: Junction temperature (°C)</div>
                        <div>• <Latex math={"T_A"} />: Operating ambient temperature (°C)</div>
                        <div>• <Latex math={"P_D"} />: Dissipated power (W)</div>
                        <div>• <Latex math={"R_{jc}"} />: Junction-to-case thermal resistance (K/W)</div>
                        <div>• <Latex math={"R_{cs}"} />: Case-to-heatsink contact resistance (K/W)</div>
                        <div>• <Latex math={"R_{sa}"} />: Heatsink thermal resistance (K/W)</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {key === 'chart' && (activeTab === 'forced' || activeTab === 'transient' || activeTab === 'sysair') && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white">
                      {activeTab === 'forced' && 'Forced Convection Thermal Resistance vs Air Velocity'}
                      {activeTab === 'transient' && 'Transient Overload Junction Temperature Response'}
                      {activeTab === 'sysair' && 'Required System Airflow vs Allowed Temperature Rise'}
                    </span>
                  </div>
                  <div className="h-[280px]">
                    <ReactECharts
                      option={
                        activeTab === 'forced' ? getForcedChartOption() : 
                        activeTab === 'transient' ? getTransientChartOption() : 
                        getSysAirChartOption()
                      }
                      notMerge={true}
                      style={{ height: '100%', width: '100%' }}
                    />
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
