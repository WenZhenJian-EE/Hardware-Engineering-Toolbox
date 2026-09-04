import { useTabHistoryState } from '../lib/tabHistory';
import { apiFetch } from '../lib/api';
import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  ArrowLeft,
  RefreshCw,
  Maximize2
} from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Button } from './ui/Button';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import InputProtectionSchematicSandbox from './InputProtectionSchematicSandbox';

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

const E96 = [
  1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43,
  1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10,
  2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
  3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53,
  4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
  6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
];

function findClosestStandard(val: number, series: number[]): { value: number; error: number } {
  if (!val || val <= 0) return { value: 0, error: 0 };
  const log10 = Math.log10(val);
  const decade = Math.floor(log10);
  const normVal = val / Math.pow(10, decade);
  let closestNorm = series[0];
  let minDiff = Math.abs(normVal - closestNorm);
  for (let i = 1; i < series.length; i++) {
    const diff = Math.abs(normVal - series[i]);
    if (diff < minDiff) {
      minDiff = diff;
      closestNorm = series[i];
    }
  }
  const standardVal = closestNorm * Math.pow(10, decade);
  const error = ((standardVal - val) / val) * 100;
  return { value: parseFloat(standardVal.toFixed(3)), error: parseFloat(error.toFixed(2)) };
}

interface FuseResponse {
  i_peak: number;
  tau_ms: number;
  i2t_calc: number;
  i2t_req: number;
}

interface NtcResponse {
  over_energy: boolean;
  e_sys: number;
  e_rec: number;
  tau_s: number;
  t_cool_s: number;
}

interface XcapResponse {
  r_rec_m: number;
  v_peak: number;
  r_max_m: number;
  r_actual_m: number;
  r_single_m: number;
  p_loss_mw: number;
  is_passed: boolean;
}

interface BomItem {
  designator: string;
  calcValue: string;
  stdValue: string;
  error: string;
  type: string;
  desc: string;
}

type ParentTab = 'fuse_center' | 'ntc_center' | 'xcap_center';
type SubTab = 'design' | 'schematic';

