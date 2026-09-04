import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, ShieldAlert, CheckCircle2, Compass } from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
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
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-xs text-slate-350" : "inline-block text-xs"} />;
};

interface SinglePointResponse {
  t_c: number;
  r_ntc_kohm: number;
  v_adc_v: number;
}

interface TableGenResponse {
  code: string;
  curve: {
    temps: number[];
    adc_vals: number[];
  };
}

interface SteinhartResponse {
  coeff_a: number;
  coeff_b: number;
  coeff_c: number;
}

interface OptDividerResponse {
  r_div_opt_kohm: number;
  t_center: number;
  curve: {
    temps: number[];
    voltages: number[];
    sensitivities: number[];
  };
}

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

function generateLocalCurve(r25: number, beta: number, rDiv: number, vref: number, isPullup: boolean) {
  const temps: number[] = [];
  const resistances: number[] = [];
  const voltages: number[] = [];
  for (let t = -40; t <= 125; t += 2) {
    const tKelvin = Math.max(t + 273.15, 1e-3);
    const r = r25 * Math.exp(beta * (1 / tKelvin - 1 / 298.15));
    const v = isPullup ? (vref * r) / Math.max(rDiv + r, 1e-6) : (vref * rDiv) / Math.max(rDiv + r, 1e-6);
    temps.push(t);
    resistances.push(parseFloat(r.toFixed(3)));
    voltages.push(parseFloat(v.toFixed(4)));
  }
  return { temps, resistances, voltages };
}

