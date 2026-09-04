import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import FlybackSchematicSandbox from './FlybackSchematicSandbox';
import SecondaryVerificationHub from './SecondaryVerificationHub';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/Accordion';
import { Button } from './ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';
import { DragDeck, DragCard, useDragDeckLayout } from './ui/LayoutEngine';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs';
import { 
  ArrowLeft, 
  Activity, 
  Layers, 
  CheckCircle2, 
  ShieldAlert, 
  Sparkles, 
  Play, 
  Cpu, 
  RefreshCw, 
  BookOpen, 
  TrendingUp, 
  Sliders, 
  Zap, 
  Info, 
  Flame, 
  Compass, 
  ChevronRight, 
  Copy 
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
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-slate-300" : "inline-block"} />;
};

interface SwitchDevice {
  name: string;
  type: string;
  v_ds_max: number;
  i_d_max: number;
  r_ds_on: number;
  package: string;
  r_jc: number;
}

interface DiodeDevice {
  name: string;
  type: string;
  v_r_max: number;
  i_f_max: number;
  v_f: number;
  package: string;
  r_jc: number;
}

interface BomResponse {
  switches: SwitchDevice[];
  diodes: DiodeDevice[];
  requirements: {
    sw_v: number;
    sw_i: number;
    diode_v: number;
    diode_i: number;
  };
}

