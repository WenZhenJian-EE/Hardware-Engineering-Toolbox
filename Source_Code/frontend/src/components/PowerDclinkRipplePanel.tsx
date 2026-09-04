import { useTabHistoryState } from '../lib/tabHistory';
// Physical Identifier: DC-Link Capacitor Ripple & Lifetime (id: power_dclink)
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
  Activity,
  ArrowLeft,
  CheckCircle2,
  Info,
  LineChart,
  RotateCcw,
  Settings,
  ShieldAlert,
  Sliders,
  Zap,
  GripVertical
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

type TabType = 'interleaved' | 'inverter' | 'lifetime';

export default function PowerDclinkRipplePanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<TabType>('interleaved', 'activeTab');
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
    panelKey: 'layout_powerdclink_v4',
    activeTab: activeTab,
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 820, results: 820 }
  });

  // Tab 1: Interleaved DC-DC
  const [intlN, setIntlN] = useState<number>(2);
  const [intlD, setIntlD] = useState<number>(0.45);
  const [intlIout, setIntlIout] = useState<number>(100);
  const [intlRipple, setIntlRipple] = useState<number>(20);
  const [intlRes, setIntlRes] = useState<any>(null);

  // Tab 2: 3-Phase Inverter
  const [invIout, setInvIout] = useState<number>(100);
  const [invVdc, setInvVdc] = useState<number>(600);
  const [invM, setInvM] = useState<number>(0.8);
  const [invPf, setInvPf] = useState<number>(0.85);
  const [invRes, setInvRes] = useState<any>(null);

  // Tab 3: Capacitor Lifetime & ESR Loss
  const [lifeL0, setLifeL0] = useState<number>(5000);
  const [lifeT0, setLifeT0] = useState<number>(105);
  const [lifeTa, setLifeTa] = useState<number>(65);
  const [lifeUseThermal, setLifeUseThermal] = useState<boolean>(true);
  const [lifeIRms, setLifeIRms] = useState<number>(10);
  const [lifeEsr, setLifeEsr] = useState<number>(25);
  const [lifeRth, setLifeRth] = useState<number>(8);
  const [lifeUseVoltage, setLifeUseVoltage] = useState<boolean>(true);
  const [lifeVNominal, setLifeVNominal] = useState<number>(450);
  const [lifeVActual, setLifeVActual] = useState<number>(400);
  const [lifeCapType, setLifeCapType] = useState<string>('Electrolytic');
  const [lifeRes, setLifeRes] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const calculateLifetime = async () => {
    try {
      const response = await apiFetch('/api/calculate/capacitor_toolbox/lifetime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          l0: lifeL0,
          t0: lifeT0,
          ta: lifeTa,
          use_thermal: lifeUseThermal,
          i_rms: lifeIRms,
          esr_mohm: lifeEsr,
          rth_kw: lifeRth,
          use_voltage: lifeUseVoltage,
          v_nominal: lifeVNominal,
          v_actual: lifeVActual,
          cap_type: lifeCapType
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed. Please verify input parameters.');
      }
      const data = await response.json();
      setLifeRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const calculateInterleaved = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_dclink/interleaved', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          n: intlN,
          d: intlD,
          i_total: intlIout,
          ripple_pct: intlRipple
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed. Please verify input parameters.');
      }
      const data = await response.json();
      setIntlRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const calculateInverter = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_dclink/inverter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          i_out_rms: invIout,
          vdc: invVdc,
          m: invM,
          pf: invPf
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed. Please verify input parameters.');
      }
      const data = await response.json();
      setInvRes(data);
      if (data && typeof data.i_cap_ripple_rms === 'number') {
        setLifeIRms(parseFloat(data.i_cap_ripple_rms.toFixed(2)));
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'interleaved') calculateInterleaved();
  }, [intlN, intlD, intlIout, intlRipple, activeTab]);

  useEffect(() => {
    if (activeTab === 'inverter') calculateInverter();
  }, [invIout, invVdc, invM, invPf, activeTab]);

  useEffect(() => {
    if (activeTab === 'lifetime') calculateLifetime();
  }, [lifeL0, lifeT0, lifeTa, lifeUseThermal, lifeIRms, lifeEsr, lifeRth, lifeUseVoltage, lifeVNominal, lifeVActual, lifeCapType, activeTab]);

  const getLifetimeChartOption = () => {
    if (!lifeRes) return {};
    let points: [number, number][] = [];
    if (lifeRes.scan && Array.isArray(lifeRes.scan.ta) && Array.isArray(lifeRes.scan.years)) {
      points = lifeRes.scan.ta.map((taVal: number, idx: number) => [taVal, lifeRes.scan.years[idx]]);
    } else {
      const minTa = 40;
      const maxTa = 95;
      const steps = 30;

      for (let taVal = minTa; taVal <= maxTa; taVal += (maxTa - minTa) / steps) {
        let dt = 0.0;
        if (lifeUseThermal) {
          dt = (lifeIRms ** 2) * (lifeEsr * 1e-3) * lifeRth;
        }
        const tCore = taVal + dt;
        let hours = lifeL0 * (2.0 ** ((lifeT0 - tCore) / 10.0));
        
        if (lifeUseVoltage && lifeVActual > 0) {
          const p_coeff = lifeCapType === 'Electrolytic' ? 4.4 : 7.5;
          hours = hours * ((lifeVNominal / lifeVActual) ** p_coeff);
        }
        hours = Math.max(0.0, Math.min(hours, 1e7));
        const years = hours / (24.0 * 365.0);
        points.push([parseFloat(taVal.toFixed(1)), parseFloat(years.toFixed(2))]);
      }
    }

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const ta = params[0].data[0];
          const years = params[0].data[1];
          return `Ambient Temp: ${ta} °C<br/>Predicted Life: ${years} Years (${(years * 365).toFixed(0)} Days)`;
        }
      },
      grid: { left: '10%', right: '10%', top: '15%', bottom: '15%' , containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Ambient Temp Ta (°C)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      yAxis: {
        type: 'value',
        name: 'Lifetime (Years)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#10b981', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      series: [
        {
          name: 'Lifetime (Years)',
          type: 'line',
          data: points,
          smooth: true,
          lineStyle: { 
            color: '#10b981', 
            width: 3,
            shadowColor: 'rgba(16, 185, 129, 0.8)',
            shadowBlur: 8
          },
          showSymbol: false,
          markLine: {
            symbol: 'none',
            data: [
              { xAxis: lifeTa, lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 }, label: { formatter: `Current Ta=${lifeTa}°C`, color: '#ef4444' } }
            ]
          }
        }
      ]
    };
  };

  // Interleaved ripple cancellation factor plot
  const getInterleavedChartOption = () => {
    const dPoints: number[] = intlRes?.scan?.d || [];
    const kPoints: number[] = intlRes?.scan?.k || [];

    return {
      backgroundColor: 'transparent',
      title: {
        text: 'DC-Link Ripple Cancellation Factor K(D) vs. Duty Cycle D',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#3b82f6',
        borderWidth: 1.5,
        shadowColor: 'rgba(59, 130, 246, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 }
      },
      legend: {
        data: ['Cancellation Factor K(D) (Lower = Better Cancellation)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '8%', right: '5%', bottom: '25%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: dPoints,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 'D'
      },
      yAxis: {
        type: 'value',
        name: 'K(D)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      dataZoom: [
        { type: 'inside', realtime: true, start: 0, end: 100 },
        {
          type: 'slider',
          show: true,
          realtime: true,
          start: 0,
          end: 100,
          height: 12,
          bottom: 5,
          borderColor: 'rgba(59, 130, 246, 0.15)',
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '110%',
          handleStyle: {
            color: '#3b82f6',
            shadowBlur: 5,
            shadowColor: 'rgba(59, 130, 246, 0.5)'
          },
          textStyle: { color: '#94a3b8', fontSize: 9 },
          fillerColor: 'rgba(59, 130, 246, 0.05)',
          dataBackground: {
            lineStyle: { color: '#3b82f6', width: 1 },
            areaStyle: { color: 'rgba(59, 130, 246, 0.02)' }
          },
          selectedDataBackground: {
            lineStyle: { color: '#3b82f6', width: 1.5 },
            areaStyle: { color: 'rgba(59, 130, 246, 0.1)' }
          }
        }
      ],
      series: [
        {
          name: 'Cancellation Factor K(D) (Lower = Better Cancellation)',
          type: 'line',
          data: kPoints,
          smooth: true,
          lineStyle: { 
            color: '#3b82f6', 
            width: 3,
            shadowColor: 'rgba(59, 130, 246, 0.8)',
            shadowBlur: 8
          },
          showSymbol: false,
          markLine: {
            symbol: 'none',
            data: [
              { xAxis: parseFloat(intlD.toFixed(2)), lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 }, label: { formatter: `Current D=${intlD}`, color: '#ef4444' } }
            ]
          }
        }
      ]
    };
  };

  const getInverterChartOption = () => {
    const mPoints: number[] = invRes?.scan?.m || [];
    const normRipple: number[] = invRes?.scan?.norm_ripple || [];

    return {
      backgroundColor: 'transparent',
      title: {
        text: 'Normalized DC-Link Capacitor Ripple RMS Current vs. Modulation Index M',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#10b981',
        borderWidth: 1.5,
        shadowColor: 'rgba(16, 185, 129, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 }
      },
      legend: {
        data: ['Normalized Ripple Ic_rms / I_phase'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '8%', right: '5%', bottom: '25%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: mPoints,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 'Modulation M'
      },
      yAxis: {
        type: 'value',
        name: 'Ic_rms/Ip',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      dataZoom: [
        { type: 'inside', realtime: true, start: 0, end: 100 },
        {
          type: 'slider',
          show: true,
          realtime: true,
          start: 0,
          end: 100,
          height: 12,
          bottom: 5,
          borderColor: 'rgba(16, 185, 129, 0.15)',
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '110%',
          handleStyle: {
            color: '#10b981',
            shadowBlur: 5,
            shadowColor: 'rgba(16, 185, 129, 0.5)'
          },
          textStyle: { color: '#94a3b8', fontSize: 9 },
          fillerColor: 'rgba(16, 185, 129, 0.05)',
          dataBackground: {
            lineStyle: { color: '#10b981', width: 1 },
            areaStyle: { color: 'rgba(16, 185, 129, 0.02)' }
          },
          selectedDataBackground: {
            lineStyle: { color: '#10b981', width: 1.5 },
            areaStyle: { color: 'rgba(16, 185, 129, 0.1)' }
          }
        }
      ],
      series: [
        {
          name: 'Normalized Ripple Ic_rms / I_phase',
          type: 'line',
          data: normRipple,
          smooth: true,
          lineStyle: { 
            color: '#10b981', 
            width: 3,
            shadowColor: 'rgba(16, 185, 129, 0.8)',
            shadowBlur: 8
          },
          showSymbol: false,
          markLine: {
            symbol: 'none',
            data: [
              { xAxis: parseFloat(invM.toFixed(2)), lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 }, label: { formatter: `Current M=${invM}`, color: '#ef4444' } }
            ]
          }
        }
      ]
    };
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Top Banner */}
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
            <h1 className="text-base font-bold text-white tracking-tight">DC-Link Capacitor Ripple & Lifetime</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Analyze DC-link capacitor RMS ripple current, ESR conduction losses, and operational lifetime for interleaved converters and 3-phase inverters.
            </p>
          </div>
        </div>

        {/* Global Toolbar */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetLayout}
            className="h-8 px-2.5 text-xs text-slate-400 border-slate-800 hover:bg-slate-900 hover:text-slate-200 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            Reset Layout
          </Button>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabType)} className="w-auto">
            <TabsList className="bg-slate-900 border border-slate-800 p-0.5 h-9">
              <TabsTrigger value="interleaved" className="text-xs px-3 h-8 data-[state=active]:bg-blue-500/10 data-[state=active]:text-blue-400 font-bold cursor-pointer">1. N-Phase Interleaved</TabsTrigger>
              <TabsTrigger value="inverter" className="text-xs px-3 h-8 data-[state=active]:bg-blue-500/10 data-[state=active]:text-blue-400 font-bold cursor-pointer">2. 3-Phase Inverter</TabsTrigger>
              <TabsTrigger value="lifetime" className="text-xs px-3 h-8 data-[state=active]:bg-blue-500/10 data-[state=active]:text-blue-400 font-bold cursor-pointer">3. Capacitor Lifetime & Loss</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      {/* Main Workspace DragDeck */}
      <div className="flex-1 min-h-0 overflow-hidden">
      <DragDeck
        isDesktop={isDesktop}
        leftSpan={leftSpan}
        rightSpan={rightSpan}
        leftCards={leftCards}
        rightCards={rightCards}
        draggedKey={draggedKey}
        onDropOnColumn={handleDropOnColumn}
        renderCard={(key: string) => (
          <DragCard
            key={key}
            cardKey={key}
            height={cardHeights[key]}
            onDragStart={(e) => handleDragStart(e, key)}
            onDragEnter={(e) => handleDragEnter(e, key)}
            onDragEnd={handleDragEnd}
            onResizeStart={handleResizeStart}
            onHeightResizeStart={handleHeightResizeStart}
          >
            {key === 'input' && (
              <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4">
                <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                  <Sliders className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-xs font-bold text-white">Operating Design Conditions</span>
                </div>

                {/* Tab 1: Interleaved */}
                {activeTab === 'interleaved' && (
                  <div className="space-y-3">
                    <span className="text-[10px] font-bold text-slate-330 block border-b border-slate-850 pb-1">Interleaved Topology Parameters</span>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[8px] text-slate-550">Parallel Phases N</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={1} max={16} step={1} value={intlN} onChange={(e) => setIntlN(Math.max(1, parseInt(e.target.value) || 1))} />
                      </div>
                      <div>
                        <label className="text-[8px] text-slate-550">Per-Phase Duty Cycle D</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0.01} max={0.99} step={0.01} value={intlD} onChange={(e) => setIntlD(Math.min(0.99, Math.max(0.01, parseFloat(e.target.value) || 0.01)))} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[8px] text-slate-550">Total Output Load Current (A)</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={1} value={intlIout} onChange={(e) => setIntlIout(Math.max(0.1, parseFloat(e.target.value) || 1))} />
                      </div>
                      <div>
                        <label className="text-[8px] text-slate-550">Per-Phase Inductor Ripple Ratio (%)</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={1} max={200} value={intlRipple} onChange={(e) => setIntlRipple(Math.max(1, parseFloat(e.target.value) || 20))} />
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 2: 3-Phase Inverter */}
                {activeTab === 'inverter' && (
                  <div className="space-y-3">
                    <span className="text-[10px] font-bold text-slate-330 block border-b border-slate-850 pb-1">Inverter Operating Conditions</span>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[8px] text-slate-550">Phase RMS Current (A)</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0.1} value={invIout} onChange={(e) => setInvIout(Math.max(0.1, parseFloat(e.target.value) || 1))} />
                      </div>
                      <div>
                        <label className="text-[8px] text-slate-550">DC-Link Voltage Vdc (V)</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={10} value={invVdc} onChange={(e) => setInvVdc(Math.max(1, parseFloat(e.target.value) || 10))} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[8px] text-slate-550">Modulation Index M [0~1.15]</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0.01} max={1.15} step={0.01} value={invM} onChange={(e) => setInvM(Math.min(1.15, Math.max(0.01, parseFloat(e.target.value) || 0.01)))} />
                      </div>
                      <div>
                        <label className="text-[8px] text-slate-550">Load Power Factor cosφ</label>
                        <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0.01} max={1.0} step={0.01} value={invPf} onChange={(e) => setInvPf(Math.min(1.0, Math.max(0.01, parseFloat(e.target.value) || 0.01)))} />
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 3: Lifetime & Loss */}
                {activeTab === 'lifetime' && (
                  <div className="space-y-4">
                    <div className="space-y-3">
                      <span className="text-[10px] font-bold text-slate-330 block border-b border-slate-850 pb-1">Capacitor Rated Specifications</span>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-[8px] text-slate-550">Capacitor Type</label>
                          <select className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" value={lifeCapType} onChange={(e) => setLifeCapType(e.target.value)}>
                            <option value="Electrolytic">Aluminum Electrolytic</option>
                            <option value="Film">Polypropylene Film</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[8px] text-slate-550">Rated Lifetime L0 (hours)</label>
                          <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={100} step={500} value={lifeL0} onChange={(e) => setLifeL0(Math.max(100, parseFloat(e.target.value) || 5000))} />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-[8px] text-slate-550">Rated Max Temp T0 (°C)</label>
                          <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={60} max={150} value={lifeT0} onChange={(e) => setLifeT0(parseFloat(e.target.value) || 105)} />
                        </div>
                        <div>
                          <label className="text-[8px] text-slate-550">Ambient Operating Temp Ta (°C)</label>
                          <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0} max={120} value={lifeTa} onChange={(e) => setLifeTa(parseFloat(e.target.value) || 65)} />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-850 pb-1">
                        <span className="text-[10px] font-bold text-slate-330">Ripple Current & Self-Heating Model</span>
                        <div className="flex items-center gap-1.5">
                          <input type="checkbox" id="lifeUseThermal" checked={lifeUseThermal} onChange={(e) => setLifeUseThermal(e.target.checked)} className="rounded bg-slate-900 border-slate-800 text-blue-500" />
                          <label htmlFor="lifeUseThermal" className="text-[9px] text-slate-400 cursor-pointer font-sans">Enable Thermal Dissipation</label>
                        </div>
                      </div>
                      {lifeUseThermal && (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="text-[8px] text-slate-550">Operating Ripple Current RMS (A)</label>
                              <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0} step={0.5} value={lifeIRms} onChange={(e) => setLifeIRms(Math.max(0, parseFloat(e.target.value) || 0))} />
                            </div>
                            <div>
                              <label className="text-[8px] text-slate-550">Equivalent Series Resistance ESR (mΩ)</label>
                              <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0.1} step={1} value={lifeEsr} onChange={(e) => setLifeEsr(Math.max(0.01, parseFloat(e.target.value) || 1))} />
                            </div>
                          </div>
                          <div>
                            <label className="text-[8px] text-slate-550">Thermal Resistance Rth (K/W)</label>
                            <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={0.1} step={0.5} value={lifeRth} onChange={(e) => setLifeRth(Math.max(0.01, parseFloat(e.target.value) || 1))} />
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-850 pb-1">
                        <span className="text-[10px] font-bold text-slate-330">Operating Voltage & Derating Model</span>
                        <div className="flex items-center gap-1.5">
                          <input type="checkbox" id="lifeUseVoltage" checked={lifeUseVoltage} onChange={(e) => setLifeUseVoltage(e.target.checked)} className="rounded bg-slate-900 border-slate-800 text-blue-500" />
                          <label htmlFor="lifeUseVoltage" className="text-[9px] text-slate-400 cursor-pointer font-sans">Enable Voltage Derating</label>
                        </div>
                      </div>
                      {lifeUseVoltage && (
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-[8px] text-slate-550">Rated Voltage Vn (V)</label>
                            <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={1} value={lifeVNominal} onChange={(e) => setLifeVNominal(Math.max(1, parseFloat(e.target.value) || 100))} />
                          </div>
                          <div>
                            <label className="text-[8px] text-slate-550">Actual Operating Voltage Va (V)</label>
                            <input className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-white" type="number" min={1} value={lifeVActual} onChange={(e) => setLifeVActual(Math.max(1, parseFloat(e.target.value) || 100))} />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {key === 'results' && (
              <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-6">
                <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                  <span className="text-xs font-bold text-white">DC-Link Ripple Calculation Results</span>
                </div>

                {/* SVG topology representations */}
                <Card className="bg-slate-900/40 border-slate-800/80">
                  <CardHeader className="pb-1">
                    <CardTitle className="text-xs font-bold text-slate-350 border-l-2 border-blue-500 pl-2">
                      Equivalent Hardware Topology & Ripple Current Flow
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex justify-center bg-slate-950/20 h-[200px] items-center border-t border-slate-900/50">
                    {activeTab === 'interleaved' && (
                      <svg width="100%" height="100%" viewBox="0 0 280 120" className="text-slate-350 max-w-[500px] max-h-[185px]">
                        <defs>
                          <style>{`
                            @keyframes flow-dash {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-flow-blue {
                              stroke-dasharray: 5, 5;
                              animation: flow-dash 1.5s linear infinite;
                            }
                          `}</style>
                          <filter id="neon-glow-blue" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-pink" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-amber" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <linearGradient id="sw-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#ec4899" stopOpacity="0.1" />
                            <stop offset="100%" stopColor="#db2777" stopOpacity="0.4" />
                          </linearGradient>
                        </defs>
                        <circle cx="20" cy="60" r="2.5" fill="#e2e8f0" />
                        <line x1="20" y1="60" x2="60" y2="60" stroke="#64748b" strokeWidth="1.2" />
                        
                        {/* Capacitor shunt */}
                        <line x1="45" y1="60" x2="45" y2="90" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="38" y1="90" x2="52" y2="90" stroke="#3b82f6" strokeWidth="2.5" filter="url(#neon-glow-blue)" />
                        <line x1="38" y1="94" x2="52" y2="94" stroke="#3b82f6" strokeWidth="2.5" filter="url(#neon-glow-blue)" />
                        <line x1="45" y1="94" x2="45" y2="105" stroke="#64748b" strokeWidth="1.2" />
                        
                        {/* GND line */}
                        <line x1="20" y1="105" x2="260" y2="105" stroke="#475569" strokeWidth="1.2" />
                        <text x="45" y="80" textAnchor="middle" fill="#93c5fd" className="text-[7px] font-bold" filter="url(#neon-glow-blue)">Cdclink</text>
                        
                        {/* Parallel branches */}
                        {/* Phase 1 */}
                        <line x1="60" y1="60" x2="80" y2="30" stroke="#64748b" strokeWidth="1.2" />
                        <rect x="80" y="22" width="25" height="16" fill="url(#sw-grad)" stroke="#ec4899" strokeWidth="1.5" rx="1" filter="url(#neon-glow-pink)" />
                        <text x="92.5" y="32" textAnchor="middle" fill="#fbcfe8" className="text-[6.5px] font-bold" filter="url(#neon-glow-pink)">Q1</text>
                        <line x1="105" y1="30" x2="135" y2="30" stroke="#cbd5e1" strokeWidth="1.2" />
                        <path d="M 135,30 Q 138,25 141,30 Q 144,25 147,30 Q 150,25 153,30" fill="none" stroke="#fb923c" strokeWidth="2.0" filter="url(#neon-glow-amber)" />
                        <line x1="153" y1="30" x2="180" y2="60" stroke="#cbd5e1" strokeWidth="1.2" />
                        <text x="145" y="20" textAnchor="middle" fill="#ffedd5" className="text-[6.5px] font-bold" filter="url(#neon-glow-amber)">L1</text>
                        
                        {/* Phase 2 */}
                        <line x1="60" y1="60" x2="80" y2="90" stroke="#64748b" strokeWidth="1.2" />
                        <rect x="80" y="82" width="25" height="16" fill="url(#sw-grad)" stroke="#ec4899" strokeWidth="1.5" rx="1" filter="url(#neon-glow-pink)" />
                        <text x="92.5" y="92" textAnchor="middle" fill="#fbcfe8" className="text-[6.5px] font-bold" filter="url(#neon-glow-pink)">Q2</text>
                        <line x1="105" y1="90" x2="135" y2="90" stroke="#cbd5e1" strokeWidth="1.2" />
                        <path d="M 135,90 Q 138,85 141,90 Q 144,85 147,90 Q 150,85 153,90" fill="none" stroke="#fb923c" strokeWidth="2.0" filter="url(#neon-glow-amber)" />
                        <line x1="153" y1="90" x2="180" y2="60" stroke="#cbd5e1" strokeWidth="1.2" />
                        <text x="145" y="82" textAnchor="middle" fill="#ffedd5" className="text-[6.5px] font-bold" filter="url(#neon-glow-amber)">L2</text>
                        
                        {/* Load Output */}
                        <line x1="180" y1="60" x2="240" y2="60" stroke="#64748b" strokeWidth="1.2" />
                        <circle cx="240" cy="60" r="2.5" fill="#10b981" />
                        <text x="248" y="58" fill="#10b981" className="text-[7.5px] font-mono">Vout</text>

                        {/* Ripple current animations */}
                        <path d="M 20,60 H 45" fill="none" stroke="#3b82f6" strokeWidth="1.5" className="animate-flow-blue" />
                      </svg>
                    )}
                    {activeTab === 'inverter' && (
                      <svg width="100%" height="100%" viewBox="0 0 280 120" className="text-slate-350 max-w-[500px] max-h-[185px]">
                        <defs>
                          <style>{`
                            @keyframes flow-dash {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-flow-blue {
                              stroke-dasharray: 5, 5;
                              animation: flow-dash 1.5s linear infinite;
                            }
                          `}</style>
                          <filter id="neon-glow-blue" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-purple" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <linearGradient id="inv-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.1" />
                            <stop offset="100%" stopColor="#6d28d9" stopOpacity="0.4" />
                          </linearGradient>
                        </defs>
                        <line x1="20" y1="30" x2="100" y2="30" stroke="#cbd5e1" strokeWidth="1.2" />
                        <line x1="20" y1="90" x2="100" y2="90" stroke="#cbd5e1" strokeWidth="1.2" />
                        
                        {/* DC link capacitor */}
                        <line x1="50" y1="30" x2="50" y2="50" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="42" y1="50" x2="58" y2="50" stroke="#3b82f6" strokeWidth="2.5" filter="url(#neon-glow-blue)" />
                        <line x1="42" y1="54" x2="58" y2="54" stroke="#3b82f6" strokeWidth="2.5" filter="url(#neon-glow-blue)" />
                        <line x1="50" y1="54" x2="50" y2="90" stroke="#64748b" strokeWidth="1.2" />
                        <text x="30" y="47" fill="#93c5fd" className="text-[7.5px] font-bold" filter="url(#neon-glow-blue)">Cdclink</text>
                        
                        {/* 3 phase legs */}
                        <rect x="100" y="20" width="120" height="80" fill="url(#inv-grad)" stroke="#8b5cf6" strokeWidth="1.5" rx="3" filter="url(#neon-glow-purple)" />
                        <text x="160" y="62" textAnchor="middle" fill="#ddd6fe" className="text-[10px] font-bold font-mono" filter="url(#neon-glow-purple)">3-Phase Inverter</text>
                        
                        <line x1="220" y1="40" x2="260" y2="40" stroke="#10b981" strokeWidth="1.2" />
                        <line x1="220" y1="60" x2="260" y2="60" stroke="#10b981" strokeWidth="1.2" />
                        <line x1="220" y1="80" x2="260" y2="80" stroke="#10b981" strokeWidth="1.2" />
                        <text x="264" y="62" fill="#10b981" className="text-[8px] font-mono">3-ph AC</text>

                        {/* Current Flow animation */}
                        <path d="M 20,30 L 100,30" fill="none" stroke="#3b82f6" strokeWidth="1.5" className="animate-flow-blue" />
                      </svg>
                    )}
                    {activeTab === 'lifetime' && (
                      <svg width="100%" height="100%" viewBox="0 0 280 120" className="text-slate-350 max-w-[500px] max-h-[185px]">
                        <defs>
                          <style>{`
                            @keyframes ripple-wave {
                              0% { transform: scale(1.0); opacity: 0.8; }
                              100% { transform: scale(1.3); opacity: 0.0; }
                            }
                            .animate-ripple {
                              transform-origin: 140px 60px;
                              animation: ripple-wave 2s infinite ease-out;
                            }
                          `}</style>
                          <filter id="core-glow" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="3" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                        </defs>
                        {/* Capacitor Body */}
                        <rect x="110" y="20" width="60" height="80" rx="4" fill="#0f172a" stroke="#3b82f6" strokeWidth="1.5" />
                        <line x1="130" y1="100" x2="130" y2="115" stroke="#94a3b8" strokeWidth="2.5" />
                        <line x1="150" y1="100" x2="150" y2="115" stroke="#94a3b8" strokeWidth="2.5" />
                        
                        {/* Top Band */}
                        <rect x="110" y="20" width="60" height="15" fill="#3b82f6" opacity="0.35" />
                        <line x1="110" y1="35" x2="170" y2="35" stroke="#3b82f6" strokeWidth="1" />
                        
                        {/* Label text */}
                        <text x="140" y="55" textAnchor="middle" fill="#93c5fd" className="text-[10px] font-bold font-mono">DC LINK</text>
                        <text x="140" y="90" textAnchor="middle" fill="#64748b" className="text-[7px] font-mono">{lifeCapType === 'Electrolytic' ? 'Electrolytic' : 'Film'}</text>
                        
                        {/* Thermal Core */}
                        {lifeUseThermal && (
                          <>
                            <circle cx="140" cy="70" r="14" fill="#ef4444" opacity="0.25" filter="url(#core-glow)" />
                            <circle cx="140" cy="70" r="14" stroke="#ef4444" strokeWidth="1.5" fill="none" className="animate-ripple" />
                            <text x="140" y="73" textAnchor="middle" fill="#f87171" className="text-[7.5px] font-bold">Core Tj</text>
                          </>
                        )}
                      </svg>
                    )}
                  </CardContent>
                </Card>

                {/* Tab 1: Interleaved results */}
                {activeTab === 'interleaved' && intlRes && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-3 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-500">DC-Link Capacitor RMS Ripple Current</span>
                        <span className="text-xs font-bold text-white font-mono">{intlRes.i_cap_ripple_rms.toFixed(2)} A</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-500">Ripple Cancellation Factor K(D)</span>
                        <span className="text-xs font-bold text-white font-mono">{intlRes.k_d.toFixed(4)}</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-500">Capacitor Peak-to-Peak Ripple I_pp</span>
                        <span className="text-xs font-bold text-cyan-400 font-mono">{intlRes.i_cap_ripple_pp.toFixed(2)} A</span>
                      </div>
                    </div>

                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardContent className="pt-4 h-[280px]">
                        <ReactECharts notMerge={true} option={getInterleavedChartOption()} style={{ height: '100%', width: '100%' }} />
                      </CardContent>
                    </Card>

                    <div className="text-[10px] text-slate-400 leading-relaxed border border-slate-800 rounded-lg p-3 bg-slate-900/10">
                      <span className="font-bold text-slate-350 block">Interleaved Ripple Cancellation Analytical Equation:</span>
                      <Latex math="K(D) = \frac{(N \cdot D - m)(m + 1 - N \cdot D)}{N \cdot D(1 - D)}" block />
                      <p>
                        Where <Latex math="m = \lfloor N \cdot D \rfloor" />. At specific duty cycles (e.g., <Latex math="D=0.5" /> in 2-phase interleaved), the ripple cancellation factor <Latex math="K(D)=0" />, meaning the DC-link capacitor theoretically experiences zero inductor switching ripple current.
                      </p>
                    </div>
                  </div>
                )}

                {/* Tab 2: Inverter results */}
                {activeTab === 'inverter' && invRes && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-500">Capacitor RMS Ripple Current Ic_rms</span>
                        <span className="text-sm font-bold text-white font-mono">{invRes.i_cap_ripple_rms.toFixed(2)} A</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-500">Normalized Ripple Ratio Ic_rms / I_phase</span>
                        <span className="text-sm font-bold text-teal-400 font-mono">{invRes.normalized_ripple.toFixed(4)}</span>
                      </div>
                    </div>

                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardContent className="pt-4 h-[280px]">
                        <ReactECharts notMerge={true} option={getInverterChartOption()} style={{ height: '100%', width: '100%' }} />
                      </CardContent>
                    </Card>

                    <div className="text-[10px] text-slate-400 leading-relaxed border border-slate-800 rounded-lg p-3 bg-slate-900/10">
                      <span className="font-bold text-slate-350 block">3-Phase Inverter DC-Link Capacitor Ripple Closed-Form Solution (SPWM/SVPWM):</span>
                      <Latex math="I_{c,rms} = I_{out,rms} \sqrt{2M \left[ \frac{\sqrt{3}}{4\pi} + M \cdot \cos^2\varphi \left( \frac{\sqrt{3}}{\pi} - \frac{9M}{16} \right) \right]}" block />
                    </div>
                  </div>
                )}

                {activeTab === 'lifetime' && lifeRes && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-3 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-550 font-sans">Core Temp Rise ΔT</span>
                        <span className="text-sm font-bold text-orange-400 font-mono">{lifeRes.dt.toFixed(2)} °C</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-550 font-sans">Predicted Lifetime (Hours)</span>
                        <span className="text-sm font-bold text-teal-400 font-mono">{(lifeRes.hours_predicted).toLocaleString('en-US', {maximumFractionDigits:0})} h</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-550 font-sans">Predicted Lifetime (Years)</span>
                        <span className="text-sm font-bold text-teal-300 font-mono">{(lifeRes.hours_predicted / (24 * 365)).toFixed(2)} Years</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-550 font-sans">Thermal Derating Factor (2^((T0-Tj)/10))</span>
                        <span className="text-sm font-bold text-white font-mono">{lifeRes.temp_derating_coeff.toFixed(2)} x</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-550 font-sans">Voltage Derating Factor</span>
                        <span className="text-sm font-bold text-white font-mono">{lifeRes.voltage_derating_coeff.toFixed(2)} x</span>
                      </div>
                    </div>

                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardHeader className="py-2.5">
                        <CardTitle className="text-xs font-bold text-slate-350">Lifetime vs. Ambient Temperature Ta (Years)</CardTitle>
                      </CardHeader>
                      <CardContent className="h-[240px]">
                        <ReactECharts option={getLifetimeChartOption()} style={{ height: '100%', width: '100%' }} notMerge={true} />
                      </CardContent>
                    </Card>

                    <div className="text-[10px] text-slate-400 leading-relaxed border border-slate-800 rounded-lg p-3 bg-slate-900/10 space-y-1">
                      <span className="font-bold text-slate-350 block">Capacitor Lifetime Prediction Arrhenius Model:</span>
                      <Latex math="L = L_0 \cdot 2^{\frac{T_0 - T_{core}}{10}} \cdot \left(\frac{V_n}{V_a}\right)^{p}" block />
                      <p>
                        Where <Latex math="T_{core} = T_a + \Delta T" />, with thermal rise calculated from ripple current and ESR dissipation: <Latex math="\Delta T = I_{rms}^2 \cdot ESR \cdot R_{th}" />. The voltage acceleration factor exponent is typically <Latex math="p = 4.4" /> for electrolytic capacitors and <Latex math="p = 7.5" /> for polypropylene film capacitors.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </DragCard>
        )}
      />
      </div>
    </div>
  );
}