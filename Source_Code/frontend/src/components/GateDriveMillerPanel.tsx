import { useTabHistoryState } from '../lib/tabHistory';
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
  CheckCircle2,
  ShieldAlert,
  FileSpreadsheet
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

interface BomItem {
  designator: string;
  calcValue: string;
  stdValue: string;
  error: string;
  type: string;
  desc: string;
}

export default function GateDriveMillerPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: (mod: string | null) => void }) {
  const [activeSubTab, setActiveSubTab] = useTabHistoryState<'miller' | 'deadtime'>('miller', 'activeSubTab');
  const activeSubTabRef = useRef(activeSubTab);
  useEffect(() => { activeSubTabRef.current = activeSubTab; }, [activeSubTab]);

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
    panelKey: 'layout_gatedrivemillerpanel_v3',
    activeTab: activeSubTab,
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 850, results: 950 }
  });

  // Tab 1: Miller Turn-on State
  const [millerPreset, setMillerPreset] = useState<string>('C3M0065090D');
  const [vBus, setVBus] = useState<number>(400.0);
  const [dvDt, setDvDt] = useState<number>(50.0); // V/ns
  const [cGd, setCGd] = useState<number>(6.0);    // pF
  const [cGs, setCGs] = useState<number>(220.0);  // pF
  const [rgOffExt, setRgOffExt] = useState<number>(4.7); // Ohm
  const [rgOffInt, setRgOffInt] = useState<number>(1.2); // Ohm
  const [rDriverOff, setRDriverOff] = useState<number>(1.5); // Ohm
  const [lGate, setLGate] = useState<number>(5.0);  // nH
  const [vGsOff, setVGsOff] = useState<number>(-3.0); // V
  const [vTh, setVTh] = useState<number>(2.1);      // V

  const [millerRes, setMillerRes] = useState<any>(null);
  const [millerError, setMillerError] = useState<string | null>(null);
  const [millerChartOpt, setMillerChartOpt] = useState<any>({});

  const millerPresets: Record<string, any> = {
    'C3M0065090D': {
      desc: 'Wolfspeed 900V SiC MOSFET (TO-247-3)',
      cGd: 6.0, cGs: 240.0, rgOffInt: 1.2, vTh: 2.1, vGsOff: -3.0
    },
    'IMZ120R030M1H': {
      desc: 'Infineon 1200V CoolSiC (TO-247-4L)',
      cGd: 5.0, cGs: 320.0, rgOffInt: 1.0, vTh: 2.25, vGsOff: -2.0
    },
    'GS66508B': {
      desc: 'GaN Systems 650V/30A GaN HEMT (Bottom Cool)',
      cGd: 2.0, cGs: 160.0, rgOffInt: 0.8, vTh: 1.7, vGsOff: 0.0
    }
  };

  useEffect(() => {
    if (millerPreset !== 'Custom' && millerPresets[millerPreset]) {
      const p = millerPresets[millerPreset];
      setCGd(p.cGd);
      setCGs(p.cGs);
      setRgOffInt(p.rgOffInt);
      setVTh(p.vTh);
      setVGsOff(p.vGsOff);
    }
  }, [millerPreset]);

  const fetchMiller = async () => {
    setMillerError(null);
    try {
      const response = await apiFetch('/api/calculate/gate_drive_miller/miller', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_bus: vBus,
          dv_dt_v_ns: dvDt,
          c_gd_pf: cGd,
          c_gs_pf: cGs,
          r_g_off_ext: rgOffExt,
          r_g_off_int: rgOffInt,
          r_driver_off: rDriverOff,
          l_g_nh: lGate,
          v_gs_off: vGsOff,
          v_th: vTh,
          sim_steps: 400
        }),
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Miller verification failed');
      }

      const data = await response.json();
      setMillerRes(data);
      renderMillerChart(data);
    } catch (e: any) {
      setMillerError(e.message);
    }
  };

  const renderMillerChart = (data: any) => {
    const option = {
      backgroundColor: 'transparent',
      title: {
        text: 'Induced Gate Voltage Vgs Transient Oscillation Waveform',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        formatter: (params: any) => {
          const t = params[0].axisValue;
          const v = params[0].data;
          return `Time: ${t} ns<br/>Vgs: <span class="font-bold text-sky-400">${v} V</span>`;
        }
      },
      grid: { left: '10%', right: '5%', bottom: '15%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.t_ns.map((t: number) => parseFloat(t.toFixed(2))),
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 'ns',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 }
      },
      yAxis: {
        type: 'value',
        name: 'Vgs (V)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }
      },
      series: [
        {
          name: 'Vgs',
          type: 'line',
          data: data.vgs_v.map((v: number) => parseFloat(v.toFixed(2))),
          smooth: true,
          lineStyle: { color: '#38bdf8', width: 2 },
          showSymbol: false,
          markLine: {
            silent: true,
            lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 },
            label: {
              formatter: `Threshold Vth = ${vTh}V`,
              position: 'insideEndTop',
              color: '#f87171',
              fontSize: 9
            },
            data: [{ yAxis: vTh }]
          }
        }
      ]
    };
    setMillerChartOpt(option);
  };

  // Tab 2: Deadtime Optimization & ZVS State
  const [fswKHz, setFswKHz] = useState<number>(100.0);
  const [iOut, setIOut] = useState<number>(10.0);
  const [vSd, setVSd] = useState<number>(3.0);
  const [cOss, setCOss] = useState<number>(150.0);
  const [eOnRef, setEOnRef] = useState<number>(80.0);
  const [eOnIRef, setEOnIRef] = useState<number>(10.0);
  const [tDeadAct, setTDeadAct] = useState<number>(100.0);

  const [deadtimeRes, setDeadtimeRes] = useState<any>(null);
  const [deadtimeError, setDeadtimeError] = useState<string | null>(null);
  const [deadtimeChartOpt, setDeadtimeChartOpt] = useState<any>({});

  const fetchDeadtime = async () => {
    setDeadtimeError(null);
    try {
      const response = await apiFetch('/api/calculate/gate_drive_miller/deadtime_opt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          t_dead_ns: tDeadAct,
          fsw_hz: fswKHz * 1000.0,
          i_out_a: iOut,
          v_sd_v: vSd,
          v_bus: vBus,
          c_oss_pf: cOss,
          e_on_ref_uj: eOnRef,
          e_on_current_ref: eOnIRef
        }),
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Deadtime optimization failed');
      }

      const data = await response.json();
      setDeadtimeRes(data);
      renderDeadtimeChart(data);
    } catch (e: any) {
      setDeadtimeError(e.message);
    }
  };

  const renderDeadtimeChart = (data: any) => {
    const xVals = data.t_dead_scan.map((t: number) => Math.round(t));
    const option = {
      backgroundColor: 'transparent',
      title: {
        text: 'Total Dissipation & Component Losses vs Deadtime',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['Total Loss (W)', 'Body Diode Loss (W)', 'Switching Loss (W)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '10%', right: '5%', bottom: '15%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: xVals,
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 'ns',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 }
      },
      yAxis: {
        type: 'value',
        name: 'Loss (W)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }
      },
      series: [
        {
          name: 'Total Loss (W)',
          type: 'line',
          data: data.p_total_w.map((v: number) => parseFloat(v.toFixed(2))),
          smooth: true,
          lineStyle: { color: '#38bdf8', width: 2 },
          showSymbol: false,
          markLine: {
            silent: true,
            lineStyle: { color: '#a855f7', type: 'dashed', width: 1.5 },
            label: {
              formatter: `Optimal Deadtime: ${Math.round(data.t_opt_ns)}ns`,
              position: 'insideEndTop',
              color: '#c084fc',
              fontSize: 9
            },
            data: [{ xAxis: xVals.findIndex((x: number) => x >= data.t_opt_ns).toString() }]
          }
        },
        {
          name: 'Body Diode Loss (W)',
          type: 'line',
          data: data.p_dead_w.map((v: number) => parseFloat(v.toFixed(2))),
          smooth: true,
          lineStyle: { color: '#818cf8', width: 1.5 },
          showSymbol: false
        },
        {
          name: 'Switching Loss (W)',
          type: 'line',
          data: data.p_sw_w.map((v: number) => parseFloat(v.toFixed(2))),
          smooth: true,
          lineStyle: { color: '#ef4444', width: 1.5 },
          showSymbol: false
        }
      ]
    };
    setDeadtimeChartOpt(option);
  };

  useEffect(() => {
    if (activeSubTab === 'miller') {
      fetchMiller();
    }
  }, [vBus, dvDt, cGd, cGs, rgOffExt, rgOffInt, rDriverOff, lGate, vGsOff, vTh, millerPreset, activeSubTab]);

  useEffect(() => {
    if (activeSubTab === 'deadtime') {
      fetchDeadtime();
    }
  }, [tDeadAct, fswKHz, iOut, vSd, vBus, cOss, eOnRef, eOnIRef, activeSubTab]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('target_gate_drive_miller_data');
      if (raw) {
        const data = JSON.parse(raw);
        if (data.tab === 'miller' && data.params) {
          const p = data.params;
          setMillerPreset('Custom');
          setTimeout(() => {
            if (p.v_bus !== undefined) setVBus(p.v_bus);
            if (p.c_gd !== undefined) setCGd(p.c_gd);
            if (p.c_gs !== undefined) setCGs(p.c_gs);
            if (p.v_th !== undefined) setVTh(p.v_th);
            if (p.rg_off_int !== undefined) setRgOffInt(p.rg_off_int);
            if (p.v_gs_off !== undefined) setVGsOff(p.v_gs_off);
          }, 50);
        }
        localStorage.removeItem('target_gate_drive_miller_data');
      }
    } catch (e) {
      console.error("Failed to parse target gate drive miller data", e);
    }
  }, []);

  const getMatchedBom = (): BomItem[] => {
    const items: BomItem[] = [];
    if (activeSubTab === 'miller' && rgOffExt > 0) {
      const match = findClosestStandard(rgOffExt, E96);
      items.push({
        designator: 'Rg_ext',
        calcValue: `${rgOffExt.toFixed(1)} Ω`,
        stdValue: `${match.value.toFixed(1)} Ω`,
        error: `${match.error > 0 ? '+' : ''}${match.error}%`,
        type: 'Resistor (E96)',
        desc: 'External turn-off gate damping resistor to suppress parasitic oscillation and limit dv/dt'
      });
    }
    return items;
  };

  const matchedBom = getMatchedBom();

  return (
    <div className="h-full w-full flex flex-col overflow-hidden bg-[#070a13] p-1">
      <div className="flex justify-between items-center bg-slate-900/30 p-2.5 rounded-xl border border-slate-800/80 mb-2">
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
              Gate Drive & Miller Clamp Verification
            </h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Verify high-speed SiC/GaN dv/dt induced Miller turn-on; evaluate deadtime losses and zero-voltage switching (ZVS) criteria.
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

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 min-h-0">
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
                <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 p-4">
                  <Card className="bg-slate-950/40 border-slate-800/80 p-4">
                    <div className="flex items-center justify-between mb-3 border-b border-slate-800/60 pb-2">
                      <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wide flex items-center gap-2">
                        Physical Design Specifications
                      </h3>
                      {activeSubTab === 'miller' && (
                        <select
                          value={millerPreset}
                          onChange={(e) => setMillerPreset(e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 outline-none focus:border-blue-500"
                        >
                          <option value="C3M0065090D">Wolfspeed C3M</option>
                          <option value="IMZ120R030M1H">Infineon CoolSiC</option>
                          <option value="GS66508B">GaN Systems HEMT</option>
                          <option value="Custom">Custom</option>
                        </select>
                      )}
                    </div>

                    <div className="flex gap-1 overflow-x-auto pb-1 mb-4 border-b border-slate-800/60">
                      {(['miller', 'deadtime'] as const).map((tab) => (
                        <button
                          key={tab}
                          onClick={() => { setActiveSubTab(tab); }}
                          className={`px-3 py-1 text-[10px] font-semibold rounded-t transition-all border-b-2 ${
                            activeSubTab === tab
                              ? 'border-b-blue-500 text-blue-400 font-bold bg-slate-900/20'
                              : 'border-b-transparent text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          {tab === 'miller' ? 'Miller Verification' : 'Deadtime & ZVS'}
                        </button>
                      ))}
                    </div>

                    <div className="space-y-4">
                      {activeSubTab === 'miller' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Power Stage & Thresholds
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Bus Voltage Vbus [V]</label>
                              <input type="number" step="10" value={vBus} onChange={(e) => setVBus(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Threshold Voltage Vth [V]</label>
                              <input type="number" step="0.1" value={vTh} onChange={(e) => setVTh(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div className="col-span-2">
                              <label className="text-[10px] text-slate-400 block mb-1">Switching Slew Rate dv/dt [V/ns]</label>
                              <input type="number" step="5" value={dvDt} onChange={(e) => setDvDt(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeSubTab === 'miller' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Device Junction Capacitances
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Reverse Transfer Cgd [pF]</label>
                              <input type="number" step="1" value={cGd} onChange={(e) => setCGd(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Input Capacitance Cgs [pF]</label>
                              <input type="number" step="10" value={cGs} onChange={(e) => setCGs(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeSubTab === 'miller' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            External Gate Resistor
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">External Pull-down Rg_off_ext [Ω]</label>
                            <input type="number" step="0.5" value={rgOffExt} onChange={(e) => setRgOffExt(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                          </div>
                        </div>
                      )}

                      {activeSubTab === 'miller' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Internal & Driver Resistances
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Internal Gate Resistance Rg_int [Ω]</label>
                              <input type="number" step="0.1" value={rgOffInt} onChange={(e) => setRgOffInt(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Driver Sink Resistance R_drv_off [Ω]</label>
                              <input type="number" step="0.5" value={rDriverOff} onChange={(e) => setRDriverOff(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeSubTab === 'miller' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Loop Parasitic Inductance
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Gate Loop Inductance L_gate [nH]</label>
                            <input type="number" step="1" value={lGate} onChange={(e) => setLGate(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                          </div>
                        </div>
                      )}

                      {activeSubTab === 'miller' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Driver Turn-off Bias
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Negative Off-State Bias Vgs_off [V]</label>
                            <input type="number" step="1" value={vGsOff} onChange={(e) => setVGsOff(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                          </div>
                        </div>
                      )}

                      {activeSubTab === 'deadtime' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Switching Frequency & Output Current
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Switching Frequency Fsw [kHz]</label>
                              <input type="number" step="10" value={fswKHz} onChange={(e) => setFswKHz(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Inductive Peak Current Iout [A]</label>
                              <input type="number" step="1.0" value={iOut} onChange={(e) => setIOut(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Diode Forward Drop Vsd [V]</label>
                              <input type="number" step="0.5" value={vSd} onChange={(e) => setVSd(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Configured Deadtime t_dead [ns]</label>
                              <input type="number" step="10" value={tDeadAct} onChange={(e) => setTDeadAct(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeSubTab === 'deadtime' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Output Capacitance Coss & ZVS
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="col-span-2">
                              <label className="text-[10px] text-slate-400 block mb-1">Equivalent Coss [pF]</label>
                              <input type="number" step="10" value={cOss} onChange={(e) => setCOss(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Reference Eon [μJ]</label>
                              <input type="number" step="10" value={eOnRef} onChange={(e) => setEOnRef(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Eon Current Ref I_ref [A]</label>
                              <input type="number" step="5" value={eOnIRef} onChange={(e) => setEOnIRef(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin space-y-6 p-4">
                  {activeSubTab === 'miller' && millerRes && (
                    (millerRes.is_safe ?? true) ? (
                      <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                        <span>Gate drive characteristics are safe: Peak Miller transient voltage of {(millerRes.vgs_peak_v ?? 0).toFixed(2)} V does not exceed threshold {vTh} V, preserving a {(millerRes.safety_margin_v ?? 0).toFixed(2)} V safety margin.</span>
                      </div>
                    ) : (
                      <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400">
                        <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="font-bold block">Miller Cross-Conduction Shoot-Through Risk</span>
                          <span className="mt-1 block">Simulation indicates the low-side gate induced transient spike of {(millerRes.vgs_peak_v ?? 0).toFixed(2)} V breaches threshold {vTh} V. This causes instantaneous half-bridge shoot-through. Reduce external pull-down Rg_ext, increase negative bias (e.g. -5V), or implement active Miller clamp circuitry.</span>
                        </div>
                      </div>
                    )
                  )}

                  {activeSubTab === 'deadtime' && deadtimeRes && (
                    (deadtimeRes.zvs_success ?? false) ? (
                      <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                        <span>ZVS soft-switching verified: Configured deadtime of {tDeadAct} ns fully discharges Coss, minimizing turn-on losses.</span>
                      </div>
                    ) : (
                      <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-start gap-2 text-xs text-yellow-300">
                        <ShieldAlert className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="font-bold block">ZVS Soft-Switching Failure Risk</span>
                          <span className="mt-1 block">Configured deadtime of {tDeadAct} ns is insufficient to fully discharge Coss before turn-on (minimum required ZVS deadtime is {Math.round(deadtimeRes.t_zvs_ns ?? 0)} ns), resulting in hard-switching losses ({(deadtimeRes.p_sw_act_w ?? 0).toFixed(2)} W). Consider adjusting deadtime closer to optimal {Math.round(deadtimeRes.t_opt_ns ?? 0)} ns.</span>
                        </div>
                      </div>
                    )
                  )}

                  {activeSubTab === 'miller' && millerRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Peak Induced Vgs</span>
                        <div className={`text-sm font-bold font-mono ${(millerRes.is_safe ?? true) ? 'text-emerald-400' : 'text-red-400'}`}>
                          {(millerRes.vgs_peak_v ?? 0).toFixed(2)} V
                        </div>
                        <span className="text-[8px] text-slate-500">Maximum transient gate surge</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Time Constant Tau</span>
                        <div className="text-sm font-bold text-slate-200 font-mono">
                          {(millerRes.tau_ns ?? 0).toFixed(2)} ns
                        </div>
                        <span className="text-[8px] text-slate-500">Gate loop RC constant</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Gate Threshold Vth</span>
                        <div className="text-sm font-bold text-slate-200 font-mono">
                          {vTh} V
                        </div>
                        <span className="text-[8px] text-slate-500">Turn-on threshold voltage</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Damping Ratio</span>
                        <div className="text-sm font-bold text-emerald-400 font-mono">
                          {(millerRes.damping_ratio ?? 0).toFixed(3)}
                        </div>
                        <span className="text-[8px] text-slate-500">&lt;1 indicates underdamped ringing</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Off-State Bias</span>
                        <div className="text-sm font-bold text-purple-400 font-mono">
                          {vGsOff} V
                        </div>
                        <span className="text-[8px] text-slate-500">Negative gate turn-off rail</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Safety Margin</span>
                        <div className={`text-sm font-bold font-mono ${(millerRes.is_safe ?? true) ? 'text-emerald-400' : 'text-red-400'}`}>
                          {(millerRes.safety_margin_v ?? 0).toFixed(2)} V
                        </div>
                        <span className="text-[8px] text-slate-500">Vth - Vgs_peak margin</span>
                      </div>
                    </div>
                  )}

                  {activeSubTab === 'deadtime' && deadtimeRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Deadtime Loss P_dead</span>
                        <div className="text-sm font-bold text-rose-500 font-mono">
                          {(deadtimeRes.p_dead_act_w ?? 0).toFixed(2)} W
                        </div>
                        <span className="text-[8px] text-slate-500">Body diode conduction loss</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Switching Loss P_sw</span>
                        <div className="text-sm font-bold text-slate-200 font-mono">
                          {(deadtimeRes.p_sw_act_w ?? 0).toFixed(2)} W
                        </div>
                        <span className="text-[8px] text-slate-500">Residual Coss discharge loss</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Total Stage Loss</span>
                        <div className="text-sm font-bold text-slate-200 font-mono">
                          {(deadtimeRes.p_total_act_w ?? 0).toFixed(2)} W
                        </div>
                        <span className="text-[8px] text-slate-500">Combined diode + switch loss</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Optimal Deadtime</span>
                        <div className="text-sm font-bold text-emerald-400 font-mono">
                          {Math.round(deadtimeRes.t_opt_ns ?? 0)} ns
                        </div>
                        <span className="text-[8px] text-slate-500">Best balance between ZVS and conduction</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Minimum ZVS Window</span>
                        <div className="text-sm font-bold text-purple-400 font-mono">
                          {Math.round(deadtimeRes.t_zvs_ns ?? 0)} ns
                        </div>
                        <span className="text-[8px] text-slate-500">Min time required to discharge Coss</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/30 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Hard-Switch Ratio</span>
                        <div className="text-sm font-bold text-rose-500 font-mono">
                          {(((deadtimeRes.p_sw_act_w ?? 0) / (deadtimeRes.p_total_act_w || 1)) * 100).toFixed(1)} %
                        </div>
                        <span className="text-[8px] text-slate-500">Percentage of hard turn-on loss</span>
                      </div>
                    </div>
                  )}

                  {activeSubTab === 'miller' && (
                    <Card className="bg-slate-950/40 border-slate-800/80">
                      <CardHeader className="py-2 border-b border-slate-800">
                        <CardTitle className="text-[10px] font-bold text-slate-400">Gate Drive Equivalent Parasitic Circuit Model</CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 flex flex-col items-center">
                        <svg viewBox="0 0 520 130" className="w-full max-w-2xl h-auto text-slate-355 mx-auto select-none">
                          <line x1="20" y1="60" x2="50" y2="60" stroke="#475569" strokeWidth="1.5" />
                          <rect x="50" y="52" width="30" height="16" rx="2" fill="#0f172a" stroke="#ef4444" strokeWidth="1.5" />
                          <text x="65" y="63" textAnchor="middle" fill="#ef4444" className="text-[9px] font-mono font-bold">Rg</text>
                          <text x="65" y="42" textAnchor="middle" className="text-[7.5px] fill-slate-400 font-bold">Rg_ext+Rg_int</text>

                          <line x1="80" y1="60" x2="110" y2="60" stroke="#475569" strokeWidth="1.5" />
                          
                          <path d="M 110,60 C 113,53 117,53 120,60 C 123,53 127,53 130,60 C 133,53 137,53 140,60 C 143,53 147,53 150,60" fill="none" stroke="#eab308" strokeWidth="1.5" />
                          <text x="130" y="44" textAnchor="middle" fill="#eab308" className="text-[8.5px] font-mono font-bold">L_gate={lGate}nH</text>
                          <line x1="150" y1="60" x2="210" y2="60" stroke="#475569" strokeWidth="1.5" />

                          <circle cx="210" cy="60" r="3" fill="#38bdf8" />
                          <text x="210" y="48" textAnchor="middle" fill="#38bdf8" className="text-[9.5px] font-bold">G (Gate)</text>

                          <line x1="210" y1="60" x2="210" y2="78" stroke="#475569" strokeWidth="1.5" />
                          <line x1="195" y1="78" x2="225" y2="78" stroke="#38bdf8" strokeWidth="2" />
                          <line x1="195" y1="82" x2="225" y2="82" stroke="#38bdf8" strokeWidth="2" />
                          <line x1="210" y1="82" x2="210" y2="105" stroke="#475569" strokeWidth="1.5" />
                          <text x="235" y="85" fill="#38bdf8" className="text-[8.5px] font-mono font-bold">Cgs={cGs}pF</text>

                          <line x1="210" y1="60" x2="280" y2="60" stroke="#475569" strokeWidth="1.5" />
                          <line x1="280" y1="48" x2="280" y2="72" stroke="#a78bfa" strokeWidth="2" />
                          <line x1="284" y1="48" x2="284" y2="72" stroke="#a78bfa" strokeWidth="2" />
                          <line x1="284" y1="60" x2="350" y2="60" stroke="#475569" strokeWidth="1.5" />
                          <text x="282" y="38" textAnchor="middle" fill="#a78bfa" className="text-[8.5px] font-mono font-bold">Cgd={cGd}pF</text>

                          <circle cx="350" cy="60" r="3" fill="#f43f5e" />
                          <text x="350" y="48" textAnchor="middle" fill="#f43f5e" className="text-[9.5px] font-bold">D (Drain)</text>
                          <line x1="350" y1="60" x2="410" y2="60" stroke="#475569" strokeWidth="1.5" />
                          <text x="420" y="64" fill="#cbd5e1" className="text-[9px] font-mono font-bold">dv/dt={dvDt} V/ns</text>

                          <line x1="180" y1="105" x2="240" y2="105" stroke="#475569" strokeWidth="1.5" />
                          <line x1="200" y1="105" x2="220" y2="105" stroke="#475569" strokeWidth="1.5" />
                          <line x1="205" y1="109" x2="215" y2="109" stroke="#475569" strokeWidth="1.5" />
                          <line x1="208" y1="113" x2="212" y2="113" stroke="#475569" strokeWidth="1.5" />
                        </svg>
                      </CardContent>
                    </Card>
                  )}

                  {activeSubTab === 'miller' && (
                    <Card className="bg-slate-950/40 border-slate-800/80">
                      <CardHeader className="py-2 border-b border-slate-800">
                        <CardTitle className="text-[10px] font-bold text-slate-400">Gate Miller Surge Transient Waveform</CardTitle>
                      </CardHeader>
                      <CardContent className="p-3 bg-slate-950/40">
                        <div className="h-[240px] w-full">
                          {millerChartOpt.series ? (
                            <ReactECharts option={millerChartOpt} notMerge={true} style={{ height: '100%', width: '100%' }} />
                          ) : (
                            <div className="flex items-center justify-center h-full text-slate-500 text-xs">No transient simulation data</div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {activeSubTab === 'deadtime' && (
                    <div className="grid grid-cols-1 gap-6">
                      <Card className="bg-slate-950/40 border-slate-800/80">
                        <CardHeader className="py-2 border-b border-slate-800">
                          <CardTitle className="text-[10px] font-bold text-slate-400">Total Switching Loss vs Deadtime</CardTitle>
                        </CardHeader>
                        <CardContent className="p-3 bg-slate-950/40">
                          <div className="h-[220px] w-full">
                            {deadtimeChartOpt.series ? (
                              <ReactECharts option={deadtimeChartOpt} notMerge={true} style={{ height: '100%', width: '100%' }} />
                            ) : (
                              <div className="flex items-center justify-center h-full text-slate-500 text-xs">No sweep curve available</div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {activeSubTab === 'miller' && matchedBom && matchedBom.length > 0 && (
                    <Card className="bg-slate-950/40 border-slate-800/80">
                      <CardHeader className="py-2.5 border-b border-slate-800/80 flex flex-row items-center gap-1.5">
                        <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                        <CardTitle className="text-xs font-bold text-slate-200">Recommended E96 Gate Resistor BOM</CardTitle>
                      </CardHeader>
                      <CardContent className="p-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-[10px] text-slate-300 border-collapse">
                            <thead>
                              <tr className="bg-slate-900/60 border-b border-slate-800/80 text-left text-slate-400 font-semibold">
                                <th className="p-2 pl-3">Designator</th>
                                <th className="p-2">Target (Ω)</th>
                                <th className="p-2 text-blue-400">Recommended E96 (Ω)</th>
                                <th className="p-2">Error</th>
                                <th className="p-2">Type</th>
                                <th className="p-2 pr-3">Function</th>
                              </tr>
                            </thead>
                            <tbody>
                              {matchedBom.map((item: any, index: number) => (
                                <tr key={index} className={`border-b border-slate-900 ${index === 0 ? 'bg-blue-500/5' : 'text-slate-400'}`}>
                                  <td className="p-2 pl-3 font-mono font-bold text-slate-200">{item.designator}</td>
                                  <td className="p-2 font-mono">{item.calcValue}</td>
                                  <td className="p-2 font-mono text-blue-400 font-bold">{item.stdValue}</td>
                                  <td className="p-2 font-mono">{item.error}</td>
                                  <td className="p-2">{item.type}</td>
                                  <td className="p-2 pr-3 text-slate-400 leading-normal">{item.desc}</td>
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
