import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { apiFetch } from '../lib/api';
import katex from 'katex';
import {
  ArrowLeft,
  ShieldAlert,
  CheckCircle2,
  TrendingUp,
  FileCode,
  RefreshCw
} from 'lucide-react';

import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
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

interface RcFilterResponse {
  fc_hz: number;
  delay_5tau_us: number;
  v_drop_mv: number;
  drop_lsb: number;
  req_c_nf: number;
  passed: boolean;
  drc_warnings: string[];
}

interface BudgetResponse {
  fc_hz: number;
  alias_att_db: number;
  delay_us: number;
  phase_lag_deg: number;
  settle_err_pct: number;
  err_lsb: number;
  noise_pin_uv_rms: number;
  noise_in_rms: number;
  qnoise_uv_rms: number;
  t_sample_rec_ns: number;
  drc_warnings: string[];
}

interface AfeReconstructResponse {
  v_pin: number;
  adc_code: number;
  gain: number;
  lsb: number;
  k: number;
  b: number;
  is_saturated: boolean;
  drc_warnings: string[];
}

interface TwoPointResponse {
  k: number;
  b: number;
}

export default function AdcConditioningPanel({ onBack }: { onBack: () => void }) {
  const [activeTab, setActiveTab] = useTabHistoryState<'rc' | 'budget' | 'afe' | 'twopoint'>('rc', 'activeTab');
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
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_adcconditioningpanel_v4',
    activeTab: activeTab,
    defaultCards: ['input', 'results', 'chart'],
    defaultColumns: { input: 'left', results: 'right', chart: 'right' },
    defaultSpans: { input: 4, results: 8, chart: 8 },
    defaultHeights: { input: 850, results: 420, chart: 430 }
  });

  const COMMON_ADC_SPECS = [
    { name: 'ADS1256 (High-Precision 24-Bit)', bits: 24, vref: 2.5, t_sample: 1000, csh: 15 },
    { name: 'ADS1115 (Standard 16-Bit)', bits: 16, vref: 4.096, t_sample: 5000, csh: 20 },
    { name: 'STM32G4 High-Speed 12-Bit', bits: 12, vref: 3.3, t_sample: 120, csh: 5 }
  ];

  const getAdcChartOption = () => {
    if (activeTab === 'rc' || activeTab === 'budget') {
      const r = activeTab === 'rc' ? rcRes : sbRflt;
      const c = activeTab === 'rc' ? rcCap : sbCflt;
      const r_src = activeTab === 'rc' ? 0 : sbRsrc;
      const total_r = r + r_src;
      const fc = 1 / (2 * Math.PI * total_r * (c * 1e-9));

      const freqPoints: any[] = [];
      for (let f = 10; f <= 10e6; f *= 1.35) {
        const gain = 20 * Math.log10(1 / Math.sqrt(1 + Math.pow(f / fc, 2)));
        freqPoints.push([f, parseFloat(gain.toFixed(2))]);
      }

      const tau = total_r * (c * 1e-9);
      const stepPoints: any[] = [];
      const vref = activeTab === 'rc' ? rcVref : sbVref;
      for (let t = 0; t <= 10 * tau; t += (10 * tau) / 100) {
        const v = vref * (1 - Math.exp(-t / tau));
        stepPoints.push([(t * 1e6).toFixed(3), parseFloat(v.toFixed(3))]);
      }

      return {
        backgroundColor: 'transparent',
        title: {
          text: 'Anti-Aliasing Filter Frequency Response & Time-Domain Step Settling',
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
        grid: [
          { left: '12%', right: '12%', top: '18%', height: '30%', containLabel: true },
          { left: '12%', right: '12%', bottom: '15%', height: '30%', containLabel: true }
        ],
        xAxis: [
          {
            type: 'log',
            gridIndex: 0,
            name: 'Frequency (Hz)',
            nameGap: 15,
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } },
            axisLine: { lineStyle: { color: '#334155' } },
            min: 10,
            max: 10000000
          },
          {
            type: 'category',
            gridIndex: 1,
            name: 'Time (μs)',
            nameGap: 15,
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } },
            axisLine: { lineStyle: { color: '#334155' } },
            data: stepPoints.map(p => p[0])
          }
        ],
        yAxis: [
          {
            type: 'value',
            gridIndex: 0,
            name: 'Gain (dB)',
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } },
            axisLine: { lineStyle: { color: '#334155' } }
          },
          {
            type: 'value',
            gridIndex: 1,
            name: 'Voltage (V)',
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } },
            axisLine: { lineStyle: { color: '#334155' } }
          }
        ],
        series: [
          {
            name: 'Magnitude Response',
            type: 'line',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: freqPoints,
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 3, color: '#10b981', shadowBlur: 8, shadowColor: 'rgba(16, 185, 129, 0.5)' }
          },
          {
            name: 'Step Response',
            type: 'line',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: stepPoints.map(p => p[1]),
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 3, color: '#38bdf8', shadowBlur: 8, shadowColor: 'rgba(56, 189, 248, 0.5)' }
          }
        ]
      };
    } else {
      const lineData: any[] = [];
      let labelIn = 'Physical Input';
      let labelOut = 'ADC Code';
      if (activeTab === 'afe' && afeResult) {
        const bits = afeBits;
        const maxCode = Math.pow(2, bits) - 1;
        const physMax = afePhysIn * 1.5;
        const physMin = afePhysIn * 0.2;
        const step = Math.max(1e-6, (physMax - physMin) / 10);
        for (let x = physMin; x <= physMax; x += step) {
          let code = (x - afeResult.b) / afeResult.k;
          if (code < 0) code = 0;
          if (code > maxCode) code = maxCode;
          lineData.push([x.toFixed(2), parseFloat(code.toFixed(0))]);
        }
        labelIn = 'Physical Input';
      } else if (activeTab === 'twopoint' && tpResult) {
        const codes = [tpX1, tpX2];
        const minCode = Math.min(...codes) * 0.5;
        const maxCode = Math.max(...codes) * 1.2;
        const step = Math.max(1e-6, (maxCode - minCode) / 10);
        for (let c = minCode; c <= maxCode; c += step) {
          const y = tpResult.k * c + tpResult.b;
          lineData.push([c.toFixed(0), parseFloat(y.toFixed(3))]);
        }
        labelIn = 'ADC Code';
        labelOut = 'Calibrated Value';
      }

      return {
        backgroundColor: 'transparent',
        title: {
          text: activeTab === 'afe' ? 'AFE Full-Scale Reconstruction Fit Line' : 'Two-Point Linear Calibration Fit',
          textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' },
          left: 'center',
          top: 5
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: '#a78bfa',
          borderWidth: 1,
          textStyle: { color: '#e2e8f0', fontSize: 10 },
          extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
        },
        grid: { left: '10%', right: '10%', top: '25%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          name: labelIn,
          nameGap: 15,
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
          axisLine: { lineStyle: { color: '#334155' } },
          data: lineData.map(d => d[0])
        },
        yAxis: {
          type: 'value',
          name: labelOut,
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
          axisLine: { lineStyle: { color: '#334155' } }
        },
        series: [
          {
            name: activeTab === 'afe' ? 'Transfer Curve' : 'Linear Fit',
            type: 'line',
            data: lineData.map(d => d[1]),
            smooth: true,
            lineStyle: { width: 3, color: '#a78bfa', shadowBlur: 8, shadowColor: 'rgba(167, 139, 250, 0.5)' }
          }
        ]
      };
    }
  };

  const [error, setError] = useState<string | null>(null);

  // Tab 1: RC Filter States
  const [rcRes, setRcRes] = useState<number>(100);
  const [rcCap, setRcCap] = useState<number>(10);
  const [rcCsh, setRcCsh] = useState<number>(10);
  const [rcBits, setRcBits] = useState<number>(12);
  const [rcVref, setRcVref] = useState<number>(3.3);
  const [rcResult, setRcResult] = useState<RcFilterResponse | null>(null);

  // Tab 2: Budget States
  const [sbRsrc, setSbRsrc] = useState<number>(200);
  const [sbRflt, setSbRflt] = useState<number>(100);
  const [sbCflt, setSbCflt] = useState<number>(4.7);
  const [sbCsh, setSbCsh] = useState<number>(12);
  const [sbTsample, setSbTsample] = useState<number>(500);
  const [sbFs, setSbFs] = useState<number>(20);
  const [sbFsignal, setSbFsignal] = useState<number>(1000);
  const [sbBits, setSbBits] = useState<number>(12);
  const [sbVref, setSbVref] = useState<number>(3.3);
  const [sbGain, setSbGain] = useState<number>(0.01);
  const [sbOpNoise, setSbOpNoise] = useState<number>(20);
  const [sbBw, setSbBw] = useState<number>(10);
  const [sbLoopFc, setSbLoopFc] = useState<number>(2);
  const [budResult, setBudResult] = useState<BudgetResponse | null>(null);

  // Tab 3: AFE Reconstruct States
  const [afeMode, setAfeMode] = useState<number>(0);
  const [afeVref, setAfeVref] = useState<number>(3.3);
  const [afeBits, setAfeBits] = useState<number>(12);
  const [afeP1, setAfeP1] = useState<number>(100.0);
  const [afeP2, setAfeP2] = useState<number>(3.3);
  const [afeBias, setAfeBias] = useState<number>(0.0);
  const [afePhysIn, setAfePhysIn] = useState<number>(12.0);
  const [afeResult, setAfeResult] = useState<AfeReconstructResponse | null>(null);

  // Tab 4: Two Point Calibration
  const [tpX1, setTpX1] = useState<number>(100);
  const [tpY1, setTpY1] = useState<number>(1.0);
  const [tpX2, setTpX2] = useState<number>(4000);
  const [tpY2, setTpY2] = useState<number>(12.0);
  const [tpResult, setTpResult] = useState<TwoPointResponse | null>(null);

  const handleRcCalc = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/adc_conditioning/rc_filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          r_ohm: rcRes,
          c_nf: rcCap,
          csh_pf: rcCsh,
          bits: rcBits,
          vref: rcVref
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'RC anti-aliasing calculation failed');
      }
      const data = await response.json();
      setRcResult(data);
    } catch (e: any) {
      setRcResult(null);
      setError(e.message);
    }
  };

  const handleBudgetCalc = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/adc_conditioning/budget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          r_src: sbRsrc,
          r_flt: sbRflt,
          c_flt_nf: sbCflt,
          c_sh_pf: sbCsh,
          t_sample_ns: sbTsample,
          f_s_khz: sbFs,
          f_signal_hz: sbFsignal,
          bits: sbBits,
          vref: sbVref,
          gain: sbGain,
          op_noise_nv: sbOpNoise,
          bw_noise_khz: sbBw,
          loop_fc_khz: sbLoopFc
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'ADC signal chain budget calculation failed');
      }
      const data = await response.json();
      setBudResult(data);
    } catch (e: any) {
      setBudResult(null);
      setError(e.message);
    }
  };

  const handleAfeCalc = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/adc_conditioning/afe_reconstruct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: afeMode,
          vref: afeVref,
          bits: afeBits,
          p1: afeP1,
          p2: afeMode === 1 ? 0.0 : afeP2,
          bias: afeBias,
          phys_in: afePhysIn
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'AFE reconstruction calculation failed: Physical input must not be zero.');
      }
      const data = await response.json();
      setAfeResult(data);
    } catch (e: any) {
      setAfeResult(null);
      setError(e.message);
    }
  };

  const handleTwoPointCalc = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/adc_conditioning/two_point', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          x1: tpX1,
          y1: tpY1,
          x2: tpX2,
          y2: tpY2
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Two-point calibration failed: Calibration point ADC codes must differ.');
      }
      const data = await response.json();
      setTpResult(data);
    } catch (e: any) {
      setTpResult(null);
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'rc') handleRcCalc();
    else if (activeTab === 'budget') handleBudgetCalc();
    else if (activeTab === 'afe') handleAfeCalc();
    else if (activeTab === 'twopoint') handleTwoPointCalc();
  }, [
    activeTab, rcRes, rcCap, rcCsh, rcBits, rcVref,
    sbRsrc, sbRflt, sbCflt, sbCsh, sbTsample, sbFs, sbFsignal, sbBits, sbVref, sbGain, sbOpNoise, sbBw, sbLoopFc,
    afeMode, afeVref, afeBits, afeP1, afeP2, afeBias, afePhysIn,
    tpX1, tpY1, tpX2, tpY2
  ]);

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
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
            <h2 className="text-base font-bold text-white tracking-tight">ADC Signal Conditioning & Calibration</h2>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Design ADC anti-aliasing RC filters, analyze noise and delay budgets, configure AFE scaling gains, and compute two-point calibrations.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Tabs value={activeTab} onValueChange={(v: any) => setActiveTab(v)} className="w-auto">
            <TabsList className="bg-slate-950/80 border border-slate-855 p-0.5 rounded-lg flex">
              <TabsTrigger value="rc" className="text-[10px] font-bold px-2.5 py-1">RC Filter</TabsTrigger>
              <TabsTrigger value="budget" className="text-[10px] font-bold px-2.5 py-1">Chain Budget</TabsTrigger>
              <TabsTrigger value="afe" className="text-[10px] font-bold px-2.5 py-1">AFE Design</TabsTrigger>
              <TabsTrigger value="twopoint" className="text-[10px] font-bold px-2.5 py-1">2-Pt Calibration</TabsTrigger>
            </TabsList>
          </Tabs>

          <Button
            size="sm"
            variant="outline"
            onClick={handleResetLayout}
            className="flex items-center gap-1.5 text-xs bg-[#0b0f19]/80 border-slate-800 hover:bg-slate-900 cursor-pointer text-slate-300 hover:text-white"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            Reset Layout
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2.5 text-xs text-rose-300 max-w-[1600px] mx-auto w-full">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>Computation Error: {error}</span>
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
                <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 p-4">
                  <Card className="bg-[#0b0f19]/30 border-slate-800/80">
                    <CardHeader className="py-3 border-b border-slate-800/80">
                      <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-2">
                        Parameter Input Configuration
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 space-y-4">
                      {(activeTab === 'rc' || activeTab === 'budget' || activeTab === 'afe') && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 1: ADC Reference & Resolution
                          </div>
                          <div className="mb-3 space-y-1">
                            <span className="text-[9px] text-slate-400 block select-none">Quick Preset Presets:</span>
                            <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                              {COMMON_ADC_SPECS.map((spec, idx) => (
                                <button
                                  key={idx}
                                  type="button"
                                  onClick={() => {
                                    if (activeTab === 'rc') {
                                      setRcVref(spec.vref);
                                      setRcBits(spec.bits);
                                      setRcCsh(spec.csh);
                                    } else if (activeTab === 'budget') {
                                      setSbVref(spec.vref);
                                      setSbBits(spec.bits);
                                      setSbCsh(spec.csh);
                                      setSbTsample(spec.t_sample);
                                    } else if (activeTab === 'afe') {
                                      setAfeVref(spec.vref);
                                      setAfeBits(spec.bits);
                                    }
                                  }}
                                  className="px-2 py-1 text-[9px] font-medium bg-slate-950 border border-slate-800 hover:border-cyan-500 hover:bg-cyan-950/20 text-slate-350 hover:text-cyan-400 rounded transition-all cursor-pointer whitespace-nowrap"
                                >
                                  {spec.name}
                                </button>
                              ))}
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Reference Vref (V)</label>
                              <input
                                type="number"
                                value={activeTab === 'rc' ? rcVref : activeTab === 'budget' ? sbVref : afeVref}
                                step="0.1"
                                onChange={e => {
                                  const val = parseFloat(e.target.value) || 0;
                                  if (activeTab === 'rc') setRcVref(val);
                                  else if (activeTab === 'budget') setSbVref(val);
                                  else setAfeVref(val);
                                }}
                                className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none"
                              />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Resolution (Bits)</label>
                              <input
                                type="number"
                                value={activeTab === 'rc' ? rcBits : activeTab === 'budget' ? sbBits : afeBits}
                                onChange={e => {
                                  const val = parseInt(e.target.value) || 0;
                                  if (activeTab === 'rc') setRcBits(val);
                                  else if (activeTab === 'budget') setSbBits(val);
                                  else setAfeBits(val);
                                }}
                                className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none"
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {(activeTab === 'rc' || activeTab === 'budget') && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 2: Anti-Aliasing RC Low-Pass Filter
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Filter Resistor R (Ω)</label>
                              <input
                                type="number"
                                value={activeTab === 'rc' ? rcRes : sbRflt}
                                onChange={e => {
                                  const val = parseFloat(e.target.value) || 0;
                                  if (activeTab === 'rc') setRcRes(val);
                                  else setSbRflt(val);
                                }}
                                className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none"
                              />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Filter Capacitor C (nF)</label>
                              <input
                                type="number"
                                value={activeTab === 'rc' ? rcCap : sbCflt}
                                onChange={e => {
                                  const val = parseFloat(e.target.value) || 0;
                                  if (activeTab === 'rc') setRcCap(val);
                                  else setSbCflt(val);
                                }}
                                className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none"
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {(activeTab === 'rc' || activeTab === 'budget') && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 3: Sample & Hold Circuit
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Sampling Cap Csh (pF)</label>
                              <input
                                type="number"
                                value={activeTab === 'rc' ? rcCsh : sbCsh}
                                onChange={e => {
                                  const val = parseFloat(e.target.value) || 0;
                                  if (activeTab === 'rc') setRcCsh(val);
                                  else setSbCsh(val);
                                }}
                                className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none"
                              />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Sampling Window Tsamp (ns)</label>
                              <input
                                type="number"
                                value={activeTab === 'rc' ? 300 : sbTsample}
                                disabled={activeTab === 'rc'}
                                onChange={e => setSbTsample(parseFloat(e.target.value) || 0)}
                                className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none disabled:opacity-30"
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeTab === 'afe' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 4: Analog Front-End Topology
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1 col-span-2">
                              <label className="text-[10px] text-slate-400">AFE Circuit Topology</label>
                              <select
                                value={afeMode}
                                onChange={e => {
                                  const mode = parseInt(e.target.value);
                                  setAfeMode(mode);
                                  if (mode === 0) { setAfeP1(100.0); setAfeP2(3.3); }
                                  else if (mode === 1) { setAfeP1(1.0); setAfeP2(0.0); }
                                  else { setAfeP1(10.0); setAfeP2(50.0); }
                                }}
                                className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-300 outline-none"
                              >
                                <option value={0}>Resistive Voltage Divider</option>
                                <option value={1}>Op-Amp Non-Inverting Amplifier</option>
                                <option value={2}>Current Shunt Resistor</option>
                              </select>
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">
                                {afeMode === 0 ? "High Side R1 (kΩ)" : afeMode === 1 ? "Gain (V/V)" : "Shunt Rs (mΩ)"}
                              </label>
                              <input type="number" value={afeP1} onChange={e => setAfeP1(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-cyan-400 outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">
                                {afeMode === 0 ? "Low Side R2 (kΩ)" : "---"}
                              </label>
                              <input type="number" value={afeP2} disabled={afeMode === 1} onChange={e => setAfeP2(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-cyan-400 outline-none disabled:opacity-30" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeTab === 'budget' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 5: Noise Environment & Bandwidth
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Op-Amp Input Noise (nV/√Hz)</label>
                              <input type="number" value={sbOpNoise} onChange={e => setSbOpNoise(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Noise Bandwidth BW (kHz)</label>
                              <input type="number" value={sbBw} onChange={e => setSbBw(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeTab === 'budget' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 6: Sampling Rate & Crossover
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Sampling Rate Fs (kS/s)</label>
                              <input type="number" value={sbFs} onChange={e => setSbFs(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Loop Crossover fc (kHz)</label>
                              <input type="number" value={sbLoopFc} onChange={e => setSbLoopFc(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeTab === 'twopoint' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 7: Calibration Low Point 1
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Raw ADC Value (Code)</label>
                              <input type="number" value={tpX1} onChange={e => setTpX1(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Physical Truth (V/A)</label>
                              <input type="number" value={tpY1} onChange={e => setTpY1(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                          </div>
                        </div>
                      )}

                      {activeTab === 'twopoint' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-cyan-500 rounded-full inline-block"></span>
                            Step 8: Calibration High Point 2
                          </div>
                          <div className="grid grid-cols-2 gap-3.5">
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Raw ADC Value (Code)</label>
                              <input type="number" value={tpX2} onChange={e => setTpX2(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[10px] text-slate-400">Physical Truth (V/A)</label>
                              <input type="number" value={tpY2} onChange={e => setTpY2(parseFloat(e.target.value) || 0)} className="bg-slate-900/60 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                            </div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <Card className="bg-[#0b0f19]/30 border-slate-800/80">
                    <CardHeader className="py-2 border-b border-slate-800/80">
                      <CardTitle className="text-[10px] font-bold text-slate-400">
                        ADC Charge Injection Formula
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3">
                      <Latex math={"Q_{drop} = C_{sh} \\cdot V_{ref} \\implies \\Delta V_{drop} = \\frac{C_{sh} \\cdot V_{ref}}{C_{filter}}"} block />
                    </CardContent>
                  </Card>
                </div>
              )}

              {key === 'results' && (
                <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                  <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                    <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      ADC Calculation & Calibration Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                    {(() => {
                      const hasResult = 
                        (activeTab === 'rc' && rcResult) ||
                        (activeTab === 'budget' && budResult) ||
                        (activeTab === 'afe' && afeResult) ||
                        (activeTab === 'twopoint' && tpResult);

                      if (!hasResult) {
                        return (
                          <div className="flex flex-col items-center justify-center h-full py-16 text-center space-y-3 select-none">
                            <div className="text-xs font-bold text-slate-400">No Calculation Results Available</div>
                            <p className="text-[10px] text-slate-500 max-w-[240px] leading-relaxed">
                              Configure circuit and ADC parameters on the left to compute anti-aliasing requirements, noise budgets, or two-point calibration coefficients.
                            </p>
                          </div>
                        );
                      }

                      return (
                        <div className="space-y-4">
                          {(() => {
                            const drcWarns: string[] = [];
                            if (activeTab === 'rc' && rcResult) {
                              if (!rcResult.passed) {
                                drcWarns.push("Charge Kickback Warning: Filter capacitor C is too small; instantaneous kickback voltage drop exceeds 0.5 LSB. Increase filter capacitance.");
                              }
                              if (rcResult.drc_warnings) {
                                drcWarns.push(...rcResult.drc_warnings);
                              }
                            } else if (activeTab === 'budget' && budResult) {
                              if (budResult.delay_us * 1000 > sbTsample) {
                                drcWarns.push(`Settling Delay Alert: Filter group delay (${budResult.delay_us.toFixed(2)} μs) exceeds sampling window (${(sbTsample/1000).toFixed(2)} μs). Reduce R_filter or C_filter.`);
                              }
                              if (budResult.drc_warnings) {
                                drcWarns.push(...budResult.drc_warnings);
                              }
                            } else if (activeTab === 'afe' && afeResult) {
                              if (afeResult.is_saturated) {
                                drcWarns.push("Saturation Alert: Scaled input signal exceeds ADC reference Vref; readings will clip!");
                              }
                              if (afeResult.drc_warnings) {
                                drcWarns.push(...afeResult.drc_warnings);
                              }
                            }

                            if (drcWarns.length > 0) {
                              return (
                                <div className="space-y-1.5">
                                  {drcWarns.map((w, i) => (
                                    <div key={i} className="p-2.5 rounded border bg-rose-500/10 border-rose-500/20 text-rose-350 text-[10px] leading-relaxed flex items-start gap-2 select-none">
                                      <ShieldAlert className="w-3.5 h-3.5 text-rose-450 shrink-0 mt-0.5" />
                                      <span>{w}</span>
                                    </div>
                                  ))}
                                </div>
                              );
                            }

                            return (
                              <div className="flex items-center gap-2 text-emerald-400 bg-emerald-950/20 p-2.5 rounded border border-emerald-900/40 text-[10px] select-none">
                                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                                <span>All signal chain margins, sampling delays, and headroom limits satisfy specifications.</span>
                              </div>
                            );
                          })()}

                          {activeTab === 'rc' && rcResult && (
                            <div className="grid grid-cols-3 gap-3">
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Cutoff Frequency fc</span>
                                <span className="text-xs font-bold text-cyan-300 font-mono">
                                  {(rcResult.fc_hz / 1000).toFixed(2)} kHz
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Settling Delay (5 tau)</span>
                                <span className="text-xs font-bold text-slate-200 font-mono">
                                  {rcResult.delay_5tau_us.toFixed(2)} μs
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Kickback Vdrop</span>
                                <span className="text-xs font-bold text-orange-400 font-mono">
                                  {rcResult.v_drop_mv.toFixed(2)} mV
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Equivalent ADC Error</span>
                                <span className="text-xs font-bold text-emerald-300 font-mono">
                                  {rcResult.drop_lsb.toFixed(2)} LSB
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Min Recommended Cap</span>
                                <span className="text-xs font-bold text-purple-300 font-mono">
                                  {rcResult.req_c_nf.toFixed(2)} nF
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Capacitor Status</span>
                                <span className={`text-[10px] font-bold ${rcResult.passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                                  {rcResult.passed ? 'Capacitance OK' : 'Capacitance Low'}
                                </span>
                              </div>
                            </div>
                          )}

                          {activeTab === 'budget' && budResult && (
                            <div className="grid grid-cols-3 gap-3">
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Filter Cutoff Fc</span>
                                <span className="text-xs font-bold text-cyan-300 font-mono">
                                  {(budResult.fc_hz / 1e3).toFixed(1)} kHz
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Aliasing Attenuation</span>
                                <span className="text-xs font-bold text-slate-200 font-mono">
                                  {budResult.alias_att_db.toFixed(1)} dB
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Group Delay</span>
                                <span className="text-xs font-bold text-slate-200 font-mono">
                                  {budResult.delay_us.toFixed(2)} μs
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Phase Lag</span>
                                <span className="text-xs font-bold text-emerald-300 font-mono">
                                  {budResult.phase_lag_deg.toFixed(2)}°
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Input Referred Noise</span>
                                <span className="text-xs font-bold text-purple-300 font-mono">
                                  {budResult.noise_in_rms.toFixed(1)} μV
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Min Safe Tsamp</span>
                                <span className="text-xs font-bold text-rose-350 font-mono">
                                  {budResult.t_sample_rec_ns.toFixed(0)} ns
                                </span>
                              </div>
                            </div>
                          )}

                          {activeTab === 'afe' && afeResult && (
                            <div className="grid grid-cols-3 gap-3">
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Equivalent LSB</span>
                                <span className="text-xs font-bold text-cyan-300 font-mono">
                                  {(afeResult.lsb * 1e6).toFixed(1)} μV
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Op-Amp Vo</span>
                                <span className="text-xs font-bold text-slate-200 font-mono">
                                  {afeResult.v_pin.toFixed(3)} V
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">ADC Code Output</span>
                                <span className="text-xs font-bold text-slate-200 font-mono">
                                  {afeResult.adc_code.toFixed(0)} LSB
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Slope K</span>
                                <span className="text-xs font-bold text-emerald-300 font-mono">
                                  {afeResult.k.toExponential(3)}
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Offset B</span>
                                <span className="text-xs font-bold text-purple-300 font-mono">
                                  {afeResult.b.toFixed(3)}
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Headroom Status</span>
                                <span className={`text-[10px] font-bold ${afeResult.is_saturated ? 'text-rose-400' : 'text-emerald-400'}`}>
                                  {afeResult.is_saturated ? 'Saturated' : 'Within Range'}
                                </span>
                              </div>
                            </div>
                          )}

                          {activeTab === 'twopoint' && tpResult && (
                            <div className="grid grid-cols-3 gap-3">
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Slope K</span>
                                <span className="text-xs font-bold text-cyan-300 font-mono">
                                  {tpResult.k.toExponential(4)}
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Offset B</span>
                                <span className="text-xs font-bold text-slate-200 font-mono">
                                  {tpResult.b.toFixed(4)}
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Low Point ADC Code</span>
                                <span className="text-xs font-bold text-slate-200 font-mono">
                                  {tpX1}
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">Low Point Value</span>
                                <span className="text-xs font-bold text-emerald-300 font-mono">
                                  {tpY1.toFixed(3)}
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">High Point ADC Code</span>
                                <span className="text-xs font-bold text-purple-300 font-mono">
                                  {tpX2}
                                </span>
                              </div>
                              <div className="p-2.5 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[8px] text-slate-400 font-medium">High Point Value</span>
                                <span className="text-xs font-bold text-rose-350 font-mono">
                                  {tpY2.toFixed(3)}
                                </span>
                              </div>
                            </div>
                          )}

                          {activeTab === 'afe' && afeResult && (
                            <Card className="bg-[#0b0f19]/30 border-slate-800/80">
                              <CardHeader className="py-2.5 border-b border-slate-800/80 flex flex-row justify-between items-center">
                                <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                  <FileCode className="w-3.5 h-3.5 text-emerald-400" />
                                  MCU Scaling & Reconstruction C Code
                                </CardTitle>
                                <Button
                                  onClick={() => {
                                    const code = `// AFE Reconstruct Calibration Formula\nfloat reconstruct_val(uint16_t adc_raw) {\n    return ((float)adc_raw * ${afeResult.k.toExponential(6)}f) + (${afeResult.b.toFixed(6)}f);\n}`;
                                    navigator.clipboard.writeText(code);
                                    alert("Reconstruction C code copied to clipboard!");
                                  }}
                                  variant="outline"
                                  size="sm"
                                  className="px-2.5 py-1 text-[10px] bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-350 cursor-pointer"
                                >
                                  Copy C Code
                                </Button>
                              </CardHeader>
                              <CardContent className="p-4 bg-slate-950/40 rounded-b-xl border-t-0 font-mono text-[9px] text-emerald-350 overflow-x-auto leading-relaxed">
                                <pre>
                                  {`// AFE Reconstruct Calibration Formula\nfloat reconstruct_val(uint16_t adc_raw) {\n    return ((float)adc_raw * ${afeResult.k.toExponential(6)}f) + (${afeResult.b.toFixed(6)}f);\n}`}
                                </pre>
                              </CardContent>
                            </Card>
                          )}

                          {activeTab === 'twopoint' && tpResult && (
                            <Card className="bg-[#0b0f19]/30 border-slate-800/80">
                              <CardHeader className="py-2.5 border-b border-slate-800/80 flex flex-row justify-between items-center">
                                <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                  <FileCode className="w-3.5 h-3.5 text-emerald-400" />
                                  Two-Point Calibration C Code
                                </CardTitle>
                                <Button
                                  onClick={() => {
                                    const code = `// Two-Point Calibration Formula\nfloat calibrate_val(uint16_t adc_raw) {\n    return ((float)adc_raw * ${tpResult.k.toExponential(6)}f) + (${tpResult.b.toFixed(6)}f);\n}`;
                                    navigator.clipboard.writeText(code);
                                    alert("Calibration C code copied to clipboard!");
                                  }}
                                  variant="outline"
                                  size="sm"
                                  className="px-2.5 py-1 text-[10px] bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-350 cursor-pointer"
                                >
                                  Copy Calibration Code
                                </Button>
                              </CardHeader>
                              <CardContent className="p-4 bg-slate-950/40 rounded-b-xl border-t-0 font-mono text-[9px] text-emerald-350 overflow-x-auto leading-relaxed">
                                <pre>
                                  {`// Two-Point Calibration Formula\nfloat calibrate_val(uint16_t adc_raw) {\n    return ((float)adc_raw * ${tpResult.k.toExponential(6)}f) + (${tpResult.b.toFixed(6)}f);\n}`}
                                </pre>
                              </CardContent>
                            </Card>
                          )}
                        </div>
                      );
                    })()}
                  </CardContent>
                </Card>
              )}
              {key === 'chart' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <Card className="bg-[#0b0f19]/30 border-slate-800/80">
                    <CardHeader className="py-2.5 border-b border-slate-800/80">
                      <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-2">
                        <TrendingUp className="w-3.5 h-3.5 text-cyan-500" />
                        Simulation & Topology Schematics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 bg-slate-950/10">
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                        <div className="lg:col-span-7 bg-slate-950/20 p-2 rounded-lg border border-slate-855" style={{ height: '360px' }}>
                          <ReactECharts 
                            option={getAdcChartOption()} 
                            style={{ height: '100%', width: '100%' }}
                            notMerge={true} 
                          />
                        </div>
                        <div className="lg:col-span-5 flex flex-col justify-between p-3 rounded-lg bg-slate-950/20 border border-slate-855 min-h-[360px]">
                          <div className="text-[10px] text-slate-400 leading-relaxed mb-2">
                            <span className="font-bold text-slate-300 block mb-1">
                              {activeTab === 'rc' || activeTab === 'budget' ? 'Anti-Aliasing Filter Equivalent Circuit:' : 'AFE Equivalent Topology:'}
                            </span>
                            {activeTab === 'rc' || activeTab === 'budget' ? (
                              <p>High-fidelity sampling requires settling delay (5 Tau) to fit within the sampling aperture window (Tsamp), with anti-aliasing cutoff attenuating signals near the Nyquist frequency (&gt; 40dB suppression).</p>
                            ) : activeTab === 'afe' ? (
                              <p>Based on the chosen AFE topology (resistor divider, non-inverting amp, or shunt), the firmware reconstructs physical quantities from raw ADC codes via slope K and offset B.</p>
                            ) : (
                              <p>Two-point calibration fits system gain and offset errors from two known physical points, eliminating drift and component tolerances.</p>
                            )}
                          </div>

                          <div className="flex justify-center items-center p-2 rounded bg-slate-950/40 border border-slate-850/50">
                            {(activeTab === 'rc' || activeTab === 'budget') && (
                              <svg width="100%" height="150" viewBox="0 0 320 110" className="text-slate-350">
                                <defs>
                                  <marker id="adc_arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3" markerHeight="3" orient="auto-start-reverse">
                                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#eab308" />
                                  </marker>
                                </defs>
                                <circle cx="35" cy="50" r="2" fill="#10b981" />
                                <text x="35" y="42" textAnchor="middle" fill="#10b981" className="text-[6px] font-mono">Source Vin</text>
                                <line x1="35" y1="50" x2="60" y2="50" stroke="#64748b" strokeWidth="1.2" />
                                <path d="M 60,50 L 63,50 L 65,46 L 69,54 L 73,46 L 77,54 L 81,46 L 83,50 L 95,50" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                                <text x="71" y="40" textAnchor="middle" fill="#ef4444" className="text-[6px] font-mono">R_flt = {activeTab === 'rc' ? rcRes : sbRflt} Ω</text>
                                <line x1="95" y1="50" x2="135" y2="50" stroke="#64748b" strokeWidth="1.2" />
                                <circle cx="135" cy="50" r="2.5" fill="#cbd5e1" />
                                <line x1="135" y1="50" x2="135" y2="65" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="125" y1="65" x2="145" y2="65" stroke="#a78bfa" strokeWidth="1.5" />
                                <line x1="125" y1="69" x2="145" y2="69" stroke="#a78bfa" strokeWidth="1.5" />
                                <line x1="135" y1="69" x2="135" y2="85" stroke="#64748b" strokeWidth="1.2" />
                                <text x="150" y="70" fill="#a78bfa" className="text-[6.5px] font-mono">C_flt = {activeTab === 'rc' ? rcCap : sbCflt} nF</text>
                                <line x1="170" y1="15" x2="170" y2="95" stroke="#475569" strokeWidth="1" strokeDasharray="3,3" />
                                <text x="175" y="22" fill="#94a3b8" className="text-[5.5px] font-semibold">MCU / ADC Boundary</text>
                                <line x1="135" y1="50" x2="180" y2="50" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="180" y1="50" x2="195" y2="42" stroke="#ef4444" strokeWidth="1.2" />
                                <circle cx="180" cy="50" r="1.5" fill="#e2e8f0" />
                                <circle cx="198" cy="50" r="1.5" fill="#e2e8f0" />
                                <text x="189" y="36" textAnchor="middle" fill="#ef4444" className="text-[6px] font-mono">S_sw (Sampling Switch)</text>
                                <line x1="198" y1="50" x2="225" y2="50" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="225" y1="50" x2="225" y2="65" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="215" y1="65" x2="235" y2="65" stroke="#38bdf8" strokeWidth="1.5" />
                                <line x1="215" y1="69" x2="235" y2="69" stroke="#38bdf8" strokeWidth="1.5" />
                                <line x1="225" y1="69" x2="225" y2="85" stroke="#64748b" strokeWidth="1.2" />
                                <text x="240" y="70" fill="#38bdf8" className="text-[6.5px] font-mono">C_sh = {activeTab === 'rc' ? rcCsh : sbCsh} pF</text>
                                <line x1="135" y1="85" x2="225" y2="85" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="135" y1="85" x2="80" y2="85" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="72" y1="85" x2="88" y2="85" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="76" y1="89" x2="84" y2="89" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="79" y1="93" x2="81" y2="93" stroke="#64748b" strokeWidth="1.2" />
                                <path d="M 135,46 C 150,30 200,30 220,44" fill="none" stroke="#eab308" strokeWidth="1.2" strokeDasharray="3,2" markerEnd="url(#adc_arrow)" className="animate-pulse" />
                                <text x="175" y="32" textAnchor="middle" fill="#eab308" className="text-[5.5px] font-bold">Charge Kickback</text>
                              </svg>
                            )}
                            {activeTab === 'afe' && afeMode === 0 && (
                              <svg width="100%" height="150" viewBox="0 0 320 110" className="text-slate-350">
                                <circle cx="30" cy="50" r="2.5" fill="#10b981" />
                                <text x="30" y="42" textAnchor="middle" fill="#10b981" className="text-[6.5px] font-mono font-bold">Vin</text>
                                <line x1="30" y1="50" x2="70" y2="50" stroke="#64748b" strokeWidth="1.2" />
                                <rect x="70" y="44" width="30" height="12" fill="none" stroke="#ef4444" strokeWidth="1.5" />
                                <text x="85" y="38" textAnchor="middle" fill="#ef4444" className="text-[6px] font-mono">R1 = {afeP1} kΩ</text>
                                <line x1="100" y1="50" x2="150" y2="50" stroke="#64748b" strokeWidth="1.2" />
                                <circle cx="150" cy="50" r="2" fill="#eab308" />
                                <text x="150" y="42" textAnchor="middle" fill="#eab308" className="text-[6.5px] font-mono">Vpin (MCU Pin)</text>
                                <line x1="150" y1="50" x2="150" y2="70" stroke="#64748b" strokeWidth="1.2" />
                                <rect x="135" y="70" width="30" height="12" fill="none" stroke="#a78bfa" strokeWidth="1.5" />
                                <text x="150" y="92" textAnchor="middle" fill="#a78bfa" className="text-[6px] font-mono">R2 = {afeP2} kΩ</text>
                                <line x1="150" y1="82" x2="150" y2="95" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="140" y1="95" x2="160" y2="95" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="144" y1="99" x2="156" y2="99" stroke="#64748b" strokeWidth="1.2" />
                                <line x1="148" y1="103" x2="152" y2="103" stroke="#64748b" strokeWidth="1.2" />
                              </svg>
                            )}
                            {activeTab === 'afe' && afeMode === 1 && (
                              <svg width="100%" height="150" viewBox="0 0 320 110" className="text-slate-350">
                                <circle cx="30" cy="40" r="2.5" fill="#10b981" />
                                <text x="30" y="32" textAnchor="middle" fill="#10b981" className="text-[6.5px] font-mono font-bold">Vin</text>
                                <line x1="30" y1="40" x2="90" y2="40" stroke="#64748b" strokeWidth="1.2" />
                                <path d="M 90,20 L 150,50 L 90,80 Z" fill="none" stroke="#38bdf8" strokeWidth="2" />
                                <text x="105" y="42" fill="#cbd5e1" className="text-[8px] font-bold">+</text>
                                <text x="105" y="65" fill="#cbd5e1" className="text-[8px] font-bold">-</text>
                                <line x1="150" y1="50" x2="200" y2="50" stroke="#38bdf8" strokeWidth="1.5" />
                                <circle cx="200" cy="50" r="2.5" fill="#eab308" />
                                <text x="200" y="42" textAnchor="middle" fill="#eab308" className="text-[6.5px] font-mono">Vout = Vo</text>
                                <text x="120" y="92" textAnchor="middle" fill="#38bdf8" className="text-[6.5px] font-mono">Gain = {afeP1} V/V</text>
                              </svg>
                            )}
                            {activeTab === 'afe' && afeMode === 2 && (
                              <svg width="100%" height="150" viewBox="0 0 320 110" className="text-slate-350">
                                <line x1="20" y1="35" x2="300" y2="35" stroke="#38bdf8" strokeWidth="4" />
                                <text x="45" y="27" fill="#38bdf8" className="text-[7px] font-bold">Input Current I_in = {afePhysIn} A</text>
                                <rect x="120" y="29" width="80" height="12" fill="#1e293b" stroke="#f43f5e" strokeWidth="2" />
                                <text x="160" y="22" textAnchor="middle" fill="#f43f5e" className="text-[6.5px] font-mono">Rs = {afeP1} mΩ</text>
                                <circle cx="130" cy="35" r="2" fill="#eab308" />
                                <circle cx="190" cy="35" r="2" fill="#eab308" />
                                <line x1="130" y1="35" x2="130" y2="65" stroke="#cbd5e1" strokeWidth="1.2" />
                                <line x1="190" y1="35" x2="190" y2="65" stroke="#cbd5e1" strokeWidth="1.2" />
                                <rect x="110" y="65" width="100" height="24" fill="none" stroke="#10b981" strokeWidth="1.5" />
                                <text x="160" y="79" textAnchor="middle" fill="#10b981" className="text-[6px] font-mono">AFE Gain = {afeP2} V/V</text>
                              </svg>
                            )}
                            {activeTab === 'twopoint' && (
                              <div className="text-[10px] text-slate-500 font-mono py-12">Two-point calibration applies across hardware configurations.</div>
                            )}
                          </div>
                        </div>
                      </div>
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
