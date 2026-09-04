import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Flame,
  Info,
  ShieldAlert,
  TrendingUp
} from 'lucide-react';

const LDO_BOM_DATABASE = [
  { name: 'LM1117-3.3', package: 'SOT-223', maxVin: 15.0, maxIout: 0.8, vdrop: 1.2, iqTypical: 0.005, rja: 61.6 },
  { name: 'TLV75733P', package: 'SOT-23-5', maxVin: 5.5, maxIout: 1.0, vdrop: 0.2, iqTypical: 0.000025, rja: 140.0 },
  { name: 'REG1117-3.3', package: 'SOT-223', maxVin: 15.0, maxIout: 0.8, vdrop: 1.2, iqTypical: 0.005, rja: 65.0 },
  { name: 'MIC5219-3.3', package: 'SOT-23-5', maxVin: 12.0, maxIout: 0.5, vdrop: 0.35, iqTypical: 0.00008, rja: 220.0 },
  { name: 'NCP1117-3.3', package: 'SOT-223', maxVin: 20.0, maxIout: 1.0, vdrop: 1.2, iqTypical: 0.006, rja: 67.0 },
  { name: 'LD39150DT33', package: 'TO-252', maxVin: 6.0, maxIout: 1.5, vdrop: 0.4, iqTypical: 0.002, rja: 54.0 },
  { name: 'LT1763', package: 'SOIC-8', maxVin: 20.0, maxIout: 0.5, vdrop: 0.3, iqTypical: 0.00003, rja: 50.0 }
];

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

