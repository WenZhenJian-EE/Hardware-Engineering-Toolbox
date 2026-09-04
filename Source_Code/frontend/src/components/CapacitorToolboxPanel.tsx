import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { useDragDeckLayout, DragCard, DragDeck } from './ui/LayoutEngine';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Compass,
  Info,
  ShieldAlert,
  TrendingUp,
  FileCode
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

interface LifetimeResponse {
  life_hours: number;
  life_years?: number;
  life_multiplier: number;
  t_core: number;
  drc_warnings: string[];
}

interface RmsSumResponse {
  i_rms_total: number;
  drc_warnings: string[];
}

interface TopologyRmsResponse {
  i_rms_cap: number;
  d_actual: number;
  p_loss_esr: number;
  t_rise: number;
  t_core: number;
  drc_warnings: string[];
}

interface MlccBiasResponse {
  c_eff: number;
  ratio: number;
  drc_warnings: string[];
}

interface HoldupResponse {
  success: boolean;
  c_val_uf: number;
  t_hold_ms: number;
  e_total_j: number;
  i_max: number;
  v_drop: number;
  drc_warnings: string[];
}

type TabType = 'life' | 'rms' | 'topology' | 'mlcc' | 'holdup';

export default function CapacitorToolboxPanel({ onBack }: { onBack: () => void }) {
  const [activeTab, setActiveTab] = useTabHistoryState<TabType>('life', 'activeTab');
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);
  const [showFormulas, setShowFormulas] = useState<boolean>(false);

  // Tab 1: Electrolytic Capacitor Lifetime
  const [lifeL0, setLifeL0] = useState<number>(2000);
  const [lifeT0, setLifeT0] = useState<number>(105);
  const [lifeTa, setLifeTa] = useState<number>(65);
  const [lifeDt, setLifeDt] = useState<number>(10);
  const [lifeUseThermal, setLifeUseThermal] = useState<boolean>(false);
  const [lifeIRms, setLifeIRms] = useState<number>(1.5);
  const [lifeEsr, setLifeEsr] = useState<number>(35);
  const [lifeRth, setLifeRth] = useState<number>(18);
  const [lifeUseVoltage, setLifeUseVoltage] = useState<boolean>(false);
  const [lifeVNominal, setLifeVNominal] = useState<number>(50.0);
  const [lifeVActual, setLifeVActual] = useState<number>(40.0);
  const [lifeCapType, setLifeCapType] = useState<string>("Electrolytic");
  const [lifeRes, setLifeRes] = useState<LifetimeResponse | null>(null);
  const [lifeError, setLifeError] = useState<string | null>(null);

  // Tab 2: RMS Current Summation
  const [rmsComponents, setRmsComponents] = useState<{ name: string; freq: string; i_rms: number }[]>([
    { name: 'Switching Frequency Ripple', freq: '100k', i_rms: 2.0 },
    { name: 'Line Grid Ripple', freq: '100', i_rms: 0.5 }
  ]);
  const [rmsRes, setRmsRes] = useState<RmsSumResponse | null>(null);
  const [rmsError, setRmsError] = useState<string | null>(null);

  // Tab 3: Topology RMS Current
  const [topoMode, setTopoMode] = useState<string>('Buck input capacitor');
  const [topoVin, setTopoVin] = useState<number>(48.0);
  const [topoVout, setTopoVout] = useState<number>(12.0);
  const [topoIout, setTopoIout] = useState<number>(10.0);
  const [topoDuty, setTopoDuty] = useState<number>(0.0);
  const [topoLir, setTopoLir] = useState<number>(30.0);
  const [topoM, setTopoM] = useState<number>(0.8);
  const [topoPf, setTopoPf] = useState<number>(0.9);
  const [topoEsr, setTopoEsr] = useState<number>(20.0);
  const [topoRth, setTopoRth] = useState<number>(12.0);
  const [topoTa, setTopoTa] = useState<number>(65.0);
  const [topoRes, setTopoRes] = useState<TopologyRmsResponse | null>(null);
  const [topoError, setTopoError] = useState<string | null>(null);

  // Tab 4: MLCC DC Bias Derating
  const [mlccCnom, setMlccCnom] = useState<number>(10.0);
  const [mlccVrated, setMlccVrated] = useState<number>(50.0);
  const [mlccVdc, setMlccVdc] = useState<number>(24.0);
  const [mlccDielectric, setMlccDielectric] = useState<string>('X5R / X7R / X7S (High K)');
  const [mlccPackage, setMlccPackage] = useState<string>('0805');
  const [mlccRes, setMlccRes] = useState<MlccBiasResponse | null>(null);
  const [mlccError, setMlccError] = useState<string | null>(null);

  // Tab 5: Hold-up Time & Supercap
  const [huVstart, setHuVstart] = useState<number>(390.0);
  const [huVstop, setHuVstop] = useState<number>(300.0);
  const [huPout, setHuPout] = useState<number>(100.0);
  const [huEff, setHuEff] = useState<number>(0.90);
  const [huEsr, setHuEsr] = useState<number>(0.0);
  const [huTargetVal, setHuTargetVal] = useState<number>(20.0);
  const [huIsCalcCap, setHuIsCalcCap] = useState<boolean>(true);
  const [huRes, setHuRes] = useState<HoldupResponse | null>(null);
  const [huError, setHuError] = useState<string | null>(null);

  const getLayoutConfigForTab = (tab: TabType) => {
    switch (tab) {
      case 'life':
        return {
          defaultCards: ['input', 'theory', 'results', 'charts', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', charts: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, charts: 8, drc: 8 },
          defaultHeights: { input: 460, theory: 280, results: 200, charts: 300, drc: 180 }
        };
      case 'rms':
        return {
          defaultCards: ['input', 'theory', 'results', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, drc: 8 },
          defaultHeights: { input: 480, theory: 260, results: 240, drc: 180 }
        };
      case 'topology':
        return {
          defaultCards: ['input', 'theory', 'results', 'schematic', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', schematic: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, schematic: 8, drc: 8 },
          defaultHeights: { input: 540, theory: 280, results: 320, schematic: 220, drc: 180 }
        };
      case 'mlcc':
        return {
          defaultCards: ['input', 'theory', 'results', 'charts', 'schematic', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', charts: 'right', schematic: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, charts: 8, schematic: 8, drc: 8 },
          defaultHeights: { input: 420, theory: 260, results: 200, charts: 300, schematic: 220, drc: 180 }
        };
      case 'holdup':
        return {
          defaultCards: ['input', 'theory', 'results', 'charts', 'schematic', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', charts: 'right', schematic: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, charts: 8, schematic: 8, drc: 8 },
          defaultHeights: { input: 480, theory: 280, results: 320, charts: 300, schematic: 220, drc: 180 }
        };
    }
  };

  const currentLayoutConfig = getLayoutConfigForTab(activeTab);

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
    panelKey: 'layout_capacitor_v4',
    activeTab: activeTab,
    defaultCards: currentLayoutConfig.defaultCards,
    defaultColumns: currentLayoutConfig.defaultColumns,
    defaultSpans: currentLayoutConfig.defaultSpans,
    defaultHeights: currentLayoutConfig.defaultHeights
  });

  useEffect(() => {
    const raw = localStorage.getItem('target_dclink_capacitor_life_data');
    if (raw) {
      try {
        const payload = JSON.parse(raw);
        if (payload.tab === 'life') {
          setActiveTab('life');
          if (payload.i_rms_phase !== undefined && payload.esr_mohm !== undefined) {
            const calculatedDt = (payload.i_rms_phase ** 2) * (payload.esr_mohm * 1e-3) * 10;
            setLifeDt(parseFloat(calculatedDt.toFixed(2)));
          }
        } else if (payload.tab === 'topology') {
          setActiveTab('topology');
          if (payload.v_actual !== undefined) setTopoVout(payload.v_actual);
          if (payload.i_rms_phase !== undefined) setTopoIout(parseFloat((payload.i_rms_phase / 0.6).toFixed(2)));
          if (payload.esr_mohm !== undefined) setTopoEsr(payload.esr_mohm);
        }
      } catch (e) {
        console.error('Failed to parse target_dclink_capacitor_life_data:', e);
      } finally {
        localStorage.removeItem('target_dclink_capacitor_life_data');
      }
    }
  }, []);

  const fetchLifetime = async () => {
    setLifeError(null);
    try {
      const response = await apiFetch('/api/calculate/capacitor_toolbox/lifetime', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          l0: lifeL0,
          t0: lifeT0,
          ta: lifeTa,
          dt: lifeDt,
          use_thermal: lifeUseThermal,
          i_rms: lifeIRms,
          esr_mohm: lifeEsr,
          rth_kw: lifeRth,
          use_voltage: lifeUseVoltage,
          v_nominal: lifeVNominal,
          v_actual: lifeVActual,
          cap_type: lifeCapType
        }),
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json();
        const errMsg = Array.isArray(err.detail)
          ? err.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ')
          : (err.detail || 'Calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setLifeRes(data);
    } catch (e: any) {
      setLifeError(e.message);
    }
  };

  const fetchRmsSum = async () => {
    setRmsError(null);
    try {
      const response = await apiFetch('/api/calculate/capacitor_toolbox/rms_sum', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          components: rmsComponents.map(c => ({ name: c.name, freq: c.freq, i_rms: c.i_rms }))
        }),
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json();
        const errMsg = Array.isArray(err.detail)
          ? err.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ')
          : (err.detail || 'Calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setRmsRes(data);
    } catch (e: any) {
      setRmsError(e.message);
    }
  };

  const fetchTopologyRms = async () => {
    setTopoError(null);
    try {
      const response = await apiFetch('/api/calculate/capacitor_toolbox/topology_rms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: topoMode,
          vin: topoVin,
          vout: topoVout,
          iout: topoIout,
          duty: topoDuty,
          lir: topoLir,
          m: topoM,
          pf: topoPf,
          esr_mohm: topoEsr,
          rth: topoRth,
          ta: topoTa
        }),
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json();
        const errMsg = Array.isArray(err.detail)
          ? err.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ')
          : (err.detail || 'Calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setTopoRes(data);
    } catch (e: any) {
      setTopoError(e.message);
    }
  };

  const fetchMlccBias = async () => {
    setMlccError(null);
    try {
      const response = await apiFetch('/api/calculate/capacitor_toolbox/mlcc_bias', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cnom: mlccCnom,
          vrated: mlccVrated,
          vdc: mlccVdc,
          dielectric: mlccDielectric,
          package: mlccPackage
        }),
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json();
        const errMsg = Array.isArray(err.detail)
          ? err.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ')
          : (err.detail || 'Calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setMlccRes(data);
    } catch (e: any) {
      setMlccError(e.message);
    }
  };

  const fetchHoldup = async () => {
    setHuError(null);
    try {
      const response = await apiFetch('/api/calculate/capacitor_toolbox/holdup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_start: huVstart,
          v_stop: huVstop,
          p_out: huPout,
          eff: huEff,
          esr: huEsr,
          target_val: huTargetVal,
          is_calc_cap: huIsCalcCap
        }),
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json();
        const errMsg = Array.isArray(err.detail)
          ? err.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', ')
          : (err.detail || 'Calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setHuRes(data);
    } catch (e: any) {
      setHuError(e.message);
      setHuRes(null);
    }
  };

  useEffect(() => {
    if (activeTab === 'life') fetchLifetime();
    else if (activeTab === 'rms') fetchRmsSum();
    else if (activeTab === 'topology') fetchTopologyRms();
    else if (activeTab === 'mlcc') fetchMlccBias();
    else if (activeTab === 'holdup') fetchHoldup();
  }, [
    lifeL0, lifeT0, lifeTa, lifeDt, 
    lifeUseThermal, lifeIRms, lifeEsr, lifeRth,
    lifeUseVoltage, lifeVNominal, lifeVActual, lifeCapType,
    rmsComponents, 
    topoMode, topoVin, topoVout, topoIout, topoDuty, topoLir, topoM, topoPf, topoEsr, topoRth, topoTa, 
    mlccCnom, mlccVrated, mlccVdc, mlccDielectric, mlccPackage, 
    huVstart, huVstop, huPout, huEff, huEsr, huTargetVal, huIsCalcCap, 
    activeTab
  ]);

  const addRmsRow = () => {
    setRmsComponents([...rmsComponents, { name: `Ripple Component #${rmsComponents.length + 1}`, freq: '1k', i_rms: 1.0 }]);
  };

  const removeRmsRow = (index: number) => {
    if (rmsComponents.length <= 1) return;
    const list = rmsComponents.filter((_, i) => i !== index);
    setRmsComponents(list);
  };

  const updateRmsRow = (index: number, key: 'name' | 'freq' | 'i_rms', val: any) => {
    const list = [...rmsComponents];
    (list[index] as any)[key] = val;
    setRmsComponents(list);
  };

  const getLifetimeChartOption = () => {
    if (!lifeRes) return {};
    const l0 = lifeL0;
    const t0 = lifeT0;
    const t_core_point = lifeRes.t_core;

    const seriesData = [];
    const minT = Math.max(0, t0 - 60);
    const maxT = t0 + 10;
    for (let t = minT; t <= maxT; t += 2) {
      const life = l0 * (2.0 ** ((t0 - t) / 10.0));
      seriesData.push([t, Math.round(life)]);
    }

    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: 'axis', 
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#14b8a6',
        borderWidth: 1.5,
        shadowColor: 'rgba(20, 184, 166, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 },
        formatter: 'Core Temp: {b}°C<br/>Estimated Lifetime: {c} hours' 
      },
      grid: { top: '15%', left: '12%', right: '10%', bottom: '25%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Temp (°C)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      yAxis: {
        type: 'log',
        name: 'Life (h)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
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
          borderColor: 'rgba(20, 184, 166, 0.15)',
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '110%',
          handleStyle: {
            color: '#14b8a6',
            shadowBlur: 5,
            shadowColor: 'rgba(20, 184, 166, 0.5)'
          },
          textStyle: { color: '#94a3b8', fontSize: 9 },
          fillerColor: 'rgba(20, 184, 166, 0.05)',
          dataBackground: {
            lineStyle: { color: '#14b8a6', width: 1 },
            areaStyle: { color: 'rgba(20, 184, 166, 0.02)' }
          },
          selectedDataBackground: {
            lineStyle: { color: '#14b8a6', width: 1.5 },
            areaStyle: { color: 'rgba(20, 184, 166, 0.1)' }
          }
        }
      ],
      series: [
        {
          name: 'Arrhenius Curve',
          type: 'line',
          data: seriesData,
          smooth: true,
          showSymbol: false,
          lineStyle: { 
            color: '#14b8a6', 
            width: 3,
            shadowColor: 'rgba(20, 184, 166, 0.8)',
            shadowBlur: 8
          },
          markPoint: {
            data: [{ name: 'Operating Point', coord: [t_core_point, Math.round(lifeRes.life_hours)], itemStyle: { color: '#f43f5e' } }]
          }
        }
      ]
    };
  };

  const getMlccChartOption = () => {
    if (!mlccRes) return {};
    const is_c0g = mlccDielectric.includes("C0G") || mlccDielectric.includes("NP0");
    const seriesData = [];

    const pkg_data: Record<string, number> = {
      "1210": 0.5, "1206": 1.0, "0805": 2.5, "0603": 4.5, "0402": 8.0, "0201": 15.0
    };
    const k_factor = pkg_data[mlccPackage] || 2.5;

    for (let v_ratio = 0; v_ratio <= 1.2; v_ratio += 0.02) {
      let ratio = 1.0;
      if (!is_c0g) {
        ratio = 1.0 / (1.0 + k_factor * (v_ratio ** 2));
        if (ratio < 0.1) ratio = 0.1;
      }
      seriesData.push([parseFloat((v_ratio * 100).toFixed(0)), parseFloat((ratio * 100).toFixed(1))]);
    }

    const current_v_ratio = (mlccVdc / mlccVrated) * 100;
    const current_ratio = mlccRes.ratio * 100;

    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: 'axis', 
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#fb923c',
        borderWidth: 1.5,
        shadowColor: 'rgba(251, 146, 60, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 },
        formatter: 'Bias Ratio: {b}%<br/>Capacity Retained: {c}%' 
      },
      grid: { top: '15%', left: '10%', right: '10%', bottom: '25%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Vdc / Vrated (%)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      yAxis: {
        type: 'value',
        name: 'Capacitance Ratio (%)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
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
          borderColor: 'rgba(251, 146, 60, 0.15)',
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '110%',
          handleStyle: {
            color: '#fb923c',
            shadowBlur: 5,
            shadowColor: 'rgba(251, 146, 60, 0.5)'
          },
          textStyle: { color: '#94a3b8', fontSize: 9 },
          fillerColor: 'rgba(251, 146, 60, 0.05)',
          dataBackground: {
            lineStyle: { color: '#fb923c', width: 1 },
            areaStyle: { color: 'rgba(251, 146, 60, 0.02)' }
          },
          selectedDataBackground: {
            lineStyle: { color: '#fb923c', width: 1.5 },
            areaStyle: { color: 'rgba(251, 146, 60, 0.1)' }
          }
        }
      ],
      series: [
        {
          name: 'DC Bias Derating',
          type: 'line',
          data: seriesData,
          smooth: true,
          showSymbol: false,
          lineStyle: { 
            color: '#fb923c', 
            width: 3,
            shadowColor: 'rgba(251, 146, 60, 0.8)',
            shadowBlur: 8
          },
          markPoint: {
            data: [{ name: 'Operating Point', coord: [current_v_ratio, current_ratio], itemStyle: { color: '#ef4444' } }]
          }
        }
      ]
    };
  };

  const getHoldupChartOption = () => {
    if (!huRes || !huRes.success) return {};
    const steps = 100;
    const v_start = huVstart;
    const c_uf = huRes.c_val_uf;
    const t_hold_ms = huRes.t_hold_ms;
    const p_in = huPout / Math.max(huEff, 0.01);
    const esr = huEsr;
    
    const vCurve = [];
    const maxTime = t_hold_ms * 1.15;
    
    for (let i = 0; i <= steps; i++) {
      const t_ms = (maxTime * i) / steps;
      const t_sec = t_ms / 1000.0;
      
      const v_cap_internal_sq = v_start ** 2 - (2.0 * p_in * t_sec) / (c_uf * 1e-6);
      if (v_cap_internal_sq <= 0) break;
      const v_cap_internal = Math.sqrt(v_cap_internal_sq);
      
      const disc = v_cap_internal ** 2 - 4.0 * p_in * esr;
      let v_terminal = v_cap_internal;
      if (disc >= 0) {
        v_terminal = (v_cap_internal + Math.sqrt(disc)) / 2.0;
      } else {
        v_terminal = 0;
      }
      
      if (v_terminal < huVstop * 0.7) break;
      vCurve.push([t_ms, v_terminal]);
    }

    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: 'axis', 
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#a78bfa',
        borderWidth: 1.5,
        shadowColor: 'rgba(167, 139, 250, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 },
        formatter: 'Time: {b} ms<br/>Voltage: {c} V' 
      },
      grid: { top: '15%', left: '10%', right: '10%', bottom: '25%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Time (ms)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      yAxis: {
        type: 'value',
        name: 'Voltage (V)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
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
          borderColor: 'rgba(167, 139, 250, 0.15)',
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '110%',
          handleStyle: {
            color: '#a78bfa',
            shadowBlur: 5,
            shadowColor: 'rgba(167, 139, 250, 0.5)'
          },
          textStyle: { color: '#94a3b8', fontSize: 9 },
          fillerColor: 'rgba(167, 139, 250, 0.05)',
          dataBackground: {
            lineStyle: { color: '#a78bfa', width: 1 },
            areaStyle: { color: 'rgba(167, 139, 250, 0.02)' }
          },
          selectedDataBackground: {
            lineStyle: { color: '#a78bfa', width: 1.5 },
            areaStyle: { color: 'rgba(167, 139, 250, 0.1)' }
          }
        }
      ],
      series: [
        {
          name: 'Discharge Voltage Trajectory',
          type: 'line',
          data: vCurve,
          smooth: true,
          showSymbol: false,
          lineStyle: { 
            color: '#a78bfa', 
            width: 3,
            shadowColor: 'rgba(167, 139, 250, 0.8)',
            shadowBlur: 8
          },
          markLine: {
            data: [
              { xAxis: t_hold_ms, name: 'Hold-up Time', lineStyle: { color: '#f43f5e', type: 'dashed' } },
              { yAxis: huVstop, name: 'Cutoff Voltage', lineStyle: { color: '#f59e0b', type: 'dashed' } }
            ]
          }
        }
      ]
    };
  };

  const renderLifeInputs = () => (
    <div className="space-y-3.5">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-500">Rated Life L0 (Hours)</label>
          <input type="number" step="500" value={lifeL0} onChange={(e) => setLifeL0(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-500">Max Rated Temp T0 (°C)</label>
          <input type="number" step="5" value={lifeT0} onChange={(e) => setLifeT0(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-500">Ambient Temp Ta (°C)</label>
          <input type="number" step="1" value={lifeTa} onChange={(e) => setLifeTa(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-500">Self-Heating ΔT (°C) {lifeUseThermal ? "(Computed)" : "(Direct Input)"}</label>
          <input type="number" step="0.5" disabled={lifeUseThermal} value={lifeDt} onChange={(e) => setLifeDt(parseFloat(e.target.value) || 0)} className={`w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono ${lifeUseThermal ? 'opacity-50 cursor-not-allowed' : ''}`} />
        </div>
      </div>

      <div className="border-t border-slate-850 my-2 pt-2">
        <div className="flex items-center gap-1.5 mb-2">
          <input type="checkbox" id="lifeUseThermal" checked={lifeUseThermal} onChange={(e) => setLifeUseThermal(e.target.checked)} className="rounded border-slate-800 bg-slate-950 text-blue-600 focus:ring-blue-600 focus:ring-offset-slate-900" />
          <label htmlFor="lifeUseThermal" className="text-[9px] font-bold text-slate-300 cursor-pointer select-none">Estimate Self-Heating (Irms / ESR / Rth)</label>
        </div>
        {lifeUseThermal && (
          <div className="grid grid-cols-3 gap-2 bg-slate-950/30 p-2 border border-slate-850 rounded-lg">
            <div className="flex flex-col gap-1">
              <label className="text-[8px] text-slate-500">Ripple Irms (A)</label>
              <input type="number" step="0.1" value={lifeIRms} onChange={(e) => setLifeIRms(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none font-mono" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[8px] text-slate-500">ESR (mΩ)</label>
              <input type="number" step="1" value={lifeEsr} onChange={(e) => setLifeEsr(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none font-mono" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[8px] text-slate-500">Thermal Rth (K/W)</label>
              <input type="number" step="1" value={lifeRth} onChange={(e) => setLifeRth(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none font-mono" />
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-slate-850 my-2 pt-2">
        <div className="flex items-center gap-1.5 mb-2">
          <input type="checkbox" id="lifeUseVoltage" checked={lifeUseVoltage} onChange={(e) => setLifeUseVoltage(e.target.checked)} className="rounded border-slate-800 bg-slate-950 text-blue-600 focus:ring-blue-600 focus:ring-offset-slate-900" />
          <label htmlFor="lifeUseVoltage" className="text-[9px] font-bold text-slate-300 cursor-pointer select-none">Voltage Stress Correction</label>
        </div>
        {lifeUseVoltage && (
          <div className="grid grid-cols-3 gap-2 bg-slate-950/30 p-2 border border-slate-850 rounded-lg">
            <div className="flex flex-col gap-1 col-span-1">
              <label className="text-[8px] text-slate-500">Type</label>
              <select value={lifeCapType} onChange={(e) => setLifeCapType(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none">
                <option value="Electrolytic">Electrolytic</option>
                <option value="Film">Film</option>
                <option value="Ceramic">Ceramic</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[8px] text-slate-500">Rated V_RWM (V)</label>
              <input type="number" step="1" value={lifeVNominal} onChange={(e) => setLifeVNominal(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none font-mono" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[8px] text-slate-500">Operating V_op (V)</label>
              <input type="number" step="1" value={lifeVActual} onChange={(e) => setLifeVActual(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none font-mono" />
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderRmsInputs = () => (
    <div className="space-y-3.5">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] text-slate-400 font-bold">Ripple Harmonics:</span>
        <Button size="sm" onClick={addRmsRow} className="text-[8px] px-2 py-0.5 h-6 bg-blue-600/30 border border-blue-500/50 hover:bg-blue-600">Add Component</Button>
      </div>
      <div className="space-y-2 border border-slate-850 rounded-lg p-2 max-h-44 overflow-y-auto scrollbar-thin">
        {rmsComponents.map((comp, idx) => (
          <div key={idx} className="flex gap-2 items-center bg-slate-950/40 p-2 border border-slate-900 rounded-md">
            <input type="text" value={comp.name} onChange={(e) => updateRmsRow(idx, 'name', e.target.value)} className="flex-1 bg-slate-900 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none" />
            <input type="text" value={comp.freq} onChange={(e) => updateRmsRow(idx, 'freq', e.target.value)} className="w-14 bg-slate-900 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none text-center font-mono" placeholder="100k" />
            <input type="number" step="0.1" value={comp.i_rms} onChange={(e) => updateRmsRow(idx, 'i_rms', parseFloat(e.target.value) || 0)} className="w-16 bg-slate-900 border border-slate-800 rounded p-1 text-[10px] text-white focus:outline-none text-right font-mono" />
            <button onClick={() => removeRmsRow(idx)} className="text-[8px] bg-rose-500/20 border border-rose-500/30 hover:bg-rose-500 hover:text-white px-1.5 py-0.5 rounded cursor-pointer transition border-0 font-bold text-rose-400">Del</button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderTopoInputs = () => (
    <div className="space-y-3.5">
      <div className="flex flex-col gap-1">
        <label className="text-[8px] text-slate-550">Converter Position</label>
        <select value={topoMode} onChange={(e) => setTopoMode(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white cursor-pointer focus:outline-none font-mono">
          <option value="Buck input capacitor">Buck Input Capacitor</option>
          <option value="Buck output capacitor">Buck Output Capacitor</option>
          <option value="Boost input capacitor">Boost Input Capacitor</option>
          <option value="Boost output capacitor">Boost Output Capacitor</option>
          <option value="Flyback output capacitor">Flyback Secondary Output Capacitor</option>
        </select>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Vin (V)</label>
          <input type="number" step="0.1" value={topoVin} onChange={(e) => setTopoVin(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Vout (V)</label>
          <input type="number" step="0.1" value={topoVout} onChange={(e) => setTopoVout(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Iout (A)</label>
          <input type="number" step="0.1" value={topoIout} onChange={(e) => setTopoIout(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">ESR (mΩ)</label>
          <input type="number" step="1" value={topoEsr} onChange={(e) => setTopoEsr(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Thermal Rth (°C/W)</label>
          <input type="number" step="0.5" value={topoRth} onChange={(e) => setTopoRth(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Ambient Ta (°C)</label>
          <input type="number" step="1" value={topoTa} onChange={(e) => setTopoTa(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Duty Cycle (0 for auto)</label>
          <input type="number" step="0.05" min="0" max="0.95" value={topoDuty} onChange={(e) => setTopoDuty(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>
    </div>
  );

  const renderMlccInputs = () => (
    <div className="space-y-3.5">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Nominal Capacitance (μF)</label>
          <input type="number" step="0.1" value={mlccCnom} onChange={(e) => setMlccCnom(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Rated Voltage V_rated (V)</label>
          <input type="number" step="1" value={mlccVrated} onChange={(e) => setMlccVrated(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-[8px] text-slate-550 font-bold text-amber-400">DC Bias Voltage Vdc (V)</label>
        <input type="number" step="0.5" value={mlccVdc} onChange={(e) => setMlccVdc(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
      </div>
      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Dielectric Class</label>
          <select value={mlccDielectric} onChange={(e) => setMlccDielectric(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white cursor-pointer focus:outline-none font-mono">
            <option value="X5R / X7R / X7S (High K)">X5R/X7R/X7S (High-K)</option>
            <option value="C0G / NP0 (Class I)">C0G/NP0 (Class I - No Derating)</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">SMD Package</label>
          <select value={mlccPackage} onChange={(e) => setMlccPackage(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white cursor-pointer focus:outline-none font-mono">
            <option value="0402">0402</option>
            <option value="0603">0603</option>
            <option value="0805">0805</option>
            <option value="1206">1206</option>
            <option value="1210">1210</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderHoldupInputs = () => (
    <div className="space-y-3.5">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Start Voltage V_start (V)</label>
          <input type="number" step="10" value={huVstart} onChange={(e) => setHuVstart(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Cutoff Voltage V_stop (V)</label>
          <input type="number" step="10" value={huVstop} onChange={(e) => setHuVstop(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Pout (W)</label>
          <input type="number" step="10" value={huPout} onChange={(e) => setHuPout(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Efficiency η (0-1)</label>
          <input type="number" step="0.01" value={huEff} onChange={(e) => setHuEff(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">ESR (Ω)</label>
          <input type="number" step="0.01" value={huEsr} onChange={(e) => setHuEsr(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="border-t border-slate-800 pt-3 flex flex-col gap-3">
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-1 text-[10px] text-slate-350 cursor-pointer">
            <input type="radio" checked={huIsCalcCap} onChange={() => setHuIsCalcCap(true)} className="rounded-full h-3 w-3 text-blue-500 focus:ring-blue-500 cursor-pointer" />
            <span>Solve Capacitance C</span>
          </label>
          <label className="flex items-center gap-1 text-[10px] text-slate-350 cursor-pointer">
            <input type="radio" checked={!huIsCalcCap} onChange={() => setHuIsCalcCap(false)} className="rounded-full h-3 w-3 text-blue-500 focus:ring-blue-500 cursor-pointer" />
            <span>Solve Hold-Up Time Thold</span>
          </label>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">
            {huIsCalcCap ? 'Target Hold-Up Time Thold (ms)' : 'Capacitance C (μF)'}
          </label>
          <input type="number" step="1" value={huTargetVal} onChange={(e) => setHuTargetVal(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>
    </div>
  );

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
            <h1 className="text-base font-bold text-white tracking-tight">Capacitor Lifetime & Derating Toolbox</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">Predict electrolytic capacitor Arrhenius thermal lifetime, multi-frequency RMS ripple summation, and MLCC DC bias derating.</p>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={() => setShowFormulas(!showFormulas)}
            className={`flex items-center space-x-2 border px-4 py-2 rounded-lg font-medium transition cursor-pointer ${
              showFormulas 
                ? 'bg-blue-600/20 border-blue-500 text-blue-400' 
                : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <FileCode className="w-4 h-4" />
            <span>Formulas</span>
          </button>
          <button
            onClick={handleResetLayout}
            className="flex items-center space-x-2 bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-350 px-4 py-2 rounded-lg text-xs transition cursor-pointer"
          >
            <span>Reset Layout</span>
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 bg-slate-900/60 p-1 rounded-xl border border-slate-800 max-w-7xl mx-auto w-full">
        {([
          { id: 'life', label: '1. Electrolytic Lifetime', icon: null},
          { id: 'rms', label: '2. Multi-Freq RMS Sum', icon: null},
          { id: 'topology', label: '3. Topology Ripple RMS', icon: null},
          { id: 'mlcc', label: '4. MLCC DC Bias Derating', icon: null},
          { id: 'holdup', label: '5. Hold-Up Energy Buffer', icon: <TrendingUp size={13} /> }
        ] as const).map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
              activeTab === tab.id
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {showFormulas && (
        <div className="max-w-7xl mx-auto w-full bg-slate-900 border border-blue-900/60 rounded-xl p-6 space-y-4">
          <h3 className="text-lg font-bold text-blue-400 flex items-center space-x-2">
            <Info className="w-5 h-5" />
            <span>Capacitor Physical Principles & Lifetime Models</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-slate-350">
            <div className="space-y-3">
              <h4 className="font-semibold text-slate-200">1. Arrhenius Lifetime Model</h4>
              <p>Chemical reaction rates double for every 10°C drop in core temperature:</p>
              <Latex math="L_{eff} = L_0 \cdot 2^{\frac{T_0 - (T_a + \Delta T)}{10}}" block />
              <p className="text-slate-400 text-xs">Where ΔT represents self-heating generated by ripple currents across internal ESR.</p>
            </div>
            <div className="space-y-3">
              <h4 className="font-semibold text-slate-200">2. Hold-Up Energy Conservation</h4>
              <p>Capacitive energy release must supply the downstream constant-power stage during outage:</p>
              <Latex math="C = \frac{2 \cdot P_{out} \cdot T_{hold}}{\eta \cdot (V_{start}^2 - V_{stop}^2)}" block />
            </div>
          </div>
        </div>
      )}

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 min-h-0">
        {lifeError && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3">Error: {lifeError}</div>}
        {rmsError && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3">Error: {rmsError}</div>}
        {topoError && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3">Error: {topoError}</div>}
        {mlccError && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3">Error: {mlccError}</div>}
        {huError && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3">Error: {huError}</div>}

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
          onDropOnColumn={handleDropOnColumn}
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
                    <span className="text-xs font-bold text-white">Electrical & Operating Inputs</span>
                  </div>
                  {activeTab === 'life' && renderLifeInputs()}
                  {activeTab === 'rms' && renderRmsInputs()}
                  {activeTab === 'topology' && renderTopoInputs()}
                  {activeTab === 'mlcc' && renderMlccInputs()}
                  {activeTab === 'holdup' && renderHoldupInputs()}
                </div>
              )}

              {key === 'theory' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md animate-fade-in">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <BookOpen className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Physical Equations & Models</span>
                  </div>
                  <div className="text-[10px] text-slate-400 space-y-4 leading-relaxed">
                    {activeTab === 'life' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">1. Arrhenius Multiplier Factor:</span>
                          <Latex math="\text{Multiplier} = 2^{\frac{T_0 - T_{core}}{10}}" block />
                        </div>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">2. Capacitor Core Temperature:</span>
                          <Latex math="T_{core} = T_a + \Delta T_{self-rise}" block />
                        </div>
                      </>
                    )}
                    {activeTab === 'rms' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">Multi-Harmonic RMS Summation:</span>
                          <p>Ripple losses across distinct frequency components are orthogonal and sum via Root-Sum-Square (RSS):</p>
                          <Latex math="I_{rms,total} = \sqrt{\sum_{k} I_{rms,k}^2}" block />
                        </div>
                      </>
                    )}
                    {activeTab === 'topology' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">Converter Topology RMS Ripple:</span>
                          <p>Taking a Buck input capacitor as an example, switching chopper RMS current is given by:</p>
                          <Latex math="I_{rms} = I_{out} \cdot \sqrt{D \cdot (1 - D)}" block />
                        </div>
                      </>
                    )}
                    {activeTab === 'mlcc' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">MLCC DC Bias Voltage Derating:</span>
                          <p>High-K ceramic capacitors (X7R/X5R) exhibit electric dipole saturation under DC bias, reducing capacitance:</p>
                          <Latex math="C_{effective} = C_{nominal} \cdot f(V_{dc}/V_{rated})" block />
                        </div>
                      </>
                    )}
                    {activeTab === 'holdup' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">Hold-up Time & Energy Storage:</span>
                          <Latex math="C = \frac{2 \cdot P_{out} \cdot T_{hold}}{\eta \cdot (V_{start}^2 - V_{stop}^2)}" block />
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Calculated Performance Metrics</span>
                  </div>

                  {activeTab === 'life' && lifeRes && (
                    <div className="grid grid-cols-2 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Predicted Lifetime (Hours)</span>
                        <span className="text-sm font-bold text-blue-400">{(lifeRes.life_hours ?? 0).toFixed(0)} h</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Predicted Lifetime (Years)</span>
                        <span className="text-sm font-bold text-emerald-400">{(lifeRes.life_years ?? 0).toFixed(2)} Years</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5 col-span-2">
                        <span className="text-[8px] text-slate-400 font-sans">Core Temp T_core (with Self-Heating)</span>
                        <span className="text-sm font-bold text-slate-200">{(lifeRes.t_core ?? 0).toFixed(1)} °C</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'rms' && rmsRes && (
                    <div className="grid grid-cols-2 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5 col-span-2">
                        <span className="text-[8px] text-slate-400 font-sans">Total Multi-Frequency RMS Ripple</span>
                        <span className="text-lg font-bold text-blue-400">{(rmsRes.i_rms_total ?? 0).toFixed(3)} Arms</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'topology' && topoRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Capacitor RMS Ripple</span>
                        <span className="text-sm font-bold text-blue-400">{(topoRes.i_rms_cap ?? 0).toFixed(3)} A</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Actual Duty Cycle</span>
                        <span className="text-sm font-bold text-slate-200">{(topoRes.d_actual ?? 0).toFixed(3)}</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">ESR Power Loss</span>
                        <span className="text-sm font-bold text-slate-200">{(topoRes.p_loss_esr ?? 0).toFixed(3)} W</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Self-Heating Rise ΔT</span>
                        <span className="text-sm font-bold text-slate-200">{(topoRes.t_rise ?? 0).toFixed(1)} °C</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Predicted Core T_core</span>
                        <span className="text-sm font-bold text-slate-200">{(topoRes.t_core ?? 0).toFixed(1)} °C</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'mlcc' && mlccRes && (
                    <div className="grid grid-cols-2 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Effective Capacitance C_eff</span>
                        <span className="text-sm font-bold text-blue-400">{(mlccRes.c_eff ?? 0).toFixed(3)} μF</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Retained Capacity</span>
                        <span className="text-sm font-bold text-emerald-400">{((mlccRes.ratio ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'holdup' && huRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Hold-Up Time Thold</span>
                        <span className="text-sm font-bold text-blue-400">{(huRes.t_hold_ms ?? 0).toFixed(2)} ms</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Required Capacitance C</span>
                        <span className="text-sm font-bold text-blue-400">{(huRes.c_val_uf ?? 0).toFixed(1)} μF</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Discharge Energy</span>
                        <span className="text-sm font-bold text-slate-200">{(huRes.e_total_j ?? 0).toFixed(3)} J</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Max DC Discharge Current</span>
                        <span className="text-sm font-bold text-slate-200">{(huRes.i_max ?? 0).toFixed(2)} A</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Initial ESR Voltage Drop</span>
                        <span className="text-sm font-bold text-slate-200">{(huRes.v_drop ?? 0).toFixed(2)} V</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'charts' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <span className="text-xs font-bold text-white block border-b border-slate-800 pb-2 mb-2">Parametric Sweeps & Response Curves</span>
                  <div className="w-full h-[180px]">
                    {activeTab === 'life' && lifeRes && (
                      <ReactECharts option={getLifetimeChartOption()} notMerge={true} style={{ width: '100%', height: '100%' }} />
                    )}
                    {activeTab === 'mlcc' && mlccRes && (
                      <ReactECharts option={getMlccChartOption()} notMerge={true} style={{ width: '100%', height: '100%' }} />
                    )}
                    {activeTab === 'holdup' && huRes && huRes.success && (
                      <ReactECharts option={getHoldupChartOption()} notMerge={true} style={{ width: '100%', height: '100%' }} />
                    )}
                  </div>
                </div>
              )}

              {key === 'schematic' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md animate-fade-in">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <Compass className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Capacitor Equivalent Circuit Model (SVG)</span>
                  </div>
                  <div className="w-full h-[180px] flex items-center justify-center bg-slate-950/20 rounded-xl border border-slate-850 p-2">
                    {activeTab === 'topology' && (
                      <svg width="100%" height="100%" viewBox="0 0 220 100" className="text-slate-400 bg-transparent max-w-[440px] max-h-[160px]">
                        <defs>
                          <style>{`
                            @keyframes flow-dash {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-flow-cyan {
                              stroke-dasharray: 5, 5;
                              animation: flow-dash 1.2s linear infinite;
                            }
                          `}</style>
                          <filter id="neon-glow-cyan" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-green" x="-25%" y="-25%" width="150%" height="150%">
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
                          <linearGradient id="blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#2563eb" stopOpacity="0.5" />
                          </linearGradient>
                        </defs>
                        <rect x="25" y="25" width="45" height="26" rx="2" fill="url(#blue-grad)" stroke="#38bdf8" strokeWidth="1.5" filter="url(#neon-glow-cyan)" />
                        <text x="47" y="41" textAnchor="middle" fill="#e0f2fe" className="text-[7.5px] font-bold" filter="url(#neon-glow-cyan)">Stage</text>
                        
                        <path d="M 70,38 L 190,38" fill="none" stroke="#38bdf8" strokeWidth="2.5" className="animate-flow-cyan" />
                        <line x1="70" y1="38" x2="190" y2="38" stroke="#cbd5e1" strokeWidth="1.0" />
                        
                        <line x1="100" y1="38" x2="100" y2="50" stroke="#cbd5e1" strokeWidth="1.2" />
                        <line x1="90" y1="50" x2="110" y2="50" stroke="#10b981" strokeWidth="2.5" filter="url(#neon-glow-green)" />
                        <line x1="90" y1="56" x2="110" y2="56" stroke="#10b981" strokeWidth="2.5" filter="url(#neon-glow-green)" />
                        <line x1="100" y1="56" x2="100" y2="66" stroke="#cbd5e1" strokeWidth="1.2" />
                        
                        <rect x="94" y="66" width="12" height="12" fill="none" stroke="#fb923c" strokeWidth="1.5" filter="url(#neon-glow-amber)" />
                        <text x="100" y="74" textAnchor="middle" fill="#ffedd5" className="text-[7px] font-bold" filter="url(#neon-glow-amber)">ESR</text>
                        <line x1="100" y1="78" x2="100" y2="88" stroke="#cbd5e1" strokeWidth="1.2" />
                        <line x1="10" y1="88" x2="200" y2="88" stroke="#64748b" strokeWidth="1.2" />
                      </svg>
                    )}
                    {activeTab === 'mlcc' && (
                      <svg width="100%" height="100%" viewBox="0 0 220 100" className="text-slate-400 bg-transparent max-w-[440px] max-h-[160px]">
                        <defs>
                          <filter id="neon-glow-amber-mlcc" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <linearGradient id="ceramic-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#b45309" stopOpacity="0.3" />
                            <stop offset="50%" stopColor="#d97706" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#78350f" stopOpacity="0.2" />
                          </linearGradient>
                          <linearGradient id="metal-grad" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#cbd5e1" />
                            <stop offset="50%" stopColor="#94a3b8" />
                            <stop offset="100%" stopColor="#475569" />
                          </linearGradient>
                        </defs>
                        <rect x="40" y="25" width="140" height="40" fill="url(#ceramic-grad)" stroke="#f59e0b" strokeWidth="1.5" filter="url(#neon-glow-amber-mlcc)" />
                        
                        <rect x="35" y="25" width="15" height="40" fill="url(#metal-grad)" stroke="#94a3b8" strokeWidth="0.8" rx="0.5" />
                        <rect x="170" y="25" width="15" height="40" fill="url(#metal-grad)" stroke="#94a3b8" strokeWidth="0.8" rx="0.5" />
                        
                        <line x1="50" y1="35" x2="150" y2="35" stroke="#e2e8f0" strokeWidth="1.5" />
                        <line x1="70" y1="45" x2="170" y2="45" stroke="#e2e8f0" strokeWidth="1.5" />
                        <line x1="50" y1="55" x2="150" y2="55" stroke="#e2e8f0" strokeWidth="1.5" />
                      </svg>
                    )}
                    {activeTab === 'holdup' && (
                      <svg width="100%" height="100%" viewBox="0 0 220 100" className="text-slate-400 bg-transparent max-w-[440px] max-h-[160px]">
                        <defs>
                          <style>{`
                            @keyframes flow-dash {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-flow-purple {
                              stroke-dasharray: 5, 5;
                              animation: flow-dash 1.2s linear infinite;
                            }
                          `}</style>
                          <filter id="neon-glow-purple" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-green" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <linearGradient id="purple-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#7c3aed" stopOpacity="0.5" />
                          </linearGradient>
                          <linearGradient id="dcdc-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#60a5fa" stopOpacity="0.1" />
                            <stop offset="100%" stopColor="#2563eb" stopOpacity="0.4" />
                          </linearGradient>
                        </defs>
                        <line x1="20" y1="30" x2="70" y2="30" stroke="#cbd5e1" strokeWidth="1.2" />
                        
                        <polygon points="70,22 70,38 85,30" fill="url(#purple-grad)" stroke="#a78bfa" strokeWidth="1.5" filter="url(#neon-glow-purple)" />
                        <line x1="85" y1="22" x2="85" y2="38" stroke="#a78bfa" strokeWidth="1.5" filter="url(#neon-glow-purple)" />
                        
                        <path d="M 85,30 L 140,30" fill="none" stroke="#a78bfa" strokeWidth="2.5" className="animate-flow-purple" />
                        <line x1="85" y1="30" x2="140" y2="30" stroke="#cbd5e1" strokeWidth="1.0" />
                        
                        <line x1="20" y1="75" x2="200" y2="75" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="110" y1="30" x2="110" y2="42" stroke="#cbd5e1" strokeWidth="1.2" />
                        
                        <line x1="100" y1="42" x2="120" y2="42" stroke="#10b981" strokeWidth="2.5" filter="url(#neon-glow-green)" />
                        <line x1="100" y1="48" x2="120" y2="48" stroke="#10b981" strokeWidth="2.5" filter="url(#neon-glow-green)" />
                        <line x1="110" y1="48" x2="110" y2="75" stroke="#cbd5e1" strokeWidth="1.2" />
                        
                        <rect x="140" y="15" width="45" height="26" rx="2" fill="url(#dcdc-grad)" stroke="#60a5fa" strokeWidth="1.5" />
                        <text x="162" y="31" textAnchor="middle" fill="#93c5fd" className="text-[7px] font-bold">DC-DC (η)</text>
                      </svg>
                    )}
                  </div>
                </div>
              )}

              {key === 'drc' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-bold text-white">DRC Rule Alerts & Checks</span>
                  </div>

                  <div className="flex flex-col gap-2.5">
                    {activeTab === 'life' && lifeRes && (
                      <>
                        {lifeRes.life_hours < 5000 ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Low Lifetime:</strong> Calculated lifetime of {(lifeRes.life_hours).toFixed(0)} hours fails to meet 5,000-10,000 hour industrial benchmarks. Choose a higher temperature-rated capacitor (T0=125°C) or reduce ripple current.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Lifetime Adequate:</strong> Projected operating life meets reliability margins.</span>
                          </div>
                        )}

                        {lifeRes.t_core > lifeT0 ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Thermal Overstress:</strong> Core temperature ({lifeRes.t_core.toFixed(1)}°C) exceeds rated limit ({lifeT0}°C). Severe risk of electrolyte dry-out and dielectric breakdown.</span>
                          </div>
                        ) : null}
                      </>
                    )}

                    {activeTab === 'topology' && topoRes && (
                      <>
                        {topoRes.t_rise > 10.0 ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Excessive Temperature Rise:</strong> Ripple heating causes a rise of {topoRes.t_rise.toFixed(1)}°C, exceeding the 10°C guideline. Parallel additional capacitors to distribute ESR loss.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Temperature Rise Safe:</strong> Self-heating ΔT remains within safe operating bounds.</span>
                          </div>
                        )}
                      </>
                    )}

                    {activeTab === 'mlcc' && mlccRes && (
                      <>
                        {mlccRes.ratio < 0.5 ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Severe MLCC Capacity Collapse:</strong> Due to DC bias, effective capacitance is derated to {((mlccRes.ratio ?? 0) * 100).toFixed(1)}% of nominal. Ripple voltage will surge and loop instability may occur. Upgrade to a larger case size or increase rated voltage.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>MLCC Capacity Adequate:</strong> DC bias capacitance retention is within acceptable margins.</span>
                          </div>
                        )}

                        {mlccVdc > mlccVrated ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Dielectric Overvoltage:</strong> Operating DC bias {mlccVdc}V exceeds rating {mlccVrated}V. Catastrophic avalanche breakdown imminent.</span>
                          </div>
                        ) : null}
                      </>
                    )}

                    {activeTab === 'holdup' && huRes && (
                      <>
                        {huRes.success === false ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>ESR Voltage Drop Violation:</strong> High discharge current across ESR produces an instantaneous drop of ({huRes.v_drop.toFixed(2)}V), immediately pulling terminal voltage below cutoff V_stop ({huVstop}V). Choose an ultra-low ESR capacitor.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Hold-Up Design Valid:</strong> ESR drop and stored energy satisfy retention constraints.</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </DragCard>
          )}
        />
      </div>
    </div>
  );
}