export default function FlybackPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
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
    panelKey: 'layout_flybackpanel_v5',
    defaultCards: ['main'],
    defaultColumns: { main: 'left' } as Record<string, 'left' | 'right'>,
    defaultSpans: { main: 12 },
    defaultHeights: { main: 900 }
  });

  const [vin, setVin] = useState<number>(100.0);
  const [vor, setVor] = useState<number>(80.0);
  const [vout, setVout] = useState<number>(12.0);
  const [iout, setIout] = useState<number>(3.0);
  const [fsw, setFsw] = useState<number>(100.0);
  const [krf, setKrf] = useState<number>(0.5);
  const [bmax, setBmax] = useState<number>(0.25);
  const [ae, setAe] = useState<number>(80.0);

  const [lpUh, setLpUh] = useState<string>('');
  const [cUf, setCUf] = useState<string>('');
  const [rcEsr, setRcEsr] = useState<number>(20.0);
  const [rcdLlk, setRcdLlk] = useState<number>(3.0);
  const [rcdVspike, setRcdVspike] = useState<number>(50.0);
  
  const [calcData, setCalcData] = useState<any>(null);
  const [bomData, setBomData] = useState<BomResponse | null>(null);
  const [mainTab, setMainTab] = useTabHistoryState<'schematic' | 'specs' | 'verification'>('schematic', 'flybackMainTab');
  const [activeTab, setActiveTab] = useTabHistoryState<'time' | 'bode'>('time', 'activeTab');
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const calcParams = {
        vin,
        vor,
        vout,
        iout,
        fsw_khz: fsw,
        krf,
        bmax,
        ae_mm2: ae,
        lp_uh: lpUh ? parseFloat(lpUh) : null,
        c_uf: cUf ? parseFloat(cUf) : null,
        rc_esr_mohm: rcEsr,
        rcd_llk_uh: rcdLlk,
        rcd_vspike_v: rcdVspike
      };

      const calcRes = await apiFetch('/api/calculate/flyback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(calcParams),
      });

      if (!calcRes.ok) {
        const errDetail = await calcRes.json();
        throw new Error(errDetail.detail || 'Calculation failed');
      }

      const data = await calcRes.json();
      setCalcData(data);

      if (!lpUh && data.actual?.lp_act_uh) {
        setLpUh(data.actual.lp_act_uh.toFixed(1));
      }
      if (!cUf && data.actual?.c_act_uf) {
        setCUf(data.actual.c_act_uf.toFixed(1));
      }

      const bomParams = {
        min_v_sw: data.simulation_time.v_ds_max,
        min_i_sw: data.simulation_time.ipk,
        min_v_diode: data.simulation_time.v_rev_max,
        min_i_diode: data.simulation_time.is_pk
      };

      const bomRes = await apiFetch('/api/bom/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bomParams),
      });

      if (bomRes.ok) {
        const bData: BomResponse = await bomRes.json();
        setBomData(bData);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleCalculate();
  }, []);

  const timeChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#1e293b' } },
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9', fontFamily: 'Inter', fontSize: 12 }
    },
    legend: {
      data: ['Primary Current i_p (A)', 'Secondary Current i_s (A)', 'Output Ripple Voltage v_ripple (mV)'],
      textStyle: { color: '#94a3b8', fontFamily: 'Inter', fontSize: 11 },
      top: 0
    },
    grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: calcData?.simulation_time?.t_us?.map((t: number) => t.toFixed(2)) || [],
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
      axisLabel: { color: '#94a3b8', fontSize: 9 },
      name: 'Time (μs)',
      nameTextStyle: { color: '#94a3b8', fontSize: 9 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Current (A)',
        position: 'left',
        axisLine: { show: true, lineStyle: { color: '#38bdf8' } },
        axisLabel: { color: '#38bdf8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      {
        type: 'value',
        name: 'Ripple Voltage (mV)',
        position: 'right',
        axisLine: { show: true, lineStyle: { color: '#f43f5e' } },
        axisLabel: { color: '#f43f5e', fontSize: 9 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: 'Primary Current i_p (A)',
        type: 'line',
        showSymbol: false,
        data: calcData?.simulation_time?.i_p_a || [],
        lineStyle: { color: '#38bdf8', width: 2 }
      },
      {
        name: 'Secondary Current i_s (A)',
        type: 'line',
        showSymbol: false,
        data: calcData?.simulation_time?.i_s_a || [],
        lineStyle: { color: '#a855f7', width: 1.5, type: 'dashed' }
      },
      {
        name: 'Output Ripple Voltage v_ripple (mV)',
        type: 'line',
        yAxisIndex: 1,
        showSymbol: false,
        data: calcData?.simulation_time?.v_ripple_mv || [],
        lineStyle: { color: '#f43f5e', width: 2 }
      }
    ]
  };

  const bodeChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#1e293b' } },
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9', fontFamily: 'Inter', fontSize: 12 }
    },
    legend: {
      data: ['Gain (dB)', 'Phase (deg)'],
      textStyle: { color: '#94a3b8', fontFamily: 'Inter', fontSize: 11 },
      top: 0
    },
    grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: {
      type: 'log',
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 9,
        formatter: (value: number) => {
          const log10 = Math.log10(value);
          if (Math.abs(log10 - Math.round(log10)) < 1e-6) {
            return value >= 1000 ? (value / 1000) + 'kHz' : value + 'Hz';
          }
          return '';
        }
      },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
      name: 'Frequency (Hz)',
      nameTextStyle: { color: '#94a3b8', fontSize: 9 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Gain (dB)',
        position: 'left',
        axisLine: { show: true, lineStyle: { color: '#38bdf8' } },
        axisLabel: { color: '#38bdf8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      {
        type: 'value',
        name: 'Phase (deg)',
        position: 'right',
        axisLine: { show: true, lineStyle: { color: '#10b981' } },
        axisLabel: { color: '#10b981', fontSize: 9 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: 'Gain (dB)',
        type: 'line',
        showSymbol: false,
        data: calcData?.simulation_bode?.gain_db?.map((g: number, idx: number) => [calcData.simulation_bode.f_hz[idx], g]) || [],
        lineStyle: { color: '#38bdf8', width: 2 }
      },
      {
        name: 'Phase (deg)',
        type: 'line',
        showSymbol: false,
        data: calcData?.simulation_bode?.phase_deg?.map((p: number, idx: number) => [calcData.simulation_bode.f_hz[idx], p]) || [],
        lineStyle: { color: '#10b981', width: 2 },
        yAxisIndex: 1
      }
    ]
  };

  return (
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
          onResetLayout={handleResetLayout}
        >
          {key === 'main' && (
            <div className="flex-1 overflow-y-auto scrollbar-thin">
              <div className="w-full flex flex-col gap-6 text-slate-200">
      
      {/* Title Header */}
      <div className="flex justify-between items-center bg-[#0f172a]/80 p-4 rounded-xl border border-slate-800/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={onBack} className="bg-slate-900 border-slate-800 text-slate-300 hover:text-white">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-md font-bold text-white flex items-center gap-2">
              Isolated Flyback Converter
            </h1>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Isolated flyback converter analysis and design. Supports AP transformer core sizing, secondary synchronous rectification loss evaluation, RCD clamp calculation, and dual-loop time/frequency domain simulation.
            </p>
          </div>
        </div>

        {/* Parent Tab Switcher */}
        <div className="flex bg-[#020617] border border-slate-850 p-0.5 rounded-lg h-9 shrink-0">
          <button
            onClick={() => setMainTab('schematic')}
            className={`px-4 text-xs font-semibold rounded-md transition-all flex items-center cursor-pointer ${
              mainTab === 'schematic'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Interactive Schematic
          </button>
          <button
            onClick={() => setMainTab('specs')}
            className={`px-4 text-xs font-semibold rounded-md transition-all flex items-center cursor-pointer ${
              mainTab === 'specs'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Specs & Operating Conditions
          </button>
          <button
            onClick={() => setMainTab('verification')}
            className={`px-4 text-xs font-semibold rounded-md transition-all flex items-center cursor-pointer ${
              mainTab === 'verification'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Secondary Verification Hub
          </button>
        </div>
      </div>

      {mainTab === 'schematic' ? (
        <div className="w-full flex-1 flex flex-col min-h-[750px] overflow-hidden relative">
          <FlybackSchematicSandbox
            vin={vin} setVin={setVin}
            vor={vor} setVor={setVor}
            vout={vout} setVout={setVout}
            iout={iout} setIout={setIout}
            fsw={fsw} setFsw={setFsw}
            krf={krf} setKrf={setKrf}
            bmax={bmax} setBmax={setBmax}
            ae={ae} setAe={setAe}
            lpUh={lpUh} setLpUh={setLpUh}
            cUf={cUf} setCUf={setCUf}
            rcEsr={rcEsr} setRcEsr={setRcEsr}
            rcdLlk={rcdLlk} setRcdLlk={setRcdLlk}
            rcdVspike={rcdVspike} setRcdVspike={setRcdVspike}
            calcData={calcData}
          />
        </div>
      ) : mainTab === 'verification' ? (
        <div className="w-full flex-1 overflow-y-auto p-4 scrollbar-thin">
          <SecondaryVerificationHub
            vinMin={vin * 0.9}
            vinNom={vin}
            vinMax={vin * 1.1}
            vout={vout}
            iout={iout}
            fsw={fsw}
            power={vout * iout}
            topology="flyback"
            setActiveModule={setActiveModule}
          />
        </div>
      ) : (
        <>
      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Sizing & Parameters */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          
          <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-xs font-bold text-white border-l-2 border-cyan-500 pl-2 flex items-center gap-2">
                Input Design Specifications
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-0 flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Minimum Input Voltage Vin [V]</label>
                  <input type="number" value={vin} onChange={e => setVin(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Reflected Voltage Vor [V]</label>
                  <input type="number" value={vor} onChange={e => setVor(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Output Voltage Vout [V]</label>
                  <input type="number" value={vout} onChange={e => setVout(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Maximum Output Current Iout [A]</label>
                  <input type="number" value={iout} onChange={e => setIout(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Switching Frequency fsw [kHz]</label>
                  <input type="number" value={fsw} onChange={e => setFsw(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Current Ripple Factor Krf</label>
                  <input type="number" step="0.05" value={krf} onChange={e => setKrf(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Design Flux Density Bmax [T]</label>
                  <input type="number" step="0.05" value={bmax} onChange={e => setBmax(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Core Cross-Section Area Ae [mm2]</label>
                  <input type="number" value={ae} onChange={e => setAe(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
              </div>

              <div className="h-px bg-slate-800 my-1" />
              
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-slate-300">Physical Operational Components</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] text-slate-400">Primary Inductance Lp [uH]</label>
                    {calcData?.design?.lp_design_uh && (
                      <Button 
                        variant="link" 
                        onClick={() => setLpUh(calcData.design.lp_design_uh.toFixed(1))}
                        className="h-auto p-0 text-[9px] text-cyan-400 hover:text-cyan-300 hover:no-underline border-0"
                      >
                        Set to Recommended
                      </Button>
                    )}
                  </div>
                  <input type="text" value={lpUh} onChange={e => setLpUh(e.target.value)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" placeholder="Enter inductance value" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] text-slate-400">Output Capacitance Co [uF]</label>
                    {calcData?.design?.c_out_design_uf && (
                      <Button 
                        variant="link" 
                        onClick={() => setCUf(calcData.design.c_out_design_uf.toFixed(1))}
                        className="h-auto p-0 text-[9px] text-cyan-400 hover:text-cyan-300 hover:no-underline border-0"
                      >
                        Set to Recommended
                      </Button>
                    )}
                  </div>
                  <input type="text" value={cUf} onChange={e => setCUf(e.target.value)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" placeholder="Enter capacitance value" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Output Capacitor ESR [mOhm]</label>
                  <input type="number" value={rcEsr} onChange={e => setRcEsr(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400">Transformer Leakage L_leak [uH]</label>
                  <input type="number" step="0.5" value={rcdLlk} onChange={e => setRcdLlk(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
                <div className="flex flex-col gap-1.5 col-span-2">
                  <label className="text-[10px] text-slate-400">Allowable RCD Spike V_spike [V]</label>
                  <input type="number" value={rcdVspike} onChange={e => setRcdVspike(parseFloat(e.target.value) || 0)} className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors" />
                </div>
              </div>

              {calcData?.simulation_time && (
                <div className="p-3.5 rounded-lg bg-slate-900/50 border border-slate-800 flex flex-col gap-2">
                  <div className="text-[10px] font-semibold text-slate-200 border-b border-slate-800 pb-1 mb-0.5 flex items-center justify-between">
                    <span>RCD Clamp Snubber Sizing</span>
                    <span className="text-[10px] text-amber-400 font-bold">Loss: {calcData.simulation_time.rcd_p_loss.toFixed(2)} W</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 leading-normal">
                    <div>Steady-state Vc: <span className="text-slate-200 font-medium">{calcData.simulation_time.rcd_vc.toFixed(1)} V</span></div>
                    <div>Resistance R_clamp: <span className="text-slate-200 font-medium">{(calcData.simulation_time.rcd_r_clamp/1000).toFixed(1)} kΩ</span></div>
                    <div>Capacitance C_clamp: <span className="text-slate-200 font-medium">{(calcData.simulation_time.rcd_c_clamp*1e9).toFixed(1)} nF</span></div>
                    <div className="col-span-2 text-[9px] text-slate-500 mt-0.5">
                      * RC parameters sized based on 10% clamp voltage ripple target
                    </div>
                  </div>
                </div>
              )}

              <Button 
                onClick={handleCalculate} 
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs"
              >
                {loading ? 'Calculating...' : 'Run Design & Simulation'}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Interactive Charts */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          
          <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200">
            <CardHeader className="p-5 pb-3">
              <CardTitle className="text-xs font-bold text-white border-l-2 border-cyan-500 pl-2 flex items-center gap-2">
                Physical Design Verification & Equations
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 pt-0 flex flex-col gap-6">
              
              {error && (
                <div className="p-4 rounded-lg bg-red-950/40 border border-red-500/30 text-red-200 text-xs">
                  {error}
                </div>
              )}

              {calcData ? (
                <div className="flex flex-col gap-5">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                    <div className="p-3 rounded-lg bg-[#020617] border border-slate-900 flex flex-col gap-1 text-center">
                      <span className="text-[10px] text-slate-400">Rec. Primary Lp</span>
                      <span className="text-sm font-bold text-cyan-300">{calcData.design.lp_design_uh.toFixed(1)} uH</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#020617] border border-slate-900 flex flex-col gap-1 text-center">
                      <span className="text-[10px] text-slate-400">Primary Turns Np</span>
                      <span className="text-sm font-bold text-cyan-300">{calcData.design.np_design_turns} turns</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#020617] border border-slate-900 flex flex-col gap-1 text-center">
                      <span className="text-[10px] text-slate-400">Secondary Turns Ns</span>
                      <span className="text-sm font-bold text-cyan-300">{calcData.design.ns_design_turns} turns</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#020617] border border-slate-900 flex flex-col gap-1 text-center">
                      <span className="text-[10px] text-slate-400">Rec. Air Gap lg</span>
                      <span className="text-sm font-bold text-cyan-300">{calcData.design.lg_design_mm.toFixed(3)} mm</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-[#020617] border border-slate-900 flex flex-col gap-3">
                    <div className="text-[11px] font-semibold text-slate-200 flex items-center justify-between">
                      <span>Operating Point Verification</span>
                      <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 text-[9px] font-bold">
                        {calcData.simulation_time.mode} Mode
                      </span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-2 text-[11px] text-slate-400">
                      <div>Actual Duty Cycle: <span className="text-slate-200 font-medium">{calcData.simulation_time.d_act.toFixed(3)}</span></div>
                      <div>Primary Peak Ip_pk: <span className="text-slate-200 font-medium">{calcData.simulation_time.ipk.toFixed(2)} A</span></div>
                      <div>Primary RMS Ip_rms: <span className="text-slate-200 font-medium">{calcData.simulation_time.ip_rms.toFixed(2)} A</span></div>
                      <div>Secondary Peak Is_pk: <span className="text-slate-200 font-medium">{calcData.simulation_time.is_pk.toFixed(2)} A</span></div>
                      <div>Secondary RMS Is_rms: <span className="text-slate-200 font-medium">{calcData.simulation_time.is_rms.toFixed(2)} A</span></div>
                      <div>Capacitor RMS Ripple: <span className="text-slate-200 font-medium">{calcData.design.cout_rms_a.toFixed(2)} A</span></div>
                      <div className="col-span-2 md:col-span-3 h-px bg-slate-900 my-1" />
                      <div className="text-cyan-400">MOSFET Stress Vds: <span className="font-bold text-slate-200">{calcData.simulation_time.v_ds_max.toFixed(1)} V</span></div>
                      <div className="text-rose-400">Diode Reverse Vrev: <span className="font-bold text-slate-200">{calcData.simulation_time.v_rev_max.toFixed(1)} V</span></div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <span className="text-xs font-semibold text-slate-300">Design Formulas & Analytical Derivations</span>
                    <Accordion type="single" collapsible className="w-full text-xs">
                      
                      {/* Formula 1: Maximum Duty Cycle */}
                      <AccordionItem value="dmax" className="border-slate-800">
                        <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2">
                          <div className="flex flex-col items-start gap-0.5 text-left">
                            <span className="text-[10px] text-slate-400">Maximum Design Duty Cycle (D_max)</span>
                            <span className="font-semibold text-cyan-300">D_max = {calcData.simulation_time.d_act.toFixed(3)}</span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                          <div>In an isolated flyback converter, when the primary MOSFET conducts, energy is stored in the transformer magnetizing inductance. When the MOSFET turns off, stored energy transfers to the secondary winding.</div>
                          <div>Let the secondary winding voltage reflected to the primary be <Latex math="V_{or} = n_{ps} (V_{out} + V_d)" /> (where <Latex math="n_{ps} = N_p / N_s" /> and <Latex math="V_d" /> is the forward diode drop).</div>
                          <div>Applying the Volt-Second Balance criterion:</div>
                          <Latex math="V_{in} \cdot t_{on} = V_{or} \cdot t_{off}" block />
                          <div>With duty cycle <Latex math="D = t_{on} / (t_{on} + t_{off})" />:</div>
                          <Latex math="V_{in} \cdot D = V_{or} \cdot (1 - D) \implies D = \frac{V_{or}}{V_{in} + V_{or}}" block />
                          <div>Evaluating at minimum input DC voltage <Latex math="V_{in}" /> yields maximum operating duty cycle <Latex math="D_{max}" />.</div>
                        </AccordionContent>
                      </AccordionItem>

                      {/* Formula 2: Primary Inductance */}
                      <AccordionItem value="lp" className="border-slate-800">
                        <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2">
                          <div className="flex flex-col items-start gap-0.5 text-left">
                            <span className="text-[10px] text-slate-400">Primary Critical & Design Inductance (Lp)</span>
                            <span className="font-semibold text-cyan-300">L_p = {calcData.design.lp_design_uh.toFixed(1)} uH</span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                          <div>**Critical Inductance**: Boundaries CCM and DCM modes. At boundary condition, initial cycle current starts exactly at zero:</div>
                          <Latex math="I_{in,avg} = \frac{1}{2} I_{p,pk} \cdot D_{max}" block />
                          <div>With total active input power <Latex math="P_{in} = V_{in} I_{in,avg}" /> and inductor current slope:</div>
                          <Latex math="I_{p,pk} = \frac{V_{in} \cdot D_{max}}{L_{p\_crit} \cdot f_{sw}}" block />
                          <div>Eliminating peak current yields critical inductance:</div>
                          <Latex math="L_{p\_crit} = \frac{V_{in}^2 D_{max}^2}{2 P_{in} f_{sw}}" block />
                          <div>**Design Inductance**: Introducing current ripple factor <Latex math="K_{rf} = \Delta I_p / I_{edc}" /> sets required inductance for continuous mode operation.</div>
                        </AccordionContent>
                      </AccordionItem>

                      {/* Formula 3: RCD Clamp Snubber */}
                      <AccordionItem value="rcd" className="border-slate-800">
                        <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2">
                          <div className="flex flex-col items-start gap-0.5 text-left">
                            <span className="text-[10px] text-slate-400">RCD Snubber Resistor & Capacitor Sizing</span>
                            <span className="font-semibold text-cyan-300">
                              R_clamp = {calcData.design.r_clamp_recommend_kohm.toFixed(1)} kΩ / C_clamp = {calcData.design.c_clamp_recommend_nf.toFixed(1)} nF
                            </span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                          <div>Upon MOSFET turn-off, leakage energy <Latex math="\frac{1}{2} L_{leak} I_{pk}^2" /> cannot couple to the secondary and must be absorbed by the RCD clamp to protect against catastrophic overvoltage.</div>
                          <div>With steady-state overshoot <Latex math="V_{spike}" />, capacitor rating <Latex math="V_c = V_{or} + V_{spike}" />:</div>
                          <Latex math="P_{loss} = \frac{1}{2} L_{leak} I_{pk}^2 \cdot f_{sw} \cdot \frac{V_c}{V_c - V_{or}}" block />
                          <div>Clamp dissipation resistance is sized by <Latex math="R_{clamp} = V_c^2 / P_{loss}" />.</div>
                          <div>To keep clamp voltage ripple under 10%:</div>
                          <Latex math="\Delta V_c \approx \frac{V_c}{R_{clamp} C_{clamp} f_{sw}} \le 10\% V_c \implies C_{clamp} \ge \frac{1}{0.1 R_{clamp} f_{sw}}" block />
                        </AccordionContent>
                      </AccordionItem>

                      {/* Formula 4: Semiconductor Voltage Stress */}
                      <AccordionItem value="stress" className="border-slate-800">
                        <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2">
                          <div className="flex flex-col items-start gap-0.5 text-left">
                            <span className="text-[10px] text-slate-400">MOSFET & Diode Voltage Stresses</span>
                            <span className="font-semibold text-cyan-300">
                              Vds_max = {calcData.simulation_time.v_ds_max.toFixed(1)}V / Vrev_max = {calcData.simulation_time.v_rev_max.toFixed(1)}V
                            </span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                          <div>**MOSFET Stress**: At turn-off, the switch withstands DC input voltage plus reflected secondary voltage plus leakage spike:</div>
                          <Latex math="V_{ds,max} = V_{in} + V_{or} + V_{spike}" block />
                          <div>**Diode Stress**: During switch conduction, the secondary diode is reverse-biased with output voltage plus coupled input:</div>
                          <Latex math="V_{rev,max} = V_{out} + \frac{V_{in}}{n_{ps}}" block />
                          <div>where transformer turns ratio <Latex math="n_{ps} = V_{or} / (V_{out} + V_d)" />.</div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </div>

                  <div className="flex flex-col gap-3">
                    <Tabs value={activeTab} onValueChange={(v: any) => setActiveTab(v)} className="w-full">
                      <TabsList className="bg-[#020617] border border-slate-800 h-8 p-0.5">
                        <TabsTrigger value="time" className="text-[10px] px-3 h-7 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400">
                          Transformer Waveforms & Ripple
                        </TabsTrigger>
                        <TabsTrigger value="bode" className="text-[10px] px-3 h-7 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400">
                          Small-Signal Loop Bode Plot
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>

                    <div className="w-full h-80 rounded-lg bg-[#020617] border border-slate-800 p-2 relative">
                      {activeTab === 'time' ? (
                        <ReactECharts notMerge={true} option={timeChartOption} style={{ width: '100%', height: '100%' }} />
                      ) : (
                        <ReactECharts notMerge={true} option={bodeChartOption} style={{ width: '100%', height: '100%' }} />
                      )}
                      {activeTab === 'bode' && calcData.simulation_bode.fc_khz > 0 && (
                        <div className="absolute bottom-3 right-4 p-2 bg-slate-950/80 rounded border border-slate-800 text-[10px] text-slate-400 flex flex-col gap-1 leading-none z-10 font-mono">
                          <div>Crossover fc: <span className="text-cyan-400 font-bold">{calcData.simulation_bode.fc_khz.toFixed(2)} kHz</span></div>
                          <div>Phase Margin PM: <span className="text-emerald-400 font-bold">{calcData.simulation_bode.pm_deg.toFixed(1)}°</span></div>
                        </div>
                      )}
                    </div>
                  </div>

                  {bomData && (
                    <div className="flex flex-col gap-4">
                      <div className="h-px bg-slate-900" />
                      <span className="text-xs font-semibold text-slate-300">
                        Commercial BOM Selection (1.2x Voltage Margin, 1.5x Current Margin)
                      </span>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        
                        <div className="flex flex-col gap-2">
                          <span className="text-[10px] font-semibold text-cyan-400">Primary MOSFET (Vds &ge; {bomData.requirements.sw_v.toFixed(1)}V, Id &ge; {bomData.requirements.sw_i.toFixed(2)}A)</span>
                          <div className="overflow-x-auto">
                            <table className="w-full text-[10px] text-slate-400 border border-slate-900 border-collapse">
                              <thead>
                                <tr className="bg-slate-900 text-slate-300 font-semibold border-b border-slate-800">
                                  <th className="px-2 py-1.5 text-left">Part Number</th>
                                  <th className="px-2 py-1.5 text-left">Vds</th>
                                  <th className="px-2 py-1.5 text-left">Id</th>
                                  <th className="px-2 py-1.5 text-left">Rds(on)</th>
                                  <th className="px-2 py-1.5 text-left">Package</th>
                                </tr>
                              </thead>
                              <tbody>
                                {bomData.switches.map((sw, i) => (
                                  <tr key={i} className="border-b border-slate-900 hover:bg-slate-900/30">
                                    <td className="px-2 py-1.5 text-slate-200 font-medium">{sw.name}</td>
                                    <td className="px-2 py-1.5">{sw.v_ds_max}V</td>
                                    <td className="px-2 py-1.5">{sw.i_d_max}A</td>
                                    <td className="px-2 py-1.5">{(sw.r_ds_on*1000).toFixed(1)}mΩ</td>
                                    <td className="px-2 py-1.5 text-slate-500">{sw.package}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>

                        <div className="flex flex-col gap-2">
                          <span className="text-[10px] font-semibold text-purple-400">Secondary Rectifier Diode (Vr &ge; {bomData.requirements.diode_v.toFixed(1)}V, If &ge; {bomData.requirements.diode_i.toFixed(2)}A)</span>
                          <div className="overflow-x-auto">
                            <table className="w-full text-[10px] text-slate-400 border border-slate-900 border-collapse">
                              <thead>
                                <tr className="bg-slate-900 text-slate-300 font-semibold border-b border-slate-800">
                                  <th className="px-2 py-1.5 text-left">Part Number</th>
                                  <th className="px-2 py-1.5 text-left">Vr</th>
                                  <th className="px-2 py-1.5 text-left">If</th>
                                  <th className="px-2 py-1.5 text-left">Vf</th>
                                  <th className="px-2 py-1.5 text-left">Package</th>
                                </tr>
                              </thead>
                              <tbody>
                                {bomData.diodes.map((d, i) => (
                                  <tr key={i} className="border-b border-slate-900 hover:bg-slate-900/30">
                                    <td className="px-2 py-1.5 text-slate-200 font-medium">{d.name}</td>
                                    <td className="px-2 py-1.5">{d.v_r_max}V</td>
                                    <td className="px-2 py-1.5">{d.i_f_max}A</td>
                                    <td className="px-2 py-1.5">{d.v_f}V</td>
                                    <td className="px-2 py-1.5 text-slate-500">{d.package}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>

                      </div>
                    </div>
                  )}

                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-slate-500 text-xs">
                  Awaiting calculation results...
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom DRC warning board */}
      <div className="w-full">
        <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200">
          <CardHeader className="p-5 pb-3">
            <CardTitle className="text-xs font-bold text-white border-l-2 border-yellow-500 pl-2 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-yellow-500" />
              DRC Rule Verification
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 pt-0 flex flex-col gap-3 min-h-[100px] justify-center">
            {calcData?.drc_warnings && calcData.drc_warnings.length > 0 ? (
              <div className="p-3.5 rounded-lg bg-yellow-950/20 border border-yellow-500/20 text-yellow-400 text-xs flex flex-col gap-2 leading-relaxed">
                {calcData.drc_warnings.map((warn: string, i: number) => (
                  <span key={i} className="flex items-start gap-1">
                    <ShieldAlert className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                    <span>{warn}</span>
                  </span>
                ))}
              </div>
            ) : (
              <div className="p-3.5 rounded-lg bg-emerald-950/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>No design safety risks detected (DRC Clear)</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      </>
      )}

    </div>
            </div>
          )}
        </DragCard>
      )}
      onDropOnColumn={handleDropOnColumn}
    />
  );
}