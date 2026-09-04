import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from '../ui/Card';
import { CheckCircle2, LineChart, ShieldAlert } from 'lucide-react';
import type { ZthRcElement } from './types';

interface PhysicsCardsProps {
  // Loss
  swDeviceType: string;
  setSwDeviceType: (v: string) => void;
  swVact: number;
  setSwVact: (v: number) => void;
  swIact: number;
  setSwIact: (v: number) => void;
  swFsw: number;
  setSwFsw: (v: number) => void;
  swDuty: number;
  setSwDuty: (v: number) => void;
  swCondParam: number;
  setSwCondParam: (v: number) => void;
  swKtemp: number;
  setSwKtemp: (v: number) => void;
  swVtest: number;
  setSwVtest: (v: number) => void;
  swItest: number;
  setSwItest: (v: number) => void;
  swEon: number;
  setSwEon: (v: number) => void;
  swEoff: number;
  setSwEoff: (v: number) => void;
  swRes: any;
  getLossChartOption: () => any;

  // Deadtime
  dtVsd: number;
  setDtVsd: (v: number) => void;
  dtIload: number;
  setDtIload: (v: number) => void;
  dtFsw: number;
  setDtFsw: (v: number) => void;
  dtTon: number;
  setDtTon: (v: number) => void;
  dtToff: number;
  setDtToff: (v: number) => void;
  dtRes: any;

  // Miller
  milCrss: number;
  setMilCrss: (v: number) => void;
  milCiss: number;
  setMilCiss: (v: number) => void;
  milVth: number;
  setMilVth: (v: number) => void;
  milRgoff: number;
  setMilRgoff: (v: number) => void;
  milDvdt: number;
  setMilDvdt: (v: number) => void;
  milRes: any;
  getMillerChartOption: () => any;

  // Zth
  zthPower: number;
  setZthPower: (v: number) => void;
  zthTime: number;
  setZthTime: (v: number) => void;
  zthTinit: number;
  setZthTinit: (v: number) => void;
  zthRepetitive: boolean;
  setZthRepetitive: (v: boolean) => void;
  zthFreq: number;
  setZthFreq: (v: number) => void;
  zthDuty: number;
  setZthDuty: (v: number) => void;
  zthRcTable: ZthRcElement[];
  updateZthRcCell: (index: number, field: 'r' | 'tau', value: string) => void;
  zthRes: any;
  getZthChartOption: () => any;

  // Diode
  dvr: number;
  setDvr: (v: number) => void;
  dif: number;
  setDif: (v: number) => void;
  dfsw: number;
  setDfsw: (v: number) => void;
  dduty: number;
  setDduty: (v: number) => void;
  dvf: number;
  setDvf: (v: number) => void;
  dqrr: number;
  setDqrr: (v: number) => void;
  isGanDiode: boolean;
  setIsGanDiode: (v: boolean) => void;
  diodeRes: any;

  // SOA
  soaVds: number;
  setSoaVds: (v: number) => void;
  soaId: number;
  setSoaId: (v: number) => void;
  soaTime: number;
  setSoaTime: (v: number) => void;
  soaTc: number;
  setSoaTc: (v: number) => void;
  soaTjmax: number;
  setSoaTjmax: (v: number) => void;
  soaZth: number;
  setSoaZth: (v: number) => void;
  soaRes: any;
  getSoaChartOption: () => any;

  // Coupled
  cType: string;
  setCType: (v: string) => void;
  cVbus: number;
  setCVbus: (v: number) => void;
  cIload: number;
  setCIload: (v: number) => void;
  cFsw: number;
  setCFsw: (v: number) => void;
  cDuty: number;
  setCDuty: (v: number) => void;
  cCond25: number;
  setCCond25: (v: number) => void;
  cRjc: number;
  setCRjc: (v: number) => void;
  cRcs: number;
  setCRcs: (v: number) => void;
  cRsa: number;
  setCRsa: (v: number) => void;
  cAlpha: number;
  setCAlpha: (v: number) => void;
  coupledRes: any;
  getCoupledPieOption: () => any;

  Latex: React.FC<{ math: string; block?: boolean }>;
}

