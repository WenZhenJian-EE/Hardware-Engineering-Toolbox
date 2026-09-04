import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { LineChart, Plus, ShieldAlert, ShoppingBag, Trash2 } from 'lucide-react';
import type { Candidate } from './types';

const E96 = [
  10.0, 10.2, 10.5, 10.7, 11.0, 11.3, 11.5, 11.8, 12.1, 12.4, 12.7, 13.0, 13.3, 13.7, 14.0, 14.3, 14.7, 15.0,
  15.4, 15.8, 16.2, 16.5, 16.9, 17.4, 17.8, 18.2, 18.7, 19.1, 19.6, 20.0, 20.5, 21.0, 21.5, 22.1, 22.6, 23.2,
  23.7, 24.3, 24.9, 25.5, 26.1, 26.7, 27.4, 28.0, 28.7, 29.4, 30.1, 30.9, 31.6, 32.4, 33.2, 34.0, 34.8, 35.7,
  36.5, 37.4, 38.3, 39.2, 40.2, 41.2, 42.2, 43.2, 44.2, 45.3, 46.4, 47.5, 48.7, 49.9, 51.1, 52.3, 53.6, 54.9,
  56.2, 57.6, 59.0, 60.4, 61.9, 63.4, 64.9, 66.5, 68.1, 69.8, 71.5, 73.2, 75.0, 76.8, 78.7, 80.6, 82.5, 84.5,
  86.6, 88.7, 90.9, 93.1, 95.3, 97.6
];

function findClosestStandard(val: number, series: number[]): { value: number; error: number } {
  if (!val || val <= 0) return { value: 0, error: 0 };
  const log10 = Math.log10(val);
  const decade = Math.floor(log10);
  const normalized = val / Math.pow(10, decade);

  let best = series[0];
  let diff = Math.abs(normalized - best);

  for (let i = 1; i < series.length; i++) {
    const d = Math.abs(normalized - series[i]);
    if (d < diff) {
      diff = d;
      best = series[i];
    }
  }

  const standardVal = best * Math.pow(10, decade);
  const errorPct = ((standardVal - val) / val) * 100.0;
  return { value: standardVal, error: parseFloat(errorPct.toFixed(2)) };
}

interface DriverCardsProps {
  // Gate Driver
  drVcc: number;
  setDrVcc: (v: number) => void;
  drVee: number;
  setDrVee: (v: number) => void;
  drRgExt: number;
  setDrRgExt: (v: number) => void;
  drRgInt: number;
  setDrRgInt: (v: number) => void;
  drQg: number;
  setDrQg: (v: number) => void;
  drFsw: number;
  setDrFsw: (v: number) => void;
  drRes: any;

  // Desat
  dsVth: number;
  setDsVth: (v: number) => void;
  dsIchg: number;
  setDsIchg: (v: number) => void;
  dsTblank: number;
  setDsTblank: (v: number) => void;
  dsVf: number;
  setDsVf: (v: number) => void;
  dsVceTrip: number;
  setDsVceTrip: (v: number) => void;
  dsRes: any;

  // Bootstrap
  btQg: number;
  setBtQg: (v: number) => void;
  btFsw: number;
  setBtFsw: (v: number) => void;
  btIq: number;
  setBtIq: (v: number) => void;
  btDuty: number;
  setBtDuty: (v: number) => void;
  btVdrop: number;
  setBtVdrop: (v: number) => void;
  btQrr: number;
  setBtQrr: (v: number) => void;
  btVcc: number;
  setBtVcc: (v: number) => void;
  btVf: number;
  setBtVf: (v: number) => void;
  btRes: any;

  // GDT
  gdtVcc: number;
  setGdtVcc: (v: number) => void;
  gdtFsw: number;
  setGdtFsw: (v: number) => void;
  gdtDuty: number;
  setGdtDuty: (v: number) => void;
  gdtAe: number;
  setGdtAe: (v: number) => void;
  gdtBsat: number;
  setGdtBsat: (v: number) => void;
  gdtNp: number;
  setGdtNp: (v: number) => void;
  gdtAl: number;
  setGdtAl: (v: number) => void;
  gdtRes: any;

  // Compare
  cmpVbus: number;
  setCmpVbus: (v: number) => void;
  cmpIrms: number;
  setCmpIrms: (v: number) => void;
  cmpIsw: number;
  setCmpIsw: (v: number) => void;
  cmpDuty: number;
  setCmpDuty: (v: number) => void;
  cmpFsw: number;
  setCmpFsw: (v: number) => void;
  cmpVgate: number;
  setCmpVgate: (v: number) => void;
  cmpTcase: number;
  setCmpTcase: (v: number) => void;
  candidates: Candidate[];
  addCandidate: () => void;
  removeCandidate: (id: number) => void;
  updateCandidate: (id: number, field: keyof Candidate, value: any) => void;
  runCompare: () => void;
  cmpSummaryHtml: string;