export default function InputProtectionPanel({ onBack }: { onBack: () => void }) {
  const [parentTab, setParentTab] = useTabHistoryState<ParentTab>('fuse_center', 'parentTab');
  const parentTabRef = useRef(parentTab);
  useEffect(() => { parentTabRef.current = parentTab; }, [parentTab]);

  const [fuseSubTab, setFuseSubTab] = useTabHistoryState<SubTab>('design', 'fuseSubTab');
  const [ntcSubTab, setNtcSubTab] = useTabHistoryState<SubTab>('design', 'ntcSubTab');
  const [xcapSubTab, setXcapSubTab] = useTabHistoryState<SubTab>('design', 'xcapSubTab');

  const activeTab = parentTab === 'fuse_center'
    ? (fuseSubTab === 'design' ? 'fuse' : 'fuse_schematic')
    : parentTab === 'ntc_center'
      ? (ntcSubTab === 'design' ? 'ntc' : 'ntc_schematic')
      : (xcapSubTab === 'design' ? 'xcap' : 'xcap_schematic');

  const [isFuseWired, setIsFuseWired] = useState(false);
  const [isNtcWired, setIsNtcWired] = useState(false);
  const [isRcWired, setIsRcWired] = useState(false);

  useEffect(() => {
    const checkSavedWired = (tab: 'fuse' | 'ntc' | 'rc') => {
      const savedWires = localStorage.getItem(`toolbox_inputprotection_layout_wires_${tab}`);
      if (!savedWires) return false;
      try {
        const wires = JSON.parse(savedWires);
        if (tab === 'fuse') {
          const w1 = wires.some((w: any) => (w.from === 'Vin.P' && w.to === 'Fuse.Pin1') || (w.from === 'Fuse.Pin1' && w.to === 'Vin.P'));
          const w2 = wires.some((w: any) => (w.from === 'Fuse.Pin2' && w.to === 'R_series.Pin1') || (w.from === 'R_series.Pin1' && w.to === 'Fuse.Pin2'));
          const w3 = wires.some((w: any) => (w.from === 'R_series.Pin2' && w.to === 'C_bulk.P') || (w.from === 'C_bulk.P' && w.to === 'R_series.Pin2'));
          const gnd1 = wires.some((w: any) => (w.from === 'Vin.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'Vin.N'));
          const gnd2 = wires.some((w: any) => (w.from === 'C_bulk.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'C_bulk.N'));
          return w1 && w2 && w3 && gnd1 && gnd2;
        } else if (tab === 'ntc') {
          const w1 = wires.some((w: any) => (w.from === 'Vin.P' && w.to === 'NTC.Pin1') || (w.from === 'NTC.Pin1' && w.to === 'Vin.P'));
          const w2 = wires.some((w: any) => (w.from === 'NTC.Pin2' && w.to === 'C_bulk.P') || (w.from === 'C_bulk.P' && w.to === 'NTC.Pin2'));
          const gnd1 = wires.some((w: any) => (w.from === 'Vin.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'Vin.N'));
          const gnd2 = wires.some((w: any) => (w.from === 'C_bulk.N' && w.to === 'GND.Pin') || (w.from === 'GND.Pin' && w.to === 'C_bulk.N'));
          return w1 && w2 && gnd1 && gnd2;
        } else if (tab === 'rc') {
          const w1 = wires.some((w: any) => (w.from === 'VAC.P' && w.to === 'CX.Pin1') || (w.from === 'CX.Pin1' && w.to === 'VAC.P'));
          const w2 = wires.some((w: any) => (w.from === 'CX.Pin1' && w.to === 'R_discharge.Pin1') || (w.from === 'R_discharge.Pin1' && w.to === 'CX.Pin1'));
          const w3 = wires.some((w: any) => (w.from === 'VAC.N' && w.to === 'CX.Pin2') || (w.from === 'CX.Pin2' && w.to === 'VAC.N'));
          const w4 = wires.some((w: any) => (w.from === 'CX.Pin2' && w.to === 'R_discharge.Pin2') || (w.from === 'R_discharge.Pin2' && w.to === 'CX.Pin2'));
          return w1 && w2 && w3 && w4;
        }
      } catch (e) {
        return false;
      }
      return false;
    };

    setIsFuseWired(checkSavedWired('fuse'));
    setIsNtcWired(checkSavedWired('ntc'));
    setIsRcWired(checkSavedWired('rc'));
  }, []);

  const renderWiredCheck = (wired: boolean, children: React.ReactNode) => {
    if (!wired) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center p-6 bg-slate-950/20 rounded-xl border border-dashed border-slate-850/60">
          <ShieldAlert className="w-8 h-8 text-amber-500 mb-2 animate-pulse" />
          <span className="text-[11px] font-semibold text-slate-350">Circuit Net Incomplete</span>
          <p className="text-[9px] text-slate-500 max-w-[240px] mt-1">Switch to the Circuit Schematic tab to connect nodes. Completing the circuit automatically unlocks calculations.</p>
        </div>
      );
    }
    return children;
  };

  const getLayoutConfigForTab = (tab: string) => {
    if (tab.endsWith('_schematic')) {
      return {
        defaultCards: ['sandbox'],
        defaultColumns: { sandbox: 'left' } as Record<string, 'left' | 'right'>,
        defaultSpans: { sandbox: 12 },
        defaultHeights: { sandbox: 650 }
      };
    }
    return {
      defaultCards: ['input', 'results'],
      defaultColumns: { input: 'left', results: 'right' } as Record<string, 'left' | 'right'>,
      defaultSpans: { input: 4, results: 8 },
      defaultHeights: { input: 800, results: 800 }
    };
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
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_inputprotectionpanel_v4',
    activeTab: activeTab,
    defaultCards: currentLayoutConfig.defaultCards,
    defaultColumns: currentLayoutConfig.defaultColumns,
    defaultSpans: currentLayoutConfig.defaultSpans,
    defaultHeights: currentLayoutConfig.defaultHeights
  });

  // Tab 1: Fuse
  const [fuseIn, setFuseIn] = useState({ vin: 230, is_ac: true, c_bulk_uf: 100, r_series: 5.0, factor: 0.3 });
  const [fuseOut, setFuseOut] = useState<FuseResponse | null>(null);

  // Tab 2: NTC
  const [ntcIn, setNtcIn] = useState({ v_in_max: 264, is_ac: true, c_bulk_uf: 100, j_rating: 30, diss_mw: 15 });
  const [ntcOut, setNtcOut] = useState<NtcResponse | null>(null);

  // Tab 3: X-Cap
  const [xcapIn, setXcapIn] = useState({ vac: 230, cx_uf: 1.0, t_limit: 2.0, v_safe: 60, n_series: 2, custom_r_m_enabled: false, custom_r_m: 1.0 });
  const [xcapOut, setXcapOut] = useState<XcapResponse | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [chartOption, setChartOption] = useState<any>({});

  const calcFuse = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/protection/fuse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vin: fuseIn.vin,
          is_ac: fuseIn.is_ac,
          c_bulk_uf: fuseIn.c_bulk_uf,
          r_series: fuseIn.r_series,
          factor: fuseIn.factor
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Fuse calculation failed');
      }
      const data = await response.json();
      setFuseOut(data);
      renderFuseChart(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const calcNtc = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/protection/ntc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_in_max: ntcIn.v_in_max,
          is_ac: ntcIn.is_ac,
          c_bulk_uf: ntcIn.c_bulk_uf,
          j_rating: ntcIn.j_rating,
          diss_mw: ntcIn.diss_mw
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'NTC inrush calculation failed');
      }
      const data = await response.json();
      setNtcOut(data);
      renderNtcChart(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const calcXcap = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/protection/xcap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vac: xcapIn.vac,
          cx_uf: xcapIn.cx_uf,
          t_limit: xcapIn.t_limit,
          v_safe: xcapIn.v_safe,
          n_series: xcapIn.n_series,
          custom_r_m: xcapIn.custom_r_m_enabled ? xcapIn.custom_r_m : null
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'X-Cap discharge calculation failed');
      }
      const data = await response.json();
      setXcapOut(data);
      renderXcapChart(data);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const renderFuseChart = (data: FuseResponse) => {
    const timeVals: number[] = [];
    const currentVals: number[] = [];
    const i2tVals: number[] = [];

    const tau = Math.max(data.tau_ms * 1e-3, 1e-9);
    const iPeak = data.i_peak;
    const steps = 100;
    const maxT = Math.max(0.01, tau * 5);

    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * maxT;
      timeVals.push(parseFloat((t * 1e3).toFixed(2)));
      
      const current = iPeak * Math.exp(-t / tau);
      currentVals.push(parseFloat(current.toFixed(2)));

      const i2t = 0.5 * iPeak * iPeak * tau * (1 - Math.exp(-2 * t / tau));
      i2tVals.push(parseFloat(i2t.toFixed(4)));
    }

    const option = {
      backgroundColor: 'transparent',
      title: {
        text: 'Turn-On Inrush Current i(t) & Accumulated Energy I²t Curve',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        shadowColor: 'rgba(56, 189, 248, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
      },
      legend: {
        data: ['Current i(t) (A)', 'Accumulated Energy I²t (A²s)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '10%', right: '10%', bottom: '25%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: timeVals,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 't (ms)'
      },
      yAxis: [
        {
          type: 'value',
          name: 'Current (A)',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
        },
        {
          type: 'value',
          name: 'I2t (A²s)',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { show: false }
        }
      ],
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
          borderColor: 'rgba(56, 189, 248, 0.15)',
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '110%',
          handleStyle: {
            color: '#38bdf8',
            shadowBlur: 5,
            shadowColor: 'rgba(56, 189, 248, 0.5)'
          },
          textStyle: { color: '#94a3b8', fontSize: 9 },
          fillerColor: 'rgba(56, 189, 248, 0.05)',
          dataBackground: {
            lineStyle: { color: '#38bdf8', width: 1 },
            areaStyle: { color: 'rgba(56, 189, 248, 0.02)' }
          },
          selectedDataBackground: {
            lineStyle: { color: '#38bdf8', width: 1.5 },
            areaStyle: { color: 'rgba(56, 189, 248, 0.1)' }
          }
        }
      ],
      series: [
        {
          name: 'Current i(t) (A)',
          type: 'line',
          data: currentVals,
          smooth: true,
          lineStyle: { 
            color: '#38bdf8', 
            width: 3,
            shadowColor: 'rgba(56, 189, 248, 0.8)',
            shadowBlur: 8
          },
          showSymbol: false
        },
        {
          name: 'Accumulated Energy I²t (A²s)',
          type: 'line',
          yAxisIndex: 1,
          data: i2tVals,
          smooth: true,
          lineStyle: { 
            color: '#c084fc', 
            width: 3,
            shadowColor: 'rgba(192, 132, 252, 0.8)',
            shadowBlur: 8
          },
          showSymbol: false
        }
      ]
    };
    setChartOption(option);
  };

  const renderNtcChart = (data: NtcResponse) => {
    const capVals: number[] = [];
    const energyVals: number[] = [];

    const startCap = 10;
    const endCap = 500;
    const steps = 30;
    const vPeak = ntcIn.is_ac ? ntcIn.v_in_max * Math.sqrt(2) : ntcIn.v_in_max;

    for (let i = 0; i <= steps; i++) {
      const c = startCap + (i / steps) * (endCap - startCap);
      capVals.push(Math.round(c));
      const e = 0.5 * (c * 1e-6) * vPeak * vPeak;
      energyVals.push(parseFloat(e.toFixed(2)));
    }

    const option = {
      backgroundColor: 'transparent',
      title: {
        text: 'Bulk Capacitor Inrush Energy Esys vs C_bulk Sweep',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#fb923c',
        borderWidth: 1.5,
        shadowColor: 'rgba(251, 146, 60, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
      },
      legend: {
        data: ['System Inrush Energy (J)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '10%', right: '5%', bottom: '25%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: capVals,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 'C_bulk (μF)'
      },
      yAxis: {
        type: 'value',
        name: 'Energy (J)',
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
          name: 'System Inrush Energy (J)',
          type: 'line',
          data: energyVals,
          smooth: true,
          lineStyle: { 
            color: '#fb923c', 
            width: 3,
            shadowColor: 'rgba(251, 146, 60, 0.8)',
            shadowBlur: 8
          },
          showSymbol: false,
          markLine: {
            symbol: ['none', 'none'],
            data: [
              {
                yAxis: ntcIn.j_rating,
                lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 },
                label: { formatter: `NTC Rated Limit: ${ntcIn.j_rating} J`, color: '#f87171', position: 'end' }
              }
            ]
          }
        }
      ]
    };
    setChartOption(option);
  };

  const renderXcapChart = (data: XcapResponse) => {
    const timeVals: number[] = [];
    const voltageVals: number[] = [];

    const r = xcapIn.custom_r_m_enabled ? xcapIn.custom_r_m : data.r_rec_m;
    const rc = Math.max(r * 1e6 * (xcapIn.cx_uf * 1e-6), 1e-9);
    const vPeak = data.v_peak;
    const steps = 100;
    const maxT = Math.max(3.0, xcapIn.t_limit * 1.5);

    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * maxT;
      timeVals.push(parseFloat(t.toFixed(3)));
      const v = vPeak * Math.exp(-t / rc);
      voltageVals.push(parseFloat(v.toFixed(1)));
    }

    const option = {
      backgroundColor: 'transparent',
      title: {
        text: 'X-Capacitor Discharge Voltage Decay v(t) Profile',
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        shadowColor: 'rgba(56, 189, 248, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
      },
      legend: {
        data: ['Discharge Residual Voltage v(t) (V)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '10%', right: '5%', bottom: '25%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: timeVals,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 't (s)'
      },
      yAxis: {
        type: 'value',
        name: 'Voltage (V)',
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
          borderColor: 'rgba(56, 189, 248, 0.15)',
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '110%',
          handleStyle: {
            color: '#38bdf8',
            shadowBlur: 5,
            shadowColor: 'rgba(56, 189, 248, 0.5)'
          },
          textStyle: { color: '#94a3b8', fontSize: 9 },
          fillerColor: 'rgba(56, 189, 248, 0.05)',
          dataBackground: {
            lineStyle: { color: '#38bdf8', width: 1 },
            areaStyle: { color: 'rgba(56, 189, 248, 0.02)' }
          },
          selectedDataBackground: {
            lineStyle: { color: '#38bdf8', width: 1.5 },
            areaStyle: { color: 'rgba(56, 189, 248, 0.1)' }
          }
        }
      ],
      series: [
        {
          name: 'Discharge Residual Voltage v(t) (V)',
          type: 'line',
          data: voltageVals,
          smooth: true,
          lineStyle: { 
            color: '#10b981', 
            width: 3,
            shadowColor: 'rgba(16, 185, 129, 0.8)',
            shadowBlur: 8
          },
          showSymbol: false,
          markLine: {
            symbol: ['none', 'none'],
            data: [
              {
                yAxis: xcapIn.v_safe,
                lineStyle: { color: '#f43f5e', type: 'dashed', width: 1.5 },
                label: { formatter: `Safety Threshold ${xcapIn.v_safe}V`, color: '#f43f5e', position: 'end' }
              },
              {
                xAxis: `${xcapIn.t_limit.toFixed(3)}`,
                lineStyle: { color: '#10b981', type: 'dashed', width: 1.5 },
                label: { formatter: `Time Limit ${xcapIn.t_limit}s`, color: '#10b981', position: 'end' }
              }
            ]
          }
        }
      ]
    };
    setChartOption(option);
  };

  useEffect(() => {
    if (activeTab === 'fuse' && isFuseWired) calcFuse();
  }, [fuseIn, activeTab, isFuseWired]);

  useEffect(() => {
    if (activeTab === 'ntc' && isNtcWired) calcNtc();
  }, [ntcIn, activeTab, isNtcWired]);

  useEffect(() => {
    if (activeTab === 'xcap' && isRcWired) calcXcap();
  }, [xcapIn, activeTab, isRcWired]);

  const getMatchedBom = (): BomItem[] => {
    const items: BomItem[] = [];
    if (activeTab === 'fuse' && fuseOut) {
      items.push({
        designator: 'F1',
        calcValue: `I²t > ${fuseOut.i2t_req.toFixed(3)} A²s`,
        stdValue: 'Littelfuse 0215004.MXP (4A / 250V / Slow-Blow)',
        error: 'N/A',
        type: 'Slow-Blow Fuse',
        desc: 'Input overcurrent & explosion-proof fuse with high inrush I²t surge withstand'
      });
    } else if (activeTab === 'ntc' && ntcOut) {
      items.push({
        designator: 'RT1',
        calcValue: `Energy >= ${(ntcOut.e_rec).toFixed(2)} J`,
        stdValue: 'EPCOS B57237S0109M000 (10 Ω / 3.2A / 3.2W)',
        error: 'N/A',
        type: 'Power NTC Thermistor',
        desc: 'Inrush current limiting negative temperature coefficient thermistor'
      });
    } else if (activeTab === 'xcap' && xcapOut) {
      const matchR = findClosestStandard(xcapOut.r_single_m * 1e6, E96);
      items.push({
        designator: 'R_bleed1, R_bleed2',
        calcValue: `${(xcapOut.r_single_m).toFixed(3)} MΩ`,
        stdValue: `${(matchR.value / 1e6).toFixed(3)} MΩ`,
        error: `${matchR.error > 0 ? '+' : ''}${matchR.error}%`,
        type: 'SMD Resistor (E96 / 1206)',
        desc: 'Safety discharge bleeder resistor (creepage & voltage withstand derated)'
      });
      items.push({
        designator: 'Cx',
        calcValue: `${xcapIn.cx_uf} μF`,
        stdValue: `${xcapIn.cx_uf.toFixed(2)} μF / 275VAC`,
        error: '0.0%',
        type: 'X2 Safety Capacitor',
        desc: 'Differential-mode EMI suppression safety film capacitor'
      });
    }
    return items;
  };

  const matchedBom = getMatchedBom();

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
            <h1 className="text-base font-bold text-white tracking-tight">Input Protection & Bleeder Design</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">Verify fuse $I^2t$ inrush surge withstand; calculate power NTC thermal capacity and X-cap safety discharge RC parameters.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleResetLayout}
            className="flex items-center gap-1.5 text-xs bg-[#0b0f19]/80 border-slate-800 hover:bg-slate-900 cursor-pointer text-slate-350 hover:text-white"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            Reset Layout
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 bg-[#0f172a]/30 p-1.5 rounded-xl border border-slate-900 max-w-7xl mx-auto w-full">
        <button
          onClick={() => setParentTab('fuse_center')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold border-0 cursor-pointer transition-all ${
            parentTab === 'fuse_center'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-950/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-805/40'
          }`}
        >
          1. Fuse Selection & Protection
        </button>
        <button
          onClick={() => setParentTab('ntc_center')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold border-0 cursor-pointer transition-all ${
            parentTab === 'ntc_center'
              ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-950/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-805/40'
          }`}
        >
          2. NTC Inrush Suppression
        </button>
        <button
          onClick={() => setParentTab('xcap_center')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold border-0 cursor-pointer transition-all ${
            parentTab === 'xcap_center'
              ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-950/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-805/40'
          }`}
        >
          3. X-Capacitor Bleeder Discharge
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 bg-slate-900/60 p-1 rounded-xl border border-slate-800 max-w-7xl mx-auto w-full">
        {parentTab === 'fuse_center' && (
          <>
            <button
              onClick={() => setFuseSubTab('design')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                fuseSubTab === 'design'
                  ? 'bg-slate-800 text-cyan-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              1.1 Fuse Parameter Design
            </button>
            <button
              onClick={() => setFuseSubTab('schematic')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                fuseSubTab === 'schematic'
                  ? 'bg-slate-800 text-cyan-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              <Maximize2 size={13} />
              1.2 Fuse Circuit Schematic
            </button>
          </>
        )}

        {parentTab === 'ntc_center' && (
          <>
            <button
              onClick={() => setNtcSubTab('design')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                ntcSubTab === 'design'
                  ? 'bg-slate-800 text-purple-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              2.1 NTC Surge Limit Design
            </button>
            <button
              onClick={() => setNtcSubTab('schematic')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                ntcSubTab === 'schematic'
                  ? 'bg-slate-800 text-purple-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              <Maximize2 size={13} />
              2.2 NTC Circuit Schematic
            </button>
          </>
        )}

        {parentTab === 'xcap_center' && (
          <>
            <button
              onClick={() => setXcapSubTab('design')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                xcapSubTab === 'design'
                  ? 'bg-slate-800 text-emerald-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              3.1 RC Bleeder Design
            </button>
            <button
              onClick={() => setXcapSubTab('schematic')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                xcapSubTab === 'schematic'
                  ? 'bg-slate-800 text-emerald-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              <Maximize2 size={13} />
              3.2 RC Bleeder Schematic
            </button>
          </>
        )}
      </div>

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 min-h-0">
        {error && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3 font-mono">Error: {error}</div>}

        {activeTab === 'fuse_schematic' && (
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-6 backdrop-blur-md h-[700px] flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">1.1 Fuse Protection Circuit Sandbox</h3>
                <p className="text-xs text-slate-400 mt-1">Connect the AC/DC source, fuse, series resistance, bulk capacitor, and ground. Full calculations unlock once connectivity is established.</p>
              </div>
              {isFuseWired ? (
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-lg animate-pulse font-mono">✓ Circuit Connected</span>
              ) : (
                <span className="text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-lg font-mono">✗ Circuit Disconnected</span>
              )}
            </div>
            <div className="flex-1 bg-slate-950/80 rounded-lg p-2 overflow-hidden border border-slate-850">
              <InputProtectionSchematicSandbox
                activeTab="fuse"
                onConnectionChange={(wired) => setIsFuseWired(wired)}
                vin={fuseIn.vin}
              />
            </div>
          </div>
        )}

        {activeTab === 'ntc_schematic' && (
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-6 backdrop-blur-md h-[700px] flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">2.1 NTC Inrush Circuit Sandbox</h3>
                <p className="text-xs text-slate-400 mt-1">Connect the power source, power NTC thermistor, bulk capacitor, and ground to unlock thermal calculations.</p>
              </div>
              {isNtcWired ? (
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-lg animate-pulse font-mono">✓ Circuit Connected</span>
              ) : (
                <span className="text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-lg font-mono">✗ Circuit Disconnected</span>
              )}
            </div>
            <div className="flex-1 bg-slate-950/80 rounded-lg p-2 overflow-hidden border border-slate-850">
              <InputProtectionSchematicSandbox
                activeTab="ntc"
                onConnectionChange={(wired) => setIsNtcWired(wired)}
                vin={ntcIn.v_in_max}
              />
            </div>
          </div>
        )}

        {activeTab === 'xcap_schematic' && (
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-6 backdrop-blur-md h-[700px] flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">3.1 RC Safety Bleeder Sandbox</h3>
                <p className="text-xs text-slate-400 mt-1">Connect the AC input, X-capacitor, and parallel discharge resistors across both rails to activate discharge verification.</p>
              </div>
              {isRcWired ? (
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-lg animate-pulse font-mono">✓ Circuit Connected</span>
              ) : (
                <span className="text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-lg font-mono">✗ Circuit Disconnected</span>
              )}
            </div>
            <div className="flex-1 bg-slate-950/80 rounded-lg p-2 overflow-hidden border border-slate-850">
              <InputProtectionSchematicSandbox
                activeTab="rc"
                onConnectionChange={(wired) => setIsRcWired(wired)}
                vin={xcapIn.vac}
              />
            </div>
          </div>
        )}

        {['fuse', 'ntc', 'xcap'].includes(activeTab) && (
          <DragDeck
        isDesktop={isDesktop}
        leftSpan={leftSpan}
        rightSpan={rightSpan}
        leftCards={leftCards}
        rightCards={rightCards}
        draggedKey={draggedKey}
        renderCard={(key) => {
          const isWired = activeTab === 'fuse' ? isFuseWired : (activeTab === 'ntc' ? isNtcWired : isRcWired);
          return (
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
                <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 p-4">
                  <Card className="bg-slate-950/40 border-slate-800/80 p-4">
                    <div className="flex items-center justify-between mb-3 border-b border-slate-800/60 pb-2">
                      <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wide flex items-center gap-2">
                        Operating Conditions & Limits
                      </h3>
                    </div>

                    <div className="space-y-4">
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                        <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                          <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                          Input Power Supply
                        </div>
                        {activeTab === 'fuse' && (
                          <div className="space-y-3">
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Rated Input Voltage Vin [V]</label>
                              <input type="number" value={fuseIn.vin} onChange={e => setFuseIn({ ...fuseIn, vin: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Voltage Type (AC/DC)</label>
                              <select value={fuseIn.is_ac ? 'ac' : 'dc'} onChange={e => setFuseIn({ ...fuseIn, is_ac: e.target.value === 'ac' })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white">
                                <option value="ac">AC RMS Voltage</option>
                                <option value="dc">DC Constant Voltage</option>
                              </select>
                            </div>
                          </div>
                        )}
                        {activeTab === 'ntc' && (
                          <div className="space-y-3">
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Max Input Peak Voltage Vpk [V]</label>
                              <input type="number" value={ntcIn.v_in_max} onChange={e => setNtcIn({ ...ntcIn, v_in_max: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                            </div>
                            <div>
                              <label className="text-[10px] text-slate-400 block mb-1">Input Source Type</label>
                              <select value={ntcIn.is_ac ? 'ac' : 'dc'} onChange={e => setNtcIn({ ...ntcIn, is_ac: e.target.value === 'ac' })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white">
                                <option value="ac">AC Source (Peak Voltage at 90°)</option>
                                <option value="dc">DC Step Turn-On</option>
                              </select>
                            </div>
                          </div>
                        )}
                        {activeTab === 'xcap' && (
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">AC RMS Voltage Vac [V]</label>
                            <input type="number" value={xcapIn.vac} onChange={e => setXcapIn({ ...xcapIn, vac: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                          </div>
                        )}
                      </div>

                      {(activeTab === 'fuse' || activeTab === 'ntc') && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Bulk Filter Capacitor C_bulk
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Total Capacitance C_bulk [μF]</label>
                            <input type="number" value={activeTab === 'fuse' ? fuseIn.c_bulk_uf : ntcIn.c_bulk_uf} onChange={e => {
                              const val = parseFloat(e.target.value) || 0;
                              if (activeTab === 'fuse') setFuseIn({ ...fuseIn, c_bulk_uf: val });
                              else setNtcIn({ ...ntcIn, c_bulk_uf: val });
                            }} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                          </div>
                        </div>
                      )}

                      {activeTab === 'fuse' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Series Resistance Rs
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Equivalent Loop Resistance Rs [Ω]</label>
                            <input type="number" step="0.5" value={fuseIn.r_series} onChange={e => setFuseIn({ ...fuseIn, r_series: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                            <span className="text-[9px] text-slate-500 mt-1 block">Internal and trace resistance limiting peak surge</span>
                          </div>
                        </div>
                      )}

                      {activeTab === 'fuse' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            Pulse Derating Factor (I²t Factor)
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Cyclic Surge Derating Ratio (f)</label>
                            <input type="number" step="0.05" value={fuseIn.factor} onChange={e => setFuseIn({ ...fuseIn, factor: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                            <span className="text-[9px] text-slate-500 mt-1 block">Typical: 0.30 for 100,000 turn-on cycles</span>
                          </div>
                          <div className="border border-slate-800/80 rounded p-2 bg-[#090d16]/60 text-[9px] text-slate-400 leading-relaxed font-mono">
                            <span className="font-bold text-slate-300 block mb-0.5">Datasheet Criteria:</span>
                            1. Datasheet rating: <strong className="text-white">Nominal Melting I²t [A²s]</strong>.<br />
                            2. Selection rule: <strong className="text-pink-400">I²t_act &lt; f · I²t_nominal</strong>.
                          </div>
                        </div>
                      )}

                      {activeTab === 'ntc' && (
                        <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                          <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                            <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                            NTC Joule Rating Limit
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Max Energy Rating [J]</label>
                            <input type="number" value={ntcIn.j_rating} onChange={e => setNtcIn({ ...ntcIn, j_rating: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                          </div>
                        </div>
                      )}

                    {activeTab === 'ntc' && (
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                        <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                          <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                          Dissipation & Cooling Constant
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400 block mb-1">Thermal Dissipation Constant (mW/°C)</label>
                          <input type="number" value={ntcIn.diss_mw} onChange={e => setNtcIn({ ...ntcIn, diss_mw: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                        </div>
                      </div>
                    )}

                    {activeTab === 'xcap' && (
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                        <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                          <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                          X-Capacitor Specifications
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">X-Cap Capacitance Cx [μF]</label>
                            <input type="number" step="0.1" value={xcapIn.cx_uf} onChange={e => setXcapIn({ ...xcapIn, cx_uf: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Series Bleed Count N</label>
                            <input type="number" min="1" value={xcapIn.n_series} onChange={e => setXcapIn({ ...xcapIn, n_series: parseInt(e.target.value) || 1 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                          </div>
                        </div>
                      </div>
                    )}

                    {activeTab === 'xcap' && (
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                        <div className="font-semibold text-slate-300 border-b border-slate-800/60 pb-1.5 mb-2 text-xs flex items-center gap-1.5 select-none">
                          <span className="w-1.5 h-3 bg-blue-500 rounded-full inline-block"></span>
                          Discharge Time & Safety Touch Limit
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Discharge Time Limit [s]</label>
                            <input type="number" value={xcapIn.t_limit} onChange={e => setXcapIn({ ...xcapIn, t_limit: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-1">Safe Touch Limit [V]</label>
                            <input type="number" value={xcapIn.v_safe} onChange={e => setXcapIn({ ...xcapIn, v_safe: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                          </div>
                          <div className="col-span-2 flex items-center gap-2 pt-1">
                            <input type="checkbox" id="custom_r_chk" checked={xcapIn.custom_r_m_enabled} onChange={e => setXcapIn({ ...xcapIn, custom_r_m_enabled: e.target.checked })} className="rounded bg-slate-950 border-slate-800 text-blue-500 focus:ring-0 focus:ring-offset-0 h-3.5 w-3.5 cursor-pointer" />
                            <label htmlFor="custom_r_chk" className="text-[10px] text-slate-400 select-none cursor-pointer">Custom Total Bleed Resistance</label>
                          </div>
                          {xcapIn.custom_r_m_enabled && (
                            <div className="col-span-2">
                              <label className="text-[10px] text-slate-400 block mb-1">Resistance [MΩ]</label>
                              <input type="number" step="0.1" value={xcapIn.custom_r_m} onChange={e => setXcapIn({ ...xcapIn, custom_r_m: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white" />
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            )}

            {key === 'results' && (
              <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 p-4">
                {renderWiredCheck(isWired, (
                  <div className="space-y-6">
                {activeTab === 'fuse' && fuseOut && (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span>Loop impedance matched: Peak inrush current is {fuseOut.i_peak.toFixed(1)} A. Recommended fuse melting I²t &gt; {fuseOut.i2t_req.toFixed(4)} A²s.</span>
                  </div>
                )}

                {activeTab === 'ntc' && ntcOut && (
                  ntcOut.over_energy ? (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400 animate-pulse">
                      <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="font-bold block">NTC Thermal Stress Overload Risk</span>
                        <span className="mt-1 block">Inrush energy of {ntcOut.e_sys.toFixed(1)} J exceeds rated limit ({ntcIn.j_rating} J). Choose a higher-joule NTC or implement relay bypass.</span>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>NTC inrush rating safe: Inrush thermal energy of {ntcOut.e_sys.toFixed(2)} J is within limits. Recommended cooling interval is {ntcOut.t_cool_s.toFixed(0)} s.</span>
                    </div>
                  )
                )}

                {activeTab === 'xcap' && xcapOut && (
                  xcapOut.is_passed ? (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-2 text-xs text-emerald-400">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>Discharge time compliant: Bleed resistance meets IEC 60950/62368 safety standards. Standby loss is ~{xcapOut.p_loss_mw.toFixed(1)} mW.</span>
                    </div>
                  ) : (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 text-xs text-red-400 animate-pulse">
                      <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="font-bold block">Safety Hazard: Discharge Overlimit</span>
                        <span className="mt-1 block">Bleed resistance is too high; voltage remains above {xcapIn.v_safe}V after {xcapIn.t_limit} s. Electric shock risk present. Reduce bleeder resistance.</span>
                      </div>
                    </div>
                  )
                )}

                <div className="grid grid-cols-2 gap-4">
                  {activeTab === 'fuse' && fuseOut && (
                    <>
                      <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-950/20 to-blue-950/20 border border-cyan-500/20 flex flex-col">
                        <span className="text-[10px] text-cyan-400 font-semibold tracking-wider uppercase">Calculated Inrush I²t</span>
                        <span className="text-xl font-black text-cyan-300 font-mono">
                          {fuseOut.i2t_calc.toFixed(4)} A²s
                        </span>
                        <span className="text-[10px] text-slate-500 mt-1">Time constant τ: {fuseOut.tau_ms.toFixed(2)} ms</span>
                      </div>

                      <div className="p-4 rounded-xl bg-gradient-to-br from-purple-950/20 to-indigo-950/20 border border-purple-500/20 flex flex-col">
                        <span className="text-[10px] text-purple-400 font-semibold tracking-wider uppercase">Min Rated Melting I²t</span>
                        <span className="text-xl font-black text-purple-300 font-mono">
                          &gt; {fuseOut.i2t_req.toFixed(4)} A²s
                        </span>
                        <span className="text-[10px] text-slate-500 mt-1">Peak inrush I_peak: {fuseOut.i_peak.toFixed(1)} A</span>
                      </div>
                    </>
                  )}

                  {activeTab === 'ntc' && ntcOut && (
                    <>
                      <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-950/20 to-blue-950/20 border border-cyan-500/20 flex flex-col">
                        <span className="text-[10px] text-cyan-400 font-semibold tracking-wider uppercase">Capacitor Inrush Energy E_sys</span>
                        <span className={`text-xl font-black font-mono ${ntcOut.over_energy ? 'text-red-400' : 'text-cyan-300'}`}>
                          {ntcOut.e_sys.toFixed(2)} J
                        </span>
                        <span className="text-[10px] text-slate-500 mt-1">NTC Candidate Rating: {ntcIn.j_rating} J</span>
                      </div>

                      <div className="p-4 rounded-xl bg-gradient-to-br from-purple-950/20 to-indigo-950/20 border border-purple-500/20 flex flex-col">
                        <span className="text-[10px] text-purple-400 font-semibold tracking-wider uppercase">Min Recommended Cooling Time</span>
                        <span className="text-xl font-black text-purple-300 font-mono">
                          ~ {ntcOut.t_cool_s.toFixed(0)} s
                        </span>
                        <span className="text-[10px] text-slate-500 mt-1">Thermal time constant τ: {ntcOut.tau_s.toFixed(1)} s</span>
                      </div>
                    </>
                  )}

                  {activeTab === 'xcap' && xcapOut && (
                    <>
                      <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-950/20 to-blue-950/20 border border-cyan-500/20 flex flex-col">
                        <span className="text-[10px] text-cyan-400 font-semibold tracking-wider uppercase">Actual Total Resistance R_act</span>
                        <span className="text-xl font-black text-cyan-300 font-mono">
                          {xcapOut.r_actual_m.toFixed(3)} MΩ
                        </span>
                        <span className="text-[10px] text-slate-500 mt-1">Max allowable R_max: {xcapOut.r_max_m.toFixed(3)} MΩ</span>
                      </div>

                      <div className="p-4 rounded-xl bg-gradient-to-br from-purple-950/20 to-indigo-950/20 border border-purple-500/20 flex flex-col">
                        <span className="text-[10px] text-purple-400 font-semibold tracking-wider uppercase">AC Standby Loss Ploss</span>
                        <span className="text-xl font-black text-purple-300 font-mono">
                          {xcapOut.p_loss_mw.toFixed(2)} mW
                        </span>
                        <span className="text-[10px] text-slate-500 mt-1">Per-resistor value (R/N): {xcapOut.r_single_m.toFixed(3)} MΩ</span>
                      </div>
                    </>
                  )}
                </div>

                <Card className="bg-slate-900/40 border-slate-800/80">
                  <CardContent className="pt-4 h-[300px]">
                    <ReactECharts notMerge={true} option={chartOption} style={{ height: '100%', width: '100%' }} />
                  </CardContent>
                </Card>

                <Card className="bg-slate-900/40 border-slate-800/80">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-bold text-slate-300 border-l-2 border-blue-500 pl-2">
                      Input Protection Commercial BOM Matches (E96/E24)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    {matchedBom.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse text-[11px] text-slate-300">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-400">
                              <th className="py-2 font-semibold">Designator</th>
                              <th className="py-2 font-semibold">Calculated</th>
                              <th className="py-2 font-semibold">Recommended Commercial</th>
                              <th className="py-2 font-semibold text-center">Error</th>
                              <th className="py-2 font-semibold">Package / Type</th>
                              <th className="py-2 font-semibold">Function & Description</th>
                            </tr>
                          </thead>
                          <tbody>
                            {matchedBom.map((item, idx) => (
                              <tr key={idx} className="border-b border-slate-900/50 hover:bg-slate-900/10 text-slate-400">
                                <td className="py-2.5 font-mono text-slate-200">{item.designator}</td>
                                <td className="py-2.5 font-mono">{item.calcValue}</td>
                                <td className="py-2.5 font-mono text-cyan-400 font-bold">{item.stdValue}</td>
                                <td className="py-2.5 font-mono text-center">{item.error}</td>
                                <td className="py-2.5 font-medium">{item.type}</td>
                                <td className="py-2.5 text-[10px] leading-relaxed">{item.desc}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center py-6 text-slate-500 text-xs">No BOM recommendations available</div>
                    )}
                  </CardContent>
                </Card>
                  </div>
                ))}
              </div>
            )}
          </DragCard>
          );
        }}
        onDropOnColumn={handleDropOnColumn}
      />
    )}
      </div>
    </div>
  );
}
