import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import {
  ArrowLeft
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

type TabType = 'generator' | 'evaluator';

interface BomItem {
  designator: string;
  calcValue: string;
  stdValue: string;
  error: string;
  type: string;
  desc: string;
}

export default function PowerDeviceDptPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: (mod: string | null) => void }) {
  const [activeTab, setActiveTab] = useTabHistoryState<TabType>('generator', 'activeTab');
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
    panelKey: 'layout_powerdevicedptpanel_v3_' + activeTab,
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 800, results: 920 }
  });
  const [error, setError] = useState<string | null>(null);
  
  // --- BOM state ---
  const [bomData, setBomData] = useState<any>(null);
  const [bomLoading, setBomLoading] = useState<boolean>(false);

  // --- Generator State ---
  const [vdc, setVdc] = useState<number>(400);
  const [imax, setImax] = useState<number>(50);
  const [lUh, setLUh] = useState<number>(100);
  const [rMohm, setRMohm] = useState<number>(50);
  const [genRes, setGenRes] = useState<any>(null);

  const calculatePulseWidths = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_dpt/pulse_widths', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vdc: vdc,
          imax: imax,
          l_uh: lUh,
          r_mohm: rMohm
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const data = await response.json();
      setGenRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'generator') calculatePulseWidths();
  }, [vdc, imax, lUh, rMohm, activeTab]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('target_power_dpt_data');
      if (raw) {
        const data = JSON.parse(raw);
        if (data.tab === 'generator' && data.params) {
          const p = data.params;
          if (p.vdc !== undefined) setVdc(p.vdc);
          if (p.imax !== undefined) setImax(p.imax);
          if (p.l_uh !== undefined) setLUh(p.l_uh);
          if (p.r_mohm !== undefined) setRMohm(p.r_mohm);
          setActiveTab('generator');
        }
        localStorage.removeItem('target_power_dpt_data');
      }
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  // --- Evaluator State ---
  const [onVsw, setOnVsw] = useState<number>(400);
  const [onIsw, setOnIsw] = useState<number>(50);
  const [onDtv, setOnDtv] = useState<number>(20);
  const [onDti, setOnDti] = useState<number>(15);
  const [onRes, setOnRes] = useState<any>(null);

  const [offVsw, setOffVsw] = useState<number>(400);
  const [offIsw, setOffIsw] = useState<number>(50);
  const [offDtv, setOffDtv] = useState<number>(15);
  const [offDti, setOffDti] = useState<number>(25);
  const [offRes, setOffRes] = useState<any>(null);

  const evalTurnOn = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_dpt/switching_eval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_sw: onVsw,
          i_sw: onIsw,
          dt_v_ns: onDtv,
          dt_i_ns: onDti,
          is_turn_on: true
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const data = await response.json();
      setOnRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const evalTurnOff = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_dpt/switching_eval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_sw: offVsw,
          i_sw: offIsw,
          dt_v_ns: offDtv,
          dt_i_ns: offDti,
          is_turn_on: false
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const data = await response.json();
      setOffRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'evaluator') {
      evalTurnOn();
      evalTurnOff();
    }
  }, [onVsw, onIsw, onDtv, onDti, offVsw, offIsw, offDtv, offDti, activeTab]);

  const fetchBomRecommendations = async (voltage: number, current: number) => {
    if (voltage <= 0 || current <= 0) return;
    setBomLoading(true);
    try {
      const response = await apiFetch('/api/bom/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          min_v_sw: voltage,
          min_i_sw: current,
          min_v_diode: voltage,
          min_i_diode: current
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const data = await response.json();
      setBomData(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBomLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'generator') {
      fetchBomRecommendations(vdc, imax);
    } else {
      fetchBomRecommendations(Math.max(onVsw, offVsw), Math.max(onIsw, offIsw));
    }
  }, [vdc, imax, onVsw, onIsw, offVsw, offIsw, activeTab]);

  // ECharts DPT Pulse simulation curve
  const getWaveOption = () => {
    if (!genRes) return {};
    const t1 = genRes.t1_us;
    const t2 = genRes.t2_us;
    const t3 = genRes.t3_us;

    const timePoints: number[] = [];
    const currentPoints: number[] = [];
    const gatePoints: number[] = [];

    const steps = 400;
    const totalTime = t1 + t2 + t3 + t1 * 0.1;

    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * totalTime;
      timePoints.push(t);

      let v_gate = 0.0;
      if (t < t1) {
        v_gate = 15.0;
      } else if (t < t1 + t2) {
        v_gate = 0.0;
      } else if (t < t1 + t2 + t3) {
        v_gate = 15.0;
      } else {
        v_gate = 0.0;
      }
      gatePoints.push(v_gate);

      const L = lUh * 1e-6;
      const R = rMohm * 1e-3;

      let i_val = 0;
      if (R < 1e-6) {
        if (t < t1) {
          i_val = (vdc / L) * (t * 1e-6);
        } else if (t < t1 + t2) {
          const i_start = (vdc / L) * (t1 * 1e-6);
          const dt = t - t1;
          i_val = i_start - (0.7 / L) * (dt * 1e-6);
        } else if (t < t1 + t2 + t3) {
          const i_start = currentPoints[currentPoints.length - 1] || 0;
          const dt = t - (t1 + t2);
          i_val = i_start + (vdc / L) * (dt * 1e-6);
        } else {
          const i_start = currentPoints[currentPoints.length - 1] || 0;
          const dt = t - (t1 + t2 + t3);
          i_val = i_start - (0.7 / L) * (dt * 1e-6);
        }
        currentPoints.push(Math.max(0.0, i_val));
      } else {
        const tau = L / R;
        const I_ss = vdc / R;

        if (t < t1) {
          i_val = I_ss * (1.0 - Math.exp(- (t * 1e-6) / tau));
        } else if (t < t1 + t2) {
          const i_start = I_ss * (1.0 - Math.exp(- (t1 * 1e-6) / tau));
          const dt = t - t1;
          i_val = i_start * Math.exp(- (dt * 1e-6) / tau) - 0.7/R * (1.0 - Math.exp(- (dt * 1e-6) / tau));
        } else if (t < t1 + t2 + t3) {
          const i_start = currentPoints[currentPoints.length - 1] || 0;
          const dt = t - (t1 + t2);
          i_val = i_start * Math.exp(- (dt * 1e-6) / tau) + I_ss * (1.0 - Math.exp(- (dt * 1e-6) / tau));
        } else {
          const i_start = currentPoints[currentPoints.length - 1] || 0;
          const dt = t - (t1 + t2 + t3);
          i_val = i_start * Math.exp(- (dt * 1e-6) / tau);
        }
        currentPoints.push(Math.max(0.0, i_val));
      }
    }

    return {
      backgroundColor: 'transparent',
      title: {
        text: 'Double-Pulse Test Inductor Current & Gate Drive Vgs Timing Simulation',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        formatter: (params: any) => {
          const t = params[0].axisValue;
          const i = params[0].data;
          const v = params[1].data;
          return `Time: ${parseFloat(t).toFixed(2)} us<br/>
                  Current: ${i.toFixed(2)} A<br/>
                  Vgs: ${v.toFixed(1)} V`;
        }
      },
      legend: {
        data: ['Inductor Current (A)', 'Low-Side Vgs Gate Drive (V)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '8%', right: '8%', top: '15%', bottom: '15%' , containLabel: true },
      xAxis: {
        type: 'category',
        name: 'Time (us)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        data: timePoints.map(t => t.toFixed(2)),
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Current (A)',
          nameTextStyle: { color: '#34d399', fontSize: 9 },
          axisLabel: { color: '#34d399', fontSize: 9 },
          splitLine: { lineStyle: { color: '#1e293b' } }
        },
        {
          type: 'value',
          name: 'Vgs (V)',
          nameTextStyle: { color: '#60a5fa', fontSize: 9 },
          axisLabel: { color: '#60a5fa', fontSize: 9 },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Inductor Current (A)',
          type: 'line',
          data: currentPoints,
          smooth: true,
          lineStyle: { color: '#34d399', width: 2.5 },
          showSymbol: false
        },
        {
          name: 'Low-Side Vgs Gate Drive (V)',
          type: 'line',
          yAxisIndex: 1,
          data: gatePoints,
          step: 'end',
          lineStyle: { color: '#60a5fa', width: 1.8 },
          showSymbol: false
        }
      ]
    };
  };

  const getOverlapOption = (isTurnOn: boolean) => {
    const timePoints: string[] = [];
    const vdsPoints: number[] = [];
    const idPoints: number[] = [];
    const pPoints: number[] = [];

    const steps = 100;
    const v_sw = isTurnOn ? onVsw : offVsw;
    const i_sw = isTurnOn ? onIsw : offIsw;
    const tv = isTurnOn ? onDtv : offDtv;
    const ti = isTurnOn ? onDti : offDti;
    const totalTime = tv + ti;

    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * totalTime;
      timePoints.push(t.toFixed(1));

      let v_val = v_sw;
      let i_val = 0.0;

      if (isTurnOn) {
        if (t < ti) {
          i_val = (t / ti) * i_sw;
          v_val = v_sw;
        } else {
          i_val = i_sw;
          v_val = v_sw * (1.0 - (t - ti) / tv);
        }
      } else {
        if (t < tv) {
          v_val = (t / tv) * v_sw;
          i_val = i_sw;
        } else {
          v_val = v_sw;
          i_val = i_sw * (1.0 - (t - tv) / ti);
        }
      }

      vdsPoints.push(v_val);
      idPoints.push(i_val);
      pPoints.push((v_val * i_val) / 1000.0);
    }

    return {
      backgroundColor: 'transparent',
      title: {
        text: isTurnOn ? 'Turn-On Transient Overlap Vds / Id Waveform' : 'Turn-Off Transient Overlap Vds / Id Waveform',
        textStyle: { color: '#e2e8f0', fontSize: 10 },
        left: 'center'
      },
      tooltip: { trigger: 'axis' },
      legend: {
        data: ['Vds (V)', 'Id (A)', 'Transient Power (kW)'],
        textStyle: { color: '#94a3b8', fontSize: 8 },
        bottom: 0
      },
      grid: { left: '8%', right: '8%', top: '15%', bottom: '15%' , containLabel: true },
      xAxis: {
        type: 'category',
        name: 'Time (ns)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        data: timePoints,
        axisLabel: { color: '#94a3b8', fontSize: 8 }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Vds (V) / Id (A)',
          axisLabel: { color: '#94a3b8', fontSize: 8 }
        },
        {
          type: 'value',
          name: 'Power (kW)',
          axisLabel: { color: '#fb7185', fontSize: 8 },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Vds (V)',
          type: 'line',
          data: vdsPoints,
          smooth: true,
          lineStyle: { color: '#60a5fa', width: 2 },
          showSymbol: false
        },
        {
          name: 'Id (A)',
          type: 'line',
          data: idPoints,
          smooth: true,
          lineStyle: { color: '#34d399', width: 2 },
          showSymbol: false
        },
        {
          name: 'Transient Power (kW)',
          type: 'line',
          yAxisIndex: 1,
          data: pPoints,
          smooth: true,
          lineStyle: { color: '#fb7185', width: 1.5, type: 'dashed' },
          showSymbol: false
        }
      ]
    };
  };

  return (
    <div className="h-full w-full flex flex-col overflow-hidden bg-slate-950">
      {/* Top Header */}
      <div className="flex-shrink-0 p-3 pb-0">
        <div className="flex items-center justify-between bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">Double-Pulse Test Sizing & Evaluation</h1>
              <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
                Calculates double-pulse test (DPT) charging pulse widths, freewheeling intervals, and switching overlap energy losses (Eon / Eoff).
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Tab selectors */}
      <div className="flex-shrink-0 px-3 pt-3 pb-1">
        <div className="flex gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800 w-fit">
          <button
            onClick={() => setActiveTab('generator')}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all border-0 cursor-pointer ${
              activeTab === 'generator' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            1. Pulse Width Calculator
          </button>
          <button
            onClick={() => setActiveTab('evaluator')}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all border-0 cursor-pointer ${
              activeTab === 'evaluator' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            2. Switching Loss & Speed Evaluator
          </button>
        </div>
      </div>

      {/* DragDeck area */}
      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin p-3 pt-0 pb-12 min-h-0">
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
                      Double-Pulse Operating Conditions
                    </h3>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                      {activeTab === 'generator' ? 'DC Test Bus Voltage' : 'Turn-On & Turn-Off Voltage Swings'}
                    </div>
                    {activeTab === 'generator' ? (
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">DC Test Bus Voltage V_DC [V]</label>
                        <input type="number" value={vdc} onChange={(e) => setVdc(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Turn-On Voltage Swing V_sw (On) [V]</label>
                          <input type="number" value={onVsw} onChange={(e) => setOnVsw(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Turn-Off Voltage Swing V_sw (Off) [V]</label>
                          <input type="number" value={offVsw} onChange={(e) => setOffVsw(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                      Target Turn-Off & Switching Currents
                    </div>
                    {activeTab === 'generator' ? (
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Target Turn-Off Current I_max [A]</label>
                        <input type="number" value={imax} onChange={(e) => setImax(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Turn-On Current Swing I_sw (On) [A]</label>
                          <input type="number" value={onIsw} onChange={(e) => setOnIsw(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Turn-Off Current Swing I_sw (Off) [A]</label>
                          <input type="number" value={offIsw} onChange={(e) => setOffIsw(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                        </div>
                      </div>
                    )}
                  </div>

                  {activeTab === 'generator' && (
                    <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                      <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                        Load Inductance & Loop DCR
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Load Inductance L [uH]</label>
                          <input type="number" value={lUh} onChange={(e) => setLUh(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Total Loop Resistance R [mΩ]</label>
                          <input type="number" value={rMohm} onChange={(e) => setRMohm(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'evaluator' && (
                    <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                      <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                        Switching Transition Time Metrics
                      </div>
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Turn-On Fall Time tvf [ns]</label>
                            <input type="number" value={onDtv} onChange={(e) => setOnDtv(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Turn-On Rise Time tir [ns]</label>
                            <input type="number" value={onDti} onChange={(e) => setOnDti(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Turn-Off Rise Time tvr [ns]</label>
                            <input type="number" value={offDtv} onChange={(e) => setOffDtv(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Turn-Off Fall Time tif [ns]</label>
                            <input type="number" value={offDti} onChange={(e) => setOffDti(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'results' && (
                <div className="overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md flex flex-col gap-4" style={{ height: cardHeights[key] ? cardHeights[key] - 50 : '100%' }}>
                  {/* Metric boxes */}
                  <div className="grid grid-cols-3 gap-4">
                    {activeTab === 'generator' && genRes && (
                      <>
                        <div className="p-3.5 rounded-xl bg-gradient-to-br from-cyan-950/20 to-blue-950/20 border border-cyan-500/20 flex flex-col">
                          <span className="text-[9px] text-cyan-400 font-semibold tracking-wider uppercase">First Pulse Width (T1)</span>
                          <span className="text-lg font-black text-cyan-300 font-mono">
                            {genRes.t1_us?.toFixed(2)} us
                          </span>
                          <span className="text-[9px] text-slate-500 mt-1">Charges inductor to: {imax} A</span>
                        </div>

                        <div className="p-3.5 rounded-xl bg-gradient-to-br from-purple-950/20 to-indigo-950/20 border border-purple-500/20 flex flex-col">
                          <span className="text-[9px] text-purple-400 font-semibold tracking-wider uppercase">Freewheeling Time (T2)</span>
                          <span className="text-lg font-black text-purple-300 font-mono">
                            {genRes.t2_us?.toFixed(1)} us
                          </span>
                          <span className="text-[9px] text-slate-400 mt-1">Second turn-on current: <strong className="text-purple-300 font-mono">{(genRes.i_start2_a ?? imax).toFixed(2)} A</strong></span>
                        </div>

                        <div className="p-3.5 rounded-xl bg-gradient-to-br from-emerald-950/20 to-teal-950/20 border border-emerald-500/20 flex flex-col">
                          <span className="text-[9px] text-emerald-400 font-semibold tracking-wider uppercase">Second Pulse Width (T3)</span>
                          <span className="text-lg font-black text-emerald-300 font-mono">
                            {genRes.t3_us?.toFixed(2)} us
                          </span>
                          <span className="text-[9px] text-slate-500 mt-1">Second turn-on rising edge capture</span>
                        </div>
                      </>
                    )}

                    {activeTab === 'evaluator' && onRes && offRes && (
                      <>
                        <div className="p-3.5 rounded-xl bg-gradient-to-br from-cyan-950/20 to-blue-950/20 border border-cyan-500/20 flex flex-col">
                          <span className="text-[9px] text-cyan-400 font-semibold tracking-wider uppercase">Turn-On Energy (E_on)</span>
                          <span className="text-lg font-black text-cyan-300 font-mono">
                            {onRes.e_loss_uj?.toFixed(1)} uJ
                          </span>
                          <span className="text-[9px] text-slate-500 mt-1">Turn-on dv/dt: {onRes.dv_dt?.toFixed(1)} V/ns | di/dt: {onRes.di_dt?.toFixed(1)} A/ns</span>
                        </div>

                        <div className="p-3.5 rounded-xl bg-gradient-to-br from-purple-950/20 to-indigo-950/20 border border-purple-500/20 flex flex-col">
                          <span className="text-[9px] text-purple-400 font-semibold tracking-wider uppercase">Turn-Off Energy (E_off)</span>
                          <span className="text-lg font-black text-purple-300 font-mono">
                            {offRes.e_loss_uj?.toFixed(1)} uJ
                          </span>
                          <span className="text-[9px] text-slate-500 mt-1">Turn-off dv/dt: {offRes.dv_dt?.toFixed(1)} V/ns | di/dt: {offRes.di_dt?.toFixed(1)} A/ns</span>
                        </div>

                        <div className="p-3.5 rounded-xl bg-gradient-to-br from-rose-950/20 to-orange-950/20 border border-rose-500/20 flex flex-col">
                          <span className="text-[9px] text-rose-400 font-semibold tracking-wider uppercase">Total Overlap Energy (E_sw)</span>
                          <span className="text-lg font-black text-rose-300 font-mono">
                            {(onRes.e_loss_uj + offRes.e_loss_uj).toFixed(1)} uJ
                          </span>
                          <span className="text-[9px] text-slate-500 mt-1">Excludes diode reverse recovery loss E_rr</span>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Card 1: Schematic SVG */}
                  <Card className="bg-slate-900/40 border-slate-800/80">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2 flex items-center justify-between">
                        <span>Double-Pulse Half-Bridge Equivalent Circuit</span>
                        <span className="text-[9px] text-slate-500">Series Inductor + Low-Side Driven DUT Mode</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="flex justify-center bg-slate-950/20 py-4 border-t border-slate-900/50">
                      <svg viewBox="0 0 480 130" className="w-full max-w-2xl h-auto text-slate-355 mx-auto select-none">
                        <circle cx="30" cy="65" r="12" fill="#1e293b" stroke="#38bdf8" strokeWidth="1.5" />
                        <text x="30" y="68" textAnchor="middle" fill="#38bdf8" className="text-[9px] font-bold font-mono">V_DC</text>
                        <line x1="30" y1="20" x2="30" y2="53" stroke="#38bdf8" strokeWidth="1.2" />
                        <line x1="30" y1="77" x2="30" y2="105" stroke="#38bdf8" strokeWidth="1.2" />
                        
                        <line x1="30" y1="20" x2="240" y2="20" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="30" y1="105" x2="240" y2="105" stroke="#64748b" strokeWidth="1.2" />
                        
                        {/* L_load Load Inductor */}
                        <rect x="80" y="13" width="60" height="14" fill="#1e293b" stroke="#34d399" strokeWidth="1.5" />
                        <text x="110" y="22" textAnchor="middle" fill="#34d399" className="text-[8.5px] font-bold font-mono">L_load={lUh}uH</text>

                        {/* Upper Switch Q1 */}
                        <line x1="240" y1="20" x2="240" y2="40" stroke="#64748b" strokeWidth="1.2" />
                        <rect x="225" y="40" width="30" height="20" rx="2" fill="#0f172a" stroke="#64748b" strokeWidth="1.2" />
                        <text x="240" y="52" textAnchor="middle" fill="#64748b" className="text-[7.5px] font-bold">Upper Q1</text>
                        
                        {/* Freewheeling Diode */}
                        <line x1="240" y1="35" x2="290" y2="35" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="240" y1="65" x2="290" y2="65" stroke="#64748b" strokeWidth="1.2" />
                        
                        <line x1="290" y1="35" x2="290" y2="65" stroke="#a855f7" strokeWidth="1.2" />
                        <polygon points="290,45 285,55 295,55" fill="#a855f7" />
                        <line x1="285" y1="45" x2="295" y2="45" stroke="#a855f7" strokeWidth="2" />
                        <text x="305" y="53" fill="#a855f7" className="text-[8.5px] font-bold">Freewheeling</text>
                        
                        {/* Current Probe */}
                        <circle cx="240" cy="65" r="3" fill="#34d399" />
                        <text x="165" y="69" fill="#34d399" className="text-[8.5px] font-bold">Current Probe</text>
                        
                        {/* DUT Q2 Switch */}
                        <line x1="240" y1="65" x2="240" y2="80" stroke="#64748b" strokeWidth="1.2" />
                        <rect x="225" y="80" width="30" height="20" rx="2" fill="#1e293b" stroke="#3b82f6" strokeWidth="1.5" />
                        <text x="240" y="92" textAnchor="middle" fill="#3b82f6" className="text-[8.5px] font-bold">DUT Q2</text>
                        
                        <line x1="240" y1="100" x2="240" y2="105" stroke="#64748b" strokeWidth="1.2" />
                      </svg>
                    </CardContent>
                  </Card>

                  {/* Card 2: Waveforms (Generator) or Results (Evaluator) */}
                  {activeTab === 'generator' && genRes ? (
                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2">
                          Switching Simulation Waveforms
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="h-64 border-t border-slate-900/50">
                        <ReactECharts notMerge={true} option={getWaveOption()} style={{ height: '100%', width: '100%' }} />
                      </CardContent>
                    </Card>
                  ) : activeTab === 'evaluator' && onRes && offRes ? (
                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2">
                          Switching Speed & Loss Calculation Principles
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="text-slate-400 text-xs space-y-2 leading-relaxed p-4 border-t border-slate-900/50">
                        <p>• **Turn-On/Turn-Off Energy Loss Integration**: Switching losses arise from instantaneous voltage and current overlap during transitions, approximated using classic triangular linear models:</p>
                        <Latex math={"E_{on} = \\int_{0}^{t_{on}} V_{ds}(t) \\cdot I_d(t) dt \\approx \\frac{1}{2} V_{sw} \\cdot I_{sw} \\cdot \\left( t_{vf} + t_{ir} \\right)"} block />
                        <Latex math={"E_{off} = \\int_{0}^{t_{off}} V_{ds}(t) \\cdot I_d(t) dt \\approx \\frac{1}{2} V_{sw} \\cdot I_{sw} \\cdot \\left( t_{vr} + t_{if} \\right)"} block />
                        <p>• **Safe Operating Area (SOA) & Thermal Check**: If E_sw is high under high-frequency operation (e.g. fsw = 100 kHz), the average dissipation <Latex math={"P_{sw} = E_{sw} \\cdot f_{sw}"} /> will heat the junction rapidly, demanding adequate heatsinking to prevent thermal runaway.</p>
                      </CardContent>
                    </Card>
                  ) : null}

                  {/* Card 3: Active Device Recommendations */}
                  <Card className="bg-slate-900/40 border-slate-800/80">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-xs font-bold text-slate-350 border-l-2 border-cyan-500 pl-2 flex items-center justify-between">
                        <span>Active Semiconductor Selection (1.2x Voltage & 1.5x Current Margin)</span>
                        <span className="text-[10px] text-slate-400">
                          {activeTab === 'generator' 
                            ? `Target Requirement: ≥${(vdc * 1.2).toFixed(0)}V, ≥${(imax * 1.5).toFixed(0)}A`
                            : `Target Requirement: ≥${(Math.max(onVsw, offVsw) * 1.2).toFixed(0)}V, ≥${(Math.max(onIsw, offIsw) * 1.5).toFixed(0)}A`
                          }
                        </span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 border-t border-slate-900/50 space-y-4">
                      {bomLoading ? (
                        <div className="flex items-center justify-center py-4 text-xs text-slate-400">
                          Querying active semiconductor database...
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Switches Table */}
                          <div className="space-y-2">
                            <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-wide">
                              Recommended Switches (MOSFET / SiC)
                            </div>
                            <div className="overflow-x-auto">
                              <table className="w-full text-left text-[10px] border-collapse">
                                <thead>
                                  <tr className="border-b border-slate-800 text-slate-400">
                                    <th className="py-1">Part Number</th>
                                    <th className="py-1">Vds</th>
                                    <th className="py-1">Id</th>
                                    <th className="py-1">Rds(on)</th>
                                    <th className="py-1">Package</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {bomData?.switches?.map((item: any, idx: number) => (
                                    <tr key={idx} className={`border-b border-slate-800/40 hover:bg-slate-800/20 ${idx === 0 ? 'bg-cyan-500/5 text-cyan-300 font-medium' : 'text-slate-350'}`}>
                                      <td className="py-2">{item.name} {idx === 0 && <span className="text-[8px] bg-cyan-500/20 text-cyan-400 px-1 rounded">Preferred</span>}</td>
                                      <td className="py-2">{item.v_ds_max}V</td>
                                      <td className="py-2">{item.i_d_max}A</td>
                                      <td className="py-2">{(item.r_ds_on * 1000).toFixed(1)}mΩ</td>
                                      <td className="py-2 text-slate-500">{item.package}</td>
                                    </tr>
                                  ))}
                                  {!bomData?.switches?.length && (
                                    <tr>
                                      <td colSpan={5} className="py-3 text-center text-slate-500">No switches match voltage / current requirements</td>
                                    </tr>
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>

                          {/* Diodes Table */}
                          <div className="space-y-2">
                            <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wide">
                              Recommended Freewheeling Diodes (SiC / Fast Recovery)
                            </div>
                            <div className="overflow-x-auto">
                              <table className="w-full text-left text-[10px] border-collapse">
                                <thead>
                                  <tr className="border-b border-slate-800 text-slate-400">
                                    <th className="py-1">Part Number</th>
                                    <th className="py-1">Vr</th>
                                    <th className="py-1">If</th>
                                    <th className="py-1">Vf</th>
                                    <th className="py-1">Package</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {bomData?.diodes?.map((item: any, idx: number) => (
                                    <tr key={idx} className={`border-b border-slate-800/40 hover:bg-slate-800/20 ${idx === 0 ? 'bg-purple-500/5 text-purple-300 font-medium' : 'text-slate-350'}`}>
                                      <td className="py-2">{item.name} {idx === 0 && <span className="text-[8px] bg-purple-500/20 text-purple-400 px-1 rounded">Preferred</span>}</td>
                                      <td className="py-2">{item.v_r_max}V</td>
                                      <td className="py-2">{item.i_f_max}A</td>
                                      <td className="py-2">{item.v_f}V</td>
                                      <td className="py-2 text-slate-500">{item.package}</td>
                                    </tr>
                                  ))}
                                  {!bomData?.diodes?.length && (
                                    <tr>
                                      <td colSpan={5} className="py-3 text-center text-slate-500">No diodes match voltage / current requirements</td>
                                    </tr>
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      )}
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
