import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
import LoopCompensationSchematicSandbox from './LoopCompensationSchematicSandbox';
import {
  ArrowLeft,
  CheckCircle2,
  ShieldAlert,
  TrendingUp,
  Compass
} from 'lucide-react';

const E96 = [
  1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43,
  1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10,
  2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
  3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53,
  4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
  6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
];

const E24 = [
  1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
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

interface BomItem {
  designator: string;
  calcValue: string;
  stdValue: string;
  error: string;
  type: string;
  desc: string;
}

export default function LoopCompensationPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: (mod: string | null) => void }) {
  const [activeTab, setActiveTab] = useState<'type2' | 'type3' | 'tl431' | 'digital'>(() => {
    const saved = localStorage.getItem('loop_compensation_active_tab');
    return (saved === 'hv' || saved === 'hv_divider') ? 'type2' : (saved as any) || 'type2';
  });

  const handleTabChange = (val: string) => {
    setActiveTab(val as any);
    localStorage.setItem('loop_compensation_active_tab', val);
  };

  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);

  const LOOP_PRESETS = [
    { name: 'Buck Current-Mode Type II', tab: 'type2', params: { vout: 5.0, iout: 2.0, cout: 47.0, esr: 10.0, fsw: 500.0, ri: 0.1, fc: 50.0, pm: 60.0, vref: 0.8, r1: 10.0 } },
    { name: 'High-Bandwidth Voltage-Mode Type III', tab: 'type3', params: { l: 10.0, c: 100.0, esr: 10.0, vin: 12.0, vramp: 1.0, fsw: 100.0, fc: 10.0, pm: 55.0, r1: 10.0, vref: 0.8, vout: 5.0 } },
    { name: 'Flyback TL431 + Optocoupler', tab: 'tl431', params: { vout: 12.0, rup: 10.0, fc: 2.0, pm: 60.0, gain: -10.0, fpopto: 10.0 } },
    { name: 'Digital Buck PID', tab: 'digital', params: { type: 'Type II', kdc: 10.0, fs: 100.0, fz1: 1.0, fz2: 2.0, fp1: 10.0, fp2: 20.0 } }
  ];

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
    panelKey: 'layout_loopcompensation_v5',
    defaultCards: ['input', 'results', 'chart', 'schematic'],
    defaultColumns: {
      input: 'left',
      results: 'right',
      chart: 'right',
      schematic: 'right'
    },
    defaultSpans: {
      input: 4,
      results: 8,
      chart: 8,
      schematic: 8
    },
    defaultHeights: {
      input: 850,
      results: 380,
      chart: 420,
      schematic: 420
    }
  });

  const [chartView, setChartView] = useState<'bode' | 'step'>('bode');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [drcWarnings, setDrcWarnings] = useState<string[]>([]);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);

  // 1. Type II State
  const [t2Vout, setT2Vout] = useState<number>(5.0);
  const [t2Iout, setT2Iout] = useState<number>(2.0);
  const [t2Cout, setT2Cout] = useState<number>(47.0);
  const [t2Esr, setT2Esr] = useState<number>(10.0);
  const [t2Fsw, setT2Fsw] = useState<number>(500.0);
  const [t2Ri, setT2Ri] = useState<number>(0.1);
  const [t2Fc, setT2Fc] = useState<number>(50.0);
  const [t2Pm, setT2Pm] = useState<number>(60.0);
  const [t2Vref, setT2Vref] = useState<number>(0.8);
  const [t2R1, setT2R1] = useState<number>(10.0);
  const [t2DigitalDelay, setT2DigitalDelay] = useState<boolean>(false);
  const [t2FsKhz, setT2FsKhz] = useState<number>(500.0);
  const [t2Result, setT2Result] = useState<any>(null);

  // 2. Type III State
  const [t3L, setT3L] = useState<number>(10.0);
  const [t3C, setT3C] = useState<number>(100.0);
  const [t3Esr, setT3Esr] = useState<number>(10.0);
  const [t3Vin, setT3Vin] = useState<number>(12.0);
  const [t3Vramp, setT3Vramp] = useState<number>(1.0);
  const [t3Fsw, setT3Fsw] = useState<number>(100.0);
  const [t3Fc, setT3Fc] = useState<number>(10.0);
  const [t3Pm, setT3Pm] = useState<number>(55.0);
  const [t3R1, setT3R1] = useState<number>(10.0);
  const [t3Vref, setT3Vref] = useState<number>(0.8);
  const [t3Vout, setT3Vout] = useState<number>(5.0);
  const [t3DigitalDelay, setT3DigitalDelay] = useState<boolean>(false);
  const [t3FsKhz, setT3FsKhz] = useState<number>(100.0);
  const [t3Result, setT3Result] = useState<any>(null);

  // 3. TL431 State
  const [tlVout, setTlVout] = useState<number>(12.0);
  const [tlRup, setTlRup] = useState<number>(10.0);
  const [tlFc, setTlFc] = useState<number>(2.0);
  const [tlPm, setTlPm] = useState<number>(60.0);
  const [tlGain, setTlGain] = useState<number>(-10.0);
  const [tlFpOpto, setTlFpOpto] = useState<number>(10.0);
  const [dcVf, setDcVf] = useState<number>(1.2);
  const [dcRled, setDcRled] = useState<number>(1.0);
  const [dcCtr, setDcCtr] = useState<number>(1.0);
  const [dcRpull, setDcRpull] = useState<number>(4.7);
  const [dcVdd, setDcVdd] = useState<number>(5.0);
  const [dcRpar, setDcRpar] = useState<number>(1.0);
  const [tlResult, setTlResult] = useState<any>(null);
  const [tlDcResult, setTlDcResult] = useState<any>(null);

  // 5. Digital PID State
  const [digControllerType, setDigControllerType] = useState<'Type II' | 'Type III'>('Type II');
  const [digKdc, setDigKdc] = useState<number>(10.0);
  const [digFs, setDigFs] = useState<number>(100.0);
  const [digFz1, setDigFz1] = useState<number>(1.0);
  const [digFz2, setDigFz2] = useState<number>(2.0);
  const [digFp1, setDigFp1] = useState<number>(10.0);
  const [digFp2, setDigFp2] = useState<number>(20.0);
  const [digResult, setDigResult] = useState<any>(null);

  const fmtRes = (v: number) => {
    if (!v) return '0 Ω';
    if (v >= 1e6) return `${(v / 1e6).toFixed(2)} MΩ`;
    if (v >= 1e3) return `${(v / 1e3).toFixed(2)} kΩ`;
    return `${v.toFixed(1)} Ω`;
  };

  const fmtCap = (v: number) => {
    if (!v) return '0 pF';
    if (v >= 1e-6) return `${(v * 1e6).toFixed(2)} μF`;
    if (v >= 1e-9) return `${(v * 1e9).toFixed(2)} nF`;
    return `${(v * 1e12).toFixed(1)} pF`;
  };

  const handleApplyPreset = (preset: any) => {
    handleTabChange(preset.tab);
    if (preset.tab === 'type2') {
      setT2Vout(preset.params.vout);
      setT2Iout(preset.params.iout);
      setT2Cout(preset.params.cout);
      setT2Esr(preset.params.esr);
      setT2Fsw(preset.params.fsw);
      setT2Ri(preset.params.ri);
      setT2Fc(preset.params.fc);
      setT2Pm(preset.params.pm);
      setT2Vref(preset.params.vref);
      setT2R1(preset.params.r1);
    } else if (preset.tab === 'type3') {
      setT3L(preset.params.l);
      setT3C(preset.params.c);
      setT3Esr(preset.params.esr);
      setT3Vin(preset.params.vin);
      setT3Vramp(preset.params.vramp);
      setT3Fsw(preset.params.fsw);
      setT3Fc(preset.params.fc);
      setT3Pm(preset.params.pm);
      setT3R1(preset.params.r1);
      setT3Vref(preset.params.vref);
      setT3Vout(preset.params.vout);
    } else if (preset.tab === 'tl431') {
      setTlVout(preset.params.vout);
      setTlRup(preset.params.rup);
      setTlFc(preset.params.fc);
      setTlPm(preset.params.pm);
      setTlGain(preset.params.gain);
      setTlFpOpto(preset.params.fpopto);
    } else if (preset.tab === 'digital') {
      setDigControllerType(preset.params.type);
      setDigKdc(preset.params.kdc);
      setDigFs(preset.params.fs);
      setDigFz1(preset.params.fz1);
      setDigFz2(preset.params.fz2);
      setDigFp1(preset.params.fp1);
      setDigFp2(preset.params.fp2);
    }
  };

  const computeType2 = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/loop_compensation/type2', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vout: t2Vout,
          iout: t2Iout,
          cout_uf: t2Cout,
          esr_mohm: t2Esr,
          fsw_khz: t2Fsw,
          ri: t2Ri,
          fc_khz: t2Fc,
          pm_target: t2Pm,
          vref: t2Vref,
          r1_k: t2R1,
          digital_delay_on: t2DigitalDelay,
          fs_khz: t2FsKhz
        })
      });
      if (!res.ok) throw new Error("Type II calculation failed");
      const data = await res.json();
      setT2Result(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Type II API response error');
    } finally {
      setLoading(false);
    }
  };

  const computeType3 = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/loop_compensation/type3', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          l_uh: t3L,
          cout_uf: t3C,
          esr_mohm: t3Esr,
          vin: t3Vin,
          vramp: t3Vramp,
          fsw_khz: t3Fsw,
          fc_khz: t3Fc,
          pm_target: t3Pm,
          r1_k: t3R1,
          vref: t3Vref,
          vout: t3Vout,
          digital_delay_on: t3DigitalDelay,
          fs_khz: t3FsKhz
        })
      });
      if (!res.ok) throw new Error("Type III calculation failed");
      const data = await res.json();
      setT3Result(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Type III API response error');
    } finally {
      setLoading(false);
    }
  };

  const computeTl431 = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/loop_compensation/tl431', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vout: tlVout,
          r_up_k: tlRup,
          fc_khz: tlFc,
          pm_deg: tlPm,
          gain_db: tlGain,
          fp_opto_khz: tlFpOpto
        })
      });
      if (!res.ok) throw new Error("TL431 AC calculation failed");
      const data = await res.json();
      setTlResult(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'TL431 AC API response error');
    } finally {
      setLoading(false);
    }
  };

  const computeTl431Dc = async () => {
    try {
      const res = await apiFetch('/api/calculate/loop_compensation/tl431_dc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vout: tlVout,
          vf: dcVf,
          r_led_k: dcRled,
          ctr: dcCtr,
          r_pull_k: dcRpull,
          vdd: dcVdd,
          r_par_k: dcRpar
        })
      });
      if (!res.ok) throw new Error("TL431 DC bias calculation failed");
      const data = await res.json();
      setTlDcResult(data.design || null);
      if (data.drc_warnings && data.drc_warnings.length > 0) {
        setDrcWarnings(prev => [...prev, ...data.drc_warnings]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'TL431 DC API response error');
    }
  };

  const computeDigital = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/loop_compensation/digital', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          controller_type: digControllerType,
          k_dc: digKdc,
          fs_khz: digFs,
          fz1_khz: digFz1,
          fz2_khz: digFz2,
          fp1_khz: digFp1,
          fp2_khz: digFp2
        })
      });
      if (activeTabRef.current !== 'type2') return;
      if (!res.ok) {
        await res.json().catch(() => ({}));
      }
      const data = await res.json();
      setDigResult(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Digital API response error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'type2') computeType2();
  }, [t2Vout, t2Iout, t2Cout, t2Esr, t2Fsw, t2Ri, t2Fc, t2Pm, t2Vref, t2R1, t2DigitalDelay, t2FsKhz, activeTab]);

  useEffect(() => {
    if (activeTab === 'type3') computeType3();
  }, [t3L, t3C, t3Esr, t3Vin, t3Vramp, t3Fsw, t3Fc, t3Pm, t3R1, t3Vref, t3Vout, t3DigitalDelay, t3FsKhz, activeTab]);

  useEffect(() => {
    if (activeTab === 'tl431') {
      setDrcWarnings([]);
      computeTl431();
      computeTl431Dc();
    }
  }, [tlVout, tlRup, tlFc, tlPm, tlGain, tlFpOpto, dcVf, dcRled, dcCtr, dcRpull, dcVdd, dcRpar, activeTab]);

  useEffect(() => {
    if (activeTab === 'digital') computeDigital();
  }, [digControllerType, digKdc, digFs, digFz1, digFz2, digFp1, digFp2, activeTab]);

  const getBodeOption = (bodeData: any) => {
    if (!bodeData || !bodeData.f_hz) return {};
    const { f_hz, gp_mag_db, gp_phase_deg, gc_mag_db, gc_phase_deg, t_mag_db, t_phase_deg, fc_khz, pm_deg } = bodeData;

    return {
      backgroundColor: 'transparent',
      title: { text: 'Open-Loop & Closed-Loop Bode Frequency Response', textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' }, left: 'center', top: 5 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#38bdf8',
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 10 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;',
        formatter: (params: any) => {
          let freq = params[0].axisValue;
          let html = `<div class="text-xs font-bold mb-1">Frequency: ${parseFloat(freq).toFixed(1)} Hz</div>`;
          params.forEach((p: any) => {
            html += `<div class="flex items-center gap-2 justify-between text-[10px]">
              <span class="text-slate-400">${p.seriesName}:</span>
              <span class="font-semibold text-right" style="color:${p.color}">${p.value[1].toFixed(2)} ${p.seriesName.includes('Gain') ? 'dB' : '°'}</span>
            </div>`;
          });
          return html;
        }
      },
      legend: {
        data: ['Plant Gain', 'Plant Phase', 'Compensator Gain', 'Compensator Phase', 'Loop Gain (T)', 'Loop Phase (T)'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 5,
        type: 'scroll'
      },
      grid: [
        { left: '12%', right: '12%', top: '15%', height: '30%', containLabel: true },
        { left: '12%', right: '12%', top: '55%', height: '30%', containLabel: true }
      ],
      xAxis: [
        { gridIndex: 0, type: 'log', logBase: 10, show: true, axisLabel: { show: false }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.15)', type: 'dashed' } }, axisLine: { lineStyle: { color: '#334155' } } },
        { gridIndex: 1, type: 'log', logBase: 10, name: 'Hz', nameTextStyle: { color: '#64748b', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.15)', type: 'dashed' } }, axisLabel: { color: '#94a3b8', fontSize: 9 }, axisLine: { lineStyle: { color: '#334155' } } }
      ],
      yAxis: [
        { gridIndex: 0, type: 'value', name: 'Gain (dB)', nameTextStyle: { color: '#64748b', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.15)' } }, axisLabel: { color: '#94a3b8', fontSize: 9 }, axisLine: { lineStyle: { color: '#334155' } } },
        { gridIndex: 1, type: 'value', name: 'Phase (deg)', nameTextStyle: { color: '#64748b', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.15)' } }, axisLabel: { color: '#94a3b8', fontSize: 9 }, axisLine: { lineStyle: { color: '#334155' } } }
      ],
      series: [
        { name: 'Plant Gain', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: f_hz.map((f: number, i: number) => [f, gp_mag_db[i]]), symbol: 'none', lineStyle: { width: 1.5, type: 'dashed', color: 'rgba(56, 189, 248, 0.5)' }, itemStyle: { color: '#38bdf8' } },
        { name: 'Plant Phase', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: f_hz.map((f: number, i: number) => [f, gp_phase_deg[i]]), symbol: 'none', lineStyle: { width: 1.5, type: 'dashed', color: 'rgba(14, 165, 233, 0.5)' }, itemStyle: { color: '#0ea5e9' } },
        { name: 'Compensator Gain', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: f_hz.map((f: number, i: number) => [f, gc_mag_db[i]]), symbol: 'none', lineStyle: { width: 1.5, type: 'dashed', color: 'rgba(192, 132, 252, 0.5)' }, itemStyle: { color: '#c084fc' } },
        { name: 'Compensator Phase', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: f_hz.map((f: number, i: number) => [f, gc_phase_deg[i]]), symbol: 'none', lineStyle: { width: 1.5, type: 'dashed', color: 'rgba(168, 85, 247, 0.5)' }, itemStyle: { color: '#a855f7' } },
        {
          name: 'Loop Gain (T)', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: f_hz.map((f: number, i: number) => [f, t_mag_db[i]]), symbol: 'none', lineStyle: { width: 3, color: '#f43f5e', shadowBlur: 8, shadowColor: 'rgba(244, 63, 94, 0.5)' }, itemStyle: { color: '#f43f5e' },
          markLine: {
            symbol: 'none',
            data: [
              { yAxis: 0, lineStyle: { color: '#64748b', type: 'solid', width: 1 } },
              { xAxis: fc_khz * 1000.0, lineStyle: { color: '#f43f5e', type: 'dashed', width: 1.5 }, label: { formatter: `fc = ${fc_khz.toFixed(2)} kHz`, color: '#f43f5e', position: 'end', fontSize: 8 } }
            ]
          }
        },
        {
          name: 'Loop Phase (T)', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: f_hz.map((f: number, i: number) => [f, t_phase_deg[i]]), symbol: 'none', lineStyle: { width: 3, color: '#10b981', shadowBlur: 8, shadowColor: 'rgba(16, 185, 129, 0.5)' }, itemStyle: { color: '#10b981' },
          markLine: {
            symbol: 'none',
            data: [
              { xAxis: fc_khz * 1000.0, lineStyle: { color: '#10b981', type: 'dashed', width: 1.5 }, label: { formatter: `PM = ${pm_deg.toFixed(1)}°`, color: '#10b981', position: 'end', fontSize: 8 } }
            ]
          }
        }
      ]
    };
  };

  const getStepOption = (stepData: any) => {
    if (!stepData || !stepData.t_ms) return {};
    const { t_ms, y, settling_time_ms } = stepData;

    return {
      backgroundColor: 'transparent',
      title: { text: 'Closed-Loop Dynamic Step Response (Time Domain)', textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' }, left: 'center', top: 5 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#38bdf8',
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 10 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;',
        formatter: (params: any) => {
          let time = params[0].axisValue;
          return `<div class="text-xs">
            <div class="font-bold mb-1">Time: ${parseFloat(time).toFixed(3)} ms</div>
            <div>Output: <span class="font-bold text-amber-400">${params[0].value[1].toFixed(4)}</span></div>
          </div>`;
        }
      },
      grid: { left: '12%', right: '12%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: { type: 'value', name: 'ms', nameTextStyle: { color: '#64748b', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.15)', type: 'dashed' } }, axisLabel: { color: '#94a3b8', fontSize: 9 }, axisLine: { lineStyle: { color: '#334155' } } },
      yAxis: { type: 'value', name: 'Output', nameTextStyle: { color: '#64748b', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.15)' } }, axisLabel: { color: '#94a3b8', fontSize: 9 }, axisLine: { lineStyle: { color: '#334155' } } },
      series: [
        {
          name: 'Step Response',
          type: 'line',
          data: t_ms.map((t: number, i: number) => [t, y[i]]),
          symbol: 'none',
          lineStyle: { width: 3, color: '#f59e0b', shadowBlur: 8, shadowColor: 'rgba(245, 158, 11, 0.5)' },
          itemStyle: { color: '#f59e0b' },
          markLine: {
            symbol: 'none',
            data: [
              { yAxis: 1.0, lineStyle: { color: '#64748b', type: 'solid', width: 1 } },
              { xAxis: settling_time_ms, lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 }, label: { formatter: `ts = ${settling_time_ms.toFixed(2)} ms`, color: '#f59e0b', position: 'end', fontSize: 8 } }
            ]
          }
        }
      ]
    };
  };

  const getMatchedBom = (): BomItem[] => {
    const items: BomItem[] = [];
    if (activeTab === 'type2' && t2Result?.design) {
      const r2 = t2Result.design.r2_ohm;
      const r3 = t2Result.design.r3_ohm;
      const c1 = t2Result.design.c1_f;
      const c2 = t2Result.design.c2_f;

      if (r2) {
        const match = findClosestStandard(r2, E96);
        items.push({ designator: 'R2', calcValue: fmtRes(r2), stdValue: fmtRes(match.value), error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'Integral feedback resistor' });
      }
      if (r3) {
        const match = findClosestStandard(r3, E96);
        items.push({ designator: 'R3', calcValue: fmtRes(r3), stdValue: fmtRes(match.value), error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'High-frequency pole limit resistor' });
      }
      if (c1) {
        const match = findClosestStandard(c1 * 1e12, E24);
        items.push({ designator: 'C1', calcValue: fmtCap(c1), stdValue: `${match.value.toFixed(1)} pF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'Main zero-setting capacitor' });
      }
      if (c2) {
        const match = findClosestStandard(c2 * 1e12, E24);
        items.push({ designator: 'C2', calcValue: fmtCap(c2), stdValue: `${match.value.toFixed(1)} pF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'High-frequency bypass filtering capacitor' });
      }
    } else if (activeTab === 'type3' && t3Result?.design) {
      const r2 = t3Result.design.r2_ohm;
      const r3 = t3Result.design.r3_ohm;
      const c1 = t3Result.design.c1_f;
      const c2 = t3Result.design.c2_f;
      const c3 = t3Result.design.c3_f;

      if (r2) {
        const match = findClosestStandard(r2, E96);
        items.push({ designator: 'R2', calcValue: fmtRes(r2), stdValue: fmtRes(match.value), error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'Mid-band gain integral resistor' });
      }
      if (r3) {
        const match = findClosestStandard(r3, E96);
        items.push({ designator: 'R3', calcValue: fmtRes(r3), stdValue: fmtRes(match.value), error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'Damping branch resistor' });
      }
      if (c1) {
        const match = findClosestStandard(c1 * 1e12, E24);
        items.push({ designator: 'C1', calcValue: fmtCap(c1), stdValue: `${match.value.toFixed(1)} pF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'Main integral capacitor' });
      }
      if (c2) {
        const match = findClosestStandard(c2 * 1e12, E24);
        items.push({ designator: 'C2', calcValue: fmtCap(c2), stdValue: `${match.value.toFixed(1)} pF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'High-frequency pole filtering capacitor' });
      }
      if (c3) {
        const match = findClosestStandard(c3 * 1e12, E24);
        items.push({ designator: 'C3', calcValue: fmtCap(c3), stdValue: `${match.value.toFixed(1)} pF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'Feedforward zero-setting capacitor' });
      }
    } else if (activeTab === 'tl431' && tlResult?.design) {
      const rcomp = tlResult.design.r_comp_ohm;
      const ccomp = tlResult.design.c_comp_f;
      const chf = tlResult.design.c_hf_f;

      if (rcomp) {
        const match = findClosestStandard(rcomp, E96);
        items.push({ designator: 'R_comp', calcValue: fmtRes(rcomp), stdValue: fmtRes(match.value), error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'TL431 cathode compensation resistor' });
      }
      if (ccomp) {
        const match = findClosestStandard(ccomp * 1e12, E24);
        items.push({ designator: 'C_comp', calcValue: fmtCap(ccomp), stdValue: `${match.value.toFixed(1)} pF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'Main zero-setting capacitor' });
      }
      if (chf) {
        const match = findClosestStandard(chf * 1e12, E24);
        items.push({ designator: 'C_hf', calcValue: fmtCap(chf), stdValue: `${match.value.toFixed(1)} pF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'High-frequency pole bypass capacitor' });
      }
    }
    return items;
  };

  const handleCopyCode = () => {
    if (digResult?.c_code) {
      navigator.clipboard.writeText(digResult.c_code);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  return (
    <div className="w-full h-full flex flex-col gap-3 text-slate-100 bg-slate-950 p-3 overflow-hidden">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center gap-3">
          <Button
            onClick={onBack}
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Control Loop Compensation Design
            </h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Design Type II/III compensators and isolated TL431-optocoupler feedback loops; optimize crossover frequency and phase margin via pole-zero synthesis.
            </p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-auto">
          <TabsList className="bg-slate-950/80 border border-slate-850 p-0.5 rounded-lg flex">
            <TabsTrigger value="type2" className="text-[9px] font-bold px-2.5 py-1">Type II</TabsTrigger>
            <TabsTrigger value="type3" className="text-[9px] font-bold px-2.5 py-1">Type III</TabsTrigger>
            <TabsTrigger value="tl431" className="text-[9px] font-bold px-2.5 py-1">TL431 + Opto</TabsTrigger>
            <TabsTrigger value="digital" className="text-[9px] font-bold px-2.5 py-1">Z-Transform (Digital)</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {errorMsg && (
        <div className="bg-red-950/40 border border-red-900 text-red-400 px-3 py-2 rounded-lg text-xs flex items-center space-x-2 flex-shrink-0">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main DragDeck Area */}
      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pr-1">
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
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-white">Design Inputs & Target Specifications</span>
                  </div>

                  <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/20 space-y-1.5 mb-2">
                    <span className="text-[9px] text-slate-400 block select-none">
                      One-click commercial compensation topology preset:
                    </span>
                    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                      {LOOP_PRESETS.map((preset, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleApplyPreset(preset)}
                          className={`px-2 py-1 text-[9px] font-medium border rounded transition-all cursor-pointer whitespace-nowrap ${
                            activeTab === preset.tab
                              ? 'bg-teal-950/30 border-teal-500 text-teal-400 font-bold'
                              : 'bg-slate-950 border-slate-800 text-slate-350 hover:border-teal-500/50 hover:text-teal-400'
                          }`}
                        >
                          {preset.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {activeTab === 'type2' && (
                    <div className="space-y-4">
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1">Plant Power Stage Parameters</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Output Voltage Vout (V)</label>
                            <input type="number" step="0.1" value={t2Vout} onChange={(e) => setT2Vout(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Full-Load Current Iout (A)</label>
                            <input type="number" step="0.5" value={t2Iout} onChange={(e) => setT2Iout(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Output Capacitance Cout (μF)</label>
                            <input type="number" value={t2Cout} onChange={(e) => setT2Cout(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Capacitor ESR (mΩ)</label>
                            <input type="number" step="0.5" value={t2Esr} onChange={(e) => setT2Esr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Switching Frequency fsw (kHz)</label>
                            <input type="number" value={t2Fsw} onChange={(e) => setT2Fsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Current Sense Resistor Ri (Ω)</label>
                            <input type="number" step="0.01" value={t2Ri} onChange={(e) => setT2Ri(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>

                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1">Feedback & Loop Crossover Targets</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Crossover Frequency fc Target (kHz)</label>
                            <input type="number" value={t2Fc} onChange={(e) => setT2Fc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Target Phase Margin PM (°)</label>
                            <input type="number" value={t2Pm} onChange={(e) => setT2Pm(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Reference Voltage Vref (V)</label>
                            <input type="number" step="0.1" value={t2Vref} onChange={(e) => setT2Vref(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Top Feedback Resistor R1 (kΩ)</label>
                            <input type="number" value={t2R1} onChange={(e) => setT2R1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <input type="checkbox" checked={t2DigitalDelay} onChange={(e) => setT2DigitalDelay(e.target.checked)} id="t2Dig" className="cursor-pointer" />
                          <label htmlFor="t2Dig" className="text-[10px] text-slate-400 cursor-pointer select-none">Include digital control sampling delay</label>
                        </div>
                        {t2DigitalDelay && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Digital Sampling Rate Fs (kHz)</label>
                            <input type="number" value={t2FsKhz} onChange={(e) => setT2FsKhz(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {activeTab === 'type3' && (
                    <div className="space-y-4">
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1">Plant Physical Parameters</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Filter Inductance L (μH)</label>
                            <input type="number" value={t3L} onChange={(e) => setT3L(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Filter Capacitance C (μF)</label>
                            <input type="number" value={t3C} onChange={(e) => setT3C(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Capacitor ESR (mΩ)</label>
                            <input type="number" step="0.5" value={t3Esr} onChange={(e) => setT3Esr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">DC Input Voltage Vin (V)</label>
                            <input type="number" value={t3Vin} onChange={(e) => setT3Vin(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">PWM Ramp Amplitude Vramp (V)</label>
                            <input type="number" step="0.1" value={t3Vramp} onChange={(e) => setT3Vramp(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Switching Frequency fsw (kHz)</label>
                            <input type="number" value={t3Fsw} onChange={(e) => setT3Fsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>

                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1">Feedback Specifications & Targets</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Crossover Frequency fc Target (kHz)</label>
                            <input type="number" value={t3Fc} onChange={(e) => setT3Fc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Target Phase Margin PM (°)</label>
                            <input type="number" value={t3Pm} onChange={(e) => setT3Pm(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Reference Voltage Vref (V)</label>
                            <input type="number" step="0.1" value={t3Vref} onChange={(e) => setT3Vref(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Top Feedback Resistor R1 (kΩ)</label>
                            <input type="number" value={t3R1} onChange={(e) => setT3R1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Output Voltage Vout (V)</label>
                            <input type="number" step="0.1" value={t3Vout} onChange={(e) => setT3Vout(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-550">Digital Sampling Rate Fs (kHz)</label>
                            <input type="number" value={t3FsKhz} onChange={(e) => setT3FsKhz(parseFloat(e.target.value) || 0)} disabled={!t3DigitalDelay} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none disabled:opacity-40" />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <input type="checkbox" checked={t3DigitalDelay} onChange={(e) => setT3DigitalDelay(e.target.checked)} id="t3Dig" className="cursor-pointer" />
                          <label htmlFor="t3Dig" className="text-[10px] text-slate-400 cursor-pointer select-none">Include digital control sampling delay</label>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'tl431' && (
                    <div className="space-y-4">
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1">Isolated Loop AC Inputs</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Output Voltage Vout (V)</label>
                            <input type="number" step="0.1" value={tlVout} onChange={(e) => setTlVout(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Top Divider Resistor Rup (kΩ)</label>
                            <input type="number" value={tlRup} onChange={(e) => setTlRup(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Crossover Frequency fc Target (kHz)</label>
                            <input type="number" value={tlFc} onChange={(e) => setTlFc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Target Phase Margin PM (°)</label>
                            <input type="number" value={tlPm} onChange={(e) => setTlPm(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Plant Gain at fc (dB)</label>
                            <input type="number" value={tlGain} onChange={(e) => setTlGain(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Optocoupler Pole fp_opto (kHz)</label>
                            <input type="number" value={tlFpOpto} onChange={(e) => setTlFpOpto(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>

                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1">Optocoupler & TL431 DC Bias Parameters</span>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">LED Forward Voltage Vf (V)</label>
                            <input type="number" step="0.1" value={dcVf} onChange={(e) => setDcVf(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">LED Series Resistor Rled (kΩ)</label>
                            <input type="number" value={dcRled} onChange={(e) => setDcRled(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Optocoupler CTR</label>
                            <input type="number" step="0.1" value={dcCtr} onChange={(e) => setDcCtr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Primary Pullup Resistor Rpull (kΩ)</label>
                            <input type="number" value={dcRpull} onChange={(e) => setDcRpull(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Controller Supply Vdd (V)</label>
                            <input type="number" step="0.5" value={dcVdd} onChange={(e) => setDcVdd(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Parallel Bleed Resistor Rpar (kΩ)</label>
                            <input type="number" value={dcRpar} onChange={(e) => setDcRpar(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'digital' && (
                    <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                      <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-850 pb-1">Continuous-to-Discrete Z-Transform</span>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">Analog Compensator Order</label>
                        <div className="grid grid-cols-2 gap-1 bg-slate-950 p-0.5 rounded border border-slate-850">
                          <button onClick={() => setDigControllerType('Type II')} className={`py-1.5 text-[8.5px] border-0 rounded cursor-pointer ${digControllerType === 'Type II' ? 'bg-teal-500/20 text-teal-400 font-bold' : 'bg-transparent text-slate-400 hover:text-white'}`}>Type II (2P2Z)</button>
                          <button onClick={() => setDigControllerType('Type III')} className={`py-1.5 text-[8.5px] border-0 rounded cursor-pointer ${digControllerType === 'Type III' ? 'bg-teal-500/20 text-teal-400 font-bold' : 'bg-transparent text-slate-400 hover:text-white'}`}>Type III (3P3Z)</button>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Continuous DC Gain Kdc</label>
                          <input type="number" value={digKdc} onChange={(e) => setDigKdc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Digital Sampling Rate Fs (kHz)</label>
                          <input type="number" value={digFs} onChange={(e) => setDigFs(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Continuous Zero fz1 (kHz)</label>
                          <input type="number" value={digFz1} onChange={(e) => setDigFz1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Continuous Zero fz2 (kHz)</label>
                          <input type="number" value={digFz2} disabled={digControllerType === 'Type II'} onChange={(e) => setDigFz2(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none disabled:opacity-40" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Continuous Pole fp1 (kHz)</label>
                          <input type="number" value={digFp1} onChange={(e) => setDigFp1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-550">Continuous Pole fp2 (kHz)</label>
                          <input type="number" value={digFp2} disabled={digControllerType === 'Type II'} onChange={(e) => setDigFp2(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none disabled:opacity-40" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* CARD: Results */}
              {key === 'results' && (
                <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                  <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                    <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      Loop Stability Margins & Synthesis Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                    <div className="space-y-2 mb-2">
                      <span className="text-[10px] font-bold text-slate-400 block select-none">Stability Design Rule Check (DRC):</span>
                      {(() => {
                        let pm = 0.0;
                        let fc = 0.0;
                        let isStable = true;
                        let errMsg = '';
                        
                        if (activeTab === 'type2' && t2Result?.bode) {
                          pm = t2Result.bode.pm_deg ?? 0.0;
                          fc = t2Result.bode.fc_khz ?? 0.0;
                        } else if (activeTab === 'type3' && t3Result?.bode) {
                          pm = t3Result.bode.pm_deg ?? 0.0;
                          fc = t3Result.bode.fc_khz ?? 0.0;
                        } else if (activeTab === 'tl431' && tlResult?.bode) {
                          pm = tlResult.bode.pm_deg ?? 0.0;
                          fc = tlResult.bode.fc_khz ?? 0.0;
                        } else if (activeTab === 'digital' && digResult?.design) {
                          const poles = [digResult.design.a1, digResult.design.a2, digResult.design.a3].filter(p => p !== undefined);
                          for (const p of poles) {
                            if (Math.abs(p) >= 1.0) {
                              isStable = false;
                              errMsg = 'Discrete denominator coefficients outside unit circle; risk of time-domain oscillatory instability!';
                            }
                          }
                        }

                        if (activeTab === 'digital') {
                          return isStable ? (
                            <div className="flex items-center gap-2 text-emerald-400 bg-emerald-950/20 p-2.5 rounded border border-emerald-900/40 text-[10px]">
                              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                              <span>Discrete difference equation poles stable within unit circle. No instability risk detected.</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 text-rose-400 bg-rose-950/20 p-2.5 rounded border border-rose-900/40 text-[10px]">
                              <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
                              <span><b>⚠️ Stability Alert:</b> {errMsg}</span>
                            </div>
                          );
                        }

                        if (pm === 0 && fc === 0) return <div className="text-[10px] text-slate-550">Waiting for loop calculation data...</div>;
                        
                        const pmAlert = pm < 45.0;
                        const fcAlert = fc > 150.0;

                        return (
                          <div className={`p-2.5 rounded border text-[10px] leading-relaxed ${
                            pmAlert ? 'bg-red-500/10 border-red-500/20 text-rose-350' :
                            fcAlert ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400' :
                            'bg-green-500/10 border-green-500/20 text-emerald-450'
                          }`}>
                            <div className="flex items-center gap-1.5 font-bold mb-0.5">
                              <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
                              <span>
                                {pmAlert ? '⚠️ Critical Warning - Insufficient Phase Margin' :
                                 fcAlert ? '⚠️ Notice - Crossover Frequency High (Noise Sensitivity)' :
                                 '✅ Normal - Loop Stability Margins Adequate'}
                              </span>
                            </div>
                            <p>Current calculated crossover: <b>{fc.toFixed(2)} kHz</b> | Phase Margin: <b>{pm.toFixed(1)}°</b> (Recommended PM ≥ 45°).</p>
                          </div>
                        );
                      })()}
                    </div>

                    <span className="text-[10px] font-bold text-slate-400 block select-none pt-2 border-t border-slate-800/80">Compensator Pole-Zero Metrics:</span>
                    {activeTab === 'type2' && t2Result?.design && (
                      <div className="grid grid-cols-3 gap-3">
                        <div className="p-3 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-400 font-medium">Zero fz</span>
                          <span className="text-sm font-bold text-cyan-300 font-mono">
                            {((t2Result.design.fz_c_hz ?? 0) / 1000).toFixed(2)} <span className="text-[9px] text-slate-400">kHz</span>
                          </span>
                        </div>
                        <div className="p-3 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-400 font-medium">Pole fp</span>
                          <span className="text-sm font-bold text-cyan-300 font-mono">
                            {((t2Result.design.fp_c_hz ?? 0) / 1000).toFixed(2)} <span className="text-[9px] text-slate-400">kHz</span>
                          </span>
                        </div>
                        <div className="p-3 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                          <span className="text-[8px] text-slate-400 font-medium">Mid-band Gain</span>
                          <span className="text-sm font-bold text-cyan-300 font-mono">
                            {(-(t2Result.design.g_plant_mag_db ?? 0)).toFixed(2)} <span className="text-[9px] text-slate-400">dB</span>
                          </span>
                        </div>
                      </div>
                    )}

                    {activeTab === 'type3' && t3Result?.design && (
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col">
                            <span className="text-[8px] text-slate-400">Zeros fz1 / fz2</span>
                            <span className="text-xs font-bold text-cyan-300 font-mono mt-0.5">
                              {((t3Result.design.fz_hz ?? 0) / 1000).toFixed(1)} / {((t3Result.design.fz_hz ?? 0) / 1000).toFixed(1)} kHz
                            </span>
                          </div>
                          <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/20 flex flex-col">
                            <span className="text-[8px] text-slate-400">Poles fp1 / fp2</span>
                            <span className="text-xs font-bold text-cyan-300 font-mono mt-0.5">
                              {((t3Result.design.fp_hz ?? 0) / 1000).toFixed(1)} / {((t3Result.design.fp_hz ?? 0) / 1000).toFixed(1)} kHz
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {activeTab === 'tl431' && tlResult?.design && (
                      <div className="space-y-3">
                        <div className="grid grid-cols-3 gap-2.5 bg-slate-900/20 p-2.5 rounded border border-slate-850">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[8px] text-slate-500">Feedback Rcomp</span>
                            <span className="text-[10px] font-bold text-white font-mono">{fmtRes(tlResult.design.r_comp_ohm)}</span>
                          </div>
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[8px] text-slate-500">Capacitor Ccomp</span>
                            <span className="text-[10px] font-bold text-cyan-400 font-mono">{fmtCap(tlResult.design.c_comp_f)}</span>
                          </div>
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[8px] text-slate-500">Capacitor Chf</span>
                            <span className="text-[10px] font-bold text-cyan-400 font-mono">{fmtCap(tlResult.design.c_hf_f)}</span>
                          </div>
                        </div>
                        
                        {tlDcResult && (
                          <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/20 space-y-1.5">
                            <span className="text-[9px] font-bold text-slate-400 block">TL431 Static DC Operating Point:</span>
                            <div className="grid grid-cols-3 gap-2">
                              <div className="flex flex-col">
                                <span className="text-[8px] text-slate-550">Static Cathode Voltage Vka</span>
                                <span className="text-[10px] font-bold text-slate-200 font-mono">{(tlDcResult.v_ka_static ?? 0).toFixed(2)} V</span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-[8px] text-slate-550">LED Current Iled</span>
                                <span className="text-[10px] font-bold text-emerald-450 font-mono">{(tlDcResult.i_led_ma ?? 0).toFixed(2)} mA</span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-[8px] text-slate-550">Bias Region</span>
                                <span className={`text-[10px] font-bold font-mono ${tlDcResult.is_valid ? 'text-emerald-450' : 'text-red-400'}`}>
                                  {tlDcResult.is_valid ? 'Valid' : 'Low Margin'}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {activeTab === 'digital' && digResult?.design && (
                      <div className="space-y-3">
                        <div className="bg-slate-900/20 p-3 rounded-xl border border-slate-850 space-y-2">
                          <span className="text-[9px] font-bold text-slate-400 block">Discrete Difference Equation Coefficients (Bilinear Transform):</span>
                          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                            <div className="space-y-1">
                              <div>b0: <span className="text-emerald-400 font-bold">{(digResult.design.b0 ?? 0).toExponential(5)}</span></div>
                              <div>b1: <span className="text-emerald-400">{(digResult.design.b1 ?? 0).toExponential(5)}</span></div>
                              <div>b2: <span className="text-emerald-400">{(digResult.design.b2 ?? 0).toExponential(5)}</span></div>
                              {digResult.design.b3 !== undefined && (
                                <div>b3: <span className="text-emerald-400">{(digResult.design.b3 ?? 0).toExponential(5)}</span></div>
                              )}
                            </div>
                            <div className="space-y-1">
                              <div>a1: <span className="text-teal-400">{(digResult.design.a1 ?? 0).toExponential(5)}</span></div>
                              <div>a2: <span className="text-teal-400">{(digResult.design.a2 ?? 0).toExponential(5)}</span></div>
                              {digResult.design.a3 !== undefined && (
                                <div>a3: <span className="text-teal-400">{(digResult.design.a3 ?? 0).toExponential(5)}</span></div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* CARD: Chart */}
              {key === 'chart' && (
                <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                  <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0 flex flex-row justify-between items-center gap-4">
                    <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                      Loop Frequency & Transient Response Characteristics
                    </CardTitle>
                    <div className="flex bg-slate-950/80 border border-slate-800 rounded p-0.5 select-none">
                      <button
                        onClick={() => setChartView('bode')}
                        className={`px-2 py-0.5 text-[9px] font-bold rounded cursor-pointer transition-all ${chartView === 'bode' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'}`}
                      >
                        Bode Domain
                      </button>
                      <button
                        onClick={() => setChartView('step')}
                        className={`px-2 py-0.5 text-[9px] font-bold rounded cursor-pointer transition-all ${chartView === 'step' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'}`}
                      >
                        Time Step
                      </button>
                    </div>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 flex justify-center items-center bg-slate-950/15">
                    <div className="w-full h-full min-h-[300px]">
                      {(() => {
                        let bodeData = null;
                        let stepData = null;

                        if (activeTab === 'type2' && t2Result) {
                          bodeData = t2Result.bode;
                          stepData = t2Result.step_response;
                        } else if (activeTab === 'type3' && t3Result) {
                          bodeData = t3Result.bode;
                          stepData = t3Result.step_response;
                        } else if (activeTab === 'tl431' && tlResult) {
                          bodeData = tlResult.bode;
                          stepData = tlResult.step_response;
                        }

                        if (chartView === 'bode') {
                          return bodeData ? (
                            <ReactECharts option={getBodeOption(bodeData)} style={{ width: '100%', height: '100%', minHeight: '300px' }} notMerge={true} />
                          ) : (
                            <div className="text-xs text-slate-500 italic">Waiting for frequency response data...</div>
                          );
                        } else {
                          return stepData ? (
                            <ReactECharts option={getStepOption(stepData)} style={{ width: '100%', height: '100%', minHeight: '300px' }} notMerge={true} />
                          ) : (
                            <div className="text-xs text-slate-500 italic">Waiting for step response simulation...</div>
                          );
                        }
                      })()}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* CARD: Schematic */}
              {key === 'schematic' && (
                <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                  <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                    <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      <Compass className="w-3.5 h-3.5 text-cyan-400" />
                      Hardware Topology Sandbox & Standard BOM
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-950/15">
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-full items-center">
                      <div className="lg:col-span-6 flex justify-center items-center p-2 rounded bg-slate-950/30 border border-slate-850/60 min-h-[220px] overflow-hidden">
                        {activeTab === 'digital' ? (
                          <svg viewBox="0 0 200 120" className="w-full max-w-[200px] h-auto text-slate-400">
                            <defs>
                              <style>
                                {`
                                  @keyframes stroke-flow-dig {
                                    to { stroke-dashoffset: -20; }
                                  }
                                  .animate-flow-dig {
                                    stroke-dasharray: 4, 3;
                                    animation: stroke-flow-dig 1.2s linear infinite;
                                    stroke: #10b981;
                                  }
                                `}
                              </style>
                            </defs>
                            <rect x="10" y="45" width="25" height="30" fill="#0f172a" stroke="#334155" strokeWidth="1.5" rx="3" />
                            <text x="15" y="63" fill="#e2e8f0" fontSize="8">Error</text>
                            <text x="17" y="71" fill="#e2e8f0" fontSize="6">e[n]</text>

                            <path d="M 35 60 L 65 60" fill="none" strokeWidth="1.5" className="animate-flow-dig" />
                            <circle cx="50" cy="60" r="1.5" fill="#10b981" />

                            <rect x="65" y="40" width="70" height="40" fill="#1e293b" stroke="#10b981" strokeWidth="1.5" rx="4" />
                            <text x="80" y="58" fill="#10b981" fontSize="9" fontWeight="bold">H(z) Filter</text>
                            <text x="73" y="70" fill="#94a3b8" fontSize="7">Bilinear Transform</text>

                            <path d="M 135 60 L 165 60" fill="none" strokeWidth="1.5" className="animate-flow-dig" />

                            <rect x="165" y="45" width="25" height="30" fill="#0f172a" stroke="#334155" strokeWidth="1.5" rx="3" />
                            <text x="171" y="63" fill="#a78bfa" fontSize="8">PWM</text>
                            <text x="171" y="71" fill="#a78bfa" fontSize="6">u[n]</text>
                          </svg>
                        ) : (
                          <div className="w-full h-full min-h-[220px]">
                            <LoopCompensationSchematicSandbox
                              activeTab={activeTab}
                              t2R1={t2R1}
                              t2Result={t2Result}
                              t3R1={t3R1}
                              t3Result={t3Result}
                              tlResult={tlResult}
                              tlVout={tlVout}
                              dcRled={dcRled}
                              tlDcResult={tlDcResult}
                              hvResult={null}
                              digResult={digResult}
                              digControllerType={digControllerType}
                            />
                          </div>
                        )}
                      </div>

                      <div className="lg:col-span-6 h-full flex flex-col justify-center min-h-[200px]">
                        {activeTab === 'digital' ? (
                          <div className="space-y-1.5 h-full">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-[10px] font-bold text-slate-400 block font-mono">Embedded C Implementation Code (PID):</span>
                              {digResult?.c_code && (
                                <button
                                  onClick={handleCopyCode}
                                  className="px-2 py-0.5 text-[8px] bg-slate-900 hover:bg-slate-800 text-teal-400 rounded transition-all cursor-pointer"
                                >
                                  {copySuccess ? 'Copied!' : 'Copy Code'}
                                </button>
                              )}
                            </div>
                            <textarea
                              readOnly
                              value={digResult?.c_code || 'Waiting for code generation...'}
                              className="w-full h-36 bg-slate-950 border border-slate-850 rounded p-2 text-[9px] font-mono text-cyan-400 focus:outline-none"
                            />
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <span className="text-[10px] font-bold text-slate-400 block font-mono">Recommended Standard E96 / E24 BOM:</span>
                            {getMatchedBom().length > 0 ? (
                              <div className="max-h-[160px] overflow-y-auto border border-slate-850 rounded">
                                <table className="w-full text-left border-collapse text-[9px] text-slate-350">
                                  <thead>
                                    <tr className="border-b border-slate-800 bg-slate-900/40 text-slate-500 font-bold">
                                      <th className="p-1.5">Designator</th>
                                      <th className="p-1.5">Calc Value</th>
                                      <th className="p-1.5">Standard</th>
                                      <th className="p-1.5 text-right font-mono">Error</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {getMatchedBom().map((item, idx) => (
                                      <tr key={idx} className="border-b border-slate-850/60 hover:bg-slate-900/20 transition-colors">
                                        <td className="p-1.5 font-bold text-teal-400">{item.designator}</td>
                                        <td className="p-1.5 font-mono">{item.calcValue}</td>
                                        <td className="p-1.5 font-mono text-emerald-450 font-semibold">{item.stdValue}</td>
                                        <td className="p-1.5 text-right font-mono text-pink-400">{item.error}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            ) : (
                              <div className="text-[10px] text-slate-500 italic text-center py-4">No BOM data generated yet...</div>
                            )}
                            <div className="text-[8.5px] text-slate-500 font-sans italic leading-relaxed">
                              * Sizing criteria: Resistors selected from 1% E96 series; Capacitors matched against standard commercial MLCC E24 series.
                            </div>
                          </div>
                        )}
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