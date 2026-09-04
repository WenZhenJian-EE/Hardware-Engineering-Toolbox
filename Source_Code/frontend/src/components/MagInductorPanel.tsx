import { useTabHistoryState } from '../lib/tabHistory';
import { apiFetch } from '../lib/api';
import React, { useState, useEffect, useRef } from 'react';
import { 
  ArrowLeft, 
  ShieldAlert, 
  FileCode
} from 'lucide-react';

import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Button } from './ui/Button';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
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

  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-slate-300" : "inline-block"} />;
};

type TabType = 'ccm' | 'gap' | 'air_core' | 'planar' | 'dc_bias' | 'litz' | 'coupled' | 'pfc' | 'inverter';

interface PowderCore {
  name: string;
  material: string;
  permeability: number;
  ae: number; // mm^2
  le: number; // mm
  ve: number; // mm^3
  al: number; // nH/N^2
}

const defaultPowderCores: PowderCore[] = [
  { name: "MS-090060-2", material: "Sendust", permeability: 60, ae: 33.1, le: 56.7, ve: 1877, al: 38 },
  { name: "MS-106060-2", material: "Sendust", permeability: 60, ae: 65.2, le: 81.2, ve: 5300, al: 75 },
  { name: "MS-130060-2", material: "Sendust", permeability: 60, ae: 65.4, le: 81.4, ve: 5320, al: 81 },
  { name: "MS-184060-2", material: "Sendust", permeability: 60, ae: 191.0, le: 107.0, ve: 20400, al: 202 },
  { name: "0077071A7", material: "Kool Mµ", permeability: 60, ae: 65.4, le: 81.4, ve: 5320, al: 81 },
  { name: "0077894A7", material: "Kool Mµ", permeability: 60, ae: 125.0, le: 95.8, ve: 12000, al: 120 },
  { name: "0058071A7", material: "High Flux", permeability: 60, ae: 65.4, le: 81.4, ve: 5320, al: 81 },
  { name: "0055071A7", material: "MPP", permeability: 60, ae: 65.4, le: 81.4, ve: 5320, al: 81 }
];

