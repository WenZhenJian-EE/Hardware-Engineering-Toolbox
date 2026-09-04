import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';

import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card, CardContent } from './ui/Card';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
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

export default function SnubberPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<'estimate' | 'measure' | 'rcd'>('estimate', 'activeTab');
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
    panelKey: 'layout_snubberpanel_v3_' + activeTab,
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 820, results: 820 }
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [drcWarnings, setDrcWarnings] = useState<string[]>([]);

  // 1. Estimate State
  const [estCoss, setEstCoss] = useState<number>(200);
  const [estLLoop, setEstLLoop] = useState<number>(5);
  const [estVin, setEstVin] = useState<number>(12);
  const [estFsw, setEstFsw] = useState<number>(500);
  const [estIpk, setEstIpk] = useState<number>(5.0);
  const [estVdsRating, setEstVdsRating] = useState<number>(30.0);
  const [estPin, setEstPin] = useState<number>(100);
  
  // Custom R/C overrides
  const [customREnabled, setCustomREnabled] = useState<boolean>(false);
  const [customCEnabled, setCustomCEnabled] = useState<boolean>(false);
  const [customR, setCustomR] = useState<number>(5.0);
  const [customC, setCustomC] = useState<number>(600);
  const [estVSwing, setEstVSwing] = useState<number>(0);
  const [estCalcData, setEstCalcData] = useState<any>(null);

  // 2. Measure State
  const [measFRing, setMeasFRing] = useState<number>(100);
  const [measCAdd, setMeasCAdd] = useState<number>(100);
  const [measFShift, setMeasFShift] = useState<number>(70);
  const [measVin, setMeasVin] = useState<number>(12);
  const [measFsw, setMeasFsw] = useState<number>(500);
  const [measIpk, setMeasIpk] = useState<number>(5.0);
  const [measVdsRating, setMeasVdsRating] = useState<number>(30.0);
  const [measPin, setMeasPin] = useState<number>(100);
  const [measVSwing, setMeasVSwing] = useState<number>(0);
  const [measCalcData, setMeasCalcData] = useState<any>(null);

  // 3. RCD State
  const [rcdLlk, setRcdLlk] = useState<number>(5.0);
  const [rcdIpk, setRcdIpk] = useState<number>(2.0);
  const [rcdVor, setRcdVor] = useState<number>(80);
  const [rcdFsw, setRcdFsw] = useState<number>(65);
  const [rcdVSpike, setRcdVSpike] = useState<number>(50);
  const [rcdRipple, setRcdRipple] = useState<number>(10);
  const [rcdVin, setRcdVin] = useState<number>(310);
  const [rcdVdsRating, setRcdVdsRating] = useState<number>(600);
  const [rcdCalcData, setRcdCalcData] = useState<any>(null);

  // Calculate Estimate
  const calculateEstimate = async () => {
    setLoading(true);
    setError(null);
    try {
      const z0 = Math.sqrt((estLLoop * 1e-9) / (estCoss * 1e-12));
      const r_rec = z0;
      const c_rec = 3.0 * estCoss;
      
      const params = {
        coss_pf: estCoss,
        l_loop_nh: estLLoop,
        vin: estVin,
        fsw_khz: estFsw,
        ipk: estIpk,
        vds_rating: estVdsRating,
        pin_w: estPin,
        r_snub: customREnabled ? customR : r_rec,
        c_snub: customCEnabled ? customC : c_rec,
        v_swing: estVSwing > 0 ? estVSwing : undefined
      };
      
      const res = await apiFetch('/api/calculate/snubber/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      if (!res.ok) {
        const errDetail = await res.json();
        throw new Error(errDetail.detail || 'Failed to calculate snubber formula');
      }
      const data = await res.json();
      if (activeTabRef.current !== 'estimate') return;
      const z0_val = Math.sqrt((estLLoop * 1e-9) / (estCoss * 1e-12));
      if (data.design && data.design.z0 === undefined) {
        data.design.z0 = z0_val;
      }
      setEstCalcData(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (e: any) {
      if (activeTabRef.current !== 'estimate') return;
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Calculate Measure
  const calculateMeasure = async () => {
    if (measFShift >= measFRing) {
      setMeasCalcData(null);
      setError("Shifted frequency f_shift with added capacitor must be lower than original ringing frequency f_ring!");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = {
        f_ring_mhz: measFRing,
        c_add_pf: measCAdd,
        f_shift_mhz: measFShift,
        vin: measVin,
        fsw_khz: measFsw,
        ipk: measIpk,
        vds_rating: measVdsRating,
        pin_w: measPin,
        v_swing: measVSwing > 0 ? measVSwing : undefined
      };
      
      const res = await apiFetch('/api/calculate/snubber/measure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      if (!res.ok) {
        const errDetail = await res.json();
        throw new Error(errDetail.detail || 'Failed to calculate measured snubber');
      }
      const data = await res.json();
      if (activeTabRef.current !== 'measure') return;
      setMeasCalcData(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (e: any) {
      if (activeTabRef.current !== 'measure') return;
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Calculate RCD
  const calculateRcd = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        l_lk_uh: rcdLlk,
        ipk: rcdIpk,
        vor: rcdVor,
        fsw_khz: rcdFsw,
        v_spike: rcdVSpike,
        ripple_pct: rcdRipple / 100,
        vin: rcdVin,
        vds_rating: rcdVdsRating
      };
      
      const res = await apiFetch('/api/calculate/snubber/rcd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      if (!res.ok) {
        const errDetail = await res.json();
        throw new Error(errDetail.detail || 'Failed to calculate RCD clamp');
      }
      const data = await res.json();
      if (activeTabRef.current !== 'rcd') return;
      setRcdCalcData(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (e: any) {
      if (activeTabRef.current !== 'rcd') return;
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'estimate') calculateEstimate();
  }, [estCoss, estLLoop, estVin, estFsw, estIpk, estVdsRating, estPin, customREnabled, customCEnabled, customR, customC, activeTab]);

  useEffect(() => {
    if (activeTab === 'measure') calculateMeasure();
  }, [measFRing, measCAdd, measFShift, measVin, measFsw, measIpk, measVdsRating, measPin, activeTab]);

  useEffect(() => {
    if (activeTab === 'rcd') calculateRcd();
  }, [rcdLlk, rcdIpk, rcdVor, rcdFsw, rcdVSpike, rcdRipple, rcdVin, rcdVdsRating, activeTab]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('target_snubber_data');
      if (raw) {
        const data = JSON.parse(raw);
        if (data.tab === 'rcd' && data.params) {
          const p = data.params;
          if (p.rcd_llk !== undefined) setRcdLlk(p.rcd_llk);
          if (p.rcd_ipk !== undefined) setRcdIpk(p.rcd_ipk);
          if (p.rcd_vor !== undefined) setRcdVor(p.rcd_vor);
          if (p.rcd_fsw !== undefined) setRcdFsw(p.rcd_fsw);
          if (p.rcd_vin !== undefined) setRcdVin(p.rcd_vin);
          if (p.rcd_vds_rating !== undefined) setRcdVdsRating(p.rcd_vds_rating);
          setActiveTab('rcd');
        }
        localStorage.removeItem('target_snubber_data');
      }
    } catch (e) {
      console.error("Failed to parse target snubber data", e);
    }
  }, []);

  return (
    <div className="h-full w-full flex flex-col overflow-hidden text-slate-100 bg-[#070a13] p-4 pb-0 gap-4">
      {/* Header Banner */}
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
            <h1 className="text-base font-bold text-white tracking-tight">Power Switch Snubber & Clamp Design</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Sizes turn-off overshoot RC snubbers and flyback RCD clamps using frequency-shift measurements or theoretical models.
            </p>
          </div>
        </div>
        
        <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as any)} className="w-auto">
          <TabsList className="bg-[#020617] border border-slate-800 h-9 p-0.5">
            <TabsTrigger value="estimate" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">RC Snubber: Theoretical Estimate</TabsTrigger>
            <TabsTrigger value="measure" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">RC Snubber: Measurement Sizing</TabsTrigger>
            <TabsTrigger value="rcd" className="text-[10px] px-3 h-8 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">RCD Clamp Design (Flyback)</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* DRC Warnings */}
      {drcWarnings.length > 0 && (
        <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 flex flex-col gap-1.5 animate-fade-in">
          <span className="text-xs font-bold text-amber-400 flex items-center gap-1">
            ⚠️ Physical Design Rule Check (DRC) Violations:
          </span>
          <div className="flex flex-col gap-1">
            {drcWarnings.map((warn, i) => (
              <span key={i} className="text-xs text-amber-300/90 leading-relaxed">• {warn}</span>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium">
          {error}
        </div>
      )}

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
            >
              {key === 'input' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Operating Input Conditions</span>
                  </div>

                  {activeTab === 'estimate' && (
                    <>
                      <div className="border border-slate-850 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Parasitics & Operating Conditions</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Junction Cap Coss (pF)</label>
                            <input type="number" value={estCoss} onChange={(e) => setEstCoss(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Loop Inductance L_loop (nH)</label>
                            <input type="number" value={estLLoop} onChange={(e) => setEstLLoop(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Operating Voltage Vin (V)</label>
                            <input type="number" value={estVin} onChange={(e) => setEstVin(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Switching Frequency fsw (kHz)</label>
                            <input type="number" value={estFsw} onChange={(e) => setEstFsw(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Peak Current I_pk (A)</label>
                            <input type="number" value={estIpk} onChange={(e) => setEstIpk(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Switch Voltage Rating Vds_rating (V)</label>
                            <input type="number" value={estVdsRating} onChange={(e) => setEstVdsRating(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">System Input Power Pin (W)</label>
                          <input type="number" value={estPin} onChange={(e) => setEstPin(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>

                      <div className="border border-slate-855 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Manual RC Snubber Trimming</span>
                        <div className="flex flex-col gap-3">
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-2">
                              <input type="checkbox" checked={customREnabled} onChange={(e) => setCustomREnabled(e.target.checked)} id="custR" className="cursor-pointer" />
                              <label htmlFor="custR" className="text-[9px] text-slate-400 cursor-pointer">Custom Resistor R_snub (Ω)</label>
                            </div>
                            <input type="number" disabled={!customREnabled} value={customR} onChange={(e) => setCustomR(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none disabled:opacity-40" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-2">
                              <input type="checkbox" checked={customCEnabled} onChange={(e) => setCustomCEnabled(e.target.checked)} id="custC" className="cursor-pointer" />
                              <label htmlFor="custC" className="text-[9px] text-slate-400 cursor-pointer">Custom Capacitor C_snub (pF)</label>
                            </div>
                            <input type="number" disabled={!customCEnabled} value={customC} onChange={(e) => setCustomC(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none disabled:opacity-40" />
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {activeTab === 'measure' && (
                    <div className="border border-slate-850 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
                      <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Frequency-Shift Measurement Parameters</span>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">Original Ringing Freq f_ring (MHz)</label>
                        <input type="number" value={measFRing} onChange={(e) => setMeasFRing(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">External Parallel Cap C_add (pF)</label>
                        <input type="number" value={measCAdd} onChange={(e) => setMeasCAdd(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">Shifted Ringing Freq f_shift (MHz)</label>
                        <input type="number" value={measFShift} onChange={(e) => setMeasFShift(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Operating Voltage Vin (V)</label>
                          <input type="number" value={measVin} onChange={(e) => setMeasVin(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Switching Frequency fsw (kHz)</label>
                          <input type="number" value={measFsw} onChange={(e) => setMeasFsw(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Peak Current I_pk (A)</label>
                          <input type="number" value={measIpk} onChange={(e) => setMeasIpk(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">MOSFET Rating Vds_rating (V)</label>
                          <input type="number" value={measVdsRating} onChange={(e) => setMeasVdsRating(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-550">System Input Power Pin (W)</label>
                        <input type="number" value={measPin} onChange={(e) => setMeasPin(e.target.value as any)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                      </div>
                    </div>
                  )}

                  {activeTab === 'rcd' && (
                    <div className="border border-slate-850 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
                      <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Flyback Transformer & Active Switch</span>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Leakage Inductance L_lk (μH)</label>
                          <input type="number" step="0.1" value={rcdLlk} onChange={(e) => setRcdLlk(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Primary Peak Current I_pk (A)</label>
                          <input type="number" step="0.1" value={rcdIpk} onChange={(e) => setRcdIpk(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Reflected Voltage Vor (V)</label>
                          <input type="number" value={rcdVor} onChange={(e) => setRcdVor(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Switching Frequency fsw (kHz)</label>
                          <input type="number" value={rcdFsw} onChange={(e) => setRcdFsw(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Allowable Voltage Spike V_spike (V)</label>
                          <input type="number" value={rcdVSpike} onChange={(e) => setRcdVSpike(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Capacitor Voltage Ripple Target ΔVc (%)</label>
                          <input type="number" value={rcdRipple} onChange={(e) => setRcdRipple(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Max DC Input Vin_max (V)</label>
                          <input type="number" value={rcdVin} onChange={(e) => setRcdVin(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Switch Voltage Rating Vds_rating (V)</label>
                          <input type="number" value={rcdVdsRating} onChange={(e) => setRcdVdsRating(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'results' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-6">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white">Snubber Design Calculation Results</span>
                  </div>

                  {/* RC snubber estimate results */}
                  {activeTab === 'estimate' && estCalcData && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-3 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Characteristic Z0</span>
                          <span className="text-xs font-bold text-white font-mono">{estCalcData.design.z0.toFixed(1)} Ω</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Recommended R_snub</span>
                          <span className="text-xs font-bold text-cyan-400 font-mono">{estCalcData.design.r_snub_ohm.toFixed(1)} Ω</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Recommended C_snub</span>
                          <span className="text-xs font-bold text-cyan-400 font-mono">{estCalcData.design.c_snub_pf.toFixed(0)} pF</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Total Snubber Power Loss</span>
                          <span className="text-xs font-bold text-rose-400 font-mono">{estCalcData.design.p_snub_loss_w.toFixed(3)} W</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Peak Voltage with Snubber</span>
                          <span className="text-xs font-bold text-emerald-400 font-mono">{estCalcData.design.v_max_with_snub.toFixed(1)} V</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Efficiency Drop Percentage</span>
                          <span className="text-xs font-bold text-rose-400 font-mono">{estCalcData.design.delta_eff_pct.toFixed(3)} %</span>
                        </div>
                      </div>

                      {/* SVG loop circuit */}
                      <Card className="bg-slate-900/40 border-slate-800/80">
                        <CardContent className="pt-4 flex justify-center bg-slate-950/20 py-4 border-t border-slate-900/50">
                          <svg width="280" height="120" viewBox="0 0 280 120" className="text-slate-350">
                            <line x1="80" y1="15" x2="105" y2="15" stroke="#64748b" strokeWidth="1.2" />
                            <path d="M 105,15 Q 110,8 115,15 Q 120,8 125,15 Q 130,8 135,15 Q 140,8 145,15" fill="none" stroke="#fbbf24" strokeWidth="1.2" />
                            <line x1="145" y1="15" x2="170" y2="15" stroke="#64748b" strokeWidth="1.2" />
                            <text x="125" y="6" textAnchor="middle" fill="#fbbf24" className="text-[6px] font-mono">Parasitic L_loop = {estLLoop} nH</text>
                            
                            <circle cx="170" cy="15" r="2.5" fill="#cbd5e1" />
                            <line x1="170" y1="15" x2="110" y2="15" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="110" y1="15" x2="110" y2="35" stroke="#64748b" strokeWidth="1.2" />
                            
                            <line x1="105" y1="35" x2="115" y2="35" stroke="#cbd5e1" strokeWidth="1.2" />
                            <line x1="110" y1="35" x2="110" y2="42" stroke="#cbd5e1" strokeWidth="1.2" />
                            <line x1="110" y1="46" x2="100" y2="52" stroke="#22c55e" strokeWidth="1.5" />
                            <line x1="110" y1="58" x2="110" y2="65" stroke="#cbd5e1" strokeWidth="1.2" />
                            <line x1="105" y1="65" x2="115" y2="65" stroke="#cbd5e1" strokeWidth="1.2" />
                            
                            <line x1="110" y1="25" x2="70" y2="25" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="70" y1="25" x2="70" y2="42" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="62" y1="42" x2="78" y2="42" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="62" y1="46" x2="78" y2="46" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="70" y1="46" x2="70" y2="65" stroke="#64748b" strokeWidth="1.2" />
                            <text x="50" y="47" textAnchor="end" fill="#38bdf8" className="text-[6.5px] font-mono">Junction Cap Coss = {estCoss} pF</text>
                            
                            <line x1="170" y1="15" x2="170" y2="30" stroke="#64748b" strokeWidth="1.2" />
                            <path d="M 170,30 L 170,35 L 165,37 L 175,41 L 165,45 L 175,49 L 165,53 L 170,55 L 170,60" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                            <text x="180" y="45" fill="#ef4444" className="text-[6.5px] font-mono">R_snub = {estCalcData.design.r_snub_ohm.toFixed(1)} Ω</text>
                            
                            <line x1="170" y1="60" x2="170" y2="68" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="162" y1="68" x2="178" y2="68" stroke="#60a5fa" strokeWidth="1.5" />
                            <line x1="162" y1="72" x2="178" y2="72" stroke="#60a5fa" strokeWidth="1.5" />
                            <line x1="170" y1="72" x2="170" y2="85" stroke="#64748b" strokeWidth="1.2" />
                            <text x="180" y="73" fill="#60a5fa" className="text-[6.5px] font-mono">C_snub = {estCalcData.design.c_snub_pf.toFixed(0)} pF</text>
                            
                            <line x1="70" y1="65" x2="170" y2="65" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="120" y1="65" x2="120" y2="92" stroke="#10b981" strokeWidth="1.2" />
                            <line x1="110" y1="92" x2="130" y2="92" stroke="#10b981" strokeWidth="1.2" />
                            <line x1="114" y1="96" x2="126" y2="96" stroke="#10b981" strokeWidth="1.2" />
                            <line x1="118" y1="100" x2="122" y2="100" stroke="#10b981" strokeWidth="1.2" />
                          </svg>
                        </CardContent>
                      </Card>

                      <div className="text-[10px] text-slate-400 leading-relaxed border border-slate-800 rounded-lg p-3 bg-slate-900/10">
                        <span className="font-bold text-slate-300 block">RC Snubber Physical Equations:</span>
                        <Latex math={"Z_0 = \\sqrt{L_{loop} / C_{oss}}"} block />
                        <Latex math={"V_{max,snub} = V_{in} + I_{pk} \\sqrt{\\frac{L_{loop}}{C_{oss} + C_{snub}}} \\cdot e^{-\\frac{\\pi \\zeta}{\\sqrt{1-\\zeta^2}}}"} block />
                      </div>
                    </div>
                  )}

                  {/* RC snubber measure results */}
                  {activeTab === 'measure' && measCalcData && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-3 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Lumped Capacitance Cp</span>
                          <span className="text-xs font-bold text-white font-mono">{measCalcData.design.c_p_pf.toFixed(1)} pF</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Parasitic Inductance Lp</span>
                          <span className="text-xs font-bold text-white font-mono">{measCalcData.design.l_p_nh.toFixed(2)} nH</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Measured Characteristic Z0</span>
                          <span className="text-xs font-bold text-white font-mono">{measCalcData.design.z0.toFixed(1)} Ω</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Optimal R_snub</span>
                          <span className="text-xs font-bold text-cyan-400 font-mono">{measCalcData.design.r_snub_ohm.toFixed(1)} Ω</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Optimal C_snub</span>
                          <span className="text-xs font-bold text-cyan-400 font-mono">{measCalcData.design.c_snub_pf.toFixed(0)} pF</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Snubber Loss P_loss</span>
                          <span className="text-xs font-bold text-rose-400 font-mono">{measCalcData.design.overshoot_details.p_snub_loss_w.toFixed(3)} W</span>
                        </div>
                      </div>

                      <div className="text-[10px] text-slate-400 leading-relaxed border border-slate-800 rounded-lg p-3 bg-slate-900/10">
                        <span className="font-bold text-slate-350 block">Frequency-Shift Self-Locking Equations:</span>
                        <Latex math={"C_p = \\frac{C_{add}}{(f_{ring}/f_{shift})^2 - 1}"} block />
                        <Latex math={"L_p = \\frac{1}{(2\\pi f_{ring})^2 \\cdot C_p}"} block />
                      </div>
                    </div>
                  )}

                  {/* RCD flyback clamp results */}
                  {activeTab === 'rcd' && rcdCalcData && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Total Clamp Voltage V_clamp</span>
                          <span className="text-sm font-bold text-white font-mono">{rcdCalcData.design.v_clamp.toFixed(1)} V</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Clamp Resistor Power Loss P_loss</span>
                          <span className="text-sm font-bold text-rose-400 font-mono">{rcdCalcData.design.p_loss.toFixed(2)} W</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 bg-slate-900/20 p-3 rounded-lg border border-slate-850">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Recommended Clamp Resistor R_clamp</span>
                          <span className="text-sm font-bold text-cyan-400 font-mono">{(rcdCalcData.design.r_clamp / 1000).toFixed(2)} kΩ</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[9px] text-slate-500">Recommended Clamp Cap C_clamp</span>
                          <span className="text-sm font-bold text-cyan-400 font-mono">{(rcdCalcData.design.c_clamp * 1e9).toFixed(2)} nF</span>
                        </div>
                      </div>

                      {/* SVG flyback layout */}
                      <Card className="bg-slate-900/40 border-slate-800/80">
                        <CardContent className="pt-4 flex justify-center bg-slate-950/20 py-4 border-t border-slate-900/50">
                          <svg width="280" height="120" viewBox="0 0 280 120" className="text-slate-350">
                            <line x1="30" y1="15" x2="70" y2="15" stroke="#cbd5e1" strokeWidth="1.2" />
                            <line x1="70" y1="15" x2="70" y2="40" stroke="#cbd5e1" strokeWidth="1.2" />
                            
                            {/* Leakage inductor */}
                            <path d="M 70,40 Q 65,45 70,50 Q 65,55 70,60 Q 65,65 70,70" fill="none" stroke="#fbbf24" strokeWidth="1.2" />
                            <text x="82" y="58" fill="#fbbf24" className="text-[6.5px] font-mono">L_lk = {rcdLlk} μH</text>
                            
                            {/* Trans primary */}
                            <path d="M 70,70 L 70,95" stroke="#cbd5e1" strokeWidth="1.5" />
                            
                            {/* RCD Clamp branch */}
                            <line x1="70" y1="40" x2="150" y2="40" stroke="#64748b" strokeWidth="1.2" />
                            
                            {/* Diode */}
                            <polygon points="150,34 150,46 160,40" fill="#ec4899" stroke="#ec4899" strokeWidth="1" />
                            <line x1="160" y1="34" x2="160" y2="46" stroke="#cbd5e1" strokeWidth="1.2" />
                            <line x1="160" y1="40" x2="190" y2="40" stroke="#64748b" strokeWidth="1.2" />
                            
                            {/* R || C */}
                            <line x1="190" y1="40" x2="190" y2="20" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="190" y1="20" x2="210" y2="20" stroke="#64748b" strokeWidth="1.2" />
                            {/* R */}
                            <path d="M 210,20 L 215,20 L 217,16 L 221,24 L 225,16 L 229,24 L 233,16 L 235,20 L 250,20" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                            <text x="230" y="11" textAnchor="middle" fill="#ef4444" className="text-[6px] font-mono">R = {(rcdCalcData.design.r_clamp / 1000).toFixed(1)} kΩ</text>
                            
                            <line x1="190" y1="40" x2="190" y2="60" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="190" y1="60" x2="215" y2="60" stroke="#64748b" strokeWidth="1.2" />
                            {/* C */}
                            <line x1="215" y1="53" x2="215" y2="67" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="219" y1="53" x2="219" y2="67" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="219" y1="60" x2="250" y2="60" stroke="#64748b" strokeWidth="1.2" />
                            <text x="235" y="73" textAnchor="middle" fill="#38bdf8" className="text-[6px] font-mono">C = {(rcdCalcData.design.c_clamp * 1e9).toFixed(1)} nF</text>
                            
                            <line x1="250" y1="20" x2="250" y2="60" stroke="#cbd5e1" strokeWidth="1.2" />
                            <line x1="250" y1="40" x2="270" y2="40" stroke="#cbd5e1" strokeWidth="1.2" />
                          </svg>
                        </CardContent>
                      </Card>

                      <div className="text-[10px] text-slate-400 leading-relaxed border border-slate-800 rounded-lg p-3 bg-slate-900/10">
                        <span className="font-bold text-slate-350 block">Flyback Leakage Energy Impedance Clamp Equations:</span>
                        <Latex math={"V_{clamp} = V_{or} + V_{spike}"} block />
                        <Latex math={"P_{loss} = \\frac{1}{2} L_{lk} I_{pk}^2 f_{sw} \\cdot \\frac{V_{clamp}}{V_{clamp} - V_{or}}"} block />
                      </div>
                    </div>
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