export default function NtcCalculatorPanel({ onBack }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<'single' | 'table' | 'steinhart' | 'opt'>('single', 'activeTab');
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
    handleHeightResizeStartTop,
    handleResetCardHeight,
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_ntccalculatorpanel_v5',
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

  const COMMON_NTC_PRESETS = [
    { name: 'Standard B57861 (10k, B3950)', r25: 10.0, beta: 3950.0, rdiv: 10.0, vref: 3.3, isPullup: true },
    { name: 'High-Temp NTC100K (100k, B3950)', r25: 100.0, beta: 3950.0, rdiv: 100.0, vref: 3.3, isPullup: true },
    { name: 'Precision NTC5K (5k, B3470)', r25: 5.0, beta: 3470.0, rdiv: 5.1, vref: 3.3, isPullup: true },
    { name: 'Low-Temp NTC2K (2k, B3100)', r25: 2.0, beta: 3100.0, rdiv: 2.0, vref: 3.3, isPullup: true }
  ];

  // Shared NTC Core Specs
  const [r25, setR25] = useState<number>(10.0);
  const [beta, setBeta] = useState<number>(3950.0);
  const [rDiv, setRDiv] = useState<number>(10.0);
  const [vref, setVref] = useState<number>(3.3);
  const [isPullup, setIsPullup] = useState<boolean>(true);

  // Tab 1: Single Point
  const [calcMode, setCalcMode] = useState<number>(0);
  const [inpVal, setInpVal] = useState<number>(25.0);
  const [singleRes, setSingleRes] = useState<SinglePointResponse | null>(null);
  const [singleError, setSingleError] = useState<string | null>(null);

  // Tab 2: Table Generator
  const [startT, setStartT] = useState<number>(-40);
  const [endT, setEndT] = useState<number>(125);
  const [stepT, setStepT] = useState<number>(1);
  const [adcMax, setAdcMax] = useState<number>(4095);
  const [tableRes, setTableRes] = useState<TableGenResponse | null>(null);
  const [tableError, setTableError] = useState<string | null>(null);

  // Tab 3: Steinhart-Hart
  const [t1, setT1] = useState<number>(-40);
  const [r1, setR1] = useState<number>(336.5);
  const [t2, setT2] = useState<number>(25);
  const [r2, setR2] = useState<number>(10.0);
  const [t3, setT3] = useState<number>(125);
  const [r3, setR3] = useState<number>(0.34);
  const [shRes, setShRes] = useState<SteinhartResponse | null>(null);
  const [shError, setShError] = useState<string | null>(null);

  // Steinhart verification state
  const [verifyR, setVerifyR] = useState<number>(10.0);
  const [verifyT, setVerifyT] = useState<number | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  // Tab 4: Resistor Divider Opt
  const [tCenter, setTCenter] = useState<number>(90.0);
  const [optRes, setOptRes] = useState<OptDividerResponse | null>(null);
  const [optError, setOptError] = useState<string | null>(null);

  const handleSingleCalc = async () => {
    setSingleError(null);
    try {
      const response = await apiFetch('/api/calculate/ntc/single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r25, beta, r_div: rDiv, vref, mode: calcMode, inp_val: inpVal, is_pullup: isPullup })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Calculation failed');
      }
      const data: SinglePointResponse = await response.json();
      setSingleRes(data);
    } catch (e: any) {
      setSingleError(e.message);
    }
  };

  const handleTableGen = async () => {
    setTableError(null);
    try {
      const response = await apiFetch('/api/calculate/ntc/table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r25, beta, r_div: rDiv, is_pullup: isPullup, start_t: startT, end_t: endT, step: stepT, adc_max: adcMax })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Lookup table generation failed');
      }
      const data: TableGenResponse = await response.json();
      setTableRes(data);
    } catch (e: any) {
      setTableError(e.message);
    }
  };

  const handleSteinhartCalc = async () => {
    setShError(null);
    try {
      const response = await apiFetch('/api/calculate/ntc/steinhart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ t_points: [t1, t2, t3], r_points: [r1, r2, r3] })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Steinhart-Hart fitting failed');
      }
      const data: SteinhartResponse = await response.json();
      setShRes(data);
    } catch (e: any) {
      setShError(e.message);
    }
  };

  const handleShVerify = async () => {
    if (!shRes) return;
    setVerifyError(null);
    try {
      const response = await apiFetch('/api/calculate/ntc/sh_verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r_in: verifyR, coeff_a: shRes.coeff_a, coeff_b: shRes.coeff_b, coeff_c: shRes.coeff_c })
      });
      if (response.ok) {
        const data = await response.json();
        setVerifyT(data.t_c);
      } else {
        const errData = await response.json().catch(() => ({}));
        setVerifyError(errData.detail || 'Verification failed');
        setVerifyT(null);
      }
    } catch (e: any) {
      setVerifyError(e.message || 'Network error');
      setVerifyT(null);
    }
  };

  const handleOptDivider = async () => {
    setOptError(null);
    try {
      const response = await apiFetch('/api/calculate/ntc/opt_divider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r25, beta, t_center: tCenter, vref })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Optimal divider calculation failed');
      }
      const data: OptDividerResponse = await response.json();
      setOptRes(data);
    } catch (e: any) {
      setOptError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'single') {
      handleSingleCalc();
    } else if (activeTab === 'table') {
      handleTableGen();
    } else if (activeTab === 'opt') {
      handleOptDivider();
    }
  }, [r25, beta, rDiv, vref, isPullup, calcMode, inpVal, activeTab]);

  useEffect(() => {
    if (activeTab === 'table') {
      handleTableGen();
    }
  }, [startT, endT, stepT, adcMax]);

  useEffect(() => {
    if (activeTab === 'steinhart') {
      handleSteinhartCalc();
    }
  }, [t1, r1, t2, r2, t3, r3, activeTab]);

  useEffect(() => {
    if (shRes) {
      handleShVerify();
    }
  }, [verifyR, shRes]);

  useEffect(() => {
    if (activeTab === 'opt') {
      handleOptDivider();
    }
  }, [tCenter]);

  useEffect(() => {
    if (calcMode === 0) {
      setInpVal(25.0);
    } else if (calcMode === 1) {
      setInpVal(1.65);
    } else {
      setInpVal(10.0);
    }
  }, [calcMode]);

  const getNtcChartOption = () => {
    const commonTooltip = {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.85)',
      borderColor: '#38bdf8',
      borderWidth: 1,
      textStyle: { color: '#e2e8f0', fontSize: 10 },
      extraCssText: 'backdrop-filter: blur(8px); border-radius: 8px;'
    };

    if (activeTab === 'single') {
      const { temps, resistances, voltages } = generateLocalCurve(r25, beta, rDiv, vref, isPullup);
      const currT = singleRes ? singleRes.t_c : 25.0;
      const currR = singleRes ? singleRes.r_ntc_kohm : 10.0;
      const currV = singleRes ? singleRes.v_adc_v : 1.65;

      let closestIdx = 0;
      let minDiff = 999;
      temps.forEach((t, idx) => {
        if (Math.abs(t - currT) < minDiff) {
          minDiff = Math.abs(t - currT);
          closestIdx = idx;
        }
      });

      return {
        backgroundColor: 'transparent',
        title: {
          text: 'NTC Temperature vs Resistance / Voltage Response Curve',
          textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' },
          left: 'center',
          top: 5
        },
        tooltip: commonTooltip,
        legend: {
          data: ['Resistance R_ntc (kΩ)', 'Voltage V_adc (V)'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          bottom: 0
        },
        grid: { left: '10%', right: '10%', top: '20%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: temps,
          axisLine: { lineStyle: { color: '#334155' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 }
        },
        yAxis: [
          {
            type: 'value',
            name: 'Resistance (kΩ)',
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
            axisLine: { lineStyle: { color: '#334155' } }
          },
          {
            type: 'value',
            name: 'Voltage (V)',
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { show: false },
            axisLine: { lineStyle: { color: '#334155' } }
          }
        ],
        series: [
          {
            name: 'Resistance R_ntc (kΩ)',
            type: 'line',
            yAxisIndex: 0,
            data: resistances,
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 3, color: '#38bdf8', shadowBlur: 8, shadowColor: 'rgba(56, 189, 248, 0.5)' },
            markPoint: {
              data: [
                {
                  name: 'Operating Resistance',
                  coord: [closestIdx, currR],
                  value: `${currR.toFixed(2)}k`,
                  itemStyle: { color: '#0284c7' }
                }
              ],
              label: { show: true, fontSize: 8, position: 'top', color: '#fff' }
            }
          },
          {
            name: 'Voltage V_adc (V)',
            type: 'line',
            yAxisIndex: 1,
            data: voltages,
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 3, color: '#a78bfa', shadowBlur: 8, shadowColor: 'rgba(167, 139, 250, 0.5)' },
            markPoint: {
              data: [
                {
                  name: 'Operating Voltage',
                  coord: [closestIdx, currV],
                  value: `${currV.toFixed(2)}V`,
                  itemStyle: { color: '#7c3aed' }
                }
              ],
              label: { show: true, fontSize: 8, position: 'bottom', color: '#fff' }
            }
          }
        ]
      };
    } else if (activeTab === 'table') {
      const curve = tableRes?.curve || { temps: [], adc_vals: [] };
      return {
        backgroundColor: 'transparent',
        title: {
          text: 'ADC Digitized Temperature Lookup Table Curve',
          textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' },
          left: 'center',
          top: 5
        },
        tooltip: commonTooltip,
        grid: { left: '10%', right: '10%', top: '20%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: curve.temps,
          axisLine: { lineStyle: { color: '#334155' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 }
        },
        yAxis: {
          type: 'value',
          name: `ADC Scale (0 ~ ${adcMax})`,
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
          axisLine: { lineStyle: { color: '#334155' } }
        },
        series: [
          {
            name: 'ADC Code',
            type: 'line',
            data: curve.adc_vals,
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 3, color: '#10b981', shadowBlur: 8, shadowColor: 'rgba(16, 185, 129, 0.5)' }
          }
        ]
      };
    } else if (activeTab === 'opt') {
      const curve = optRes?.curve || { temps: [], voltages: [], sensitivities: [] };
      let maxSensIdx = 0;
      let maxSens = -1;
      curve.sensitivities.forEach((s, idx) => {
        if (s > maxSens) {
          maxSens = s;
          maxSensIdx = idx;
        }
      });

      return {
        backgroundColor: 'transparent',
        title: {
          text: 'Optimized Operating Point Sensitivity dV/dT Curve',
          textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' },
          left: 'center',
          top: 5
        },
        tooltip: commonTooltip,
        legend: {
          data: ['ADC Voltage (V)', 'Sensitivity dV/dT (mV/°C)'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          bottom: 0
        },
        grid: { left: '10%', right: '10%', top: '20%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: curve.temps,
          axisLine: { lineStyle: { color: '#334155' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 }
        },
        yAxis: [
          {
            type: 'value',
            name: 'Voltage (V)',
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
            axisLine: { lineStyle: { color: '#334155' } }
          },
          {
            type: 'value',
            name: 'Sensitivity (mV/°C)',
            nameTextStyle: { color: '#64748b', fontSize: 9 },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { show: false },
            axisLine: { lineStyle: { color: '#334155' } }
          }
        ],
        series: [
          {
            name: 'ADC Voltage (V)',
            type: 'line',
            yAxisIndex: 0,
            data: curve.voltages,
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 3, color: '#38bdf8', shadowBlur: 8, shadowColor: 'rgba(56, 189, 248, 0.5)' }
          },
          {
            name: 'Sensitivity dV/dT (mV/°C)',
            type: 'line',
            yAxisIndex: 1,
            data: curve.sensitivities,
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 3, color: '#f59e0b', shadowBlur: 8, shadowColor: 'rgba(245, 158, 11, 0.5)' },
            markPoint: {
              data: [
                {
                  name: 'Max Sensitivity',
                  coord: [maxSensIdx, maxSens],
                  value: `Max: ${maxSens.toFixed(1)}`,
                  itemStyle: { color: '#d97706' }
                }
              ],
              label: { show: true, fontSize: 8, position: 'top', color: '#fff' }
            }
          }
        ]
      };
    } else if (activeTab === 'steinhart') {
      const temps: number[] = [];
      const resistances: number[] = [];
      for (let t = -40; t <= 125; t += 2) {
        temps.push(t);
        const tKelvin = Math.max(t + 273.15, 1e-3);
        const r = r2 * Math.exp(beta * (1 / tKelvin - 1 / Math.max(t2 + 273.15, 1e-3)));
        resistances.push(parseFloat(r.toFixed(3)));
      }

      return {
        backgroundColor: 'transparent',
        title: {
          text: 'Steinhart-Hart High-Precision Non-linear Fit Curve',
          textStyle: { color: '#e2e8f0', fontSize: 10, fontWeight: 'bold' },
          left: 'center',
          top: 5
        },
        tooltip: commonTooltip,
        grid: { left: '10%', right: '10%', top: '20%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: temps,
          axisLine: { lineStyle: { color: '#334155' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 }
        },
        yAxis: {
          type: 'log',
          name: 'NTC Resistance (kΩ) [Log]',
          nameTextStyle: { color: '#64748b', fontSize: 9 },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } },
          axisLine: { lineStyle: { color: '#334155' } }
        },
        series: [
          {
            name: 'Resistance',
            type: 'line',
            data: resistances,
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 3, color: '#38bdf8', shadowBlur: 8, shadowColor: 'rgba(56, 189, 248, 0.5)' },
            markPoint: {
              data: [
                { name: 'Cal Point T1', coord: [4, r1], value: `R1: ${r1}k`, itemStyle: { color: '#ef4444' } },
                { name: 'Cal Point T2', coord: [20, r2], value: `R2: ${r2}k`, itemStyle: { color: '#10b981' } },
                { name: 'Cal Point T3', coord: [36, r3], value: `R3: ${r3}k`, itemStyle: { color: '#f59e0b' } }
              ],
              label: { show: true, fontSize: 8, position: 'top', color: '#fff' }
            }
          }
        ]
      };
    }
    return {};
  };

  const getSelfHeatingInfo = () => {
    if (activeTab === 'steinhart') {
      return null;
    }
    let rNtc = r25;
    let tVal = 25.0;
    if (activeTab === 'single' && singleRes) {
      rNtc = singleRes.r_ntc_kohm;
      tVal = singleRes.t_c;
    } else if (activeTab === 'opt' && optRes) {
      rNtc = optRes.r_div_opt_kohm;
      tVal = optRes.t_center;
    }
    if (rNtc <= 0) return null;
    const currentMa = vref / (rDiv + rNtc);
    const pdMw = Math.pow(currentMa, 2) * rNtc;
    const delta = 2.0;
    const deltaT = pdMw / delta;
    let status: 'green' | 'yellow' | 'red' = 'green';
    let msg = 'Sensor self-heating is negligible; measurement accuracy unaffected.';
    if (deltaT >= 0.5) {
      status = 'red';
      msg = 'Warning: Severe self-heating! Increase divider resistor Rdiv or lower Vref to reduce bias current.';
    } else if (deltaT >= 0.1) {
      status = 'yellow';
      msg = 'Advisory: Minor self-heating present; may impact high-precision instrumentation.';
    }
    return {
      currentUa: currentMa * 1000,
      pdMw,
      deltaT,
      status,
      msg,
      tVal
    };
  };

  const getActiveError = () => {
    if (activeTab === 'single') return singleError;
    if (activeTab === 'table') return tableError;
    if (activeTab === 'steinhart') return shError;
    return optError;
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      <div className="space-y-3">
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
              <h1 className="text-base font-bold text-white tracking-tight">NTC Thermistor Temperature & Linearization</h1>
              <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">Fit NTC resistance curves using Beta or Steinhart-Hart equations, optimize divider sensitivity, and generate lookup C tables.</p>
            </div>
          </div>
          <Button onClick={handleResetLayout} variant="outline" size="sm" className="bg-slate-900 border border-slate-800 text-slate-350 hover:bg-slate-800 text-[10px] rounded-lg">
            Reset Layout
          </Button>
        </div>

        <div className="flex border-b border-slate-800 gap-1 overflow-x-auto pb-1">
          {(['single', 'table', 'steinhart', 'opt'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-[10px] font-semibold rounded-t-lg transition-all border-b-2 cursor-pointer ${
                activeTab === tab
                  ? 'border-b-cyan-500 text-cyan-400 font-bold bg-slate-950/40'
                  : 'border-b-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab === 'single' && 'Single Point Solve'}
              {tab === 'table' && 'LUT C Code Generation'}
              {tab === 'steinhart' && 'Steinhart-Hart Fitting'}
              {tab === 'opt' && 'Divider Optimization'}
            </button>
          ))}
        </div>

        {getActiveError() && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs p-3 rounded-lg flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
            <span>Calculation Alert: {getActiveError()}</span>
          </div>
        )}
      </div>

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 pr-1 p-3 pt-0 min-h-0">
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
              {key === 'input' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4 bg-slate-900/40 border border-slate-800/80 rounded-xl backdrop-blur-md">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Operating Inputs</span>
                  </div>

                  {activeTab !== 'steinhart' && (
                    <div className="p-3 rounded-lg border border-slate-850 bg-slate-950/20 space-y-1.5 mb-2">
                      <span className="text-[9px] text-slate-400 block select-none">
                        Commercial Thermistor Presets:
                      </span>
                      <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                        {COMMON_NTC_PRESETS.map((preset, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => {
                              setR25(preset.r25);
                              setBeta(preset.beta);
                              setRDiv(preset.rdiv);
                              setVref(preset.vref);
                              setIsPullup(preset.isPullup);
                            }}
                            className="px-2 py-1 text-[9px] font-medium bg-slate-950 border border-slate-800 hover:border-cyan-500 hover:bg-cyan-950/20 text-slate-350 hover:text-cyan-400 rounded transition-all cursor-pointer whitespace-nowrap"
                          >
                            {preset.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeTab !== 'steinhart' && (
                    <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                      <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">NTC Core Specifications</span>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-500">Nominal R25 (kΩ)</label>
                          <input type="number" step="0.5" value={r25} onChange={(e) => setR25(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-500">Beta Constant B (K)</label>
                          <input type="number" step="10" value={beta} onChange={(e) => setBeta(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                      </div>
                      {activeTab !== 'opt' && (
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Divider Resistor Rdiv (kΩ)</label>
                            <input type="number" step="0.5" value={rDiv} onChange={(e) => setRDiv(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">ADC Reference Vref (V)</label>
                            <input type="number" step="0.1" value={vref} onChange={(e) => setVref(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      )}
                      {activeTab !== 'opt' && (
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-500">Topology Mode</label>
                          <select value={isPullup ? 'pullup' : 'pulldown'} onChange={(e) => setIsPullup(e.target.value === 'pullup')} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs w-full text-white focus:outline-none focus:border-cyan-500 cursor-pointer">
                            <option value="pullup">Pull-Up (NTC to GND)</option>
                            <option value="pulldown">Pull-Down (NTC to Vref)</option>
                          </select>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'single' && (
                    <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                      <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Solve Direction & Input Value</span>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">Mode</label>
                        <select value={calcMode} onChange={(e) => setCalcMode(parseInt(e.target.value))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs w-full text-white focus:outline-none focus:border-cyan-500 cursor-pointer">
                          <option value={0}>Direction A: Temp T (°C) → Resistance R & Voltage V</option>
                          <option value={1}>Direction B: Voltage V (V) → Temp T & Resistance R</option>
                          <option value={2}>Direction C: Resistance R (kΩ) → Temp T & Voltage V</option>
                        </select>
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">
                          {calcMode === 0 && 'Target Temperature (°C)'}
                          {calcMode === 1 && 'Measured ADC Voltage (V)'}
                          {calcMode === 2 && 'NTC Measured Resistance (kΩ)'}
                        </label>
                        <input type="number" step="any" value={inpVal} onChange={(e) => setInpVal(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                      </div>
                    </div>
                  )}

                  {activeTab === 'table' && (
                    <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                      <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">LUT Temperature Span</span>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-500">Start Temp (°C)</label>
                          <input type="number" value={startT} onChange={(e) => setStartT(parseInt(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-500">End Temp (°C)</label>
                          <input type="number" value={endT} onChange={(e) => setEndT(parseInt(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[8px] text-slate-500">Step (°C)</label>
                          <input type="number" value={stepT} onChange={(e) => setStepT(parseInt(e.target.value) || 1)} className="w-full bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none focus:border-cyan-500" />
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">ADC Scale Max</label>
                        <select value={adcMax} onChange={(e) => setAdcMax(parseInt(e.target.value))} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs w-full text-white focus:outline-none focus:border-cyan-500 cursor-pointer">
                          <option value={1023}>10-bit (0 ~ 1023)</option>
                          <option value={4095}>12-bit (0 ~ 4095)</option>
                          <option value={65535}>16-bit (0 ~ 65535)</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {activeTab === 'steinhart' && (
                    <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                      <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Three-Point Calibration Pairs (T-R)</span>
                      <div className="space-y-2.5">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Low Temp T1 (°C)</label>
                            <input type="number" value={t1} onChange={(e) => setT1(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Resistance R1 (kΩ)</label>
                            <input type="number" value={r1} onChange={(e) => setR1(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Room Temp T2 (°C)</label>
                            <input type="number" value={t2} onChange={(e) => setT2(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Resistance R2 (kΩ)</label>
                            <input type="number" value={r2} onChange={(e) => setR2(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">High Temp T3 (°C)</label>
                            <input type="number" value={t3} onChange={(e) => setT3(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[8px] text-slate-500">Resistance R3 (kΩ)</label>
                            <input type="number" value={r3} onChange={(e) => setR3(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'opt' && (
                    <div className="border border-slate-800 rounded-lg p-3.5 bg-slate-900/20 space-y-3">
                      <span className="text-[10px] font-bold text-slate-300 border-b border-slate-800/60 pb-1.5 block">Optimization Target</span>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">Target Center Temp T_center (°C)</label>
                        <input type="number" value={tCenter} onChange={(e) => setTCenter(parseFloat(e.target.value) || 25.0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[8px] text-slate-500">ADC Reference Vref (V)</label>
                        <input type="number" step="0.1" value={vref} onChange={(e) => setVref(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none focus:border-cyan-500" />
                      </div>
                    </div>
                  )}
                </div>
              )}

            {key === 'results' && (
              <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                  <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    Physical Outputs & Design Verification
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
                  <div className="space-y-2 mb-2">
                    <span className="text-[10px] font-bold text-slate-400 block select-none">Self-Heating & Precision DRC:</span>
                    {activeTab === 'steinhart' ? (
                      <div className="p-2.5 rounded border border-slate-800 bg-slate-950/20 text-slate-400 text-[10px] leading-relaxed">
                        <span>For three-point Steinhart-Hart calibration, bias current through the thermistor should be kept <b>≤ 100 μA</b> to limit self-heating error to <b>≤ 0.05°C</b>.</span>
                      </div>
                    ) : (() => {
                      const sh = getSelfHeatingInfo();
                      if (!sh) return <div className="text-[10px] text-slate-550">Awaiting parameter input...</div>;
                      return (
                        <div className={`p-2.5 rounded border text-[10px] leading-relaxed ${
                          sh.status === 'red' ? 'bg-red-500/10 border-red-500/20 text-rose-350' :
                          sh.status === 'yellow' ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400' :
                          'bg-green-500/10 border-green-500/20 text-emerald-450'
                        }`}>
                          <div className="flex items-center gap-1.5 font-bold mb-1">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
                            <span>
                              {sh.status === 'red' && 'Warning - Excessive Self-Heating'}
                              {sh.status === 'yellow' && 'Notice - Minor Self-Heating'}
                              {sh.status === 'green' && 'OK - Self-Heating Negligible'}
                            </span>
                          </div>
                          <p>{sh.msg}</p>
                          <div className="text-[8px] text-slate-500 mt-1 font-mono">
                            Point: {sh.tVal.toFixed(1)}°C | Current: {sh.currentUa.toFixed(1)} μA | Rise: {sh.deltaT.toFixed(3)}°C
                          </div>
                        </div>
                      );
                    })()}
                  </div>

                  <span className="text-[10px] font-bold text-slate-400 block select-none pt-2 border-t border-slate-800/80">Calculated Metrics:</span>
                  {activeTab === 'single' && singleRes && (
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3.5 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-400 font-medium">Temperature T_c</span>
                        <span className="text-lg font-bold text-cyan-300 font-mono">
                          {(singleRes.t_c ?? 0.0).toFixed(2)} <span className="text-xs text-slate-400">°C</span>
                        </span>
                      </div>
                      <div className="p-3.5 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-400 font-medium">NTC Resistance R_ntc</span>
                        <span className="text-lg font-bold text-cyan-300 font-mono">
                          {(singleRes.r_ntc_kohm ?? 0.0).toFixed(3)} <span className="text-xs text-slate-400">kΩ</span>
                        </span>
                      </div>
                      <div className="p-3.5 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-400 font-medium">Sampling Voltage V_adc</span>
                        <span className="text-lg font-bold text-cyan-300 font-mono">
                          {(singleRes.v_adc_v ?? 0.0).toFixed(4)} <span className="text-xs text-slate-400">V</span>
                        </span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'table' && tableRes && (
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/20 text-xs leading-relaxed space-y-2">
                      <div className="font-semibold text-slate-300 flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span>Temperature LUT C Code Generated Successfully</span>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        Span: <b>{startT} °C</b> to <b>{endT} °C</b>, generating <b>{Math.floor((endT - startT) / stepT) + 1}</b> ADC calibration entries.
                      </p>
                    </div>
                  )}

                  {activeTab === 'steinhart' && shRes && (
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-400 font-medium">Fitting Constant A</span>
                        <span className="text-xs font-bold text-cyan-300 font-mono mt-1">
                          {(shRes.coeff_a ?? 0.0).toExponential(6)}
                        </span>
                      </div>
                      <div className="p-3 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-400 font-medium">Fitting Constant B</span>
                        <span className="text-xs font-bold text-cyan-300 font-mono mt-1">
                          {(shRes.coeff_b ?? 0.0).toExponential(6)}
                        </span>
                      </div>
                      <div className="p-3 rounded-xl border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                        <span className="text-[10px] text-slate-400 font-medium">Fitting Constant C</span>
                        <span className="text-xs font-bold text-cyan-300 font-mono mt-1">
                          {(shRes.coeff_c ?? 0.0).toExponential(6)}
                        </span>
                      </div>
                    </div>
                  )}

                  {activeTab === 'opt' && optRes && (
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3.5 rounded-xl bg-gradient-to-br from-cyan-950/20 to-blue-950/20 border border-cyan-500/20 flex flex-col">
                        <span className="text-[10px] text-cyan-400 font-semibold tracking-wider uppercase">Optimal Divider R_div</span>
                        <span className="text-lg font-black text-cyan-300 font-mono mt-1">
                          {(optRes.r_div_opt_kohm ?? 0.0).toFixed(3)} kΩ
                        </span>
                        <span className="text-[9px] text-slate-500 mt-1">
                          E96 Std: {findClosestStandard(optRes.r_div_opt_kohm, E96).value.toFixed(2)} kΩ (Error: {findClosestStandard(optRes.r_div_opt_kohm, E96).error.toFixed(2)}%)
                        </span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-gradient-to-br from-blue-950/20 to-indigo-950/20 border border-blue-500/20 flex flex-col">
                        <span className="text-[10px] text-blue-400 font-semibold tracking-wider uppercase">Matched Center Temp T_center</span>
                        <span className="text-lg font-black text-blue-300 font-mono mt-1">
                          {(optRes.t_center ?? 0.0).toFixed(1)} °C
                        </span>
                        <span className="text-[9px] text-slate-500 mt-1">
                          Maximum sensitivity dV/dT achieved here
                        </span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {key === 'chart' && (
              <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                  <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    Nonlinear Fit & Sensitivity Response
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 flex justify-center items-center bg-slate-950/15">
                  <div className="w-full h-full min-h-[300px]">
                    <ReactECharts
                      option={getNtcChartOption()}
                      style={{ width: '100%', height: '100%', minHeight: '300px' }}
                      notMerge={true}
                    />
                  </div>
                </CardContent>
              </Card>
            )}

            {key === 'schematic' && (
              <Card className="h-full flex flex-col bg-slate-900/40 border-slate-800/80 overflow-hidden">
                <CardHeader className="py-2.5 border-b border-slate-800/80 flex-shrink-0">
                  <CardTitle className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-cyan-400" />
                    Interactive Topology & Firmware Code
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto scrollbar-thin p-4 bg-slate-950/15">
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-full items-center">
                    <div className="lg:col-span-6 flex justify-center items-center p-2 rounded bg-slate-950/30 border border-slate-850/60 min-h-[220px]">
                      <svg viewBox="0 0 200 120" className="w-full max-w-[200px] h-auto text-slate-400 bg-transparent">
                        <defs>
                          <style>
                            {`
                              @keyframes stroke-flow-ntc {
                                to { stroke-dashoffset: -20; }
                              }
                              .animate-flow-ntc {
                                stroke-dasharray: 5, 4;
                                animation: stroke-flow-ntc 1.5s linear infinite;
                                stroke: #38bdf8;
                              }
                            `}
                          </style>
                        </defs>
                        <circle cx="100" cy="15" r="4" fill="none" stroke="#64748b" strokeWidth="1.5" />
                        <line x1="100" y1="11" x2="100" y2="7" stroke="#64748b" strokeWidth="1.5" />
                        <line x1="96" y1="7" x2="104" y2="7" stroke="#64748b" strokeWidth="1.5" />
                        <text x="108" y="16" fill="#64748b" fontSize="7" fontWeight="bold">Vref</text>

                        {isPullup ? (
                          <>
                            <path d="M 100 19 L 100 35" stroke="#38bdf8" strokeWidth="1.5" />
                            <rect x="94" y="35" width="12" height="20" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                            <text x="110" y="47" fill="#64748b" fontSize="7">R_div</text>
                            
                            <path d="M 100 55 L 100 75" stroke="#38bdf8" strokeWidth="1.5" />
                            <circle cx="100" cy="65" r="2.5" fill="#38bdf8" />
                            <path d="M 100 65 L 145 65" stroke="#38bdf8" strokeWidth="1.5" />
                            <circle cx="145" cy="65" r="3" stroke="#a78bfa" fill="#1e1b4b" strokeWidth="1.5" />
                            <text x="153" y="68" fill="#a78bfa" fontSize="7" fontWeight="bold">V_adc</text>

                            <rect x="94" y="75" width="12" height="20" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="90" x2="110" y1="90" y2="80" stroke="#f43f5e" strokeWidth="1" />
                            <line x1="90" x2="86" y1="90" y2="90" stroke="#f43f5e" strokeWidth="1" />
                            <text x="76" y="93" fill="#f43f5e" fontSize="6">-t°</text>
                            <text x="110" y="87" fill="#f43f5e" fontSize="7" fontWeight="bold">NTC</text>

                            <path d="M 100 95 L 100 108" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="90" x2="110" y1="108" y2="108" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="94" x2="106" y1="111" y2="111" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="98" x2="102" y1="114" y2="114" stroke="#64748b" strokeWidth="1.5" />

                            <path d="M 100 19 L 100 108" fill="none" strokeWidth="1.5" className="animate-flow-ntc" />
                          </>
                        ) : (
                          <>
                            <path d="M 100 19 L 100 35" stroke="#38bdf8" strokeWidth="1.5" />
                            <rect x="94" y="35" width="12" height="20" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="90" x2="110" y1="50" y2="40" stroke="#f43f5e" strokeWidth="1" />
                            <line x1="90" x2="86" y1="50" y2="50" stroke="#f43f5e" strokeWidth="1" />
                            <text x="76" y="53" fill="#f43f5e" fontSize="6">-t°</text>
                            <text x="110" y="47" fill="#f43f5e" fontSize="7" fontWeight="bold">NTC</text>

                            <path d="M 100 55 L 100 75" stroke="#38bdf8" strokeWidth="1.5" />
                            <circle cx="100" cy="65" r="2.5" fill="#38bdf8" />
                            <path d="M 100 65 L 145 65" stroke="#38bdf8" strokeWidth="1.5" />
                            <circle cx="145" cy="65" r="3" stroke="#a78bfa" fill="#1e1b4b" strokeWidth="1.5" />
                            <text x="153" y="68" fill="#a78bfa" fontSize="7" fontWeight="bold">V_adc</text>

                            <rect x="94" y="75" width="12" height="20" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                            <text x="110" y="87" fill="#64748b" fontSize="7">R_div</text>

                            <path d="M 100 95 L 100 108" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="90" x2="110" y1="108" y2="108" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="94" x2="106" y1="111" y2="111" stroke="#64748b" strokeWidth="1.5" />
                            <line x1="98" x2="102" y1="114" y2="114" stroke="#64748b" strokeWidth="1.5" />

                            <path d="M 100 19 L 100 108" fill="none" strokeWidth="1.5" className="animate-flow-ntc" />
                          </>
                        )}
                      </svg>
                    </div>

                    <div className="lg:col-span-6 h-full flex flex-col justify-center min-h-[200px]">
                      {activeTab === 'table' ? (
                        <div className="space-y-1.5 h-full">
                          <span className="text-[10px] font-bold text-slate-400 block mb-1">C Code Table Outputs:</span>
                          <textarea
                            readOnly
                            value={tableRes?.code || 'Awaiting code generation...'}
                            className="w-full h-36 bg-slate-950 border border-slate-850 rounded p-2 text-[9px] font-mono text-cyan-400 focus:outline-none"
                          />
                        </div>
                      ) : activeTab === 'steinhart' ? (
                        <div className="space-y-3 leading-relaxed text-[10px]">
                          <span className="text-[10px] font-bold text-slate-400 block border-b border-slate-800 pb-1 font-mono">Steinhart-Hart Coefficients Verify:</span>
                          <div className="flex gap-4 items-center bg-slate-950/40 p-2.5 rounded border border-slate-850">
                            <div className="flex flex-col gap-1">
                              <label className="text-[8px] text-slate-500">Test Resistance (kΩ)</label>
                              <input
                                type="number"
                                step="0.1"
                                value={verifyR}
                                onChange={(e) => setVerifyR(parseFloat(e.target.value) || 0)}
                                className="bg-slate-950 border border-slate-850 rounded p-1 text-[10px] text-white w-20 focus:outline-none focus:border-cyan-500"
                              />
                            </div>
                            <div className="flex flex-col gap-0.5">
                              <span className="text-[8px] text-slate-500">Calculated T_c</span>
                              <span className="text-xs font-bold text-green-400 font-mono">
                                {verifyT !== null ? `${verifyT.toFixed(3)} °C` : '--'}
                              </span>
                              {verifyError && (
                                <span className="text-[8px] text-red-500 font-sans block mt-0.5 leading-none">
                                  {verifyError}
                                </span>
                              )}
                            </div>
                          </div>
                          <Latex math="\frac{1}{T} = A + B\ln R + C(\ln R)^3" block />
                        </div>
                      ) : (
                        <div className="space-y-2 text-[10px] font-mono leading-relaxed">
                          <span className="text-[10px] font-bold text-slate-400 block mb-1">Physics Models:</span>
                          <div>
                            <span className="text-[9px] text-slate-550 block">1. Exponential NTC Equation:</span>
                            <Latex math="R_{ntc} = R_{25} \cdot e^{B \left( \frac{1}{T} - \frac{1}{298.15} \right)}" block />
                          </div>
                          <div>
                            <span className="text-[9px] text-slate-550 block">2. Max Sensitivity (Zero Crossing of 2nd Derivative):</span>
                            <Latex math="\frac{d^2 V}{dT^2} = 0 \implies R_{div} = R_{ntc}(T_{center})" block />
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
