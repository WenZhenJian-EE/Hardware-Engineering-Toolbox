import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import {
  ArrowLeft,
  CheckCircle2,
  Compass,
  ShieldAlert,
  TrendingUp,
  RefreshCw
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
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-xs text-slate-300" : "inline-block text-xs"} />;
};

const DIGITAL_PID_PRESETS = [
  {
    name: 'CM Buck 3.3V',
    tab: 'design',
    params: { mode: 0, vin: 12.0, vout: 3.3, iout: 2.0, l: 10.0, c: 47.0, fs: 100.0, vref: 3.3, kdiv: 1.0, fc: 5.0, pm: 60.0 }
  },
  {
    name: 'VM Buck 5.0V',
    tab: 'design',
    params: { mode: 1, vin: 12.0, vout: 5.0, iout: 3.0, l: 22.0, c: 100.0, fs: 200.0, vref: 3.3, kdiv: 0.66, fc: 10.0, pm: 55.0 }
  },
  {
    name: 'CM Boost 24V',
    tab: 'design',
    params: { mode: 2, vin: 12.0, vout: 24.0, iout: 1.0, l: 33.0, c: 47.0, fs: 150.0, vref: 3.3, kdiv: 0.137, fc: 2.0, pm: 50.0 }
  },
  {
    name: 'Lag Comp',
    tab: 's2z',
    params: { fz: 1.0, fp: 20.0, gain: 10.0, fs: 200.0, method: 'tustin' }
  },
  {
    name: 'Lead Comp',
    tab: 's2z',
    params: { fz: 5.0, fp: 25.0, gain: 5.0, fs: 250.0, method: 'tustin' }
  },
  {
    name: '1st Low-Pass (20k/1k)',
    tab: 'filter',
    params: { type: '1st', fs: 20000.0, fc: 1000.0 }
  },
  {
    name: '2nd Butterworth (10k/500)',
    tab: 'filter',
    params: { type: '2nd', fs: 10000.0, fc: 500.0 }
  }
];

interface DigitalPidPanelProps {
  onBack: () => void;
  setActiveModule?: any;
}