export default function MagInductorPanel({ onBack }: { onBack: () => void; setActiveModule?: (mod: string | null) => void }) {
  const [activeTab, setActiveTab] = useTabHistoryState<TabType>('ccm', 'activeTab');
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
    panelKey: 'layout_maginductorpanel_v3_' + activeTab,
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 820, results: 820 }
  });

  const [showFormulas, setShowFormulas] = useState<boolean>(true);
  const [hoveredPart, setHoveredPart] = useState<string | null>(null);

  const API_BASE = '/api/calculate/mag_inductor';

  // Tab 1: Buck CCM Design
  const [ccmVin, setCcmVin] = useState<number>(12.0);
  const [ccmVout, setCcmVout] = useState<number>(5.0);
  const [ccmIout, setCcmIout] = useState<number>(2.0);
  const [ccmFsw, setCcmFsw] = useState<number>(100.0);
  const [ccmK, setCcmK] = useState<number>(0.3);
  const [ccmAe, setCcmAe] = useState<number>(60.0);
  const [ccmBmax, setCcmBmax] = useState<number>(0.3);
  const [ccmJ, setCcmJ] = useState<number>(4.0);
  const [ccmKu, setCcmKu] = useState<number>(0.4);
  const [ccmRes, setCcmRes] = useState<any>(null);
  const [ccmError, setCcmError] = useState<string | null>(null);

  const fetchCcm = async () => {
    setCcmError(null);
    if (ccmVin <= ccmVout) {
      setCcmRes(null);
      setCcmError("In Buck mode, input voltage must exceed output voltage (Vin > Vout).");
      return;
    }
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/ccm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vin: ccmVin,
          vout: ccmVout,
          iout: ccmIout,
          fsw_hz: ccmFsw * 1000.0,
          k_ripple: ccmK
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setCcmRes(data);
    } catch (e: any) {
      setCcmError(e.message);
    }
  };

  // Tab 2: Core Air Gap & Fringing
  const [gapAe, setGapAe] = useState<number>(100.0);
  const [gapTurns, setGapTurns] = useState<number>(50);
  const [gapTargetL, setGapTargetL] = useState<number>(100.0);
  const [gapWindowH, setGapWindowH] = useState<number>(15.0);
  const [gapLe, setGapLe] = useState<number>(50.0);
  const [gapUr, setGapUr] = useState<number>(2000);
  const [gapMode, setGapMode] = useState<'L' | 'AL'>('L');
  const [gapRes, setGapRes] = useState<any>(null);
  const [gapError, setGapError] = useState<string | null>(null);

  const fetchGap = async () => {
    setGapError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/gap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ae_mm2: gapAe,
          turns: gapTurns,
          target_l_uh: gapTargetL,
          window_h_mm: gapWindowH,
          le_mm: gapLe,
          ur: gapUr,
          mode: gapMode
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setGapRes(data);
    } catch (e: any) {
      setGapError(e.message);
    }
  };

  // Tab 3: Air Core Inductor
  const [airDia, setAirDia] = useState<number>(10.0);
  const [airTurns, setAirTurns] = useState<number>(10);
  const [airWireD, setAirWireD] = useState<number>(0.5);
  const [airLength, setAirLength] = useState<number>(5.0);
  const [airCloseWound, setAirCloseWound] = useState<boolean>(false);
  const [airTargetL, setAirTargetL] = useState<number>(1.0);
  const [airResL, setAirResL] = useState<number | null>(null);
  const [airResTurns, setAirResTurns] = useState<number | null>(null);
  const [airError, setAirError] = useState<string | null>(null);

  useEffect(() => {
    if (airCloseWound) {
      setAirLength(parseFloat((airTurns * airWireD).toFixed(2)));
    }
  }, [airCloseWound, airTurns, airWireD]);

  const handleAirCalcL = async () => {
    setAirError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/air_core`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dia_mm: airDia,
          turns: airTurns,
          wire_d_mm: airWireD,
          length_mm: airLength,
          close_wound: airCloseWound
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setAirResL(data.l_uh);
      if (airCloseWound) {
        setAirLength(data.length_mm);
      }
    } catch (e: any) {
      setAirError(e.message);
    }
  };

  const handleAirCalcTurns = async () => {
    setAirError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/air_core_turns`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_l_uh: airTargetL,
          dia_mm: airDia,
          wire_d_mm: airWireD,
          length_mm: airCloseWound ? 0 : airLength,
          close_wound: airCloseWound
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setAirResTurns(data.turns);
      setAirTurns(parseFloat(data.turns.toFixed(1)));
      if (airCloseWound) {
        setAirLength(parseFloat((data.turns * airWireD).toFixed(2)));
      }
    } catch (e: any) {
      setAirError(e.message);
    }
  };

  // Tab 4: PCB Planar Inductor
  const [planarShape, setPlanarShape] = useState<string>('square');
  const [planarTurns, setPlanarTurns] = useState<number>(5);
  const [planarW, setPlanarW] = useState<number>(0.5);
  const [planarS, setPlanarS] = useState<number>(0.2);
  const [planarDin, setPlanarDin] = useState<number>(10.0);
  const [planarT, setPlanarT] = useState<number>(0.035);
  const [planarRes, setPlanarRes] = useState<any>(null);
  const [planarError, setPlanarError] = useState<string | null>(null);

  const fetchPlanar = async () => {
    setPlanarError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/planar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          shape: planarShape,
          turns: planarTurns,
          w_mm: planarW,
          s_mm: planarS,
          din_mm: planarDin,
          t_cu_mm: planarT
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setPlanarRes(data);
    } catch (e: any) {
      setPlanarError(e.message);
    }
  };

  // Tab 5: DC Bias Saturation Check
  const biasMaterials: Record<string, { a: number; b: number; c: number }> = {
    "Kool Mµ 60u (Ref)":  { a: 1.0, b: 0.0076, c: 1.85 },
    "Kool Mµ 26u (Ref)":  { a: 1.0, b: 0.0028, c: 1.95 },
    "High Flux 60u (Ref)": { a: 1.0, b: 0.0018, c: 2.15 },
    "XFlux 60u (Ref)":     { a: 1.0, b: 0.0006, c: 2.30 },
    "Custom":              { a: 1.0, b: 0.01,   c: 2.0  }
  };
  const [biasMat, setBiasMat] = useState<string>('Kool Mµ 60u (Ref)');
  const [biasA, setBiasA] = useState<number>(1.0);
  const [biasB, setBiasB] = useState<number>(0.0076);
  const [biasC, setBiasC] = useState<number>(1.85);
  const [biasL0, setBiasL0] = useState<number>(100.0);
  const [biasN] = useState<number>(40);
  const [biasLe] = useState<number>(50.0);
  const [biasImax, setBiasImax] = useState<number>(10.0);
  const [biasIdesign, setBiasIdesign] = useState<number>(5.0);
  const [biasRes, setBiasRes] = useState<any>(null);
  const [biasError, setBiasError] = useState<string | null>(null);

  useEffect(() => {
    if (biasMaterials[biasMat]) {
      const coeffs = biasMaterials[biasMat];
      setBiasA(coeffs.a);
      setBiasB(coeffs.b);
      setBiasC(coeffs.c);
    }
  }, [biasMat]);

  const fetchDcBias = async () => {
    setBiasError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/dc_bias`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          coefs: [biasA, biasB, biasC],
          l0_uh: biasL0,
          turns: biasN,
          le_mm: biasLe,
          i_max: biasImax,
          i_design: biasIdesign,
          steps: 50
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setBiasRes(data);
    } catch (e: any) {
      setBiasError(e.message);
    }
  };

  const getBiasChartOption = () => {
    if (!biasRes) return {};
    const { i_vals, l_vals, perm_pct_vals } = biasRes;
    
    return {
      backgroundColor: 'transparent',
      title: {
        text: `DC Bias Soft Saturation Curve (L0 = ${biasL0} uH)`,
        textStyle: { color: '#e2e8f0', fontSize: 13, fontWeight: 'bold' },
        left: 'center'
      },
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: {
        data: ['Inductance (uH)', 'Permeability Ratio (%)'],
        textStyle: { color: '#94a3b8', fontSize: 10 },
        bottom: 0
      },
      grid: { top: '15%', left: '10%', right: '10%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: i_vals.map((v: number) => v.toFixed(2)),
        name: 'Current (A)',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        axisLine: { lineStyle: { color: '#334155' } },
        splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Inductance L (uH)',
          nameTextStyle: { color: '#38bdf8' },
          axisLabel: { color: '#38bdf8' },
          axisLine: { lineStyle: { color: '#334155' } },
          splitLine: { lineStyle: { color: '#1e293b' } }
        },
        {
          type: 'value',
          name: 'Permeability %',
          min: 0,
          max: 110,
          nameTextStyle: { color: '#34d399' },
          axisLabel: { color: '#34d399' },
          axisLine: { lineStyle: { color: '#334155' } },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Inductance (uH)',
          type: 'line',
          data: l_vals,
          lineStyle: { color: '#38bdf8', width: 3 },
          itemStyle: { color: '#38bdf8' }
        },
        {
          name: 'Permeability Ratio (%)',
          type: 'line',
          yAxisIndex: 1,
          data: perm_pct_vals,
          lineStyle: { color: '#34d399', width: 2, type: 'dotted' },
          itemStyle: { color: '#34d399' }
        }
      ]
    };
  };

  // Tab 6: High Frequency Winding & Litz Wire
  const [litzFreq, setLitzFreq] = useState<number>(100.0);
  const [litzIrms, setLitzIrms] = useState<number>(5.0);
  const [litzLayers, setLitzLayers] = useState<number>(1.0);
  const [litzCondType, setLitzCondType] = useState<string>('Copper');
  const [litzRes, setLitzRes] = useState<any>(null);
  const [litzError, setLitzError] = useState<string | null>(null);

  const fetchLitz = async () => {
    setLitzError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/litz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          i_rms_a: litzIrms,
          f_hz: litzFreq * 1000.0,
          layers: litzLayers
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setLitzRes(data);
    } catch (e: any) {
      setLitzError(e.message);
    }
  };

  // Tab 7: Coupled Inductor Design
  const [coupVin, setCoupVin] = useState<number>(12.0);
  const [coupVout, setCoupVout] = useState<number>(5.0);
  const [coupIout, setCoupIout] = useState<number>(4.0);
  const [coupFsw, setCoupFsw] = useState<number>(100.0);
  const [coupLself] = useState<number>(10.0);
  const [coupCoeff] = useState<number>(-0.5);
  const [coupTurns, setCoupTurns] = useState<number>(15);
  const [coupAe, setCoupAe] = useState<number>(120.0);
  const [coupLe, setCoupLe] = useState<number>(56.0);
  const [coupUr, setCoupUr] = useState<number>(2000);
  const [coupRes, setCoupRes] = useState<any>(null);
  const [coupError, setCoupError] = useState<string | null>(null);

  const fetchCoupled = async () => {
    setCoupError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`${API_BASE}/coupled`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vin: coupVin,
          vout: coupVout,
          iout: coupIout,
          fsw_hz: coupFsw * 1000.0,
          L_self_uh: coupLself,
          coupled_coeff: coupCoeff,
          ae_mm2: coupAe,
          le_mm: coupLe,
          ur: coupUr,
          turns: coupTurns
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setCoupRes(data);
    } catch (e: any) {
      setCoupError(e.message);
    }
  };

  // Tab 8: PFC Boost Inductor Design
  const [pfcVacMin, setPfcVacMin] = useState<number>(176);
  const [pfcVbus, setPfcVbus] = useState<number>(400);
  const [pfcPout, setPfcPout] = useState<number>(3000);
  const [pfcEff, setPfcEff] = useState<number>(0.97);
  const [pfcFsw, setPfcFsw] = useState<number>(65);
  const [pfcK, setPfcK] = useState<number>(0.3);
  const [pfcIsCrm, setPfcIsCrm] = useState<boolean>(false);
  const [pfcRes, setPfcRes] = useState<any>(null);
  const [pfcError, setPfcError] = useState<string | null>(null);
  const [pfcAe, setPfcAe] = useState<number>(120.0);
  const [pfcBmax, setPfcBmax] = useState<number>(0.3);
  const [pfcLe, setPfcLe] = useState<number>(60.0);
  const [pfcUr, setPfcUr] = useState<number>(2000);

  const fetchPfc = async () => {
    setPfcError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`/api/calculate/power_topology/pfc_inductor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vac_min: pfcVacMin,
          vbus: pfcVbus,
          pout: pfcPout,
          eff: pfcEff,
          fsw_khz: pfcFsw,
          k_ripple: pfcK,
          is_crm: pfcIsCrm
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setPfcRes(data);
    } catch (e: any) {
      setPfcError(e.message);
    }
  };

  // Tab 9: Inverter Filter Inductor Design
  const [invVdc, setInvVdc] = useState<number>(400);
  const [invVoutRms, setInvVoutRms] = useState<number>(220);
  const [invIoutRms, setInvIoutRms] = useState<number>(13.6);
  const [invFsw, setInvFsw] = useState<number>(20);
  const [invFout, setInvFout] = useState<number>(50);
  const [invK, setInvK] = useState<number>(20);
  const [invIs3Ph, setInvIs3Ph] = useState<boolean>(false);
  const [invModMethod, setInvModMethod] = useState<string>('SPWM');
  const [invFCutoff, setInvFCutoff] = useState<number>(1.0);
  const [invLevelType, setInvLevelType] = useState<string>('2-Level');
  const [invRes, setInvRes] = useState<any>(null);
  const [invError, setInvError] = useState<string | null>(null);
  const [invAe, setInvAe] = useState<number>(150.0);
  const [invBmax, setInvBmax] = useState<number>(0.3);
  const [invLe, setInvLe] = useState<number>(75.0);
  const [invUr, setInvUr] = useState<number>(2000);

  const fetchInv = async () => {
    setInvError(null);
    try {
      const targetTab = activeTab;
      const response = await apiFetch(`/api/calculate/power_inverter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_3phase: invIs3Ph,
          vdc: invVdc,
          vac: invVoutRms,
          pout: invIoutRms * (invIs3Ph ? Math.sqrt(3) : 1) * invVoutRms,
          fout: invFout,
          fsw_khz: invFsw,
          lir_pct: invK,
          mod_method: invModMethod,
          f_cutoff_khz: invFCutoff,
          level_type: invLevelType
        }),
      });
      if (activeTabRef.current !== targetTab) return;
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      const data = await response.json();
      setInvRes(data);
    } catch (e: any) {
      setInvError(e.message);
    }
  };

  useEffect(() => {
    if (invIs3Ph) {
      setInvModMethod('SVPWM');
    } else {
      setInvModMethod('SPWM');
    }
  }, [invIs3Ph]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('target_mag_inductor_data');
      if (raw) {
        const data = JSON.parse(raw);
        if (data.tab) {
          setActiveTab(data.tab);
          if (data.tab === 'pfc') {
            if (data.params.vac_min !== undefined) setPfcVacMin(data.params.vac_min);
            if (data.params.vbus !== undefined) setPfcVbus(data.params.vbus);
            if (data.params.pout !== undefined) setPfcPout(data.params.pout);
            if (data.params.eff !== undefined) setPfcEff(data.params.eff);
            if (data.params.fsw_khz !== undefined) setPfcFsw(data.params.fsw_khz);
            if (data.params.k_ripple !== undefined) setPfcK(data.params.k_ripple);
            if (data.params.is_crm !== undefined) setPfcIsCrm(data.params.is_crm);
          } else if (data.tab === 'inverter') {
            if (data.params.vdc !== undefined) setInvVdc(data.params.vdc);
            if (data.params.vout_rms !== undefined) setInvVoutRms(data.params.vout_rms);
            if (data.params.iout_rms !== undefined) setInvIoutRms(data.params.iout_rms);
            if (data.params.fsw_khz !== undefined) setInvFsw(data.params.fsw_khz);
            if (data.params.f_out_hz !== undefined) setInvFout(data.params.f_out_hz);
            if (data.params.k_ripple !== undefined) setInvK(data.params.k_ripple);
            if (data.params.is_three_phase !== undefined) setInvIs3Ph(data.params.is_three_phase);
          }
        }
        localStorage.removeItem('target_mag_inductor_data');
      }
    } catch (e) {
      console.error("Failed to parse target mag inductor data", e);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (activeTab === 'ccm') fetchCcm();
      if (activeTab === 'gap') fetchGap();
      if (activeTab === 'air_core') handleAirCalcL();
      if (activeTab === 'planar') fetchPlanar();
      if (activeTab === 'dc_bias') fetchDcBias();
      if (activeTab === 'litz') fetchLitz();
      if (activeTab === 'coupled') fetchCoupled();
      if (activeTab === 'pfc') fetchPfc();
      if (activeTab === 'inverter') fetchInv();
    }, 500);
    return () => clearTimeout(timer);
  }, [
    activeTab,
    ccmVin, ccmVout, ccmIout, ccmFsw, ccmK, ccmAe, ccmBmax, ccmJ, ccmKu,
    gapAe, gapTurns, gapTargetL, gapWindowH, gapLe, gapUr, gapMode,
    airDia, airTurns, airWireD, airLength, airCloseWound,
    planarShape, planarTurns, planarW, planarS, planarDin, planarT,
    biasA, biasB, biasC, biasL0, biasN, biasLe, biasImax, biasIdesign,
    litzFreq, litzIrms, litzLayers,
    coupVin, coupVout, coupIout, coupFsw, coupLself, coupCoeff, coupTurns, coupAe, coupLe, coupUr,
    pfcVacMin, pfcVbus, pfcPout, pfcEff, pfcFsw, pfcK, pfcIsCrm, 
    invVdc, invVoutRms, invIoutRms, invFsw, invFout, invK, invIs3Ph, invModMethod, invFCutoff, invLevelType
  ]);

  const getRecommendedPowderCores = (targetL_uh: number, iDesign_a: number) => {
    const list = [];
    for (const core of defaultPowderCores) {
      const N = Math.ceil(Math.sqrt((targetL_uh * 1000) / core.al));
      const H = (0.4 * Math.PI * N * iDesign_a) / (core.le * 0.1);
      
      let a = 1.0, b = 0.0076, c = 1.85;
      if (core.material === 'High Flux') {
        b = 0.0018; c = 2.15;
      } else if (core.material === 'MPP') {
        b = 0.0006; c = 2.30;
      }
      
      const permPct = 100 / (a + b * Math.pow(H, c));
      const lActual = (N * N * core.al * (permPct / 100)) / 1000;
      const u_eff = core.permeability * (permPct / 100);
      const Bpk = (4 * Math.PI * 1e-7 * N * iDesign_a * u_eff) / (core.le * 1e-3);
      
      list.push({
        ...core,
        turns: N,
        h_oe: H,
        perm_pct: permPct,
        l_actual: lActual,
        b_pk: Bpk,
        ok: Bpk < 0.35 && permPct >= 50
      });
    }
    return list.sort((x, y) => y.perm_pct - x.perm_pct);
  };

  const renderInput = () => {
    switch (activeTab) {
      case 'ccm':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Topology & Operating Stresses</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Input Voltage Vin (V)</label>
                  <input type="number" value={ccmVin} onChange={(e) => setCcmVin(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Output Voltage Vout (V)</label>
                  <input type="number" value={ccmVout} onChange={(e) => setCcmVout(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Output Current Iout (A)</label>
                  <input type="number" value={ccmIout} onChange={(e) => setCcmIout(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={ccmFsw} onChange={(e) => setCcmFsw(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[9px] text-slate-400">Ripple Ratio K_ripple (ΔIL/Iout)</label>
                <input type="number" step="0.05" value={ccmK} onChange={(e) => setCcmK(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
              </div>
            </div>

            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Core Physical Design Targets</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Effective Area Ae (mm²)</label>
                  <input type="number" value={ccmAe} onChange={(e) => setCcmAe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Max Flux Density Bmax (T)</label>
                  <input type="number" step="0.05" value={ccmBmax} onChange={(e) => setCcmBmax(Math.max(0.05, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Current Density J (A/mm²)</label>
                  <input type="number" value={ccmJ} onChange={(e) => setCcmJ(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Window Fill Factor Ku</label>
                  <input type="number" step="0.05" value={ccmKu} onChange={(e) => setCcmKu(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
              </div>
            </div>
            <Button onClick={fetchCcm} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute CCM Sizing</Button>
          </div>
        );

      case 'gap':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Air Gap Physical Parameters</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Calculation Mode</label>
                  <select value={gapMode} onChange={(e) => setGapMode(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500">
                    <option value="L">Solve Air Gap from Target Inductance</option>
                    <option value="AL">Solve Air Gap from AL Factor (nH/N²)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Effective Area Ae (mm²)</label>
                  <input type="number" value={gapAe} onChange={(e) => setGapAe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Winding Turns N</label>
                  <input type="number" value={gapTurns} onChange={(e) => setGapTurns(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">{gapMode === 'L' ? 'Target Inductance L (uH)' : 'Target AL Factor (nH/N²)'}</label>
                  <input type="number" value={gapTargetL} onChange={(e) => setGapTargetL(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Window Height G (mm)</label>
                  <input type="number" value={gapWindowH} onChange={(e) => setGapWindowH(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Magnetic Path Length le (mm)</label>
                  <input type="number" value={gapLe} onChange={(e) => setGapLe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Relative Permeability ur</label>
                  <input type="number" value={gapUr} onChange={(e) => setGapUr(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none focus:border-cyan-500" />
                </div>
              </div>
            </div>
            <Button onClick={fetchGap} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute Air Gap Sizing</Button>
          </div>
        );

      case 'air_core':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Air Core Coil Geometry</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Coil Inner Diameter Din (mm)</label>
                  <input type="number" value={airDia} onChange={(e) => setAirDia(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Coil Turns N</label>
                  <input type="number" value={airTurns} onChange={(e) => setAirTurns(Math.max(1, parseFloat(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Wire Diameter d (mm)</label>
                  <input type="number" step="0.05" value={airWireD} onChange={(e) => setAirWireD(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Winding Length L (mm)</label>
                  <input type="number" disabled={airCloseWound} value={airLength} onChange={(e) => setAirLength(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none disabled:opacity-50" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="airCloseWound" checked={airCloseWound} onChange={(e) => setAirCloseWound(e.target.checked)} className="accent-cyan-500 cursor-pointer" />
                <label htmlFor="airCloseWound" className="text-xs text-slate-350 cursor-pointer">Close-Wound (Length = Turns × Wire Diameter)</label>
              </div>
              <div className="flex flex-col gap-1 pt-2 border-t border-slate-850">
                <label className="text-[9px] text-slate-400">Target Inductance for Inverse Solve (uH)</label>
                <input type="number" value={airTargetL} onChange={(e) => setAirTargetL(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button onClick={handleAirCalcL} className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-[10px] py-2">Calculate Inductance</Button>
              <Button onClick={handleAirCalcTurns} className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-[10px] py-2">Solve Required Turns</Button>
            </div>
          </div>
        );

      case 'planar':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">PCB Planar Spiral Specs</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Trace Geometry</label>
                  <select value={planarShape} onChange={(e) => setPlanarShape(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                    <option value="square">Square</option>
                    <option value="hexagonal">Hexagonal</option>
                    <option value="octagonal">Octagonal</option>
                    <option value="circular">Circular</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Trace Turns N</label>
                  <input type="number" value={planarTurns} onChange={(e) => setPlanarTurns(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Trace Width w (mm)</label>
                  <input type="number" step="0.05" value={planarW} onChange={(e) => setPlanarW(Math.max(0.05, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Spacing s (mm)</label>
                  <input type="number" step="0.05" value={planarS} onChange={(e) => setPlanarS(Math.max(0.05, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Inner Diameter Din (mm)</label>
                  <input type="number" value={planarDin} onChange={(e) => setPlanarDin(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Copper Thickness t (mm)</label>
                  <input type="number" step="0.005" value={planarT} onChange={(e) => setPlanarT(Math.max(0.005, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
            <Button onClick={fetchPlanar} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute Planar Inductor Sizing</Button>
          </div>
        );

      case 'dc_bias':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">DC Bias Conditions</span>
              <div className="flex flex-col gap-1">
                <label className="text-[9px] text-slate-400">Powder Core Material Grade</label>
                <select value={biasMat} onChange={(e) => setBiasMat(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                  {Object.keys(biasMaterials).map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Zero-Bias L0 (uH)</label>
                  <input type="number" value={biasL0} onChange={(e) => setBiasL0(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Design Current Id (A)</label>
                  <input type="number" value={biasIdesign} onChange={(e) => setBiasIdesign(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Max Current Imax (A)</label>
                  <input type="number" value={biasImax} onChange={(e) => setBiasImax(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
            <Button onClick={fetchDcBias} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute DC Bias Sizing</Button>
          </div>
        );

      case 'litz':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">High-Frequency Litz Parameters</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Operating Frequency fsw (kHz)</label>
                  <input type="number" value={litzFreq} onChange={(e) => setLitzFreq(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">RMS Current Irms (A)</label>
                  <input type="number" value={litzIrms} onChange={(e) => setLitzIrms(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Winding Layers</label>
                  <input type="number" value={litzLayers} onChange={(e) => setLitzLayers(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Conductor Material</label>
                  <select value={litzCondType} onChange={(e) => setLitzCondType(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                    <option value="Copper">Solid Copper</option>
                    <option value="Silver">Silver-Plated Copper</option>
                    <option value="Aluminum">Aluminum</option>
                  </select>
                </div>
              </div>
            </div>
            <Button onClick={fetchLitz} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute AC Resistance Sizing</Button>
          </div>
        );

      case 'coupled':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Coupled Topology & Physical Specs</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Input Voltage Vin (V)</label>
                  <input type="number" value={coupVin} onChange={(e) => setCoupVin(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Output Voltage Vout (V)</label>
                  <input type="number" value={coupVout} onChange={(e) => setCoupVout(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Total Output Load (A)</label>
                  <input type="number" value={coupIout} onChange={(e) => setCoupIout(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={coupFsw} onChange={(e) => setCoupFsw(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Winding Turns N</label>
                  <input type="number" value={coupTurns} onChange={(e) => setCoupTurns(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Core Area Ae (mm²)</label>
                  <input type="number" value={coupAe} onChange={(e) => setCoupAe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Mean Magnetic Path le (mm)</label>
                  <input type="number" value={coupLe} onChange={(e) => setCoupLe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Relative Permeability ur</label>
                  <input type="number" value={coupUr} onChange={(e) => setCoupUr(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
            <Button onClick={fetchCoupled} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute Coupled Inductor Sizing</Button>
          </div>
        );

      case 'pfc':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">PFC Electrical Parameters</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Min Grid Vac_min (V)</label>
                  <input type="number" value={pfcVacMin} onChange={(e) => setPfcVacMin(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">DC Bus Vbus (V)</label>
                  <input type="number" value={pfcVbus} onChange={(e) => setPfcVbus(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Output Power Pout (W)</label>
                  <input type="number" value={pfcPout} onChange={(e) => setPfcPout(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Estimated Efficiency Eff [0~1]</label>
                  <input type="number" step="0.01" value={pfcEff} onChange={(e) => setPfcEff(Math.min(1.0, Math.max(0.1, parseFloat(e.target.value) || 0.97)))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={pfcFsw} onChange={(e) => setPfcFsw(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Ripple Ratio K_ripple</label>
                  <input type="number" step="0.05" value={pfcK} onChange={(e) => setPfcK(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="pfcIsCrm" checked={pfcIsCrm} onChange={(e) => setPfcIsCrm(e.target.checked)} className="accent-cyan-500 cursor-pointer" />
                <label htmlFor="pfcIsCrm" className="text-xs text-slate-350 cursor-pointer">CRM Critical Conduction Mode (LIR forced to 2.0)</label>
              </div>
            </div>

            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Core Geometry Targets</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Core Area Ae (mm²)</label>
                  <input type="number" value={pfcAe} onChange={(e) => setPfcAe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Max Flux Density Bmax (T)</label>
                  <input type="number" step="0.05" value={pfcBmax} onChange={(e) => setPfcBmax(Math.max(0.05, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Mean Path Length le (mm)</label>
                  <input type="number" value={pfcLe} onChange={(e) => setPfcLe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Relative Permeability ur</label>
                  <input type="number" value={pfcUr} onChange={(e) => setPfcUr(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
            <Button onClick={fetchPfc} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute PFC Inductor Sizing</Button>
          </div>
        );

      case 'inverter':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Inverter Operating Stresses</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">DC Bus Vdc (V)</label>
                  <input type="number" value={invVdc} onChange={(e) => setInvVdc(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Output Voltage RMS (V)</label>
                  <input type="number" value={invVoutRms} onChange={(e) => setInvVoutRms(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Output Current RMS (A)</label>
                  <input type="number" value={invIoutRms} onChange={(e) => setInvIoutRms(Math.max(0.01, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Switching Frequency (kHz)</label>
                  <input type="number" value={invFsw} onChange={(e) => setInvFsw(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Fundamental Frequency f0 (Hz)</label>
                  <input type="number" value={invFout} onChange={(e) => setInvFout(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Inductor Ripple Ratio LIR (%)</label>
                  <input type="number" value={invK} onChange={(e) => setInvK(Math.max(1.0, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Modulation Scheme</label>
                  <select value={invModMethod} onChange={(e) => setInvModMethod(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                    <option value="SVPWM">Three-Phase Space Vector (SVPWM)</option>
                    <option value="SPWM">Sinusoidal PWM (SPWM)</option>
                  </select>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="invIs3Ph" checked={invIs3Ph} onChange={(e) => setInvIs3Ph(e.target.checked)} className="accent-cyan-500 cursor-pointer" />
                <label htmlFor="invIs3Ph" className="text-xs text-slate-350 cursor-pointer">Three-Phase System Architecture</label>
              </div>
            </div>

            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Magnetic & Geometric Limits</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Topology Level Architecture</label>
                  <select value={invLevelType} onChange={(e) => setInvLevelType(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                    <option value="2-Level">2-Level Inverter</option>
                    <option value="T-Type">3-Level T-Type</option>
                    <option value="I-Type">3-Level I-Type</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Effective Area Ae (mm²)</label>
                  <input type="number" value={invAe} onChange={(e) => setInvAe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Saturation Flux Density Bmax (T)</label>
                  <input type="number" step="0.05" value={invBmax} onChange={(e) => setInvBmax(Math.max(0.05, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Mean Path Length le (mm)</label>
                  <input type="number" value={invLe} onChange={(e) => setInvLe(Math.max(1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Relative Permeability ur</label>
                  <input type="number" value={invUr} onChange={(e) => setInvUr(Math.max(1, parseInt(e.target.value) || 1))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">LC Cutoff Frequency fc (kHz)</label>
                  <input type="number" step="0.1" value={invFCutoff} onChange={(e) => setInvFCutoff(Math.max(0.1, parseFloat(e.target.value) || 0))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
            <Button onClick={fetchInv} className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold text-xs">Execute Inverter Inductor Sizing</Button>
          </div>
        );

      default:
        return null;
    }
  };

  const renderResults = () => {
    return (
      <div className="space-y-6">
        {showFormulas && (
          <Card className="border-slate-800 bg-[#0b0f19]/60 border-l-4 border-l-cyan-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <FileCode className="w-4 h-4 text-cyan-400" />
                Design Equations & Mathematical Formulations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-slate-950/60 p-4 rounded border border-slate-900 text-xs">
                {activeTab === 'ccm' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Buck CCM Filter Inductor Formulation:</div>
                    <Latex math={"L_{min} = \\frac{V_{out}(V_{in} - V_{out})}{V_{in} \\cdot f_{sw} \\cdot \\Delta I_L}"} block />
                    <div className="mt-3 mb-2 text-xs font-semibold text-slate-300">Inductor Current RMS:</div>
                    <Latex math={"I_{rms} = \\sqrt{I_{out}^2 + \\frac{\\Delta I_L^2}{12}}"} block />
                    <div className="mt-3 text-[10px] text-slate-400">
                      Core Area Product (AP) Method Formulation:
                      <Latex math={"A_p = A_e \\cdot A_w = \\frac{L \\cdot I_{pk} \\cdot I_{rms}}{B_{max} \\cdot J \\cdot K_u}"} block />
                    </div>
                  </>
                )}
                {activeTab === 'gap' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Core Air Gap Calculation:</div>
                    <Latex math={"l_g = \\frac{\\mu_0 A_e N^2}{L} - \\frac{l_e}{\\mu_r}"} block />
                    <div className="mt-3 mb-2 text-xs font-semibold text-slate-300">Fringing Factor F:</div>
                    <Latex math={"F = 1 + \\frac{l_g}{\\sqrt{A_e}} \\ln\\left(\\frac{2G}{l_g}\\right)"} block />
                  </>
                )}
                {activeTab === 'air_core' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Single-Layer Solenoid (Wheeler Formula):</div>
                    <Latex math={"L (\\mu H) = \\frac{d^2 N^2}{18d + 40l} \\quad (d, l \\text{ in inches})"} block />
                  </>
                )}
                {activeTab === 'planar' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Planar Spiral Inductance (Current Sheet Approx):</div>
                    <Latex math={"L \\approx \\frac{\\mu_0 N^2 d_{avg} c_1}{2} \\left[ \\ln\\left(\\frac{c_2}{\\rho}\\right) + c_3 \\rho + c_4 \\rho^2 \\right]"} block />
                  </>
                )}
                {activeTab === 'dc_bias' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Permeability DC Bias Roll-Off:</div>
                    <Latex math={"\\% \\mu = \\frac{100}{a + b \\cdot H^c} \\quad (H = \\frac{0.4 \\pi N I_{dc}}{l_e})"} block />
                  </>
                )}
                {activeTab === 'litz' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Dowell HF AC Resistance Factor Fr:</div>
                    <Latex math={"F_R = \\xi \\left[ \\frac{\\sinh(2\\xi) + \\sin(2\\xi)}{\\cosh(2\\xi) - \\cos(2\\xi)} + \\frac{2(m^2-1)}{3} \\frac{\\sinh(\\xi) - \\sin(\\xi)}{\\cosh(\\xi) + \\cos(\\xi)} \\right]"} block />
                  </>
                )}
                {activeTab === 'coupled' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Coupled Inductor Peak Flux Density:</div>
                    <Latex math={"B_{pk} = B_{dc} + B_{ac} = \\frac{L_{lk} I_{dc}}{N A_e} + \\frac{\\Delta I_L L_{self}}{2 N A_e}"} block />
                  </>
                )}
                {activeTab === 'pfc' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">PFC Boost Inductance Formulation:</div>
                    <Latex math={"L_{min} = \\frac{\\sqrt{2} V_{ac,min} (1 - \\sqrt{2}V_{ac,min}/V_{bus})}{f_{sw} \\cdot (K_{ripple} \\cdot I_{in,pk})}"} block />
                  </>
                )}
                {activeTab === 'inverter' && (
                  <>
                    <div className="mb-2 text-xs font-semibold text-slate-300">Inverter LC Filter Inductance:</div>
                    <Latex math={"L_f = \\frac{V_{dc}}{6 \\cdot \\Delta I_L \\cdot f_{sw}} \\quad (\\text{3-Phase SVPWM})"} block />
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="border-slate-800 bg-[#0b0f19]/60 flex flex-col flex-1">
          <CardHeader className="border-b border-slate-800/80 pb-3 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              Physical Design & Sizing Results
            </CardTitle>
            <div className="text-[10px] text-slate-500 font-mono">
              {activeTab.toUpperCase()} ENGINE ACTIVE
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            {((activeTab === 'ccm' && ccmError) || 
              (activeTab === 'gap' && gapError) || 
              (activeTab === 'air_core' && airError) || 
              (activeTab === 'planar' && planarError) || 
              (activeTab === 'dc_bias' && biasError) || 
              (activeTab === 'litz' && litzError) || 
              (activeTab === 'coupled' && coupError) ||
              (activeTab === 'pfc' && pfcError) ||
              (activeTab === 'inverter' && invError)) && (
              <div className="bg-red-950/40 border border-red-900 rounded p-4 flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div className="text-xs text-red-200">
                  <div className="font-semibold">Calculation Error Occurred</div>
                  <div>{ccmError || gapError || airError || planarError || biasError || litzError || coupError || pfcError || invError}</div>
                </div>
              </div>
            )}

            {activeTab === 'ccm' && ccmRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Min Inductance L_min</span>
                    <span className="text-sm font-bold text-cyan-400">{(ccmRes.l_min_h * 1e6).toFixed(2)} uH</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Ripple Current ΔIL</span>
                    <span className="text-sm font-bold text-emerald-400">{ccmRes.i_ripple_a.toFixed(2)} A</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Peak Current I_peak</span>
                    <span className="text-sm font-bold text-amber-400">{ccmRes.i_peak_a.toFixed(2)} A</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">RMS Current Irms</span>
                    <span className="text-sm font-bold text-emerald-400">{ccmRes.i_rms_a.toFixed(2)} A</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl flex flex-col gap-2">
                  <span className="text-xs font-semibold text-slate-300">AP Core Geometric Sizing Result</span>
                  {(() => {
                    const Ap_cm4 = ((ccmRes.l_min_h * ccmRes.i_peak_a * ccmRes.i_rms_a) / (ccmBmax * ccmJ * ccmKu * 1e-2)) * 10;
                    return (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-400">
                        <div>Required Min AP Area: <span className="text-cyan-400 font-bold">{Ap_cm4.toFixed(3)} cm⁴</span></div>
                        <div>Recommended Core Ae: <span className="text-slate-200 font-semibold">{ccmAe.toFixed(1)} mm²</span></div>
                        <div>Safety Flux Limit Bmax: <span className="text-slate-200 font-semibold">{ccmBmax.toFixed(2)} T</span></div>
                        <div>Current Density J: <span className="text-slate-200 font-semibold">{ccmJ.toFixed(1)} A/mm²</span></div>
                      </div>
                    );
                  })()}
                </div>

                <div className="flex flex-col gap-2">
                  <span className="text-xs text-slate-400 font-semibold">Inductor Current Waveform over Switching Period (CCM)</span>
                  <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 flex justify-center">
                    <svg className="w-full max-w-[400px] h-[140px]" viewBox="0 0 400 140">
                      <line x1="40" y1="20" x2="360" y2="20" stroke="#334155" strokeWidth="0.5" strokeDasharray="2" />
                      <line x1="40" y1="75" x2="360" y2="75" stroke="#334155" strokeWidth="0.5" strokeDasharray="2" />
                      <line x1="40" y1="120" x2="360" y2="120" stroke="#334155" strokeWidth="0.5" strokeDasharray="2" />
                      <line x1="40" y1="120" x2="370" y2="120" stroke="#64748b" strokeWidth="1.5" />
                      <line x1="40" y1="10" x2="40" y2="120" stroke="#64748b" strokeWidth="1.5" />
                      <path d="M 40,85 L 200,35 L 360,85" fill="none" stroke="#22c55e" strokeWidth="2.5" />
                      <circle cx="200" cy="35" r="4" fill="#f59e0b" />
                      <text x="210" y="38" fill="#f59e0b" fontSize="10" fontWeight="bold">I_peak = {ccmRes.i_peak_a.toFixed(2)}A</text>
                      <line x1="40" y1="60" x2="360" y2="60" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="4" />
                      <text x="250" y="52" fill="#38bdf8" fontSize="9">I_out = {ccmIout.toFixed(1)}A</text>
                      <text x="375" y="123" fill="#64748b" fontSize="10">t</text>
                      <text x="15" y="15" fill="#64748b" fontSize="10">i_L</text>
                    </svg>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'gap' && gapRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Theoretical Air Gap lg</span>
                    <span className="text-sm font-bold text-cyan-400">{gapRes.lg_mm.toFixed(3)} mm</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Fringing Factor F</span>
                    <span className="text-sm font-bold text-amber-400">{gapRes.fringing_f.toFixed(3)}</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Corrected Air Gap lg'</span>
                    <span className="text-sm font-bold text-emerald-400">{gapRes.lg_corr_mm.toFixed(3)} mm</span>
                  </div>
                </div>

                {gapRes.lg_corr_mm > 5.0 && (
                  <div className="bg-amber-950/40 border border-amber-900/60 rounded p-3 text-xs text-amber-200 flex items-start gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <strong>Excessive Air Gap Warning:</strong> Corrected air gap is <strong>{gapRes.lg_corr_mm.toFixed(2)} mm</strong>. An overly large air gap leads to strong fringing leakage and winding overheating. Consider increasing core area Ae or turns N.
                    </div>
                  </div>
                )}

                <div className="flex flex-col gap-2">
                  <span className="text-xs text-slate-400 font-semibold">EE Core Physical Air Gap & Fringing Flux Diagram (Hover for details)</span>
                  <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 flex flex-col items-center gap-3">
                    <svg width="340" height="150" viewBox="0 0 340 150" className="text-slate-350">
                      <path d="M 40,15 L 140,15 L 140,25 L 55,25 L 55,58 L 115,58 M 115,78 L 55,78 L 55,115 L 140,115 L 140,125 L 40,125 Z" 
                        fill={hoveredPart === 'core' ? '#475569' : '#334155'} stroke="#475569" strokeWidth="0.8"
                        onMouseEnter={() => setHoveredPart('core')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <path d="M 300,15 L 200,15 L 200,25 L 285,25 L 285,58 L 225,58 M 225,78 L 285,78 L 285,115 L 200,115 L 200,125 L 300,125 Z" 
                        fill={hoveredPart === 'core' ? '#475569' : '#334155'} stroke="#475569" strokeWidth="0.8"
                        onMouseEnter={() => setHoveredPart('core')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <line x1="140" y1="15" x2="200" y2="15" stroke="#64748b" strokeWidth="1" />
                      <line x1="140" y1="125" x2="200" y2="125" stroke="#64748b" strokeWidth="1" />
                      <rect x="115" y="58" width="110" height="20" fill="#090d16" stroke="#fbbf24" strokeWidth="0.8" strokeDasharray="1.5,1.5"
                        onMouseEnter={() => setHoveredPart('gap')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer" />
                      <path d="M 115,58 Q 170,30 225,58" fill="none" stroke="#fbbf24" strokeWidth={hoveredPart === 'fringing' ? '2' : '1'} strokeDasharray="2,2" 
                        onMouseEnter={() => setHoveredPart('fringing')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-all" />
                      <path d="M 115,78 Q 170,106 225,78" fill="none" stroke="#fbbf24" strokeWidth={hoveredPart === 'fringing' ? '2' : '1'} strokeDasharray="2,2"
                        onMouseEnter={() => setHoveredPart('fringing')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-all" />
                      <circle cx="75" cy="40" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <circle cx="95" cy="40" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <circle cx="245" cy="40" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <circle cx="265" cy="40" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <circle cx="75" cy="100" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <circle cx="95" cy="100" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <circle cx="245" cy="100" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                      <circle cx="265" cy="100" r="4" fill={hoveredPart === 'winding' ? '#ea580c' : '#c2410c'} onMouseEnter={() => setHoveredPart('winding')} onMouseLeave={() => setHoveredPart(null)} className="cursor-pointer transition-colors" />
                    </svg>

                    <div className="w-full mt-2 min-h-[50px]">
                      {hoveredPart === 'core' && (
                        <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded text-xs text-slate-300">
                          <strong>Core Body:</strong> Primary magnetic flux return path. Ae = {gapAe} mm², le = {gapLe} mm.
                        </div>
                      )}
                      {hoveredPart === 'gap' && (
                        <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded text-xs text-slate-300">
                          <strong>Physical Air Gap:</strong> Stores magnetic energy and prevents core saturation. Suggested gap is <strong>{gapRes.lg_corr_mm.toFixed(3)} mm</strong>.
                        </div>
                      )}
                      {hoveredPart === 'winding' && (
                        <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded text-xs text-slate-300">
                          <strong>Winding Turns:</strong> Carries excitation current with N = {gapTurns} turns.
                        </div>
                      )}
                      {hoveredPart === 'fringing' && (
                        <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded text-xs text-slate-300">
                          <strong>Fringing Flux:</strong> Magnetic field lines bulging outside the gap, accounted for by fringing factor F = {gapRes.fringing_f.toFixed(3)}.
                        </div>
                      )}
                      {!hoveredPart && (
                        <div className="text-center text-slate-500 text-xs py-2 italic">
                          (Hover over regions to inspect physical details)
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'air_core' && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-2 gap-4">
                  {airResL !== null && (
                    <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                      <span className="text-[10px] text-slate-500">Calculated Inductance L</span>
                      <span className="text-sm font-bold text-cyan-400">{airResL.toFixed(4)} uH</span>
                    </div>
                  )}
                  {airResTurns !== null && (
                    <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                      <span className="text-[10px] text-slate-500">Solved Required Turns N</span>
                      <span className="text-sm font-bold text-emerald-400">{airResTurns.toFixed(1)} Turns</span>
                    </div>
                  )}
                </div>

                <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 flex justify-center">
                  <svg width="280" height="90" viewBox="0 0 280 90" className="text-slate-300">
                    {(() => {
                      const turns = Math.min(15, Math.max(3, Math.round(airTurns)));
                      const start_x = 50;
                      const end_x = 230;
                      const len = end_x - start_x;
                      const pitch = len / turns;
                      const paths = [];
                      for (let i = 0; i < turns; i++) {
                        const cx1 = start_x + i * pitch;
                        const cx2 = start_x + (i + 0.5) * pitch;
                        const cx3 = start_x + (i + 1) * pitch;
                        paths.push(<path key={`back-${i}`} d={`M ${cx1},45 Q ${cx2},65 ${cx3},45`} fill="none" stroke="#7c2d12" strokeWidth="2" strokeDasharray="1.5,1.5" opacity="0.6" />);
                        paths.push(<path key={`front-${i}`} d={`M ${cx1},45 Q ${cx2},25 ${cx3},45`} fill="none" stroke="#ea580c" strokeWidth="2.5" strokeLinecap="round" />);
                      }
                      return paths;
                    })()}
                    <path d="M 20,45 L 50,45" fill="none" stroke="#ea580c" strokeWidth="2" />
                    <path d="M 230,45 L 260,45" fill="none" stroke="#ea580c" strokeWidth="2" />
                    <text x="140" y="15" textAnchor="middle" fill="#94a3b8" className="text-[8px] font-semibold">Axial Length L = {airLength.toFixed(1)} mm</text>
                    <text x="140" y="85" textAnchor="middle" fill="#38bdf8" className="text-[8px] font-semibold">Coil Inner Diameter Din = {airDia.toFixed(1)} mm</text>
                  </svg>
                </div>
              </div>
            )}

            {activeTab === 'planar' && planarRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Inductance L</span>
                    <span className="text-sm font-bold text-cyan-400">{planarRes.l_uh.toFixed(4)} uH</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">DC Resistance DCR</span>
                    <span className="text-sm font-bold text-amber-400">{planarRes.dcr_mohm.toFixed(1)} mΩ</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Outer Diameter Dout</span>
                    <span className="text-sm font-bold text-emerald-400">{planarRes.dout_mm.toFixed(2)} mm</span>
                  </div>
                </div>

                <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 flex justify-center">
                  <svg width="200" height="180" viewBox="0 0 200 180" className="text-slate-350">
                    {(() => {
                      const turns = Math.min(10, planarTurns);
                      const paths = [];
                      const center_x = 100;
                      const center_y = 90;
                      const r_start = 20;
                      const step = 6;
                      if (planarShape === 'circle') {
                        const pts = [];
                        const steps = turns * 36;
                        for (let i = 0; i <= steps; i++) {
                          const theta = (i / 36) * 2 * Math.PI;
                          const r = r_start + (i / steps) * (turns * step);
                          pts.push(`${center_x + r * Math.cos(theta)},${center_y + r * Math.sin(theta)}`);
                        }
                        paths.push(<path key="spiral" d={`M ${pts.join(' L ')}`} fill="none" stroke="#10b981" strokeWidth="2" />);
                      } else {
                        const pts = [];
                        let r = r_start;
                        pts.push(`${center_x},${center_y - r}`);
                        for (let i = 0; i < turns * 4; i++) {
                          r += step / 4;
                          if (i % 4 === 0) pts.push(`${center_x + r},${center_y - r}`);
                          else if (i % 4 === 1) pts.push(`${center_x + r},${center_y + r}`);
                          else if (i % 4 === 2) pts.push(`${center_x - r},${center_y + r}`);
                          else pts.push(`${center_x - r},${center_y - r}`);
                        }
                        paths.push(<path key="spiral" d={`M ${pts.join(' L ')}`} fill="none" stroke="#10b981" strokeWidth="2" />);
                      }
                      return paths;
                    })()}
                    <text x="100" y="175" textAnchor="middle" fill="#fbbf24" className="text-[8px] font-bold">Outer Diameter Dout = {planarRes.dout_mm.toFixed(1)} mm</text>
                  </svg>
                </div>
              </div>
            )}

            {activeTab === 'dc_bias' && biasRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Design Operating Inductance</span>
                    <span className="text-sm font-bold text-cyan-400">{biasRes.l_design_uh.toFixed(2)} uH</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Permeability Retention</span>
                    <span className="text-sm font-bold text-emerald-400">{biasRes.perm_pct_design.toFixed(1)} %</span>
                  </div>
                </div>

                {biasRes.perm_pct_design < 50.0 && (
                  <div className="bg-red-950/40 border border-red-900/60 rounded p-3 text-xs text-red-200 flex items-start gap-2">
                    <ShieldAlert className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    <div>
                      <strong>Severe Magnetic Saturation Warning:</strong> At design current, core permeability drops to <strong>{biasRes.perm_pct_design.toFixed(1)}%</strong> (below 50% safety margin), posing severe risk of saturation runaway! Consider increasing core size, path length le, or choosing High Flux materials.
                    </div>
                  </div>
                )}

                <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 h-[220px]">
                  <ReactECharts notMerge={true} option={getBiasChartOption()} style={{ height: '100%', width: '100%' }} />
                </div>

                <div className="bg-slate-900/20 p-3.5 rounded-xl border border-slate-800 flex flex-col gap-3">
                  <span className="text-[10px] font-bold text-slate-200 border-l-2 border-emerald-500 pl-2">Commercial Powder Core BOM Recommendations (Based on DC Bias Stability)</span>
                  <div className="overflow-x-auto text-[10px]">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="py-2">Part Number</th>
                          <th className="py-2">Area Ae</th>
                          <th className="py-2">AL Value</th>
                          <th className="py-2">Turns</th>
                          <th className="py-2">Actual L</th>
                          <th className="py-2">Permeability</th>
                          <th className="py-2">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {getRecommendedPowderCores(biasL0, biasIdesign).map((c, i) => (
                          <tr key={i} className="border-b border-slate-900 hover:bg-slate-950/40 text-slate-355">
                            <td className="py-2 font-mono">{c.name} ({c.material})</td>
                            <td className="py-2">{c.ae} mm²</td>
                            <td className="py-2">{c.al} nH</td>
                            <td className="py-2">{c.turns} Turns</td>
                            <td className="py-2 font-semibold text-cyan-400">{c.l_actual.toFixed(2)} uH</td>
                            <td className="py-2">{c.perm_pct.toFixed(1)}%</td>
                            <td className="py-2">
                              {c.ok ? (
                                <span className="text-emerald-400 bg-emerald-950/30 px-1 rounded text-[9px]">Recommended</span>
                              ) : (
                                <span className="text-red-400 bg-red-950/30 px-1 rounded text-[9px]">Saturated</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'litz' && litzRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Skin Depth (75°C)</span>
                    <span className="text-sm font-bold text-cyan-400">{litzRes.skin_depth_mm.toFixed(4)} mm</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Dowell Fr Factor</span>
                    <span className="text-sm font-bold text-amber-400">{litzRes.dowell_fr.toFixed(2)}</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Recommended Litz Spec</span>
                    <span className="text-sm font-bold text-emerald-400">AWG {litzRes.recommended_awg}</span>
                  </div>
                </div>

                <div className="bg-slate-900/40 p-4 rounded border border-slate-800 text-xs">
                  <strong>Litz Wire Specification:</strong> At {litzFreq} kHz, we recommend using <strong>AWG {litzRes.recommended_awg}</strong> strand wire with <strong>{litzRes.num_strands} strands</strong> (estimated bundle outer diameter {litzRes.litz_od_mm.toFixed(2)} mm), keeping the Dowell proximity resistance ratio down to <strong>{litzRes.dowell_fr.toFixed(2)}</strong>.
                </div>
              </div>
            )}

            {activeTab === 'coupled' && coupRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Leakage Inductance L_lk</span>
                    <span className="text-sm font-bold text-cyan-400">{coupRes.l_lk_uh.toFixed(2)} uH</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Mutual Inductance L_m</span>
                    <span className="text-sm font-bold text-cyan-400">{coupRes.l_m_uh.toFixed(2)} uH</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Outer Leg Gap lg</span>
                    <span className="text-sm font-bold text-emerald-400">{coupRes.g_outer_mm.toFixed(4)} mm</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Center Post Gap g_ctr</span>
                    <span className="text-sm font-bold text-emerald-400">{coupRes.g_center_mm.toFixed(4)} mm</span>
                  </div>
                </div>

                <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 flex justify-center">
                  <svg className="w-[280px] h-[110px]" viewBox="0 0 280 110">
                    <path d="M 30,10 L 130,10 L 130,25 L 55,25 L 55,50 L 130,50 L 130,70 L 55,70 L 55,95 L 130,95 L 130,110 L 30,110 Z" fill="#475569" />
                    <path d="M 250,10 L 150,10 L 150,25 L 225,25 L 225,50 L 150,50 L 150,70 L 225,70 L 225,95 L 150,95 L 150,110 L 250,110 Z" fill="#475569" />
                    <rect x="70" y="20" width="20" height="70" rx="2" fill="#d97706" opacity="0.9" />
                    <text x="80" y="60" fill="#fff" fontSize="8" textAnchor="middle">N1</text>
                    <rect x="190" y="20" width="20" height="70" rx="2" fill="#d97706" opacity="0.9" />
                    <text x="200" y="60" fill="#fff" fontSize="8" textAnchor="middle">N2</text>
                    <rect x="135" y="50" width="10" height="20" fill="#ef4444" />
                    <text x="140" y="44" fill="#ef4444" fontSize="8" textAnchor="middle">g_ctr</text>
                  </svg>
                </div>
              </div>
            )}

            {activeTab === 'pfc' && pfcRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Optimal Inductance L_opt</span>
                    <span className="text-sm font-bold text-cyan-400">{pfcRes.l_opt_uh.toFixed(1)} uH</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Peak Inductor Current I_L_pk</span>
                    <span className="text-sm font-bold text-cyan-400">{pfcRes.i_l_pk_a.toFixed(2)} A</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Grid Peak Input Current</span>
                    <span className="text-sm font-bold text-cyan-400">{pfcRes.iin_pk_a.toFixed(2)} A</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl flex flex-col gap-2">
                  <span className="text-xs font-semibold text-slate-200">PFC Boost Inductor Physical Specifications</span>
                  {(() => {
                    const L = pfcRes.l_opt_uh * 1e-6;
                    const I_pk = pfcRes.i_l_pk_a;
                    const N = Math.ceil((L * I_pk) / (pfcBmax * pfcAe * 1e-6));
                    const lg = ((4 * Math.PI * 1e-7 * (N ** 2) * pfcAe * 1e-6) / L - (pfcLe * 1e-3 / pfcUr)) * 1000;
                    return (
                      <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                        <div>Recommended Turns N: <span className="text-slate-200 font-semibold">{N} Turns</span></div>
                        <div>Physical Air Gap lg: <span className="text-emerald-400 font-semibold">{lg.toFixed(2)} mm</span></div>
                        <div>Operating Flux Bmax: <span className="text-slate-200 font-semibold">{pfcBmax.toFixed(2)} T</span></div>
                        <div>RMS Input Current Iin_rms: <span className="text-slate-200 font-semibold">{(pfcRes.iin_pk_a / Math.sqrt(2)).toFixed(2)} A</span></div>
                      </div>
                    );
                  })()}
                </div>

                <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 h-[220px]">
                  <ReactECharts notMerge={true} option={(() => {
                    const pts = 50;
                    const avg = [];
                    const upper = [];
                    const lower = [];
                    const cats = [];
                    const L_val = pfcRes.l_opt_uh * 1e-6;
                    const F_val = pfcFsw * 1000.0;
                    for (let i = 0; i <= pts; i++) {
                      const theta = (i / pts) * Math.PI;
                      const Vin_t = pfcVacMin * Math.sqrt(2) * Math.sin(theta);
                      const D_t = Math.max(0, 1 - Vin_t / pfcVbus);
                      const dI = L_val > 0 && F_val > 0 ? (Vin_t * D_t) / (L_val * F_val) : 0;
                      const I_in_t = pfcRes.iin_pk_a * Math.sin(theta);
                      avg.push(parseFloat(I_in_t.toFixed(2)));
                      upper.push(parseFloat((I_in_t + dI/2).toFixed(2)));
                      lower.push(parseFloat(Math.max(0, I_in_t - dI/2).toFixed(2)));
                      cats.push(((i/pts)*10).toFixed(1) + "ms");
                    }
                    return {
                      backgroundColor: 'transparent',
                      tooltip: { trigger: 'axis' },
                      legend: { data: ['Input Average Current', 'Inductor Peak Envelope', 'Inductor Valley Envelope'], textStyle: { color: '#94a3b8', fontSize: 9 } },
                      grid: { left: '10%', right: '10%', bottom: '5%', containLabel: true },
                      xAxis: { type: 'category', data: cats, axisLabel: { color: '#64748b' } },
                      yAxis: { type: 'value', axisLabel: { color: '#64748b' } },
                      series: [
                        { name: 'Input Average Current', type: 'line', data: avg, smooth: true, itemStyle: { color: '#3b82f6' } },
                        { name: 'Inductor Peak Envelope', type: 'line', data: upper, smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#ef4444' } },
                        { name: 'Inductor Valley Envelope', type: 'line', data: lower, smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#10b981' } }
                      ]
                    };
                  })()} style={{ height: '100%', width: '100%' }} />
                </div>
              </div>
            )}

            {activeTab === 'inverter' && invRes && (
              <div className="flex flex-col gap-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Modulation Index M</span>
                    <span className="text-sm font-bold text-cyan-400">{invRes.modulation_index.toFixed(3)}</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Filter Inductance L_f</span>
                    <span className="text-sm font-bold text-emerald-400">{(invRes.l_min_h * 1e6).toFixed(1)} uH</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Filter Capacitance C_f</span>
                    <span className="text-sm font-bold text-emerald-400">{((invRes.c_min_f ?? 0) * 1e6 || 10).toFixed(2)} uF</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl flex flex-col gap-2">
                  <span className="text-xs font-semibold text-slate-200">Inverter Filter Inductor Specifications</span>
                  {(() => {
                    const L = invRes.l_min_h;
                    const I_pk = invIoutRms * Math.sqrt(2) + invRes.delta_il / 2;
                    const N = Math.ceil((L * I_pk) / (invBmax * invAe * 1e-6));
                    const lg = Math.max(0, ((4 * Math.PI * 1e-7 * (N ** 2) * invAe * 1e-6) / L - (invLe * 1e-3 / invUr)) * 1000);
                    return (
                      <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                        <div>Recommended Turns N: <span className="text-slate-200 font-semibold">{N} Turns</span></div>
                        <div>Physical Air Gap lg: <span className="text-emerald-400 font-semibold">{lg.toFixed(2)} mm</span></div>
                        <div>Max Current Stress I_L_pk: <span className="text-slate-200 font-semibold">{I_pk.toFixed(2)} A</span></div>
                        <div>Cutoff Frequency fc: <span className="text-slate-200 font-semibold">{invFCutoff} kHz</span></div>
                      </div>
                    );
                  })()}
                </div>

                <div className="w-full bg-slate-950/60 p-4 rounded border border-slate-900 h-[220px]">
                  <ReactECharts notMerge={true} option={(() => {
                    const pts = 60;
                    const avg = [];
                    const upper = [];
                    const lower = [];
                    const cats = [];
                    const I_pk = invIoutRms * Math.sqrt(2);
                    for (let i = 0; i <= pts; i++) {
                      const theta = (i / pts) * 2 * Math.PI;
                      const I_fund = I_pk * Math.sin(theta);
                      avg.push(parseFloat(I_fund.toFixed(2)));
                      upper.push(parseFloat((I_fund + invRes.delta_il/2).toFixed(2)));
                      lower.push(parseFloat((I_fund - invRes.delta_il/2).toFixed(2)));
                      cats.push(((i/pts)*20).toFixed(1) + "ms");
                    }
                    return {
                      backgroundColor: 'transparent',
                      tooltip: { trigger: 'axis' },
                      legend: { data: ['Fundamental Output Current', 'Inductor Peak Envelope', 'Inductor Valley Envelope'], textStyle: { color: '#94a3b8', fontSize: 9 } },
                      grid: { left: '10%', right: '10%', bottom: '5%', containLabel: true },
                      xAxis: { type: 'category', data: cats, axisLabel: { color: '#64748b' } },
                      yAxis: { type: 'value', axisLabel: { color: '#64748b' } },
                      series: [
                        { name: 'Fundamental Output Current', type: 'line', data: avg, smooth: true, itemStyle: { color: '#3b82f6' } },
                        { name: 'Inductor Peak Envelope', type: 'line', data: upper, smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#ef4444' } },
                        { name: 'Inductor Valley Envelope', type: 'line', data: lower, smooth: true, lineStyle: { type: 'dashed' }, itemStyle: { color: '#10b981' } }
                      ]
                    };
                  })()} style={{ height: '100%', width: '100%' }} />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
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
            <h1 className="text-base font-bold text-white tracking-tight">Power Inductor Magnetic Design & Sizing</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Calculate magnetic core, air gap, and winding parameters for power inductors, with Dowell AC resistance, fringing factor correction, and DC bias soft saturation checks.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            onClick={handleResetLayout}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2 bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-350 px-4 py-2 rounded-lg text-xs transition cursor-pointer"
          >
            <span>Reset Layout</span>
          </Button>
          <button
            onClick={() => setShowFormulas(!showFormulas)}
            className={`px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1 border transition-all cursor-pointer ${
              showFormulas 
                ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' 
                : 'bg-slate-950 border-slate-800 text-slate-400'
            }`}
          >
            <FileCode className="w-3 h-3" />
            {showFormulas ? 'Hide Equations' : 'Show Equations'}
          </button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={(val: any) => setActiveTab(val as TabType)} className="w-full">
        <TabsList className="bg-[#020617] border border-slate-800 h-auto p-1 flex flex-wrap gap-1 justify-start">
          <TabsTrigger value="ccm" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">Buck Design (CCM)</TabsTrigger>
          <TabsTrigger value="gap" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">Air Gap & Fringing</TabsTrigger>
          <TabsTrigger value="air_core" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">Air Core (Wheeler)</TabsTrigger>
          <TabsTrigger value="planar" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">PCB Spiral Inductor</TabsTrigger>
          <TabsTrigger value="dc_bias" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">DC Bias Soft Saturation</TabsTrigger>
          <TabsTrigger value="litz" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">HF Litz Wire (Dowell)</TabsTrigger>
          <TabsTrigger value="coupled" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">Coupled Inductor</TabsTrigger>
          <TabsTrigger value="pfc" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">PFC Boost Inductor</TabsTrigger>
          <TabsTrigger value="inverter" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">Inverter LC Inductor</TabsTrigger>
        </TabsList>
      </Tabs>

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
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Operating Conditions & Design Inputs</span>
                  </div>
                  {renderInput()}
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
                  {renderResults()}
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
