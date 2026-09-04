import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useTabHistoryState } from '../lib/tabHistory';
import { apiFetch } from '../lib/api';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
import { Button } from './ui/Button';
import { ArrowLeft } from 'lucide-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import type { MainTabType, DriverSubTabType, PhysicsSubTabType, Candidate, ZthRcElement } from './power_device/types';
import { renderDriverCardContent } from './power_device/PowerDeviceDriverCards';
import { renderPhysicsCardContent } from './power_device/PowerDevicePhysicsCards';

// LaTeX formula renderer
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

  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-slate-300 animate-fade-in" : "inline-block"} />;
};

export default function PowerDeviceSuitePanel({ onBack }: { onBack: () => void; setActiveModule?: any }) {
  const [activeMainTab, setActiveMainTab] = useTabHistoryState<MainTabType>('driver', 'activeMainTab');
  const [driverTab, setDriverTab] = useTabHistoryState<DriverSubTabType>('gate', 'driverTab');
  const [physicsTab, setPhysicsTab] = useTabHistoryState<PhysicsSubTabType>('loss', 'physicsTab');
  const [, setError] = useState<string | null>(null);

  const getLayoutConfig = () => {
    if (activeMainTab === 'driver') {
      switch (driverTab) {
        case 'gate':
          return {
            defaultCards: ['input_gate', 'result_gate', 'bom_gate'],
            defaultColumns: { input_gate: 'left', result_gate: 'right', bom_gate: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_gate: 4, result_gate: 8, bom_gate: 8 },
            defaultHeights: { input_gate: 550, result_gate: 460, bom_gate: 150 }
          };
        case 'desat':
          return {
            defaultCards: ['input_desat', 'result_desat', 'chart_desat'],
            defaultColumns: { input_desat: 'left', result_desat: 'right', chart_desat: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_desat: 4, result_desat: 8, chart_desat: 8 },
            defaultHeights: { input_desat: 500, result_desat: 450, chart_desat: 260 }
          };
        case 'bootstrap':
          return {
            defaultCards: ['input_boot', 'result_boot', 'bom_boot'],
            defaultColumns: { input_boot: 'left', result_boot: 'right', bom_boot: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_boot: 4, result_boot: 8, bom_boot: 8 },
            defaultHeights: { input_boot: 520, result_boot: 460, bom_boot: 220 }
          };
        case 'gdt':
          return {
            defaultCards: ['input_gdt', 'result_gdt', 'chart_gdt'],
            defaultColumns: { input_gdt: 'left', result_gdt: 'right', chart_gdt: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_gdt: 4, result_gdt: 8, chart_gdt: 8 },
            defaultHeights: { input_gdt: 500, result_gdt: 320, chart_gdt: 260 }
          };
        case 'compare':
          return {
            defaultCards: ['input_cmp', 'result_cmp', 'chart_cmp'],
            defaultColumns: { input_cmp: 'left', result_cmp: 'right', chart_cmp: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_cmp: 4, result_cmp: 8, chart_cmp: 8 },
            defaultHeights: { input_cmp: 500, result_cmp: 300, chart_cmp: 260 }
          };
      }
    } else if (activeMainTab === 'physics') {
      switch (physicsTab) {
        case 'loss':
          return {
            defaultCards: ['input_loss', 'result_loss', 'chart_loss'],
            defaultColumns: { input_loss: 'left', result_loss: 'right', chart_loss: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_loss: 4, result_loss: 8, chart_loss: 8 },
            defaultHeights: { input_loss: 580, result_loss: 200, chart_loss: 340 }
          };
        case 'deadtime':
          return {
            defaultCards: ['input_deadtime', 'result_deadtime', 'chart_deadtime'],
            defaultColumns: { input_deadtime: 'left', result_deadtime: 'right', chart_deadtime: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_deadtime: 4, result_deadtime: 8, chart_deadtime: 8 },
            defaultHeights: { input_deadtime: 400, result_deadtime: 185, chart_deadtime: 320 }
          };
        case 'miller':
          return {
            defaultCards: ['input_miller', 'result_miller', 'chart_miller'],
            defaultColumns: { input_miller: 'left', result_miller: 'right', chart_miller: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_miller: 4, result_miller: 8, chart_miller: 8 },
            defaultHeights: { input_miller: 420, result_miller: 220, chart_miller: 280 }
          };
        case 'zth':
          return {
            defaultCards: ['input_zth', 'result_zth', 'chart_zth'],
            defaultColumns: { input_zth: 'left', result_zth: 'right', chart_zth: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_zth: 4, result_zth: 8, chart_zth: 8 },
            defaultHeights: { input_zth: 650, result_zth: 180, chart_zth: 430 }
          };
        case 'diode':
          return {
            defaultCards: ['input_diode', 'result_diode', 'chart_diode'],
            defaultColumns: { input_diode: 'left', result_diode: 'right', chart_diode: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_diode: 4, result_diode: 8, chart_diode: 8 },
            defaultHeights: { input_diode: 420, result_diode: 180, chart_diode: 320 }
          };
        case 'soa':
          return {
            defaultCards: ['input_soa', 'result_soa', 'chart_soa'],
            defaultColumns: { input_soa: 'left', result_soa: 'right', chart_soa: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_soa: 4, result_soa: 8, chart_soa: 8 },
            defaultHeights: { input_soa: 420, result_soa: 220, chart_soa: 340 }
          };
        case 'coupled':
          return {
            defaultCards: ['input_coupled', 'result_coupled', 'chart_coupled'],
            defaultColumns: { input_coupled: 'left', result_coupled: 'right', chart_coupled: 'right' } as Record<string, 'left' | 'right'>,
            defaultSpans: { input_coupled: 4, result_coupled: 8, chart_coupled: 8 },
            defaultHeights: { input_coupled: 650, result_coupled: 200, chart_coupled: 430 }
          };
      }
    }
    return {
      defaultCards: ['input_gate', 'result_gate'],
      defaultColumns: { input_gate: 'left', result_gate: 'right' } as Record<string, 'left' | 'right'>,
      defaultSpans: { input_gate: 4, result_gate: 8 },
      defaultHeights: { input_gate: 550, result_gate: 460 }
    };
  };

  const layoutCfg = useMemo(() => getLayoutConfig(), [activeMainTab, driverTab, physicsTab]);

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
    handleDropOnColumn
  } = useDragDeckLayout({
    panelKey: 'layout_powerdevicesuitepanel_v3_' + activeMainTab + '_' + (activeMainTab === 'driver' ? driverTab : physicsTab),
    defaultCards: layoutCfg.defaultCards,
    defaultColumns: layoutCfg.defaultColumns,
    defaultSpans: layoutCfg.defaultSpans,
    defaultHeights: layoutCfg.defaultHeights
  });

  // ==========================================
  // State for Gate Driver
  // ==========================================
  const [drVcc, setDrVcc] = useState<number>(15);
  const [drVee, setDrVee] = useState<number>(0);
  const [drRgExt, setDrRgExt] = useState<number>(10);
  const [drRgInt, setDrRgInt] = useState<number>(2);
  const [drQg, setDrQg] = useState<number>(100);
  const [drFsw, setDrFsw] = useState<number>(50);
  const [drRes, setDrRes] = useState<any>(null);

  const calcGateDriver = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/driver', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vcc: drVcc,
          vee: drVee,
          rg_ext: drRgExt,
          rg_int: drRgInt,
          qg_nc: drQg,
          fsw_khz: drFsw
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setDrRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'driver' && driverTab === 'gate') calcGateDriver();
  }, [drVcc, drVee, drRgExt, drRgInt, drQg, drFsw, activeMainTab, driverTab]);

  // ==========================================
  // State for Desat Protection
  // ==========================================
  const [dsVth, setDsVth] = useState<number>(6.5);
  const [dsIchg, setDsIchg] = useState<number>(250);
  const [dsTblank, setDsTblank] = useState<number>(2.0);
  const [dsVf, setDsVf] = useState<number>(0.7);
  const [dsVceTrip, setDsVceTrip] = useState<number>(2.5);
  const [dsRes, setDsRes] = useState<any>(null);

  const calcDesat = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/desat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vth: dsVth,
          ichg_ua: dsIchg,
          tblank_us: dsTblank,
          vf: dsVf,
          vce_sat: dsVceTrip
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setDsRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'driver' && driverTab === 'desat') calcDesat();
  }, [dsVth, dsIchg, dsTblank, dsVf, dsVceTrip, activeMainTab, driverTab]);

  // ==========================================
  // State for Bootstrap
  // ==========================================
  const [btQg, setBtQg] = useState<number>(50);
  const [btFsw, setBtFsw] = useState<number>(100);
  const [btIq, setBtIq] = useState<number>(50);
  const [btDuty, setBtDuty] = useState<number>(95);
  const [btVdrop, setBtVdrop] = useState<number>(0.5);
  const [btQrr, setBtQrr] = useState<number>(20);
  const [btVcc, setBtVcc] = useState<number>(15);
  const [btVf, setBtVf] = useState<number>(1.0);
  const [btRes, setBtRes] = useState<any>(null);

  const calcBootstrap = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/bootstrap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          qg_nc: btQg,
          fsw_khz: btFsw,
          duty_pct: btDuty,
          i_leak_ua: btIq,
          qrr_nc: btQrr,
          vdrop: btVdrop,
          vcc: btVcc,
          vf_diode: btVf
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setBtRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'driver' && driverTab === 'bootstrap') calcBootstrap();
  }, [btQg, btFsw, btIq, btDuty, btVdrop, btQrr, btVcc, btVf, activeMainTab, driverTab]);

  // ==========================================
  // State for GDT
  // ==========================================
  const [gdtVcc, setGdtVcc] = useState<number>(15);
  const [gdtFsw, setGdtFsw] = useState<number>(100);
  const [gdtDuty, setGdtDuty] = useState<number>(0.5);
  const [gdtAe, setGdtAe] = useState<number>(25.0);
  const [gdtBsat, setGdtBsat] = useState<number>(0.3);
  const [gdtNp, setGdtNp] = useState<number>(15);
  const [gdtAl, setGdtAl] = useState<number>(1500);
  const [gdtRes, setGdtRes] = useState<any>(null);

  const calcGdt = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/gdt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_drv: gdtVcc,
          fsw_khz: gdtFsw,
          d_max: gdtDuty,
          ae_mm2: gdtAe,
          bsat_t: gdtBsat,
          np: gdtNp,
          al_nh: gdtAl
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setGdtRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'driver' && driverTab === 'gdt') calcGdt();
  }, [gdtVcc, gdtFsw, gdtDuty, gdtAe, gdtBsat, gdtNp, gdtAl, activeMainTab, driverTab]);

  // ==========================================
  // State for Device Comparison
  // ==========================================
  const [cmpVbus, setCmpVbus] = useState<number>(400);
  const [cmpIrms, setCmpIrms] = useState<number>(10);
  const [cmpIsw, setCmpIsw] = useState<number>(10);
  const [cmpDuty, setCmpDuty] = useState<number>(50);
  const [cmpFsw, setCmpFsw] = useState<number>(100);
  const [cmpVgate, setCmpVgate] = useState<number>(15);
  const [cmpTcase, setCmpTcase] = useState<number>(80);

  const [candidates, setCandidates] = useState<Candidate[]>([
    { id: 1, name: 'SiC_A', tech: 'SiC', vds: 650, id_max: 30, rds: 45, qg: 85, eon: 120, eoff: 80, eoss: 12, qrr: 0, rthjc: 0.7, tcase: '' },
    { id: 2, name: 'MOS_A', tech: 'MOSFET', vds: 650, id_max: 25, rds: 95, qg: 60, eon: 180, eoff: 120, eoss: 8, qrr: 80, rthjc: 1.0, tcase: '' },
    { id: 3, name: 'GaN_A', tech: 'GaN', vds: 650, id_max: 20, rds: 70, qg: 18, eon: 45, eoff: 35, eoss: 5, qrr: 0, rthjc: 1.5, tcase: '' }
  ]);
  const [cmpSummaryHtml, setCmpSummaryHtml] = useState<string>('');

  const addCandidate = () => {
    const newId = candidates.length > 0 ? Math.max(...candidates.map(c => c.id)) + 1 : 1;
    setCandidates([...candidates, {
      id: newId, name: `Dev_${newId}`, tech: 'MOSFET', vds: 650, id_max: 20, rds: 80, qg: 50, eon: 100, eoff: 80, eoss: 5, qrr: 0, rthjc: 1.0, tcase: ''
    }]);
  };

  const removeCandidate = (id: number) => {
    setCandidates(candidates.filter(c => c.id !== id));
  };

  const updateCandidate = (id: number, field: keyof Candidate, value: any) => {
    setCandidates(candidates.map(c => c.id === id ? { ...c, [field]: value } : c));
  };

  const runCompare = async () => {
    try {
      const updated = await Promise.all(candidates.map(async (c) => {
        const rds_r = c.rds * 1e-3;
        const qg_c = c.qg * 1e-9;
        const eon_j = c.eon * 1e-6;
        const eoff_j = c.eoff * 1e-6;
        const eoss_j = c.eoss * 1e-6;
        const qrr_c = c.qrr * 1e-9;
        const fsw_hz = cmpFsw * 1e3;

        const p_cond = Math.pow(cmpIrms, 2) * rds_r * (cmpDuty / 100.0);
        const p_sw = (eon_j + eoff_j + eoss_j) * fsw_hz;
        const p_qrr = qrr_c * cmpVbus * fsw_hz;
        const p_gate = qg_c * cmpVgate * fsw_hz;
        const p_total = p_cond + p_sw + p_qrr + p_gate;

        const effective_tcase = c.tcase !== '' ? parseFloat(c.tcase) : cmpTcase;
        const tj = effective_tcase + p_total * c.rthjc;

        const rg_fast = c.qg > 0 ? (cmpVgate * 30e-9) / qg_c : 0.0;
        const rg_slow = c.qg > 0 ? (cmpVgate * 100e-9) / qg_c : 0.0;

        return {
          ...c,
          p_total,
          p_cond,
          p_sw,
          p_qrr,
          p_gate,
          tj,
          result: `P=${p_total.toFixed(2)}W, Tj=${tj.toFixed(1)}℃, Rg=${rg_fast.toFixed(1)}~${rg_slow.toFixed(1)}Ω`
        };
      }));

      setCandidates(updated);

      const sorted = [...updated].sort((a, b) => (a.p_total || 0) - (b.p_total || 0));
      let html = `<div class="font-bold text-slate-200 mb-2">Candidate Loss & Thermal Ranking:</div>`;
      sorted.forEach((c) => {
        const isHot = (c.tj || 0) >= 125;
        const isWarm = (c.tj || 0) >= 100;
        const colorClass = isHot ? 'text-rose-400' : isWarm ? 'text-amber-400' : 'text-emerald-400';
        html += `<div class="text-sm py-1 border-b border-slate-800 flex justify-between">
          <span><strong class="text-slate-300 font-medium">${c.name} (${c.tech})</strong>: <span class="${colorClass}">${c.p_total?.toFixed(2)} W, Tj=${c.tj?.toFixed(1)}℃</span></span>
          <span class="text-xs text-slate-400">Cond: ${c.p_cond?.toFixed(2)}W | Sw: ${c.p_sw?.toFixed(2)}W | Qrr: ${c.p_qrr?.toFixed(2)}W | Gate: ${c.p_gate?.toFixed(2)}W</span>
        </div>`;
      });
      setCmpSummaryHtml(html);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'driver' && driverTab === 'compare') runCompare();
  }, [cmpVbus, cmpIrms, cmpIsw, cmpDuty, cmpFsw, cmpVgate, cmpTcase, activeMainTab, driverTab]);

  // ==========================================
  // State for MOSFET/IGBT Loss
  // ==========================================
  const [swDeviceType, setSwDeviceType] = useState<string>('MOSFET');
  const [swVact, setSwVact] = useState<number>(400);
  const [swIact, setSwIact] = useState<number>(10);
  const [swFsw, setSwFsw] = useState<number>(50);
  const [swDuty, setSwDuty] = useState<number>(0.5);
  const [swCondParam, setSwCondParam] = useState<number>(100);
  const [swKtemp, setSwKtemp] = useState<number>(1.4);
  const [swVtest, setSwVtest] = useState<number>(300);
  const [swItest, setSwItest] = useState<number>(10);
  const [swEon, setSwEon] = useState<number>(500);
  const [swEoff, setSwEoff] = useState<number>(300);
  const [swRes, setSwRes] = useState<any>(null);

  const calcSwLoss = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/loss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_type: swDeviceType,
          v_act: swVact,
          i_act: swIact,
          f_sw_hz: swFsw * 1000.0,
          duty: swDuty,
          cond_param: swCondParam,
          v_test: swVtest,
          i_test: swItest,
          e_on_uj: swEon,
          e_off_uj: swEoff
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setSwRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'physics' && physicsTab === 'loss') calcSwLoss();
  }, [swDeviceType, swVact, swIact, swFsw, swDuty, swCondParam, swVtest, swItest, swEon, swEoff, activeMainTab, physicsTab]);

  // ==========================================
  // State for Deadtime Loss
  // ==========================================
  const [dtVsd, setDtVsd] = useState<number>(2.5);
  const [dtIload, setDtIload] = useState<number>(10);
  const [dtFsw, setDtFsw] = useState<number>(100);
  const [dtTon, setDtTon] = useState<number>(50);
  const [dtToff, setDtToff] = useState<number>(50);
  const [dtRes, setDtRes] = useState<any>(null);

  const calcDeadtimeLoss = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/deadtime_loss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vsd: dtVsd,
          i_load: dtIload,
          f_sw_hz: dtFsw * 1000.0,
          t_dt_on_ns: dtTon,
          t_dt_off_ns: dtToff
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setDtRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'physics' && physicsTab === 'deadtime') calcDeadtimeLoss();
  }, [dtVsd, dtIload, dtFsw, dtTon, dtToff, activeMainTab, physicsTab]);

  // ==========================================
  // State for Miller Risk
  // ==========================================
  const [milCrss, setMilCrss] = useState<number>(100);
  const [milCiss, setMilCiss] = useState<number>(1000);
  const [milVth, setMilVth] = useState<number>(3.0);
  const [milRgoff, setMilRgoff] = useState<number>(2.0);
  const [milDvdt, setMilDvdt] = useState<number>(50);
  const [milRes, setMilRes] = useState<any>(null);

  const calcMiller = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/miller_risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          c_rss_pf: milCrss,
          c_iss_pf: milCiss,
          vth_min: milVth,
          rg_off: milRgoff,
          dv_dt_vns: milDvdt
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setMilRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'physics' && physicsTab === 'miller') calcMiller();
  }, [milCrss, milCiss, milVth, milRgoff, milDvdt, activeMainTab, physicsTab]);

  // ==========================================
  // State for Foster Zth
  // ==========================================
  const [zthPower, setZthPower] = useState<number>(1000);
  const [zthTime, setZthTime] = useState<number>(10);
  const [zthTinit, setZthTinit] = useState<number>(25);
  const [zthRepetitive, setZthRepetitive] = useState<boolean>(false);
  const [zthFreq, setZthFreq] = useState<number>(50);
  const [zthDuty, setZthDuty] = useState<number>(0.5);
  const [zthRes, setZthRes] = useState<any>(null);

  const [zthRcTable, setZthRcTable] = useState<ZthRcElement[]>([
    { r: 0.05, tau: 0.0001 },
    { r: 0.15, tau: 0.005 },
    { r: 0.40, tau: 0.05 },
    { r: 0.20, tau: 0.5 }
  ]);

  const calcZth = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/zth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pulse_power: zthPower,
          pulse_time_ms: zthTime,
          t_init: zthTinit,
          rc_elements: zthRcTable,
          repetitive: zthRepetitive,
          freq_hz: zthFreq,
          duty: zthDuty
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setZthRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'physics' && physicsTab === 'zth') calcZth();
  }, [zthPower, zthTime, zthTinit, zthRepetitive, zthFreq, zthDuty, zthRcTable, activeMainTab, physicsTab]);

  const updateZthRcCell = (index: number, field: 'r' | 'tau', value: string) => {
    const val = parseFloat(value);
    if (!isNaN(val)) {
      const updated = [...zthRcTable];
      updated[index][field] = val;
      setZthRcTable(updated);
    }
  };

  const getZthChartOption = () => {
    const timePoints: number[] = [];
    const zthValues: number[] = [];
    const dtValues: number[] = [];

    for (let i = -6; i <= 1; i += 0.1) {
      const t = Math.pow(10, i);
      timePoints.push(t);

      let z_sum = 0.0;
      zthRcTable.forEach((rc) => {
        if (rc.tau > 0) {
          z_sum += rc.r * (1.0 - Math.exp(-t / rc.tau));
        }
      });
      zthValues.push(z_sum);
      dtValues.push(z_sum * zthPower);
    }

    return {
      backgroundColor: 'transparent',
      title: {
        text: 'Transient Thermal Impedance Zth(t)',
        textStyle: { color: '#94a3b8', fontSize: 13, fontWeight: 'normal' },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const t = params[0].axisValue;
          const z = params[0].data;
          const dt = params[1].data;
          return `Time: ${parseFloat(t).toExponential(2)} s<br/>
                  Zth: ${z.toFixed(4)} ℃/W<br/>
                  ΔTj: ${dt.toFixed(1)} ℃`;
        }
      },
      legend: {
        data: ['Zth (℃/W)', 'Temp Rise ΔTj (℃)'],
        textStyle: { color: '#94a3b8' },
        bottom: 0
      },
      grid: { left: '8%', right: '8%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'log',
        name: 'Time (s)',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Zth (℃/W)',
          nameTextStyle: { color: '#34d399' },
          axisLabel: { color: '#34d399' },
          splitLine: { lineStyle: { color: '#334155' } }
        },
        {
          type: 'value',
          name: 'ΔTj (℃)',
          nameTextStyle: { color: '#fb7185' },
          axisLabel: { color: '#fb7185' },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Zth (℃/W)',
          type: 'line',
          data: zthValues,
          smooth: true,
          lineStyle: { color: '#34d399', width: 2 }
        },
        {
          name: 'Temp Rise ΔTj (℃)',
          type: 'line',
          yAxisIndex: 1,
          data: dtValues,
          smooth: true,
          lineStyle: { color: '#fb7185', width: 2, type: 'dashed' },
          showSymbol: false
        }
      ]
    };
  };

  // ==========================================
  // State for Diode Loss
  // ==========================================
  const [dvr, setDvr] = useState<number>(400);
  const [dif, setDif] = useState<number>(10);
  const [dfsw, setDfsw] = useState<number>(50);
  const [dduty, setDduty] = useState<number>(0.5);
  const [dvf, setDvf] = useState<number>(1.2);
  const [dqrr, setDqrr] = useState<number>(500);
  const [isGanDiode, setIsGanDiode] = useState<boolean>(false);
  const [diodeRes, setDiodeRes] = useState<any>(null);

  const calcDiode = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/diode_loss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vr: dvr,
          if_val: dif,
          fsw_hz: dfsw * 1000.0,
          duty: dduty,
          vf: dvf,
          qrr_nc: isGanDiode ? 0.0 : dqrr
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setDiodeRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'physics' && physicsTab === 'diode') calcDiode();
  }, [dvr, dif, dfsw, dduty, dvf, dqrr, isGanDiode, activeMainTab, physicsTab]);

  // ==========================================
  // State for SOA Check
  // ==========================================
  const [soaVds, setSoaVds] = useState<number>(24);
  const [soaId, setSoaId] = useState<number>(10);
  const [soaTime, setSoaTime] = useState<number>(1.0);
  const [soaTc, setSoaTc] = useState<number>(25);
  const [soaTjmax, setSoaTjmax] = useState<number>(175);
  const [soaZth, setSoaZth] = useState<number>(0.5);
  const [soaRes, setSoaRes] = useState<any>(null);

  const calcSoa = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/soa_safety', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vds: soaVds,
          id_curr: soaId,
          t_ms: soaTime,
          tc: soaTc,
          tj_max: soaTjmax,
          zth: soaZth
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setSoaRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'physics' && physicsTab === 'soa') calcSoa();
  }, [soaVds, soaId, soaTime, soaTc, soaTjmax, soaZth, activeMainTab, physicsTab]);

  // ==========================================
  // State for Coupled Loss-Thermal
  // ==========================================
  const [cType, setCType] = useState<string>('MOSFET');
  const [cVbus, setCVbus] = useState<number>(400);
  const [cIload, setCIload] = useState<number>(10);
  const [cFsw, setCFsw] = useState<number>(50);
  const [cDuty, setCDuty] = useState<number>(0.5);
  const [cCond25, setCCond25] = useState<number>(100);
  const [cVtest] = useState<number>(300);
  const [cItest] = useState<number>(10);
  const [cEon] = useState<number>(500);
  const [cEoff] = useState<number>(300);
  const [cRjc, setCRjc] = useState<number>(1.0);
  const [cRcs, setCRcs] = useState<number>(0.5);
  const [cRsa, setCRsa] = useState<number>(1.5);
  const [cTamb] = useState<number>(50);
  const [cAlpha, setCAlpha] = useState<number>(0.006);
  const [cMaxIter] = useState<number>(20);
  const [cTol] = useState<number>(0.1);
  const [coupledRes, setCoupledRes] = useState<any>(null);

  const runCoupledSolver = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_device/coupled_solver', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_type: cType,
          v_act: cVbus,
          i_act: cIload,
          f_sw_hz: cFsw * 1000.0,
          duty: cDuty,
          cond_param_25: cCond25,
          v_test: cVtest,
          i_test: cItest,
          e_on_uj: cEon,
          e_off_uj: cEoff,
          t_amb: cTamb,
          r_jc: cRjc,
          r_cs: cRcs,
          r_sa: cRsa,
          alpha: cAlpha,
          max_iter: cMaxIter,
          tolerance: cTol
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please verify parameter validity');
      }
      const data = await response.json();
      setCoupledRes(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeMainTab === 'physics' && physicsTab === 'coupled') runCoupledSolver();
  }, [cType, cVbus, cIload, cFsw, cDuty, cCond25, cVtest, cItest, cEon, cEoff, cRjc, cRcs, cRsa, cTamb, cAlpha, cMaxIter, cTol, activeMainTab, physicsTab]);

  const getCoupledPieOption = () => {
    if (!coupledRes) return {};
    const condLoss = coupledRes.final_ploss * 0.4;
    const swLoss = coupledRes.final_ploss * 0.6;
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      series: [
        {
          name: 'Loss Distribution',
          type: 'pie',
          radius: '55%',
          data: [
            { value: condLoss, name: 'Conduction Loss' },
            { value: swLoss, name: 'Switching Loss' }
          ],
          label: {
            color: '#94a3b8',
            formatter: '{b}: {d}%'
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  };

  const getLossChartOption = () => {
    if (!swRes) return {};
    const t_on = 50;
    const t_off = 80;
    const t_cond = 200;
    const data = [];
    const rdsOndV = swDeviceType === 'MOSFET' ? (swIact * swCondParam / 1000) : swCondParam;
    for (let t = 0; t <= 400; t += 5) {
      let v = swVact;
      let i = 0;
      if (t < t_on) {
        const pct = t / t_on;
        v = swVact * (1 - pct);
        i = swIact * pct;
      } else if (t < t_on + t_cond) {
        v = rdsOndV;
        i = swIact;
      } else if (t < t_on + t_cond + t_off) {
        const pct = (t - t_on - t_cond) / t_off;
        v = swVact * pct;
        i = swIact * (1 - pct);
      } else {
        v = swVact;
        i = 0;
      }
      const p = v * i;
      data.push([t, v, i, p]);
    }
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: ['Vds (V)', 'Id (A)', 'Power (W)'], textStyle: { color: '#94a3b8' } },
      grid: { left: '8%', right: '8%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: { type: 'value', name: 'Time (ns)', nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      yAxis: [
        { type: 'value', name: 'Voltage / Current', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
        { type: 'value', name: 'Power (W)', axisLabel: { color: '#94a3b8' }, splitLine: { show: false } }
      ],
      series: [
        { name: 'Vds (V)', type: 'line', smooth: true, data: data.map(d => [d[0], d[1]]), lineStyle: { color: '#38bdf8', width: 2 } },
        { name: 'Id (A)', type: 'line', smooth: true, data: data.map(d => [d[0], d[2]]), lineStyle: { color: '#10b981', width: 2 } },
        { name: 'Power (W)', type: 'line', smooth: true, yAxisIndex: 1, data: data.map(d => [d[0], d[3]]), lineStyle: { color: '#f43f5e', width: 1.5, type: 'dashed' }, areaStyle: { color: 'rgba(244, 63, 94, 0.1)' } }
      ]
    };
  };

  const getMillerChartOption = () => {
    if (!milRes) return {};
    const t_max = 50;
    const data = [];
    const v_induced = milRes.vgs_induced || 0.0;
    const v_th = milVth;
    for (let t = 0; t <= t_max; t++) {
      const peak_time = 10;
      let v = 0;
      if (t > 5) {
        const dt = t - 5;
        v = v_induced * (dt / peak_time) * Math.exp(1 - dt / peak_time);
      }
      data.push([t, v]);
    }
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: '8%', right: '8%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: { type: 'value', name: 'Time (ns)', nameTextStyle: { color: '#94a3b8' }, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      yAxis: { type: 'value', name: 'Vgs (V)', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      series: [
        {
          name: 'Induced Gate Voltage Vgs',
          type: 'line',
          smooth: true,
          data: data,
          lineStyle: { color: v_induced > v_th ? '#ef4444' : '#10b981', width: 2 },
          areaStyle: { color: v_induced > v_th ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)' },
          markLine: {
            symbol: 'none',
            label: { formatter: 'Vth Threshold' },
            data: [
              { yAxis: v_th, lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 } }
            ]
          }
        }
      ]
    };
  };

  const getSoaChartOption = () => {
    if (!soaRes) return {};
    const vds_vals = [10, 20, 50, 100, 200, 500, 1000];
    const dc_limit = vds_vals.map(v => [v, Math.min(100, 1500 / v)]);
    const pulse_1ms = vds_vals.map(v => [v, Math.min(300, 4500 / v)]);
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      grid: { left: '10%', right: '8%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: { type: 'log', name: 'Vds (V)', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      yAxis: { type: 'log', name: 'Id (A)', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      legend: { data: ['DC Limit', '1ms Pulse', 'Operating Point'], textStyle: { color: '#94a3b8' } },
      series: [
        { name: 'DC Limit', type: 'line', data: dc_limit, lineStyle: { color: '#475569', type: 'dashed' } },
        { name: '1ms Pulse', type: 'line', data: pulse_1ms, lineStyle: { color: '#38bdf8' } },
        {
          name: 'Operating Point',
          type: 'scatter',
          data: [[soaVds, soaId]],
          symbolSize: 12,
          itemStyle: { color: soaRes.status_code === 'FAIL' ? '#ef4444' : '#10b981' }
        }
      ]
    };
  };

  const renderCardContent = (key: string) => {
    if (activeMainTab === 'driver') {
      return renderDriverCardContent(key, {
        drVcc, setDrVcc, drVee, setDrVee, drRgExt, setDrRgExt, drRgInt, setDrRgInt, drQg, setDrQg, drFsw, setDrFsw, drRes,
        dsVth, setDsVth, dsIchg, setDsIchg, dsTblank, setDsTblank, dsVf, setDsVf, dsVceTrip, setDsVceTrip, dsRes,
        btQg, setBtQg, btFsw, setBtFsw, btIq, setBtIq, btDuty, setBtDuty, btVdrop, setBtVdrop, btQrr, setBtQrr, btVcc, setBtVcc, btVf, setBtVf, btRes,
        gdtVcc, setGdtVcc, gdtFsw, setGdtFsw, gdtDuty, setGdtDuty, gdtAe, setGdtAe, gdtBsat, setGdtBsat, gdtNp, setGdtNp, gdtAl, setGdtAl, gdtRes,
        cmpVbus, setCmpVbus, cmpIrms, setCmpIrms, cmpIsw, setCmpIsw, cmpDuty, setCmpDuty, cmpFsw, setCmpFsw, cmpVgate, setCmpVgate, cmpTcase, setCmpTcase,
        candidates, addCandidate, removeCandidate, updateCandidate, runCompare, cmpSummaryHtml,
        Latex
      });
    }
    return renderPhysicsCardContent(key, {
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
    });
  };

  return (
    <div className="h-full w-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      <div className="space-y-3 flex-shrink-0">
        {/* Top Banner */}
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
              <h1 className="text-base font-bold text-white tracking-tight">Power Semiconductor Loss & Thermal Sizing</h1>
              <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
                Evaluate MOSFET/IGBT semiconductor conduction and switching losses, driver sizing, Miller clamp, and thermal impedance.
              </p>
            </div>
          </div>
        </div>

        <Tabs value={activeMainTab} onValueChange={(val: any) => setActiveMainTab(val as MainTabType)} className="w-auto">
          <TabsList className="bg-[#020617] border border-slate-800 h-auto p-1 flex flex-wrap gap-1 justify-start">
            <TabsTrigger value="driver" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">
              Gate Drive & Protection Circuits
            </TabsTrigger>
            <TabsTrigger value="physics" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">
              Semiconductor Physics & Losses
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="flex flex-wrap gap-1 bg-[#020617] p-1 rounded-lg border border-slate-800/60">
          {activeMainTab === 'driver' ? (
            <>
              <button onClick={() => setDriverTab('gate')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${driverTab === 'gate' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Gate Drive Loss</button>
              <button onClick={() => setDriverTab('desat')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${driverTab === 'desat' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Desat Protection</button>
              <button onClick={() => setDriverTab('bootstrap')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${driverTab === 'bootstrap' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Bootstrap Circuit</button>
              <button onClick={() => setDriverTab('gdt')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${driverTab === 'gdt' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Gate Drive Transformer</button>
              <button onClick={() => setDriverTab('compare')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${driverTab === 'compare' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Device Comparison</button>
            </>
          ) : (
            <>
              <button onClick={() => setPhysicsTab('loss')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${physicsTab === 'loss' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>MOSFET/IGBT Loss</button>
              <button onClick={() => setPhysicsTab('deadtime')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${physicsTab === 'deadtime' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Synchronous Deadtime</button>
              <button onClick={() => setPhysicsTab('miller')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${physicsTab === 'miller' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Miller Effect Risk</button>
              <button onClick={() => setPhysicsTab('zth')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${physicsTab === 'zth' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Transient Thermal Zth</button>
              <button onClick={() => setPhysicsTab('diode')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${physicsTab === 'diode' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Diode Recovery</button>
              <button onClick={() => setPhysicsTab('soa')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${physicsTab === 'soa' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>SOA & Short Circuit</button>
              <button onClick={() => setPhysicsTab('coupled')} className={`px-3 py-1.5 rounded text-[10px] font-bold border transition-all cursor-pointer ${physicsTab === 'coupled' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-transparent border-transparent text-slate-400 hover:text-slate-200'}`}>Coupled Electro-Thermal</button>
            </>
          )}
        </div>
      </div>

      {/* DragDeck area container */}
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
            >
              {renderCardContent(key)}
            </DragCard>
          )}
          onDropOnColumn={handleDropOnColumn}
        />
      </div>
    </div>
  );
}