export default function LdoThermalPanel({ onBack }: { onBack: () => void }) {
  const [vin, setVin] = useState<number>(12.0);
  const [vout, setVout] = useState<number>(3.3);
  const [iout, setIout] = useState<number>(0.3);
  const [iq, setIq] = useState<number>(0.005);
  const [ta, setTa] = useState<number>(50.0);
  const [rja, setRja] = useState<number>(65.0);

  // PCB Copper Cooling Mode
  const [enablePcbCopper, setEnablePcbCopper] = useState<boolean>(false);
  const [copperArea, setCopperArea] = useState<number>(10.0);
  const [copperOz, setCopperOz] = useState<number>(1.0);
  const [thetaJc, setThetaJc] = useState<number>(15.0);

  const [activeChartTab, setActiveChartTab] = useTabHistoryState<'vin' | 'iout'>('vin', 'activeChartTab');
  const activeChartTabRef = useRef(activeChartTab);
  useEffect(() => { activeChartTabRef.current = activeChartTab; }, [activeChartTab]);

  const [ldoResult, setLdoResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const packageType: string = rja === 65.0 ? 'SOT-223' : rja === 140.0 ? 'SOT-23-5' : rja === 54.0 ? 'TO-252' : 'Custom';

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
    panelKey: 'layout_ldothermal_v4',
    activeTab: 'ldothermal',
    defaultCards: ['input', 'theory', 'results', 'temp_curve', 'bom', 'drc'],
    defaultColumns: { input: 'left', theory: 'left', results: 'right', temp_curve: 'right', bom: 'right', drc: 'right' },
    defaultSpans: { input: 4, theory: 4, results: 8, temp_curve: 8, bom: 8, drc: 8 },
    defaultHeights: { input: 500, theory: 280, results: 300, temp_curve: 280, bom: 400, drc: 280 }
  });

  const runCalculation = async () => {
    if (vin <= vout) {
      setError('Input voltage Vin must be strictly greater than output voltage Vout');
      setLdoResult(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      let currentRja = rja;
      if (enablePcbCopper) {
        const copperRes = await apiFetch('/api/calculate/ldo_thermal/pcb_copper', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            area_cm2: Math.max(copperArea, 0.01),
            copper_oz: copperOz,
            theta_jc: thetaJc
          })
        });
        if (copperRes.ok) {
          const copperData = await copperRes.json();
          currentRja = copperData.design.theta_ja_eff;
        }
      }

      const res = await apiFetch('/api/calculate/ldo_thermal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vin,
          vout,
          iout,
          iq,
          rja: currentRja,
          ta
        })
      });
      
      if (!res.ok) {
        const errDetail = await res.json();
        throw new Error(errDetail.detail || 'LDO thermal calculation API error');
      }

      const data = await res.json();
      setLdoResult(data.design);
    } catch (e: any) {
      setError(e.message);
      setLdoResult(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runCalculation();
  }, [vin, vout, iout, iq, ta, rja, enablePcbCopper, copperArea, copperOz, thetaJc]);

  const getTjColorClass = (tj: number) => {
    if (tj >= 125.0) return 'text-rose-500';
    if (tj >= 100.0) return 'text-amber-500';
    return 'text-emerald-500';
  };

  const getChartOption = () => {
    if (!ldoResult) return {};
    const isVinSweep = activeChartTab === 'vin';
    const xData = isVinSweep ? ldoResult.vin_sweep : ldoResult.iout_sweep;
    const yData = isVinSweep ? ldoResult.tj_vs_vin : ldoResult.tj_vs_iout;
    if (!xData || !yData || xData.length === 0) return {};
    const xMax = Math.max(...xData);

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: 'rgba(6, 182, 212, 0.3)',
        textStyle: { color: '#f1f5f9', fontSize: 10 },
        extraCssText: 'backdrop-filter: blur(8px); border: 1px solid rgba(6, 182, 212, 0.3); box-shadow: 0 0 10px rgba(6, 182, 212, 0.15);',
        formatter: (params: any) => {
          const val = params[0];
          if (!val || !val.value) return '';
          const xVal = parseFloat(val.value[0]);
          const yVal = parseFloat(val.value[1]);
          return `${isVinSweep ? 'Input Voltage' : 'Output Current'}: ${xVal.toFixed(2)}${isVinSweep ? ' V' : ' A'}<br/>Predicted Tj: <span class="font-bold text-cyan-400">${yVal.toFixed(1)} °C</span>`;
        }
      },
      grid: { left: '8%', right: '18%', top: '15%', bottom: '20%', containLabel: true },
      xAxis: {
        type: 'value',
        name: isVinSweep ? 'Vin (V)' : 'Iout (A)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#94a3b8', fontSize: 8 },
        axisLine: { lineStyle: { color: '#334155' } },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        name: 'Junction Tj (°C)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#94a3b8', fontSize: 8 },
        axisLine: { lineStyle: { color: '#334155' } },
        splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.05)' } }
      },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', height: 12, bottom: 5, start: 0, end: 100, textStyle: { color: '#94a3b8', fontSize: 7 } }
      ],
      series: [
        {
          name: 'Junction Tj',
          data: xData.map((x: number, idx: number) => [x, yData[idx]]),
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 3, color: '#06b6d4', shadowBlur: 8, shadowColor: 'rgba(6, 182, 212, 0.4)' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(6, 182, 212, 0.25)' },
                { offset: 1, color: 'rgba(6, 182, 212, 0)' }
              ]
            }
          }
        },
        {
          name: 'Limit 125°C',
          type: 'line',
          symbol: 'circle',
          symbolSize: 0,
          showSymbol: true,
          silent: true,
          lineStyle: { color: '#ef4444', type: 'dashed', width: 1.2 },
          label: {
            show: true,
            position: 'right',
            formatter: (params: any) => {
              if (params.dataIndex === 1) return 'Limit 125°C';
              return '';
            },
            color: '#ef4444',
            fontSize: 9,
            fontWeight: 'bold'
          },
          data: [
            [0, 125.0],
            [xMax, 125.0]
          ]
        },
        {
          name: 'Warning 100°C',
          type: 'line',
          symbol: 'circle',
          symbolSize: 0,
          showSymbol: true,
          silent: true,
          lineStyle: { color: '#eab308', type: 'dashed', width: 1.2 },
          label: {
            show: true,
            position: 'right',
            formatter: (params: any) => {
              if (params.dataIndex === 1) return 'Warning 100°C';
              return '';
            },
            color: '#eab308',
            fontSize: 9,
            fontWeight: 'bold'
          },
          data: [
            [0, 100.0],
            [xMax, 100.0]
          ]
        }
      ]
    };
  };

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
            <h1 className="text-base font-bold text-white tracking-tight">LDO Thermal & Dissipation Design</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Calculate LDO linear regulator thermal dissipation, determine PCB copper cooling requirements, and verify junction temperature limits.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={handleResetLayout} variant="outline" size="sm" className="bg-slate-900 border border-slate-800 text-slate-350 hover:bg-slate-800 text-[10px] rounded-lg">
            Reset Layout
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs flex items-center gap-2 animate-shake">
          <ShieldAlert className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}</span>
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
              onHeightResizeStartTop={handleHeightResizeStartTop}
              onResetHeight={() => handleResetCardHeight(key)}
            >
              {key === 'input' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Operating Conditions & Thermal Inputs</span>
                  </div>

                  <div className="space-y-3.5">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Input Voltage Vin (V)</label>
                        <input type="number" step="0.1" value={vin} onChange={(e) => setVin(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Output Voltage Vout (V)</label>
                        <input type="number" step="0.1" value={vout} onChange={(e) => setVout(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Output Current Iout (A)</label>
                        <input type="number" step="0.01" value={iout} onChange={(e) => setIout(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">Quiescent Current Iq (A)</label>
                        <input type="number" step="0.0001" value={iq} onChange={(e) => setIq(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Ambient Temperature Ta (°C)</label>
                      <input type="number" step="1" value={ta} onChange={(e) => setTa(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                    </div>

                    <div className="flex items-center gap-2 border-t border-slate-800 pt-3.5">
                      <input
                        type="checkbox"
                        id="enablePcbCopper"
                        checked={enablePcbCopper}
                        onChange={(e) => setEnablePcbCopper(e.target.checked)}
                        className="rounded border-slate-800 bg-slate-950 text-blue-500 focus:ring-blue-500 h-3.5 w-3.5 cursor-pointer"
                      />
                      <label htmlFor="enablePcbCopper" className="text-[10px] font-bold text-slate-350 cursor-pointer select-none">
                        Enable PCB Copper Thermal Spreading Model
                      </label>
                    </div>

                    {!enablePcbCopper ? (
                      <div className="flex flex-col gap-3 pt-2">
                        <span className="text-[9px] text-slate-400 font-semibold">Standard Package & Thermal Resistance θ_JA</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Preset Package (Typical)</label>
                            <select
                              value={rja}
                              onChange={(e) => setRja(e.target.value as any)}
                              className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white cursor-pointer focus:outline-none"
                            >
                              <option value={65.0}>SOT-223 (65.0 °C/W)</option>
                              <option value={140.0}>SOT-23-5 (140.0 °C/W)</option>
                              <option value={54.0}>TO-252 (54.0 °C/W)</option>
                              <option value={50.0}>SOIC-8 (50.0 °C/W)</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Custom θ_JA (°C/W)</label>
                            <input type="number" step="0.1" value={rja} onChange={(e) => setRja(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-3 pt-2">
                        <span className="text-[9px] text-slate-400 font-semibold">PCB Copper Thermal Geometry & Conduction Parameters</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Copper Area (cm²)</label>
                            <input type="number" step="0.5" value={copperArea} onChange={(e) => setCopperArea(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Copper Weight (oz)</label>
                            <select
                              value={copperOz}
                              onChange={(e) => setCopperOz(e.target.value as any)}
                              className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white cursor-pointer focus:outline-none"
                            >
                              <option value={1.0}>1.0 oz (Standard Board)</option>
                              <option value={2.0}>2.0 oz (Heavy Copper)</option>
                              <option value={3.0}>3.0 oz (Ultra-Heavy Copper)</option>
                            </select>
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Junction-to-Case θ_JC (°C/W)</label>
                          <input type="number" step="0.1" value={thetaJc} onChange={(e) => setThetaJc(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {key === 'theory' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <BookOpen className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">LDO Thermal Dissipation Physical Principles</span>
                  </div>
                  <div className="text-[10px] text-slate-400 space-y-4 leading-relaxed">
                    <div className="space-y-1">
                      <span className="font-semibold text-slate-350">1. Total Power Dissipation:</span>
                      <Latex math={"P_D = (V_{in} - V_{out}) \\cdot I_{out} + V_{in} \\cdot I_q"} block />
                    </div>
                    <div className="space-y-1">
                      <span className="font-semibold text-slate-350">2. Electrical Conversion Efficiency:</span>
                      <Latex math={"\\eta = \\frac{V_{out} \\cdot I_{out}}{V_{in} \\cdot (I_{out} + I_q)} \\cdot 100\\%"} block />
                    </div>
                    <div className="space-y-1">
                      <span className="font-semibold text-slate-350">3. Peak Silicon Junction Temperature:</span>
                      <Latex math={"T_J = T_a + P_D \\cdot \\theta_{JA}"} block />
                    </div>
                    {enablePcbCopper && (
                      <div className="space-y-1">
                        <span className="font-semibold text-slate-350">4. PCB Copper Equivalent Convective Thermal Resistance:</span>
                        <Latex math={"\\theta_{JA} = \\theta_{JC} + \\theta_{\\text{copper}} = \\theta_{JC} + \\frac{75}{\\sqrt{A_{\\text{copper}}} \\cdot K_{\\text{oz}}}"} block />
                      </div>
                    )}
                    <p className="text-[8.5px] text-slate-550 border-t border-slate-850 pt-2 leading-relaxed">
                      * Note: For linear regulators, all dissipated power is converted directly into Joule heat. In large dropout conditions, junction temperature rises sharply, risking over-temperature shutdown (OTP).
                    </p>
                  </div>
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Thermal & Power Synthesis Results</span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    <div className="glass-card p-3 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-1">
                      <span className="text-[8px] text-slate-400 font-medium">Predicted Junction Temperature (Tj)</span>
                      <span className={`text-base font-bold font-mono ${getTjColorClass(ldoResult?.t_j ?? 0.0)}`}>
                        {(ldoResult?.t_j ?? 0.0).toFixed(1)} <span className="text-[10px] text-slate-400">°C</span>
                      </span>
                    </div>

                    <div className="glass-card p-3 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-1">
                      <span className="text-[8px] text-slate-400 font-medium">Total Power Dissipation (Pd)</span>
                      <span className="text-base font-bold text-slate-200 font-mono">
                        {(ldoResult?.p_diss_w ?? 0.0).toFixed(3)} <span className="text-[10px] text-slate-400">W</span>
                      </span>
                      <span className="text-[8px] text-slate-550">Quiescent Power: {((ldoResult?.p_iq_w ?? 0.0) * 1000).toFixed(1)} mW</span>
                    </div>

                    <div className="glass-card p-3 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-1">
                      <span className="text-[8px] text-slate-400 font-medium">Conversion Efficiency</span>
                      <span className="text-base font-bold text-slate-200 font-mono">
                        {(ldoResult?.efficiency_pct ?? 0.0).toFixed(1)}%
                      </span>
                    </div>

                    <div className="glass-card p-3 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-1">
                      <span className="text-[8px] text-slate-400 font-medium">Package / Effective Thermal Resistance</span>
                      <span className="text-xs font-bold text-slate-200 font-mono">
                        {enablePcbCopper ? 'PCB Copper Spreading' : packageType} ({(ldoResult ? (enablePcbCopper ? thetaJc + (ldoResult.t_j - ta) / ldoResult.p_diss_w : rja) : rja).toFixed(1)} °C/W)
                      </span>
                    </div>

                    <div className="glass-card p-3 rounded-lg border border-slate-855 bg-slate-900/20 flex flex-col gap-1">
                      <span className="text-[8px] text-slate-400 font-medium">Temperature Rise ΔT_JA</span>
                      <span className="text-base font-bold text-slate-200 font-mono">
                        {Math.max(0, (ldoResult?.t_j ?? ta) - ta).toFixed(1)} <span className="text-[10px] text-slate-400">°C</span>
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {key === 'temp_curve' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
                    <span className="text-xs font-bold text-white">Steady-State Junction Temperature Sweep Curve</span>
                    <div className="bg-[#020617] border border-slate-800 rounded p-0.5 flex gap-1 scale-90 origin-right">
                      <button
                        onClick={() => setActiveChartTab('vin')}
                        className={`px-2 py-0.5 rounded text-[8px] font-bold cursor-pointer ${
                          activeChartTab === 'vin' ? 'bg-blue-600/30 text-white' : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        Vin Sweep
                      </button>
                      <button
                        onClick={() => setActiveChartTab('iout')}
                        className={`px-2 py-0.5 rounded text-[8px] font-bold cursor-pointer ${
                          activeChartTab === 'iout' ? 'bg-blue-600/30 text-white' : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        Iout Sweep
                      </button>
                    </div>
                  </div>
                  <div className="w-full h-[180px] flex items-center justify-center">
                    {ldoResult ? (
                      <ReactECharts option={getChartOption()} notMerge={true} style={{ width: '100%', height: '100%' }} />
                    ) : (
                      <span className="text-xs text-slate-500">Waiting for curve data...</span>
                    )}
                  </div>
                </div>
              )}

              {key === 'bom' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <span className="text-xs font-bold text-white">Recommended Commercial LDO BOM</span>
                  </div>
                  <div className="overflow-x-auto scrollbar-thin rounded-lg border border-slate-800/80">
                    <table className="w-full text-[10px] text-left text-slate-350 border-collapse">
                      <thead className="text-[9px] uppercase bg-slate-950/80 text-slate-300 border-b border-slate-800">
                        <tr>
                          <th className="px-3 py-2 border-r border-slate-800">Part Number</th>
                          <th className="px-3 py-2 border-r border-slate-800">Package</th>
                          <th className="px-3 py-2 border-r border-slate-800 text-center">Rated Vin</th>
                          <th className="px-3 py-2 border-r border-slate-800 text-center">Max Iout</th>
                          <th className="px-3 py-2 border-r border-slate-800 text-center">Typical Vdrop</th>
                          <th className="px-3 py-2 border-r border-slate-800 text-center">Quiescent Iq</th>
                          <th className="px-3 py-2 border-r border-slate-800 text-center">Thermal θ_JA</th>
                          <th className="px-3 py-2">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {LDO_BOM_DATABASE.map((dev, idx) => {
                          const isVinOk = dev.maxVin >= vin * 1.2;
                          const isIoutOk = dev.maxIout >= iout * 1.5;
                          const isPass = isVinOk && isIoutOk;

                          let statusText = 'Recommended';
                          let statusClass = 'text-emerald-400 font-semibold';
                          if (!isVinOk) {
                            statusText = 'Vin Below Rating';
                            statusClass = 'text-rose-400';
                          } else if (!isIoutOk) {
                            statusText = 'Current Exceeded';
                            statusClass = 'text-amber-400';
                          }

                          return (
                            <tr key={idx} className={`border-b border-slate-855/80 bg-slate-900/10 hover:bg-slate-800/20 transition-colors ${isPass && idx === 0 ? 'bg-emerald-950/15 border-l-2 border-l-emerald-500' : ''}`}>
                              <td className="px-3 py-2 border-r border-slate-800 text-white flex items-center gap-1.5">
                                {dev.name}
                                {isPass && idx === 0 && (
                                  <span className="bg-emerald-500/20 text-emerald-400 text-[8px] px-1 rounded border border-emerald-500/30 scale-90 origin-left">Preferred</span>
                                )}
                              </td>
                              <td className="px-3 py-2 border-r border-slate-800 text-slate-300">{dev.package}</td>
                              <td className="px-3 py-2 border-r border-slate-800 text-center text-slate-200">{dev.maxVin} V</td>
                              <td className="px-3 py-2 border-r border-slate-800 text-center text-slate-200">{dev.maxIout} A</td>
                              <td className="px-3 py-2 border-r border-slate-800 text-center text-slate-200">{dev.vdrop} V</td>
                              <td className="px-3 py-2 border-r border-slate-800 text-center text-slate-200">{(dev.iqTypical * 1000).toFixed(2)} mA</td>
                              <td className="px-3 py-2 border-r border-slate-800 text-center text-slate-200">{dev.rja} °C/W</td>
                              <td className={`px-3 py-2 font-medium ${statusClass}`}>{statusText}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <div className="text-[8px] text-slate-500 leading-relaxed italic mt-2">
                    * Sizing criteria: Standard commercial parts derated with &ge;1.2&times; voltage margin and &ge;1.5&times; current margin, sorted by thermal resistance and quiescent power.
                  </div>
                </div>
              )}

              {key === 'drc' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md animate-fade-in">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-bold text-white">Thermal & Efficiency DRC Validation</span>
                  </div>
                  <div className="flex flex-col gap-2.5">
                    {/* Junction Temp Check */}
                    {(ldoResult?.t_j ?? 0.0) > 125 ? (
                      <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed">
                        <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                        <span><strong>Junction Temperature Exceeded:</strong> Predicted junction temperature is <span className="font-mono text-white">{(ldoResult?.t_j ?? 0.0).toFixed(1)}°C</span>, exceeding the standard 125°C threshold. Increase PCB copper spreading area, improve airflow, or select a lower thermal resistance package.</span>
                      </div>
                    ) : (ldoResult?.t_j ?? 0.0) > 100 ? (
                      <div className="flex items-start gap-2 text-[10px] text-amber-300 border border-amber-500/20 bg-amber-500/5 p-2 rounded-lg leading-relaxed">
                        <Info className="w-3.5 h-3.5 shrink-0 text-amber-500 mt-0.5" />
                        <span><strong>Elevated Junction Temperature:</strong> Predicted junction temperature is <span className="font-mono text-white">{(ldoResult?.t_j ?? 0.0).toFixed(1)}°C</span>, exceeding the 100°C warning threshold. Consider a larger package or additional thermal relief copper.</span>
                      </div>
                    ) : (
                      <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed">
                        <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                        <span><strong>Junction Temperature Safe:</strong> Predicted junction temperature is <span className="font-mono text-white">{(ldoResult?.t_j ?? 0.0).toFixed(1)}°C</span>, well within the 100°C derated design limit.</span>
                      </div>
                    )}

                    {/* High Drop Voltage & Low Efficiency Topology Recommendation */}
                    {(vin - vout > 5.0 && iout > 0.5 && (ldoResult?.efficiency_pct ?? 0.0) < 40.0) && (
                      <div className="flex items-start gap-2 text-[10px] text-rose-300 border border-rose-500/40 bg-rose-950/30 p-2.5 rounded-lg leading-relaxed shadow-lg">
                        <Flame className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                        <div>
                          <strong className="text-rose-400 block mb-0.5">⚠️ Buck Converter Topology Recommended</strong>
                          <span>Dropout voltage exceeds 5V ({(vin - vout).toFixed(1)}V) at {iout}A load, driving efficiency down to <strong>{(ldoResult?.efficiency_pct ?? 0.0).toFixed(1)}%</strong> with {(ldoResult?.p_diss_w ?? 0.0).toFixed(2)}W dissipated as heat. Consider switching to a switching Buck converter for higher efficiency.</span>
                        </div>
                      </div>
                    )}

                    {/* Efficiency Check */}
                    {(ldoResult?.efficiency_pct ?? 0.0) < 85 ? (
                      <div className="flex items-start gap-2 text-[10px] text-amber-300 border border-amber-500/20 bg-amber-500/5 p-2 rounded-lg leading-relaxed">
                        <Info className="w-3.5 h-3.5 shrink-0 text-amber-500 mt-0.5" />
                        <span><strong>Low Conversion Efficiency:</strong> Efficiency is <span className="font-mono text-white">{(ldoResult?.efficiency_pct ?? 0.0).toFixed(1)}%</span>. High voltage drop ({(vin - vout).toFixed(1)}V) dissipates <span className="font-mono text-white">{(ldoResult?.p_diss_w ?? 0.0).toFixed(3)} W</span> as heat. Pre-regulate with a switching stage if thermal margins are tight.</span>
                      </div>
                    ) : (
                      <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed">
                        <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                        <span><strong>Efficiency Compliant:</strong> Current efficiency is <span className="font-mono text-white">{(ldoResult?.efficiency_pct ?? 0.0).toFixed(1)}%</span> with acceptable heat generation.</span>
                      </div>
                    )}

                    {/* Dropout Margin Check */}
                    {vin - vout < 0.2 ? (
                      <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed">
                        <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                        <span><strong>Dropout Voltage Insufficient:</strong> Input-to-output differential is only <span className="font-mono text-white">{(vin - vout).toFixed(2)}V</span>, below the physical dropout limit (0.2V); the regulator may fall out of regulation into dropout mode.</span>
                      </div>
                    ) : vin - vout < 1.2 && (packageType === 'SOT-223' || packageType === 'SOT-89') ? (
                      <div className="flex items-start gap-2 text-[10px] text-amber-300 border border-amber-500/20 bg-amber-500/5 p-2 rounded-lg leading-relaxed">
                        <Info className="w-3.5 h-3.5 shrink-0 text-amber-500 mt-0.5" />
                        <span><strong>Dropout Margin Notice:</strong> Dropout is <span className="font-mono text-white">{(vin - vout).toFixed(2)}V</span>. Standard regulators like LM1117 require at least 1.2V dropout. Use ultra-low-dropout (ULDO) devices such as TLV757P if maintaining low headroom.</span>
                      </div>
                    ) : null}

                    {/* Heatsink Limit Check */}
                    {ta >= 85 && (
                      <div className="flex items-start gap-2 text-[10px] text-amber-300 border border-amber-500/20 bg-amber-500/5 p-2 rounded-lg leading-relaxed">
                        <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-amber-500 mt-0.5" />
                        <span><strong>High Ambient Temperature:</strong> Ambient temperature <span className="font-mono text-white">{ta}°C</span> approaches industrial limits, significantly constraining natural convective dissipation.</span>
                      </div>
                    )}
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
