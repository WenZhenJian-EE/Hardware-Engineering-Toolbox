import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { useDragDeckLayout, DragDeck, DragCard } from './ui/LayoutEngine';
import {
  ArrowLeft,
  CheckCircle2,
  Compass,
  ShieldAlert
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
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-slate-300" : "inline-block text-xs"} />;
};

interface CtResponse {
  i_sec_rms: number;
  r_burden_ohm: number;
  p_burden_mw: number;
  b_op_t: number;
  is_saturated: boolean;
  drc_warnings: string[];
}

interface ShuntResponse {
  p_actual_w: number;
  t_final_c: number;
  temp_rise_c: number;
  drift_pct: number;
  err_amps: number;
  v_spike_mv: number;
  r_trace_mohm: number;
  pcb_err_pct: number;
  is_overloaded: boolean;
  drc_warnings: string[];
}

export default function CurrentShuntPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<'ct' | 'shunt'>('ct', 'activeTab');
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);

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
    panelKey: 'layout_currentshuntpanel_v4_' + activeTab,
    activeTab: activeTab,
    defaultCards: ['input', 'results', 'chart', 'schematic'],
    defaultColumns: {
      input: 'left',
      results: 'right',
      chart: 'right',
      schematic: 'right'
    },
    defaultSpans: {
      input: 4,
      results: 8,
      chart: 8,
      schematic: 8
    },
    defaultHeights: {
      input: 850,
      results: 380,
      chart: 420,
      schematic: 420
    }
  });

  const COMMON_CT_PRESETS = [
    { name: 'Precision General CT (1:1000)', ratio: 1000, ae: 20.0, bmax: 1.0, rsec: 8.0 },
    { name: 'High-Current Industrial CT (1:2000)', ratio: 2000, ae: 45.0, bmax: 1.2, rsec: 15.0 },
    { name: 'Miniature High-Frequency CT (1:500)', ratio: 500, ae: 10.0, bmax: 0.8, rsec: 4.5 }
  ];

  const COMMON_SHUNT_PRESETS = [
    { name: 'Precision Manganin Shunt (1mΩ, 3W, 50ppm)', rval: 1.0, prating: 3.0, tcr: 50.0, rth: 20.0, esl: 2.0 },
    { name: 'High-Current Copper Busbar (0.5mΩ, 10W, 30ppm)', rval: 0.5, prating: 10.0, tcr: 30.0, rth: 8.0, esl: 4.0 },
    { name: 'Ultra-Low-Ohmic Shunt (0.2mΩ, 5W, 75ppm)', rval: 0.2, prating: 5.0, tcr: 75.0, rth: 12.0, esl: 1.5 }
  ];

  const getCurrentShuntChartOption = () => {
    if (activeTab === 'ct') {
      const iSecRms = ctIpri / (ctRatio || 1);
      const points: [number, number][] = [];
      const currentRb = ctRes?.r_burden_ohm ?? 10.0;

      for (let rb = 0; rb <= 100; rb += 2) {
        const vCoreRms = iSecRms * (rb + ctRsec);
        const bOp = (vCoreRms * 1e6) / (4.44 * ctFreq * (ctRatio || 1) * ctAe);
        points.push([rb, parseFloat(bOp.toFixed(3))]);
      }

      const currentB = (iSecRms * (currentRb + ctRsec) * 1e6) / (4.44 * ctFreq * (ctRatio || 1) * ctAe);

      return {
        backgroundColor: 'transparent',
        title: {
          text: 'Core Flux Density B_op vs Burden Resistor Curve',
          textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' },
          left: 'center',
          top: 5
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: '#38bdf8',
          borderWidth: 1,
          textStyle: { color: '#e2e8f0', fontSize: 10 },
          extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
        },
        grid: { left: '12%', right: '12%', top: '20%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'value',
          name: 'Burden Resistance (Ω)',
          nameGap: 15,
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } },
          axisLine: { lineStyle: { color: '#334155' } },
          min: 0,
          max: 100
        },
        yAxis: {
          type: 'value',
          name: 'Core Flux Density B_op (T)',
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } },
          axisLine: { lineStyle: { color: '#334155' } }
        },
        series: [
          {
            name: 'Operating Flux Density',
            type: 'line',
            data: points,
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 3, color: '#38bdf8', shadowBlur: 8, shadowColor: 'rgba(56, 189, 248, 0.5)' },
            markLine: {
              symbol: 'none',
              data: [
                {
                  yAxis: ctBmax,
                  name: 'Saturation Threshold',
                  lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 }
                }
              ],
              label: {
                position: 'end',
                formatter: '{b}: {c} T',
                color: '#ef4444',
                fontSize: 8
              }
            },
            markPoint: {
              data: [
                {
                  coord: [currentRb, parseFloat(currentB.toFixed(3))],
                  name: 'Operating Point',
                  itemStyle: { color: '#f59e0b' }
                }
              ],
              label: {
                show: true,
                formatter: 'Operating Point\n{c} T',
                fontSize: 8,
                position: 'top',
                color: '#fff'
              }
            }
          }
        ]
      };
    } else if (activeTab === 'shunt' && shRes) {
      const points: [number, number][] = [];
      const iMax = shImax;

      const step = iMax > 0 ? iMax / 30 : 1;
      for (let i = 0; i <= iMax; i += step) {
        const power = Math.pow(i, 2) * (shRval * 1e-3);
        const tempRise = power * shRth;
        const drift = shTcr * 1e-6 * tempRise * 100;
        points.push([i, parseFloat(drift.toFixed(4))]);
      }

      const pcbErr = shRes.pcb_err_pct ?? 0.0;
      const pcbData = points.map(pt => [pt[0], parseFloat(pcbErr.toFixed(4))]);

      return {
        backgroundColor: 'transparent',
        title: {
          text: 'Self-Heating TCR Drift vs PCB Stray Copper Error',
          textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' },
          left: 'center',
          top: 5
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: '#10b981',
          borderWidth: 1,
          textStyle: { color: '#e2e8f0', fontSize: 10 },
          extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
        },
        legend: {
          data: ['TCR Thermal Drift (%)', 'PCB Non-Kelvin Error (%)'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          bottom: 5
        },
        grid: { left: '12%', right: '12%', top: '20%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'value',
          name: 'Load Current (A)',
          nameGap: 15,
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
          axisLine: { lineStyle: { color: '#334155' } }
        },
        yAxis: {
          type: 'value',
          name: 'Resistance Error (%)',
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
          axisLine: { lineStyle: { color: '#334155' } }
        },
        series: [
          {
            name: 'TCR Thermal Drift (%)',
            type: 'line',
            data: points,
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 3, color: '#f43f5e', shadowBlur: 8, shadowColor: 'rgba(244, 63, 94, 0.5)' }
          },
          {
            name: 'PCB Non-Kelvin Error (%)',
            type: 'line',
            data: pcbData,
            showSymbol: false,
            lineStyle: { width: 2, color: '#10b981', type: 'dashed' }
          }
        ]
      };
    }
    return {};
  };

  const [ctIpri, setCtIpri] = useState<number>(50.0);
  const [ctRatio, setCtRatio] = useState<number>(1000);
  const [ctFreq, setCtFreq] = useState<number>(50.0);
  const [ctVoutPk, setCtVoutPk] = useState<number>(1.65);
  const [ctAe, setCtAe] = useState<number>(20.0);
  const [ctBmax, setCtBmax] = useState<number>(1.2);
  const [ctRsec, setCtRsec] = useState<number>(10.0);

  const [ctRes, setCtRes] = useState<CtResponse | null>(null);
  const [ctLoading, setCtLoading] = useState<boolean>(false);
  const [ctError, setCtError] = useState<string | null>(null);

  const [shImax, setShImax] = useState<number>(50.0);
  const [shRval, setShRval] = useState<number>(1.0);
  const [shPrating, setShPrating] = useState<number>(3.0);
  const [shTcr, setShTcr] = useState<number>(50.0);
  const [shRth, setShRth] = useState<number>(20.0);
  const [shTamb, setShTamb] = useState<number>(25.0);
  const [shEsl, setShEsl] = useState<number>(3.0);
  const [shDidt, setShDidt] = useState<number>(0.1);
  const [shPcbL, setShPcbL] = useState<number>(0.0);
  const [shPcbW, setShPcbW] = useState<number>(5.0);

  const [shRes, setShRes] = useState<ShuntResponse | null>(null);
  const [shLoading, setShLoading] = useState<boolean>(false);
  const [shError, setShError] = useState<string | null>(null);

  const calculateCt = async () => {
    setCtLoading(true);
    setCtError(null);
    try {
      const payload = {
        i_pri_rms: ctIpri,
        n_ratio: ctRatio,
        f: ctFreq,
        v_out_pk: ctVoutPk,
        ae_mm2: ctAe,
        b_max: ctBmax,
        r_sec: ctRsec,
      };

      const response = await apiFetch('/api/calculate/current_shunt/ct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || 'CT calculation failed');
      }

      const data: CtResponse = await response.json();
      setCtRes(data);
    } catch (e: any) {
      setCtError(e.message);
    } finally {
      setCtLoading(false);
    }
  };

  const calculateShunt = async () => {
    setShLoading(true);
    setShError(null);
    try {
      const payload = {
        i_max: shImax,
        r_mohm: shRval,
        p_rating: shPrating,
        tcr: shTcr,
        r_theta: shRth,
        t_amb: shTamb,
        esl_nh: shEsl,
        didt_aus: shDidt,
        pcb_l: shPcbL,
        pcb_w: shPcbW,
      };

      const response = await apiFetch('/api/calculate/current_shunt/shunt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || 'Shunt calculation failed');
      }

      const data: ShuntResponse = await response.json();
      setShRes(data);
    } catch (e: any) {
      setShError(e.message);
    } finally {
      setShLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'ct') {
      calculateCt();
    }
  }, [ctIpri, ctRatio, ctFreq, ctVoutPk, ctAe, ctBmax, ctRsec, activeTab]);

  useEffect(() => {
    if (activeTab === 'shunt') {
      calculateShunt();
    }
  }, [shImax, shRval, shPrating, shTcr, shRth, shTamb, shEsl, shDidt, shPcbL, shPcbW, activeTab]);

  const getActiveError = () => {
    return activeTab === 'ct' ? ctError : shError;
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Header */}
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
            <h1 className="text-base font-bold text-white tracking-tight">Current Shunt & Transformer Verification</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Verify current transformer (CT) core saturation and burden resistor; evaluate shunt resistor self-heating TCR drift and non-Kelvin PCB trace errors.
            </p>
          </div>
        </div>
        <Button onClick={handleResetLayout} variant="outline" size="sm" className="bg-slate-900 border border-slate-800 text-slate-350 hover:bg-slate-800 text-[10px] rounded-lg">
          Reset Layout
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 gap-1 flex-shrink-0">
        <button
          onClick={() => setActiveTab('ct')}
          className={`px-4 py-2 bg-transparent border-0 border-b-2 text-[10px] font-semibold cursor-pointer transition-all ${
            activeTab === 'ct'
              ? 'text-cyan-400 border-cyan-400 font-bold'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Current Transformer (CT) Design & Sizing
        </button>
        <button
          onClick={() => setActiveTab('shunt')}
          className={`px-4 py-2 bg-transparent border-0 border-b-2 text-[10px] font-semibold cursor-pointer transition-all ${
            activeTab === 'shunt'
              ? 'text-cyan-400 border-cyan-400 font-bold'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Shunt Resistor Error & Thermal Analysis
        </button>
      </div>

      {getActiveError() && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2.5 text-xs text-rose-300 flex-shrink-0">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>Calculation Warning: {getActiveError()}</span>
        </div>
      )}

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 pr-1 min-h-0">
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
                    <span className="text-xs font-bold text-white">Input Operating Conditions</span>
                  </div>

                  <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/20 space-y-1.5 mb-2">
                    <span className="text-[9px] text-slate-400 block select-none">
                      {activeTab === 'ct' ? 'Commercial CT Presets:' : 'Commercial Shunt Resistor Presets:'}
                    </span>
                    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                      {activeTab === 'ct' ? (
                        COMMON_CT_PRESETS.map((preset, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setCtRatio(preset.ratio);
                              setCtAe(preset.ae);
                              setCtBmax(preset.bmax);
                              setCtRsec(preset.rsec);
                            }}
                            className="px-2 py-1 text-[9px] font-medium bg-slate-950 border border-slate-800 hover:border-cyan-500 hover:bg-cyan-950/20 text-slate-350 hover:text-cyan-400 rounded transition-all cursor-pointer whitespace-nowrap"
                          >
                            {preset.name}
                          </button>
                        ))
                      ) : (
                        COMMON_SHUNT_PRESETS.map((preset, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setShRval(preset.rval);
                              setShPrating(preset.prating);
                              setShTcr(preset.tcr);
                              setShRth(preset.rth);
                              setShEsl(preset.esl);
                            }}
                            className="px-2 py-1 text-[9px] font-medium bg-slate-950 border border-slate-800 hover:border-cyan-500 hover:bg-cyan-950/20 text-slate-350 hover:text-cyan-400 rounded transition-all cursor-pointer whitespace-nowrap"
                          >
                            {preset.name}
                          </button>
                        ))
                      )}
                    </div>
                  </div>

                  {activeTab === 'ct' ? (
                    <div className="space-y-4">
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">CT Electrical Ratings</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Primary Current Ipri (A_rms)</label>
                            <input type="number" value={ctIpri} onChange={(e) => setCtIpri(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Turns Ratio N (1:N)</label>
                            <input type="number" value={ctRatio} onChange={(e) => setCtRatio(parseInt(e.target.value) || 1)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Frequency f (Hz)</label>
                            <input type="number" value={ctFreq} onChange={(e) => setCtFreq(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Target Peak Vout_pk (V)</label>
                            <input type="number" step="0.05" value={ctVoutPk} onChange={(e) => setCtVoutPk(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>

                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Core & Secondary Winding Specs</span>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Core Area Ae (mm²)</label>
                            <input type="number" value={ctAe} onChange={(e) => setCtAe(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Saturation Flux Bmax (T)</label>
                            <input type="number" step="0.1" value={ctBmax} onChange={(e) => setCtBmax(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Secondary DCR Rsec (Ω)</label>
                            <input type="number" value={ctRsec} onChange={(e) => setCtRsec(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Shunt Ratings & Thermal Resistance</span>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Current Imax (A)</label>
                            <input type="number" value={shImax} onChange={(e) => setShImax(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Resistance R_shunt (mΩ)</label>
                            <input type="number" step="0.1" value={shRval} onChange={(e) => setShRval(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Rated Power P_rat (W)</label>
                            <input type="number" step="0.5" value={shPrating} onChange={(e) => setShPrating(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">TCR (ppm/°C)</label>
                            <input type="number" value={shTcr} onChange={(e) => setShTcr(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Thermal Res R_th (°C/W)</label>
                            <input type="number" value={shRth} onChange={(e) => setShRth(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Ambient Temp Ta (°C)</label>
                            <input type="number" value={shTamb} onChange={(e) => setShTamb(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>

                      <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Parasitic Inductance & PCB Trace Layout</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Parasitic ESL (nH)</label>
                            <input type="number" value={shEsl} onChange={(e) => setShEsl(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Slew Rate di/dt (A/μs)</label>
                            <input type="number" step="0.05" value={shDidt} onChange={(e) => setShDidt(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Non-Kelvin Trace Length L (mm)</label>
                            <input type="number" value={shPcbL} onChange={(e) => setShPcbL(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Trace Width W (mm)</label>
                            <input type="number" value={shPcbW} onChange={(e) => setShPcbW(Math.max(0.1, parseFloat(e.target.value) || 1.0))} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'results' && (
                <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                  <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                    <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      Physical Limits & Safety Verification
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                    <div className="space-y-2 mb-2">
                      <span className="text-[10px] font-bold text-slate-400 block select-none">Design Rule Check (DRC):</span>
                      {activeTab === 'ct' ? (
                        ctRes?.drc_warnings && ctRes.drc_warnings.length > 0 ? (
                          <div className="flex flex-col gap-1.5">
                            {ctRes.drc_warnings.map((warn, i) => (
                              <div key={i} className="p-2.5 rounded border border-red-500/20 bg-red-950/20 text-rose-350 text-[10px] flex items-start gap-2 leading-relaxed">
                                <ShieldAlert className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                                <span>{warn}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="p-2.5 rounded border border-emerald-500/20 bg-emerald-950/10 text-emerald-400 text-[10px] flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            <span>Flux density and burden resistor checks passed. Core will operate safely without saturation.</span>
                          </div>
                        )
                      ) : (
                        shRes?.drc_warnings && shRes.drc_warnings.length > 0 ? (
                          <div className="flex flex-col gap-1.5">
                            {shRes.drc_warnings.map((warn, i) => (
                              <div key={i} className="p-2.5 rounded border border-red-500/20 bg-red-950/20 text-rose-350 text-[10px] flex items-start gap-2 leading-relaxed">
                                <ShieldAlert className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                                <span>{warn}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="p-2.5 rounded border border-emerald-500/20 bg-emerald-950/10 text-emerald-400 text-[10px] flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            <span>Shunt thermal dissipation, temperature rise, and layout errors meet industrial safety and precision criteria.</span>
                          </div>
                        )
                      )}
                    </div>

                    <span className="text-[10px] font-bold text-slate-400 block select-none pt-2 border-t border-slate-800/80">Sizing & Metrics:</span>
                    {activeTab === 'ct' ? (
                      ctRes && (
                        <div className="grid grid-cols-2 gap-3 pt-1">
                          <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-400 uppercase font-semibold">Recommended Burden Resistance</span>
                            <div className="text-lg font-bold text-cyan-400 font-mono">
                              {(ctRes.r_burden_ohm ?? 0.0).toFixed(2)} <span className="text-[9px] text-slate-500 font-normal">Ω</span>
                            </div>
                            <span className="text-[8px] text-slate-500">Burden Power: {(ctRes.p_burden_mw ?? 0.0).toFixed(1)} mW</span>
                          </div>
                          <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-400 uppercase font-semibold">Operating Flux Density B_op</span>
                            <div className={`text-lg font-bold font-mono ${ctRes.is_saturated ? 'text-rose-500' : 'text-emerald-400'}`}>
                              {(ctRes.b_op_t ?? 0.0).toFixed(3)} <span className="text-[9px] text-slate-500 font-normal">T</span>
                            </div>
                            <span className="text-[8px] text-slate-500">Saturation Limit Bmax: {ctBmax.toFixed(2)} T</span>
                          </div>
                        </div>
                      )
                    ) : (
                      shRes && (
                        <div className="space-y-3 pt-1">
                          <div className="grid grid-cols-3 gap-2">
                            <div className="p-2.5 rounded border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                              <span className="text-[9px] text-slate-400 uppercase font-semibold">Dissipation P_loss</span>
                              <div className={`text-base font-bold font-mono ${shRes.is_overloaded ? 'text-rose-500' : 'text-slate-200'}`}>
                                {(shRes.p_actual_w ?? 0.0).toFixed(2)} <span className="text-[9px] text-slate-500 font-normal">W</span>
                              </div>
                              <span className="text-[8px] text-slate-500">Rating: {shPrating.toFixed(1)}W</span>
                            </div>
                            <div className="p-2.5 rounded border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                              <span className="text-[9px] text-slate-400 uppercase font-semibold">Predicted Temp T_j</span>
                              <div className={`text-base font-bold font-mono ${shRes.t_final_c > 125.0 ? 'text-rose-500' : 'text-orange-400'}`}>
                                {(shRes.t_final_c ?? 0.0).toFixed(1)} <span className="text-[9px] text-slate-500 font-normal">°C</span>
                              </div>
                              <span className="text-[8px] text-slate-500">Rise ΔT: +{(shRes.temp_rise_c ?? 0.0).toFixed(1)}°C</span>
                            </div>
                            <div className="p-2.5 rounded border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                              <span className="text-[9px] text-slate-400 uppercase font-semibold">TCR Thermal Drift Error</span>
                              <div className="text-base font-bold text-cyan-400 font-mono">
                                {(shRes.drift_pct ?? 0.0).toFixed(3)} <span className="text-[9px] text-slate-500 font-normal">%</span>
                              </div>
                              <span className="text-[8px] text-slate-500">Max Current Offset: {(shRes.err_amps ?? 0.0).toFixed(3)} A</span>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-3">
                            <div className="p-2.5 rounded border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                              <span className="text-[9px] text-slate-400 uppercase font-semibold">ESL Induced Spike Voltage</span>
                              <div className="text-base font-bold text-amber-300 font-mono">
                                {(shRes.v_spike_mv ?? 0.0).toFixed(1)} <span className="text-[9px] text-slate-500 font-normal">mV</span>
                              </div>
                            </div>
                            <div className="p-2.5 rounded border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                              <span className="text-[9px] text-slate-400 uppercase font-semibold">Non-Kelvin PCB Trace Error</span>
                              <div className="text-base font-bold text-slate-200 font-mono">
                                {shRes.r_trace_mohm > 0 
                                  ? `${shRes.r_trace_mohm.toFixed(2)} mΩ (${(shRes.pcb_err_pct ?? 0.0).toFixed(1)}%)`
                                  : '0.00 mΩ (Kelvin)'}
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    )}
                  </CardContent>
                </Card>
              )}

              {key === 'chart' && (
                <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                  <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                    <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      Thermal & Impedance Sweeps
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 flex justify-center items-center bg-slate-950/15">
                    <div className="w-full h-full min-h-[300px]">
                      <ReactECharts
                        option={getCurrentShuntChartOption()}
                        style={{ width: '100%', height: '100%', minHeight: '300px' }}
                        notMerge={true}
                      />
                    </div>
                  </CardContent>
                </Card>
              )}

              {key === 'schematic' && (
                <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                  <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                    <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      <Compass className="w-3.5 h-3.5 text-cyan-400" />
                      Sampling Circuit Schematics & Formulas
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-950/15">
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-full items-center">
                      <div className="lg:col-span-7 flex justify-center items-center p-2 rounded bg-slate-950/30 border border-slate-850/60 min-h-[200px]">
                        {activeTab === 'ct' ? (
                          <svg viewBox="0 0 420 120" className="w-full max-w-[400px] h-auto text-slate-350 bg-transparent">
                            <defs>
                              <style>
                                {`
                                  @keyframes stroke-flow-pri {
                                    to { stroke-dashoffset: -20; }
                                  }
                                  .animate-flow-pri {
                                    stroke-dasharray: 6, 4;
                                    animation: stroke-flow-pri 1.2s linear infinite;
                                    stroke: #f43f5e;
                                  }
                                `}
                              </style>
                            </defs>
                            <path d="M 10 30 L 190 30 M 230 30 L 410 30" stroke="#475569" strokeWidth="3" fill="none" />
                            <path d="M 10 30 L 410 30" strokeWidth="2" className="animate-flow-pri" fill="none" />
                            
                            <text x="30" y="20" fill="#f43f5e" fontSize="9" fontWeight="bold">I_pri (Primary Current)</text>
                            <ellipse cx="210" cy="30" rx="20" ry="12" stroke="#64748b" strokeWidth="2.5" fill="none" />
                            <path d="M 210 42 C 215 50, 195 55, 200 65 C 205 75, 185 80, 190 90" stroke="#38bdf8" strokeWidth="1.5" fill="none" />
                            <path d="M 190 90 L 140 90 L 140 100 L 150 100 L 150 110 L 130 110 L 130 100 L 140 100" stroke="#94a3b8" strokeWidth="1" fill="none" />
                            <text x="105" y="80" fill="#38bdf8" fontSize="8">R_sec (DCR)</text>
                            <path d="M 250 90 M 250 90 L 290 90 L 290 80 L 300 80 L 300 100 L 280 100 L 280 80 M 290 100 L 290 110" stroke="#94a3b8" strokeWidth="1" fill="none" />
                            <path d="M 210 42 L 290 42 L 290 90 M 190 90 L 110 90 L 110 110 M 290 110 L 330 110 M 110 110 L 330 110" stroke="#64748b" strokeWidth="1" fill="none" />
                            <text x="260" y="72" fill="#38bdf8" fontSize="8" fontWeight="bold">R_burden</text>
                            <circle cx="330" cy="90" r="10" stroke="#a78bfa" strokeWidth="1.5" fill="#1e1b4b" />
                            <text x="326" y="93" fill="#a78bfa" fontSize="8" fontWeight="bold">V</text>
                            <path d="M 330 110 L 330 100" stroke="#64748b" strokeWidth="1" fill="none" />
                            <path d="M 290 42 L 330 42 L 330 80" stroke="#64748b" strokeWidth="1" fill="none" />
                            <text x="345" y="65" fill="#a78bfa" fontSize="8">V_out</text>
                          </svg>
                        ) : (
                          <div className="grid grid-cols-1 gap-3 w-full">
                            <div className="flex flex-col gap-1 p-1 bg-slate-950/20 rounded border border-slate-900">
                              <span className="text-[8px] text-emerald-400 font-semibold select-none">👍 4-Wire Kelvin Sense (Zero PCB Error)</span>
                              <svg viewBox="0 0 200 80" className="w-full h-16 text-slate-400 bg-transparent">
                                <defs>
                                  <style>
                                    {`
                                      @keyframes stroke-flow-shunt {
                                        to { stroke-dashoffset: -20; }
                                      }
                                      .animate-flow-shunt {
                                        stroke-dasharray: 6, 4;
                                        animation: stroke-flow-shunt 1s linear infinite;
                                        stroke: #f43f5e;
                                      }
                                    `}
                                  </style>
                                </defs>
                                <rect x="50" y="20" width="100" height="30" rx="3" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                                <text x="84" y="38" fill="#94a3b8" fontSize="8" fontWeight="bold">SHUNT</text>
                                <path d="M 10 35 L 50 35" stroke="#f43f5e" strokeWidth="4" />
                                <path d="M 10 35 L 190 35" strokeWidth="2" className="animate-flow-shunt" fill="none" />
                                <path d="M 150 35 L 190 35" stroke="#f43f5e" strokeWidth="4" />
                                <circle cx="65" cy="35" r="2.5" fill="#06b6d4" />
                                <circle cx="135" cy="35" r="2.5" fill="#06b6d4" />
                                <path d="M 65 35 L 65 65 L 85 65" stroke="#06b6d4" strokeWidth="1.2" fill="none" />
                                <path d="M 135 35 L 135 65 L 115 65" stroke="#06b6d4" strokeWidth="1.2" fill="none" />
                                <circle cx="100" cy="65" r="4.5" stroke="#06b6d4" fill="#1e1b4b" strokeWidth="1" />
                                <text x="98" y="68" fill="#06b6d4" fontSize="7">V</text>
                                <text x="14" y="15" fill="#f43f5e" fontSize="6">I_load</text>
                              </svg>
                            </div>
                            <div className="flex flex-col gap-1 p-1 bg-slate-950/20 rounded border border-slate-900">
                              <span className="text-[8px] text-red-400 font-semibold select-none">👎 2-Wire Non-Kelvin Sense (PCB Trace Error)</span>
                              <svg viewBox="0 0 200 80" className="w-full h-16 text-slate-400 bg-transparent">
                                <rect x="50" y="20" width="100" height="30" rx="3" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                                <text x="84" y="38" fill="#94a3b8" fontSize="8" fontWeight="bold">SHUNT</text>
                                <path d="M 10 35 L 50 35" stroke="#f43f5e" strokeWidth="4" />
                                <path d="M 10 35 L 190 35" strokeWidth="2" className="animate-flow-shunt" fill="none" />
                                <path d="M 150 35 L 190 35" stroke="#f43f5e" strokeWidth="4" />
                                <circle cx="25" cy="35" r="2.5" fill="#ef4444" />
                                <circle cx="175" cy="35" r="2.5" fill="#ef4444" />
                                <path d="M 25 35 L 25 65 L 85 65" stroke="#ef4444" strokeWidth="1.2" fill="none" />
                                <path d="M 175 35 L 175 65 L 115 65" stroke="#ef4444" strokeWidth="1.2" fill="none" />
                                <circle cx="100" cy="65" r="4.5" stroke="#ef4444" fill="#1e1b4b" strokeWidth="1" />
                                <text x="98" y="68" fill="#ef4444" fontSize="7">V</text>
                                <path d="M 25 28 L 50 28" stroke="#f59e0b" strokeWidth="1.2" />
                                <text x="28" y="24" fill="#f59e0b" fontSize="6">R_copper</text>
                              </svg>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="lg:col-span-5 p-2 rounded bg-slate-950/30 border border-slate-850/60 h-full flex flex-col justify-center min-h-[180px] leading-relaxed">
                        <span className="text-[10px] font-bold text-slate-400 block mb-2 select-none">
                          Physical Derivations & Formulas:
                        </span>
                        {activeTab === 'ct' ? (
                          <div className="flex flex-col gap-2.5 text-[10px] font-mono">
                            <div>
                              <span className="text-[9px] text-slate-500 block">1. Burden Resistance:</span>
                              <Latex math="R_{bd} = \frac{V_{out,pk} \cdot N}{I_{pri} \cdot \sqrt{2}}" block />
                            </div>
                            <div>
                              <span className="text-[9px] text-slate-500 block">2. Core Max Induced EMF:</span>
                              <Latex math="V_{core} = I_{sec} \cdot (R_{bd} + R_{sec})" block />
                            </div>
                            <div>
                              <span className="text-[9px] text-slate-500 block">3. Peak Operating Flux Density B_op:</span>
                              <Latex math="B_{op} = \frac{V_{core} \cdot 10^6}{4.44 \cdot f \cdot N \cdot A_e}" block />
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col gap-2.5 text-[10px] font-mono">
                            <div>
                              <span className="text-[9px] text-slate-500 block">1. Temperature Resistance Shift:</span>
                              <Latex math="\Delta R = TCR \cdot (I^2 \cdot R \cdot R_{\theta})" block />
                            </div>
                            <div>
                              <span className="text-[9px] text-slate-500 block">2. Parasitic Inductive Spike:</span>
                              <Latex math="V_{spike} = ESL \cdot \frac{di}{dt}" block />
                            </div>
                            <div>
                              <span className="text-[9px] text-slate-500 block">3. Non-Kelvin Copper Trace Resistance:</span>
                              <Latex math="R_{trace} = \rho \cdot \frac{L}{W \cdot T}" block />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </DragCard>
          )}
          onDropOnColumn={handleDropOnColumn}
        />
      </div>
    </div>
  );
}