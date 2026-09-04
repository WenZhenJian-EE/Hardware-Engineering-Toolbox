import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import { apiFetch } from '../lib/api';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import {
  ArrowLeft,
  Sparkles,
  RefreshCw,
  ShoppingBag,
  LineChart,
  HelpCircle
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

  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-xs text-slate-350" : "inline-block text-xs text-slate-355"} />;
};

interface EmcToolboxPanelProps {
  onBack: () => void;
  setActiveModule?: any;
}

export default function EmcToolboxPanel({ onBack, setActiveModule }: EmcToolboxPanelProps) {
  const [activeTab, setActiveTab] = useTabHistoryState<'conducted' | 'radiated'>('conducted', 'activeTab');
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showGuide, setShowGuide] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [drcWarnings, setDrcWarnings] = useState<string[]>([]);

  // 1. Conducted EMI & Filter Synthesis State
  const [standardsDb, setStandardsDb] = useState<any>({});
  const [limitList, setLimitList] = useState<string[]>([]);
  
  const [fixStd, setFixStd] = useState<string>('');
  const [fixFreq, setFixFreq] = useState<number>(0.15); // MHz
  const [fixMeas, setFixMeas] = useState<number>(76.0); // dBuV
  const [fixMargin, setFixMargin] = useState<number>(6.0); // dB
  const [fixCmPct, setFixCmPct] = useState<number>(60.0); // %
  const [fixVline, setFixVline] = useState<number>(220.0); // Vrms
  const [fixFline, setFixFline] = useState<number>(50.0); // Hz
  const [fixIleak, setFixIleak] = useState<number>(0.5); // mA
  const [fixCx, setFixCx] = useState<number>(0.22); // uF
  const [fixKleak, setFixKleak] = useState<number>(1.0); // %
  
  const [conductedRes, setConductedRes] = useState<any>(null);
  const [bodeData, setBodeData] = useState<any>(null);
  const [sweepMode, setSweepMode] = useState<'cm' | 'dm'>('cm');

  // Engineering unit conversion state
  const [convMode, setConvMode] = useState<string>('dbuv');
  const [convVal, setConvVal] = useState<number>(60.0);
  const [convResult, setConvResult] = useState<any>(null);

  // 2. Radiated EMI & Shielding State
  const [radFreq, setRadFreq] = useState<number>(100.0); // MHz
  const [vrx, setVrx] = useState<number>(30.0); // dBuV
  const [antennaFactor, setAntennaFactor] = useState<number>(10.0); // dB/m
  const [cableLoss, setCableLoss] = useState<number>(2.5); // dB
  const [ampGain, setAmpGain] = useState<number>(0.0); // dB
  const [shieldMaterial, setShieldMaterial] = useState<'copper' | 'aluminum' | 'iron' | 'stainless_steel'>('aluminum');
  const [shieldThickness, setShieldThickness] = useState<number>(1.0); // mm
  const [gapLength, setGapLength] = useState<number>(15.0); // mm
  const [gapWidth, setGapWidth] = useState<number>(1.5); // mm
  const [gapCount, setGapCount] = useState<number>(2);

  const [radRes, setRadRes] = useState<any>(null);

  const conductedLayout = useDragDeckLayout({
    panelKey: 'layout_emctoolbox_conducted_v6',
    defaultCards: ['input_conducted', 'result_conducted', 'schematic_conducted', 'chart_conducted'],
    defaultColumns: { input_conducted: 'left', result_conducted: 'right', schematic_conducted: 'left', chart_conducted: 'right' },
    defaultSpans: { input_conducted: 4, result_conducted: 8, schematic_conducted: 4, chart_conducted: 8 },
    defaultHeights: { input_conducted: 670, result_conducted: 350, schematic_conducted: 240, chart_conducted: 490 }
  });

  const radiatedLayout = useDragDeckLayout({
    panelKey: 'layout_emctoolbox_radiated_v6',
    defaultCards: ['input_radiated', 'result_radiated', 'schematic_radiated'],
    defaultColumns: { input_radiated: 'left', result_radiated: 'right', schematic_radiated: 'right' },
    defaultSpans: { input_radiated: 4, result_radiated: 8, schematic_radiated: 8 },
    defaultHeights: { input_radiated: 540, result_radiated: 230, schematic_radiated: 400 }
  });

  useEffect(() => {
    const fetchStandards = async () => {
      try {
        const res = await apiFetch('/api/calculate/emc_toolbox/standards');
        if (!res.ok) {
          const errDetail = await res.json().catch(() => ({}));
          throw new Error(errDetail.detail || 'Failed to fetch standards');
        }
        const data = await res.json();
        setStandardsDb(data);
        const keys = Object.keys(data).filter(k => data[k].type === 'Conducted');
        setLimitList(keys);
        if (keys.length > 0) {
          setFixStd(keys[0]);
        }
      } catch (err: any) {
        setError(err.message);
      }
    };
    fetchStandards();
  }, []);

  useEffect(() => {
    try {
      const savedState = localStorage.getItem('project_state');
      if (savedState) {
        const state = JSON.parse(savedState);
        if (state.emi_jump_flag) {
          setActiveTab('conducted');
          if (state.ind_fsw_khz) {
            setFixFreq(parseFloat((state.ind_fsw_khz / 1000).toFixed(3)));
          }
          state.emi_jump_flag = false;
          localStorage.setItem('project_state', JSON.stringify(state));
        }
      }
    } catch (e: any) {
      setError(e.message);
    }
  }, [activeTab]);

  const handleConversion = async () => {
    try {
      const res = await apiFetch('/api/calculate/emc_toolbox/conversion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ val: convVal, mode: convMode })
      });
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Conversion failed');
      }
      if (activeTabRef.current !== activeTab) return;
      const data = await res.json();
      setConvResult(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const calculateConducted = async () => {
    if (!fixStd) return;
    setLoading(true);
    setErrorMsg('');
    setDrcWarnings([]);
    try {
      const fixRes = await apiFetch('/api/calculate/emc_toolbox/conducted_fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          std_key: fixStd,
          freq_mhz: fixFreq,
          measured_dbuv: fixMeas,
          margin_db: fixMargin,
          cm_share_pct: fixCmPct,
          v_line: fixVline,
          f_line: fixFline,
          i_leak_ma: fixIleak,
          cx_uf: fixCx,
          k_leak_pct: fixKleak
        })
      });
      if (activeTabRef.current !== 'conducted') return;
      if (!fixRes.ok) {
        const err = await fixRes.json();
        throw new Error(err.detail || "Conducted filter synthesis failed");
      }
      const fixData = await fixRes.json();
      setConductedRes(fixData);
      setDrcWarnings(fixData.drc_warnings || []);

      try {
        const savedState = localStorage.getItem('project_state');
        if (savedState) {
          const state = JSON.parse(savedState);
          state.emi_l_cm_recommend = fixData.lcm_mh;
          state.emi_c_y_recommend = fixData.cy_nf;
          state.emi_l_dm_recommend = fixData.ldm_add_uh;
          localStorage.setItem('project_state', JSON.stringify(state));
        }
      } catch (e) {}

      const lcm = fixData.lcm_mh;
      const cy = fixData.cy_nf;
      const ldm = fixData.ldm_uh;
      const cx = fixCx;
      const rdamp = fixData.r_damp_ohm;
      const cdamp = fixData.c_damp_uf;

      const [bodeCmRes, bodeDmRes] = await Promise.all([
        apiFetch('/api/calculate/emc_toolbox/filter_bode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ l_val: lcm, c_val: cy, r_damp: rdamp, c_damp: cdamp, is_cm: true })
        }),
        apiFetch('/api/calculate/emc_toolbox/filter_bode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ l_val: ldm, c_val: cx, r_damp: rdamp, c_damp: cdamp, is_cm: false })
        })
      ]);

      if (!bodeCmRes.ok) {
        const err = await bodeCmRes.json().catch(() => ({}));
        throw new Error(err.detail || "CM filter frequency sweep failed");
      }
      if (!bodeDmRes.ok) {
        const err = await bodeDmRes.json().catch(() => ({}));
        throw new Error(err.detail || "DM filter frequency sweep failed");
      }
      if (activeTabRef.current !== 'conducted') return;
      const cmBode = await bodeCmRes.json();
      const dmBode = await bodeDmRes.json();
      setBodeData({ cm: cmBode, dm: dmBode });
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const calculateRadiated = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/calculate/emc_toolbox/radiated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          f_mhz: radFreq,
          v_rx_dbuv: vrx,
          af_db_m: antennaFactor,
          cable_loss_db: cableLoss,
          amp_gain_db: ampGain
        })
      });
      if (activeTabRef.current !== 'radiated') return;
      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({}));
        throw new Error(errDetail.detail || "Radiated physical value calculation failed");
      }
      const data = await res.json();

      const lam = 300.0 / radFreq;
      const gap_l_m = gapLength / 1000.0;
      
      const rs = gap_l_m > 0 ? Math.max(0.0, 20.0 * Math.log10(lam / (2.0 * gap_l_m))) : 100.0;
      const as = gapWidth > 0 ? 27.3 * (shieldThickness / gapWidth) : 100.0;
      const penalty = gapCount > 0 ? 10.0 * Math.log10(gapCount) : 0.0;
      const se = Math.max(0.0, rs + as - penalty);

      setRadRes({
        wavelength_m: data.wavelength_m,
        safe_gap_mm: data.safe_gap_mm,
        field_strength_dbuv_m: data.field_strength_dbuv_m,
        rs_db: rs,
        as_db: as,
        se_db: se
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Calculation error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'conducted' && fixStd) {
      calculateConducted();
    }
  }, [fixStd, fixFreq, fixMeas, fixMargin, fixCmPct, fixVline, fixFline, fixIleak, fixCx, fixKleak, activeTab]);

  useEffect(() => {
    if (activeTab === 'radiated') {
      calculateRadiated();
    }
  }, [radFreq, vrx, antennaFactor, cableLoss, ampGain, shieldMaterial, shieldThickness, gapLength, gapWidth, gapCount, activeTab]);

  useEffect(() => {
    handleConversion();
  }, [convVal, convMode]);

  const handleResetLayout = () => {
    if (activeTab === 'conducted') {
      conductedLayout.handleResetLayout();
    } else {
      radiatedLayout.handleResetLayout();
    }
  };

  const getBodeChartOption = () => {
    if (!bodeData) return {};
    const data = sweepMode === 'cm' ? bodeData.cm : bodeData.dm;

    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        extraCssText: 'backdrop-filter: blur(8px);',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#334155',
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        formatter: (params: any) => {
          const f = params[0].value[0];
          let fStr = f >= 1e6 ? `${(f / 1e6).toFixed(2)} MHz` : `${(f / 1e3).toFixed(1)} kHz`;
          let html = `Frequency: <span class="font-bold text-white">${fStr}</span><br/>`;
          params.forEach((p: any) => {
            html += `${p.seriesName}: <span class="font-bold font-mono" style="color:${p.color}">${p.value[1].toFixed(2)} dB</span><br/>`;
          });
          return html;
        }
      },
      legend: {
        data: ['Undamped Insertion Loss', 'RC Damped Insertion Loss'],
        textStyle: { color: '#94a3b8', fontSize: 10 },
        bottom: 0
      },
      grid: { left: '10%', right: '10%', bottom: '15%', top: '10%', containLabel: true },
      xAxis: {
        type: 'log',
        name: 'Frequency (Hz)',
        nameTextStyle: { color: '#64748b', fontSize: 9 },
        nameLocation: 'middle',
        nameGap: 18,
        min: 10000,
        max: 30000000,
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: {
          color: '#94a3b8',
          fontSize: 9,
          formatter: (value: number) => {
            if (value === 10000) return '10kHz';
            if (value === 100000) return '100kHz';
            if (value === 150000) return '150kHz';
            if (value === 1000000) return '1MHz';
            if (value === 10000000) return '10MHz';
            if (value === 30000000) return '30MHz';
            return '';
          }
        },
        splitLine: { show: true, lineStyle: { type: 'dashed', color: 'rgba(255, 255, 255, 0.05)' } }
      },
      yAxis: {
        type: 'value',
        name: 'Attenuation IL (dB)',
        nameTextStyle: { color: '#64748b', fontSize: 9 },
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { show: true, lineStyle: { type: 'dashed', color: 'rgba(255, 255, 255, 0.05)' } }
      },
      series: [
        {
          name: 'Undamped Insertion Loss',
          type: 'line',
          data: data.freqs.map((f: number, i: number) => [f, data.il_undamped[i]]),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 3, color: '#f43f5e', shadowBlur: 6, shadowColor: 'rgba(244,63,94,0.4)' }
        },
        {
          name: 'RC Damped Insertion Loss',
          type: 'line',
          data: data.freqs.map((f: number, i: number) => [f, data.il_damped[i]]),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 3, color: '#10b981', shadowBlur: 6, shadowColor: 'rgba(16,185,129,0.4)' }
        }
      ]
    };
  };

  const getShieldBodeChartOption = () => {
    if (!radRes) return {};
    const f_arr = Array.from({ length: 50 }, (_, i) => 30.0 + i * 20.0);
    const lam_arr = f_arr.map(f => 300.0 / f);
    
    const gap_l_m = gapLength / 1000.0;
    const penalty = gapCount > 0 ? 10.0 * Math.log10(gapCount) : 0.0;
    
    const se_data = f_arr.map((f, i) => {
      const l = lam_arr[i];
      const rs = gap_l_m > 0 ? Math.max(0.0, 20.0 * Math.log10(l / (2.0 * gap_l_m))) : 100.0;
      const as = gapLength > 0 ? 27.3 * (shieldThickness / gapLength) : 100.0;
      return [f, Math.max(0.0, rs + as - penalty)];
    });

    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        extraCssText: 'backdrop-filter: blur(8px);',
        backgroundColor: 'rgba(15, 23, 42, 0.85)',
        borderColor: '#334155',
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 11 },
        formatter: (params: any) => {
          return `Frequency: <span class="font-bold text-white">${params[0].value[0].toFixed(0)} MHz</span><br/>` +
                 `Shielding Effectiveness SE: <span class="font-bold text-pink-400 font-mono">${params[0].value[1].toFixed(1)} dB</span>`;
        }
      },
      grid: { left: '10%', right: '10%', bottom: '15%', top: '10%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Frequency (MHz)',
        nameTextStyle: { color: '#64748b', fontSize: 9 },
        nameLocation: 'middle',
        nameGap: 18,
        min: 30,
        max: 1000,
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { show: true, lineStyle: { type: 'dashed', color: 'rgba(255, 255, 255, 0.05)' } }
      },
      yAxis: {
        type: 'value',
        name: 'Shielding Effectiveness SE (dB)',
        nameTextStyle: { color: '#64748b', fontSize: 9 },
        axisLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { show: true, lineStyle: { type: 'dashed', color: 'rgba(255, 255, 255, 0.05)' } }
      },
      series: [
        {
          name: 'Shielding Effectiveness',
          type: 'line',
          data: se_data,
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 3, color: '#ec4899', shadowBlur: 6, shadowColor: 'rgba(236,72,153,0.4)' },
          markPoint: {
            data: [
              {
                coord: [radFreq, radRes.se_db],
                value: 'Design Point',
                label: { formatter: `Design Point: ${radRes.se_db.toFixed(1)}dB`, color: '#f472b6', fontSize: 9, position: 'top' },
                itemStyle: { color: '#db2777' }
              }
            ]
          }
        }
      ]
    };
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden text-slate-100 bg-[#070a13] p-4 pb-0 gap-4">
      {/* Top Header */}
      <div className="flex-shrink-0 flex justify-between items-center gap-4 py-2 border-b border-slate-900 pb-3">
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
            <h1 className="text-base font-bold text-white tracking-tight">EMC Filter & Damping Network Design</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Convert EMC units, synthesize CM/DM filter attenuation, size RC damping networks, and evaluate enclosure shielding effectiveness.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button size="sm" variant="outline" className="h-8 text-xs border-slate-800 hover:bg-slate-900 text-slate-400" onClick={handleResetLayout}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Reset Layout
          </Button>
          <button
            onClick={() => setShowGuide(!showGuide)}
            className="bg-purple-600/90 hover:bg-purple-600 text-white font-medium text-xs px-3.5 py-1.5 rounded-lg border-0 cursor-pointer transition-all shrink-0"
          >
            EMC Filter Design Guide
          </button>
        </div>
      </div>

      {showGuide && (
        <div className="flex-shrink-0 bg-purple-900/40 border border-purple-500/50 p-4 rounded-lg mt-2 text-purple-200 text-xs leading-relaxed relative">
          <button onClick={() => setShowGuide(false)} className="absolute top-2 right-2 text-purple-400 hover:text-white cursor-pointer bg-transparent border-0 font-bold">×</button>
          <h3 className="font-bold mb-2 text-purple-100">EMC Design Practical Guidelines</h3>
          <ul className="list-decimal pl-5 space-y-1">
            <li>150kHz~500kHz conducted emissions are typically dominated by Differential Mode (DM) noise; size large X capacitors and DM chokes.</li>
            <li>5MHz~30MHz emissions are predominantly Common Mode (CM) noise; size Y capacitors and high-inductance CM chokes.</li>
            <li>Parallel RC damping networks effectively suppress low-pass filter resonance peaks at cutoff, preventing unintended EMI amplification.</li>
            <li>Enclosure apertures and slot seam diagonals must be kept below lambda / 20 to prevent radiation leakage.</li>
          </ul>
        </div>
      )}

      {/* Tabs */}
      <div className="flex-shrink-0 flex bg-[#0c101d] border border-slate-800 p-1.5 rounded-lg">
        <button
          onClick={() => setActiveTab('conducted')}
          className={`flex-1 border-0 cursor-pointer text-xs font-semibold py-2 px-4 rounded-md transition-all ${activeTab === 'conducted' ? 'bg-purple-600 text-white font-bold' : 'bg-transparent text-slate-400 hover:text-slate-200'}`}
        >
          Conducted EMI & Filter Synthesis
        </button>
        <button
          onClick={() => setActiveTab('radiated')}
          className={`flex-1 border-0 cursor-pointer text-xs font-semibold py-2 px-4 rounded-md transition-all ${activeTab === 'radiated' ? 'bg-purple-600 text-white font-bold' : 'bg-transparent text-slate-400 hover:text-slate-200'}`}
        >
          Radiated EMI & Enclosure Shielding Effectiveness
        </button>
      </div>

      {/* Warnings & Errors */}
      {errorMsg && (
        <div className="flex-shrink-0 bg-rose-950/40 border border-rose-800/80 p-3 rounded-lg text-rose-450 font-mono text-xs">
          ❌ Calculation Error: {errorMsg}
        </div>
      )}

      {drcWarnings.length > 0 && (
        <div className="flex-shrink-0 bg-amber-950/20 border border-amber-800/60 p-3 rounded-lg space-y-1">
          <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">⚠️ EMC Safety Design & DRC Verification Warnings</span>
          <div className="space-y-1 text-[10px] text-amber-300/90 font-mono leading-normal">
            {drcWarnings.map((warn, i) => <div key={i}>• {warn}</div>)}
          </div>
        </div>
      )}

      {/* Main DragDeck Area */}
      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin p-3 pt-0 pb-12 min-h-0">
        {activeTab === 'conducted' ? (
          <DragDeck
            isDesktop={conductedLayout.isDesktop}
            leftSpan={conductedLayout.leftSpan}
            rightSpan={conductedLayout.rightSpan}
            leftCards={conductedLayout.leftCards}
            rightCards={conductedLayout.rightCards}
            draggedKey={conductedLayout.draggedKey}
            renderCard={(key) => {
              switch (key) {
                case 'input_conducted':
                  return (
                    <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
                      <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
                        <span className="text-xs font-bold text-white">Operating Conditions & Safety Leakage Limits</span>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
                        <div className="border border-slate-800/80 rounded-lg p-3 bg-slate-900/10 space-y-3">
                          <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Standard Limits & Measured Noise</span>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Standard Limit Profile</label>
                              <select value={fixStd} onChange={e => setFixStd(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none cursor-pointer">
                                {limitList.map(std => <option key={std} value={std}>{std}</option>)}
                              </select>
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Peak Noise Frequency (MHz)</label>
                              <input type="number" value={fixFreq} step={0.01} onChange={e => setFixFreq(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Measured Noise (dBµV)</label>
                              <input type="number" value={fixMeas} onChange={e => setFixMeas(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Target Design Margin (dB)</label>
                              <input type="number" value={fixMargin} onChange={e => setFixMargin(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                          </div>
                        </div>

                        <div className="border border-slate-800/80 rounded-lg p-3 bg-slate-900/10 space-y-3">
                          <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Safety Leakage & Filter Parameters</span>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Common Mode Share CM (%)</label>
                              <input type="number" value={fixCmPct} onChange={e => setFixCmPct(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Allowable Leakage Current (mA)</label>
                              <input type="number" value={fixIleak} onChange={e => setFixIleak(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Mains Voltage (Vrms)</label>
                              <input type="number" value={fixVline} onChange={e => setFixVline(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Mains Frequency (Hz)</label>
                              <input type="number" value={fixFline} onChange={e => setFixFline(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Preset X Capacitance (uF)</label>
                              <input type="number" value={fixCx} onChange={e => setFixCx(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Choke Leakage Inductance Ratio (%)</label>
                              <input type="number" value={fixKleak} onChange={e => setFixKleak(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                          </div>
                        </div>

                        {/* Conversion widget */}
                        <div className="border-t border-slate-850 pt-3.5 space-y-2.5">
                          <div className="flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                            <span className="text-[10px] font-bold text-white uppercase tracking-wide">EMC Engineering Unit Converter</span>
                          </div>
                          <div className="grid grid-cols-3 gap-2">
                            <div className="flex flex-col gap-0.5">
                              <label className="text-[8px] text-slate-500">Input Value</label>
                              <input type="number" value={convVal} onChange={e => setConvVal(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-0.5">
                              <label className="text-[8px] text-slate-500">Source Unit</label>
                              <select value={convMode} onChange={e => setConvMode(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1 text-[10px] text-white outline-none cursor-pointer">
                                <option value="dbuv">dBµV</option>
                                <option value="mv">mV</option>
                                <option value="dbm">dBm</option>
                                <option value="dbua">dBµA</option>
                              </select>
                            </div>
                            <div className="flex flex-col gap-0.5 justify-end">
                              <Button size="sm" onClick={handleConversion} className="bg-purple-900/40 hover:bg-purple-800 border border-purple-800/60 text-purple-300 text-[9px] py-1 h-[24px] cursor-pointer">
                                Convert
                              </Button>
                            </div>
                          </div>
                          {convResult && (
                            <div className="grid grid-cols-2 gap-2 text-[9px] font-mono bg-slate-950/60 p-2.5 border border-slate-850 rounded-lg">
                              <div className="flex justify-between">
                                <span className="text-slate-500">Level:</span>
                                <span className="text-cyan-400 font-bold">{(convResult?.dbuv ?? 0).toFixed(1)} dBµV</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-500">Linear Voltage:</span>
                                <span className="text-slate-300">{(convResult?.mv ?? 0).toFixed(3)} mV</span>
                              </div>
                              <div className="flex justify-between col-span-2 border-t border-slate-900 pt-1.5 mt-1">
                                <span className="text-slate-500">Export to Noise Input:</span>
                                <button
                                  onClick={() => {
                                    setFixMeas(parseFloat((convResult?.dbuv ?? 0).toFixed(1)));
                                  }}
                                  className="bg-purple-600/30 hover:bg-purple-600/50 text-purple-300 border-0 px-2 py-0.5 rounded cursor-pointer text-[8px] transition-colors"
                                >
                                  Import
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  );
                case 'result_conducted':
                  return (
                    <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
                      <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
                        <span className="text-xs font-bold text-white">Conducted Filter & Damping Network Synthesis Specifications</span>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
                        {conductedRes ? (
                          <div className="space-y-4 text-xs">
                            <div className="grid grid-cols-4 gap-3">
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm text-center">
                                <span className="block text-[8px] font-bold text-slate-500 uppercase">Standard Limit:</span>
                                <span className="text-xs font-extrabold text-slate-200 font-mono">{(conductedRes.limit ?? 0).toFixed(1)} dBµV</span>
                              </div>
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm text-center">
                                <span className="block text-[8px] font-bold text-slate-500 uppercase">Over Limit:</span>
                                <span className={`text-xs font-extrabold font-mono ${conductedRes.over > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                                  {(conductedRes.over ?? 0).toFixed(1)} dB
                                </span>
                              </div>
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm text-center">
                                <span className="block text-[8px] font-bold text-slate-500 uppercase">CM Required Attenuation:</span>
                                <span className="text-xs font-extrabold text-cyan-400 font-mono">{(conductedRes.cm_att ?? 0).toFixed(1)} dB</span>
                              </div>
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm text-center">
                                <span className="block text-[8px] font-bold text-slate-500 uppercase">DM Required Attenuation:</span>
                                <span className="text-xs font-extrabold text-amber-400 font-mono">{(conductedRes.dm_att ?? 0).toFixed(1)} dB</span>
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-850 space-y-2">
                                <span className="text-cyan-400 font-bold block mb-1 text-[10px]">[Common Mode Y Filtering]</span>
                                <div className="space-y-1 font-mono text-[10px]">
                                  <div className="flex justify-between">
                                    <span>Max Y Capacitance (Cy_max):</span>
                                    <span className="text-slate-400">{((conductedRes.cy_nf ?? 0) * 1.2).toFixed(2)} nF</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Recommended Y Capacitance (Cy):</span>
                                    <span className="text-cyan-300 font-bold">{(conductedRes.cy_nf ?? 0).toFixed(2)} nF</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Min Common Mode Inductance (LCM):</span>
                                    <span className="text-cyan-300 font-bold">{(conductedRes.lcm_mh ?? 0).toFixed(2)} mH</span>
                                  </div>
                                </div>
                              </div>

                              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-850 space-y-2">
                                <span className="text-amber-400 font-bold block mb-1 text-[10px]">[Differential Mode X Filtering & Damping]</span>
                                <div className="space-y-1 font-mono text-[10px]">
                                  <div className="flex justify-between">
                                    <span>X Capacitance (Cx):</span>
                                    <span className="text-slate-400">{fixCx.toFixed(2)} uF</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Added Differential Inductance (Ldm):</span>
                                    <span className="text-amber-300 font-bold">{(conductedRes.ldm_add_uh ?? 0).toFixed(1)} uH</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Damping Resistance (Rdamp):</span>
                                    <span className="text-green-400 font-bold">{(conductedRes.r_damp_ohm ?? 0).toFixed(1)} Ω</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Damping Capacitance (Cdamp):</span>
                                    <span className="text-green-400 font-bold">{(conductedRes.c_damp_uf ?? 0).toFixed(2)} uF</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="bg-[#0c101e]/60 border border-slate-855 rounded-lg p-3 space-y-1.5">
                              <span className="text-[10px] font-bold text-purple-400 block">💡 Conducted Choke & Resonance Damping Rationale</span>
                              <p className="text-[10px] text-slate-400 leading-normal font-sans">
                                Second-order LC low-pass filters exhibit significant resonant peaking near their corner frequency if undamped.
                                A parallel RC damping network placed across the X capacitor, configured with <Latex math="C_d = 3 \cdot C_x" /> and <Latex math="R_d = \sqrt{L_{dm}/C_x}" />, effectively attenuates resonance peaking to <Latex math="\le 3\text{ dB}" />.
                              </p>
                            </div>
                          </div>
                        ) : (
                          <div className="h-48 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                            Enter operating parameters to automatically generate filter specifications.
                          </div>
                        )}
                      </div>
                    </Card>
                  );
                case 'schematic_conducted':
                  return (
                    <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
                      <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
                        <ShoppingBag className="w-4 h-4 text-purple-400" />
                        <span className="text-xs font-bold text-white">Composite EMI Filter & Damping Circuit Topology</span>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 flex flex-col justify-center">
                        <svg className="w-full h-36 text-slate-400 select-none" viewBox="0 0 500 130">
                          <defs>
                            <linearGradient id="flowCM" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stopColor="#22d3ee" stopOpacity="0" />
                              <stop offset="50%" stopColor="#22d3ee" stopOpacity="1" />
                              <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
                            </linearGradient>
                          </defs>

                          <path d="M 20 30 L 80 30 M 20 90 L 80 90" stroke="#475569" strokeWidth="2" fill="none" />
                          
                          <rect x="80" y="22" width="8" height="76" fill="rgba(168, 85, 247, 0.15)" stroke="#a855f7" strokeWidth="1.5" />
                          <text x="84" y="60" fill="#a855f7" fontSize="8" textAnchor="middle" transform="rotate(-90 84 60)">Cx</text>
                          <line x1="84" y1="30" x2="84" y2="22" stroke="#475569" strokeWidth="1.5" />
                          <line x1="84" y1="98" x2="84" y2="90" stroke="#475569" strokeWidth="1.5" />

                          <line x1="120" y1="30" x2="120" y2="40" stroke="#475569" strokeWidth="1.5" />
                          <rect x="115" y="40" width="10" height="15" fill="#0f172a" stroke="#10b981" strokeWidth="1.5" />
                          <text x="126" y="50" fill="#10b981" fontSize="7" fontWeight="bold">Rd</text>
                          <line x1="120" y1="55" x2="120" y2="65" stroke="#475569" strokeWidth="1.5" />
                          <rect x="115" y="65" width="10" height="4" fill="rgba(16,185,129,0.2)" stroke="#10b981" strokeWidth="1.5" />
                          <rect x="115" y="71" width="10" height="4" fill="rgba(16,185,129,0.2)" stroke="#10b981" strokeWidth="1.5" />
                          <text x="126" y="73" fill="#10b981" fontSize="7" fontWeight="bold">Cd</text>
                          <line x1="120" y1="75" x2="120" y2="90" stroke="#475569" strokeWidth="1.5" />

                          <path d="M 84 30 L 170 30 M 84 90 L 170 90" stroke="#475569" strokeWidth="2" fill="none" />

                          <circle cx="190" cy="30" r="14" fill="none" stroke="#22d3ee" strokeWidth="2" strokeDasharray="3,3" />
                          <circle cx="190" cy="90" r="14" fill="none" stroke="#22d3ee" strokeWidth="2" strokeDasharray="3,3" />
                          <rect x="183" y="44" width="14" height="32" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
                          <text x="190" y="62" fill="#22d3ee" fontSize="8" textAnchor="middle" fontWeight="bold">LCM</text>
                          <line x1="170" y1="30" x2="176" y2="30" stroke="#475569" strokeWidth="2" />
                          <line x1="204" y1="30" x2="230" y2="30" stroke="#475569" strokeWidth="2" />
                          <line x1="170" y1="90" x2="176" y2="90" stroke="#475569" strokeWidth="2" />
                          <line x1="204" y1="90" x2="230" y2="90" stroke="#475569" strokeWidth="2" />

                          <path d="M 230 30 L 240 30 Q 244 22, 248 30 Q 252 22, 256 30 Q 260 22, 264 30 L 280 30" stroke="#eab308" strokeWidth="2" fill="none" />
                          <text x="252" y="16" fill="#eab308" fontSize="7" textAnchor="middle">Ldm_add</text>
                          <line x1="230" y1="90" x2="280" y2="90" stroke="#475569" strokeWidth="2" />

                          <line x1="280" y1="30" x2="330" y2="30" stroke="#475569" strokeWidth="2" />
                          <line x1="280" y1="90" x2="330" y2="90" stroke="#475569" strokeWidth="2" />
                          
                          <line x1="330" y1="30" x2="330" y2="45" stroke="#475569" strokeWidth="1.5" />
                          <rect x="323" y="45" width="14" height="6" fill="rgba(16, 185, 129, 0.15)" stroke="#10b981" strokeWidth="1.5" />
                          <line x1="330" y1="51" x2="330" y2="65" stroke="#475569" strokeWidth="1.5" />
                          
                          <line x1="330" y1="90" x2="330" y2="75" stroke="#475569" strokeWidth="1.5" />
                          <rect x="323" y="69" width="14" height="6" fill="rgba(16, 185, 129, 0.15)" stroke="#10b981" strokeWidth="1.5" />
                          
                          <line x1="330" y1="63" x2="360" y2="63" stroke="#475569" strokeWidth="1.5" />
                          <line x1="360" y1="57" x2="360" y2="69" stroke="#64748b" strokeWidth="2" />
                          <line x1="364" y1="60" x2="364" y2="66" stroke="#64748b" strokeWidth="2" />
                          <line x1="368" y1="62" x2="368" y2="64" stroke="#64748b" strokeWidth="2" />
                          <text x="320" y="52" fill="#10b981" fontSize="7">Cy</text>
                          <text x="320" y="78" fill="#10b981" fontSize="7">Cy</text>

                          <line x1="330" y1="30" x2="420" y2="30" stroke="#475569" strokeWidth="2" />
                          <line x1="330" y1="90" x2="420" y2="90" stroke="#475569" strokeWidth="2" />
                          
                          <text x="40" y="16" fill="#64748b" fontSize="7" textAnchor="middle">LISN (Source)</text>
                          <text x="400" y="16" fill="#64748b" fontSize="7" textAnchor="middle">EUT (Load)</text>

                          <path d="M 20 30 L 176 30 M 204 30 L 420 30" fill="none" stroke="url(#flowCM)" strokeWidth="3" className="stroke-flow-animation" />
                        </svg>
                        <style>{`
                          .stroke-flow-animation {
                            stroke-dasharray: 20 80;
                            animation: flow 2s linear infinite;
                          }
                          @keyframes flow {
                            to { stroke-dashoffset: -100; }
                          }
                        `}</style>
                      </div>
                    </Card>
                  );
                case 'chart_conducted':
                  return (
                    <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
                        <div className="flex items-center gap-2">
                          <LineChart className="w-4 h-4 text-purple-400" />
                          <span className="text-xs font-bold text-white">Filter Frequency Attenuation Characteristic Curve</span>
                        </div>
                        <div className="flex bg-[#0c101d] border border-slate-800 rounded p-0.5">
                          <button
                            onClick={() => setSweepMode('cm')}
                            className={`border-0 py-0.5 px-2.5 rounded text-[10px] font-semibold cursor-pointer transition-all ${sweepMode === 'cm' ? 'bg-purple-600 text-white font-bold' : 'bg-transparent text-slate-400 hover:text-slate-200'}`}
                          >
                            Common Mode (CM)
                          </button>
                          <button
                            onClick={() => setSweepMode('dm')}
                            className={`border-0 py-0.5 px-2.5 rounded text-[10px] font-semibold cursor-pointer transition-all ${sweepMode === 'dm' ? 'bg-purple-600 text-white font-bold' : 'bg-transparent text-slate-400 hover:text-slate-200'}`}
                          >
                            Differential Mode (DM)
                          </button>
                        </div>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 flex flex-col justify-center">
                        {bodeData ? (
                          <div className="bg-slate-950 rounded-xl border border-slate-900/60 p-2 h-72">
                            <ReactECharts notMerge={true} option={getBodeChartOption()} style={{ height: '100%', width: '100%' }} />
                          </div>
                        ) : (
                          <div className="h-64 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                            Enter parameters to view insertion loss comparison with/without RC damping.
                          </div>
                        )}
                      </div>
                    </Card>
                  );
                default:
                  return null;
              }
            }}
            onDropOnColumn={conductedLayout.handleDropOnColumn}
          />
        ) : (
          <DragDeck
            isDesktop={radiatedLayout.isDesktop}
            leftSpan={radiatedLayout.leftSpan}
            rightSpan={radiatedLayout.rightSpan}
            leftCards={radiatedLayout.leftCards}
            rightCards={radiatedLayout.rightCards}
            draggedKey={radiatedLayout.draggedKey}
            renderCard={(key) => {
              switch (key) {
                case 'input_radiated':
                  return (
                    <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
                      <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
                        <span className="text-xs font-bold text-white">Radiated Field & Aperture Geometry Inputs</span>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
                        <div className="border border-slate-800/80 rounded-lg p-3 bg-slate-900/10 space-y-3">
                          <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Radiated Field & Receiver Parameters</span>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Radiation Frequency (MHz)</label>
                              <input type="number" value={radFreq} onChange={e => setRadFreq(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Receiver Reading (dBµV)</label>
                              <input type="number" value={vrx} onChange={e => setVrx(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Antenna Factor AF (dB/m)</label>
                              <input type="number" value={antennaFactor} onChange={e => setAntennaFactor(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Cable Loss (dB)</label>
                              <input type="number" value={cableLoss} onChange={e => setCableLoss(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                          </div>
                        </div>

                        <div className="border border-slate-800/80 rounded-lg p-3 bg-slate-900/10 space-y-3">
                          <span className="text-[10px] font-bold text-slate-350 block border-b border-slate-850 pb-1">Enclosure Material & Aperture Dimensions</span>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Shielding Material Type</label>
                              <select
                                value={shieldMaterial}
                                onChange={e => setShieldMaterial(e.target.value as any)}
                                className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none cursor-pointer"
                              >
                                <option value="aluminum">Aluminum</option>
                                <option value="copper">Copper</option>
                                <option value="iron">Steel / Iron</option>
                                <option value="stainless_steel">Stainless Steel</option>
                              </select>
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Material Thickness t (mm)</label>
                              <input type="number" value={shieldThickness} onChange={e => setShieldThickness(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Aperture Length L (mm)</label>
                              <input type="number" value={gapLength} onChange={e => setGapLength(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1">
                              <label className="text-[9px] text-slate-400">Aperture Width W (mm)</label>
                              <input type="number" value={gapWidth} onChange={e => setGapWidth(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                            <div className="flex flex-col gap-1 col-span-2">
                              <label className="text-[9px] text-slate-400">Total Aperture Count N</label>
                              <input type="number" value={gapCount} onChange={e => setGapCount(parseInt(e.target.value) || 1)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                            </div>
                          </div>
                        </div>
                      </div>
                    </Card>
                  );
                case 'result_radiated':
                  return (
                    <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
                      <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
                        <span className="text-xs font-bold text-white">Enclosure Shielding Effectiveness & Physical Attenuation Results</span>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs font-mono">
                        {radRes ? (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm">
                                <span className="block text-[8px] font-bold text-slate-500">Measured Radiated Field:</span>
                                <span className="text-sm font-extrabold text-amber-400">{(radRes.field_strength_dbuv_m ?? 0).toFixed(2)} dBµV/m</span>
                              </div>
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm">
                                <span className="block text-[8px] font-bold text-slate-500">Max Safe Aperture Size:</span>
                                <span className="text-sm font-extrabold text-pink-400">{(radRes.safe_gap_mm ?? 0).toFixed(2)} mm</span>
                              </div>
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm">
                                <span className="block text-[8px] font-bold text-slate-500">Aperture Reflection Loss RS:</span>
                                <span className="text-sm font-extrabold text-slate-200">{(radRes.rs_db ?? 0).toFixed(1)} dB</span>
                              </div>
                              <div className="bg-[#0b0f19]/80 border border-slate-800/80 rounded-xl p-3 shadow-sm">
                                <span className="block text-[8px] font-bold text-slate-500">Aperture Absorption Loss AS:</span>
                                <span className="text-sm font-extrabold text-slate-200">{(radRes.as_db ?? 0).toFixed(1)} dB</span>
                              </div>
                              <div className="bg-slate-950 border border-slate-850 rounded-xl p-4 col-span-2 flex justify-between items-center">
                                <div>
                                  <span className="block text-[8px] font-bold text-slate-400 uppercase">Total Shielding Effectiveness SE:</span>
                                  <span className="text-base font-extrabold text-pink-500">{(radRes.se_db ?? 0).toFixed(1)} dB</span>
                                </div>
                                <div className="text-right">
                                  <span className="block text-[8px] font-bold text-slate-500">Protection Rating:</span>
                                  <span className={`text-[10px] font-bold ${radRes.se_db >= 40 ? 'text-emerald-400' : radRes.se_db >= 20 ? 'text-amber-400' : 'text-rose-400'}`}>
                                    {radRes.se_db >= 40 ? '🥇 Excellent (IP6X Shielding Class)' : radRes.se_db >= 20 ? '🥈 Moderate (Standard Industrial Shielding)' : '🥉 Poor (Severe EMI Leakage)'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="h-32 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                            Enter parameters to calculate radiated electromagnetic attenuation.
                          </div>
                        )}
                      </div>
                    </Card>
                  );
                case 'schematic_radiated':
                  return (
                    <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
                      <div className="flex justify-between items-center border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
                        <span className="text-xs font-bold text-white flex items-center gap-1">
                          <HelpCircle className="w-4 h-4 text-purple-400" />
                          Enclosure Aperture Transmission Loss & SE Frequency Response
                        </span>
                      </div>
                      <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="border border-slate-800/80 rounded-xl bg-slate-950/40 p-3 flex flex-col items-center justify-center">
                          <span className="text-[9px] font-semibold text-slate-400 mb-1.5 self-start">Enclosure Aperture/Slot Wave Penetration Schematic:</span>
                          <svg className="w-full h-32 text-slate-400" viewBox="0 0 200 120">
                            <rect x="20" y="20" width="60" height="25" fill="#1e293b" stroke="#475569" strokeWidth="1" />
                            <rect x="20" y="75" width="60" height="25" fill="#1e293b" stroke="#475569" strokeWidth="1" />
                            <text x="50" y="35" fill="#94a3b8" fontSize="7" textAnchor="middle">Wall Thickness t</text>
                            <text x="50" y="90" fill="#94a3b8" fontSize="7" textAnchor="middle">Chassis Wall</text>

                            <line x1="30" y1="45" x2="30" y2="75" stroke="#ec4899" strokeWidth="1" strokeDasharray="2,2" />
                            <text x="26" y="62" fill="#ec4899" fontSize="7" textAnchor="end">Gap Width W</text>

                            <path d="M 120 60 Q 140 50, 160 60 Q 180 70, 200 60" fill="none" stroke="#ef4444" strokeWidth="1.5" />
                            <text x="180" y="50" fill="#ef4444" fontSize="6">Incident Wave</text>

                            <path d="M 110 40 Q 130 30, 150 40" fill="none" stroke="#eab308" strokeWidth="1" strokeDasharray="3,3" />
                            <text x="140" y="26" fill="#eab308" fontSize="6">Reflection Rs</text>

                            <path d="M 20 60 Q 10 58, 0 60" fill="none" stroke="#ec4899" strokeWidth="1" />
                            <text x="5" y="52" fill="#ec4899" fontSize="6">Penetration</text>

                            <rect x="35" y="45" width="30" height="30" fill="rgba(236,72,153,0.1)" stroke="none" />
                            <text x="50" y="62" fill="#ec4899" fontSize="6" textAnchor="middle" fontWeight="bold">Cavity Absorption As</text>
                          </svg>
                        </div>

                        {radRes ? (
                          <div className="bg-slate-950 rounded-xl border border-slate-900/60 p-1 h-36">
                            <ReactECharts notMerge={true} option={getShieldBodeChartOption()} style={{ height: '100%', width: '100%' }} />
                          </div>
                        ) : (
                          <div className="h-32 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                            Frequency sweep response will be generated after calculation.
                          </div>
                        )}
                      </div>
                    </Card>
                  );
                default:
                  return null;
              }
            }}
            onDropOnColumn={radiatedLayout.handleDropOnColumn}
          />
        )}
      </div>
    </div>
  );
}