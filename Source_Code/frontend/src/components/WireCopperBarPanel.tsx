import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import { 
  ArrowLeft, 
  ShieldAlert, 
  CheckCircle2, 
  BookOpen,
  TrendingUp,
  X,
  Compass
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

interface LitzStrandData {
  dia_mm: number;
  name: string;
  strands: number;
  fr: number;
  loss_score: number;
  evaluation: string;
}

interface LitzResponse {
  delta_mm: number;
  max_rec_dia_mm: number;
  area_target_mm2: number;
  area_real_mm2: number;
  strands_needed: number;
  fr_skin_theoretical: number;
  r_dc_ohm: number;
  p_loss_w: number;
  litz_od_mm: number;
  optimizer: {
    best_dia_mm: number;
    best_name: string;
    best_strands: number;
    data: LitzStrandData[];
  };
  drc_warnings: string[];
}

interface AwgResponse {
  dia_mm: number;
  area_mm2: number;
  r_total_ohm: number;
  v_drop_v: number;
  p_loss_w: number;
  i_chassis_limit_a: number;
  i_trans_limit_a: number;
  drc_warnings: string[];
}

interface BusbarResponse {
  area_mm2: number;
  density_a_mm2: number;
  temp_rise_c: number;
  r_total_ohm: number;
  v_drop_mv: number;
  p_loss_w: number;
  drc_warnings: string[];
}

type TabType = 'litz' | 'awg' | 'busbar';

export default function WireCopperBarPanel({ onBack }: { onBack: () => void }) {
  const [activeTab, setActiveTab] = useTabHistoryState<TabType>('litz', 'activeTab');
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);
  const [showMtlModal, setShowMtlModal] = useState<boolean>(false);

  // MTL Calculator Modal States
  const [mtlCoreType, setMtlCoreType] = useState<'round' | 'rect'>('round');
  const [mtlRoundDia, setMtlRoundDia] = useState<number>(10.0);
  const [mtlRoundBuild, setMtlRoundBuild] = useState<number>(2.0);
  const [mtlRectA, setMtlRectA] = useState<number>(10.0);
  const [mtlRectB, setMtlRectB] = useState<number>(10.0);
  const [mtlRectBuild, setMtlRectBuild] = useState<number>(2.0);
  const [calcMtlResult, setCalcMtlResult] = useState<number>(37.7);

  // Tab 1: Litz Wire Parameters
  const [lzFreq, setLzFreq] = useState<number>(100.0); 
  const [lzCurr, setLzCurr] = useState<number>(5.0); 
  const [lzJ, setLzJ] = useState<number>(4.0); 
  const [lzStrandSelect, setLzStrandSelect] = useState<number>(0.1); 
  const [lzCustomDia, setLzCustomDia] = useState<number>(0.1);
  const [lzMtl, setLzMtl] = useState<number>(35.0); 
  const [lzTurns, setLzTurns] = useState<number>(40);
  const [lzLen, setLzLen] = useState<number>(1.4); 
  const [lzTemp, setLzTemp] = useState<number>(100.0); 
  const [lzAcFactor, setLzAcFactor] = useState<number>(1.2);
  const [litzRes, setLitzRes] = useState<LitzResponse | null>(null);
  const [litzError, setLitzError] = useState<string | null>(null);
  const [litzChartOption, setLitzChartOption] = useState<any>({});

  // Tab 2: AWG Round Wire Parameters
  const [awgSelect, setAwgSelect] = useState<number>(18); 
  const [awgLen, setAwgLen] = useState<number>(1.0); 
  const [awgCurr, setAwgCurr] = useState<number>(5.0); 
  const [awgTemp, setAwgTemp] = useState<number>(75.0); 
  const [awgRes, setAwgRes] = useState<AwgResponse | null>(null);
  const [awgError, setAwgError] = useState<string | null>(null);

  // Tab 3: Busbar Parameters
  const [bbWidth, setBbWidth] = useState<number>(20.0); 
  const [bbThick, setBbThick] = useState<number>(3.0); 
  const [bbLen, setBbLen] = useState<number>(500.0); 
  const [bbCurr, setBbCurr] = useState<number>(100.0); 
  const [bbTempAmb, setBbTempAmb] = useState<number>(40.0); 
  const [busbarRes, setBusbarRes] = useState<BusbarResponse | null>(null);
  const [busbarError, setBusbarError] = useState<string | null>(null);

  const getLayoutConfigForTab = (tab: TabType) => {
    switch (tab) {
      case 'litz':
        return {
          defaultCards: ['input', 'theory', 'results', 'schematic', 'bom', 'charts', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', schematic: 'right', bom: 'right', charts: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, schematic: 8, bom: 8, charts: 8, drc: 8 },
          defaultHeights: { input: 540, theory: 280, results: 240, schematic: 220, bom: 340, charts: 280, drc: 180 }
        };
      case 'awg':
        return {
          defaultCards: ['input', 'theory', 'results', 'schematic', 'bom', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', schematic: 'right', bom: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, schematic: 8, bom: 8, drc: 8 },
          defaultHeights: { input: 420, theory: 260, results: 240, schematic: 220, bom: 340, drc: 180 }
        };
      case 'busbar':
        return {
          defaultCards: ['input', 'theory', 'results', 'schematic', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', schematic: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, schematic: 8, drc: 8 },
          defaultHeights: { input: 450, theory: 260, results: 240, schematic: 220, drc: 180 }
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
    panelKey: 'layout_conductor_v4',
    activeTab: activeTab,
    defaultCards: currentLayoutConfig.defaultCards,
    defaultColumns: currentLayoutConfig.defaultColumns,
    defaultSpans: currentLayoutConfig.defaultSpans,
    defaultHeights: currentLayoutConfig.defaultHeights
  });

  useEffect(() => {
    if (mtlCoreType === 'round') {
      const circumference = Math.PI * mtlRoundDia;
      const buildFactor = 2.0 * Math.PI * mtlRoundBuild;
      setCalcMtlResult(parseFloat((circumference + buildFactor).toFixed(1)));
    } else {
      const perimeter = 2.0 * (mtlRectA + mtlRectB);
      const buildFactor = 2.0 * Math.PI * mtlRectBuild;
      setCalcMtlResult(parseFloat((perimeter + buildFactor).toFixed(1)));
    }
  }, [mtlCoreType, mtlRoundDia, mtlRoundBuild, mtlRectA, mtlRectB, mtlRectBuild]);

  const calculateLitz = async () => {
    setLitzError(null);
    try {
      const strandDia = lzStrandSelect === -1 ? lzCustomDia : lzStrandSelect;
      const response = await apiFetch('/api/calculate/wire_copper_bar/litz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          freq_khz: lzFreq,
          i_rms: lzCurr,
          j_density: lzJ,
          strand_dia: strandDia,
          length_m: lzLen,
          temp_c: lzTemp,
          ac_factor: lzAcFactor
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Litz wire calculation failed');
      }
      const data: LitzResponse = await response.json();
      setLitzRes(data);
      renderLitzChart(data);
    } catch (e: any) {
      setLitzError(e.message);
    }
  };

  const calculateAwg = async () => {
    setAwgError(null);
    try {
      const response = await apiFetch('/api/calculate/wire_copper_bar/awg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          awg_val: awgSelect,
          custom_dia: 0.0,
          current: awgCurr,
          length_m: awgLen,
          temp_amb: awgTemp,
          material: "copper"
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'AWG wire calculation failed');
      }
      const data: AwgResponse = await response.json();
      setAwgRes(data);
    } catch (e: any) {
      setAwgError(e.message);
    }
  };

  const calculateBusbar = async () => {
    setBusbarError(null);
    try {
      const response = await apiFetch('/api/calculate/wire_copper_bar/busbar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          width_mm: bbWidth,
          thick_mm: bbThick,
          length_mm: bbLen,
          current: bbCurr
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Copper busbar calculation failed');
      }
      const data: BusbarResponse = await response.json();
      setBusbarRes(data);
    } catch (e: any) {
      setBusbarError(e.message);
    }
  };

  const renderLitzChart = (data: LitzResponse) => {
    if (!data.optimizer || !data.optimizer.data) return;
    const strandData = data.optimizer.data;

    const names = strandData.map(d => d.name);
    const lossScores = strandData.map(d => parseFloat(d.loss_score.toFixed(1)));

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        shadowColor: 'rgba(56, 189, 248, 0.4)',
        shadowBlur: 8,
        textStyle: { color: '#f1f5f9', fontSize: 11 },
        formatter: (params: any) => {
          if (!params || !params[0]) return '';
          return `${params[0].name}: Loss Score ${params[0].value}`;
        }
      },
      grid: { top: '10%', left: '5%', right: '5%', bottom: '25%', containLabel: true },
      xAxis: {
        type: 'category',
        data: names,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 8, interval: 0, rotate: 20 }
      },
      yAxis: {
        type: 'value',
        name: 'Estimated Loss Score (Lower is better)',
        nameTextStyle: { color: '#94a3b8', fontSize: 8 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#94a3b8', fontSize: 8 },
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
          name: 'Loss Score',
          type: 'bar',
          data: lossScores,
          barWidth: '45%',
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#22d3ee' },
                { offset: 1, color: '#0284c7' }
              ]
            },
            borderRadius: [4, 4, 0, 0],
            shadowColor: 'rgba(34, 211, 238, 0.4)',
            shadowBlur: 8
          }
        }
      ]
    };
    setLitzChartOption(option);
  };

  useEffect(() => {
    if (activeTab === 'litz') {
      const timer = setTimeout(() => {
        calculateLitz();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [lzFreq, lzCurr, lzJ, lzStrandSelect, lzCustomDia, lzMtl, lzTurns, lzLen, lzTemp, lzAcFactor, activeTab]);

  useEffect(() => {
    if (activeTab === 'awg') calculateAwg();
  }, [awgSelect, awgLen, awgCurr, awgTemp, activeTab]);

  useEffect(() => {
    if (activeTab === 'busbar') calculateBusbar();
  }, [bbWidth, bbThick, bbLen, bbCurr, bbTempAmb, activeTab]);

  const activeErrors = 
    activeTab === 'litz' ? litzError : 
    activeTab === 'awg' ? awgError : busbarError;

  const renderLitzInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-500">Switching Frequency Freq (kHz)</label>
          <input type="number" value={lzFreq} onChange={e => setLzFreq(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Rated RMS Current Arms (A)</label>
          <input type="number" value={lzCurr} onChange={e => setLzCurr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-500">Target Current Density J (A/mm²)</label>
          <input type="number" step="0.5" value={lzJ} onChange={e => setLzJ(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Thermal Derating AC Factor</label>
          <input type="number" step="0.05" value={lzAcFactor} onChange={e => setLzAcFactor(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="border border-slate-850 rounded-lg p-2.5 bg-slate-900/10 space-y-2">
        <span className="text-[9px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Single Strand Litz Wire Diameter</span>
        <select value={lzStrandSelect} onChange={e => setLzStrandSelect(parseFloat(e.target.value))} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white cursor-pointer focus:outline-none font-mono">
          <option value={0.05}>0.05 mm (38 AWG - Ultra-HF)</option>
          <option value={0.08}>0.08 mm (36 AWG)</option>
          <option value={0.1}>0.10 mm (34 AWG)</option>
          <option value={0.15}>0.15 mm (32 AWG)</option>
          <option value={0.2}>0.20 mm (30 AWG)</option>
          <option value={-1}>Custom Strand Diameter</option>
        </select>
        {lzStrandSelect === -1 && (
          <div className="flex flex-col gap-1 mt-1">
            <label className="text-[8px] text-slate-550">Custom Wire Diameter (mm)</label>
            <input type="number" step="0.01" value={lzCustomDia} onChange={e => setLzCustomDia(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
        )}
      </div>

      <div className="border border-slate-850 rounded-lg p-2.5 bg-slate-900/10 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center">
              <span>Mean Turn Length MTL (mm)</span>
              <button onClick={() => setShowMtlModal(true)} className="text-[7.5px] border-0 text-cyan-400 hover:text-cyan-300 font-bold bg-transparent cursor-pointer">Quick Calc</button>
            </div>
            <input type="number" value={lzMtl} onChange={e => setLzMtl(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Total Winding Turns (N)</label>
            <input type="number" value={lzTurns} onChange={e => setLzTurns(parseInt(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-500">Lead Extra Length (m)</label>
            <input type="number" step="0.1" value={lzLen} onChange={e => setLzLen(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Design Working Temp (°C)</label>
            <input type="number" value={lzTemp} onChange={e => setLzTemp(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
        </div>
      </div>
    </div>
  );

  const renderAwgInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="flex flex-col gap-1">
        <label className="text-[8px] text-slate-550">Select Standard Wire Gauge (AWG)</label>
        <select value={awgSelect} onChange={e => setAwgSelect(parseInt(e.target.value))} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white cursor-pointer focus:outline-none font-mono">
          {Array.from({ length: 39 }, (_, i) => i + 4).map(awg => (
            <option key={awg} value={awg}>AWG {awg}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Load Current Arms (A)</label>
          <input type="number" value={awgCurr} onChange={e => setAwgCurr(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Total Wire Length (m)</label>
          <input type="number" step="0.5" value={awgLen} onChange={e => setAwgLen(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-[8px] text-slate-550 font-bold text-amber-400">Wire Operating Temperature (°C)</label>
        <input type="number" value={awgTemp} onChange={e => setAwgTemp(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
      </div>
    </div>
  );

  const renderBusbarInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550 font-bold text-blue-400">Busbar Width (mm)</label>
          <input type="number" step="1" value={bbWidth} onChange={e => setBbWidth(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Busbar Thickness (mm)</label>
          <input type="number" step="0.5" value={bbThick} onChange={e => setBbThick(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Continuous DC Current (A)</label>
          <input type="number" step="10" value={bbCurr} onChange={e => setBbCurr(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Chassis Ambient Temp Ta (°C)</label>
          <input type="number" value={bbTempAmb} onChange={e => setBbTempAmb(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-[8px] text-slate-550">Busbar Length (mm)</label>
        <input type="number" step="50" value={bbLen} onChange={e => setBbLen(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
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
            <h1 className="text-base font-bold text-white tracking-tight">Winding Wire & High-Current Copper Busbar Sizing</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">Analyze high-frequency Litz wire skin & proximity effect losses; verify solid round AWG ampacity & high-current busbar steady-state heating.</p>
          </div>
        </div>

        <button
          onClick={handleResetLayout}
          className="flex items-center space-x-2 bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-350 px-4 py-2 rounded-lg text-xs transition cursor-pointer"
        >
          <span>Reset Layout</span>
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 bg-slate-900/60 p-1 rounded-xl border border-slate-800 max-w-7xl mx-auto w-full">
        {([
          { id: 'litz', label: '1. Litz Wire Optimization', icon: null},
          { id: 'awg', label: '2. Standard AWG Wire Sizing', icon: null},
          { id: 'busbar', label: '3. High-Current Copper Busbar', icon: null}
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

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 min-h-0">
        {activeErrors && <div className="text-xs text-red-400 border border-red-500/20 bg-red-500/5 p-3 rounded-lg mb-3 font-mono">Error: {activeErrors}</div>}

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
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Input Operating Conditions</span>
                  </div>
                  {activeTab === 'litz' && renderLitzInputs()}
                  {activeTab === 'awg' && renderAwgInputs()}
                  {activeTab === 'busbar' && renderBusbarInputs()}
                </div>
              )}

              {key === 'theory' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <BookOpen className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Physical Principles & Equations</span>
                  </div>
                  <div className="text-[10px] text-slate-400 space-y-4 leading-relaxed font-sans">
                    {activeTab === 'litz' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">1. Skin Depth Formula:</span>
                          <Latex math={"\\delta = \\sqrt{\\frac{\\rho}{\\pi \\cdot f \\cdot \\mu_0 \\cdot \\mu_r}}"} block />
                          <p>In high-frequency magnetic winding design, strand radius should be less than or equal to skin depth (<Latex math={"\\delta"} />) to avoid steep increases in AC resistance factor <Latex math={"Fr"} />.</p>
                        </div>
                      </>
                    )}
                    {activeTab === 'awg' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">AWG Wire Cross-Section & Resistance Model:</span>
                          <Latex math={"d_{awg} = 0.127 \\cdot 92^{\\frac{36-awg}{39}} \\text{ mm} \\quad R_{dc} = \\frac{\\rho \\cdot L}{A}"} block />
                        </div>
                      </>
                    )}
                    {activeTab === 'busbar' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">DIN-43671 High-Current Busbar Thermal Rise Estimation:</span>
                          <Latex math={"\\Delta T \\approx 10 \\cdot \\left( \\frac{J}{1.2} \\right)^{2.0} \\quad (°\\text{C})"} block />
                          <p>Excessive current density <Latex math={"J"} /> causes severe busbar heating; derating margins must be preserved.</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {key === 'results' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Core Calculation Results</span>
                  </div>

                  {activeTab === 'litz' && litzRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Skin Depth at Frequency</span>
                        <span className="text-xs font-bold text-blue-400">{(litzRes.delta_mm ?? 0).toFixed(4)} mm</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Max Recommended Strand Dia</span>
                        <span className="text-xs font-bold text-blue-400">{(litzRes.max_rec_dia_mm ?? 0).toFixed(4)} mm</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Optimized Total Strands</span>
                        <span className="text-xs font-bold text-emerald-400">{(litzRes.strands_needed ?? 0)} Strands</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Target Copper Area</span>
                        <span className="text-xs font-bold text-slate-200">{(litzRes.area_target_mm2 ?? 0).toFixed(4)} mm²</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Actual Copper Area</span>
                        <span className="text-xs font-bold text-slate-200">{(litzRes.area_real_mm2 ?? 0).toFixed(4)} mm²</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Estimated Power Loss</span>
                        <span className="text-xs font-bold text-rose-400">{(litzRes.p_loss_w ?? 0).toFixed(3)} W</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'awg' && awgRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans font-bold">Bare Conductor Diameter</span>
                        <span className="text-xs font-bold text-white">{(awgRes.dia_mm ?? 0).toFixed(4)} mm</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans font-bold">Cross-Sectional Area</span>
                        <span className="text-xs font-bold text-white">{(awgRes.area_mm2 ?? 0).toFixed(4)} mm²</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Total DC Resistance</span>
                        <span className="text-xs font-bold text-cyan-400">{(awgRes.r_total_ohm ?? 0).toFixed(4)} Ω</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">DC Voltage Drop</span>
                        <span className="text-xs font-bold text-orange-400">{(awgRes.v_drop_v ?? 0).toFixed(3)} V</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Full Load Loss Ploss</span>
                        <span className="text-xs font-bold text-rose-400">{(awgRes.p_loss_w ?? 0).toFixed(3)} W</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'busbar' && busbarRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Busbar Cross-Section</span>
                        <span className="text-xs font-bold text-white">{(busbarRes.area_mm2 ?? 0).toFixed(2)} mm²</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Current Density</span>
                        <span className="text-xs font-bold text-slate-200">{(busbarRes.density_a_mm2 ?? 0).toFixed(2)} A/mm²</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Predicted Temp Rise ΔT</span>
                        <span className="text-xs font-bold text-rose-400">{(busbarRes.temp_rise_c ?? 0).toFixed(1)} °C</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Equivalent Resistance</span>
                        <span className="text-xs font-bold text-slate-200">{((busbarRes.r_total_ohm ?? 0) * 1e6).toFixed(1)} μΩ</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Busbar Voltage Drop</span>
                        <span className="text-xs font-bold text-orange-400">{(busbarRes.v_drop_mv ?? 0).toFixed(2)} mV</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Full Load Copper Loss</span>
                        <span className="text-xs font-bold text-rose-400">{(busbarRes.p_loss_w ?? 0).toFixed(3)} W</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {key === 'bom' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <span className="text-xs font-bold text-white">
                      {activeTab === 'litz' ? 'Alternative Strand Loss Comparison Table' : 'Standard Wire Gauge Comparison Table'}
                    </span>
                  </div>

                  {activeTab === 'litz' && litzRes && (
                    <div className="overflow-x-auto scrollbar-thin rounded-lg border border-slate-800">
                      <table className="w-full text-[10px] text-left text-slate-350 border-collapse">
                        <thead className="text-[8.5px] uppercase bg-slate-950/80 text-slate-300 border-b border-slate-800">
                          <tr>
                            <th className="px-3 py-2 border-r border-slate-800">Spec Name</th>
                            <th className="px-3 py-2 border-r border-slate-800">Strand Dia</th>
                            <th className="px-3 py-2 border-r border-slate-800">Strands</th>
                            <th className="px-3 py-2 border-r border-slate-800">AC Factor Fr</th>
                            <th className="px-3 py-2 text-right">Loss Rating</th>
                          </tr>
                        </thead>
                        <tbody>
                          {litzRes.optimizer.data.map((item, idx) => (
                            <tr key={idx} className="border-b border-slate-850/80 bg-slate-900/10 hover:bg-slate-800/20 transition-colors">
                              <td className="px-3 py-2 border-r border-slate-800 text-white font-bold">{item.name}</td>
                              <td className="px-3 py-2 border-r border-slate-800 font-mono">{item.dia_mm.toFixed(3)} mm</td>
                              <td className="px-3 py-2 border-r border-slate-800 font-mono text-center">{item.strands} Strands</td>
                              <td className="px-3 py-2 border-r border-slate-800 font-mono text-center text-blue-400">{(item.fr).toFixed(3)}</td>
                              <td className={`px-3 py-2 text-right font-bold ${item.loss_score <= 1.2 ? 'text-green-400' : 'text-slate-350'}`}>{item.loss_score <= 1.2 ? 'Optimal' : 'Acceptable'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {key === 'charts' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <span className="text-xs font-bold text-white block border-b border-slate-800 pb-2 mb-2">Graphical Parametric Sweep Analysis</span>
                  <div className="w-full h-[180px]">
                    {activeTab === 'litz' && litzRes && (
                      <ReactECharts option={litzChartOption} notMerge={true} style={{ width: '100%', height: '100%' }} />
                    )}
                  </div>
                </div>
              )}

              {key === 'schematic' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <Compass className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Conductor & Busbar Structural Model (SVG)</span>
                  </div>

                  <div className="w-full h-[180px] flex items-center justify-center bg-slate-950/20 rounded-xl border border-slate-850 p-2">
                    {activeTab === 'litz' && (
                      <svg className="w-full h-full max-h-[160px] drop-shadow-2xl" viewBox="-70 -70 140 140" preserveAspectRatio="xMidYMid meet">
                        <defs>
                          <radialGradient id="neon-copper" cx="35%" cy="35%" r="65%">
                            <stop offset="0%" stopColor="#ffd700" />
                            <stop offset="40%" stopColor="#f59e0b" />
                            <stop offset="100%" stopColor="#b45309" />
                          </radialGradient>
                          <filter id="neon-glow" x="-30%" y="-30%" width="160%" height="160%">
                            <feGaussianBlur stdDeviation="4" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                        </defs>
                        <circle cx="0" cy="0" r="52" fill="rgba(6, 182, 212, 0.05)" stroke="#06b6d4" strokeWidth="1.5" filter="url(#neon-glow)" />
                        <circle cx="0" cy="0" r="49" fill="none" stroke="#0891b2" strokeWidth="0.8" strokeDasharray="3,3" />

                        <circle cx="0" cy="0" r="4.2" fill="url(#neon-copper)" stroke="#090d16" strokeWidth="0.6" />
                        
                        {[0, 60, 120, 180, 240, 300].map((deg) => {
                          const rad = (deg * Math.PI) / 180;
                          return (
                            <circle
                              key={`l1-${deg}`}
                              cx={11 * Math.cos(rad)}
                              cy={11 * Math.sin(rad)}
                              r="4.2"
                              fill="url(#neon-copper)"
                              stroke="#090d16"
                              strokeWidth="0.6"
                            />
                          );
                        })}

                        {Array.from({ length: 12 }).map((_, i) => {
                          const deg = (i * 360) / 12;
                          const rad = (deg * Math.PI) / 180;
                          return (
                            <circle
                              key={`l2-${i}`}
                              cx={22 * Math.cos(rad)}
                              cy={22 * Math.sin(rad)}
                              r="4.2"
                              fill="url(#neon-copper)"
                              stroke="#090d16"
                              strokeWidth="0.6"
                            />
                          );
                        })}

                        {Array.from({ length: 18 }).map((_, i) => {
                          const deg = (i * 360) / 18 + 10;
                          const rad = (deg * Math.PI) / 180;
                          return (
                            <circle
                              key={`l3-${i}`}
                              cx={33 * Math.cos(rad)}
                              cy={33 * Math.sin(rad)}
                              r="4.2"
                              fill="url(#neon-copper)"
                              stroke="#090d16"
                              strokeWidth="0.6"
                            />
                          );
                        })}

                        <line x1="-65" y1="0" x2="65" y2="0" stroke="#06b6d4" strokeWidth="0.4" strokeDasharray="2,2" opacity="0.3" />
                        <line x1="0" y1="-65" x2="0" y2="65" stroke="#06b6d4" strokeWidth="0.4" strokeDasharray="2,2" opacity="0.3" />
                        
                        <text x="0" y="-57" textAnchor="middle" fill="#06b6d4" className="text-[6.5px] font-mono font-bold tracking-wider">
                          OD ≈ {litzRes?.litz_od_mm ? litzRes.litz_od_mm.toFixed(2) : ((lzStrandSelect === -1 ? lzCustomDia : lzStrandSelect) * 1.15).toFixed(2)} mm
                        </text>
                        <text x="0" y="58" textAnchor="middle" fill="#ffd700" className="text-[6px] font-mono">
                          Strand d = {(lzStrandSelect === -1 ? lzCustomDia : lzStrandSelect).toFixed(3)} mm
                        </text>
                        <text x="0" y="66" textAnchor="middle" fill="#f87171" className="text-[5.5px] font-mono font-bold">
                          Skin Depth δ = {litzRes?.delta_mm ? litzRes.delta_mm.toFixed(3) : '---'} mm
                        </text>
                      </svg>
                    )}

                    {activeTab === 'awg' && (
                      <svg width="100%" height="100%" viewBox="0 0 240 110" className="text-slate-350 bg-transparent max-w-[480px] max-h-[180px]">
                        <defs>
                          <linearGradient id="copper-gradient-awg" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#f59e0b" />
                            <stop offset="50%" stopColor="#fbbf24" />
                            <stop offset="100%" stopColor="#d97706" />
                          </linearGradient>
                          <filter id="neon-glow-blue-awg" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <marker id="arrow-start" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                            <path d="M 10 0 L 0 5 L 10 10 z" fill="#fbbf24" />
                          </marker>
                          <marker id="arrow-end" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#fbbf24" />
                          </marker>
                        </defs>
                        <rect x="20" y="40" width="110" height="30" fill="#2563eb" fillOpacity="0.25" stroke="#3b82f6" strokeWidth="1.5" rx="2" filter="url(#neon-glow-blue-awg)" />
                        <rect x="130" y="44" width="60" height="22" fill="url(#copper-gradient-awg)" stroke="#d97706" strokeWidth="0.5" rx="0.5" />
                        
                        <line x1="198" y1="44" x2="198" y2="66" stroke="#fbbf24" strokeWidth="0.8" markerStart="url(#arrow-start)" markerEnd="url(#arrow-end)" />
                        <text x="204" y="58" fill="#fbbf24" className="text-[7px] font-mono">d = {awgRes?.dia_mm ? awgRes.dia_mm.toFixed(3) : ''} mm</text>

                        <text x="75" y="58" fill="#cbd5e1" className="text-[7.5px] font-bold font-mono">AWG {awgSelect}</text>
                        <text x="100" y="96" textAnchor="middle" fill="#60a5fa" className="text-[6.5px] font-mono">Solid Conductor Physical Cross-Section</text>
                      </svg>
                    )}

                    {activeTab === 'busbar' && (
                      <svg width="100%" height="100%" viewBox="0 0 240 110" className="text-slate-350 bg-transparent max-w-[480px] max-h-[180px]">
                        <defs>
                          <style>{`
                            @keyframes current-flow {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-current {
                              stroke-dasharray: 6, 4;
                              animation: current-flow 1.2s linear infinite;
                            }
                          `}</style>
                          <linearGradient id="copper-3d-top" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#fbbf24" />
                            <stop offset="100%" stopColor="#ea580c" />
                          </linearGradient>
                          <linearGradient id="copper-3d-side" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#b45309" />
                            <stop offset="100%" stopColor="#78350f" />
                          </linearGradient>
                          <linearGradient id="copper-3d-front" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#d97706" />
                            <stop offset="100%" stopColor="#92400e" />
                          </linearGradient>
                          <filter id="neon-glow-red" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <marker id="arrow-start" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                            <path d="M 10 0 L 0 5 L 10 10 z" fill="#fbbf24" />
                          </marker>
                          <marker id="arrow-end" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#fbbf24" />
                          </marker>
                          <marker id="arrow-start-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                            <path d="M 10 0 L 0 5 L 10 10 z" fill="#3b82f6" />
                          </marker>
                          <marker id="arrow-end-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
                          </marker>
                          <marker id="arrow-end-red" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
                          </marker>
                        </defs>
                        <polygon points="70,20 190,20 150,55 30,55" fill="url(#copper-3d-top)" stroke="#d97706" strokeWidth="0.4" />
                        <polygon points="150,55 190,20 190,32 150,67" fill="url(#copper-3d-side)" stroke="#78350f" strokeWidth="0.4" />
                        <polygon points="30,55 150,55 150,67 30,67" fill="url(#copper-3d-front)" stroke="#b45309" strokeWidth="0.4" />

                        <line x1="25" y1="55" x2="25" y2="67" stroke="#fbbf24" strokeWidth="0.8" markerStart="url(#arrow-start)" markerEnd="url(#arrow-end)" />
                        <text x="18" y="64" textAnchor="end" fill="#fbbf24" className="text-[6.5px] font-mono">T = {bbThick} mm</text>

                        <line x1="30" y1="74" x2="150" y2="74" stroke="#3b82f6" strokeWidth="0.8" markerStart="url(#arrow-start-blue)" markerEnd="url(#arrow-end-blue)" />
                        <text x="90" y="85" textAnchor="middle" fill="#60a5fa" className="text-[6.5px] font-mono">W = {bbWidth} mm</text>

                        <line x1="198" y1="18" x2="158" y2="53" stroke="#10b981" strokeWidth="0.8" />
                        <text x="188" y="40" fill="#34d399" className="text-[6.5px] font-mono">L = {bbLen} mm</text>

                        <line x1="80" y1="38" x2="140" y2="38" stroke="#ef4444" strokeWidth="2.0" markerEnd="url(#arrow-end-red)" className="animate-current" filter="url(#neon-glow-red)" />
                        <text x="110" y="34" textAnchor="middle" fill="#f87171" className="text-[6.5px] font-bold font-mono" filter="url(#neon-glow-red)">Current Direction I</text>
                      </svg>
                    )}
                  </div>
                </div>
              )}

              {key === 'drc' && (
                <div className="h-full overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-bold text-white">DRC Design Rule Check</span>
                  </div>

                  <div className="flex flex-col gap-2.5">
                    {activeTab === 'litz' && litzRes && (
                      <>
                        {(() => {
                          const strandDia = lzStrandSelect === -1 ? lzCustomDia : lzStrandSelect;
                          if (strandDia > litzRes.max_rec_dia_mm * 1.2) {
                            return (
                              <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                                <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                                <span><strong>Strand Diameter Excessive:</strong> Selected strand diameter ({strandDia} mm) exceeds skin depth limit ({litzRes.max_rec_dia_mm.toFixed(3)} mm). High-frequency skin effect causes high eddy current losses. Select a finer strand diameter (e.g. 0.1 mm or 0.08 mm).</span>
                              </div>
                            );
                          } else {
                            return (
                              <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                                <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                                <span><strong>Skin Depth Compliant:</strong> Selected strand diameter satisfies high-frequency skin depth limits.</span>
                              </div>
                            );
                          }
                        })()}
                      </>
                    )}

                    {activeTab === 'awg' && awgRes && (
                      <>
                        {awgCurr > awgRes.i_chassis_limit_a ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Conductor Ampacity Exceeded:</strong> Load current ({awgCurr} A) exceeds chassis enclosed rating limit ({awgRes.i_chassis_limit_a.toFixed(2)} A). Risk of excessive thermal rise and insulation damage. Select a thicker wire gauge.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Ampacity Safe:</strong> Load current is well within wire gauge limit.</span>
                          </div>
                        )}
                      </>
                    )}

                    {activeTab === 'busbar' && busbarRes && (
                      <>
                        {busbarRes.temp_rise_c > 30.0 ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Busbar Temperature Rise Warning:</strong> Steady-state self-heating rise is {busbarRes.temp_rise_c.toFixed(1)} °C, exceeding standard 30°C design guidelines. Widen or thicken the busbar, or add forced air cooling.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Busbar Temperature Rise Compliant.</strong></span>
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

      {showMtlModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full relative space-y-4">
            <button onClick={() => setShowMtlModal(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white border-0 bg-transparent cursor-pointer"><X className="w-4 h-4" /></button>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Mean Turn Length (MTL) Quick Calculator
            </h3>
            
            <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-850">
              <button onClick={() => setMtlCoreType('round')} className={`flex-1 py-1 text-[10px] border-0 rounded cursor-pointer ${mtlCoreType === 'round' ? 'bg-indigo-500/20 text-indigo-400 font-bold' : 'bg-transparent text-slate-400'}`}>Round Centerpost (EE/RM)</button>
              <button onClick={() => setMtlCoreType('rect')} className={`flex-1 py-1 text-[10px] border-0 rounded cursor-pointer ${mtlCoreType === 'rect' ? 'bg-indigo-500/20 text-indigo-400 font-bold' : 'bg-transparent text-slate-400'}`}>Rectangular / Pot Core</button>
            </div>

            {mtlCoreType === 'round' ? (
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-500">Bobbin Diameter (mm)</label>
                  <input type="number" value={mtlRoundDia} onChange={(e) => setMtlRoundDia(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-500">Bobbin Build Thickness (mm)</label>
                  <input type="number" value={mtlRoundBuild} onChange={(e) => setMtlRoundBuild(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
                </div>
              </div>
            ) : (
              <div className="space-y-3 pt-2">
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-[8px] text-slate-500">Bobbin Width A (mm)</label>
                    <input type="number" value={mtlRectA} onChange={(e) => setMtlRectA(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[8px] text-slate-500">Bobbin Height B (mm)</label>
                    <input type="number" value={mtlRectB} onChange={(e) => setMtlRectB(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-500">Coil Build Thickness (mm)</label>
                  <input type="number" value={mtlRectBuild} onChange={(e) => setMtlRectBuild(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
                </div>
              </div>
            )}

            <div className="border border-slate-850 rounded bg-slate-950/60 p-3 text-center">
              <span className="text-[10px] text-slate-550 block">Calculated Mean Turn Length (MTL)</span>
              <span className="text-lg font-bold text-emerald-400 font-mono">{calcMtlResult} mm</span>
            </div>

            <div className="flex justify-end gap-2.5 pt-2">
              <Button onClick={() => setShowMtlModal(false)} variant="ghost" className="text-xs h-8 cursor-pointer">Cancel</Button>
              <Button onClick={() => { setLzMtl(calcMtlResult); setShowMtlModal(false); }} className="text-xs h-8 bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer">Apply Length</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