export const renderPhysicsCardContent = (key: string, props: PhysicsCardsProps): React.ReactNode => {
  const {
    swDeviceType, setSwDeviceType, swVact, setSwVact, swIact, setSwIact, swFsw, setSwFsw, swDuty, setSwDuty,
    swCondParam, setSwCondParam, swKtemp, setSwKtemp, swVtest, setSwVtest, swItest, setSwItest, swEon, setSwEon, swEoff, setSwEoff,
    swRes, getLossChartOption,
    dtVsd, setDtVsd, dtIload, setDtIload, dtFsw, setDtFsw, dtTon, setDtTon, dtToff, setDtToff, dtRes,
    milCrss, setMilCrss, milCiss, setMilCiss, milVth, setMilVth, milRgoff, setMilRgoff, milDvdt, setMilDvdt, milRes, getMillerChartOption,
    zthPower, setZthPower, zthTime, setZthTime, zthTinit, setZthTinit, zthRepetitive, setZthRepetitive, zthFreq, setZthFreq, zthDuty, setZthDuty,
    zthRcTable, updateZthRcCell, zthRes, getZthChartOption,
    dvr, setDvr, dif, setDif, dfsw, setDfsw, dduty, setDduty, dvf, setDvf, dqrr, setDqrr, isGanDiode, setIsGanDiode, diodeRes,
    soaVds, setSoaVds, soaId, setSoaId, soaTime, setSoaTime, soaTc, setSoaTc, soaTjmax, setSoaTjmax, soaZth, setSoaZth, soaRes, getSoaChartOption,
    cType, setCType, cVbus, setCVbus, cIload, setCIload, cFsw, setCFsw, cDuty, setCDuty, cCond25, setCCond25, cRjc, setCRjc, cRcs, setCRcs, cRsa, setCRsa, cAlpha, setCAlpha,
    coupledRes, getCoupledPieOption,
    Latex
  } = props;

  switch (key) {
    case 'input_loss':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Switching Loss Parameters</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <div className="flex justify-between items-center border-b border-slate-850 pb-1 mb-2">
                <span className="text-[10px] font-bold text-slate-300">Device Type & Operating Conditions</span>
                <select value={swDeviceType} onChange={(e) => setSwDeviceType(e.target.value)} className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[9px] text-slate-300 outline-none">
                  <option value="MOSFET">MOSFET</option>
                  <option value="IGBT">IGBT</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Turn-Off Voltage V_act (V)</label>
                  <input type="number" value={swVact} onChange={(e) => setSwVact(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">On-State Current I_act (A)</label>
                  <input type="number" value={swIact} onChange={(e) => setSwIact(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency f_sw (kHz)</label>
                  <input type="number" value={swFsw} onChange={(e) => setSwFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Duty Cycle D</label>
                  <input type="number" step="0.05" value={swDuty} onChange={(e) => setSwDuty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">{swDeviceType === 'MOSFET' ? 'On-Resistance Rds(on) (mΩ)' : 'Saturation Drop Vce(sat) (V)'}</label>
                  <input type="number" value={swCondParam} onChange={(e) => setSwCondParam(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                {swDeviceType === 'MOSFET' && (
                  <div className="flex flex-col gap-1">
                    <label className="text-[9px] text-slate-400">Temp Drift Coefficient k_temp</label>
                    <input type="number" step="0.1" value={swKtemp} onChange={(e) => setSwKtemp(parseFloat(e.target.value) || 1.4)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" placeholder="SiC 1.4 / Si 1.8" />
                  </div>
                )}
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Test Voltage V_test (V)</label>
                  <input type="number" value={swVtest} onChange={(e) => setSwVtest(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Test Current I_test (A)</label>
                  <input type="number" value={swItest} onChange={(e) => setSwItest(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Turn-On Energy E_on (μJ)</label>
                  <input type="number" value={swEon} onChange={(e) => setSwEon(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Turn-Off Energy E_off (μJ)</label>
                  <input type="number" value={swEoff} onChange={(e) => setSwEoff(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_loss':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Semiconductor Loss Calculation Results</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {swRes && (
              <div className="space-y-4">
                {swRes.p_tot >= 35.0 ? (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400">
                    <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-bold block">⚠️ Excessive Switch Loss Warning</span>
                      <span className="mt-1 block">Total switch power dissipation is {swRes.p_tot.toFixed(2)} W! To safeguard junction temperature, forced-air cooling (air velocity &gt; 2.0 m/s) or high-performance aluminum/copper IMS substrate with external heatsinking is strongly advised to prevent thermal breakdown.</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>✅ Normal Thermal Dissipation: Total device loss is {swRes.p_tot.toFixed(2)} W, well within standard natural convection and PCB copper thermal relief limits.</span>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Conduction Loss P_cond</span>
                    <span className="text-sm font-extrabold text-cyan-400">{(swRes.p_cond ?? 0).toFixed(2)} W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Switching Loss P_sw</span>
                    <span className="text-sm font-extrabold text-emerald-400">{(swRes.p_sw ?? 0).toFixed(2)} W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Total Switch Loss P_tot</span>
                    <span className="text-sm font-extrabold text-rose-400">{(swRes.p_tot ?? 0).toFixed(2)} W</span>
                  </div>
                </div>
                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-slate-350 text-[10px] leading-relaxed">
                  <div>Conduction Loss Share: <span className="text-cyan-400 font-bold">{((swRes.p_cond / (swRes.p_tot || 1)) * 100).toFixed(1)} %</span></div>
                  <div>Switching Loss Share: <span className="text-emerald-400 font-bold">{((swRes.p_sw / (swRes.p_tot || 1)) * 100).toFixed(1)} %</span></div>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_loss':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Switching Transition Overlap Loss Simulation</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {swRes && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[260px]">
                <ReactECharts notMerge={true} option={getLossChartOption()} style={{ height: '100%', width: '100%' }} />
              </div>
            )}
          </div>
        </Card>
      );

    case 'input_deadtime':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Synchronous Rectification Dead-Time Settings</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Body Diode Drop Vsd (V)</label>
                  <input type="number" value={dtVsd} onChange={(e) => setDtVsd(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Load Current I_load (A)</label>
                  <input type="number" value={dtIload} onChange={(e) => setDtIload(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={dtFsw} onChange={(e) => setDtFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Turn-On Dead Time Ton (ns)</label>
                  <input type="number" value={dtTon} onChange={(e) => setDtTon(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Turn-Off Dead Time Toff (ns)</label>
                  <input type="number" value={dtToff} onChange={(e) => setDtToff(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_deadtime':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Dead-Time Loss Calculation Results</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {dtRes && (
              <div className="space-y-4">
                {dtRes.p_out_ratio > 1.5 ? (
                  <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-start gap-2 text-xs text-yellow-400">
                    <ShieldAlert className="w-4.5 h-4.5 text-yellow-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-bold block">⚠️ Elevated Body Diode Conduction Loss</span>
                      <span className="mt-1 block">Body diode conduction loss accounts for {dtRes.p_out_ratio.toFixed(2)}%, which significantly reduces system efficiency and increases device thermal stress. Consider antiparalleling an ultra-low Vf Schottky barrier diode or tuning gate drive dead time to minimize freewheeling duration.</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>✅ Optimal Dead-Time Matching: Diode dead-time conduction accounts for only {dtRes.p_out_ratio.toFixed(2)}%, satisfying high-efficiency synchronous rectification guidelines.</span>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Dead-Time Loss P_dt</span>
                    <span className="text-sm font-extrabold text-rose-400">{(dtRes.p_deadtime ?? 0).toFixed(3)} W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Output Loss Share</span>
                    <span className="text-sm font-extrabold text-amber-400">{(dtRes.p_out_ratio ?? 0).toFixed(2)} %</span>
                  </div>
                </div>
                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-slate-350 text-[10px] leading-relaxed">
                  <div>Efficiency drop attributable to dead-time: <span className="text-red-400">{(dtRes.p_out_ratio || 0).toFixed(2)}%</span></div>
                  <div>Dead-Time Conduction Loss Formulation:
                    <Latex math={"P_{deadtime} = V_{sd} \\cdot I_{load} \\cdot (t_{on} + t_{off}) \\cdot f_{sw}"} block />
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_deadtime':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Synchronous Rectification Dead-Time Timing Diagram</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            <div className="border border-slate-800 rounded-lg p-3 bg-slate-950/20 flex flex-col items-center">
              <svg className="w-full max-w-2xl h-auto text-slate-350 mx-auto select-none" viewBox="0 0 340 160">
                <line x1="10" y1="30" x2="330" y2="30" stroke="#1e293b" />
                <text x="15" y="24" className="text-[10px] font-bold fill-slate-300">HS Gate Drive</text>
                <path d="M 40,30 L 120,30 L 120,60 L 220,60 L 220,30 L 300,30" fill="none" stroke="#38bdf8" strokeWidth="2" />
                <line x1="10" y1="90" x2="330" y2="90" stroke="#1e293b" />
                <text x="15" y="84" className="text-[10px] font-bold fill-slate-300">LS Gate Drive</text>
                <path d="M 40,90 L 140,90 L 140,120 L 200,120 L 200,90 L 300,90" fill="none" stroke="#10b981" strokeWidth="2" />
                <rect x="120" y="20" width="20" height="110" fill="rgba(245, 158, 11, 0.15)" stroke="rgba(245, 158, 11, 0.3)" strokeDasharray="2,2" />
                <rect x="200" y="20" width="20" height="110" fill="rgba(245, 158, 11, 0.15)" stroke="rgba(245, 158, 11, 0.3)" strokeDasharray="2,2" />
                <text x="130" y="146" className="text-[9px] font-bold fill-amber-400 font-mono" textAnchor="middle">Turn-On Ton</text>
                <text x="210" y="146" className="text-[9px] font-bold fill-amber-400 font-mono" textAnchor="middle">Turn-Off Toff</text>
                <text x="170" y="76" className="text-[9px] font-bold fill-slate-400" textAnchor="middle">Non-Overlap Dead Time</text>
              </svg>
            </div>
          </div>
        </Card>
      );

    case 'input_miller':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Miller Effect Parameter Inputs</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Feedback Capacitance Crss (pF)</label>
                  <input type="number" value={milCrss} onChange={(e) => setMilCrss(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Input Capacitance Ciss (pF)</label>
                  <input type="number" value={milCiss} onChange={(e) => setMilCiss(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Turn-On Threshold Vth (V)</label>
                  <input type="number" value={milVth} onChange={(e) => setMilVth(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Turn-Off Gate Resistor Rg_off (Ω)</label>
                  <input type="number" value={milRgoff} onChange={(e) => setMilRgoff(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Half-Bridge dV/dt (V/ns)</label>
                  <input type="number" value={milDvdt} onChange={(e) => setMilDvdt(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_miller':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Miller Turn-On Immunity Verification</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {milRes && (
              <div className="space-y-4">
                {milRes.status !== 'Safe' ? (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400">
                    <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-bold block">⚠️ Severe Miller Cross-Conduction Shoot-Through Risk</span>
                      <span className="mt-1 block">Half-bridge dV/dt transient induces a gate voltage of {milRes.vgs_induced.toFixed(2)} V, exceeding the threshold of {milVth} V! This will cause arm shoot-through and catastrophic destruction. Implement Active Miller Clamping (AMC), introduce negative gate bias (e.g. -5V), or reduce turn-off gate resistance Rg_off.</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>✅ Miller Immunity Verified: Induced gate voltage of {milRes.vgs_induced.toFixed(2)} V remains safely below threshold {milVth} V, ensuring zero shoot-through risk.</span>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Miller Current I_miller</span>
                    <span className="text-xs font-bold text-cyan-400">{milRes.i_miller?.toFixed(2)} A</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Induced Vgs</span>
                    <span className="text-xs font-bold text-amber-400">{milRes.vgs_induced?.toFixed(2)} V</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Status</span>
                    <span className={`text-xs font-bold ${milRes.status === 'Safe' ? 'text-emerald-400' : 'text-rose-400'}`}>{milRes.status}</span>
                  </div>
                </div>
                {milRes.advice && (
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-[10px] text-slate-300">
                    Advice: {milRes.advice}
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_miller':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Miller Transient Gate Voltage Response</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {milRes && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[260px]">
                <ReactECharts notMerge={true} option={getMillerChartOption()} style={{ height: '100%', width: '100%' }} />
              </div>
            )}
          </div>
        </Card>
      );

    case 'input_zth':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Transient Thermal Conditions Input</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <div className="flex justify-between items-center border-b border-slate-850 pb-1 mb-2">
                <span className="text-[10px] font-bold text-slate-350">Pulse & Temperature Profiles</span>
                <label className="flex items-center gap-1 text-[9px] text-cyan-400 cursor-pointer text-slate-400">
                  <input type="checkbox" checked={zthRepetitive} onChange={(e) => setZthRepetitive(e.target.checked)} className="rounded bg-slate-950 border-slate-800" />
                  Repetitive Pulse Train
                </label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Pulse Power P_pulse (W)</label>
                  <input type="number" value={zthPower} onChange={(e) => setZthPower(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Pulse Width ton (ms)</label>
                  <input type="number" value={zthTime} onChange={(e) => setZthTime(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Initial Case Temp T_init (°C)</label>
                  <input type="number" value={zthTinit} onChange={(e) => setZthTinit(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                {zthRepetitive && (
                  <>
                    <div className="flex flex-col gap-1">
                      <label className="text-[9px] text-slate-400">Repetition Frequency f (Hz)</label>
                      <input type="number" value={zthFreq} onChange={(e) => setZthFreq(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[9px] text-slate-400">Duty Cycle D (0~1)</label>
                      <input type="number" step="0.05" value={zthDuty} onChange={(e) => setZthDuty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                    </div>
                  </>
                )}
              </div>
            </div>
            <div className="border border-slate-800/80 rounded-lg p-3 bg-slate-900/10 space-y-2">
              <span className="text-[9px] font-bold text-slate-355 block border-b border-slate-800 pb-1">Foster 4th-Order RC Thermal Network Parameters</span>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                {zthRcTable.map((rc, idx) => (
                  <div key={idx} className="bg-slate-950/40 p-2 rounded border border-slate-900 grid grid-cols-2 gap-1.5">
                    <div>
                      <label className="text-[8px] text-slate-500">R{idx+1} (°C/W)</label>
                      <input type="number" step="0.01" value={rc.r} onChange={(e) => updateZthRcCell(idx, 'r', e.target.value)} className="w-full bg-slate-950 border border-slate-900 rounded p-1 text-[10px] text-slate-200 outline-none text-right font-mono" />
                    </div>
                    <div>
                      <label className="text-[8px] text-slate-500">τ{idx+1} (s)</label>
                      <input type="number" step="0.0001" value={rc.tau} onChange={(e) => updateZthRcCell(idx, 'tau', e.target.value)} className="w-full bg-slate-950 border border-slate-900 rounded p-1 text-[10px] text-slate-200 outline-none text-right font-mono" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_zth':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Transient Thermal Rise Calculation</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {zthRes && (
              <div className="space-y-4">
                {zthRes.tj_peak > 150.0 ? (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400">
                    <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-bold block">⚠️ Transient Over-Temperature Thermal Failure Warning</span>
                      <span className="mt-1 block">Peak junction temperature reaches {zthRes.tj_peak.toFixed(1)} °C, exceeding the 150 °C silicon safety limit! This presents severe risk of thermal runaway. Shorten pulse duration, reduce operating duty cycle, or select packages with lower thermal impedance.</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>✅ Safe Transient Junction Temperature: Peak junction temperature is {zthRes.tj_peak.toFixed(1)} °C, well below the 150 °C maximum silicon thermal limit.</span>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Equivalent Zth</span>
                    <span className="text-xs font-bold text-cyan-400">{(zthRes.zth_eff ?? 0).toFixed(4)} °C/W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Pulse Temp Rise ΔTj</span>
                    <span className="text-xs font-bold text-cyan-400">+{(zthRes.temp_rise ?? 0).toFixed(2)} °C</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Peak Tj</span>
                    <span className={`text-xs font-bold ${zthRes.tj_peak > 150 ? 'text-red-400 animate-pulse font-semibold' : 'text-emerald-400'}`}>{(zthRes.tj_peak ?? 0).toFixed(2)} °C</span>
                  </div>
                </div>
                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 text-[10px] text-slate-355 leading-relaxed">
                  <div>Total Network Thermal Resistance Rth_total: <span className="text-slate-200 font-semibold">{zthRcTable.reduce((acc, c) => acc + (c.r || 0), 0).toFixed(3)} °C/W</span></div>
                  <div>Transient Thermal Formulations:
                    <Latex math={"Z_{\\theta}(t) = \\sum_{i=1}^4 R_i \\cdot (1 - e^{-\\frac{t_{on}}{\\tau_i}})"} block />
                    <Latex math={"T_{j,peak} = T_{init} + P_{pulse} \\cdot Z_{\\theta}(t)"} block />
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_zth':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Foster RC Network Z_th(t) Transient Thermal Response</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {zthRes && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[360px]">
                <ReactECharts notMerge={true} option={getZthChartOption()} style={{ height: '100%', width: '100%' }} />
              </div>
            )}
          </div>
        </Card>
      );

    case 'input_diode':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Diode Reverse Recovery Parameters</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1">
                <span className="text-[10px] font-bold text-slate-300">Diode Physical Specifications</span>
                <label className="flex items-center gap-1.5 text-[9px] text-cyan-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isGanDiode}
                    onChange={(e) => {
                      setIsGanDiode(e.target.checked);
                      if (e.target.checked) setDqrr(0);
                    }}
                    className="rounded border-slate-800 bg-slate-950 text-cyan-500 focus:ring-0"
                  />
                  <span>GaN Zero Reverse Recovery (Qrr = 0)</span>
                </label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Reverse Breakdown Vr (V)</label>
                  <input type="number" value={dvr} onChange={(e) => setDvr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Forward Operating Current If (A)</label>
                  <input type="number" value={dif} onChange={(e) => setDif(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={dfsw} onChange={(e) => setDfsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Operating Duty D</label>
                  <input type="number" step="0.05" value={dduty} onChange={(e) => setDduty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Forward Voltage Vf (V)</label>
                  <input type="number" value={dvf} onChange={(e) => setDvf(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Reverse Recovery Charge Qrr (nC)</label>
                  <input type="number" value={isGanDiode ? 0 : dqrr} disabled={isGanDiode} onChange={(e) => setDqrr(parseFloat(e.target.value) || 0)} className={`bg-slate-950 border border-slate-800 rounded p-1.5 text-xs outline-none ${isGanDiode ? 'text-slate-500 opacity-60' : 'text-white'}`} />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_diode':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Diode Recovery Loss Calculation</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {diodeRes && (
              <div className="space-y-4">
                {(diodeRes.p_rr / (diodeRes.p_tot || 1.0)) > 0.4 ? (
                  <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-start gap-2 text-xs text-yellow-400">
                    <ShieldAlert className="w-4.5 h-4.5 text-yellow-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-bold block">⚠️ Reverse Recovery Dominates Thermal Dissipation</span>
                      <span className="mt-1 block">Reverse recovery accounts for {((diodeRes.p_rr / (diodeRes.p_tot || 1)) * 100).toFixed(1)}% of total diode dissipation! Consider adopting Fast Recovery Epitaxial Diodes (FRED) or Silicon Carbide (SiC) Schottky barrier diodes to eliminate reverse recovery losses.</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>✅ Moderate Recovery Loss: Reverse recovery accounts for {((diodeRes.p_rr / (diodeRes.p_tot || 1)) * 100).toFixed(1)}% of diode dissipation, well within normal thermal margins.</span>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Conduction Loss P_cond</span>
                    <span className="text-xs font-bold text-cyan-400">{(diodeRes.p_cond ?? 0).toFixed(2)} W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Recovery Loss P_rr</span>
                    <span className="text-xs font-bold text-cyan-400">{(diodeRes.p_rr ?? 0).toFixed(2)} W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Total Diode Loss P_tot</span>
                    <span className="text-xs font-bold text-rose-400">{(diodeRes.p_tot ?? 0).toFixed(2)} W</span>
                  </div>
                </div>
                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 text-[10px] text-slate-350 leading-relaxed space-y-1">
                  <div>Recovery Loss Share: <span className="text-rose-400 font-bold">{((diodeRes.p_rr / (diodeRes.p_tot || 1)) * 100).toFixed(1)} %</span></div>
                  <div>Diode Loss Equations:
                    <Latex math={"P_{cond} = I_{f} \\cdot V_{f} \\cdot D"} block />
                    <Latex math={"P_{rr} = Q_{rr} \\cdot V_{r} \\cdot f_{sw}"} block />
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_diode':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Diode Reverse Recovery Time-Domain Waveforms</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            <div className="border border-slate-800 rounded-lg p-3 bg-slate-950/20 flex flex-col items-center">
              <svg className="w-full max-w-2xl h-auto text-slate-350 mx-auto select-none" viewBox="0 0 340 130">
                <line x1="10" y1="50" x2="330" y2="50" stroke="#475569" strokeDasharray="3,3" />
                <path d="M 30,20 L 100,20 L 140,50 L 170,110 L 220,53 L 300,50" fill="none" stroke="#f43f5e" strokeWidth="2" />
                <text x="50" y="14" className="text-[10px] font-bold fill-rose-500">Forward Current If</text>
                <text x="165" y="124" className="text-[10px] font-bold fill-rose-500">Peak Reverse Current Irr</text>
                <line x1="140" y1="50" x2="140" y2="120" stroke="#f59e0b" strokeWidth="1" strokeDasharray="2,2" />
                <line x1="210" y1="50" x2="210" y2="120" stroke="#f59e0b" strokeWidth="1" strokeDasharray="2,2" />
                <path d="M 140,115 L 210,115" fill="none" stroke="#f59e0b" />
                <text x="175" y="110" className="text-[9px] font-bold fill-amber-400 font-mono" textAnchor="middle">Recovery trr</text>
              </svg>
            </div>
          </div>
        </Card>
      );

    case 'input_soa':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">SOA Short-Circuit Surge Input</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Surge Drain-Source Voltage Vds (V)</label>
                  <input type="number" value={soaVds} onChange={(e) => setSoaVds(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Surge Short-Circuit Current Id (A)</label>
                  <input type="number" value={soaId} onChange={(e) => setSoaId(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Pulse Duration t_pulse (ms)</label>
                  <input type="number" value={soaTime} onChange={(e) => setSoaTime(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Reference Case Temp Tc (°C)</label>
                  <input type="number" value={soaTc} onChange={(e) => setSoaTc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Max Allowable Junction Temp Tjmax (°C)</label>
                  <input type="number" value={soaTjmax} onChange={(e) => setSoaTjmax(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Transient Thermal Impedance Zth_pulse (°C/W)</label>
                  <input type="number" value={soaZth} onChange={(e) => setSoaZth(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_soa':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">SOA Short-Circuit Safety Assessment</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {soaRes && (
              <div className="space-y-4">
                {soaRes.status_code === 'FAIL' ? (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400">
                    <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-bold block">⚠️ SOA Boundary Violation & Spirito Instability Warning</span>
                      <span className="mt-1 block">Operating condition exceeds the Safe Operating Area (SOA) boundary with critical Spirito second-breakdown risk! Desat/short-circuit protection must trip within 1-2 μs to prevent destructive thermal runaway.</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>✅ SOA Boundary Safe: Pulse stress profile is strictly inside the Safe Operating Area with minimal Spirito instability risk.</span>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Surge Power P_pulse</span>
                    <span className="text-sm font-extrabold text-cyan-400">{soaRes.p_pulse?.toFixed(1)} W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Peak Temp Rise ΔTj</span>
                    <span className="text-sm font-extrabold text-amber-400">+{soaRes.temp_rise?.toFixed(2)} °C</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1 col-span-2">
                    <span className="text-[9px] text-slate-500 uppercase">Peak Junction Temp (Tj_peak) & Status</span>
                    <span className={`text-sm font-bold ${soaRes.status_code === 'FAIL' ? 'text-red-400 animate-pulse font-semibold' : 'text-emerald-400'}`}>
                      {soaRes.tj_peak?.toFixed(2)} °C ({soaRes.status})
                    </span>
                  </div>
                </div>
                <div className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 space-y-2 text-slate-350 text-[10px] leading-relaxed">
                  <div>Spirito Instability Risk: <span className={`font-bold ${soaRes.spirito_risk === 'High Risk' ? 'text-red-400' : 'text-emerald-400'}`}>{soaRes.spirito_risk}</span></div>
                  <div>Description: <span className="text-slate-200">{soaRes.spirito_msg}</span></div>
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_soa':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Safe Operating Area (SOA) Diagram</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {soaRes && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[260px]">
                <ReactECharts notMerge={true} option={getSoaChartOption()} style={{ height: '100%', width: '100%' }} />
              </div>
            )}
          </div>
        </Card>
      );

    case 'input_coupled':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Electro-Thermal Coupled System Parameters</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-slate-300">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <div className="flex justify-between items-center border-b border-slate-850 pb-1 mb-2">
                <span className="text-[10px] font-bold text-slate-300">Device Type & Operating Conditions</span>
                <select value={cType} onChange={(e) => setCType(e.target.value)} className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[9px] text-slate-300 outline-none">
                  <option value="MOSFET">MOSFET</option>
                  <option value="IGBT">IGBT</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Voltage V_act (V)</label>
                  <input type="number" value={cVbus} onChange={(e) => setCVbus(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Current I_act (A)</label>
                  <input type="number" value={cIload} onChange={(e) => setCIload(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Frequency f_sw (kHz)</label>
                  <input type="number" value={cFsw} onChange={(e) => setCFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Duty Cycle D</label>
                  <input type="number" step="0.05" value={cDuty} onChange={(e) => setCDuty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">25°C On-Resistance (mΩ)</label>
                  <input type="number" value={cCond25} onChange={(e) => setCCond25(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Junction-to-Case R_jc (°C/W)</label>
                  <input type="number" value={cRjc} onChange={(e) => setCRjc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Case-to-Heatsink R_cs (°C/W)</label>
                  <input type="number" value={cRcs} onChange={(e) => setCRcs(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Heatsink-to-Ambient R_sa (°C/W)</label>
                  <input type="number" value={cRsa} onChange={(e) => setCRsa(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Temp Coefficient α</label>
                  <input type="number" step="0.001" value={cAlpha} onChange={(e) => setCAlpha(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none text-right font-mono" />
                </div>
              </div>
            </div>
          </div>
        </Card>
      );

    case 'result_coupled':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <span className="text-xs font-bold text-white">Electro-Thermal Iteration Results</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono text-slate-350">
            {coupledRes && (
              <div className="space-y-4 font-semibold">
                {coupledRes.final_tj > 150.0 ? (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400">
                    <ShieldAlert className="w-4.5 h-4.5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-bold block">⚠️ Electro-Thermal Thermal Runaway Warning</span>
                      <span className="mt-1 block">After accounting for positive temperature coefficient drift, the electro-thermal converged junction temperature reaches {coupledRes.final_tj.toFixed(1)} °C, exceeding safe operating limits. Positive feedback between resistance and dissipation risks thermal runaway. Reduce Tamb, choose lower Rds(on) devices, or improve heatsinking.</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>✅ Electro-Thermal Equilibrium Converged: Stable junction temperature is {coupledRes.final_tj.toFixed(1)} °C, achieved after {coupledRes.iterations} iterations, satisfying long-term reliability criteria.</span>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Converged Junction Temp Tj</span>
                    <span className={`text-xs font-bold ${coupledRes.final_tj > 150 ? 'text-rose-500 animate-pulse font-semibold' : 'text-emerald-400'}`}>
                      {coupledRes.final_tj?.toFixed(2)} °C
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Coupled Loss P_loss</span>
                    <span className="text-xs font-bold text-emerald-400">{coupledRes.final_ploss?.toFixed(2)} W</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <span className="text-[9px] text-slate-500 uppercase">Iteration Steps</span>
                    <span className="text-xs font-bold text-amber-400">{coupledRes.iterations} steps</span>
                  </div>
                </div>
                <div className="bg-slate-950/40 p-2 rounded-lg border border-slate-800 text-[9px] flex flex-col gap-1 max-h-[100px] overflow-y-auto">
                  <span className="text-slate-400 font-semibold mb-0.5">Iteration Convergence History:</span>
                  {coupledRes.history?.map((h: any, idx: number) => (
                    <div key={idx} className="text-slate-400 font-mono text-[9px]">
                      Step {h.iteration}: Tj = {h.tj?.toFixed(1)}°C | Loss = {h.p_loss?.toFixed(2)}W
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      );

    case 'chart_coupled':
      return (
        <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
            <LineChart className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-white">Converged Loss Breakdown Pie Chart</span>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
            {coupledRes && (
              <div className="bg-slate-950 rounded-lg border border-slate-800 h-[240px]">
                <ReactECharts notMerge={true} option={getCoupledPieOption()} style={{ height: '100%', width: '100%' }} />
              </div>
            )}
          </div>
        </Card>
      );

    default:
      return null;
  }
};
