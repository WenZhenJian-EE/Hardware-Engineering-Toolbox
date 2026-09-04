import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import TvsZenerSchematicSandbox from './TvsZenerSchematicSandbox';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import { 
  ArrowLeft, 
  ShieldAlert, 
  CheckCircle2, 
  Maximize2,
  BookOpen,
  TrendingUp
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

interface ZenerResponse {
  r_max: number;
  pr_max: number;
  pz_max: number;
  is_passed: boolean;
  warn_msg: string;
}

interface TvsResponse {
  r_dyn: number;
  vc_act: number;
  ipp_act: number;
  p_act: number;
  is_overload: boolean;
  status_msg: string;
}

interface BomItem {
  designator: string;
  calcValue: string;
  stdValue: string;
  error: string;
  type: string;
  desc: string;
}

type TabType = 'zener' | 'zener_schematic' | 'tvs' | 'tvs_schematic';
type ParentTab = 'zener_center' | 'tvs_center';
type SubTab = 'design' | 'schematic';

export default function TvsZenerPanel({ onBack }: { onBack: () => void }) {
  const [parentTab, setParentTab] = useTabHistoryState<ParentTab>('zener_center', 'parentTab');
  const [zenerSubTab, setZenerSubTab] = useTabHistoryState<SubTab>('design', 'zenerSubTab');
  const [tvsSubTab, setTvsSubTab] = useTabHistoryState<SubTab>('design', 'tvsSubTab');

  const activeTab: TabType = parentTab === 'zener_center'
    ? (zenerSubTab === 'design' ? 'zener' : 'zener_schematic')
    : (tvsSubTab === 'design' ? 'tvs' : 'tvs_schematic');
  
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);

  // Tab 1: Zener
  const [zenerIn, setZenerIn] = useState({ vin_min: 10, vin_max: 24, vz: 5.1, iz_min_ma: 5, iload_min_ma: 0, iload_max_ma: 50, r_sel: 100, p_max_w: 0.5, zzt: 15 });
  const [zenerOut, setZenerOut] = useState<ZenerResponse | null>(null);

  // Tab 2: TVS
  const [tvsIn, setTvsIn] = useState({ v_surge: 2000, r_src: 2.0, vrwm: 24, vbr: 26.7, vc_spec: 38.9, ipp_spec: 15.4, pppm_rated: 600, pulse_type: '10/1000us' });
  const [tvsOut, setTvsOut] = useState<TvsResponse | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [chartOption, setChartOption] = useState<any>({});
  const [isZenerWired, setIsZenerWired] = useState(false);
  const [isTvsWired, setIsTvsWired] = useState(false);

  useEffect(() => {
    const checkSavedWired = (tab: 'zener' | 'tvs') => {
      const savedWires = localStorage.getItem(`toolbox_tvszener_layout_wires_${tab}`);
      if (!savedWires) return false;
      try {
        const wires = JSON.parse(savedWires);
        if (tab === 'zener') {
          const conns = [
            { from: 'Vin.P', to: 'R_limit.Pin1' },
            { from: 'R_limit.Pin2', to: 'Dz.K' },
            { from: 'Dz.K', to: 'RL.Pin1' },
            { from: 'Vin.N', to: 'GND.Pin' },
            { from: 'Dz.A', to: 'GND.Pin' },
            { from: 'RL.Pin2', to: 'GND.Pin' }
          ];
          return conns.every(c => 
            wires.some((w: any) => 
              (w.from === c.from && w.to === c.to) || (w.from === c.to && w.to === c.from)
            )
          );
        } else {
          const conns = [
            { from: 'Vsurge.P', to: 'R_src.Pin1' },
            { from: 'R_src.Pin2', to: 'L_line.Pin1' },
            { from: 'L_line.Pin2', to: 'TVS.K' },
            { from: 'TVS.K', to: 'EUT.Pin1' },
            { from: 'Vsurge.N', to: 'GND.Pin' },
            { from: 'TVS.A', to: 'GND.Pin' },
            { from: 'EUT.Pin2', to: 'GND.Pin' }
          ];
          return conns.every(c => 
            wires.some((w: any) => 
              (w.from === c.from && w.to === c.to) || (w.from === c.to && w.to === c.from)
            )
          );
        }
      } catch (e) {
        return false;
      }
    };

    setIsZenerWired(checkSavedWired('zener'));
    setIsTvsWired(checkSavedWired('tvs'));
  }, []);

  const renderWiredCheck = (wired: boolean, children: React.ReactNode) => {
    if (!wired) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center p-6 bg-slate-950/20 rounded-xl border border-dashed border-slate-850/60">
          <ShieldAlert className="w-8 h-8 text-amber-500 mb-2 animate-pulse" />
          <span className="text-[11px] font-semibold text-slate-350">Circuit Wiring Incomplete</span>
          <p className="text-[9px] text-slate-500 max-w-[240px] mt-1">Please navigate to the schematic tab to complete all pin connections. This panel will unlock automatically once wired.</p>
        </div>
      );
    }
    return children;
  };

  const getLayoutConfigForTab = (tab: TabType) => {
    switch (tab) {
      case 'zener':
        return {
          defaultCards: ['input', 'results', 'bom', 'charts', 'drc'],
          defaultColumns: { input: 'left', results: 'right', bom: 'right', charts: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, results: 8, bom: 8, charts: 8, drc: 8 },
          defaultHeights: { input: 500, results: 240, bom: 180, charts: 300, drc: 180 }
        };
      case 'tvs':
        return {
          defaultCards: ['input', 'results', 'bom', 'charts', 'drc'],
          defaultColumns: { input: 'left', results: 'right', bom: 'right', charts: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, results: 8, bom: 8, charts: 8, drc: 8 },
          defaultHeights: { input: 480, results: 240, bom: 180, charts: 300, drc: 180 }
        };
      case 'zener_schematic':
      case 'tvs_schematic':
        return {
          defaultCards: ['sandbox'],
          defaultColumns: { sandbox: 'left' } as Record<string, 'left' | 'right'>,
          defaultSpans: { sandbox: 12 },
          defaultHeights: { sandbox: 650 }
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
    panelKey: 'layout_tvs_zener_v4',
    activeTab: activeTab,
    defaultCards: currentLayoutConfig.defaultCards,
    defaultColumns: currentLayoutConfig.defaultColumns,
    defaultSpans: currentLayoutConfig.defaultSpans,
    defaultHeights: currentLayoutConfig.defaultHeights
  });

  const calcZener = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/tvs_zener/zener', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vin_min: zenerIn.vin_min,
          vin_max: zenerIn.vin_max,
          vz: zenerIn.vz,
          iz_min_ma: zenerIn.iz_min_ma,
          iload_min_ma: zenerIn.iload_min_ma,
          iload_max_ma: zenerIn.iload_max_ma,
          r_sel: zenerIn.r_sel,
          p_max_w: zenerIn.p_max_w,
          zzt: zenerIn.zzt
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        if (errData.detail && Array.isArray(errData.detail)) {
          throw new Error(errData.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', '));
        }
        throw new Error(errData.detail || 'Zener calculation failed');
      }
      const data = await response.json();
      setZenerOut(data);
      renderZenerChart(data);
    } catch (e: any) {
      setError(e.message || String(e));
      setZenerOut(null);
    }
  };

  const calcTvs = async () => {
    setError(null);
    try {
      const response = await apiFetch('/api/calculate/tvs_zener/tvs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_surge: tvsIn.v_surge,
          r_src: tvsIn.r_src,
          vbr: tvsIn.vbr,
          vc_spec: tvsIn.vc_spec,
          ipp_spec: tvsIn.ipp_spec,
          pppm_rated: tvsIn.pppm_rated,
          pulse_type: tvsIn.pulse_type
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        if (errData.detail && Array.isArray(errData.detail)) {
          throw new Error(errData.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join(', '));
        }
        throw new Error(errData.detail || 'TVS clamping calculation failed');
      }
      const data = await response.json();
      setTvsOut(data);
      renderTvsChart(data);
    } catch (e: any) {
      setError(e.message || String(e));
      setTvsOut(null);
    }
  };

  const renderZenerChart = (data: ZenerResponse) => {
    const vinVals: number[] = [];
    const pzPower: number[] = [];
    const prPower: number[] = [];

    const startVin = zenerIn.vin_min;
    const endVin = zenerIn.vin_max * 1.25;
    const steps = 40;
    const r = Math.max(0.001, zenerIn.r_sel || 100);
    for (let i = 0; i <= steps; i++) {
      const vin = startVin + (i / steps) * (endVin - startVin);
      vinVals.push(parseFloat(vin.toFixed(1)));
      
      const iRes = (vin - zenerIn.vz) / r;
      const iZ = iRes - (zenerIn.iload_min_ma * 1e-3);
      const pz = zenerIn.vz * Math.max(0, iZ);
      const pr = iRes * iRes * r;

      pzPower.push(parseFloat(pz.toFixed(3)));
      prPower.push(parseFloat(pr.toFixed(2)));
    }

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#0ea5e9',
        borderWidth: 1.5,
        shadowColor: 'rgba(14, 165, 233, 0.3)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 10 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
      },
      legend: {
        data: ['Zener Dissipation Pz (W)', 'Series Resistor Pr (W)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '8%', right: '8%', bottom: '25%', top: '12%', containLabel: true },
      xAxis: {
        type: 'category',
        data: vinVals,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 8 },
        name: 'Vin(V)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 }
      },
      yAxis: {
        type: 'value',
        name: 'Power (W)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 8 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        {
          type: 'slider',
          start: 0,
          end: 100,
          bottom: 25,
          height: 16,
          textStyle: { color: '#94a3b8', fontSize: 8 },
          borderColor: 'rgba(255,255,255,0.04)',
          fillerColor: 'rgba(14, 165, 233, 0.15)'
        }
      ],
      series: [
        {
          name: 'Zener Dissipation Pz (W)',
          type: 'line',
          data: pzPower,
          smooth: true,
          lineStyle: {
            color: '#f43f5e',
            width: 3,
            shadowBlur: 8,
            shadowColor: 'rgba(244, 63, 94, 0.6)'
          },
          showSymbol: false
        },
        {
          name: 'Series Resistor Pr (W)',
          type: 'line',
          data: prPower,
          smooth: true,
          lineStyle: {
            color: '#0ea5e9',
            width: 3,
            shadowBlur: 8,
            shadowColor: 'rgba(14, 165, 233, 0.6)'
          },
          showSymbol: false
        }
      ]
    };
    setChartOption(option);
  };

  const renderTvsChart = (data: TvsResponse) => {
    const tVals: number[] = [];
    const iSurge: number[] = [];
    const vClamp: number[] = [];

    const steps = 100;
    const tmax = 50.0;
    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * tmax;
      tVals.push(parseFloat(t.toFixed(1)));

      const iPulse = data ? data.ipp_act * (t / 8.0) * Math.exp(1 - t / 8.0) : 0;
      const vTvs = tvsIn.vbr + (data?.r_dyn ?? 0) * Math.max(0, iPulse);

      iSurge.push(parseFloat(iPulse.toFixed(2)));
      vClamp.push(parseFloat(vTvs.toFixed(2)));
    }

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#eab308',
        borderWidth: 1.5,
        shadowColor: 'rgba(234, 179, 8, 0.3)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 10 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
      },
      legend: {
        data: ['Surge Current Ipp (A)', 'Clamping Voltage Vc (V)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '8%', right: '8%', bottom: '25%', top: '12%', containLabel: true },
      xAxis: {
        type: 'category',
        data: tVals.map(t => `${t}μs`),
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 8 }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Current (A)',
          nameTextStyle: { color: '#eab308', fontSize: 8 },
          axisLabel: { color: '#eab308', fontSize: 8 },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
        },
        {
          type: 'value',
          name: 'Voltage (V)',
          nameTextStyle: { color: '#ec4899', fontSize: 8 },
          axisLabel: { color: '#ec4899', fontSize: 8 },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          splitLine: { show: false }
        }
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        {
          type: 'slider',
          start: 0,
          end: 100,
          bottom: 25,
          height: 16,
          textStyle: { color: '#94a3b8', fontSize: 8 },
          borderColor: 'rgba(255,255,255,0.04)',
          fillerColor: 'rgba(234, 179, 8, 0.15)'
        }
      ],
      series: [
        {
          name: 'Surge Current Ipp (A)',
          type: 'line',
          yAxisIndex: 0,
          data: iSurge,
          smooth: true,
          lineStyle: {
            color: '#eab308',
            width: 3,
            shadowBlur: 8,
            shadowColor: 'rgba(234, 179, 8, 0.6)'
          },
          showSymbol: false
        },
        {
          name: 'Clamping Voltage Vc (V)',
          type: 'line',
          yAxisIndex: 1,
          data: vClamp,
          smooth: true,
          lineStyle: {
            color: '#ec4899',
            width: 3,
            shadowBlur: 8,
            shadowColor: 'rgba(236, 72, 153, 0.6)'
          },
          showSymbol: false
        }
      ]
    };
    setChartOption(option);
  };

  useEffect(() => {
    if (activeTab === 'zener' && isZenerWired) {
      calcZener();
    } else if (activeTab === 'tvs' && isTvsWired) {
      calcTvs();
    }
  }, [zenerIn, tvsIn, activeTab, isZenerWired, isTvsWired]);

  const getMatchedBom = (): BomItem[] => {
    const items: BomItem[] = [];
    if (activeTab === 'zener' && zenerOut) {
      const rVal = zenerIn.r_sel;
      const match = findClosestStandard(rVal, E96);
      items.push({
        designator: 'R_limit',
        calcValue: `${rVal.toFixed(1)} Ω`,
        stdValue: `${match.value.toFixed(1)} Ω`,
        error: `${match.error > 0 ? '+' : ''}${match.error}%`,
        type: 'Resistor (E96)',
        desc: `Zener series current limiting resistor (recommended rating: ${(zenerOut.pr_max * 1.5).toFixed(2)} W)`
      });
    }
    return items;
  };

  const bomList = getMatchedBom();

  const renderZenerInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Minimum Input Vin(min) [V]</label>
          <input type="number" value={zenerIn.vin_min} onChange={e => setZenerIn({ ...zenerIn, vin_min: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Maximum Input Vin(max) [V]</label>
          <input type="number" value={zenerIn.vin_max} onChange={e => setZenerIn({ ...zenerIn, vin_max: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550 font-bold text-pink-400">Nominal Zener Voltage Vz [V]</label>
          <input type="number" value={zenerIn.vz} onChange={e => setZenerIn({ ...zenerIn, vz: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Knee Current Izk / Izt [mA]</label>
          <input type="number" value={zenerIn.iz_min_ma} onChange={e => setZenerIn({ ...zenerIn, iz_min_ma: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Minimum Load Io(min) [mA]</label>
          <input type="number" value={zenerIn.iload_min_ma} onChange={e => setZenerIn({ ...zenerIn, iload_min_ma: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Maximum Load Io(max) [mA]</label>
          <input type="number" value={zenerIn.iload_max_ma} onChange={e => setZenerIn({ ...zenerIn, iload_max_ma: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550 font-bold text-blue-400">Current Limiting Resistor R [Ω]</label>
          <input type="number" value={zenerIn.r_sel} onChange={e => setZenerIn({ ...zenerIn, r_sel: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550 font-bold text-emerald-400">Rated Dissipation Pd [W]</label>
          <input type="number" step="0.1" value={zenerIn.p_max_w} onChange={e => setZenerIn({ ...zenerIn, p_max_w: parseFloat(e.target.value) || 0.5 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="border border-slate-800/80 rounded-lg p-2.5 bg-[#090d16]/60 text-[9px] text-slate-400 space-y-1.5">
        <div className="font-bold text-slate-300 border-b border-slate-800 pb-1 flex items-center justify-between">
          <span>📖 Common Zener Diode Datasheet Quick Reference:</span>
          <span className="text-[8px] text-pink-500 font-mono font-normal">Typical Values</span>
        </div>
        <div className="space-y-1 font-mono leading-relaxed text-slate-350">
          <div>• <strong className="text-white">1N4733A</strong> (1W): Vz = 5.1V, Izt = 49mA, Izk = 1.0mA, Zzt = 7Ω</div>
          <div>• <strong className="text-white">BZX84C-5V1</strong> (350mW): Vz = 5.1V, Izt = 5.0mA, Izk = 1.0mA, Zzt = 60Ω</div>
          <div>• <strong className="text-white">BZX55C-12V</strong> (500mW): Vz = 12V, Izt = 5.0mA, Izk = 1.0mA, Zzt = 25Ω</div>
        </div>
      </div>
    </div>
  );

  const renderTvsInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550 font-bold text-yellow-500">Peak Surge Voltage V_surge (V)</label>
          <input type="number" value={tvsIn.v_surge} onChange={e => setTvsIn({ ...tvsIn, v_surge: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Source Impedance R_src (Ω)</label>
          <input type="number" value={tvsIn.r_src} onChange={e => setTvsIn({ ...tvsIn, r_src: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="border border-slate-850 rounded-lg p-2.5 bg-slate-900/10 space-y-3 border-t border-slate-800 pt-3">
        <span className="text-[9px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Datasheet Rated TVS Parameters</span>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Stand-off Voltage VRWM [V]</label>
            <input type="number" value={tvsIn.vrwm} onChange={e => setTvsIn({ ...tvsIn, vrwm: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Minimum Breakdown VBR(min) [V]</label>
            <input type="number" value={tvsIn.vbr} onChange={e => setTvsIn({ ...tvsIn, vbr: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Maximum Clamping Voltage Vc [V]</label>
            <input type="number" value={tvsIn.vc_spec} onChange={e => setTvsIn({ ...tvsIn, vc_spec: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Maximum Pulse Current Ipp [A]</label>
            <input type="number" value={tvsIn.ipp_spec} onChange={e => setTvsIn({ ...tvsIn, ipp_spec: parseFloat(e.target.value) || 0 })} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Rated Peak Pulse Power Pppm [W]</label>
          <input type="number" value={tvsIn.pppm_rated} onChange={e => setTvsIn({ ...tvsIn, pppm_rated: parseFloat(e.target.value) || 0 })} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="border border-slate-800/80 rounded-lg p-2.5 bg-[#090d16]/60 text-[9px] text-slate-400 space-y-1.5">
        <div className="font-bold text-slate-300 border-b border-slate-800 pb-1 flex items-center justify-between">
          <span>📖 Common 24V Operating Voltage TVS Reference (Littelfuse):</span>
          <span className="text-[8px] text-yellow-500 font-mono font-normal">Bidirectional CA / Unidirectional A</span>
        </div>
        <div className="space-y-1 font-mono leading-relaxed text-slate-350">
          <div>• <strong className="text-white">SMAJ24CA</strong> (400W): VRWM=24V, VBR=26.7V, Vc=38.9V, Ipp=10.3A</div>
          <div>• <strong className="text-white">SMBJ24CA</strong> (600W): VRWM=24V, VBR=26.7V, Vc=38.9V, Ipp=15.4A</div>
          <div>• <strong className="text-white">SMCJ24CA</strong> (1500W): VRWM=24V, VBR=26.7V, Vc=38.9V, Ipp=38.6A</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
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
            <h1 className="text-base font-bold text-white tracking-tight">TVS / Zener Overvoltage Protection Sizing</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">Calculate Zener worst-case dissipation & series ballast resistor; verify TVS surge peak power, clamping voltage & junction thermal limits.</p>
          </div>
        </div>

        <button
          onClick={handleResetLayout}
          className="flex items-center space-x-2 bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-350 px-4 py-2 rounded-lg text-xs transition cursor-pointer"
        >
          <span>Reset Layout</span>
        </button>
      </div>

      <div className="flex flex-wrap gap-2 bg-[#0f172a]/30 p-1.5 rounded-xl border border-slate-900 max-w-7xl mx-auto w-full">
        <button
          onClick={() => setParentTab('zener_center')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold border-0 cursor-pointer transition-all ${
            parentTab === 'zener_center'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-950/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
          }`}
        >
          1. Zener Diode Protection & Regulation Center
        </button>
        <button
          onClick={() => setParentTab('tvs_center')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold border-0 cursor-pointer transition-all ${
            parentTab === 'tvs_center'
              ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-950/20'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
          }`}
        >
          2. TVS Transient Overvoltage Protection Center
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 bg-slate-900/60 p-1 rounded-xl border border-slate-800 max-w-7xl mx-auto w-full">
        {parentTab === 'zener_center' ? (
          <>
            <button
              onClick={() => setZenerSubTab('design')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                zenerSubTab === 'design'
                  ? 'bg-slate-800 text-cyan-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              1.1 Zener Sizing & Calculation
            </button>
            <button
              onClick={() => setZenerSubTab('schematic')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                zenerSubTab === 'schematic'
                  ? 'bg-slate-800 text-cyan-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              <Maximize2 size={13} />
              1.2 Zener Schematic Wiring
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => setTvsSubTab('design')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                tvsSubTab === 'design'
                  ? 'bg-slate-800 text-purple-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              2.1 TVS Surge Sizing & Calculation
            </button>
            <button
              onClick={() => setTvsSubTab('schematic')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold border-0 cursor-pointer transition-colors ${
                tvsSubTab === 'schematic'
                  ? 'bg-slate-800 text-purple-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/40'
              }`}
            >
              <Maximize2 size={13} />
              2.2 TVS Schematic Wiring
            </button>
          </>
        )}
      </div>

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 min-h-0">
        {error && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3 font-mono">Error: {error}</div>}

        {activeTab === 'zener_schematic' && (
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-6 backdrop-blur-md h-[700px] flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">1.1 Zener Diode Physical Wiring Sandbox</h3>
                <p className="text-xs text-slate-400 mt-1">Connect the DC source, series resistor, Zener diode, load resistor, and ground. Wiring unlocks full design metrics and DRC checks.</p>
              </div>
              {isZenerWired ? (
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-lg animate-pulse font-mono">✓ Circuit Connected</span>
              ) : (
                <span className="text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-lg font-mono">✗ Circuit Disconnected</span>
              )}
            </div>
            <div className="flex-1 bg-slate-950/80 rounded-lg p-2 overflow-hidden border border-slate-850">
              <TvsZenerSchematicSandbox
                activeTab="zener"
                onConnectionChange={(wired) => setIsZenerWired(wired)}
                vinZener={zenerIn.vin_max}
                voutZener={zenerIn.vz}
                rLimit={zenerIn.r_sel}
              />
            </div>
          </div>
        )}

        {activeTab === 'tvs_schematic' && (
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-6 backdrop-blur-md h-[700px] flex flex-col gap-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">2.1 TVS Surge Protection Physical Wiring Sandbox</h3>
                <p className="text-xs text-slate-400 mt-1">Connect surge source, line impedance, TVS diode, load, and ground. Wiring unlocks full design calculations and DRC validation.</p>
              </div>
              {isTvsWired ? (
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-lg animate-pulse font-mono">✓ Circuit Connected</span>
              ) : (
                <span className="text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-lg font-mono">✗ Circuit Disconnected</span>
              )}
            </div>
            <div className="flex-1 bg-slate-950/80 rounded-lg p-2 overflow-hidden border border-slate-850">
              <TvsZenerSchematicSandbox
                activeTab="tvs"
                onConnectionChange={(wired) => setIsTvsWired(wired)}
                vSurge={tvsIn.v_surge}
                rSrc={tvsIn.r_src}
                iPeakAct={tvsOut?.ipp_act}
                vClampAct={tvsOut?.vc_act}
              />
            </div>
          </div>
        )}

        {(activeTab === 'zener' || activeTab === 'tvs') && (
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
          renderCard={(key) => {
            const isWired = activeTab === 'zener' ? isZenerWired : isTvsWired;
            return (
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
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Input Operating Conditions</span>
                  </div>
                  {activeTab === 'zener' && renderZenerInputs()}
                  {activeTab === 'tvs' && renderTvsInputs()}
                </div>
              )}

              {key === 'theory' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-1">
                    <BookOpen className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Equivalent Circuit Principles & Physical Models</span>
                  </div>

                  <TvsZenerSchematicSandbox
                    activeTab={activeTab}
                    onConnectionChange={(isWired) => {
                      if (activeTab === 'zener') {
                        setIsZenerWired(isWired);
                      } else {
                        setIsTvsWired(isWired);
                      }
                    }}
                    vinZener={zenerIn.vin_max}
                    voutZener={zenerIn.vz}
                    rLimit={zenerIn.r_sel}
                    vSurge={tvsIn.v_surge}
                    rSrc={tvsIn.r_src}
                  />

                  <div className="text-[10px] text-slate-400 space-y-2 leading-relaxed font-sans border-t border-slate-850 pt-2">
                    <span className="font-semibold text-slate-300 block">
                      {activeTab === 'zener' ? 'Zener Regulator Model:' : 'TVS Dynamic Impedance & Clamping Model:'}
                    </span>
                    {activeTab === 'zener' ? (
                      <>
                        <Latex math="I_{R} = \\frac{V_{in} - V_z}{R} \\quad I_{z\\_max} = I_R - I_{load\\_min}" block />
                        <p>Series ballast resistor R must maintain minimum knee current at Vin_min under full load, while avoiding excessive dissipation at Vin_max under zero load.</p>
                      </>
                    ) : (
                      <>
                        <Latex math="R_{dyn} = \\frac{V_{c\\_spec} - V_{br}}{I_{pp\\_spec}} \\quad I_{pp\\_act} = \\frac{V_{surge} - V_{br}}{R_{src} + R_{dyn}}" block />
                        <Latex math="V_{c\\_act} = V_{br} + I_{pp\\_act} \\cdot R_{dyn}" block />
                        <p>Calculates peak surge current and actual clamping voltage based on TVS dynamic resistance Rdyn fitted from datasheet pulse test points.</p>
                      </>
                    )}
                  </div>
                </div>
              )}

              {key === 'results' && renderWiredCheck(isWired, (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Core Calculation Results</span>
                  </div>

                  {activeTab === 'zener' && zenerOut && (
                    <div className="grid grid-cols-2 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Maximum Allowable Resistance R_max</span>
                        <span className="text-xs font-bold text-blue-400">{(zenerOut.r_max ?? 0).toFixed(1)} Ω</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Resistor Max Dissipation Pr_max</span>
                        <span className="text-xs font-bold text-rose-400">{(zenerOut.pr_max ?? 0).toFixed(3)} W</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5 col-span-2">
                        <span className="text-[8px] text-slate-400 font-sans font-bold text-teal-400">Zener Peak Dissipation Pz_max</span>
                        <span className="text-xs font-bold text-teal-400">{(zenerOut.pz_max ?? 0).toFixed(3)} W</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'tvs' && tvsOut && (
                    <div className="grid grid-cols-2 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">TVS Dynamic Resistance Rdyn</span>
                        <span className="text-xs font-bold text-blue-400">{(tvsOut.r_dyn ?? 0).toFixed(4)} Ω</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Surge Peak Discharge Current Ipp</span>
                        <span className="text-xs font-bold text-amber-400">{(tvsOut.ipp_act ?? 0).toFixed(2)} A</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans font-bold text-teal-400">Actual Clamping Voltage Vc</span>
                        <span className="text-xs font-bold text-teal-400">{(tvsOut.vc_act ?? 0).toFixed(2)} V</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Peak Transient Pulse Power</span>
                        <span className="text-xs font-bold text-rose-400">{(tvsOut.p_act ?? 0).toFixed(1)} W</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {key === 'bom' && renderWiredCheck(isWired, (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <span className="text-xs font-bold text-white">Recommended BOM Component Sizing</span>
                  </div>

                  {activeTab === 'zener' && bomList.length > 0 && (
                    <div className="overflow-x-auto scrollbar-thin rounded-lg border border-slate-800">
                      <table className="w-full text-[10px] text-left text-slate-350 border-collapse">
                        <thead className="text-[8.5px] uppercase bg-slate-950/80 text-slate-300 border-b border-slate-800">
                          <tr>
                            <th className="px-3 py-2 border-r border-slate-800">Designator</th>
                            <th className="px-3 py-2 border-r border-slate-800">Calculated</th>
                            <th className="px-3 py-2 border-r border-slate-800">Standard Value</th>
                            <th className="px-3 py-2 border-r border-slate-800">Error %</th>
                            <th className="px-3 py-2">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {bomList.map((item, idx) => (
                            <tr key={idx} className="border-b border-slate-850/80 bg-slate-900/10 hover:bg-slate-800/20 transition-colors">
                              <td className="px-3 py-2 border-r border-slate-800 text-white font-bold">{item.designator}</td>
                              <td className="px-3 py-2 border-r border-slate-800 font-mono">{item.calcValue}</td>
                              <td className="px-3 py-2 border-r border-slate-800 font-mono text-cyan-400 font-bold">{item.stdValue}</td>
                              <td className="px-3 py-2 border-r border-slate-800 font-mono text-center">{item.error}</td>
                              <td className="px-3 py-2 text-slate-400">{item.desc}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {activeTab === 'tvs' && tvsOut && (
                    <div className="text-[10px] text-slate-400 leading-relaxed border border-slate-800/80 rounded-lg p-3 bg-slate-950/40">
                      <span className="font-bold text-slate-350 block">Commercial TVS Selection Criteria:</span>
                      <p className="mt-1">
                        {"1. Choose standoff voltage V_RWM &ge; 1.15 × maximum system continuous DC voltage."}
                        <br />
                        {"2. Rated peak pulse power rating Pppm must exceed actual dissipated pulse power: "}
                        P_act = {(tvsOut.p_act ?? 0).toFixed(1)} W.
                      </p>
                    </div>
                  )}
                </div>
              ))}

              {key === 'charts' && renderWiredCheck(isWired, (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <span className="text-xs font-bold text-white block border-b border-slate-800 pb-2 mb-2">Graphical Parametric Sweep Analysis</span>
                  <div className="w-full h-[180px]">
                    <ReactECharts option={chartOption} notMerge={true} style={{ width: '100%', height: '100%' }} />
                  </div>
                </div>
              ))}

              {key === 'drc' && renderWiredCheck(isWired, (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-bold text-white">DRC Design Rule Check</span>
                  </div>

                  <div className="flex flex-col gap-2.5 font-mono text-[10px]">
                    {activeTab === 'zener' && zenerOut && (
                      <>
                        {!zenerOut.is_passed ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Zener Regulation Failed:</strong> {zenerOut.warn_msg}. Check whether Vin_min suffices to keep the Zener in regulation or reduce the series resistor value.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Zener Operating Safe:</strong> Series resistor sizing is correct; Zener maintains breakdown regulation with safe thermal margins.</span>
                          </div>
                        )}
                      </>
                    )}

                    {activeTab === 'tvs' && tvsOut && (
                      <>
                        {tvsOut.is_overload ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>TVS Power Rating Exceeded:</strong> {tvsOut.status_msg}. Select a higher-power TVS (e.g. from 600W SMBJ to 1500W SMCJ or 3000W SMDJ) or add upstream series impedance.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>TVS Clamping Safe:</strong> Surge pulse power and clamping voltage are within safe operational limits.</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              ))}
            </DragCard>
          );
        }}
      />
    )}
  </div>
</div>
);
}