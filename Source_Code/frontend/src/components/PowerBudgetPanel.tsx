import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import {
  ArrowLeft,
  CheckCircle2,
  Info,
  PieChart,
  ShieldAlert,
  RefreshCw
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

export default function PowerBudgetPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
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
    panelKey: 'layout_powerbudgetpanel_v3_granular',
    defaultCards: ['input', 'results', 'chart', 'recommend'],
    defaultColumns: { input: 'left', results: 'right', chart: 'right', recommend: 'right' },
    defaultSpans: { input: 4, results: 8, chart: 8, recommend: 8 },
    defaultHeights: { input: 800, results: 210, chart: 300, recommend: 430 }
  });

  const [vin, setVin] = useState<number>(48);
  const [vout, setVout] = useState<number>(12);
  const [iout, setIout] = useState<number>(10);

  const [lossSw, setLossSw] = useState<number>(2.5);
  const [lossMag, setLossMag] = useState<number>(1.2);
  const [lossRect, setLossRect] = useState<number>(0.8);
  const [lossCap, setLossCap] = useState<number>(0.3);
  const [lossCtrl, setLossCtrl] = useState<number>(0.5);
  const [lossMisc, setLossMisc] = useState<number>(0.2);

  const [report, setReport] = useState<{
    pout_w: number;
    p_loss_total_w: number;
    pin_w: number;
    efficiency_pct: number;
    iin_a?: number;
  } | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/power_budget/calc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vin,
          vout,
          iout,
          l_sw: lossSw,
          l_mag: lossMag,
          l_rect: lossRect,
          l_cap: lossCap,
          l_ctrl: lossCtrl,
          l_misc: lossMisc
        })
      });
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Calculation failed; please check input values');
      }

      const data = await response.json();
      setReport(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleCalculate();
  }, [vin, vout, iout, lossSw, lossMag, lossRect, lossCap, lossCtrl, lossMisc]);

  const getChartOption = () => {
    const data = [
      { value: lossSw, name: 'Switching Loss' },
      { value: lossMag, name: 'Magnetic Loss' },
      { value: lossRect, name: 'Rectification Loss' },
      { value: lossCap, name: 'Capacitor Loss' },
      { value: lossCtrl, name: 'Control Logic Loss' },
      { value: lossMisc, name: 'Stray/PCB Loss' }
    ].filter(item => item.value > 0);

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} W ({d}%)',
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9', fontSize: 10 }
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 9 },
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 8
      },
      series: [
        {
          name: 'Loss Breakdown',
          type: 'pie',
          radius: ['50%', '75%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 4,
            borderColor: '#0f172a',
            borderWidth: 1.5
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 11,
              fontWeight: 'bold',
              color: '#ffffff',
              formatter: '{b}\n{c} W'
            }
          },
          labelLine: {
            show: false
          },
          data: data,
          color: ['#38bdf8', '#fb7185', '#fbbf24', '#c084fc', '#4ade80', '#94a3b8']
        }
      ]
    };
  };

  const isLowEfficiency = report && report.efficiency_pct < 85.0;

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Top Header */}
      <div className="flex-shrink-0 flex justify-between items-center gap-4 py-2 border-b border-slate-900 pb-3 mb-3">
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
            <h1 className="text-base font-bold text-white tracking-tight">Converter Loss & Efficiency Budget</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Analyze multi-component loss breakdown and full-system efficiency across active switches, magnetics, capacitors, and control circuits.
            </p>
          </div>
        </div>
        <Button
          onClick={handleResetLayout}
          variant="outline"
          size="sm"
          className="text-xs text-slate-350 border-slate-800 hover:bg-slate-850 hover:text-white flex items-center gap-1 bg-transparent shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset Layout
        </Button>
      </div>

      {/* Errors / Warnings */}
      {error && (
        <div className="flex-shrink-0 px-3 pt-3">
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* DragDeck area */}
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
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md space-y-4">
                  <div className="flex items-center justify-between mb-3 border-b border-slate-800/60 pb-2">
                    <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wide flex items-center gap-2">
                      Power Budget & Operating Conditions
                    </h3>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                      Main Input / Output Ratings
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Input Voltage Vin (V)</label>
                        <input type="number" value={vin} onChange={(e) => setVin(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Output Voltage Vout (V)</label>
                        <input type="number" value={vout} onChange={(e) => setVout(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                      <div className="col-span-2">
                        <label className="text-[10px] text-slate-400 block mb-1">Load Output Current Iout (A)</label>
                        <input type="number" value={iout} onChange={(e) => setIout(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                    </div>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                      Power Stage Loss Breakdown (W)
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Active Switch Conduction & Switching P_sw (W)</label>
                        <input type="number" step="0.1" value={lossSw} onChange={(e) => setLossSw(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Magnetics Copper & Core Loss P_mag (W)</label>
                        <input type="number" step="0.1" value={lossMag} onChange={(e) => setLossMag(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Rectifier / Synchronous FET Loss P_rect (W)</label>
                        <input type="number" step="0.1" value={lossRect} onChange={(e) => setLossRect(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">Capacitor ESR Loss P_cap (W)</label>
                        <input type="number" step="0.1" value={lossCap} onChange={(e) => setLossCap(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                    </div>
                  </div>

                  <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                    <div className="font-semibold text-xs text-slate-300 border-b border-slate-800/60 pb-1 mb-1">
                      Control Logic & PCB Stray Losses (W)
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">IC / Controller Loss (W)</label>
                        <input type="number" step="0.1" value={lossCtrl} onChange={(e) => setLossCtrl(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-400 block mb-1">PCB Stray & Trace Loss (W)</label>
                        <input type="number" step="0.1" value={lossMisc} onChange={(e) => setLossMisc(e.target.value as any)} className="form-input w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:border-blue-500 focus:outline-none" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md flex flex-col gap-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white">Efficiency & System Power Metrics</span>
                  </div>

                  {report && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col">
                        <span className="text-[9px] text-slate-400 font-semibold tracking-wider uppercase">Output Power (Pout)</span>
                        <span className="text-lg font-black text-white font-mono mt-0.5">
                          {report.pout_w.toFixed(2)} W
                        </span>
                      </div>

                      <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col">
                        <span className="text-[9px] text-slate-400 font-semibold tracking-wider uppercase">Total Losses (Ploss)</span>
                        <span className="text-lg font-black text-rose-400 font-mono mt-0.5">
                          {report.p_loss_total_w.toFixed(2)} W
                        </span>
                      </div>

                      <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col">
                        <span className="text-[9px] text-slate-400 font-semibold tracking-wider uppercase">Input Power (Pin)</span>
                        <span className="text-lg font-black text-cyan-400 font-mono mt-0.5">
                          {report.pin_w.toFixed(2)} W
                        </span>
                        <span className="text-[9px] text-slate-400 mt-1">Equivalent Input Current: <strong className="text-cyan-300 font-mono">{(report.iin_a ?? (report.pin_w / vin)).toFixed(2)} A</strong></span>
                      </div>

                      <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col">
                        <span className="text-[9px] text-slate-400 font-semibold tracking-wider uppercase">Efficiency</span>
                        <span className="text-lg font-black text-emerald-400 font-mono mt-0.5">
                          {report.efficiency_pct.toFixed(2)} %
                        </span>
                      </div>
                    </div>
                  )}

                  {/* DRC Alert Panel */}
                  {report && (
                    <div className="space-y-2">
                      {isLowEfficiency ? (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400 animate-pulse">
                          <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-bold block">⚠️ Low Converter Efficiency DRC Warning</span>
                            <span className="mt-1 block">Calculated efficiency is {report.efficiency_pct.toFixed(2)}%, which is below the industrial volume production threshold (85.0%). Total dissipated loss reaches {report.p_loss_total_w.toFixed(2)} W. It is recommended to optimize the highest-contributing loss sub-item (e.g. lower Rds(on) FETs, gate drive optimization, or lower-loss magnetic core materials).</span>
                          </div>
                        </div>
                      ) : (
                        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                          <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                          <span>✅ Efficiency Compliant: Full system calculated efficiency is {report.efficiency_pct.toFixed(2)}%, satisfying design target requirements.</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {key === 'chart' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md flex flex-col gap-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <PieChart className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold text-white">Full-System Loss Distribution Breakdown</span>
                  </div>
                  <div className="h-64">
                    <ReactECharts notMerge={true} option={getChartOption()} style={{ height: '100%', width: '100%' }} />
                  </div>
                </div>
              )}

              {key === 'recommend' && (
                <div className="overflow-y-auto scrollbar-thin p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md flex flex-col gap-4" style={{ height: cardHeights[key] ? cardHeights[key] - 50 : '100%' }}>
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <Info className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-bold text-white">Loss Factor Characteristics & Optimization Recommendations</span>
                  </div>
                  <div className="text-slate-400 text-xs">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b border-slate-800 text-[10px] text-slate-400">
                            <th className="pb-2 font-semibold">Loss Category</th>
                            <th className="pb-2 font-semibold text-center">Current Power (W)</th>
                            <th className="pb-2 font-semibold text-right">Optimization Guideline</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-850/60">
                          <tr className="hover:bg-slate-900/10 transition-colors">
                            <td className="py-2.5 font-medium text-slate-300">Switching Devices</td>
                            <td className="py-2.5 text-center font-mono text-rose-300">{lossSw.toFixed(1)}W</td>
                            <td className="py-2.5 text-right text-[11px] text-slate-400">
                              <span>If dominant, high-frequency switching overlap is significant; optimize gate resistor </span>
                              <Latex math="R_g" />
                              <span> or select wide-bandgap devices (SiC/GaN) with lower </span>
                              <Latex math="Q_g" />
                              <span>.</span>
                            </td>
                          </tr>
                          <tr className="hover:bg-slate-900/10 transition-colors">
                            <td className="py-2.5 font-medium text-slate-300">Magnetics</td>
                            <td className="py-2.5 text-center font-mono text-rose-300">{lossMag.toFixed(1)}W</td>
                            <td className="py-2.5 text-right text-[11px] text-slate-400">Comprises core and copper losses. Optimize air-gap depth, use multi-strand Litz wire to minimize skin effect, or choose low-loss MnZn ferrite / Sendust cores.</td>
                          </tr>
                          <tr className="hover:bg-slate-900/10 transition-colors">
                            <td className="py-2.5 font-medium text-slate-300">Rectification</td>
                            <td className="py-2.5 text-center font-mono text-rose-300">{lossRect.toFixed(1)}W</td>
                            <td className="py-2.5 text-right text-[11px] text-slate-400">
                              <span>Mainly caused by Schottky forward voltage drop </span>
                              <Latex math="V_f" />
                              <span>. Replace with synchronous rectification (SR) MOSFETs to lower the effective on-state drop to ~0.1V.</span>
                            </td>
                          </tr>
                          <tr className="hover:bg-slate-900/10 transition-colors">
                            <td className="py-2.5 font-medium text-slate-300">Capacitors</td>
                            <td className="py-2.5 text-center font-mono text-rose-300">{lossCap.toFixed(1)}W</td>
                            <td className="py-2.5 text-right text-[11px] text-slate-400">
                              <span>Capacitor </span>
                              <Latex math="ESR" />
                              <span> heating caused by high AC ripple current. Parallel multiple film or MLCC capacitors to reduce net </span>
                              <Latex math="ESR" />
                              <span>.</span>
                            </td>
                          </tr>
                          <tr className="hover:bg-slate-900/10 transition-colors">
                            <td className="py-2.5 font-medium text-slate-300">Control Logic</td>
                            <td className="py-2.5 text-center font-mono text-rose-300">{lossCtrl.toFixed(1)}W</td>
                            <td className="py-2.5 text-right text-[11px] text-slate-400">IC operating and bias power. Select low-quiescent-current PWM controllers and enable burst-mode / green-mode operation at light loads.</td>
                          </tr>
                          <tr className="hover:bg-slate-900/10 transition-colors">
                            <td className="py-2.5 font-medium text-slate-300">Stray / PCB</td>
                            <td className="py-2.5 text-center font-mono text-rose-300">{lossMisc.toFixed(1)}W</td>
                            <td className="py-2.5 text-right text-[11px] text-slate-400">Caused by copper trace resistance, via resistance, and parasitic loop inductance. Widen high-current power tracks and minimize high-frequency loop area.</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
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