  Latex: React.FC<{ math: string; block?: boolean }>;
}

export const renderDriverCardContent = (key: string, props: DriverCardsProps): React.ReactNode => {
  const {
    drVcc, setDrVcc, drVee, setDrVee, drRgExt, setDrRgExt, drRgInt, setDrRgInt, drQg, setDrQg, drFsw, setDrFsw, drRes,
    dsVth, setDsVth, dsIchg, setDsIchg, dsTblank, setDsTblank, dsVf, setDsVf, dsVceTrip, setDsVceTrip, dsRes,
    btQg, setBtQg, btFsw, setBtFsw, btIq, setBtIq, btDuty, setBtDuty, btVdrop, setBtVdrop, btQrr, setBtQrr, btVcc, setBtVcc, btVf, setBtVf, btRes,
    gdtVcc, setGdtVcc, gdtFsw, setGdtFsw, gdtDuty, setGdtDuty, gdtAe, setGdtAe, gdtBsat, setGdtBsat, gdtNp, setGdtNp, gdtAl, setGdtAl, gdtRes,
    cmpVbus, setCmpVbus, cmpIrms, setCmpIrms, cmpIsw, setCmpIsw, cmpDuty, setCmpDuty, cmpFsw, setCmpFsw, cmpVgate, setCmpVgate, cmpTcase, setCmpTcase,
    candidates, addCandidate, removeCandidate, updateCandidate, runCompare, cmpSummaryHtml,
    Latex
  } = props;

  switch (key) {
    case 'input_gate':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Gate Drive Circuit Parameters</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Driver IC & Gate Characteristics</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Positive Gate Voltage Vcc (V)</label>
                  <input type="number" value={drVcc} onChange={(e) => setDrVcc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Negative Gate Voltage Vee (V)</label>
                  <input type="number" value={drVee} onChange={(e) => setDrVee(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">External Gate Resistor Rg_ext (Ω)</label>
                  <input type="number" value={drRgExt} onChange={(e) => setDrRgExt(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Internal Gate Resistor Rg_int (Ω)</label>
                  <input type="number" value={drRgInt} onChange={(e) => setDrRgInt(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Total Gate Charge Qg (nC)</label>
                  <input type="number" value={drQg} onChange={(e) => setDrQg(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={drFsw} onChange={(e) => setDrFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_gate':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Drive Power & Peak Current Sizing</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {drRes && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase font-semibold">Peak Source/Sink</span>
                    <span className="text-xs font-bold text-cyan-400">{(drRes.i_peak ?? 0).toFixed(2)} A</span>
                    <span className="text-[8px] text-slate-400">At min loop resistance</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase font-semibold">Total Drive Power P_drv</span>
                    <span className="text-xs font-bold text-emerald-400">{((drRes.p_drv ?? 0) * 1000).toFixed(1)} mW</span>
                    <span className="text-[8px] text-slate-400">Gate charge cycling</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase font-semibold">External Rg Loss P_rg</span>
                    <span className="text-xs font-bold text-amber-400">{((drRes.p_rg ?? 0) * 1000).toFixed(1)} mW</span>
                    <span className="text-[8px] text-slate-400">Resistor dissipation</span>
                  </div>
                </div>

                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Gate Voltage Swing:</span>
                    <span className="text-slate-200 font-bold font-mono">{drVcc + Math.abs(drVee)} V</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Recommended Min Dead Time:</span>
                    <span className="text-rose-400 font-bold font-mono">&gt; {(drRes.deadtime ?? 0).toFixed(0)} ns</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">External Resistor Loss Share:</span>
                    <span className="text-slate-200 font-semibold font-mono">{(((drRes.p_rg ?? 0) / (drRes.p_drv || 1)) * 100).toFixed(1)} %</span>
                  </div>
                </div>

                <div className="border border-slate-800 rounded-lg p-3 bg-slate-950/20 flex flex-col items-center">
                  <span className="text-[9px] text-slate-400 mb-2">Gate Drive Loop Equivalent Topology</span>
                  <svg className="w-full max-w-2xl h-auto text-slate-350 mx-auto select-none" viewBox="0 0 340 100">
                    <rect x="10" y="20" width="70" height="60" rx="4" fill="#0f172a" stroke="#1e293b" strokeWidth="1.5" />
                    <text x="45" y="54" className="text-[10px] font-bold fill-sky-400" textAnchor="middle">Driver IC</text>
                    <line x1="80" y1="50" x2="120" y2="50" stroke="#475569" strokeWidth="1.5" />
                    <circle cx="100" cy="50" r="2.5" fill="#38bdf8" />
                    <rect x="120" y="42" width="30" height="16" fill="#0f172a" stroke="#10b981" strokeWidth="1.5" />
                    <text x="135" y="53" className="text-[8px] font-bold fill-emerald-400 font-mono" textAnchor="middle">Rg_ext</text>
                    <line x1="150" y1="50" x2="190" y2="50" stroke="#475569" strokeWidth="1.5" />
                    <rect x="190" y="42" width="30" height="16" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                    <text x="205" y="53" className="text-[8px] font-bold fill-slate-400 font-mono" textAnchor="middle">Rg_int</text>
                    <line x1="220" y1="50" x2="260" y2="50" stroke="#475569" strokeWidth="1.5" />
                    <line x1="260" y1="35" x2="260" y2="65" stroke="#f43f5e" strokeWidth="2" />
                    <line x1="265" y1="30" x2="265" y2="70" stroke="#f43f5e" strokeWidth="2" strokeDasharray="2,2" />
                    <line x1="265" y1="35" x2="285" y2="35" stroke="#475569" strokeWidth="1.5" />
                    <line x1="265" y1="65" x2="285" y2="65" stroke="#475569" strokeWidth="1.5" />
                    <text x="300" y="54" className="text-[10px] font-bold fill-rose-500" fontWeight="bold">MOSFET</text>
                  </svg>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'bom_gate': {
      const closestMatch = findClosestStandard(drRgExt, E96);
      const alignedVal = closestMatch.value;
      const alignedErr = closestMatch.error;
      
      let smdCode = '';
      if (alignedVal < 10) {
        smdCode = `${alignedVal.toFixed(1).replace('.', 'R')}0`;
      } else if (alignedVal < 100) {
        smdCode = `${Math.round(alignedVal)}R0`;
      } else {
        smdCode = `${Math.round(alignedVal)}0`;
      }

      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <ShoppingBag className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Commercial Gate Resistor E96 BOM Alignment</span>
          </div>
          
          <div className="flex-grow overflow-y-auto scrollbar-thin text-xs text-slate-350">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  Aligned standard for input resistance <span className="text-emerald-400 font-bold font-mono">{drRgExt} Ω</span>:
                </div>
                
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 grid grid-cols-3 gap-2">
                  <div>
                    <span className="block text-[8px] text-slate-500 uppercase">E96 Value</span>
                    <span className="text-xs font-bold text-emerald-400 font-mono">
                      {alignedVal.toFixed(1)} Ω
                    </span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-slate-500 uppercase">Error</span>
                    <span className="text-xs font-bold text-slate-200 font-mono">
                      {alignedErr > 0 ? '+' : ''}{alignedErr}%
                    </span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-slate-500 uppercase">Package</span>
                    <span className="text-xs text-slate-350 font-semibold font-mono">1206 Thin Film</span>
                  </div>
                </div>

                <div className="border border-slate-900 rounded-lg p-2 bg-slate-950/40 flex flex-col items-center">
                  <svg className="w-full max-w-[160px] h-[65px] text-slate-350 select-none" viewBox="0 0 160 70">
                    <line x1="10" y1="35" x2="150" y2="35" stroke="#047857" strokeWidth="5" strokeLinecap="round" opacity="0.3" />
                    <rect x="35" y="15" width="90" height="40" fill="#1e293b" stroke="#334155" strokeWidth="1.5" rx="1.5" />
                    <rect x="35" y="15" width="16" height="40" fill="#cbd5e1" rx="0.5" />
                    <rect x="109" y="15" width="16" height="40" fill="#cbd5e1" rx="0.5" />
                    <text x="80" y="39" className="text-[12px] font-black fill-slate-100 font-mono" textAnchor="middle">{smdCode}</text>
                    <text x="80" y="65" className="text-[8px] fill-slate-500 font-mono" textAnchor="middle">1206 (3216 Metric)</text>
                  </svg>
                </div>
              </div>

              <div className="space-y-2">
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
                  <span className="block text-[9px] text-cyan-400 font-bold mb-2 uppercase">Typical Gate Values & Sizing Rules</span>
                  <div className="space-y-1.5 text-[10px]">
                    <div className="flex justify-between border-b border-slate-900 pb-1 text-slate-500 text-[8px] font-semibold">
                      <span>Value</span>
                      <span>Target Topology</span>
                      <span>Recommended Tech</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span className="font-mono font-bold text-emerald-400">2.2 Ω</span>
                      <span>GaN / SiC High-Speed Bridges</span>
                      <span>0805 Thin Film Non-Inductive</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span className="font-mono font-bold text-emerald-400">4.7 Ω</span>
                      <span>Standard Silicon MOSFETs</span>
                      <span>1206 Thin Film 0.25W</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span className="font-mono font-bold text-emerald-400">10.0 Ω</span>
                      <span>Mid-Power Half-Bridge Primary</span>
                      <span>1206 Precision Thin Film</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span className="font-mono font-bold text-emerald-400">22.0 Ω</span>
                      <span>High-Power IGBT / Parallel Bridges</span>
                      <span>1206 Anti-Surge Thick Film</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      );
    }

    case 'input_desat':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">DESAT Blanking & Fault Parameters</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Driver IC DESAT Pin Setup</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">DESAT Threshold Vth (V)</label>
                  <input type="number" value={dsVth} onChange={(e) => setDsVth(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Charging Constant Current Ichg (μA)</label>
                  <input type="number" value={dsIchg} onChange={(e) => setDsIchg(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Target Blanking Time Tblank (μs)</label>
                  <input type="number" value={dsTblank} onChange={(e) => setDsTblank(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Diode Forward Drop Vf (V)</label>
                  <input type="number" value={dsVf} onChange={(e) => setDsVf(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Trip Voltage Threshold Vce_trip (V)</label>
                  <input type="number" value={dsVceTrip} onChange={(e) => setDsVceTrip(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_desat':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">DESAT Blanking Capacitor Sizing</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-350">
            {dsRes && (
              <div className="space-y-4">
                {dsRes.error_msg !== "" ? (
                  <div className="bg-rose-950/30 border border-rose-800 p-4 rounded-lg text-rose-400 font-mono text-xs">
                    {dsRes.error_msg}
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-3 font-mono">
                      <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                        <span className="text-[9px] text-slate-500 uppercase">Calculated Capacitance C_blk</span>
                        <span className="text-xs font-bold text-cyan-400">{(dsRes.c_blk_pf ?? 0).toFixed(1)} pF</span>
                      </div>
                      <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                        <span className="text-[9px] text-slate-500 uppercase">Recommended E24 Standard</span>
                        <span className="text-xs font-bold text-emerald-400">{dsRes.c_blk_std_pf} pF</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-xs flex flex-col justify-between">
                        <div>Series Resistor Range R_desat: <span className="text-amber-400 font-bold font-mono">{dsRes.r_desat_range}</span></div>
                        <div className="text-[10px] text-slate-400 leading-normal">
                          Blanking Time Formulation:
                          <Latex math={"t_{blank} = C_{blk} \\cdot \\frac{V_{th} - V_{f} - V_{ce,sat}}{I_{chg}}"} block />
                        </div>
                      </div>
                      <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-xs flex flex-col justify-between">
                        <span className="font-bold text-slate-300">DESAT Diode Selection Criteria</span>
                        <p className="text-[10px] text-slate-400 leading-relaxed">D_desat requires high breakdown voltage and ultra-fast recovery:</p>
                        <div className="space-y-1 font-mono text-[10px]">
                          <div className="flex justify-between border-b border-slate-900 pb-0.5">
                            <span>Voltage Rating:</span>
                            <span className="text-rose-400 font-bold">&gt; 650 V</span>
                          </div>
                          <div className="flex justify-between pt-0.5">
                            <span>Recommended P/N:</span>
                            <span className="text-emerald-400 font-bold">MURA160T3G / US1M</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="border border-slate-800 rounded-lg p-3 bg-slate-950/20 flex flex-col items-center">
                      <span className="text-[9px] text-slate-400 mb-2">DESAT Circuit Equivalent Schematic</span>
                      <svg className="w-full max-w-2xl h-auto text-slate-350 mx-auto select-none" viewBox="0 0 340 100">
                        <rect x="10" y="15" width="80" height="70" rx="4" fill="#0f172a" stroke="#1e293b" strokeWidth="1.5" />
                        <text x="50" y="36" className="text-[9px] font-bold fill-slate-300" textAnchor="middle">IC DESAT Pin</text>
                        <line x1="90" y1="50" x2="130" y2="50" stroke="#475569" strokeWidth="1.5" />
                        <line x1="130" y1="50" x2="130" y2="70" stroke="#475569" strokeWidth="1.5" />
                        <line x1="120" y1="70" x2="140" y2="70" stroke="#10b981" strokeWidth="2" />
                        <line x1="120" y1="74" x2="140" y2="74" stroke="#10b981" strokeWidth="2" />
                        <line x1="130" y1="74" x2="130" y2="90" stroke="#475569" strokeWidth="1.5" />
                        <text x="146" y="76" className="text-[8px] font-bold fill-emerald-400 font-mono">C_blk</text>
                        <line x1="130" y1="50" x2="180" y2="50" stroke="#475569" strokeWidth="1.5" />
                        <rect x="180" y="42" width="24" height="16" fill="#0f172a" stroke="#fbbf24" strokeWidth="1.5" />
                        <text x="192" y="53" className="text-[8px] font-bold fill-amber-400 font-mono" textAnchor="middle">R_desat</text>
                        <line x1="204" y1="50" x2="230" y2="50" stroke="#475569" strokeWidth="1.5" />
                        <polygon points="230,50 240,43 240,57" fill="#a78bfa" stroke="#a78bfa" strokeWidth="1" />
                        <line x1="230" y1="43" x2="230" y2="57" stroke="#a78bfa" strokeWidth="2" />
                        <line x1="240" y1="50" x2="280" y2="50" stroke="#475569" strokeWidth="1.5" />
                        <text x="235" y="38" className="text-[8px] font-bold fill-purple-400">D_desat</text>
                        <circle cx="280" cy="50" r="3" fill="#f43f5e" />
                        <text x="288" y="53" className="text-[8px] font-bold fill-rose-500">Drain</text>
                      </svg>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_desat':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">DESAT Blanking Capacitor Charging Waveform</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {dsRes && dsRes.error_msg === "" && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[220px]">
                <ReactECharts
                  notMerge={true}
                  option={{
                    backgroundColor: 'transparent',
                    tooltip: { trigger: 'axis' },
                    grid: { left: '8%', right: '8%', top: '15%', bottom: '15%', containLabel: true },
                    xAxis: {
                      type: 'value',
                      name: 'Time (μs)',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                      splitLine: { lineStyle: { color: '#1e293b' } }
                    },
                    yAxis: {
                      type: 'value',
                      name: 'DESAT Voltage (V)',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                      splitLine: { lineStyle: { color: '#1e293b' } }
                    },
                    series: [
                      {
                        name: 'V_desat(t)',
                        type: 'line',
                        smooth: true,
                        data: Array.from({ length: 40 }, (_, idx) => {
                          const t = (idx * (dsTblank * 1.5)) / 40;
                          const slope = dsIchg / (dsRes.c_blk_std_pf || 100);
                          const v = Math.min(dsVth * 1.2, dsVf + dsVceTrip + slope * t);
                          return [t.toFixed(2), v.toFixed(2)];
                        }),
                        lineStyle: { color: '#06b6d4', width: 2 },
                        markLine: {
                          symbol: 'none',
                          label: { position: 'insideEnd', formatter: 'Vth Threshold' },
                          data: [
                            { yAxis: dsVth, lineStyle: { color: '#ef4444', type: 'dashed' } }
                          ]
                        }
                      }
                    ]
                  }}
                  style={{ height: '100%', width: '100%' }}
                />
              </div>
            )}
          </div>
        </Card>
      );

    case 'input_boot':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Bootstrap Circuit Parameters</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Driver Supply & Switching Characteristics</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Total Gate Charge Qg (nC)</label>
                  <input type="number" value={btQg} onChange={(e) => setBtQg(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={btFsw} onChange={(e) => setBtFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">High-Side Quiescent Iq (μA)</label>
                  <input type="number" value={btIq} onChange={(e) => setBtIq(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Max Duty Cycle Dmax (%)</label>
                  <input type="number" value={btDuty} onChange={(e) => setBtDuty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Allowable Ripple Drop ΔV (V)</label>
                  <input type="number" value={btVdrop} onChange={(e) => setBtVdrop(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Bootstrap Diode Qrr (nC)</label>
                  <input type="number" value={btQrr} onChange={(e) => setBtQrr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Driver Supply Vcc (V)</label>
                  <input type="number" value={btVcc} onChange={(e) => setBtVcc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Bootstrap Diode Forward Vf (V)</label>
                  <input type="number" value={btVf} onChange={(e) => setBtVf(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_boot':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Bootstrap Capacitor Sizing Results</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-350 font-mono">
            {btRes && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Min Bootstrap Cap</span>
                    <span className="text-xs font-bold text-cyan-400">{(btRes.c_min_uf ?? 0).toFixed(4)} μF</span>
                    <span className="text-[8px] text-slate-400">Theoretical minimum</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Recommended C_boot</span>
                    <span className="text-xs font-bold text-emerald-400">{(btRes.c_rec_uf ?? 0).toFixed(3)} μF</span>
                    <span className="text-[8px] text-slate-400">With 10x safety margin</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Max Inrush Resistor</span>
                    <span className="text-xs font-bold text-amber-400">{(btRes.r_max_ohm ?? 0).toFixed(2)} Ω</span>
                    <span className="text-[8px] text-slate-400">Limits peak charging surge</span>
                  </div>
                </div>

                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">High-Side Charging Inrush Peak:</span>
                    <span className="text-slate-200 font-bold font-mono">{(btRes.i_inrush_peak ?? 0).toFixed(2)} A (Based on typical 2.2Ω series limit)</span>
                  </div>
                  <div className="text-[10px] text-slate-400 leading-normal">
                    Bootstrap Circuit Formulation:
                    <Latex math={"Q_{total} = Q_{g} + I_{q} \\cdot \\frac{D_{max}}{f_{sw}} + Q_{rr}"} block />
                    <Latex math={"C_{boot,min} = \\frac{Q_{total}}{\\Delta V_{boot}}"} block />
                  </div>
                </div>

                <div className="border border-slate-800 rounded-lg p-3 bg-slate-950/20 flex flex-col items-center">
                  <span className="text-[9px] text-slate-400 mb-2">Typical Bootstrap Circuit Topology</span>
                  <svg className="w-full max-w-2xl h-auto text-slate-350 mx-auto select-none" viewBox="0 0 340 90">
                    <text x="30" y="24" className="text-[9px] font-bold fill-sky-400">Vcc (15V)</text>
                    <line x1="30" y1="30" x2="30" y2="50" stroke="#475569" strokeWidth="1.5" />
                    <polygon points="45,50 53,42 53,58" fill="#a78bfa" stroke="#a78bfa" strokeWidth="1" />
                    <line x1="45" y1="42" x2="45" y2="58" stroke="#a78bfa" strokeWidth="2" />
                    <line x1="30" y1="50" x2="45" y2="50" stroke="#475569" strokeWidth="1.5" />
                    <line x1="53" y1="50" x2="80" y2="50" stroke="#475569" strokeWidth="1.5" />
                    <text x="49" y="35" className="text-[8px] font-bold fill-purple-400">D_boot</text>
                    <rect x="80" y="42" width="24" height="16" fill="#0f172a" stroke="#fbbf24" strokeWidth="1.5" />
                    <text x="92" y="53" className="text-[8px] font-bold fill-amber-400 font-mono" textAnchor="middle">R_boot</text>
                    <line x1="104" y1="50" x2="150" y2="50" stroke="#475569" strokeWidth="1.5" />
                    <circle cx="150" cy="50" r="3.5" fill="#38bdf8" />
                    <line x1="150" y1="50" x2="150" y2="75" stroke="#475569" strokeWidth="1.5" />
                    <line x1="140" y1="75" x2="160" y2="75" stroke="#10b981" strokeWidth="2" />
                    <line x1="140" y1="79" x2="160" y2="79" stroke="#10b981" strokeWidth="2" />
                    <text x="170" y="80" className="text-[8px] font-bold fill-emerald-400 font-mono">C_boot</text>
                  </svg>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'bom_boot':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <ShoppingBag className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Bootstrap Components BOM Selection</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-350">
            {btRes && (
              <div className="space-y-3 font-mono">
                <div>
                  <span className="text-slate-400 block font-semibold mb-1 text-[10px]">1. Bootstrap Capacitor C_boot:</span>
                  <div className="bg-slate-950 p-2 border border-slate-800 rounded flex justify-between font-mono">
                    <span>Recommended: <b>{(btRes.c_rec_uf ?? 1.0).toFixed(1)} μF / 50V</b></span>
                    <span className="text-emerald-400">Package: 0805 MLCC</span>
                  </div>
                </div>
                <div className="border-t border-slate-850 pt-2">
                  <span className="text-slate-400 block font-semibold mb-1 text-[10px]">2. Bootstrap Blocking Diode D_boot:</span>
                  <div className="bg-slate-950 p-2 border border-slate-800 rounded flex justify-between font-mono">
                    <span>Recommended: <b>MURA160 / ES1J</b></span>
                    <span className="text-amber-400">Rating: 600V / 1A</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'input_gdt':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">GDT Core & Drive Pulse Parameters</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-350">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Drive Pulse & Core Parameters</span>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Drive Voltage Swing V_drv (V)</label>
                  <input type="number" value={gdtVcc} onChange={(e) => setGdtVcc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={gdtFsw} onChange={(e) => setGdtFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Max Duty Cycle D_max</label>
                  <input type="number" step="0.05" value={gdtDuty} onChange={(e) => setGdtDuty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Core Cross-Section Ae (mm²)</label>
                  <input type="number" value={gdtAe} onChange={(e) => setGdtAe(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Core Saturation Flux Bsat (T)</label>
                  <input type="number" step="0.05" value={gdtBsat} onChange={(e) => setGdtBsat(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Primary Winding Turns Np</label>
                  <input type="number" value={gdtNp} onChange={(e) => setGdtNp(parseInt(e.target.value) || 1)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Inductance Factor Al (nH/T²)</label>
                  <input type="number" value={gdtAl} onChange={(e) => setGdtAl(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_gdt':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">GDT Volt-Second & Flux Density Results</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-350">
            {gdtRes && (
              <div className="space-y-4 text-xs font-mono">
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Peak Working Flux B_peak</span>
                    <span className="text-xs font-bold text-cyan-400">{(gdtRes.b_peak ?? 0).toFixed(3)} T</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Magnetizing Current I_mag</span>
                    <span className="text-xs font-bold text-emerald-400">{(gdtRes.i_mag_pk_ma ?? 0).toFixed(1)} mA</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Saturation Assessment</span>
                    <span className={`text-xs font-bold ${gdtRes.status_code === 'DANGER' ? 'text-red-400' : 'text-emerald-400'}`}>{gdtRes.status}</span>
                  </div>
                </div>

                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-[10px] leading-relaxed">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Peak Volt-Microsecond Product Et:</span>
                    <span className="text-slate-200 font-bold font-mono">{(gdtRes.et_product ?? 0).toFixed(2)} V·μs</span>
                  </div>
                  <div className="text-[9px] text-slate-400 leading-normal">
                    GDT Magnetic Design Equation:
                    <Latex math={"B_{max} = \\frac{V_{drv} \\cdot D_{max}}{N_{p} \\cdot A_{e} \\cdot f_{sw}}"} block />
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_gdt':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">GDT Core B-H Magnetization Loop Simulation</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {gdtRes && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[220px]">
                <ReactECharts
                  notMerge={true}
                  option={{
                    backgroundColor: 'transparent',
                    tooltip: { trigger: 'axis' },
                    grid: { left: '8%', right: '8%', top: '15%', bottom: '15%', containLabel: true },
                    xAxis: {
                      type: 'value',
                      name: 'Magnetic Field H (A/m)',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                      splitLine: { lineStyle: { color: '#1e293b' } }
                    },
                    yAxis: {
                      type: 'value',
                      name: 'Flux Density B (T)',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                      splitLine: { lineStyle: { color: '#1e293b' } }
                    },
                    series: [
                      {
                        name: 'B-H Loop',
                        type: 'line',
                        smooth: true,
                        data: Array.from({ length: 40 }, (_, idx) => {
                          const x = -300 + (idx * 600) / 40;
                          const saturation = gdtBsat;
                          const y = saturation * Math.tanh(x / 100);
                          return [x.toFixed(0), y.toFixed(3)];
                        }),
                        lineStyle: { color: '#8b5cf6', width: 2 },
                        markLine: {
                          symbol: 'none',
                          data: [
                            { yAxis: gdtBsat, lineStyle: { color: '#ef4444', type: 'dashed' } },
                            { yAxis: -gdtBsat, lineStyle: { color: '#ef4444', type: 'dashed' } },
                            { yAxis: gdtRes.b_peak, lineStyle: { color: '#06b6d4', width: 1.5 }, label: { formatter: 'B_peak' } }
                          ]
                        }
                      }
                    ]
                  }}
                  style={{ height: '100%', width: '100%' }}
                />
              </div>
            )}
          </div>
        </Card>
      );

    case 'input_cmp':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Device Comparison Operating Conditions</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Comparison Operating Point</span>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Bus Voltage Vbus (V)</label>
                  <input type="number" value={cmpVbus} onChange={(e) => setCmpVbus(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Load RMS Current (A)</label>
                  <input type="number" value={cmpIrms} onChange={(e) => setCmpIrms(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switch Current Isw (A)</label>
                  <input type="number" value={cmpIsw} onChange={(e) => setCmpIsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Duty Cycle D (%)</label>
                  <input type="number" value={cmpDuty} onChange={(e) => setCmpDuty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={cmpFsw} onChange={(e) => setCmpFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Gate Voltage Vgate (V)</label>
                  <input type="number" value={cmpVgate} onChange={(e) => setCmpVgate(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Reference Case Temp Tcase (°C)</label>
                  <input type="number" value={cmpTcase} onChange={(e) => setCmpTcase(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
              </div>
            </div>
            <Button onClick={addCandidate} className="w-full text-[10px] font-semibold bg-slate-900 border border-slate-800 hover:bg-slate-850 cursor-pointer"><Plus className="w-4 h-4 mr-1" /> Add Device Candidate</Button>
            <Button onClick={runCompare} className="w-full bg-blue-600 hover:bg-blue-500 font-bold text-xs cursor-pointer">Run Multi-Device Comparison</Button>
          </div>
        </Card>
      );

    case 'result_cmp':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Commercial Power Devices Specification & Loss Comparison</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            <div className="bg-slate-950 rounded-lg border border-slate-800 overflow-x-auto">
              <table className="w-full border-collapse text-left text-[10px]">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900 text-slate-400 font-semibold uppercase">
                    <th className="p-2">Part Number</th>
                    <th className="p-2">Technology</th>
                    <th className="p-2">Rds [mΩ]</th>
                    <th className="p-2">Qg [nC]</th>
                    <th className="p-2">Eon [μJ]</th>
                    <th className="p-2">Eoff [μJ]</th>
                    <th className="p-2">Rthjc</th>
                    <th className="p-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((c) => (
                    <tr key={c.id} className="border-b border-slate-900 hover:bg-slate-900/30">
                      <td className="p-2">
                        <input type="text" value={c.name} onChange={(e) => updateCandidate(c.id, 'name', e.target.value)} className="w-16 bg-slate-950 border border-slate-850 rounded px-1 py-0.5 text-slate-200 text-[10px]" />
                      </td>
                      <td className="p-2">
                        <select value={c.tech} onChange={(e) => updateCandidate(c.id, 'tech', e.target.value)} className="bg-slate-950 border border-slate-850 rounded px-1 py-0.5 text-slate-300 text-[9px]">
                          <option value="MOSFET">MOSFET</option>
                          <option value="SiC">SiC</option>
                          <option value="GaN">GaN</option>
                          <option value="IGBT">IGBT</option>
                        </select>
                      </td>
                      <td className="p-2">
                        <input type="number" value={c.rds} onChange={(e) => updateCandidate(c.id, 'rds', parseFloat(e.target.value) || 0)} className="w-12 bg-slate-950 border border-slate-850 rounded px-1 py-0.5 text-slate-200 text-[10px] text-right font-mono" />
                      </td>
                      <td className="p-2">
                        <input type="number" value={c.qg} onChange={(e) => updateCandidate(c.id, 'qg', parseFloat(e.target.value) || 0)} className="w-12 bg-slate-950 border border-slate-850 rounded px-1 py-0.5 text-slate-200 text-[10px] text-right font-mono" />
                      </td>
                      <td className="p-2">
                        <input type="number" value={c.eon} onChange={(e) => updateCandidate(c.id, 'eon', parseFloat(e.target.value) || 0)} className="w-12 bg-slate-950 border border-slate-850 rounded px-1 py-0.5 text-slate-200 text-[10px] text-right font-mono" />
                      </td>
                      <td className="p-2">
                        <input type="number" value={c.eoff} onChange={(e) => updateCandidate(c.id, 'eoff', parseFloat(e.target.value) || 0)} className="w-12 bg-slate-950 border border-slate-850 rounded px-1 py-0.5 text-slate-200 text-[10px] text-right font-mono" />
                      </td>
                      <td className="p-2">
                        <input type="number" step="0.1" value={c.rthjc} onChange={(e) => updateCandidate(c.id, 'rthjc', parseFloat(e.target.value) || 0)} className="w-12 bg-slate-950 border border-slate-850 rounded px-1 py-0.5 text-slate-200 text-[10px] text-right font-mono" />
                      </td>
                      <td className="p-2">
                        <Button size="icon" variant="ghost" className="h-5 w-5 text-rose-500 hover:bg-slate-900 cursor-pointer" onClick={() => removeCandidate(c.id)}><Trash2 className="w-3 h-3" /></Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {cmpSummaryHtml && (
              <div className="bg-slate-950/40 p-4 border border-slate-850 rounded-lg text-[10px] leading-relaxed text-slate-350" dangerouslySetInnerHTML={{ __html: cmpSummaryHtml }} />
            )}
          </div>
        </Card>
      );

    case 'chart_cmp':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Total Power Dissipation Comparison</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {candidates.some(c => c.p_total) && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[220px]">
                <ReactECharts
                  notMerge={true}
                  option={{
                    backgroundColor: 'transparent',
                    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                    grid: { left: '8%', right: '8%', top: '15%', bottom: '15%', containLabel: true },
                    xAxis: {
                      type: 'category',
                      data: candidates.map(c => c.name),
                      axisLabel: { color: '#94a3b8' }
                    },
                    yAxis: {
                      type: 'value',
                      name: 'Estimated Loss (W)',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                      splitLine: { lineStyle: { color: '#1e293b' } }
                    },
                    series: [
                      {
                        name: 'Conduction Loss P_cond',
                        type: 'bar',
                        stack: 'total',
                        data: candidates.map(c => (c.p_cond ?? 0).toFixed(2)),
                        itemStyle: { color: '#06b6d4' }
                      },
                      {
                        name: 'Switching Loss P_sw',
                        type: 'bar',
                        stack: 'total',
                        data: candidates.map(c => (c.p_sw ?? 0).toFixed(2)),
                        itemStyle: { color: '#f43f5e' }
                      },
                      {
                        name: 'Gate Drive Loss P_gate',
                        type: 'bar',
                        stack: 'total',
                        data: candidates.map(c => (c.p_gate ?? 0).toFixed(2)),
                        itemStyle: { color: '#10b981' }
                      }
                    ]
                  }}
                  style={{ height: '100%', width: '100%' }}
                />
              </div>
            )}
          </div>
        </Card>
      );

    default:
      return null;
  }
};
