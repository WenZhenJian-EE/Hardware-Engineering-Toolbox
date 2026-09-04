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
  Info, 
  BookOpen,
  TrendingUp,
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

interface TraceResponse {
  area_sq_mils: number;
  width_mils: number;
  width_mm: number;
  width_mm_2152: number;
  r_trace_ohm: number;
  v_drop_v: number;
  p_loss_w: number;
  temp_work_c: number;
  drc_warnings: string[];
}

interface ViaResponse {
  i_max_single_a: number;
  derating_factor: number;
  i_total_capacity_a: number;
  r_th_total_k_w: number;
  r_via_total_mohm: number;
  v_drop_mv: number;
  p_loss_mw: number;
  l_via_nh: number;
  c_via_pf: number;
  is_passed: boolean;
  drc_warnings: string[];
}

interface ImpedanceResponse {
  z0_ohm: number;
  z_diff_ohm: number;
  delay_ps_mm: number;
  drc_warnings: string[];
}

type TabType = 'trace' | 'via' | 'impedance';

export default function PcbToolboxPanel({ onBack }: { onBack: () => void }) {
  const [activeTab, setActiveTab] = useTabHistoryState<TabType>('trace', 'activeTab');
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);

  // Tab 1: Trace Carrier Parameters
  const [traceCurrent, setTraceCurrent] = useState<number>(5.0);
  const [traceTempRise, setTraceTempRise] = useState<number>(20.0);
  const [traceCopperOz, setTraceCopperOz] = useState<number>(1.0); 
  const [traceLength, setTraceLength] = useState<number>(100.0);
  const [traceInternal, setTraceInternal] = useState<boolean>(false);
  const [traceTempAmb, setTraceTempAmb] = useState<number>(25.0);
  const [traceRes, setTraceRes] = useState<TraceResponse | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);

  // Tab 2: Via Analysis Parameters
  const [viaDia, setViaDia] = useState<number>(0.3); 
  const [viaPlating, setViaPlating] = useState<number>(20.0); 
  const [viaHeight, setViaHeight] = useState<number>(1.6); 
  const [viaCount, setViaCount] = useState<number>(1);
  const [viaCurrent, setViaCurrent] = useState<number>(2.0);
  const [viaTempRise, setViaTempRise] = useState<number>(15.0);
  const [viaInternal, setViaInternal] = useState<boolean>(false);
  const [viaSolderFilled, setViaSolderFilled] = useState<boolean>(false);
  const [viaRes, setViaRes] = useState<ViaResponse | null>(null);
  const [viaError, setViaError] = useState<string | null>(null);

  // Tab 3: Impedance Parameters
  const [impEr, setImpEr] = useState<number>(4.2); 
  const [impW, setImpW] = useState<number>(0.38); 
  const [impH, setImpH] = useState<number>(0.2); 
  const [impT, setImpT] = useState<number>(35.0); 
  const [impStruct, setImpStruct] = useState<'microstrip' | 'stripline'>('microstrip');
  const [impIsDiff, setImpIsDiff] = useState<boolean>(false);
  const [impS, setImpS] = useState<number>(0.2); 
  const [impRes, setImpRes] = useState<ImpedanceResponse | null>(null);
  const [impError, setImpError] = useState<string | null>(null);

  const getLayoutConfigForTab = (tab: TabType) => {
    switch (tab) {
      case 'trace':
        return {
          defaultCards: ['input', 'theory', 'results', 'schematic', 'charts', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', schematic: 'right', charts: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, schematic: 8, charts: 8, drc: 8 },
          defaultHeights: { input: 480, theory: 280, results: 240, schematic: 220, charts: 300, drc: 180 }
        };
      case 'via':
        return {
          defaultCards: ['input', 'theory', 'results', 'schematic', 'charts', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', schematic: 'right', charts: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, schematic: 8, charts: 8, drc: 8 },
          defaultHeights: { input: 500, theory: 280, results: 300, schematic: 220, charts: 300, drc: 180 }
        };
      case 'impedance':
        return {
          defaultCards: ['input', 'theory', 'results', 'schematic', 'charts', 'drc'],
          defaultColumns: { input: 'left', theory: 'left', results: 'right', schematic: 'right', charts: 'right', drc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, theory: 4, results: 8, schematic: 8, charts: 8, drc: 8 },
          defaultHeights: { input: 460, theory: 260, results: 240, schematic: 220, charts: 300, drc: 180 }
        };
    }
  };

  const currentLayoutConfig = getLayoutConfigForTab(activeTab);

  const getChartOption = () => {
    if (activeTab === 'trace') {
      const currents: number[] = [];
      const widthIPC2221: number[] = [];
      const widthIPC2152: number[] = [];
      const k = traceInternal ? 0.024 : 0.048;
      const th_mils = traceCopperOz * 1.378;
      for (let i = 1; i <= 20; i++) {
        currents.push(i);
        const area_sq_mils = Math.pow(i / (k * Math.pow(traceTempRise, 0.44)), 1.0 / 0.725);
        const width_mils = area_sq_mils / th_mils;
        const width_mm = width_mils * 0.0254;
        const val1 = parseFloat(width_mm.toFixed(3));
        widthIPC2221.push(Number.isFinite(val1) ? val1 : 0);
        const width_mm_2152 = width_mm * (traceInternal ? 0.448 : 0.627);
        const val2 = parseFloat(width_mm_2152.toFixed(3));
        widthIPC2152.push(Number.isFinite(val2) ? val2 : 0);
      }

      return {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: '#2dd4bf',
          borderWidth: 1.5,
          shadowColor: 'rgba(45, 212, 191, 0.4)',
          shadowBlur: 8,
          textStyle: { color: '#f1f5f9', fontSize: 11 },
          formatter: (params: any) => {
            return `<div class="font-mono p-1">
              <span style="color:#94a3b8">Load Current:</span> <b>${params[0].name} A</b><br/>
              <span style="color:#38bdf8">●</span> ${params[0].seriesName}: <b>${params[0].value} mm</b><br/>
              <span style="color:#2dd4bf">●</span> ${params[1].seriesName}: <b>${params[1].value} mm</b>
            </div>`;
          }
        },
        legend: {
          data: ['IPC-2221 Width', 'IPC-2152 Width'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          top: 0
        },
        grid: { left: '10%', right: '10%', bottom: '22%', top: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: currents,
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          name: 'Current (A)',
          nameTextStyle: { color: '#94a3b8', fontSize: 8 }
        },
        yAxis: {
          type: 'value',
          name: 'Width (mm)',
          nameTextStyle: { color: '#94a3b8', fontSize: 8 },
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
            borderColor: 'rgba(45, 212, 191, 0.15)',
            handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
            handleSize: '110%',
            handleStyle: {
              color: '#2dd4bf',
              shadowBlur: 5,
              shadowColor: 'rgba(45, 212, 191, 0.5)'
            },
            textStyle: { color: '#94a3b8', fontSize: 9 },
            fillerColor: 'rgba(45, 212, 191, 0.05)',
            dataBackground: {
              lineStyle: { color: '#2dd4bf', width: 1 },
              areaStyle: { color: 'rgba(45, 212, 191, 0.02)' }
            },
            selectedDataBackground: {
              lineStyle: { color: '#2dd4bf', width: 1.5 },
              areaStyle: { color: 'rgba(45, 212, 191, 0.1)' }
            }
          }
        ],
        series: [
          {
            name: 'IPC-2221 Width',
            type: 'line',
            data: widthIPC2221,
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
            name: 'IPC-2152 Width',
            type: 'line',
            data: widthIPC2152,
            smooth: true,
            lineStyle: { 
              color: '#2dd4bf', 
              width: 3,
              shadowColor: 'rgba(45, 212, 191, 0.8)',
              shadowBlur: 8
            },
            showSymbol: false
          }
        ]
      };
    } else if (activeTab === 'via') {
      const diameters: number[] = [];
      const capacities: number[] = [];
      const resistances: number[] = [];
      const k_via = viaInternal ? 0.024 : 0.048;
      const t_mil = (viaPlating / 1000.0) / 0.0254;
      const derating = viaCount > 1 ? Math.max(0.5, 1.0 - 0.05 * (viaCount - 1)) : 1.0;
      const temp_work = 25.0 + viaTempRise;
      const rho = 1.724e-8 * (1.0 + 0.00393 * (temp_work - 25.0));
      for (let i = 0; i <= 20; i++) {
        const d = 0.1 + (i / 20) * 1.9;
        diameters.push(parseFloat(d.toFixed(2)));
        const d_mil = d / 0.0254;
        const area_sq_mils = Math.PI * d_mil * t_mil;
        const i_max_single = k_via * Math.pow(viaTempRise, 0.44) * Math.pow(area_sq_mils, 0.725);
        const i_total = viaCount * i_max_single * derating;
        const val1 = parseFloat(i_total.toFixed(2));
        capacities.push(Number.isFinite(val1) ? val1 : 0);

        const d_outer = d * 1e-3;
        const t_plating = viaPlating * 1e-6;
        const d_inner = Math.max(0.0, d_outer - 2.0 * t_plating);
        const area_cu = (Math.PI / 4.0) * (d_outer * d_outer - d_inner * d_inner);
        const r_via_single = rho * (viaHeight * 1e-3) / area_cu;
        const r_via_total = (r_via_single / viaCount) * 1000.0;
        const val2 = parseFloat(r_via_total.toFixed(2));
        resistances.push(Number.isFinite(val2) ? val2 : 0);
      }

      return {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: '#f59e0b',
          borderWidth: 1.5,
          shadowColor: 'rgba(245, 158, 11, 0.4)',
          shadowBlur: 8,
          textStyle: { color: '#f1f5f9', fontSize: 11 },
          formatter: (params: any) => {
            return `<div class="font-mono p-1">
              <span style="color:#94a3b8">Via Drill Dia:</span> <b>${params[0].name} mm</b><br/>
              <span style="color:#f59e0b">●</span> ${params[0].seriesName}: <b>${params[0].value} A</b><br/>
              <span style="color:#a855f7">●</span> ${params[1].seriesName}: <b>${params[1].value} mΩ</b>
            </div>`;
          }
        },
        legend: {
          data: ['Total Ampacity', 'Equivalent Resistance'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          top: 0
        },
        grid: { left: '10%', right: '10%', bottom: '22%', top: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: diameters,
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          name: 'Diameter (mm)',
          nameTextStyle: { color: '#94a3b8', fontSize: 8 }
        },
        yAxis: [
          {
            type: 'value',
            name: 'Current (A)',
            nameTextStyle: { color: '#94a3b8', fontSize: 8 },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
          },
          {
            type: 'value',
            name: 'Resistance (mΩ)',
            nameTextStyle: { color: '#94a3b8', fontSize: 8 },
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
            borderColor: 'rgba(245, 158, 11, 0.15)',
            handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
            handleSize: '110%',
            handleStyle: {
              color: '#f59e0b',
              shadowBlur: 5,
              shadowColor: 'rgba(245, 158, 11, 0.5)'
            },
            textStyle: { color: '#94a3b8', fontSize: 9 },
            fillerColor: 'rgba(245, 158, 11, 0.05)',
            dataBackground: {
              lineStyle: { color: '#f59e0b', width: 1 },
              areaStyle: { color: 'rgba(245, 158, 11, 0.02)' }
            },
            selectedDataBackground: {
              lineStyle: { color: '#f59e0b', width: 1.5 },
              areaStyle: { color: 'rgba(245, 158, 11, 0.1)' }
            }
          }
        ],
        series: [
          {
            name: 'Total Ampacity',
            type: 'line',
            data: capacities,
            smooth: true,
            lineStyle: { 
              color: '#f59e0b', 
              width: 3,
              shadowColor: 'rgba(245, 158, 11, 0.8)',
              shadowBlur: 8
            },
            showSymbol: false
          },
          {
            name: 'Equivalent Resistance',
            type: 'line',
            yAxisIndex: 1,
            data: resistances,
            smooth: true,
            lineStyle: { 
              color: '#a855f7', 
              width: 3,
              shadowColor: 'rgba(168, 85, 247, 0.8)',
              shadowBlur: 8
            },
            showSymbol: false
          }
        ]
      };
    } else { // impedance
      const widths: number[] = [];
      const z0s: number[] = [];
      const zdiffs: number[] = [];
      const h_mil = impH / 0.0254;
      const t_mil = (impT / 1000.0) / 0.0254;
      const s_mil = impS / 0.0254;
      for (let i = 0; i <= 20; i++) {
        const w = 0.1 + (i / 20) * 1.9;
        widths.push(parseFloat(w.toFixed(2)));
        const w_mil = w / 0.0254;
        let z0 = 0;
        if (impStruct === 'microstrip') {
          const term = (5.98 * h_mil) / (0.8 * w_mil + t_mil);
          z0 = term > 0 ? (87.0 / Math.sqrt(impEr + 1.41)) * Math.log(term) : 0;
        } else { // stripline
          const term = (1.9 * h_mil) / (0.8 * w_mil + t_mil);
          z0 = term > 0 ? (60.0 / Math.sqrt(impEr)) * Math.log(term) : 0;
        }
        const val1 = parseFloat(z0.toFixed(2));
        z0s.push(Number.isFinite(val1) ? val1 : 0);

        if (impIsDiff) {
          let factor = 1.0;
          if (impStruct === 'microstrip') {
            factor = 1.0 - 0.48 * Math.exp(-0.96 * s_mil / h_mil);
          } else {
            factor = 1.0 - 0.347 * Math.exp(-2.9 * s_mil / h_mil);
          }
          const val2 = parseFloat((2.0 * z0 * factor).toFixed(2));
          zdiffs.push(Number.isFinite(val2) ? val2 : 0);
        }
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
          formatter: (params: any) => {
            let html = `<div class="font-mono p-1">
              <span style="color:#94a3b8">Trace Width:</span> <b>${params[0].name} mm</b><br/>
              <span style="color:#14b8a6">●</span> ${params[0].seriesName}: <b>${params[0].value} Ω</b>`;
            if (params[1]) {
              html += `<br/><span style="color:#ec4899">●</span> ${params[1].seriesName}: <b>${params[1].value} Ω</b>`;
            }
            html += `</div>`;
            return html;
          }
        },
        legend: {
          data: impIsDiff ? ['Single-Ended Z0', 'Differential Zdiff'] : ['Single-Ended Z0'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          top: 0
        },
        grid: { left: '10%', right: '10%', bottom: '22%', top: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: widths,
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          name: 'Width (mm)',
          nameTextStyle: { color: '#94a3b8', fontSize: 8 }
        },
        yAxis: {
          type: 'value',
          name: 'Impedance (Ω)',
          nameTextStyle: { color: '#94a3b8', fontSize: 8 },
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
            name: 'Single-Ended Z0',
            type: 'line',
            data: z0s,
            smooth: true,
            lineStyle: { 
              color: '#14b8a6', 
              width: 3,
              shadowColor: 'rgba(20, 184, 166, 0.8)',
              shadowBlur: 8
            },
            showSymbol: false
          },
          ...(impIsDiff ? [{
            name: 'Differential Zdiff',
            type: 'line',
            data: zdiffs,
            smooth: true,
            lineStyle: { 
              color: '#ec4899', 
              width: 3,
              shadowColor: 'rgba(236, 72, 153, 0.8)',
              shadowBlur: 8
            },
            showSymbol: false
          }] : [])
        ]
      };
    }
  };

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
    panelKey: 'layout_pcbtoolbox_v4',
    activeTab: activeTab,
    defaultCards: currentLayoutConfig.defaultCards,
    defaultColumns: currentLayoutConfig.defaultColumns,
    defaultSpans: currentLayoutConfig.defaultSpans,
    defaultHeights: currentLayoutConfig.defaultHeights
  });

  const applyCopperPreset = (oz: number) => {
    setTraceCopperOz(oz);
  };

  const applyErPreset = (val: number) => {
    setImpEr(val);
  };

  const handleTraceCalc = async () => {
    setTraceError(null);
    try {
      const response = await apiFetch('/api/calculate/pcb_toolbox/trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current: traceCurrent,
          temp_rise: traceTempRise,
          copper_oz: traceCopperOz,
          length_mm: traceLength,
          is_internal: traceInternal,
          temp_amb: traceTempAmb
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        const errMsg = Array.isArray(err.detail) ? err.detail.map((d: any) => d.loc.join('.') + ': ' + d.msg).join(', ') : (err.detail || 'Trace calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setTraceRes(data);
    } catch (e: any) {
      setTraceError(e.message);
    }
  };

  const handleViaCalc = async () => {
    setViaError(null);
    try {
      const response = await apiFetch('/api/calculate/pcb_toolbox/via', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dia_mm: viaDia,
          plating_um: viaPlating,
          height_mm: viaHeight,
          count: viaCount,
          current: viaCurrent,
          temp_rise: viaTempRise,
          is_internal: viaInternal,
          is_solder_filled: viaSolderFilled
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        const errMsg = Array.isArray(err.detail) ? err.detail.map((d: any) => d.loc.join('.') + ': ' + d.msg).join(', ') : (err.detail || 'Via calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setViaRes(data);
    } catch (e: any) {
      setViaError(e.message);
    }
  };

  const handleImpedanceCalc = async () => {
    setImpError(null);
    try {
      const response = await apiFetch('/api/calculate/pcb_toolbox/impedance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          er: impEr,
          w_mm: impW,
          h_mm: impH,
          t_um: impT,
          struct_type: impStruct,
          is_diff: impIsDiff,
          s_mm: impS
        })
      });
      if (activeTabRef.current !== activeTab) return;
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        const errMsg = Array.isArray(err.detail) ? err.detail.map((d: any) => d.loc.join('.') + ': ' + d.msg).join(', ') : (err.detail || 'Impedance calculation failed');
        throw new Error(errMsg);
      }
      const data = await response.json();
      setImpRes(data);
    } catch (e: any) {
      setImpError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'trace') handleTraceCalc();
  }, [traceCurrent, traceTempRise, traceCopperOz, traceLength, traceInternal, traceTempAmb, activeTab]);

  useEffect(() => {
    if (activeTab === 'via') handleViaCalc();
  }, [viaDia, viaPlating, viaHeight, viaCount, viaCurrent, viaTempRise, viaInternal, viaSolderFilled, activeTab]);

  useEffect(() => {
    if (activeTab === 'impedance') handleImpedanceCalc();
  }, [impEr, impW, impH, impT, impStruct, impIsDiff, impS, activeTab]);

  const activeErrors = 
    activeTab === 'trace' ? traceError : 
    activeTab === 'via' ? viaError : impError;

  const renderTraceInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Continuous Current I_max (A)</label>
          <input type="number" step="0.5" value={traceCurrent} onChange={(e) => setTraceCurrent(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Allowed Temp Rise ΔT (°C)</label>
          <input type="number" step="1" value={traceTempRise} onChange={(e) => setTraceTempRise(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="border border-slate-850 rounded-lg p-2.5 bg-slate-900/10 space-y-2">
        <span className="text-[9px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Trace Copper Weight</span>
        <div className="grid grid-cols-3 gap-1">
          {[[0.5, '0.5 oz (18μm)'], [1.0, '1 oz (35μm)'], [2.0, '2 oz (70μm)']].map(([val, label]) => (
            <button
              key={val}
              onClick={() => applyCopperPreset(val as number)}
              className={`py-1 text-[8px] border-0 rounded cursor-pointer transition-colors ${traceCopperOz === val ? 'bg-teal-600 text-white font-bold' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-850'}`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex flex-col gap-1 mt-1">
          <label className="text-[8px] text-slate-500">Custom Copper oz</label>
          <input type="number" step="0.1" value={traceCopperOz} onChange={(e) => setTraceCopperOz(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Total Trace Length (mm)</label>
          <input type="number" step="10" value={traceLength} onChange={(e) => setTraceLength(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Ambient Temp Ta (°C)</label>
          <input type="number" step="1" value={traceTempAmb} onChange={(e) => setTraceTempAmb(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="flex items-center gap-2 border-t border-slate-800 pt-3">
        <input
          type="checkbox"
          id="traceInternal"
          checked={traceInternal}
          onChange={(e) => setTraceInternal(e.target.checked)}
          className="rounded border-slate-800 bg-slate-950 text-teal-500 focus:ring-teal-500 h-3.5 w-3.5 cursor-pointer"
        />
        <label htmlFor="traceInternal" className="text-[10px] font-bold text-slate-355 cursor-pointer select-none">
          Internal Layer Routing
        </label>
      </div>
    </div>
  );

  const renderViaInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Via Drill Dia d (mm)</label>
          <input type="number" step="0.05" value={viaDia} onChange={(e) => setViaDia(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Plating Thickness (μm)</label>
          <input type="number" step="1" value={viaPlating} onChange={(e) => setViaPlating(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Board Thickness / Height h (mm)</label>
          <input type="number" step="0.1" value={viaHeight} onChange={(e) => setViaHeight(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Parallel Via Count</label>
          <input type="number" min="1" value={viaCount} onChange={(e) => setViaCount(parseInt(e.target.value) || 1)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 border-t border-slate-800 pt-3">
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Total Current (A)</label>
          <input type="number" step="0.5" value={viaCurrent} onChange={(e) => setViaCurrent(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[8px] text-slate-550">Allowed Temp Rise (°C)</label>
          <input type="number" step="1" value={viaTempRise} onChange={(e) => setViaTempRise(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="flex flex-col gap-2.5 pt-1.5 border-t border-slate-800/80">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="viaInternal"
            checked={viaInternal}
            onChange={(e) => setViaInternal(e.target.checked)}
            className="rounded border-slate-800 bg-slate-950 text-teal-500 focus:ring-teal-500 h-3.5 w-3.5 cursor-pointer"
          />
          <label htmlFor="viaInternal" className="text-[10px] font-bold text-slate-350 cursor-pointer select-none">
            Internal Layer Routing Via
          </label>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="viaSolderFilled"
            checked={viaSolderFilled}
            onChange={(e) => setViaSolderFilled(e.target.checked)}
            className="rounded border-slate-800 bg-slate-950 text-teal-500 focus:ring-teal-500 h-3.5 w-3.5 cursor-pointer"
          />
          <label htmlFor="viaSolderFilled" className="text-[10px] font-bold text-slate-355 cursor-pointer select-none">
            Solder-Filled Via Barrel
          </label>
        </div>
      </div>
    </div>
  );

  const renderImpedanceInputs = () => (
    <div className="space-y-3.5 font-sans">
      <div className="border border-slate-850 rounded-lg p-2.5 bg-slate-900/10 space-y-2">
        <span className="text-[9px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Substrate Relative Permittivity (Er)</span>
        <div className="grid grid-cols-4 gap-1">
          {[['FR-4', 4.2], ['Rogers', 3.48], ['Teflon', 2.1], ['Polyimide', 3.5]].map(([label, val]) => (
            <button
              key={label}
              onClick={() => applyErPreset(val as number)}
              className={`py-1 text-[8.5px] border-0 rounded cursor-pointer transition-colors ${impEr === val ? 'bg-teal-600 text-white font-bold' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-850'}`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex flex-col gap-1 mt-1">
          <label className="text-[8px] text-slate-500">Relative Permittivity Er</label>
          <input type="number" step="0.05" value={impEr} onChange={(e) => setImpEr(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
        </div>
      </div>

      <div className="border border-slate-850 rounded-lg p-2.5 bg-slate-900/10 space-y-3 border-t border-slate-800 pt-3">
        <span className="text-[9px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Geometry Specifications</span>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-500">Topology Structure</label>
            <div className="grid grid-cols-2 gap-1 bg-slate-950 p-0.5 rounded border border-slate-850">
              <button onClick={() => setImpStruct('microstrip')} className={`py-1 text-[8.5px] border-0 rounded cursor-pointer ${impStruct === 'microstrip' ? 'bg-teal-500/20 text-teal-400 font-bold' : 'bg-transparent text-slate-400 hover:text-white'}`}>Microstrip</button>
              <button onClick={() => setImpStruct('stripline')} className={`py-1 text-[8.5px] border-0 rounded cursor-pointer ${impStruct === 'stripline' ? 'bg-teal-500/20 text-teal-400 font-bold' : 'bg-transparent text-slate-400 hover:text-white'}`}>Stripline</button>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-500">Pair Mode</label>
            <div className="grid grid-cols-2 gap-1 bg-slate-950 p-0.5 rounded border border-slate-850">
              <button onClick={() => setImpIsDiff(false)} className={`py-1 text-[8.5px] border-0 rounded cursor-pointer ${!impIsDiff ? 'bg-teal-500/20 text-teal-400 font-bold' : 'bg-transparent text-slate-400 hover:text-white'}`}>Single-Ended</button>
              <button onClick={() => setImpIsDiff(true)} className={`py-1 text-[8.5px] border-0 rounded cursor-pointer ${impIsDiff ? 'bg-teal-500/20 text-teal-400 font-bold' : 'bg-transparent text-slate-400 hover:text-white'}`}>Differential</button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Trace Width w (mm)</label>
            <input type="number" step="0.05" value={impW} onChange={(e) => setImpW(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Dielectric Height h (mm)</label>
            <input type="number" step="0.05" value={impH} onChange={(e) => setImpH(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[8px] text-slate-550">Copper Thickness t (μm)</label>
            <input type="number" value={impT} onChange={(e) => setImpT(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
          </div>
          {impIsDiff && (
            <div className="flex flex-col gap-1">
              <label className="text-[8px] text-slate-550">Trace Spacing s (mm)</label>
              <input type="number" step="0.05" value={impS} onChange={(e) => setImpS(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none font-mono" />
            </div>
          )}
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
            <h1 className="text-base font-bold text-white tracking-tight">PCB Electromagnetic & Ampacity Toolbox</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">Calculate trace ampacity and thermal rise; compute via parasitics and thermal resistance; design microstrip and stripline controlled impedance.</p>
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
          { id: 'trace', label: '1. PCB Trace Ampacity & Temp Rise', icon: null},
          { id: 'via', label: '2. Via Current Capacity & Heating', icon: null},
          { id: 'impedance', label: '3. Single-Ended & Differential Impedance', icon: null}
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
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Input Operating Conditions</span>
                  </div>
                  {activeTab === 'trace' && renderTraceInputs()}
                  {activeTab === 'via' && renderViaInputs()}
                  {activeTab === 'impedance' && renderImpedanceInputs()}
                </div>
              )}

              {key === 'theory' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <BookOpen className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">Physical Equations & Mathematical Models</span>
                  </div>
                  <div className="text-[10px] text-slate-400 space-y-4 leading-relaxed font-sans">
                    {activeTab === 'trace' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">IPC-2221 Empirical Thermal Formula:</span>
                          <Latex math="I = K \cdot \Delta T^{0.44} \cdot A^{0.725}" block />
                          <p>External trace: K = 0.048, Internal trace: K = 0.024. Cross-sectional area A in mil².</p>
                        </div>
                      </>
                    )}
                    {activeTab === 'via' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">1. Via Resistance & Parasitic Inductance Model:</span>
                          <Latex math="R_{via} = \rho \cdot \frac{h}{\pi (d - t) \cdot t} \quad L_{via} \approx 0.2 \cdot h \cdot \left( \ln\left(\frac{4h}{d}\right) + 1 \right)" block />
                        </div>
                      </>
                    )}
                    {activeTab === 'impedance' && (
                      <>
                        <div className="space-y-1">
                          <span className="font-semibold text-slate-350">Microstrip Characteristic Impedance Equation:</span>
                          <Latex math="Z_0 = \frac{87}{\sqrt{\epsilon_r + 1.41}} \ln\left( \frac{5.98 h}{0.8 w + t} \right)" block />
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
                    <span className="text-xs font-bold text-white">Core Calculation Results</span>
                  </div>

                  {activeTab === 'trace' && traceRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">IPC-2152 Recommended Width</span>
                        <span className="text-xs font-bold text-blue-400">{(traceRes.width_mm_2152 ?? 0).toFixed(2)} mm</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">IPC-2221 Recommended Width</span>
                        <span className="text-xs font-bold text-blue-400">{(traceRes.width_mm ?? 0).toFixed(2)} mm</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Trace Resistance R</span>
                        <span className="text-xs font-bold text-slate-200">{(traceRes.r_trace_ohm ?? 0).toFixed(4)} Ω</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Full-Load Voltage Drop</span>
                        <span className="text-xs font-bold text-orange-400">{(traceRes.v_drop_v ?? 0).toFixed(3)} V</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Trace Power Loss Ploss</span>
                        <span className="text-xs font-bold text-rose-400">{(traceRes.p_loss_w ?? 0).toFixed(2)} W</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Steady-State Operating Temp</span>
                        <span className="text-xs font-bold text-emerald-400">{(traceRes.temp_work_c ?? 0).toFixed(1)} °C</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'via' && viaRes && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-200 font-mono">
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Single Via Ampacity</span>
                        <span className="text-xs font-bold text-white">{(viaRes.i_max_single_a ?? 0).toFixed(2)} A</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Array Thermal Derating</span>
                        <span className="text-xs font-bold text-white">{((viaRes.derating_factor ?? 1) * 100).toFixed(0)} %</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5 col-span-2">
                        <span className="text-[8px] text-slate-400 font-sans font-bold text-teal-400">Total Parallel Ampacity</span>
                        <span className="text-xs font-bold text-teal-400">{(viaRes.i_total_capacity_a ?? 0).toFixed(2)} A</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Array Resistance</span>
                        <span className="text-xs font-bold text-slate-350">{(viaRes.r_via_total_mohm ?? 0).toFixed(2)} mΩ</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Voltage Drop</span>
                        <span className="text-xs font-bold text-orange-400">{(viaRes.v_drop_mv ?? 0).toFixed(2)} mV</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Parasitic Inductance L_via</span>
                        <span className="text-xs font-bold text-slate-200">{(viaRes.l_via_nh ?? 0).toFixed(3)} nH</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Parasitic Capacitance C_via</span>
                        <span className="text-xs font-bold text-slate-200">{(viaRes.c_via_pf ?? 0).toFixed(3)} pF</span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'impedance' && impRes && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-slate-200 font-mono">
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5 col-span-2">
                        <span className="text-[8px] text-slate-400 font-sans">Single-Ended Characteristic Impedance Z0</span>
                        <span className="text-sm font-bold text-blue-400">{(impRes.z0_ohm ?? 0).toFixed(2)} Ω</span>
                      </div>
                      <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-sans">Propagation Delay</span>
                        <span className="text-xs font-bold text-slate-350">{(impRes.delay_ps_mm ?? 0).toFixed(2)} ps/mm</span>
                      </div>
                      {impIsDiff && (
                        <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/40 flex flex-col gap-0.5 col-span-3 border-t border-teal-500/20">
                          <span className="text-[8px] text-teal-400 font-sans">Differential Characteristic Impedance Zdiff</span>
                          <span className="text-sm font-bold text-teal-400">{(impRes.z_diff_ohm ?? 0).toFixed(2)} Ω</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {key === 'schematic' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <Compass className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-bold text-white">PCB Cross-Section Geometric Model (SVG)</span>
                  </div>

                  <div className="w-full h-[180px] flex items-center justify-center bg-slate-950/20 rounded-xl border border-slate-850 p-2">
                    {activeTab === 'trace' && (
                      <svg width="100%" height="100%" viewBox="0 0 320 120" className="text-slate-350 max-w-[500px] max-h-[180px]">
                        <defs>
                          <style>{`
                            @keyframes flow-horizontal {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-flow-trace {
                              stroke-dasharray: 6, 6;
                              animation: flow-horizontal 1.2s linear infinite;
                              filter: url(#neon-glow-cyan-trace);
                            }
                          `}</style>
                          <pattern id="fr4-pattern" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
                            <path d="M 0,8 L 8,0 M 0,0 L 8,8" stroke="#166534" strokeWidth="0.5" strokeOpacity="0.25" />
                          </pattern>
                          <filter id="neon-glow-cyan-trace" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-green-trace" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-amber-trace" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <linearGradient id="neon-fr4-grad-trace" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#0f766e" />
                            <stop offset="100%" stopColor="#064e3b" />
                          </linearGradient>
                          <linearGradient id="neon-copper-grad-trace" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#f59e0b" />
                            <stop offset="50%" stopColor="#fbbf24" />
                            <stop offset="100%" stopColor="#b45309" />
                          </linearGradient>
                          <marker id="arrow-start" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                            <path d="M 10 0 L 0 5 L 10 10 z" fill="#fbbf24" />
                          </marker>
                          <marker id="arrow-end" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#fbbf24" />
                          </marker>
                        </defs>

                        <rect x="20" y="45" width="280" height="40" fill="url(#neon-fr4-grad-trace)" fillOpacity="0.45" stroke="#166534" strokeWidth="1.5" rx="2" filter="url(#neon-glow-green-trace)" />
                        <rect x="20" y="45" width="280" height="40" fill="url(#fr4-pattern)" rx="2" />

                        <rect x="20" y="85" width="280" height="4" fill="url(#neon-copper-grad-trace)" stroke="#d97706" strokeWidth="0.3" filter="url(#neon-glow-amber-trace)" />
                        <text x="160" y="98" textAnchor="middle" fill="#475569" className="text-[6px] font-mono">GND Reference Plane</text>

                        {traceInternal ? (
                          <>
                            <rect x="100" y="60" width="120" height="10" fill="url(#neon-copper-grad-trace)" stroke="#d97706" strokeWidth="0.5" rx="0.5" filter="url(#neon-glow-amber-trace)" />
                            <line x1="102" y1="65" x2="218" y2="65" stroke="#2dd4bf" strokeWidth="2" className="animate-flow-trace" />
                            <text x="160" y="58" textAnchor="middle" fill="#2dd4bf" className="text-[7px] font-bold font-mono" filter="url(#neon-glow-cyan-trace)">Internal Trace W x T</text>
                            <text x="30" y="58" fill="#86efac" className="text-[6.5px]">Dielectric H1</text>
                            <text x="30" y="78" fill="#86efac" className="text-[6.5px]">Dielectric H2</text>
                          </>
                        ) : (
                          <>
                            <rect x="100" y="35" width="120" height="10" fill="url(#neon-copper-grad-trace)" stroke="#d97706" strokeWidth="0.5" rx="0.5" filter="url(#neon-glow-amber-trace)" />
                            <line x1="102" y1="40" x2="218" y2="40" stroke="#38bdf8" strokeWidth="2" className="animate-flow-trace" />
                            <line x1="100" y1="28" x2="220" y2="28" stroke="#fbbf24" strokeWidth="0.8" markerStart="url(#arrow-start)" markerEnd="url(#arrow-end)" />
                            <text x="160" y="24" textAnchor="middle" fill="#fbbf24" className="text-[7px] font-mono">Width W = {traceLength} mm</text>
                            <line x1="225" y1="35" x2="225" y2="45" stroke="#fbbf24" strokeWidth="0.8" />
                            <text x="235" y="41" fill="#fbbf24" className="text-[6.5px] font-mono">Thickness T</text>
                            <text x="160" y="72" textAnchor="middle" fill="#86efac" className="text-[7.5px] font-bold">FR4 Substrate Layer</text>
                          </>
                        )}
                      </svg>
                    )}

                    {activeTab === 'via' && (
                      <svg width="100%" height="100%" viewBox="0 0 320 120" className="text-slate-350 max-w-[500px] max-h-[180px]">
                        <defs>
                          <style>{`
                            @keyframes flow-vertical {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-flow-via {
                              stroke-dasharray: 6, 6;
                              animation: flow-vertical 1.2s linear infinite;
                              filter: url(#neon-glow-cyan-via);
                            }
                          `}</style>
                          <pattern id="fr4-pattern" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
                            <path d="M 0,8 L 8,0 M 0,0 L 8,8" stroke="#166534" strokeWidth="0.5" strokeOpacity="0.25" />
                          </pattern>
                          <filter id="neon-glow-cyan-via" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-green-via" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-amber-via" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <linearGradient id="neon-fr4-grad-via" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#0f766e" />
                            <stop offset="100%" stopColor="#064e3b" />
                          </linearGradient>
                          <linearGradient id="neon-copper-grad-via" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#f59e0b" />
                            <stop offset="50%" stopColor="#fbbf24" />
                            <stop offset="100%" stopColor="#b45309" />
                          </linearGradient>
                          <marker id="arrow-start-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                            <path d="M 10 0 L 0 5 L 10 10 z" fill="#3b82f6" />
                          </marker>
                          <marker id="arrow-end-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
                          </marker>
                        </defs>

                        <rect x="40" y="25" width="240" height="60" fill="url(#neon-fr4-grad-via)" fillOpacity="0.45" stroke="#166534" strokeWidth="1.5" rx="2" filter="url(#neon-glow-green-via)" />
                        <rect x="40" y="25" width="240" height="60" fill="url(#fr4-pattern)" rx="2" />

                        <rect x="80" y="19" width="160" height="6" fill="url(#neon-copper-grad-via)" stroke="#d97706" strokeWidth="0.5" filter="url(#neon-glow-amber-via)" />
                        <rect x="80" y="85" width="160" height="6" fill="url(#neon-copper-grad-via)" stroke="#d97706" strokeWidth="0.5" filter="url(#neon-glow-amber-via)" />

                        <rect x="130" y="25" width="5" height="60" fill="url(#neon-copper-grad-via)" filter="url(#neon-glow-amber-via)" />
                        <rect x="185" y="25" width="5" height="60" fill="url(#neon-copper-grad-via)" filter="url(#neon-glow-amber-via)" />

                        <rect x="135" y="25" width="50" height="60" fill={viaSolderFilled ? "rgba(100, 116, 139, 0.6)" : "rgba(2, 6, 23, 0.85)"} stroke={viaSolderFilled ? "#cbd5e1" : "#1e293b"} strokeWidth="0.5" />
                        
                        <line x1="132.5" y1="25" x2="132.5" y2="85" stroke="#38bdf8" strokeWidth="1.5" className="animate-flow-via" />
                        <line x1="187.5" y1="25" x2="187.5" y2="85" stroke="#38bdf8" strokeWidth="1.5" className="animate-flow-via" />

                        <text x="160" y="57" textAnchor="middle" fill={viaSolderFilled ? "#cbd5e1" : "#475569"} className="text-[7px] font-mono">
                          {viaSolderFilled ? 'Solder-Filled' : 'Hollow Barrel'}
                        </text>

                        <line x1="130" y1="52" x2="190" y2="52" stroke="#3b82f6" strokeWidth="0.8" markerStart="url(#arrow-start-blue)" markerEnd="url(#arrow-end-blue)" />
                        <text x="160" y="47" textAnchor="middle" fill="#60a5fa" className="text-[7px] font-mono" filter="url(#neon-glow-cyan-via)">Drill Dia D = {viaDia} mm</text>
                        <line x1="120" y1="35" x2="130" y2="35" stroke="#fbbf24" strokeWidth="0.8" />
                        <text x="96" y="38" fill="#fbbf24" className="text-[6.5px] font-mono">Barrel Plating t</text>
                      </svg>
                    )}

                    {activeTab === 'impedance' && (
                      <svg width="100%" height="100%" viewBox="0 0 320 120" className="text-slate-350 max-w-[500px] max-h-[180px]">
                        <defs>
                          <style>{`
                            @keyframes flow-horizontal {
                              to { stroke-dashoffset: -20; }
                            }
                            .animate-flow-cyan {
                              stroke-dasharray: 6, 6;
                              animation: flow-horizontal 1.2s linear infinite;
                              filter: url(#neon-glow-cyan-imp);
                            }
                            .animate-flow-purple {
                              stroke-dasharray: 6, 6;
                              animation: flow-horizontal 1.2s linear infinite;
                              filter: url(#neon-glow-purple-imp);
                            }
                          `}</style>
                          <pattern id="fr4-pattern" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
                            <path d="M 0,8 L 8,0 M 0,0 L 8,8" stroke="#166534" strokeWidth="0.5" strokeOpacity="0.25" />
                          </pattern>
                          <filter id="neon-glow-cyan-imp" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-purple-imp" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-green-imp" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <filter id="neon-glow-amber-imp" x="-25%" y="-25%" width="150%" height="150%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                            <feMerge>
                              <feMergeNode in="blur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <linearGradient id="neon-fr4-grad-imp" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#0f766e" />
                            <stop offset="100%" stopColor="#064e3b" />
                          </linearGradient>
                          <linearGradient id="neon-copper-grad-imp" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#f59e0b" />
                            <stop offset="50%" stopColor="#fbbf24" />
                            <stop offset="100%" stopColor="#b45309" />
                          </linearGradient>
                        </defs>

                        <rect x="25" y="45" width="270" height="40" fill="url(#neon-fr4-grad-imp)" fillOpacity="0.45" stroke="#166534" strokeWidth="1.5" rx="2" filter="url(#neon-glow-green-imp)" />
                        <rect x="25" y="45" width="270" height="40" fill="url(#fr4-pattern)" rx="2" />

                        <rect x="25" y="85" width="270" height="5" fill="url(#neon-copper-grad-imp)" stroke="#d97706" strokeWidth="0.3" filter="url(#neon-glow-amber-imp)" />
                        
                        {impStruct === 'stripline' && (
                          <rect x="25" y="20" width="270" height="5" fill="url(#neon-copper-grad-imp)" stroke="#d97706" strokeWidth="0.3" filter="url(#neon-glow-amber-imp)" />
                        )}

                        {impIsDiff ? (
                          <>
                            <rect x="90" y={impStruct === 'stripline' ? 55 : 35} width="45" height="10" fill="url(#neon-copper-grad-imp)" stroke="#d97706" strokeWidth="0.5" rx="0.5" filter="url(#neon-glow-amber-imp)" />
                            <rect x="180" y={impStruct === 'stripline' ? 55 : 35} width="45" height="10" fill="url(#neon-copper-grad-imp)" stroke="#d97706" strokeWidth="0.5" rx="0.5" filter="url(#neon-glow-amber-imp)" />
                            
                            <line x1="92" y1={impStruct === 'stripline' ? 60 : 40} x2="133" y2={impStruct === 'stripline' ? 60 : 40} stroke="#38bdf8" strokeWidth="2" className="animate-flow-cyan" />
                            <line x1="182" y1={impStruct === 'stripline' ? 60 : 40} x2="223" y2={impStruct === 'stripline' ? 60 : 40} stroke="#ec4899" strokeWidth="2" className="animate-flow-purple" />

                            <line x1="90" y1="28" x2="135" y2="28" stroke="#fbbf24" strokeWidth="0.8" markerStart="url(#arrow-start)" markerEnd="url(#arrow-end)" />
                            <text x="112.5" y="24" textAnchor="middle" fill="#fbbf24" className="text-[6.5px] font-mono">W</text>

                            <line x1="135" y1="28" x2="180" y2="28" stroke="#3b82f6" strokeWidth="0.8" markerStart="url(#arrow-start-blue)" markerEnd="url(#arrow-end-blue)" />
                            <text x="157.5" y="24" textAnchor="middle" fill="#60a5fa" className="text-[6.5px] font-mono">S = {impS} mm</text>
                          </>
                        ) : (
                          <>
                            <rect x="110" y={impStruct === 'stripline' ? 55 : 35} width="100" height="10" fill="url(#neon-copper-grad-imp)" stroke="#d97706" strokeWidth="0.5" rx="0.5" filter="url(#neon-glow-amber-imp)" />
                            <line x1="112" y1={impStruct === 'stripline' ? 60 : 40} x2="208" y2={impStruct === 'stripline' ? 60 : 40} stroke="#38bdf8" strokeWidth="2" className="animate-flow-cyan" />
                            <line x1="110" y1="28" x2="210" y2="28" stroke="#fbbf24" strokeWidth="0.8" markerStart="url(#arrow-start)" markerEnd="url(#arrow-end)" />
                            <text x="160" y="24" textAnchor="middle" fill="#fbbf24" className="text-[7.5px] font-mono">W = {impW} mm</text>
                          </>
                        )}

                        <line x1="285" y1="45" x2="285" y2="85" stroke="#10b981" strokeWidth="0.8" />
                        <line x1="282" y1="45" x2="288" y2="45" stroke="#10b981" strokeWidth="0.8" />
                        <line x1="282" y1="85" x2="288" y2="85" stroke="#10b981" strokeWidth="0.8" />
                        <text x="292" y="68" fill="#10b981" className="text-[7px] font-mono">H = {impH} mm</text>
                      </svg>
                    )}
                  </div>
                </div>
              )}

              {key === 'charts' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <span className="text-xs font-bold text-white block border-b border-slate-800 pb-2 mb-2">Parametric Sweep Curves</span>
                  <div className="w-full h-[180px]">
                    <ReactECharts option={getChartOption()} notMerge={true} style={{ width: '100%', height: '100%' }} />
                  </div>
                </div>
              )}

              {key === 'drc' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-bold text-white">DRC Design Rule Check</span>
                  </div>

                  <div className="flex flex-col gap-2.5">
                    {activeTab === 'trace' && traceRes && (
                      <>
                        {traceTempRise > 30.0 ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Temperature Rise Excessive:</strong> Estimated trace thermal rise ({traceTempRise}°C) is high. Elevated current accelerates substrate aging and causes pad delamination. Increase trace width or copper weight (e.g. 2oz).</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Trace Ampacity Safe:</strong> Operating temperature rise is within safe derating limits.</span>
                          </div>
                        )}
                      </>
                    )}

                    {activeTab === 'via' && viaRes && (
                      <>
                        {viaCurrent > viaRes.i_total_capacity_a ? (
                          <div className="flex items-start gap-2 text-[10px] text-rose-350 border border-rose-500/20 bg-rose-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-500 mt-0.5" />
                            <span><strong>Via Ampacity Insufficient:</strong> Design current ({viaCurrent} A) exceeds total parallel via capacity ({viaRes.i_total_capacity_a.toFixed(2)} A). High risk of via barrel burnout. Add more parallel vias or widen drill diameter.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Via Ampacity Safe:</strong> Sufficient margin for parallel via array.</span>
                          </div>
                        )}
                      </>
                    )}

                    {activeTab === 'impedance' && impRes && (
                      <>
                        {Math.abs(impRes.z0_ohm - 50) > 10 && Math.abs(impRes.z_diff_ohm - 100) > 15 ? (
                          <div className="flex items-start gap-2 text-[10px] text-amber-300 border border-amber-500/20 bg-amber-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <Info className="w-3.5 h-3.5 shrink-0 text-amber-500 mt-0.5" />
                            <span><strong>Impedance Mismatch Advisory:</strong> Characteristic impedance ({impRes.z0_ohm.toFixed(1)} Ω) deviates from standard transmission line targets (e.g. 50Ω single-ended / 100Ω differential). May cause reflections and signal integrity degradation.</span>
                          </div>
                        ) : (
                          <div className="flex items-start gap-2 text-[10px] text-emerald-400 border border-emerald-500/20 bg-emerald-500/5 p-2 rounded-lg leading-relaxed font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500 mt-0.5" />
                            <span><strong>Characteristic Impedance Matched.</strong></span>
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