export default function DigitalPidPanel({ onBack, setActiveModule }: DigitalPidPanelProps) {
  const [activeTab, setActiveTab] = useTabHistoryState<'design' | 's2z' | 'filter'>(() => {
    const saved = localStorage.getItem('digital_pid_panel_active_tab');
    return (saved as 'design' | 's2z' | 'filter') || 'design';
  }, 'activeTab');

  const handleTabChange = (tab: 'design' | 's2z' | 'filter') => {
    setActiveTab(tab);
    localStorage.setItem('digital_pid_panel_active_tab', tab);
    setErrorMsg('');
  };

  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);

  const handleApplyPreset = (preset: any) => {
    handleTabChange(preset.tab);
    if (preset.tab === 'design') {
      setPidMode(preset.params.mode);
      setPidVin(preset.params.vin);
      setPidVout(preset.params.vout);
      setPidIout(preset.params.iout);
      setPidL(preset.params.l);
      setPidC(preset.params.c);
      setPidFs(preset.params.fs);
      setPidVref(preset.params.vref);
      setPidKdiv(preset.params.kdiv);
      setPidFc(preset.params.fc);
      setPidPm(preset.params.pm);
    } else if (preset.tab === 's2z') {
      setS2zFz(preset.params.fz);
      setS2zFp(preset.params.fp);
      setS2zGain(preset.params.gain);
      setS2zFs(preset.params.fs);
      setS2zMethod(preset.params.method);
    } else if (preset.tab === 'filter') {
      setFilterType(preset.params.type);
      setFilterFs(preset.params.fs);
      setFilterFc(preset.params.fc);
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
    panelKey: `layout_digitalpidpanel_v5_${activeTab}`,
    activeTab: activeTab,
    defaultCards: ['input', 'results', 'chart', 'schematic'],
    defaultColumns: { input: 'left', results: 'left', chart: 'right', schematic: 'right' },
    defaultSpans: { input: 4, results: 4, chart: 8, schematic: 8 },
    defaultHeights: { input: 680, results: 380, chart: 420, schematic: 420 }
  });

  const [chartView, setChartView] = useState<'bode' | 'step'>('bode');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [drcWarnings, setDrcWarnings] = useState<string[]>([]);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);

  const handleCopyCode = (code: string) => {
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    });
  };

  const [pidMode, setPidMode] = useState<number>(0);
  const [pidVin, setPidVin] = useState<number>(12.0);
  const [pidVout, setPidVout] = useState<number>(3.3);
  const [pidIout, setPidIout] = useState<number>(2.0);
  const [pidL, setPidL] = useState<number>(10.0);
  const [pidC, setPidC] = useState<number>(47.0);
  const [pidFs, setPidFs] = useState<number>(100.0);
  const [pidVref, setPidVref] = useState<number>(3.3);
  const [pidKdiv, setPidKdiv] = useState<number>(0.5);
  const [pidFc, setPidFc] = useState<number>(5.0);
  const [pidPm, setPidPm] = useState<number>(60.0);

  const [s2zFz, setS2zFz] = useState<number>(1.0);
  const [s2zFp, setS2zFp] = useState<number>(50.0);
  const [s2zGain, setS2zGain] = useState<number>(10.0);
  const [s2zFs, setS2zFs] = useState<number>(100.0);
  const [s2zMethod, setS2zMethod] = useState<'tustin' | 'euler' | 'forward_euler' | 'backward_euler'>('tustin');

  const [filterType, setFilterType] = useState<'1st' | '2nd'>('1st');
  const [filterFs, setFilterFs] = useState<number>(20000.0);
  const [filterFc, setFilterFc] = useState<number>(1000.0);

  const [designResult, setDesignResult] = useState<any>(null);
  const [s2zResult, setS2zResult] = useState<any>(null);
  const [filterResult, setFilterResult] = useState<any>(null);

  const [bodeChartOpt, setBodeChartOpt] = useState<any>({});
  const [stepChartOpt, setStepChartOpt] = useState<any>({});
  const [filterChartOpt, setFilterChartOpt] = useState<any>({});

  useEffect(() => {
    try {
      const savedState = localStorage.getItem('project_state');
      if (savedState) {
        const state = JSON.parse(savedState);
        if (state.ind_vin) setPidVin(state.ind_vin);
        if (state.ind_vout) setPidVout(state.ind_vout);
        if (state.ind_iout) setPidIout(state.ind_iout);
        if (state.ind_l_uh) setPidL(state.ind_l_uh);
        if (state.ind_c_uf) setPidC(state.ind_c_uf);
        if (state.ind_fsw_khz) setPidFs(state.ind_fsw_khz);
      }
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  const computePidDesign = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/digital_pid/design', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: pidMode,
          vin: pidVin,
          vout: pidVout,
          iout: pidIout,
          l_uh: pidL,
          c_uf: pidC,
          fs_khz: pidFs,
          v_ref_adc: pidVref,
          k_div: pidKdiv,
          fc_khz: pidFc,
          pm_deg: pidPm
        })
      });
      if (activeTabRef.current !== 'design') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "Digital PID calculation failed, please check power stage and controller inputs.");
      }
      const data = await res.json();
      setDesignResult(data);
      setDrcWarnings(data.drc_warnings || []);
      renderBodeChart(data.bode_data, pidFc, pidPm);
      renderStepChart(data.step_data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  const computeS2z = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/digital_pid/s2z', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fz_khz: s2zFz,
          fp_khz: s2zFp,
          gain: s2zGain,
          fs_khz: s2zFs,
          method: s2zMethod
        })
      });
      if (activeTabRef.current !== 's2z') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "S-domain to Z-domain conversion failed.");
      }
      const data = await res.json();
      setS2zResult(data);
      setDrcWarnings(data.drc_warnings || []);
      renderBodeChart(data.bode_data, s2zFz, 60.0);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  const computeFilter = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/digital_pid/filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filter_type: filterType,
          fs_hz: filterFs,
          fc_hz: filterFc
        })
      });
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "ADC digital filter calculation failed: cutoff frequency must be less than half of sampling frequency (Nyquist limit).");
      }
      const data = await res.json();
      setFilterResult(data);
      setDrcWarnings(data.drc_warnings || []);
      renderFilterChart(data.bode_data, filterFc);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      if (activeTab === 'design') computePidDesign();
      else if (activeTab === 's2z') computeS2z();
      else if (activeTab === 'filter') computeFilter();
    }, 500);
    return () => clearTimeout(timer);
  }, [pidMode, pidVin, pidVout, pidIout, pidL, pidC, pidFs, pidVref, pidKdiv, pidFc, pidPm, s2zFz, s2zFp, s2zGain, s2zFs, s2zMethod, filterType, filterFs, filterFc, activeTab]);

  const renderBodeChart = (bodeData: any, fc_khz: number, pm_deg: number) => {
    if (!bodeData || bodeData.length === 0) return;
    const f = bodeData.map((d: any) => d.f);
    const loop_mag = bodeData.map((d: any) => d.loop_mag ?? d.mag_db);
    const loop_phase = bodeData.map((d: any) => d.loop_phase ?? d.phase_deg);

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: 'rgba(56, 189, 248, 0.4)',
        extraCssText: 'backdrop-filter: blur(8px); border: 1px solid rgba(56, 189, 248, 0.4);',
        textStyle: { color: '#f1f5f9' },
        formatter: (params: any) => {
          const freq = params[0].axisValue;
          let html = `<div class="text-[10px] font-bold mb-1">Frequency: ${parseFloat(freq).toFixed(1)} Hz</div>`;
          params.forEach((p: any) => {
            const unit = p.seriesName.includes('Magnitude') || p.seriesName.includes('Gain') ? 'dB' : '°';
            html += `<div class="flex items-center gap-4 justify-between text-[10px]">
              <span class="text-slate-400">${p.seriesName}:</span>
              <span class="font-mono font-bold" style="color:${p.color}">${p.value[1].toFixed(2)} ${unit}</span>
            </div>`;
          });
          return html;
        }
      },
      legend: {
        data: ['Open-Loop Magnitude', 'Open-Loop Phase'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        top: 5
      },
      grid: [
        { left: '12%', right: '12%', top: '12%', height: '35%', containLabel: true },
        { left: '12%', right: '12%', top: '55%', height: '35%', containLabel: true }
      ],
      xAxis: [
        { gridIndex: 0, type: 'log', logBase: 10, show: true, axisLabel: { show: false }, splitLine: { lineStyle: { color: 'rgba(30,41,59,0.2)', type: 'dashed' } } },
        { gridIndex: 1, type: 'log', logBase: 10, name: 'Hz', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(30,41,59,0.2)', type: 'dashed' } } }
      ],
      yAxis: [
        { gridIndex: 0, type: 'value', name: 'Gain (dB)', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(30,41,59,0.2)' } } },
        { gridIndex: 1, type: 'value', name: 'Phase (deg)', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(30,41,59,0.2)' } } }
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1] },
        { type: 'slider', xAxisIndex: [0, 1], bottom: 5, textStyle: { color: '#94a3b8' } }
      ],
      series: [
        {
          name: 'Open-Loop Magnitude',
          type: 'line',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: f.map((freq: number, i: number) => [freq, loop_mag[i]]),
          symbol: 'none',
          lineStyle: { width: 3, color: '#ec4899', shadowBlur: 8, shadowColor: '#ec4899' },
          itemStyle: { color: '#ec4899' },
          markLine: {
            symbol: 'none',
            data: [
              { yAxis: 0, lineStyle: { color: '#475569', type: 'solid', width: 1.5 } },
              { xAxis: fc_khz * 1000.0, lineStyle: { color: '#ec4899', type: 'dashed', width: 1.2 }, label: { formatter: `fc = ${fc_khz.toFixed(1)} kHz`, color: '#ec4899', position: 'end', fontSize: 8 } }
            ]
          }
        },
        {
          name: 'Open-Loop Phase',
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: f.map((freq: number, i: number) => [freq, loop_phase[i]]),
          symbol: 'none',
          lineStyle: { width: 3, color: '#10b981', shadowBlur: 8, shadowColor: '#10b981' },
          itemStyle: { color: '#10b981' },
          markLine: {
            symbol: 'none',
            data: [
              { xAxis: fc_khz * 1000.0, lineStyle: { color: '#10b981', type: 'dashed', width: 1.2 }, label: { formatter: `PM = ${pm_deg.toFixed(1)}°`, color: '#10b981', position: 'end', fontSize: 8 } }
            ]
          }
        }
      ]
    };
    setBodeChartOpt(option);
  };

  const renderStepChart = (stepData: any) => {
    if (!stepData || !stepData.t || stepData.t.length === 0) return;
    const { t, y } = stepData;
    const option = {
      backgroundColor: 'transparent',
      title: { text: 'Closed-Loop Time-Domain Step Response', textStyle: { color: '#e2e8f0', fontSize: 11 }, left: 'center' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: 'rgba(56, 189, 248, 0.4)',
        extraCssText: 'backdrop-filter: blur(8px); border: 1px solid rgba(56, 189, 248, 0.4);',
        textStyle: { color: '#f1f5f9' },
        formatter: (params: any) => `Time: ${(params[0].axisValue * 1000).toFixed(2)} ms<br/>Output: <span class="font-mono font-bold text-sky-400">${params[0].data.toFixed(3)} V</span>`
      },
      grid: { left: '12%', right: '12%', bottom: '20%', top: '18%', containLabel: true },
      xAxis: {
        type: 'category',
        data: t.map((val: number) => val),
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9, formatter: (val: any) => (parseFloat(val) * 1000).toFixed(1) },
        name: 'ms',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 }
      },
      yAxis: {
        type: 'value',
        name: 'Voltage (V)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(30,41,59,0.2)' } }
      },
      dataZoom: [
        { type: 'inside', filterMode: 'filter' },
        { type: 'slider', filterMode: 'filter', bottom: 5, textStyle: { color: '#94a3b8' } }
      ],
      series: [
        {
          name: 'Step Response',
          type: 'line',
          data: y,
          symbol: 'none',
          lineStyle: { width: 3, color: '#fb923c', shadowBlur: 8, shadowColor: '#fb923c' },
          itemStyle: { color: '#fb923c' }
        }
      ]
    };
    setStepChartOpt(option);
  };

  const renderFilterChart = (bodeData: any, fc_hz: number) => {
    if (!bodeData || bodeData.length === 0) return;
    const f = bodeData.map((d: any) => d.f);
    const mag = bodeData.map((d: any) => d.mag_db);

    const option = {
      backgroundColor: 'transparent',
      title: { text: 'Digital Low-Pass Filter Frequency Response', textStyle: { color: '#e2e8f0', fontSize: 11 }, left: 'center' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: 'rgba(56, 189, 248, 0.4)',
        extraCssText: 'backdrop-filter: blur(8px); border: 1px solid rgba(56, 189, 248, 0.4);',
        textStyle: { color: '#f1f5f9' },
        formatter: (params: any) => `Frequency: ${parseFloat(params[0].axisValue).toFixed(0)} Hz<br/>Attenuation: <span class="font-mono font-bold text-rose-450">${params[0].data.toFixed(2)} dB</span>`
      },
      grid: { left: '12%', right: '12%', bottom: '20%', top: '18%', containLabel: true },
      xAxis: {
        type: 'category',
        data: f.map((freq: number) => Math.round(freq)),
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        name: 'Hz',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 }
      },
      yAxis: {
        type: 'value',
        name: 'Gain (dB)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(30,41,59,0.2)' } }
      },
      dataZoom: [
        { type: 'inside', filterMode: 'filter' },
        { type: 'slider', filterMode: 'filter', bottom: 5, textStyle: { color: '#94a3b8' } }
      ],
      series: [
        {
          name: 'Magnitude Response',
          type: 'line',
          data: mag,
          symbol: 'none',
          lineStyle: { width: 3, color: '#ec4899', shadowBlur: 8, shadowColor: '#ec4899' },
          itemStyle: { color: '#ec4899' },
          markLine: {
            symbol: 'none',
            data: [
              { yAxis: -3.0, lineStyle: { color: '#64748b', type: 'dashed', width: 1.0 } },
              { xAxis: Math.round(fc_hz), lineStyle: { color: '#ec4899', type: 'dashed', width: 1.2 }, label: { formatter: `fc = ${fc_hz.toFixed(0)} Hz`, color: '#ec4899', position: 'end', fontSize: 8 } }
            ]
          }
        }
      ]
    };
    setFilterChartOpt(option);
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Header Banner */}
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
            <h1 className="text-base font-bold text-white tracking-tight">Digital PID & Discretization Toolbox</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Discretizes continuous transfer functions (S-domain to Z-domain) and computes digital Butterworth filters and PID difference equations.
            </p>
          </div>
        </div>
        
        {/* Tab Selection & Control */}
        <div className="flex items-center gap-3">
          <div className="flex gap-1 bg-slate-950/40 p-0.5 rounded-lg border border-slate-800/80">
            <button
              onClick={() => handleTabChange('design')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-bold border-0 cursor-pointer transition-all ${
                activeTab === 'design' ? 'bg-cyan-500/10 text-cyan-400' : 'bg-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              PID Design
            </button>
            <button
              onClick={() => handleTabChange('s2z')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-bold border-0 cursor-pointer transition-all ${
                activeTab === 's2z' ? 'bg-cyan-500/10 text-cyan-400' : 'bg-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              S-to-Z Discretization
            </button>
            <button
              onClick={() => handleTabChange('filter')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-bold border-0 cursor-pointer transition-all ${
                activeTab === 'filter' ? 'bg-cyan-500/10 text-cyan-400' : 'bg-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Digital Filter
            </button>
          </div>

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

      {errorMsg && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2.5 text-xs text-rose-350 flex-shrink-0">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>Error: {errorMsg}</span>
        </div>
      )}

      {/* Main DragDeck Grid Canvas */}
      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 pr-1 min-h-0">
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
              {/* CARD: Input parameters */}
              {key === 'input' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-850 pb-2">
                    <span className="text-xs font-bold text-white">Parameter Inputs & Operating Specifications</span>
                  </div>

                  {/* Commercial Presets */}
                  <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/20 space-y-1.5 mb-2">
                    <span className="text-[9px] text-slate-400 block select-none">
                      Commercial Control Loop & Filter Presets:
                    </span>
                    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                      {DIGITAL_PID_PRESETS.map((preset, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleApplyPreset(preset)}
                          className={`px-2 py-1 text-[9px] font-medium border rounded transition-all cursor-pointer whitespace-nowrap ${
                            activeTab === preset.tab
                              ? 'bg-cyan-950/30 border-cyan-500 text-cyan-400 font-bold'
                              : 'bg-slate-950 border-slate-800 text-slate-350 hover:border-cyan-500/50 hover:text-cyan-400'
                          }`}
                        >
                          {preset.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {activeTab === 'design' && (
                    <div className="space-y-4">
                      {/* Step 1: Topology */}
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850/80 pb-1">Step 1: Power Stage Topology & Operating Conditions</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1 col-span-2">
                            <label className="text-[9px] text-slate-400">Control Topology</label>
                            <select
                              value={pidMode}
                              onChange={(e) => setPidMode(parseInt(e.target.value))}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            >
                              <option value={0}>Current-Mode Buck</option>
                              <option value={1}>Voltage-Mode Buck</option>
                              <option value={2}>Current-Mode Boost</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Input Voltage Vin (V)</label>
                            <input
                              type="number"
                              value={pidVin}
                              onChange={(e) => setPidVin(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Output Voltage Vout (V)</label>
                            <input
                              type="number"
                              value={pidVout}
                              onChange={(e) => setPidVout(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Step 2: Inductor & Capacitor */}
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850/80 pb-1">Step 2: Power Stage LC Filter Parameters</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Filter Inductance L (μH)</label>
                            <input
                              type="number"
                              value={pidL}
                              onChange={(e) => setPidL(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Output Capacitance C (μF)</label>
                            <input
                              type="number"
                              value={pidC}
                              onChange={(e) => setPidC(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1 col-span-2">
                            <label className="text-[9px] text-slate-400">Rated Output Current Iout (A)</label>
                            <input
                              type="number"
                              value={pidIout}
                              onChange={(e) => setPidIout(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Step 3: Loop specifications */}
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850/80 pb-1">Step 3: Loop Feedback & Target Crossover Specs</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Feedback Ratio Kdiv</label>
                            <input
                              type="number"
                              step="0.05"
                              value={pidKdiv}
                              onChange={(e) => setPidKdiv(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Reference Voltage Vref (V)</label>
                            <input
                              type="number"
                              value={pidVref}
                              onChange={(e) => setPidVref(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Target Crossover fc (kHz)</label>
                            <input
                              type="number"
                              value={pidFc}
                              onChange={(e) => setPidFc(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Phase Margin PM (deg)</label>
                            <input
                              type="number"
                              value={pidPm}
                              onChange={(e) => setPidPm(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Step 7 & 8: Controller timing & limits */}
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850/80 pb-1">Steps 7 & 8: Controller Timing & Limit Parameters</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1 col-span-2">
                            <label className="text-[9px] text-slate-400">Control Sampling Freq Fsw (kHz)</label>
                            <input
                              type="number"
                              value={pidFs}
                              onChange={(e) => setPidFs(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                        </div>
                        <div className="p-2.5 bg-slate-950 rounded border border-slate-850 space-y-2">
                          <div className="flex justify-between items-center text-[10px]">
                            <span className="text-slate-400">Max Duty Cycle Clamp:</span>
                            <span className="text-amber-500 font-bold font-mono">0.95</span>
                          </div>
                          <div className="flex justify-between items-center text-[10px]">
                            <span className="text-slate-400">Min Duty Cycle Clamp:</span>
                            <span className="text-slate-500 font-mono">0.02</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 's2z' && (
                    <div className="space-y-4">
                      {/* Step 4: S domain zeros and poles */}
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850/80 pb-1">Step 4: Continuous S-Domain Zeros & Poles</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Continuous Zero fz (kHz)</label>
                            <input
                              type="number"
                              value={s2zFz}
                              onChange={(e) => setS2zFz(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Continuous Pole fp (kHz)</label>
                            <input
                              type="number"
                              value={s2zFp}
                              onChange={(e) => setS2zFp(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1 col-span-2">
                            <label className="text-[9px] text-slate-400">Proportional Gain</label>
                            <input
                              type="number"
                              value={s2zGain}
                              onChange={(e) => setS2zGain(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Step 5: Discretization algorithms */}
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850/80 pb-1">Step 5: Discretization Method & Sampling Rate</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1 col-span-2">
                            <label className="text-[9px] text-slate-400">Mapping Method</label>
                            <select
                              value={s2zMethod}
                              onChange={(e: any) => setS2zMethod(e.target.value)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            >
                              <option value="tustin">Tustin Bilinear Transform</option>
                              <option value="forward_euler">Forward Euler</option>
                              <option value="backward_euler">Backward Euler</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1 col-span-2">
                            <label className="text-[9px] text-slate-400">Discretization Sampling Rate Fs (kHz)</label>
                            <input
                              type="number"
                              value={s2zFs}
                              onChange={(e) => setS2zFs(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'filter' && (
                    <div className="space-y-4">
                      {/* Step 6: Filter parameters */}
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850/80 pb-1">Step 6: Digital Filter Specifications</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1 col-span-2">
                            <label className="text-[9px] text-slate-400">Filter Order & Type</label>
                            <select
                              value={filterType}
                              onChange={(e: any) => setFilterType(e.target.value)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            >
                              <option value="1st">1st-Order Inertial LPF</option>
                              <option value="2nd">2nd-Order Butterworth</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Cutoff Frequency fc (Hz)</label>
                            <input
                              type="number"
                              value={filterFc}
                              onChange={(e) => setFilterFc(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-400">Sampling Frequency Fs (Hz)</label>
                            <input
                              type="number"
                              value={filterFs}
                              onChange={(e) => setFilterFs(parseFloat(e.target.value) || 0)}
                              className="bg-slate-950 border border-slate-850 rounded px-2.5 py-1.5 text-xs text-slate-200 outline-none"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

            {key === 'results' && (
              <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                  <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    Control Metrics & Stability Margin DRC
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  {/* DRC Check at the top */}
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold text-slate-400 block select-none">Digital Control Design Rule Check (DRC):</span>
                    {(() => {
                      const warnings: string[] = [...drcWarnings];

                      if (activeTab === 's2z' && s2zResult) {
                        const a1 = s2zResult.a1 ?? 0.0;
                        const a2 = s2zResult.a2 ?? 0.0;
                        if (Math.abs(a1) >= 1.0 || Math.abs(a2) >= 1.0 || Math.abs(a1 + a2) >= 1.0) {
                          warnings.push("⚠️ [Z-Domain Instability] Denominator coefficients place poles outside the unit circle! Increase Fs or adjust zero/pole frequencies.");
                        }
                      }

                      if (warnings.length > 0) {
                        return (
                          <div className="space-y-1.5">
                            {warnings.map((warn, i) => (
                              <div key={i} className="p-2.5 rounded border bg-rose-500/10 border-rose-500/20 text-rose-350 text-[10px] leading-relaxed flex items-start gap-2">
                                <ShieldAlert className="w-3.5 h-3.5 text-rose-450 shrink-0 mt-0.5" />
                                <span>{warn}</span>
                              </div>
                            ))}
                          </div>
                        );
                      }

                      return (
                        <div className="flex items-center gap-2 text-emerald-400 bg-emerald-950/20 p-2.5 rounded border border-emerald-900/40 text-[10px]">
                          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                          <span>All safety margins and Nyquist discretization limits satisfy design specifications.</span>
                        </div>
                      );
                    })()}
                  </div>

                  <span className="text-[10px] font-bold text-slate-400 block select-none pt-2 border-t border-slate-800/80">Key Parameters & Coefficients:</span>
                  
                  {activeTab === 'design' && designResult && (
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-medium">Proportional Kp</span>
                        <span className="text-xs font-bold text-cyan-300 font-mono">
                          {(designResult.kp_dig ?? 0).toFixed(4)}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-medium">Integral Ki</span>
                        <span className="text-xs font-bold text-cyan-300 font-mono">
                          {(designResult.ki_dig ?? 0).toFixed(4)}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-medium">Derivative Kd</span>
                        <span className="text-xs font-bold text-cyan-300 font-mono">
                          {(designResult.kd_dig ?? 0).toFixed(4)}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-medium">Crossover fc</span>
                        <span className="text-xs font-bold text-slate-200 font-mono">
                          {pidFc.toFixed(2)} kHz
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-medium">Phase Margin PM</span>
                        <span className="text-xs font-bold text-slate-200 font-mono">
                          {pidPm.toFixed(1)}°
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-400 font-medium">Est. Overshoot</span>
                        <span className="text-xs font-bold text-orange-400 font-mono">
                          {(designResult.step_data?.overshoot_pct ?? 0.0).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  )}

                  {activeTab === 's2z' && s2zResult && (
                    <div className="space-y-3">
                      <div className="grid grid-cols-3 gap-2.5 bg-slate-900/20 p-2.5 rounded border border-slate-850">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-450">Numerator b0</span>
                          <span className="text-[10px] font-bold text-emerald-400 font-mono">{(s2zResult.b0 ?? 0).toFixed(5)}</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-450">Numerator b1</span>
                          <span className="text-[10px] font-bold text-emerald-400 font-mono">{(s2zResult.b1 ?? 0).toFixed(5)}</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-450">Numerator b2</span>
                          <span className="text-[10px] font-bold text-emerald-400 font-mono">{(s2zResult.b2 ?? 0).toFixed(5)}</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-450">Denominator a1</span>
                          <span className="text-[10px] font-bold text-teal-400 font-mono">{(s2zResult.a1 ?? 0).toFixed(5)}</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-450">Denominator a2</span>
                          <span className="text-[10px] font-bold text-teal-400 font-mono">{(s2zResult.a2 ?? 0).toFixed(5)}</span>
                        </div>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-450">Frequency Warp Ratio</span>
                          <span className="text-[10px] font-bold text-rose-450 font-mono">{((s2zFp / (s2zFs || 1.0)) * 100.0).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'filter' && filterResult && (
                    <div className="grid grid-cols-3 gap-2.5 bg-slate-900/20 p-2.5 rounded border border-slate-850">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-450">
                          {filterType === '1st' ? 'Alpha Coeff' : 'b0 Factor'}
                        </span>
                        <span className="text-[10px] font-bold text-cyan-400 font-mono">
                          {filterType === '1st'
                            ? (filterResult.coeffs?.alpha ?? 0).toFixed(5)
                            : (filterResult.coeffs?.b0 ?? 0).toFixed(5)}
                        </span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-450">Term a1</span>
                        <span className="text-[10px] font-bold text-slate-200 font-mono">
                          {filterType === '1st' ? '0.00000' : (filterResult.coeffs?.a1 ?? 0).toFixed(5)}
                        </span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-450">Term a2</span>
                        <span className="text-[10px] font-bold text-slate-200 font-mono">
                          {filterType === '1st' ? '0.00000' : (filterResult.coeffs?.a2 ?? 0).toFixed(5)}
                        </span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-450">Cutoff fc</span>
                        <span className="text-[10px] font-bold text-emerald-450 font-mono">{filterFc.toFixed(0)} Hz</span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-450">Bandwidth Ratio fc/Fs</span>
                        <span className="text-[10px] font-bold text-purple-400 font-mono">
                          {((filterFc / (filterFs || 1.0)) * 100.0).toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] text-slate-450">Equiv Group Delay</span>
                        <span className="text-[10px] font-bold text-rose-450 font-mono">
                          {(1.0 / (2.0 * Math.PI * (filterFc || 1.0)) * 1e6).toFixed(1)} μs
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Theoretical equations */}
                  <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-850/60 space-y-1">
                    <span className="text-[9px] font-bold text-slate-400 block select-none">Control Mathematics Formulation:</span>
                    {activeTab === 'design' && (
                      <div className="space-y-1.5 text-[10px] text-slate-450">
                        <p>Continuous Transfer Function:</p>
                        <Latex math={"G_c(s) = K_p + \\frac{K_i}{s} + K_d s"} block />
                        <p>Discrete Bilinear Mapping: <Latex math={"s \\approx \\frac{2}{T_s} \\frac{z-1}{z+1}"} /></p>
                      </div>
                    )}
                    {activeTab === 's2z' && (
                      <div className="space-y-1.5 text-[10px] text-slate-450">
                        <p>Continuous Single Pole-Zero Model:</p>
                        <Latex math={"H(s) = Gain \\cdot \\frac{s + 2\\pi f_z}{s + 2\\pi f_p}"} block />
                        <p>Bilinear Tustin discretization.</p>
                      </div>
                    )}
                    {activeTab === 'filter' && (
                      <div className="space-y-1.5 text-[10px] text-slate-450">
                        <p>1st-Order Low-Pass Difference: <Latex math={"y[n] = (1-\\alpha)y[n-1] + \\alpha x[n]"} /></p>
                        <p>2nd-Order Butterworth Difference:</p>
                        <Latex math={"y[n] = b_0 x[n] + b_1 x[n-1] + b_2 x[n-2] - a_1 y[n-1] - a_2 y[n-2]"} block />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {key === 'chart' && (
              <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0 flex flex-row justify-between items-center gap-4">
                  <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                    Frequency Sweep & Simulation Curves
                  </CardTitle>
                  {activeTab === 'design' && (
                    <div className="flex bg-slate-950/80 border border-slate-800 rounded p-0.5 select-none">
                      <button
                        onClick={() => setChartView('bode')}
                        className={`px-2 py-0.5 text-[9px] font-bold rounded cursor-pointer transition-all ${chartView === 'bode' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}`}
                      >
                        Bode Plot
                      </button>
                      <button
                        onClick={() => setChartView('step')}
                        className={`px-2 py-0.5 text-[9px] font-bold rounded cursor-pointer transition-all ${chartView === 'step' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}`}
                      >
                        Step Response
                      </button>
                    </div>
                  )}
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 flex justify-center items-center bg-slate-950/15">
                  <div className="w-full h-full min-h-[300px]">
                    {(() => {
                      if (activeTab === 'design') {
                        if (chartView === 'bode') {
                          return bodeChartOpt.series ? (
                            <ReactECharts option={bodeChartOpt} style={{ width: '100%', height: '100%', minHeight: '300px' }} notMerge={true} />
                          ) : (
                            <div className="text-xs text-slate-500 italic">Awaiting frequency sweep calculation...</div>
                          );
                        } else {
                          return stepChartOpt.series ? (
                            <ReactECharts option={stepChartOpt} style={{ width: '100%', height: '100%', minHeight: '300px' }} notMerge={true} />
                          ) : (
                            <div className="text-xs text-slate-500 italic">Awaiting step simulation...</div>
                          );
                        }
                      } else if (activeTab === 's2z') {
                        return bodeChartOpt.series ? (
                          <ReactECharts option={bodeChartOpt} style={{ width: '100%', height: '100%', minHeight: '300px' }} notMerge={true} />
                        ) : (
                          <div className="text-xs text-slate-500 italic">Awaiting continuous-to-discrete conversion...</div>
                        );
                      } else {
                        return filterChartOpt.series ? (
                          <ReactECharts option={filterChartOpt} style={{ width: '100%', height: '100%', minHeight: '300px' }} notMerge={true} />
                        ) : (
                          <div className="text-xs text-slate-500 italic">Awaiting digital filter frequency response...</div>
                        );
                      }
                    })()}
                  </div>
                </CardContent>
              </Card>
            )}

            {key === 'schematic' && (
              <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                  <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-cyan-400" />
                    Control Topology & Embedded C Code
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-950/15">
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-full items-center">
                    <div className="lg:col-span-6 flex justify-center items-center p-2 rounded bg-slate-950/30 border border-slate-850/60 min-h-[220px] overflow-hidden">
                      {activeTab === 'filter' ? (
                        <svg viewBox="0 0 200 120" className="w-full max-w-[200px] h-auto text-slate-400">
                          <defs>
                            <style>
                              {`
                                @keyframes stroke-flow-filt {
                                  to { stroke-dashoffset: -20; }
                                }
                                .animate-flow-filt {
                                  stroke-dasharray: 4, 3;
                                  animation: stroke-flow-filt 1.2s linear infinite;
                                  stroke: #ec4899;
                                }
                              `}
                            </style>
                          </defs>
                          <circle cx="20" cy="40" r="3" fill="#e2e8f0" />
                          <text x="12" y="32" fill="#e2e8f0" fontSize="7">x[n]</text>
                          <path d="M 23 40 L 60 40" fill="none" strokeWidth="1.2" className="animate-flow-filt" />

                          {/* Gain block alpha */}
                          <rect x="60" y="30" width="20" height="20" fill="#1e293b" stroke="#ec4899" strokeWidth="1.5" rx="2" />
                          <text x="66" y="43" fill="#ec4899" fontSize="8">α</text>
                          <path d="M 80 40 L 110 40" fill="none" strokeWidth="1.2" className="animate-flow-filt" />

                          {/* Adder [+] */}
                          <circle cx="120" cy="40" r="10" fill="#0f172a" stroke="#e2e8f0" strokeWidth="1" />
                          <text x="117" y="43.5" fill="#e2e8f0" fontSize="10">+</text>
                          <path d="M 130 40 L 175 40" fill="none" strokeWidth="1.2" className="animate-flow-filt" />

                          {/* Output y[n] */}
                          <circle cx="178" cy="40" r="3" fill="#ec4899" />
                          <text x="172" y="32" fill="#ec4899" fontSize="7">y[n]</text>

                          {/* Delay path down */}
                          <path d="M 155 40 L 155 80 L 130 80" fill="none" stroke="#64748b" strokeWidth="1" />
                          {/* Delay z^-1 block */}
                          <rect x="100" y="70" width="30" height="20" fill="#1e293b" stroke="#64748b" strokeWidth="1" rx="2" />
                          <text x="107" y="82.5" fill="#94a3b8" fontSize="8">z^-1</text>
                          <path d="M 100 80 L 70 80" fill="none" stroke="#64748b" strokeWidth="1" />

                          {/* Feedback gain (1-alpha) */}
                          <rect x="50" y="70" width="20" height="20" fill="#1e293b" stroke="#ec4899" strokeWidth="1" rx="2" />
                          <text x="51.5" y="82" fill="#ec4899" fontSize="6">1-α</text>
                          
                          <path d="M 50 80 L 120 80 L 120 50" fill="none" stroke="#64748b" strokeWidth="1" />
                        </svg>
                      ) : (
                        <svg viewBox="0 0 200 120" className="w-full max-w-[200px] h-auto text-slate-400">
                          <defs>
                            <style>
                              {`
                                @keyframes stroke-flow-pid {
                                  to { stroke-dashoffset: -20; }
                                }
                                .animate-flow-pid {
                                  stroke-dasharray: 4, 3;
                                  animation: stroke-flow-pid 1.2s linear infinite;
                                  stroke: #10b981;
                                }
                              `}
                            </style>
                          </defs>
                          <text x="10" y="32" fill="#38bdf8" fontSize="7">Vref</text>
                          <path d="M 15 35 L 40 35" fill="none" strokeWidth="1.2" stroke="#38bdf8" />
                          
                          {/* Error Adder [+] */}
                          <circle cx="45" cy="35" r="5" fill="#0f172a" stroke="#e2e8f0" strokeWidth="1" />
                          <text x="43" y="38" fill="#e2e8f0" fontSize="7">+</text>
                          
                          <path d="M 50 35 L 70 35" fill="none" strokeWidth="1.2" className="animate-flow-pid" />
                          <text x="53" y="28" fill="#94a3b8" fontSize="6">e[n]</text>

                          {/* Controller H(z) */}
                          <rect x="70" y="20" width="40" height="30" fill="#1e293b" stroke="#10b981" strokeWidth="1.5" rx="3" />
                          <text x="82" y="35" fill="#10b981" fontSize="9" fontWeight="bold">H(z)</text>
                          <text x="75" y="45" fill="#94a3b8" fontSize="6">PID Filter</text>

                          <path d="M 110 35 L 130 35" fill="none" strokeWidth="1.2" className="animate-flow-pid" />
                          <text x="115" y="28" fill="#94a3b8" fontSize="6">u[n]</text>

                          {/* Plant G_p(s) */}
                          <rect x="130" y="20" width="45" height="30" fill="#1e293b" stroke="#38bdf8" strokeWidth="1" rx="3" />
                          <text x="140" y="38" fill="#38bdf8" fontSize="8">Power Stage</text>

                          <path d="M 175 35 L 195 35" fill="none" strokeWidth="1.2" stroke="#38bdf8" />
                          <text x="180" y="28" fill="#38bdf8" fontSize="7">Vout</text>

                          {/* Feedback Loop */}
                          <path d="M 185 35 L 185 80 L 45 80 L 45 40" fill="none" stroke="#64748b" strokeWidth="1" />
                          <text x="92" y="76" fill="#64748b" fontSize="6">Feedback Kdiv</text>
                        </svg>
                      )}
                    </div>

                    <div className="lg:col-span-6 h-full flex flex-col justify-center min-h-[200px]">
                      <div className="space-y-1.5 h-full">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] font-bold text-slate-400 block font-mono">Generated C Firmware Implementation:</span>
                          {(() => {
                            const code = activeTab === 'design' ? designResult?.c_code : activeTab === 's2z' ? s2zResult?.c_code : filterResult?.c_code;
                            return code ? (
                              <button
                                onClick={() => handleCopyCode(code)}
                                className="px-2 py-0.5 text-[8px] bg-slate-900 hover:bg-slate-800 text-teal-400 rounded transition-all cursor-pointer font-bold"
                              >
                                {copySuccess ? 'Copied!' : 'Copy Code'}
                              </button>
                            ) : null;
                          })()}
                        </div>
                        <textarea
                          readOnly
                          value={
                            (activeTab === 'design' ? designResult?.c_code : activeTab === 's2z' ? s2zResult?.c_code : filterResult?.c_code) || 
                            'Awaiting calculation to generate embedded C code...'
                          }
                          className="w-full h-36 bg-slate-950 border border-slate-850 rounded p-2 text-[9px] font-mono text-cyan-400 focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            </DragCard>
          )}
          onDropOnColumn={handleDropOnColumn}
        />
      </div>
    </div>
  );
}
