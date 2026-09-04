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
  ShieldAlert,
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

export default function FilterPassivePanel({ onBack }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<'passive' | 'active' | 'power_emi' | 'stability_pdn'>('passive', 'activeTab');

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
    panelKey: 'layout_filterpassivepanel_v3_' + activeTab,
    defaultCards: ['input', 'results'],
    defaultColumns: { input: 'left', results: 'right' },
    defaultSpans: { input: 4, results: 8 },
    defaultHeights: { input: 820, results: 820 }
  });

  const [, setLoading] = useState<boolean>(false);
  const [, setErrorMsg] = useState<string>('');
  const [drcWarnings, setDrcWarnings] = useState<string[]>([]);

  // Tab 1: Signals Passive (RC/LC/RL)
  const [passSubTab, setPassSubTab] = useTabHistoryState<'rc' | 'lc' | 'rl'>('rc', 'passSubTab');
  const [passMode, setPassMode] = useState<number>(0); // 0: fc, 1: R/L, 2: C/L
  const [passR, setPassR] = useState<number>(1000.0);
  const [passL, setPassL] = useState<number>(100.0);
  const [passC, setPassC] = useState<number>(0.1);
  const [passFc, setPassFc] = useState<number>(1000.0);
  const [passResult, setPassResult] = useState<any>(null);

  // Tab 2: Active (Sallen-Key/MFB)
  const [actTopo, setActTopo] = useState<number>(0); // 0: Sallen-Key, 1: MFB
  const [actFc, setActFc] = useState<number>(1000.0);
  const [actQ, setActQ] = useState<number>(0.707);
  const [actC1, setActC1] = useState<number>(10.0);
  const [actC2Opt, setActC2Opt] = useState<string>('none');
  const [actResult, setActResult] = useState<any>(null);

  // Tab 3: Power & EMI
  const [powerSubTab, setPowerSubTab] = useTabHistoryState<'emi' | 'cmc_sat' | 'spwm' | 'bead'>('emi', 'powerSubTab');
  const [emiType, setEmiType] = useState<'dm' | 'cm'>('dm');
  const [emiL, setEmiL] = useState<number>(100.0);
  const [emiC, setEmiC] = useState<number>(0.1);
  const [emiFc, setEmiFc] = useState<number>(50.0); // kHz
  const [emiResult, setEmiResult] = useState<any>(null);

  const [cmcL, setCmcL] = useState<number>(2.2); // mH
  const [cmcLeakRatio, setCmcLeakRatio] = useState<number>(1.0); // %
  const [cmcIdm, setCmcIdm] = useState<number>(5.0); // A
  const [cmcN, setCmcN] = useState<number>(24);
  const [cmcAe, setCmcAe] = useState<number>(120.0); // mm²
  const [cmcBsat, setCmcBsat] = useState<number>(0.35); // T
  const [cmcResult, setCmcResult] = useState<any>(null);

  const [spwmVdc, setSpwmVdc] = useState<number>(400.0);
  const [spwmVac, setSpwmVac] = useState<number>(220.0);
  const [spwmPkw, setSpwmPkw] = useState<number>(5.0);
  const [spwmFsw, setSpwmFsw] = useState<number>(20.0); // kHz
  const [spwmFout, setSpwmFout] = useState<number>(50.0); // Hz
  const [spwmRipple, setSpwmRipple] = useState<number>(20.0); // %
  const [spwmIsLcl, setSpwmIsLcl] = useState<boolean>(false);
  const [spwmResult, setSpwmResult] = useState<any>(null);

  const [beadL, setBeadL] = useState<number>(1.5); // uH
  const [beadC, setBeadC] = useState<number>(2.2); // uF
  const [beadResult, setBeadResult] = useState<any>(null);

  // Tab 4: Middlebrook & PDN Decoupling
  const [stabSubTab, setStabSubTab] = useTabHistoryState<'stability' | 'pdn'>('stability', 'stabSubTab');
  const [stabVin, setStabVin] = useState<number>(48.0);
  const [stabPout, setStabPout] = useState<number>(120.0);
  const [stabL, setStabL] = useState<number>(4.7); // uH
  const [stabC, setStabC] = useState<number>(100.0); // uF
  const [stabResult, setStabResult] = useState<any>(null);

  const [pdnMode, setPdnMode] = useState<'target' | 'anti'>('target');
  const [pdnDi, setPdnDi] = useState<number>(3.0); // A
  const [pdnDv, setPdnDv] = useState<number>(50.0); // mV
  const [pdnEsr, setPdnEsr] = useState<number>(5.0); // mΩ
  const [pdnEsl, setPdnEsl] = useState<number>(0.8); // nH
  const [pdnTgtZ, setPdnTgtZ] = useState<number | null>(null);
  const [pdnCapNumResult, setPdnCapNumResult] = useState<any>(null);

  const [pdnC1, setPdnC1] = useState<number>(10.0); // uF
  const [pdnEsr1, setPdnEsr1] = useState<number>(8.0); // mΩ
  const [pdnEsl1, setPdnEsl1] = useState<number>(1.2); // nH
  const [pdnC2, setPdnC2] = useState<number>(0.1); // uF
  const [pdnEsr2, setPdnEsr2] = useState<number>(20.0); // mΩ
  const [pdnEsl2, setPdnEsl2] = useState<number>(0.4); // nH
  const [pdnResult, setPdnResult] = useState<any>(null);

  // Load verification payload on mount
  useEffect(() => {
    const raw = localStorage.getItem('target_filter_passive_data');
    if (raw) {
      try {
        const payload = JSON.parse(raw);
        setActiveTab('passive');
        setPassSubTab('lc');
        if (payload.l_uh !== undefined) setPassL(payload.l_uh);
        if (payload.c_uf !== undefined) setPassC(payload.c_uf);
        if (payload.l_uh !== undefined) setStabL(payload.l_uh);
        if (payload.c_uf !== undefined) setStabC(payload.c_uf);
      } catch (e) {
        console.error('Failed to parse target_filter_passive_data:', e);
      } finally {
        localStorage.removeItem('target_filter_passive_data');
      }
    }
  }, [setActiveTab, setPassSubTab]);

  const computePassive = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/filter_design/passive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filter_type: passSubTab,
          mode: passMode,
          r: passR,
          l_uh: passL,
          c_uf: passC,
          fc_hz: passFc
        })
      });
      if (activeTabRef.current !== 'passive') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "Passive filter calculation failed. Please check inputs.");
      }
      const data = await res.json();
      setPassResult(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  const computeActive = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/filter_design/active', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topo: actTopo,
          fc_hz: actFc,
          q: actQ,
          c1_nf: actC1,
          c2_nf_opt: actC2Opt === 'none' ? 0.0 : parseFloat(actC2Opt)
        })
      });
      if (activeTabRef.current !== 'active') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "Active filter design failed. Please check C1/C2 and Q constraints.");
      }
      const data = await res.json();
      setActResult(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  const computePowerEmi = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      let body: any = { calc_type: powerSubTab };
      if (powerSubTab === 'emi') {
        body.calc_type = emiType === 'dm' ? 'emi_dm' : 'emi_cm';
        body.emi_l_uh = emiL;
        body.emi_c_uf = emiC;
        body.emi_fc_hz = emiFc * 1000.0;
      } else if (powerSubTab === 'cmc_sat') {
        body.cmc_l_mh = cmcL;
        body.cmc_leak_ratio = cmcLeakRatio;
        body.cmc_idm = cmcIdm;
        body.cmc_n = cmcN;
        body.cmc_ae = cmcAe;
        body.cmc_bsat = cmcBsat;
      } else if (powerSubTab === 'spwm') {
        body.spwm_vdc = spwmVdc;
        body.spwm_vac_ll = spwmVac;
        body.spwm_p_kw = spwmPkw;
        body.spwm_fsw_khz = spwmFsw;
        body.spwm_fout_hz = spwmFout;
        body.spwm_ripple_pct = spwmRipple;
        body.spwm_is_lcl = spwmIsLcl;
      } else if (powerSubTab === 'bead') {
        body.bead_l_uh = beadL;
        body.bead_c_uf = beadC;
      }

      const res = await apiFetch('/api/calculate/filter_design/power', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (activeTabRef.current !== 'power_emi') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "Power/EMI filter calculation failed. Please check inputs.");
      }
      const data = await res.json();
      if (powerSubTab === 'emi') setEmiResult(data);
      else if (powerSubTab === 'cmc_sat') setCmcResult(data);
      else if (powerSubTab === 'spwm') setSpwmResult(data);
      else if (powerSubTab === 'bead') setBeadResult(data);

      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  const computeInputStability = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/filter_design/input_stability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vin: stabVin, pout: stabPout, l_uh: stabL, c_uf: stabC })
      });
      if (activeTabRef.current !== 'stability_pdn') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "Input stability calculation failed");
      }
      const data = await res.json();
      setStabResult(data);
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  const computePdn = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      let body: any = { calc_type: pdnMode };
      if (pdnMode === 'target') {
        body.di = pdnDi;
        body.dv_ripple_mv = pdnDv;
      } else if (pdnMode === 'anti') {
        body.c1_uf = pdnC1;
        body.esr1_mohm = pdnEsr1;
        body.esl1_nh = pdnEsl1;
        body.c2_uf = pdnC2;
        body.esr2_mohm = pdnEsr2;
        body.esl2_nh = pdnEsl2;
      }

      const res = await apiFetch('/api/calculate/filter_design/pdn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (activeTabRef.current !== 'stability_pdn') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "PDN impedance and decoupling analysis failed");
      }
      const data = await res.json();

      if (pdnMode === 'target') {
        setPdnTgtZ(data.z_target_mohm);
        const capRes = await apiFetch('/api/calculate/filter_design/pdn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            calc_type: 'cap_num',
            z_target_mohm: data.z_target_mohm,
            cap_esr_mohm: pdnEsr,
            cap_esl_nh: pdnEsl
          })
        });
        if (capRes.ok) {
          const capData = await capRes.json();
          setPdnCapNumResult(capData);
        }
      } else {
        setPdnResult(data);
      }
      setDrcWarnings(data.drc_warnings || []);
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  // Triggers
  useEffect(() => {
    if (activeTab === 'passive') computePassive();
  }, [passSubTab, passMode, passR, passL, passC, passFc, activeTab]);

  useEffect(() => {
    if (activeTab === 'active') computeActive();
  }, [actTopo, actFc, actQ, actC1, actC2Opt, activeTab]);

  useEffect(() => {
    if (activeTab === 'power_emi') computePowerEmi();
  }, [powerSubTab, emiType, emiL, emiC, emiFc, cmcL, cmcLeakRatio, cmcIdm, cmcN, cmcAe, cmcBsat, spwmVdc, spwmVac, spwmPkw, spwmFsw, spwmFout, spwmRipple, spwmIsLcl, beadL, beadC, activeTab]);

  useEffect(() => {
    if (activeTab === 'stability_pdn') {
      if (stabSubTab === 'stability') computeInputStability();
      else computePdn();
    }
  }, [stabSubTab, stabVin, stabPout, stabL, stabC, pdnMode, pdnDi, pdnDv, pdnEsr, pdnEsl, pdnC1, pdnEsr1, pdnEsl1, pdnC2, pdnEsr2, pdnEsl2, activeTab]);

  const getBodeOption = (bodeData: any, fc_hz: number, title: string) => {
    if (!bodeData || bodeData.length === 0) return {};
    const f = bodeData.map((d: any) => d.f);
    const mag = bodeData.map((d: any) => d.mag_db);
    const phase = bodeData.map((d: any) => d.phase_deg);

    return {
      title: { text: title, textStyle: { color: '#e2e8f0', fontSize: 11 }, left: 'center' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        extraCssText: 'backdrop-filter: blur(8px);',
        formatter: (params: any) => {
          let freq = params[0].axisValue;
          let html = `<div class="text-xs font-bold mb-1">Frequency: ${parseFloat(freq).toFixed(1)} Hz</div>`;
          params.forEach((p: any) => {
            html += `<div class="flex items-center gap-2 justify-between text-[10px]">
              <span class="text-slate-400">${p.seriesName}:</span>
              <span class="font-semibold text-right" style="color:${p.color}">${p.value[1].toFixed(2)} ${p.seriesName.includes('Magnitude') ? 'dB' : '°'}</span>
            </div>`;
          });
          return html;
        }
      },
      legend: {
        data: ['Magnitude', 'Phase'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: [
        { left: '12%', right: '12%', top: '15%', height: '32%', containLabel: true },
        { left: '12%', right: '12%', top: '55%', height: '32%', containLabel: true }
      ],
      xAxis: [
        { gridIndex: 0, type: 'log', logBase: 10, show: true, axisLabel: { show: false }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } },
        { gridIndex: 1, type: 'log', logBase: 10, name: 'Hz', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } }
      ],
      yAxis: [
        { gridIndex: 0, type: 'value', name: 'Gain (dB)', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: '#1e293b' } } },
        { gridIndex: 1, type: 'value', name: 'Phase (deg)', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: '#1e293b' } } }
      ],
      series: [
        {
          name: 'Magnitude', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: f.map((freq: number, i: number) => [freq, mag[i]]), symbol: 'none', lineStyle: { width: 2, color: '#38bdf8', shadowBlur: 8, shadowColor: 'rgba(0, 255, 255, 0.8)' }, itemStyle: { color: '#38bdf8' },
          markLine: {
            symbol: 'none',
            data: [
              { yAxis: -3, lineStyle: { color: '#f59e0b', type: 'dashed', width: 1 } },
              ...(fc_hz > 0 ? [{ xAxis: fc_hz, lineStyle: { color: '#ef4444', type: 'dashed', width: 1.2 }, label: { formatter: `fc = ${fc_hz >= 1000 ? (fc_hz / 1000).toFixed(2) + ' kHz' : fc_hz.toFixed(0) + ' Hz'}`, color: '#ef4444', position: 'end' } }] : [])
            ]
          }
        },
        { name: 'Phase', type: 'line', xAxisIndex: 1, yAxisIndex: 1, data: f.map((freq: number, i: number) => [freq, phase[i]]), symbol: 'none', lineStyle: { width: 2, color: '#a855f7', shadowBlur: 8, shadowColor: 'rgba(255, 0, 255, 0.8)' }, itemStyle: { color: '#a855f7' } }
      ]
    };
  };

  const getPdnBodeOption = (bodeData: any, f_peak_mhz: number, z_peak_ohm: number) => {
    if (!bodeData || bodeData.length === 0) return {};
    const f = bodeData.map((d: any) => d.f);
    const z1 = bodeData.map((d: any) => d.z1_mag);
    const z2 = bodeData.map((d: any) => d.z2_mag);
    const z_total = bodeData.map((d: any) => d.z_total);

    return {
      title: { text: 'PDN Parallel Decoupling Impedance Response', textStyle: { color: '#e2e8f0', fontSize: 11 }, left: 'center' },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0f172a',
        borderColor: '#334155',
        textStyle: { color: '#f1f5f9' },
        extraCssText: 'backdrop-filter: blur(8px);',
        formatter: (params: any) => {
          let freq = params[0].axisValue;
          let html = `<div class="text-xs font-bold mb-1">Frequency: ${(parseFloat(freq) / 1e6).toFixed(3)} MHz</div>`;
          params.forEach((p: any) => {
            html += `<div class="flex items-center gap-2 justify-between text-[10px]">
              <span class="text-slate-400">${p.seriesName}:</span>
              <span class="font-semibold text-right" style="color:${p.color}">${p.value[1].toFixed(4)} Ω</span>
            </div>`;
          });
          return html;
        }
      },
      legend: {
        data: ['Capacitor C1 Impedance', 'Capacitor C2 Impedance', 'Total Parallel Impedance'],
        textStyle: { color: '#94a3b8', fontSize: 9 },
        bottom: 0
      },
      grid: { left: '12%', right: '12%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: { type: 'log', logBase: 10, name: 'Hz', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } } },
      yAxis: { type: 'log', logBase: 10, name: 'Impedance (Ω)', nameTextStyle: { color: '#94a3b8', fontSize: 9 }, splitLine: { lineStyle: { color: '#1e293b' } } },
      series: [
        { name: 'Capacitor C1 Impedance', type: 'line', data: f.map((freq: number, i: number) => [freq, z1[i]]), symbol: 'none', lineStyle: { width: 1, type: 'dashed', color: '#38bdf8' }, itemStyle: { color: '#38bdf8' } },
        { name: 'Capacitor C2 Impedance', type: 'line', data: f.map((freq: number, i: number) => [freq, z2[i]]), symbol: 'none', lineStyle: { width: 1, type: 'dashed', color: '#a855f7' }, itemStyle: { color: '#a855f7' } },
        {
          name: 'Total Parallel Impedance', type: 'line', data: f.map((freq: number, i: number) => [freq, z_total[i]]), symbol: 'none', lineStyle: { width: 2.5, color: '#f43f5e', shadowBlur: 8, shadowColor: 'rgba(255, 0, 255, 0.8)' }, itemStyle: { color: '#f43f5e' },
          markPoint: {
            data: [
              { name: 'Anti-Resonance Peak', coord: [f_peak_mhz * 1e6, z_peak_ohm], value: `Anti-Res: ${f_peak_mhz.toFixed(2)} MHz\nZ: ${z_peak_ohm.toFixed(2)} Ω`, itemStyle: { color: '#f59e0b' }, label: { position: 'top', color: '#f1f5f9', fontSize: 9 } }
            ]
          }
        }
      ]
    };
  };

  const getMatchedBom = (): BomItem[] => {
    const items: BomItem[] = [];
    if (activeTab === 'passive' && passResult) {
      if (passMode === 1) {
        if (passResult.r) {
          const match = findClosestStandard(passResult.r, E96);
          items.push({ designator: 'R', calcValue: `${passResult.r.toFixed(1)} Ω`, stdValue: `${match.value.toFixed(1)} Ω`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'Filter main matching resistor' });
        }
      } else if (passMode === 2) {
        if (passResult.c_uf && (passSubTab === 'rc' || passSubTab === 'lc')) {
          const match = findClosestStandard(passResult.c_uf * 1e-6, E24);
          items.push({ designator: 'C', calcValue: `${passResult.c_uf.toFixed(3)} uF`, stdValue: `${(match.value * 1e6).toFixed(3)} uF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'Filter bypass decoupling capacitor' });
        }
      }
    } else if (activeTab === 'active' && actResult?.success) {
      const { r1, r2, r3, c2 } = actResult;
      if (r1) {
        const match = findClosestStandard(r1, E96);
        items.push({ designator: 'R1', calcValue: `${r1.toFixed(1)} Ω`, stdValue: `${match.value.toFixed(1)} Ω`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'Input scaling resistor' });
      }
      if (r2) {
        const match = findClosestStandard(r2, E96);
        items.push({ designator: 'R2', calcValue: `${r2.toFixed(1)} Ω`, stdValue: `${match.value.toFixed(1)} Ω`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'Negative feedback loop damping resistor' });
      }
      if (r3 && r3 > 0) {
        const match = findClosestStandard(r3, E96);
        items.push({ designator: 'R3', calcValue: `${r3.toFixed(1)} Ω`, stdValue: `${match.value.toFixed(1)} Ω`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Resistor (E96)', desc: 'Reference bias resistor' });
      }
      if (c2) {
        const match = findClosestStandard(c2, E24);
        items.push({ designator: 'C2', calcValue: `${(c2 * 1e9).toFixed(2)} nF`, stdValue: `${(match.value * 1e9).toFixed(2)} nF`, error: `${match.error > 0 ? '+' : ''}${match.error}%`, type: 'Capacitor (E24)', desc: 'Integration damping capacitor' });
      }
    } else if (activeTab === 'power_emi') {
      if (powerSubTab === 'emi' && emiResult) {
        const match = findClosestStandard(emiResult.c_uf * 1e-6, E24);
        items.push({
          designator: emiType === 'dm' ? 'Cx' : 'Cy',
          calcValue: emiType === 'dm' ? `${emiResult.c_uf.toFixed(3)} uF` : `${(emiResult.c_nf).toFixed(2)} nF`,
          stdValue: emiType === 'dm' ? `${(match.value * 1e6).toFixed(3)} uF` : `${(match.value * 1e9).toFixed(2)} nF`,
          error: `${match.error > 0 ? '+' : ''}${match.error}%`,
          type: 'Safety Cap (E24)',
          desc: emiType === 'dm' ? 'Across-the-line differential Cx capacitor' : 'Line-to-ground common-mode Cy capacitor'
        });
      } else if (powerSubTab === 'spwm' && spwmResult) {
        const matchL = findClosestStandard(spwmResult.l_uh * 1e-6, E24);
        const matchC = findClosestStandard(spwmResult.c_uf * 1e-6, E24);
        items.push({ designator: 'L_filter', calcValue: `${spwmResult.l_uh.toFixed(1)} uH`, stdValue: `${(matchL.value * 1e6).toFixed(1)} uH`, error: `${matchL.error > 0 ? '+' : ''}${matchL.error}%`, type: 'Power Inductor', desc: 'SPWM main choke inductor' });
        items.push({ designator: 'C_filter', calcValue: `${spwmResult.c_uf.toFixed(2)} uF`, stdValue: `${(matchC.value * 1e6).toFixed(2)} uF`, error: `${matchC.error > 0 ? '+' : ''}${matchC.error}%`, type: 'Film Cap', desc: 'AC side low-ESL parallel capacitor' });
      }
    }
    return items;
  };

  const bomList = getMatchedBom();

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
              <h1 className="text-base font-bold text-white tracking-tight">Passive & Active Filter Design</h1>
              <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
                Design signal-conditioning filters and CM/DM EMI filters, evaluate PDN decoupling impedances and Middlebrook stability criteria.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button size="sm" variant="outline" className="h-8 text-xs border-slate-800 hover:bg-slate-900 text-slate-400" onClick={handleResetLayout}>
              <RefreshCw className="w-3.5 h-3.5 mr-1" /> Reset Layout
            </Button>
            <select
              value={activeTab}
              onChange={(e) => setActiveTab(e.target.value as any)}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-cyan-400 font-bold outline-none focus:border-cyan-500 cursor-pointer"
            >
              <option value="passive">1. Signal Passive Filters</option>
              <option value="active">2. Signal Active Filters</option>
              <option value="power_emi">3. Power & EMI Filters</option>
              <option value="stability_pdn">4. Impedance & Decoupling PDN</option>
            </select>
          </div>
        </div>

        {drcWarnings.length > 0 && (
          <div className="flex flex-col gap-2">
            {drcWarnings.map((warn, i) => (
              <div
                key={i}
                className="text-xs p-2.5 rounded-lg border bg-yellow-500/10 border-yellow-500/20 text-yellow-300 flex items-start gap-2"
              >
                <ShieldAlert className="w-3.5 h-3.5 text-yellow-400 mt-0.5 flex-shrink-0" />
                <span>{warn}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 p-3 pt-0 min-h-0">
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
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">Filter Parameter Inputs</span>
                  </div>

                  {activeTab === 'passive' && (
                    <select
                      value={passSubTab}
                      onChange={(e) => setPassSubTab(e.target.value as any)}
                      className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-350 focus:outline-none"
                    >
                      <option value="rc">RC 1st-Order</option>
                      <option value="lc">LC 2nd-Order</option>
                      <option value="rl">RL 1st-Order</option>
                    </select>
                  )}
                  {activeTab === 'power_emi' && (
                    <select
                      value={powerSubTab}
                      onChange={(e) => setPowerSubTab(e.target.value as any)}
                      className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-350 focus:outline-none"
                    >
                      <option value="emi">EMI LC Filter</option>
                      <option value="cmc_sat">CMC Core Saturation</option>
                      <option value="spwm">SPWM Inverter Filter</option>
                      <option value="bead">Ferrite Bead Damping</option>
                    </select>
                  )}
                  {activeTab === 'stability_pdn' && (
                    <select
                      value={stabSubTab}
                      onChange={(e) => setStabSubTab(e.target.value as any)}
                      className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-350 focus:outline-none"
                    >
                      <option value="stability">Middlebrook Stability</option>
                      <option value="pdn">PDN Anti-Resonance</option>
                    </select>
                  )}
                </div>

                {/* 1. Passive inputs */}
                {activeTab === 'passive' && (
                  <div className="space-y-3.5">
                    <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-2">
                      <span className="text-[10px] font-semibold text-slate-350">Target Solving Mode & Conditions</span>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-500">Mode</label>
                          <select value={passMode} onChange={(e) => setPassMode(parseInt(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none">
                            <option value={0}>Solve Cutoff fc</option>
                            <option value={1}>Solve Resistance R / L</option>
                            <option value={2}>Solve Capacitance C / L</option>
                          </select>
                        </div>
                        {(passMode === 1 || passMode === 2) && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Target fc (Hz)</label>
                            <input type="number" value={passFc} onChange={e => setPassFc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        )}
                        {(passMode === 0 || passMode === 2) && (passSubTab === 'rc' || passSubTab === 'rl') && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Paired Resistor R (Ω)</label>
                            <input type="number" value={passR} onChange={e => setPassR(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-2">
                      <span className="text-[10px] font-semibold text-slate-350">Inductance & Capacitance Settings</span>
                      <div className="grid grid-cols-2 gap-3">
                        {(passSubTab === 'lc' || passSubTab === 'rl') && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Filter Inductor L (μH)</label>
                            <input type="number" value={passL} onChange={e => setPassL(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        )}
                        {(passSubTab === 'rc' || passSubTab === 'lc') && (passMode === 0 || passMode === 1) && (
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Filter Capacitor C (μF)</label>
                            <input type="number" value={passC} onChange={e => setPassC(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. Active inputs */}
                {activeTab === 'active' && (
                  <div className="space-y-3.5">
                    <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] text-slate-500">Op-Amp Topology</label>
                        <select value={actTopo} onChange={e => setActTopo(parseInt(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none">
                          <option value={0}>Sallen-Key (Voltage-Controlled Voltage Source)</option>
                          <option value={1}>MFB (Multiple Feedback Infinite Gain)</option>
                        </select>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-500">Target Cutoff fc (Hz)</label>
                          <input type="number" value={actFc} onChange={e => setActFc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-500">Quality Factor Q</label>
                          <input type="number" step="0.01" value={actQ} onChange={e => setActQ(parseFloat(e.target.value) || 0.707)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-500">Base Capacitor C1 (nF)</label>
                          <input type="number" value={actC1} onChange={e => setActC1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-500">Paired C2 (nF) ('none' for auto)</label>
                          <input type="text" value={actC2Opt} onChange={e => setActC2Opt(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 3. Power & EMI inputs */}
                {activeTab === 'power_emi' && (
                  <div className="space-y-3.5">
                    {powerSubTab === 'emi' && (
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">EMI Noise Mode</label>
                            <select value={emiType} onChange={e => setEmiType(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none">
                              <option value="dm">Differential Mode (DM)</option>
                              <option value="cm">Common Mode (CM)</option>
                            </select>
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Target fc (kHz)</label>
                            <input type="number" value={emiFc} onChange={e => setEmiFc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Inductance (μH)</label>
                            <input type="number" value={emiL} onChange={e => setEmiL(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">{emiType === 'dm' ? 'DM Capacitor Cx (uF)' : 'CM Capacitor Cy (nF)'}</label>
                            <input type="number" value={emiC} onChange={e => setEmiC(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>
                    )}

                    {powerSubTab === 'cmc_sat' && (
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">CM Inductance Lcm (mH)</label>
                            <input type="number" value={cmcL} onChange={e => setCmcL(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Leakage Inductance Ratio (%)</label>
                            <input type="number" value={cmcLeakRatio} onChange={e => setCmcLeakRatio(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">DM Current Idm (A)</label>
                            <input type="number" value={cmcIdm} onChange={e => setCmcIdm(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Winding Turns N</label>
                            <input type="number" value={cmcN} onChange={e => setCmcN(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Core Ae (mm²)</label>
                            <input type="number" value={cmcAe} onChange={e => setCmcAe(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-500">Saturation Flux Density Bsat (T)</label>
                          <input type="number" step="0.05" value={cmcBsat} onChange={e => setCmcBsat(parseFloat(e.target.value) || 0)} className="w-full bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                        </div>
                      </div>
                    )}

                    {powerSubTab === 'spwm' && (
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">DC Bus Vdc (V)</label>
                            <input type="number" value={spwmVdc} onChange={e => setSpwmVdc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Output Vac_ll (V)</label>
                            <input type="number" value={spwmVac} onChange={e => setSpwmVac(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Rated Power P (kW)</label>
                            <input type="number" value={spwmPkw} onChange={e => setSpwmPkw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Carrier fsw (kHz)</label>
                            <input type="number" value={spwmFsw} onChange={e => setSpwmFsw(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Fundamental fout (Hz)</label>
                            <input type="number" value={spwmFout} onChange={e => setSpwmFout(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Ripple Ratio LIR (%)</label>
                            <input type="number" value={spwmRipple} onChange={e => setSpwmRipple(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <input type="checkbox" checked={spwmIsLcl} onChange={e => setSpwmIsLcl(e.target.checked)} className="rounded text-blue-500 bg-slate-950 border-slate-800 focus:ring-0" />
                          <label className="text-[10px] text-slate-350">Use 3rd-order LCL topology instead of single LC</label>
                        </div>
                      </div>
                    )}

                    {powerSubTab === 'bead' && (
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Bead Inductance L_bead (μH)</label>
                            <input type="number" value={beadL} onChange={e => setBeadL(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Bypass Capacitor C (μF)</label>
                            <input type="number" value={beadC} onChange={e => setBeadC(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 4. Stability & PDN inputs */}
                {activeTab === 'stability_pdn' && (
                  <div className="space-y-3.5">
                    {stabSubTab === 'stability' && (
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Input Voltage Vin (V)</label>
                            <input type="number" value={stabVin} onChange={e => setStabVin(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Load Power Pout (W)</label>
                            <input type="number" value={stabPout} onChange={e => setStabPout(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Filter Inductance L_filter (μH)</label>
                            <input type="number" value={stabL} onChange={e => setStabL(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[9px] text-slate-500">Filter Capacitance C_filter (μF)</label>
                            <input type="number" value={stabC} onChange={e => setStabC(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                          </div>
                        </div>
                      </div>
                    )}

                    {stabSubTab === 'pdn' && (
                      <div className="border border-slate-850 rounded-lg p-3 bg-slate-900/10 space-y-3">
                        <div className="flex flex-col gap-1">
                          <label className="text-[9px] text-slate-500">PDN Decoupling Mode</label>
                          <select value={pdnMode} onChange={e => setPdnMode(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none">
                            <option value="target">Target Impedance Z_target & Count Sizing</option>
                            <option value="anti">Dual Cap Parallel Anti-Resonance Response</option>
                          </select>
                        </div>

                        {pdnMode === 'target' ? (
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                              <div className="flex flex-col gap-1">
                                <label className="text-[9px] text-slate-500">Transient Step dI (A)</label>
                                <input type="number" value={pdnDi} onChange={e => setPdnDi(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                              </div>
                              <div className="flex flex-col gap-1">
                                <label className="text-[9px] text-slate-500">Max Ripple dV (mV)</label>
                                <input type="number" value={pdnDv} onChange={e => setPdnDv(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                              <div className="flex flex-col gap-1">
                                <label className="text-[9px] text-slate-500">Capacitor ESR (mΩ)</label>
                                <input type="number" value={pdnEsr} onChange={e => setPdnEsr(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                              </div>
                              <div className="flex flex-col gap-1">
                                <label className="text-[9px] text-slate-500">Capacitor ESL (nH)</label>
                                <input type="number" value={pdnEsl} onChange={e => setPdnEsl(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white focus:outline-none" />
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="border-t border-slate-800/60 pt-2 space-y-2">
                              <span className="text-[9px] font-bold text-slate-400">Capacitor C1 (Bulk Storage)</span>
                              <div className="grid grid-cols-3 gap-2">
                                <div className="flex flex-col gap-1">
                                  <label className="text-[8px] text-slate-550">C1 (μF)</label>
                                  <input type="number" value={pdnC1} onChange={e => setPdnC1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                                </div>
                                <div className="flex flex-col gap-1">
                                  <label className="text-[8px] text-slate-550">ESR1 (mΩ)</label>
                                  <input type="number" value={pdnEsr1} onChange={e => setPdnEsr1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                                </div>
                                <div className="flex flex-col gap-1">
                                  <label className="text-[8px] text-slate-550">ESL1 (nH)</label>
                                  <input type="number" value={pdnEsl1} onChange={e => setPdnEsl1(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                                </div>
                              </div>
                            </div>

                            <div className="border-t border-slate-800/60 pt-2 space-y-2">
                              <span className="text-[9px] font-bold text-slate-400">Capacitor C2 (High-Frequency Bypass)</span>
                              <div className="grid grid-cols-3 gap-2">
                                <div className="flex flex-col gap-1">
                                  <label className="text-[8px] text-slate-550">C2 (μF)</label>
                                  <input type="number" value={pdnC2} onChange={e => setPdnC2(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                                </div>
                                <div className="flex flex-col gap-1">
                                  <label className="text-[8px] text-slate-550">ESR2 (mΩ)</label>
                                  <input type="number" value={pdnEsr2} onChange={e => setPdnEsr2(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                                </div>
                                <div className="flex flex-col gap-1">
                                  <label className="text-[8px] text-slate-550">ESL2 (nH)</label>
                                  <input type="number" value={pdnEsl2} onChange={e => setPdnEsl2(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-xs text-white focus:outline-none" />
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {key === 'results' && (
              <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-6">
                <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                  <span className="text-xs font-bold text-white">Filter Topologies & Simulation Responses</span>
                </div>

                {/* Circuit equivalent schematics */}
                <Card className="bg-slate-900/40 border-slate-800/80">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-bold text-slate-350 border-l-2 border-blue-500 pl-2">
                      Equivalent Filter Schematics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex justify-center bg-slate-950/20 py-4 border-t border-slate-900/50">
                    <svg style={{ position: 'absolute', width: 0, height: 0 }}>
                      <defs>
                        <g id="pass_gnd">
                          <line x1="0" y1="0" x2="14" y2="0" stroke="#cbd5e1" strokeWidth="1.2" />
                          <line x1="2" y1="3" x2="12" y2="3" stroke="#cbd5e1" strokeWidth="1.2" />
                          <line x1="5" y1="6" x2="9" y2="6" stroke="#cbd5e1" strokeWidth="1.2" />
                        </g>
                      </defs>
                    </svg>

                    {activeTab === 'passive' && passResult && (
                      <svg width="320" height="110" viewBox="0 0 320 110" className="text-slate-350">
                        <circle cx="45" cy="55" r="2.5" fill="#10b981" />
                        <text x="40" y="52" textAnchor="end" fill="#10b981" className="text-[7px] font-mono select-none">In</text>

                        {passSubTab === 'rc' && (
                          <>
                            <line x1="45" y1="55" x2="70" y2="55" stroke="#64748b" strokeWidth="1.2" />
                            <path d="M 70,55 L 73,55 L 75,51 L 79,59 L 83,51 L 87,59 L 91,51 L 93,55 L 115,55" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                            <text x="82" y="44" textAnchor="middle" fill="#ef4444" className="text-[7px] font-mono select-none">R = {passResult.r.toFixed(1)} Ω</text>
                          </>
                        )}
                        {passSubTab === 'lc' && (
                          <>
                            <line x1="45" y1="55" x2="70" y2="55" stroke="#64748b" strokeWidth="1.2" />
                            <path d="M 70,55 Q 74,48 78,55 Q 82,48 86,55 Q 90,48 94,55 Q 98,48 102,55" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                            <line x1="102" y1="55" x2="120" y2="55" stroke="#64748b" strokeWidth="1.2" />
                            <text x="86" y="44" textAnchor="middle" fill="#ef4444" className="text-[7px] font-mono select-none">L = {passResult.l_uh.toFixed(1)} μH</text>
                          </>
                        )}
                        {passSubTab === 'rl' && (
                          <>
                            <line x1="45" y1="55" x2="70" y2="55" stroke="#64748b" strokeWidth="1.2" />
                            <path d="M 70,55 L 73,55 L 75,51 L 79,59 L 83,51 L 87,59 L 91,51 L 93,55 L 115,55" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                            <text x="82" y="44" textAnchor="middle" fill="#ef4444" className="text-[7px] font-mono select-none">R = {passResult.r.toFixed(1)} Ω</text>
                          </>
                        )}

                        <circle cx="120" cy="55" r="2" fill="#cbd5e1" />
                        <line x1="120" y1="55" x2="160" y2="55" stroke="#64748b" strokeWidth="1.2" />

                        {passSubTab === 'rc' && (
                          <>
                            <line x1="120" y1="55" x2="120" y2="70" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="110" y1="70" x2="130" y2="70" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="110" y1="74" x2="130" y2="74" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="120" y1="74" x2="120" y2="90" stroke="#64748b" strokeWidth="1.2" />
                            <use href="#pass_gnd" x="113" y="90" />
                            <text x="135" y="77" fill="#38bdf8" className="text-[7px] font-mono select-none">C = {passResult.c_uf.toFixed(3)} μF</text>
                          </>
                        )}
                        {passSubTab === 'lc' && (
                          <>
                            <line x1="120" y1="55" x2="120" y2="70" stroke="#64748b" strokeWidth="1.2" />
                            <line x1="110" y1="70" x2="130" y2="70" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="110" y1="74" x2="130" y2="74" stroke="#38bdf8" strokeWidth="1.5" />
                            <line x1="120" y1="74" x2="120" y2="90" stroke="#64748b" strokeWidth="1.2" />
                            <use href="#pass_gnd" x="113" y="90" />
                            <text x="135" y="77" fill="#38bdf8" className="text-[7px] font-mono select-none">C = {passResult.c_uf.toFixed(3)} μF</text>
                          </>
                        )}
                        {passSubTab === 'rl' && (
                          <>
                            <line x1="120" y1="55" x2="120" y2="70" stroke="#64748b" strokeWidth="1.2" />
                            <path d="M 120,70 Q 113,74 120,78 Q 113,82 120,86 Q 113,90 120,94" fill="none" stroke="#38bdf8" strokeWidth="1.2" />
                            <line x1="120" y1="94" x2="120" y2="100" stroke="#64748b" strokeWidth="1.2" />
                            <use href="#pass_gnd" x="113" y="100" />
                            <text x="132" y="85" fill="#38bdf8" className="text-[7px] font-mono select-none">L = {passResult.l_uh.toFixed(1)} μH</text>
                          </>
                        )}

                        <circle cx="160" cy="55" r="2.5" fill="#10b981" />
                        <text x="165" y="52" fill="#10b981" className="text-[7px] font-mono select-none">Out</text>
                      </svg>
                    )}

                    {activeTab === 'active' && actResult?.success && (
                      <svg width="320" height="110" viewBox="0 0 320 110" className="text-slate-350">
                        <polygon points="170,45 210,60 170,75" fill="#1e293b" stroke="#cbd5e1" strokeWidth="1.2" />
                        <text x="176" y="57" fill="#94a3b8" className="text-[7px] font-bold select-none">+</text>
                        <text x="176" y="70" fill="#94a3b8" className="text-[7px] font-bold select-none">-</text>

                        <line x1="170" y1="52" x2="150" y2="52" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="150" y1="52" x2="150" y2="60" stroke="#64748b" strokeWidth="1.2" />
                        <use href="#pass_gnd" x="143" y="60" />

                        <line x1="170" y1="67" x2="130" y2="67" stroke="#64748b" strokeWidth="1.2" />
                        <circle cx="130" cy="67" r="1.5" fill="#cbd5e1" />

                        <line x1="130" y1="67" x2="100" y2="67" stroke="#64748b" strokeWidth="1.2" />
                        <path d="M 100,67 L 97,67 L 95,63 L 91,71 L 87,63 L 83,71 L 79,63 L 77,67 L 55,67" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                        <text x="77" y="58" textAnchor="middle" fill="#ef4444" className="text-[6.5px] font-mono select-none">R1={actResult.r1 >= 1000 ? `${(actResult.r1/1000).toFixed(1)}k` : `${actResult.r1.toFixed(0)}Ω`}</text>
                        <circle cx="55" cy="67" r="2.5" fill="#10b981" />
                        <text x="50" y="64" textAnchor="end" fill="#10b981" className="text-[7px] font-mono select-none">In</text>

                        <line x1="130" y1="67" x2="130" y2="30" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="130" y1="30" x2="160" y2="30" stroke="#64748b" strokeWidth="1.2" />
                        <path d="M 160,30 L 163,30 L 165,26 L 169,34 L 173,26 L 177,34 L 181,26 L 183,30 L 210,30" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                        <text x="175" y="22" textAnchor="middle" fill="#ef4444" className="text-[6.5px] font-mono select-none">R2={actResult.r2 >= 1000 ? `${(actResult.r2/1000).toFixed(1)}k` : `${actResult.r2.toFixed(0)}Ω`}</text>
                        <line x1="210" y1="30" x2="230" y2="30" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="230" y1="30" x2="230" y2="60" stroke="#64748b" strokeWidth="1.2" />

                        <line x1="210" y1="60" x2="250" y2="60" stroke="#64748b" strokeWidth="1.2" />
                        <circle cx="230" cy="60" r="2" fill="#cbd5e1" />
                        <circle cx="250" cy="60" r="2.5" fill="#10b981" />
                        <text x="255" y="57" fill="#10b981" className="text-[7px] font-mono select-none">Out</text>

                        <line x1="130" y1="67" x2="130" y2="85" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="130" y1="85" x2="180" y2="85" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="180" y1="79" x2="180" y2="91" stroke="#38bdf8" strokeWidth="1.5" />
                        <line x1="184" y1="79" x2="184" y2="91" stroke="#38bdf8" strokeWidth="1.5" />
                        <line x1="184" y1="85" x2="230" y2="85" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="230" y1="85" x2="230" y2="60" stroke="#64748b" strokeWidth="1.2" />
                        <text x="200" y="96" textAnchor="middle" fill="#38bdf8" className="text-[6.5px] font-mono select-none">C2={(actResult.c2*1e9).toFixed(2)}nF</text>
                      </svg>
                    )}

                    {activeTab === 'power_emi' && powerSubTab === 'emi' && emiResult && (
                      <svg width="320" height="110" viewBox="0 0 320 110" className="text-slate-350">
                        <circle cx="45" cy="55" r="2.5" fill="#10b981" />
                        <text x="40" y="52" textAnchor="end" fill="#10b981" className="text-[7px] font-mono select-none">GridIn</text>

                        <line x1="45" y1="55" x2="70" y2="55" stroke="#64748b" strokeWidth="1.2" />
                        <path d="M 70,55 Q 74,48 78,55 Q 82,48 86,55 Q 90,48 94,55 Q 98,48 102,55" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                        <line x1="102" y1="55" x2="135" y2="55" stroke="#64748b" strokeWidth="1.2" />
                        <text x="86" y="44" textAnchor="middle" fill="#ef4444" className="text-[7px] font-mono select-none">L = {emiType === 'dm' ? `${emiResult.l_uh.toFixed(1)} uH` : `${emiResult.l_mh.toFixed(2)} mH`}</text>

                        <circle cx="135" cy="55" r="2" fill="#cbd5e1" />
                        <line x1="135" y1="55" x2="135" y2="70" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="125" y1="70" x2="145" y2="70" stroke="#38bdf8" strokeWidth="1.5" />
                        <line x1="125" y1="74" x2="145" y2="74" stroke="#38bdf8" strokeWidth="1.5" />
                        <line x1="135" y1="74" x2="135" y2="90" stroke="#64748b" strokeWidth="1.2" />
                        <use href="#pass_gnd" x="128" y="90" />
                        <text x="150" y="77" fill="#38bdf8" className="text-[7px] font-mono select-none">C = {emiType === 'dm' ? `${emiResult.c_uf.toFixed(3)} uF` : `${emiResult.c_nf.toFixed(2)} nF`}</text>

                        <line x1="135" y1="55" x2="200" y2="55" stroke="#64748b" strokeWidth="1.2" />
                        <circle cx="200" cy="55" r="2.5" fill="#10b981" />
                        <text x="205" y="52" fill="#10b981" className="text-[7px] font-mono select-none">PowerOut</text>
                      </svg>
                    )}

                    {activeTab === 'stability_pdn' && stabSubTab === 'stability' && stabResult && (
                      <svg width="320" height="110" viewBox="0 0 320 110" className="text-slate-350">
                        <circle cx="45" cy="55" r="2.5" fill="#10b981" />
                        <text x="40" y="52" textAnchor="end" fill="#10b981" className="text-[7px] font-mono select-none">DC_Source</text>

                        <line x1="45" y1="55" x2="70" y2="55" stroke="#64748b" strokeWidth="1.2" />
                        <path d="M 70,55 Q 74,48 78,55 Q 82,48 86,55 Q 90,48 94,55 Q 98,48 102,55" fill="none" stroke="#ef4444" strokeWidth="1.2" />
                        <line x1="102" y1="55" x2="135" y2="55" stroke="#64748b" strokeWidth="1.2" />
                        <text x="86" y="44" textAnchor="middle" fill="#ef4444" className="text-[7px] font-mono select-none">L_filter = {stabL} μH</text>

                        <circle cx="135" cy="55" r="2" fill="#cbd5e1" />
                        <line x1="135" y1="55" x2="135" y2="70" stroke="#64748b" strokeWidth="1.2" />
                        <line x1="125" y1="70" x2="145" y2="70" stroke="#38bdf8" strokeWidth="1.5" />
                        <line x1="125" y1="74" x2="145" y2="74" stroke="#38bdf8" strokeWidth="1.5" />
                        <line x1="135" y1="74" x2="135" y2="90" stroke="#64748b" strokeWidth="1.2" />
                        <use href="#pass_gnd" x="128" y="90" />
                        <text x="150" y="77" fill="#38bdf8" className="text-[7px] font-mono select-none">C_filter = {stabC} μF</text>

                        <line x1="135" y1="55" x2="200" y2="55" stroke="#64748b" strokeWidth="1.2" />
                        <rect x="200" y="40" width="40" height="30" fill="#1e293b" stroke="#e2e8f0" strokeWidth="1.2" />
                        <text x="220" y="58" textAnchor="middle" fill="#e2e8f0" className="text-[6.5px] font-bold select-none">DCDC</text>
                      </svg>
                    )}
                  </CardContent>
                </Card>

                {/* Results Metrics */}
                {activeTab === 'passive' && passResult && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-500">Cutoff Frequency fc</span>
                        <span className="text-sm font-bold text-cyan-400 font-mono">
                          {passResult.fc_hz >= 1000 ? `${(passResult.fc_hz/1000).toFixed(2)} kHz` : `${passResult.fc_hz.toFixed(1)} Hz`}
                        </span>
                      </div>
                      <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-500">Characteristic Impedance Z0</span>
                        <span className="text-sm font-bold text-cyan-400 font-mono">
                          {(passResult.z0 ?? 0.0).toFixed(1)} Ω
                        </span>
                      </div>
                      <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-500">Damping Ratio ζ</span>
                        <span className="text-sm font-bold text-cyan-400 font-mono">
                          {(passResult.damping ?? 0.0).toFixed(3)}
                        </span>
                      </div>
                    </div>

                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardContent className="pt-4 h-[400px]">
                        <ReactECharts notMerge={true} option={getBodeOption(passResult?.bode || passResult?.bode_data, passResult.fc_hz, 'Signal Filter Bode Frequency Response')} style={{ height: '100%', width: '100%' }} />
                      </CardContent>
                    </Card>
                  </div>
                )}

                {activeTab === 'active' && actResult?.success && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-4 gap-2">
                      <div className="glass-card p-2 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col">
                        <span className="text-[8px] text-slate-500">R1 Resistance</span>
                        <span className="text-xs font-bold text-cyan-400 font-mono">{(actResult.r1 ?? 0).toFixed(1)} Ω</span>
                      </div>
                      <div className="glass-card p-2 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col">
                        <span className="text-[8px] text-slate-500">R2 Resistance</span>
                        <span className="text-xs font-bold text-cyan-400 font-mono">{(actResult.r2 ?? 0).toFixed(1)} Ω</span>
                      </div>
                      <div className="glass-card p-2 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col">
                        <span className="text-[8px] text-slate-500">R3 Resistance</span>
                        <span className="text-xs font-bold text-cyan-400 font-mono">{(actResult.r3 ?? 0).toFixed(1)} Ω</span>
                      </div>
                      <div className="glass-card p-2 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col">
                        <span className="text-[8px] text-slate-500">C2 Capacitance</span>
                        <span className="text-xs font-bold text-cyan-400 font-mono">{(actResult.c2 * 1e9).toFixed(2)} nF</span>
                      </div>
                    </div>

                    <Card className="bg-slate-900/40 border-slate-800/80">
                      <CardContent className="pt-4 h-[400px]">
                        <ReactECharts notMerge={true} option={getBodeOption(actResult?.bode || actResult?.bode_data, actResult.fc_hz, 'Active Filter Bode Frequency Response')} style={{ height: '100%', width: '100%' }} />
                      </CardContent>
                    </Card>
                  </div>
                )}

                {activeTab === 'power_emi' && (
                  <div className="space-y-4">
                    {powerSubTab === 'emi' && emiResult && (
                      <>
                        <div className="grid grid-cols-3 gap-3">
                          <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500">Cutoff fc</span>
                            <span className="text-sm font-bold text-cyan-400 font-mono">{(emiResult.fc_hz / 1000).toFixed(2)} kHz</span>
                          </div>
                          <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500">Attenuation @ 150 kHz</span>
                            <span className="text-sm font-bold text-cyan-400 font-mono">{emiResult.att_150k_db.toFixed(1)} dB</span>
                          </div>
                          <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500">Attenuation @ 30 MHz</span>
                            <span className="text-sm font-bold text-cyan-400 font-mono">{emiResult.att_30m_db.toFixed(1)} dB</span>
                          </div>
                        </div>

                        <Card className="bg-slate-900/40 border-slate-800/80">
                          <CardContent className="pt-4 h-[400px]">
                            <ReactECharts notMerge={true} option={getBodeOption(emiResult?.bode || emiResult?.bode_data, emiResult.fc_hz, 'EMI Filter Attenuation Bode Sweep')} style={{ height: '100%', width: '100%' }} />
                          </CardContent>
                        </Card>
                      </>
                    )}

                    {powerSubTab === 'cmc_sat' && cmcResult && (
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-3">
                        <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-800 pb-1">Common-Mode Choke Core Saturation Check</span>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500">DM Leakage Equivalent Bm_dm</span>
                            <span className="text-sm font-bold text-cyan-400 font-mono">{cmcResult.bmax_dm_t.toFixed(4)} T</span>
                          </div>
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500">Saturation Margin Ratio</span>
                            <span className={`text-sm font-bold font-mono ${cmcResult.margin_sat_pct < 20 ? 'text-red-400 animate-pulse' : 'text-emerald-400'}`}>
                              {cmcResult.margin_sat_pct.toFixed(1)} %
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {powerSubTab === 'spwm' && spwmResult && (
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-4">
                        <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-800 pb-1">SPWM Inverter Filter Design Results</span>
                        <div className="grid grid-cols-3 gap-3">
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-500">Filter Inductance L</span>
                            <span className="text-xs font-bold text-cyan-400 font-mono">{spwmResult.l_uh.toFixed(1)} μH</span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-500">Filter Capacitance C</span>
                            <span className="text-xs font-bold text-cyan-400 font-mono">{spwmResult.c_uf.toFixed(2)} μF</span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-500">Cutoff Frequency fc</span>
                            <span className="text-xs font-bold text-cyan-400 font-mono">{spwmResult.fc_hz.toFixed(0)} Hz</span>
                          </div>
                        </div>

                        {spwmIsLcl && spwmResult.lcl_design && (
                          <div className="mt-2 border-t border-slate-800/80 pt-2 space-y-2">
                            <span className="text-[9px] font-semibold text-slate-400 block">LCL Topology Grid-Side Parameters</span>
                            <div className="grid grid-cols-3 gap-2 text-[10px]">
                              <div>Grid Inductance L2: <span className="text-green-400 font-mono">{(spwmResult.lcl_design.l2_uh ?? 0.0).toFixed(1)} μH</span></div>
                              <div>Damping Resistor Rd: <span className="text-green-400 font-mono">{(spwmResult.lcl_design.rd_ohm ?? 0.0).toFixed(2)} Ω</span></div>
                              <div>Damping Dissipation Pd: <span className="text-green-400 font-mono">{(spwmResult.lcl_design.rd_loss_w ?? 0.0).toFixed(2)} W</span></div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {powerSubTab === 'bead' && beadResult && (
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-2">
                        <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-800 pb-1">Ferrite Bead Damping Parameters</span>
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          <div>Resonant Frequency fr: <span className="text-cyan-400 font-mono">{(beadResult.fr_mhz ?? 0.0).toFixed(2)} MHz</span></div>
                          <div>Max Quality Factor Qm: <span className="text-cyan-400 font-mono">{(beadResult.q ?? 0.0).toFixed(3)}</span></div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'stability_pdn' && (
                  <div className="space-y-4">
                    {stabSubTab === 'stability' && stabResult && (
                      <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-4">
                        <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-800 pb-1">Middlebrook Input Impedance Stability Check</span>
                        <div className="grid grid-cols-3 gap-3">
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-500">Filter Output Impedance Zo_max</span>
                            <span className="text-xs font-bold text-cyan-400 font-mono">{stabResult.zo_max_ohm.toFixed(3)} Ω</span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-500">Converter Input Impedance |Zin|</span>
                            <span className="text-xs font-bold text-cyan-400 font-mono">{stabResult.zin_neg_ohm.toFixed(2)} Ω</span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[9px] text-slate-500">Stability Verdict</span>
                            <span className={`text-xs font-bold font-mono ${stabResult.stable ? 'text-emerald-400' : 'text-red-400 animate-pulse'}`}>
                              {stabResult.stable ? 'Pass (Zo < Zin)' : 'Warning (Oscillation Risk)'}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {stabSubTab === 'pdn' && (
                      <>
                        {pdnMode === 'target' && pdnTgtZ !== null && pdnCapNumResult && (
                          <div className="border border-slate-800 rounded-lg p-3 bg-slate-900/20 space-y-4">
                            <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-800 pb-1">Decoupling Capacitor Count Sizing</span>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="flex flex-col">
                                <span className="text-[9px] text-slate-500">Target Impedance Z_target</span>
                                <span className="text-sm font-bold text-cyan-400 font-mono">{pdnTgtZ.toFixed(2)} mΩ</span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-[9px] text-slate-500">Min Required Capacitors N</span>
                                <span className="text-sm font-bold text-cyan-400 font-mono">{pdnCapNumResult.n_req} pcs</span>
                              </div>
                            </div>
                          </div>
                        )}

                        {pdnMode === 'anti' && pdnResult && (
                          <>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[9px] text-slate-500">Anti-Resonance Frequency fp</span>
                                <span className="text-sm font-bold text-cyan-400 font-mono">{(pdnResult.f_peak_mhz).toFixed(2)} MHz</span>
                              </div>
                              <div className="glass-card p-3 rounded-lg border border-slate-800 bg-slate-900/20 flex flex-col gap-0.5">
                                <span className="text-[9px] text-slate-500">Anti-Resonance Peak Impedance Zp</span>
                                <span className="text-sm font-bold text-red-400 font-mono">{(pdnResult.z_peak_ohm).toFixed(3)} Ω</span>
                              </div>
                            </div>

                            <Card className="bg-slate-900/40 border-slate-800/80">
                              <CardContent className="pt-4 h-[400px]">
                                <ReactECharts notMerge={true} option={getPdnBodeOption(pdnResult?.bode || pdnResult?.bode_data, pdnResult.f_peak_mhz, pdnResult.z_peak_ohm)} style={{ height: '100%', width: '100%' }} />
                              </CardContent>
                            </Card>
                          </>
                        )}
                      </>
                    )}
                  </div>
                )}

                {/* E-series standard matches BOM */}
                {bomList.length > 0 && (
                  <Card className="bg-slate-900/40 border-slate-800/80">
                    <CardHeader className="pb-1">
                      <CardTitle className="text-xs font-bold text-slate-350 border-l-2 border-blue-500 pl-2">
                        Recommended Commercial E24 / E96 Standard Values
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse text-[11px] text-slate-350">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-500">
                              <th className="py-1">Designator</th>
                              <th className="py-1">Calculated</th>
                              <th className="py-1">Standard Nom</th>
                              <th className="py-1 text-right">Deviation</th>
                              <th className="py-1">Description</th>
                            </tr>
                          </thead>
                          <tbody>
                            {bomList.map((item, idx) => (
                              <tr key={idx} className="border-b border-slate-850 hover:bg-slate-900/30 transition-colors">
                                <td className="py-1.5 font-bold text-cyan-400">{item.designator}</td>
                                <td className="py-1.5 font-mono">{item.calcValue}</td>
                                <td className="py-1.5 font-mono text-green-400 font-semibold">{item.stdValue}</td>
                                <td className="py-1.5 text-right font-mono text-pink-400">{item.error}</td>
                                <td className="py-1.5 text-[10px] text-slate-400">{item.desc}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}
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