import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import { 
  ArrowLeft, 
  ShieldAlert, 
  CheckCircle2, 
  Info, 
  Plus, 
  Trash2, 
  LineChart, 
  RotateCcw 
} from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { apiFetch } from '../lib/api';
import { useDragDeckLayout, DragDeck, DragCard } from './ui/LayoutEngine';
import { Card } from './ui/Card';

// Latex Formula Display Component
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

  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center text-slate-300 animate-fade-in" : "inline-block"} />;
};

type TabType = 
  | 'forward' 
  | 'flyback' 
  | 'llc_integration' 
  | 'ap' 
  | 'fill' 
  | 'core_loss' 
  | 'ac_loss' 
  | 'leakage' 
  | 'fit';

export default function MagTransformerPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<TabType>('forward', 'activeTab');
  const activeTabRef = useRef(activeTab);
  useEffect(() => { activeTabRef.current = activeTab; }, [activeTab]);

  // -------------------------------------------------------------
  // Tab: Forward/Bridge (Forward / Bridge / Push-Pull Transformer Design)
  // -------------------------------------------------------------
  const [fwdTopo, setFwdTopo] = useState<string>('Full-Bridge');
  const [fwdVinMin, setFwdVinMin] = useState<number>(300.0);
  const [fwdVout, setFwdVout] = useState<number>(24.0);
  const [fwdIout, setFwdIout] = useState<number>(10.0);
  const [fwdFsw, setFwdFsw] = useState<number>(100.0); // kHz
  const [fwdDmax, setFwdDmax] = useState<number>(0.45);
  const [fwdBpeak, setFwdBpeak] = useState<number>(0.15); // T
  const [fwdAe, setFwdAe] = useState<number>(119.0);
  const [fwdAw, setFwdAw] = useState<number>(43.0);
  
  const [fwdNp, setFwdNp] = useState<number | null>(null);
  const [fwdNs, setFwdNs] = useState<number | null>(null);
  const [fwdAp, setFwdAp] = useState<number | null>(null);
  const [fwdError, setFwdError] = useState<string | null>(null);

  const calculateForward = async () => {
    setFwdError(null);
    try {
      if (fwdVinMin <= 0 || fwdVout <= 0 || fwdFsw <= 0 || fwdDmax <= 0 || fwdBpeak <= 0 || fwdAe <= 0) {
        throw new Error("Input parameters must be greater than zero");
      }
      const response = await apiFetch('/api/calculate/mag_transformer/forward', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topo: fwdTopo,
          vin_min: fwdVinMin,
          vout: fwdVout,
          iout: fwdIout,
          fsw_khz: fwdFsw,
          dmax: fwdDmax,
          bpeak: fwdBpeak,
          ae_mm2: fwdAe,
          aw_mm2: fwdAw
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Failed to calculate forward transformer');
      }
      const data = await response.json();
      setFwdNp(data.np);
      setFwdNs(data.ns);
      setFwdAp(data.ap_cm4);
    } catch (e: any) {
      setFwdError(e.message);
    }
  };

  useEffect(() => {
    calculateForward();
  }, [fwdTopo, fwdVinMin, fwdVout, fwdIout, fwdFsw, fwdDmax, fwdBpeak, fwdAe, fwdAw]);

  // -------------------------------------------------------------
  // Tab: Flyback (Flyback Transformer Design)
  // -------------------------------------------------------------
  const [flyVin, setFlyVin] = useState<number>(85.0);
  const [flyVor, setFlyVor] = useState<number>(80.0);
  const [flyVout, setFlyVout] = useState<number>(12.0);
  const [flyIout, setFlyIout] = useState<number>(2.0);
  const [flyFsw, setFlyFsw] = useState<number>(65.0); // kHz
  const [flyKrf, setFlyKrf] = useState<number>(0.4);
  const [flyBmax, setFlyBmax] = useState<number>(0.25);
  const [flyAe, setFlyAe] = useState<number>(23.0);
  
  const [flyRes, setFlyRes] = useState<any>(null);
  const [flyError, setFlyError] = useState<string | null>(null);

  const calculateFlyback = async () => {
    setFlyError(null);
    try {
      const response = await apiFetch('/api/calculate/mag_transformer/flyback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vin: flyVin,
          vor: flyVor,
          vout: flyVout,
          iout: flyIout,
          fsw_khz: flyFsw,
          krf: flyKrf,
          bmax: flyBmax,
          ae_mm2: flyAe
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Failed to calculate flyback transformer');
      }
      const data = await response.json();
      setFlyRes(data);
    } catch (e: any) {
      setFlyError(e.message);
    }
  };

  useEffect(() => {
    calculateFlyback();
  }, [flyVin, flyVor, flyVout, flyIout, flyFsw, flyKrf, flyBmax, flyAe]);

  // -------------------------------------------------------------
  // Tab: LLC Integration (LLC Integrated Leakage & Dowell Sizing)
  // -------------------------------------------------------------
  const [llcNp, setLlcNp] = useState<number>(40);
  const [llcNs, setLlcNs] = useState<number>(4);
  const [llcLw, setLlcLw] = useState<number>(80.0);
  const [llcBw, setLlcBw] = useState<number>(25.0);
  const [llcDelta, setLlcDelta] = useState<number>(0.5);
  const [llcHp, setLlcHp] = useState<number>(2.0);
  const [llcHs, setLlcHs] = useState<number>(2.0);
  const [llcFsw, setLlcFsw] = useState<number>(100.0); // kHz
  const [llcDLitz, setLlcDLitz] = useState<number>(0.1);
  const [llcLayers, setLlcLayers] = useState<number>(3.0);
  const [llcLg, setLlcLg] = useState<number>(0.5);
  const [llcDGap, setLlcDGap] = useState<number>(2.0);
  
  const [llcRes, setLlcRes] = useState<any>(null);
  const [llcError, setLlcError] = useState<string | null>(null);

  const fetchLlcIntegration = async () => {
    setLlcError(null);
    try {
      const response = await apiFetch('/api/calculate/mag_transformer/llc_integration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          turns_p: llcNp,
          turns_s: llcNs,
          l_w_mm: llcLw,
          b_w_mm: llcBw,
          delta_mm: llcDelta,
          h_p_mm: llcHp,
          h_s_mm: llcHs,
          fsw_khz: llcFsw,
          d_litz_mm: llcDLitz,
          layers: llcLayers,
          l_g_mm: llcLg,
          d_gap_dist_mm: llcDGap
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setLlcRes(data);
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
    } catch (e: any) {
      setLlcError(e.message);
    }
  };

  useEffect(() => {
    fetchLlcIntegration();
  }, [llcNp, llcNs, llcLw, llcBw, llcDelta, llcHp, llcHs, llcFsw, llcDLitz, llcLayers, llcLg, llcDGap]);

  // -------------------------------------------------------------
  // Tab: AP Core Selection (AP Core Sizing Estimation)
  // -------------------------------------------------------------
  const [apPout, setApPout] = useState<number>(100.0);
  const [apFsw, setApFsw] = useState<number>(100.0);
  const [apDb, setApDb] = useState<number>(0.2);
  const [apJ, setApJ] = useState<number>(4.5);
  const [apKtopo, setApKtopo] = useState<number>(1.8); // Default Flyback

  const [apRes, setApRes] = useState<any>(null);
  const [apError, setApError] = useState<string | null>(null);

  const fetchAp = async () => {
    setApError(null);
    try {
      const response = await apiFetch('/api/calculate/mag_transformer/ap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pout: apPout,
          fsw_khz: apFsw,
          db_t: apDb,
          j_amm2: apJ,
          k_topo: apKtopo
        })
      });
      if (response.ok) {
        const data = await response.json();
        setApRes(data);
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
    } catch (e: any) {
      setApError(e.message);
    }
  };

  useEffect(() => {
    fetchAp();
  }, [apPout, apFsw, apDb, apJ, apKtopo]);

  // -------------------------------------------------------------
  // Tab: Winding Fill Factor (Window Fill Factor Verification)
  // -------------------------------------------------------------
  const [fillWinW, setFillWinW] = useState<number>(8.0);
  const [fillWinD, setFillWinD] = useState<number>(3.0);
  const [fillTurns, setFillTurns] = useState<number>(40.0);
  const [fillWireOd, setFillWireOd] = useState<number>(0.35);
  const [fillStrands, setFillStrands] = useState<number>(1.0);
  const [fillTape, setFillTape] = useState<number>(0.05);

  const [fillRes, setFillRes] = useState<any>(null);
  const [fillError, setFillError] = useState<string | null>(null);

  const fetchFill = async () => {
    setFillError(null);
    try {
      const response = await apiFetch('/api/calculate/mag_transformer/fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          win_w: fillWinW,
          win_d: fillWinD,
          turns: fillTurns,
          wire_od: fillWireOd,
          strands: fillStrands,
          tape_thickness: fillTape
        })
      });
      if (response.ok) {
        const data = await response.json();
        setFillRes(data);
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
    } catch (e: any) {
      setFillError(e.message);
    }
  };

  useEffect(() => {
    fetchFill();
  }, [fillWinW, fillWinD, fillTurns, fillWireOd, fillStrands, fillTape]);

  // -------------------------------------------------------------
  // Tab: Core Loss (Core Loss Analysis)
  // -------------------------------------------------------------
  const [lossVol, setLossVol] = useState<number>(5.35); // cm^3
  const [lossFreq, setLossFreq] = useState<number>(100.0); // kHz
  const [lossB, setLossB] = useState<number>(0.15); // T
  const [lossK, setLossK] = useState<number>(0.035);
  const [lossAlpha, setLossAlpha] = useState<number>(1.63);
  const [lossBeta, setLossBeta] = useState<number>(2.68);
  const [selectedMaterial, setSelectedMaterial] = useState<string>('PC40 (TDK)');

  const [lossRes, setLossRes] = useState<any>(null);
  const [lossError, setLossError] = useState<string | null>(null);

  useEffect(() => {
    const materials: Record<string, any> = {
      "PC40 (TDK)":  {k: 0.0350, a: 1.63, b: 2.68},
      "PC95 (TDK)":  {k: 0.3500, a: 1.45, b: 2.45},
      "3C90 (Ferroxcube)": {k: 0.0320, a: 1.46, b: 2.75},
      "3C94 (Ferroxcube)": {k: 0.0280, a: 1.50, b: 2.70},
      "N87 (Epcos)": {k: 0.0270, a: 1.60, b: 2.70}
    };
    if (selectedMaterial !== 'Custom') {
      const coeff = materials[selectedMaterial];
      if (coeff) {
        setLossK(coeff.k);
        setLossAlpha(coeff.a);
        setLossBeta(coeff.b);
      }
    }
  }, [selectedMaterial]);

  const fetchLoss = async () => {
    setLossError(null);
    try {
      const response = await apiFetch('/api/calculate/mag_transformer/core_loss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          volume_cm3: lossVol,
          f_khz: lossFreq,
          b_t: lossB,
          k_stein: lossK,
          alpha: lossAlpha,
          beta: lossBeta
        })
      });
      if (response.ok) {
        const data = await response.json();
        setLossRes(data);
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
    } catch (e: any) {
      setLossError(e.message);
    }
  };

  useEffect(() => {
    fetchLoss();
  }, [lossVol, lossFreq, lossB, lossK, lossAlpha, lossBeta]);

  // -------------------------------------------------------------
  // Tab: AC Winding Loss (AC Resistance Ratio - Proximity)
  // -------------------------------------------------------------
  const [acLayers, setAcLayers] = useState<number>(3.0);
  const [acFreq, setAcFreq] = useState<number>(100.0); // kHz
  const [acDia, setAcDia] = useState<number>(0.35);
  const [acPorosity, setAcPorosity] = useState<number>(0.9);

  const [acRes, setAcRes] = useState<any>(null);
  const [acError, setAcError] = useState<string | null>(null);

  const fetchAcWinding = async () => {
    setAcError(null);
    try {
      const response = await apiFetch('/api/calculate/mag_inductor/litz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          i_rms_a: 5.0,
          f_hz: acFreq * 1000.0,
          layers: acLayers
        })
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
      
      const skin_depth_mm = 72.0 / Math.sqrt(acFreq * 1000.0);
      const phi = (acDia / skin_depth_mm) * Math.sqrt(acPorosity);
      
      const computeDowell = (phi_val: number, m: number) => {
        const sinh_2p = Math.sinh(2.0 * phi_val);
        const sin_2p = Math.sin(2.0 * phi_val);
        const cosh_2p = Math.cosh(2.0 * phi_val);
        const cos_2p = Math.cos(2.0 * phi_val);
        
        const term1 = phi_val * (sinh_2p + sin_2p) / (cosh_2p - cos_2p || 1e-9);
        
        const sinh_p = Math.sinh(phi_val);
        const sin_p = Math.sin(phi_val);
        const cosh_p = Math.cosh(phi_val);
        const cos_p = Math.cos(phi_val);
        
        const term2 = (2.0 / 3.0) * (Math.pow(m, 2) - 1.0) * phi_val * (sinh_p - sin_p) / (cosh_p + cos_p || 1e-9);
        return term1 + term2;
      };
      
      const fr = computeDowell(phi, acLayers);

      setAcRes({
        skin_depth_mm,
        phi,
        fr
      });
    } catch (e: any) {
      setAcError(e.message);
    }
  };

  useEffect(() => {
    fetchAcWinding();
  }, [acLayers, acFreq, acDia, acPorosity]);

  // -------------------------------------------------------------
  // Tab: Leakage Inductance (Leakage Estimation)
  // -------------------------------------------------------------
  const [lkTurns, setLkTurns] = useState<number>(40);
  const [lkMlt, setLkMlt] = useState<number>(80.0);
  const [lkBw, setLkBw] = useState<number>(25.0);
  const [lkHp, setLkHp] = useState<number>(2.0);
  const [lkHs, setLkHs] = useState<number>(2.0);
  const [lkTins, setLkTins] = useState<number>(0.1);
  const [lkIsSandwich, setLkIsSandwich] = useState<boolean>(true);
  const [lkInterleaveM, setLkInterleaveM] = useState<number>(2);

  const [lkRes, setLkRes] = useState<any>(null);
  const [lkError, setLkError] = useState<string | null>(null);

  const fetchLeakage = async () => {
    setLkError(null);
    try {
      const response = await apiFetch('/api/calculate/mag_transformer/leakage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          turns: lkTurns,
          mlt_mm: lkMlt,
          bw_mm: lkBw,
          hp_mm: lkHp,
          hs_mm: lkHs,
          tins_mm: lkTins,
          is_sandwich: lkIsSandwich,
          interleave_m: lkInterleaveM
        })
      });
      if (response.ok) {
        const data = await response.json();
        setLkRes(data);
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Calculation failed');
      }
    } catch (e: any) {
      setLkError(e.message);
    }
  };

  useEffect(() => {
    fetchLeakage();
  }, [lkTurns, lkMlt, lkBw, lkHp, lkHs, lkTins, lkIsSandwich, lkInterleaveM]);

  // -------------------------------------------------------------
  // Tab: Steinmetz Fit (Curve Fitting)
  // -------------------------------------------------------------
  const [fitRows, setFitRows] = useState<any[]>([
    { f: '100', b: '100', pv: '65' },
    { f: '100', b: '200', pv: '400' },
    { f: '200', b: '100', pv: '200' },
    { f: '', b: '', pv: '' }
  ]);
  const [fitRes, setFitRes] = useState<any>(null);
  const [fitError, setFitError] = useState<string | null>(null);
  
  const [valF, setValF] = useState<number>(100.0);
  const [valB, setValB] = useState<number>(150.0);
  const [valPv, setValPv] = useState<number | null>(null);

  const handleAddFitRow = () => {
    setFitRows([...fitRows, { f: '', b: '', pv: '' }]);
  };

  const handleClearFitTable = () => {
    setFitRows([
      { f: '', b: '', pv: '' },
      { f: '', b: '', pv: '' },
      { f: '', b: '', pv: '' }
    ]);
    setFitRes(null);
  };

  const handleFitCalculate = async () => {
    setFitError(null);
    try {
      const f_list: number[] = [];
      const b_list: number[] = [];
      const pv_list: number[] = [];
      
      fitRows.forEach(row => {
        if (row.f && row.b && row.pv) {
          const f = parseFloat(row.f);
          const b = parseFloat(row.b);
          const pv = parseFloat(row.pv);
          if (f > 0 && b > 0 && pv > 0) {
            f_list.push(f);
            b_list.push(b);
            pv_list.push(pv);
          }
        }
      });

      if (f_list.length < 3) {
        throw new Error("At least 3 valid positive sampling points are required for fitting");
      }

      const response = await apiFetch('/api/calculate/mag_transformer/fit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ f_list, b_list, pv_list })
      });
      if (response.ok) {
        const data = await response.json();
        setFitRes(data);
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Fitting failed');
      }
    } catch (e: any) {
      setFitError(e.message);
    }
  };

  useEffect(() => {
    if (fitRes) {
      const pv_pred = fitRes.k * Math.pow(valF, fitRes.alpha) * Math.pow(valB, fitRes.beta);
      setValPv(pv_pred);
    }
  }, [valF, valB, fitRes]);

  // -------------------------------------------------------------
  // ECharts Plot Setup
  // -------------------------------------------------------------
  const getAcLossChartOption = () => {
    if (!acRes) return {};
    const fPoints: number[] = [];
    const frPoints: number[] = [];
    
    for (let f = 1; f <= 10000; f = f * 1.15) {
      const f_hz = f * 1000.0;
      const skin_depth = 72.0 / Math.sqrt(f_hz);
      const phi_val = (acDia / skin_depth) * Math.sqrt(acPorosity);
      
      const sinh_2p = Math.sinh(2.0 * phi_val);
      const sin_2p = Math.sin(2.0 * phi_val);
      const cosh_2p = Math.cosh(2.0 * phi_val);
      const cos_2p = Math.cos(2.0 * phi_val);
      
      const term1 = phi_val * (sinh_2p + sin_2p) / (cosh_2p - cos_2p || 1e-9);
      
      const sinh_p = Math.sinh(phi_val);
      const sin_p = Math.sin(phi_val);
      const cosh_p = Math.cosh(phi_val);
      const cos_p = Math.cos(phi_val);
      
      const term2 = (2.0 / 3.0) * (Math.pow(acLayers, 2) - 1.0) * phi_val * (sinh_p - sin_p) / (cosh_p + cos_p || 1e-9);
      const fr_val = term1 + term2;
      
      fPoints.push(f);
      frPoints.push(Math.min(100, Math.max(1, fr_val)));
    }
    
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const f = params[0].axisValue;
          const fr = params[0].data[1];
          return `Frequency: ${parseFloat(f).toFixed(1)} kHz<br/>Fr (Rac/Rdc): ${parseFloat(fr).toFixed(2)}`;
        }
      },
      grid: { left: '10%', right: '10%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'log',
        name: 'Frequency (kHz)',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        min: 1,
        max: 10000
      },
      yAxis: {
        type: 'value',
        name: 'AC Resistance Factor Fr',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      series: [
        {
          data: frPoints.map((val, idx) => [fPoints[idx], val]),
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { color: '#22d3ee', width: 2 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(34, 211, 238, 0.2)' },
                { offset: 1, color: 'rgba(34, 211, 238, 0)' }
              ]
            }
          }
        }
      ]
    };
  };

  const getFitChartOption = () => {
    if (!fitRes) return {};
    
    const validPoints: { f: number; b: number; pv: number }[] = [];
    fitRows.forEach(row => {
      if (row.f && row.b && row.pv) {
        const f = parseFloat(row.f);
        const b = parseFloat(row.b);
        const pv = parseFloat(row.pv);
        if (f > 0 && b > 0 && pv > 0) {
          validPoints.push({ f, b, pv });
        }
      }
    });
    
    if (validPoints.length === 0) return {};
    
    const curveB: number[] = [];
    const curvePv: number[] = [];
    const minB = Math.max(10, Math.min(...validPoints.map(p => p.b)) * 0.5);
    const maxB = Math.max(100, Math.max(...validPoints.map(p => p.b)) * 1.5);
    
    for (let b = minB; b <= maxB; b += (maxB - minB) / 50) {
      const pv_pred = fitRes.k * Math.pow(valF, fitRes.alpha) * Math.pow(b, fitRes.beta);
      curveB.push(b);
      curvePv.push(pv_pred);
    }
    
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: {
        textStyle: { color: '#94a3b8' },
        data: ['Fitted Steinmetz Curve', 'Measured Data Points']
      },
      grid: { left: '10%', right: '10%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Flux Density B (mT)',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      yAxis: {
        type: 'value',
        name: 'Loss Pv (mW/cm³)',
        nameTextStyle: { color: '#94a3b8' },
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
      },
      series: [
        {
          name: 'Fitted Steinmetz Curve',
          data: curvePv.map((val, idx) => [curveB[idx], val]),
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { color: '#a855f7', width: 2 }
        },
        {
          name: 'Measured Data Points',
          data: validPoints.map(p => [p.b, p.pv]),
          type: 'scatter',
          symbolSize: 8,
          itemStyle: { color: '#22d3ee' }
        }
      ]
    };
  };

  const renderLlcSvg = () => {
    return (
      <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-xl border border-slate-850 h-[300px]">
        <span className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wide">Transformer Bobbin & Winding Physical Cross Section</span>
        <svg viewBox="0 0 400 180" className="w-full max-w-[320px] h-auto">
          <rect x="20" y="20" width="30" height="140" rx="4" fill="#334155" opacity="0.8" />
          <rect x="185" y="20" width="30" height="140" rx="2" fill="#334155" opacity="0.8" />
          <rect x="350" y="20" width="30" height="140" rx="4" fill="#334155" opacity="0.8" />
          <rect x="20" y="20" width="360" height="20" fill="#334155" opacity="0.8" />
          <rect x="20" y="140" width="360" height="20" fill="#334155" opacity="0.8" />

          <rect x="185" y="85" width="30" height="10" fill="#020617" />
          <path d="M 180 82 Q 170 90 180 98" fill="none" stroke="#eab308" strokeWidth="1" strokeDasharray="2,2" opacity="0.8" />
          <path d="M 180 77 Q 160 90 180 103" fill="none" stroke="#eab308" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
          <path d="M 220 82 Q 230 90 220 98" fill="none" stroke="#eab308" strokeWidth="1" strokeDasharray="2,2" opacity="0.8" />
          <path d="M 220 77 Q 240 90 220 103" fill="none" stroke="#eab308" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
          <text x="145" y="93" fill="#eab308" fontSize="8" fontWeight="bold">Air Gap lg</text>

          <rect x="180" y="40" width="5" height="100" fill="#475569" />
          <rect x="215" y="40" width="5" height="100" fill="#475569" />
          <rect x="180" y="88" width="40" height="4" fill="#475569" />

          <g opacity="0.9">
            <rect x="135" y="45" width="45" height="40" rx="3" fill="none" stroke="#f97316" strokeWidth="1.5" strokeDasharray="2,2" />
            <circle cx="145" cy="55" r="4" fill="#f97316" />
            <circle cx="157" cy="55" r="4" fill="#f97316" />
            <circle cx="169" cy="55" r="4" fill="#f97316" />
            <circle cx="145" cy="67" r="4" fill="#f97316" />
            <circle cx="157" cy="67" r="4" fill="#f97316" />
            <circle cx="169" cy="67" r="4" fill="#f97316" />
            <circle cx="145" cy="79" r="4" fill="#f97316" />
            <circle cx="157" cy="79" r="4" fill="#f97316" />
            <text x="100" y="68" fill="#f97316" fontSize="8" fontWeight="bold">Pri (P)</text>
          </g>

          <g opacity="0.9">
            <rect x="135" y="95" width="45" height="40" rx="3" fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="2,2" />
            <circle cx="145" cy="105" r="4" fill="#3b82f6" />
            <circle cx="157" cy="105" r="4" fill="#3b82f6" />
            <circle cx="169" cy="105" r="4" fill="#3b82f6" />
            <circle cx="145" cy="117" r="4" fill="#3b82f6" />
            <circle cx="157" cy="117" r="4" fill="#3b82f6" />
            <circle cx="169" cy="117" r="4" fill="#3b82f6" />
            <text x="100" y="118" fill="#3b82f6" fontSize="8" fontWeight="bold">Sec (S)</text>
          </g>

          <g opacity="0.9">
            <rect x="220" y="45" width="45" height="40" rx="3" fill="none" stroke="#f97316" strokeWidth="1.5" strokeDasharray="2,2" />
            <circle cx="230" cy="55" r="4" fill="#f97316" />
            <circle cx="242" cy="55" r="4" fill="#f97316" />
            <circle cx="254" cy="55" r="4" fill="#f97316" />
            <circle cx="230" cy="67" r="4" fill="#f97316" />
            <circle cx="242" cy="67" r="4" fill="#f97316" />
            <circle cx="254" cy="67" r="4" fill="#f97316" />
            <circle cx="230" cy="79" r="4" fill="#f97316" />
            <circle cx="242" cy="79" r="4" fill="#f97316" />
          </g>
          <g opacity="0.9">
            <rect x="220" y="95" width="45" height="40" rx="3" fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="2,2" />
            <circle cx="230" cy="105" r="4" fill="#3b82f6" />
            <circle cx="242" cy="105" r="4" fill="#3b82f6" />
            <circle cx="254" cy="105" r="4" fill="#3b82f6" />
            <circle cx="230" cy="117" r="4" fill="#3b82f6" />
            <circle cx="242" cy="117" r="4" fill="#3b82f6" />
            <circle cx="254" cy="117" r="4" fill="#3b82f6" />
          </g>

          <line x1="180" y1="155" x2="145" y2="155" stroke="#ef4444" strokeWidth="1" markerEnd="url(#arrow)" />
          <line x1="180" y1="155" x2="200" y2="155" stroke="#ef4444" strokeWidth="1" />
          <circle cx="180" cy="85" r="2" fill="#ef4444" />
          <line x1="180" y1="85" x2="180" y2="155" stroke="#ef4444" strokeWidth="0.8" strokeDasharray="1,1" />
          <line x1="145" y1="85" x2="145" y2="155" stroke="#ef4444" strokeWidth="0.8" strokeDasharray="1,1" />
          <text x="130" y="165" fill="#ef4444" fontSize="7" fontWeight="bold">Gap Clearance d_gap</text>

          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
            </marker>
          </defs>
        </svg>
      </div>
    );
  };

  // -------------------------------------------------------------
  // DragDeck Setup
  // -------------------------------------------------------------
  const getLayoutConfig = () => {
    switch (activeTab) {
      case 'forward':
        return {
          defaultCards: ['input_forward', 'result_forward', 'formula_forward'],
          defaultColumns: { input_forward: 'left', formula_forward: 'left', result_forward: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_forward: 4, formula_forward: 4, result_forward: 8 },
          defaultHeights: { input_forward: 500, formula_forward: 200, result_forward: 700 }
        };
      case 'flyback':
        return {
          defaultCards: ['input_flyback', 'result_flyback', 'formula_flyback'],
          defaultColumns: { input_flyback: 'left', formula_flyback: 'left', result_flyback: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_flyback: 4, formula_flyback: 4, result_flyback: 8 },
          defaultHeights: { input_flyback: 500, formula_flyback: 200, result_flyback: 700 }
        };
      case 'llc_integration':
        return {
          defaultCards: ['input_llc', 'result_llc', 'chart_llc'],
          defaultColumns: { input_llc: 'left', result_llc: 'right', chart_llc: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_llc: 4, result_llc: 8, chart_llc: 8 },
          defaultHeights: { input_llc: 700, result_llc: 320, chart_llc: 380 }
        };
      case 'ap':
        return {
          defaultCards: ['input_ap', 'result_ap', 'formula_ap'],
          defaultColumns: { input_ap: 'left', formula_ap: 'left', result_ap: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_ap: 4, formula_ap: 4, result_ap: 8 },
          defaultHeights: { input_ap: 400, formula_ap: 200, result_ap: 600 }
        };
      case 'fill':
        return {
          defaultCards: ['input_fill', 'result_fill'],
          defaultColumns: { input_fill: 'left', result_fill: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_fill: 4, result_fill: 8 },
          defaultHeights: { input_fill: 400, result_fill: 400 }
        };
      case 'core_loss':
        return {
          defaultCards: ['input_core', 'result_core'],
          defaultColumns: { input_core: 'left', result_core: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_core: 4, result_core: 8 },
          defaultHeights: { input_core: 550, result_core: 550 }
        };
      case 'ac_loss':
        return {
          defaultCards: ['input_ac_loss', 'result_ac_loss', 'chart_ac_loss'],
          defaultColumns: { input_ac_loss: 'left', result_ac_loss: 'right', chart_ac_loss: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_ac_loss: 4, result_ac_loss: 8, chart_ac_loss: 8 },
          defaultHeights: { input_ac_loss: 420, result_ac_loss: 260, chart_ac_loss: 380 }
        };
      case 'leakage':
        return {
          defaultCards: ['input_leakage', 'result_leakage'],
          defaultColumns: { input_leakage: 'left', result_leakage: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_leakage: 4, result_leakage: 8 },
          defaultHeights: { input_leakage: 450, result_leakage: 450 }
        };
      case 'fit':
        return {
          defaultCards: ['input_fit', 'result_fit', 'chart_fit'],
          defaultColumns: { input_fit: 'left', result_fit: 'right', chart_fit: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input_fit: 4, result_fit: 8, chart_fit: 8 },
          defaultHeights: { input_fit: 600, result_fit: 220, chart_fit: 380 }
        };
      default:
        return {
          defaultCards: ['input', 'result'],
          defaultColumns: { input: 'left', result: 'right' } as Record<string, 'left' | 'right'>,
          defaultSpans: { input: 4, result: 8 },
          defaultHeights: { input: 500, result: 500 }
        };
    }
  };

  const layoutCfg = getLayoutConfig();
  const activeCfgSpans = layoutCfg.defaultSpans;

  const {
    isDesktop,
    draggedKey,
    leftCards,
    rightCards,
    leftSpan,
    rightSpan,
    cardHeights,
    handleDragStart,
    handleDragEnter,
    handleDragEnd,
    handleDropOnColumn,
    handleResizeStart,
    handleHeightResizeStart,
    handleHeightResizeStartTop,
    handleResetCardHeight,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_magtransformerpanel_v3_' + activeTab,
    defaultCards: layoutCfg.defaultCards,
    defaultColumns: layoutCfg.defaultColumns,
    defaultSpans: activeCfgSpans,
    defaultHeights: layoutCfg.defaultHeights
  });

  useEffect(() => {
    const raw = localStorage.getItem('target_mag_transformer_data');
    if (raw) {
      try {
        const payload = JSON.parse(raw);
        if (payload.tab) {
          setActiveTab(payload.tab as any);
        }
        const p = payload.params || {};
        if (payload.tab === 'forward') {
          if (p.vin_min !== undefined) setFwdVinMin(p.vin_min);
          if (p.vout !== undefined) setFwdVout(p.vout);
          if (p.pout !== undefined && p.vout > 0) setFwdIout(p.pout / p.vout);
          if (p.fsw_khz !== undefined) setFwdFsw(p.fsw_khz);
        } else if (payload.tab === 'flyback') {
          if (p.fly_vin !== undefined) setFlyVin(p.fly_vin);
          if (p.fly_vor !== undefined) setFlyVor(p.fly_vor);
          if (p.fly_vout !== undefined) setFlyVout(p.fly_vout);
          if (p.pout !== undefined && p.fly_vout > 0) setFlyIout(p.pout / p.fly_vout);
          if (p.fsw_khz !== undefined) setFlyFsw(p.fsw_khz);
        }
      } catch (e) {
        console.error('Failed to parse target_mag_transformer_data:', e);
      } finally {
        localStorage.removeItem('target_mag_transformer_data');
      }
    }
  }, []);

  const renderCardContent = (key: string) => {
    switch (key) {
      // --- Forward Tab Cards ---
      case 'input_forward':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Forward / Bridge Operating Specs</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="flex flex-col gap-1">
                <label className="text-slate-400 font-semibold">Topology Structure</label>
                <select value={fwdTopo} onChange={(e) => setFwdTopo(e.target.value)} className="neon-input">
                  <option value="Full-Bridge">Full-Bridge</option>
                  <option value="Half-Bridge">Half-Bridge</option>
                  <option value="Push-Pull">Push-Pull</option>
                  <option value="Forward">Single-Switch Forward</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Min Input Vin_min (V)</label>
                  <input type="number" value={fwdVinMin} onChange={(e) => setFwdVinMin(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Output Voltage Vout (V)</label>
                  <input type="number" value={fwdVout} onChange={(e) => setFwdVout(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Output Current Iout (A)</label>
                  <input type="number" value={fwdIout} onChange={(e) => setFwdIout(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Frequency fsw (kHz)</label>
                  <input type="number" value={fwdFsw} onChange={(e) => setFwdFsw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Max Duty Cycle Dmax</label>
                  <input type="number" step="0.01" value={fwdDmax} onChange={(e) => setFwdDmax(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Peak AC Flux Bac (T)</label>
                  <input type="number" step="0.01" value={fwdBpeak} onChange={(e) => setFwdBpeak(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Core Area Ae (mm²)</label>
                  <input type="number" value={fwdAe} onChange={(e) => setFwdAe(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Window Area Aw (mm²)</label>
                  <input type="number" value={fwdAw} onChange={(e) => setFwdAw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
              </div>
            </div>
          </Card>
        );

      case 'result_forward':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Design Calculation Results</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-300 font-mono">
              {fwdError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-red-500" />
                  <span>{fwdError}</span>
                </div>
              )}
              {fwdNp !== null && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col">
                      <span className="text-[10px] text-slate-400 font-semibold">Min Primary Turns (Np)</span>
                      <span className="text-xl font-bold text-cyan-400 mt-1">{fwdNp} turns</span>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col">
                      <span className="text-[10px] text-slate-400 font-semibold">Calculated Secondary Turns (Ns)</span>
                      <span className="text-xl font-bold text-cyan-400 mt-1">{fwdNs} turns</span>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col col-span-2">
                      <span className="text-[10px] text-slate-400 font-semibold">Core Equivalent Area Product (AP)</span>
                      <span className="text-xl font-bold text-purple-400 mt-1">{fwdAp?.toFixed(3)} cm⁴</span>
                      <span className="text-[9px] text-slate-500 mt-0.5">Formula: Ae * Aw / 10000</span>
                    </div>
                  </div>
                  {fwdDmax > 0.5 && fwdTopo.includes("Forward") && (
                    <div className="p-3 bg-yellow-950/20 border border-yellow-500/20 text-yellow-300 rounded-lg text-[11px] flex gap-2">
                      <ShieldAlert className="w-4.5 h-4.5 text-yellow-500 shrink-0" />
                      <span>Forward duty cycle &gt; 0.50 requires reset winding N3 &lt; N1 to guarantee full demagnetization and avoid saturation.</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        );

      case 'formula_forward':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <Info className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-white">Physical Design Formulas</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-3 text-[11px] text-slate-350 leading-relaxed font-mono">
              <p>1. Primary Turns Equation:</p>
              <Latex math="N_p \ge \frac{V_{in,min} \cdot D_{max}}{f_{sw} \cdot A_e \cdot \Delta B}" block />
              <p className="text-[10px] text-slate-500">Applies Volt-Second balance with flux excursion ΔB tailored to the converter topology.</p>
              <p>2. Secondary Turns Equation:</p>
              <Latex math="N_s = N_p \cdot \frac{V_{out} + V_{diode}}{V_{in,min} \cdot D_{max}}" block />
            </div>
          </Card>
        );

      // --- Flyback Tab Cards ---
      case 'input_flyback':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Flyback Input Parameters</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Min Input Vin_min (V)</label>
                  <input type="number" value={flyVin} onChange={(e) => setFlyVin(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Reflected Voltage Vor (V)</label>
                  <input type="number" value={flyVor} onChange={(e) => setFlyVor(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Output Voltage Vout (V)</label>
                  <input type="number" value={flyVout} onChange={(e) => setFlyVout(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Output Current Iout (A)</label>
                  <input type="number" value={flyIout} onChange={(e) => setFlyIout(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Frequency fsw (kHz)</label>
                  <input type="number" value={flyFsw} onChange={(e) => setFlyFsw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Ripple Factor Krf</label>
                  <input type="number" step="0.05" value={flyKrf} onChange={(e) => setFlyKrf(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Peak Flux Bmax (T)</label>
                  <input type="number" step="0.01" value={flyBmax} onChange={(e) => setFlyBmax(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Core Area Ae (mm²)</label>
                  <input type="number" value={flyAe} onChange={(e) => setFlyAe(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
              </div>
            </div>
          </Card>
        );

      case 'result_flyback':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Design Estimation Results</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-300 font-mono">
              {flyError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{flyError}</span>
                </div>
              )}
              {flyRes && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <div className="text-[10px] text-slate-400">Operating Mode</div>
                      <div className="text-md font-bold text-cyan-400 mt-0.5">{flyRes?.mode ?? ''}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <div className="text-[10px] text-slate-400">Primary Inductance Lp</div>
                      <div className="text-md font-bold text-cyan-400 mt-0.5">{(flyRes?.lp_uh ?? 0).toFixed(1)} uH</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <div className="text-[10px] text-slate-400">Primary Turns Np</div>
                      <div className="text-md font-bold text-purple-400 mt-0.5">{flyRes?.np ?? 0} turns</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <div className="text-[10px] text-slate-400">Machined Air Gap lg</div>
                      <div className="text-md font-bold text-purple-400 mt-0.5">{(flyRes?.lg_mm ?? 0).toFixed(3)} mm</div>
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-855 flex flex-col gap-2">
                    <div className="text-xs text-slate-400 border-b border-slate-800 pb-1 mb-1 font-semibold">Stress & RMS Current Ratings</div>
                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div>Primary Peak/RMS Current: <span className="text-slate-200 font-semibold">{(flyRes?.ip_pk ?? 0).toFixed(2)} A / {(flyRes?.ip_rms ?? 0).toFixed(2)} A</span></div>
                      <div>Secondary Peak/RMS Current: <span className="text-slate-200 font-semibold">{(flyRes?.is_pk ?? 0).toFixed(2)} A / {(flyRes?.is_rms ?? 0).toFixed(2)} A</span></div>
                      <div className="col-span-2">Calculated Peak Flux B_pk: <span className="text-emerald-400 font-semibold">{(flyRes?.bpk ?? 0).toFixed(3)} T</span></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        );

      case 'formula_flyback':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <Info className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-white">Flyback Analytical Formulas</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-3 text-[11px] text-slate-350 leading-relaxed font-mono">
              <p>1. Maximum Operating Duty Cycle:</p>
              <Latex math="D_{max} = \frac{V_{or}}{V_{in,min} + V_{or}}" block />
              <p>2. Continuous Conduction Primary Inductance:</p>
              <Latex math="L_p = \frac{V_{in,min} \cdot D_{max}}{K_{rf} \cdot I_{EDC} \cdot f_{sw}}" block />
              <p>3. Physical Air Gap Sizing with Fringing Correction:</p>
              <Latex math="l_g = \frac{\mu_0 \cdot N_p^2 \cdot A_e}{L_p}" block />
            </div>
          </Card>
        );

      // --- LLC Integration Cards ---
      case 'input_llc':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Geometry & Winding Structure</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Primary Turns Np</label>
                  <input type="number" value={llcNp} onChange={(e) => setLlcNp(parseInt(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Secondary Turns Ns</label>
                  <input type="number" value={llcNs} onChange={(e) => setLlcNs(parseInt(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Mean Length Turn lw (mm)</label>
                  <input type="number" value={llcLw} onChange={(e) => setLlcLw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Window Width bw (mm)</label>
                  <input type="number" value={llcBw} onChange={(e) => setLlcBw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Insulation Clearance Δ (mm)</label>
                  <input type="number" step="0.1" value={llcDelta} onChange={(e) => setLlcDelta(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Primary Height hp (mm)</label>
                  <input type="number" step="0.1" value={llcHp} onChange={(e) => setLlcHp(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Secondary Height hs (mm)</label>
                  <input type="number" step="0.1" value={llcHs} onChange={(e) => setLlcHs(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Operating Frequency fsw (kHz)</label>
                  <input type="number" value={llcFsw} onChange={(e) => setLlcFsw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Litz Strand Diameter (mm)</label>
                  <input type="number" step="0.01" value={llcDLitz} onChange={(e) => setLlcDLitz(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Equivalent Layers m</label>
                  <input type="number" value={llcLayers} onChange={(e) => setLlcLayers(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Air Gap lg (mm)</label>
                  <input type="number" step="0.1" value={llcLg} onChange={(e) => setLlcLg(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Gap Clearance d_gap (mm)</label>
                  <input type="number" step="0.5" value={llcDGap} onChange={(e) => setLlcDGap(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
              </div>
            </div>
          </Card>
        );

      case 'result_llc':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Leakage & High-Frequency Loss Assessment</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-350 font-mono">
              {llcError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{llcError}</span>
                </div>
              )}
              {llcRes && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col">
                      <span className="text-[10px] text-slate-400 font-semibold tracking-wider">Integrated Leakage (Lk)</span>
                      <span className="text-xl font-bold text-emerald-400 mt-1">{(llcRes?.l_lk_uh ?? 0).toFixed(3)} uH</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col">
                      <span className="text-[10px] text-slate-400 font-semibold tracking-wider">Skin Depth (δ)</span>
                      <span className="text-xl font-bold text-slate-200 mt-1">{(llcRes?.skin_depth_mm ?? 0).toFixed(4)} mm</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col col-span-2">
                      <span className="text-[10px] text-slate-400 font-semibold tracking-wider">Dowell AC Resistance Ratio (Fr)</span>
                      <span className="text-xl font-bold text-cyan-400 mt-1">{(llcRes?.fr_pri ?? 0).toFixed(2)}</span>
                      <span className="text-[9px] text-slate-500 mt-0.5">High-frequency AC resistance increases to {(llcRes?.fr_pri ?? 0).toFixed(1)}x of DC resistance.</span>
                    </div>
                  </div>

                  {llcRes?.fringing_flux_warning ? (
                    <div className="p-3 bg-red-950/20 border border-red-500/30 text-red-200 rounded-lg flex flex-col gap-1 text-[11px] animate-pulse">
                      <div className="flex items-center gap-1.5 font-bold text-red-400">
                        <span>⚠️ Fringing Flux Winding Overheating Risk!</span>
                      </div>
                      <p>Winding distance to air gap ({llcDGap}mm) is less than 3 * lg threshold ({(llcRes?.min_safe_dist_mm ?? 0).toFixed(1)}mm). Severe fringing flux will induce high eddy loss and insulation failure. Increase bobbin spacer or decrease gap size.</p>
                    </div>
                  ) : (
                    <div className="p-3 bg-emerald-950/20 border border-emerald-500/20 text-emerald-300 rounded-lg flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>Winding distance complies with 3 * lg safe thermal rule ({llcDGap}mm &gt;= {(llcRes?.min_safe_dist_mm ?? 0).toFixed(1)}mm)</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        );

      case 'chart_llc':
        return renderLlcSvg();

      // --- AP Sizing Cards ---
      case 'input_ap':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Input Design Requirements</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="flex flex-col gap-1">
                <label className="text-slate-400">Topology Factor (K Coefficient)</label>
                <select value={apKtopo} onChange={(e) => setApKtopo(parseFloat(e.target.value))} className="neon-input">
                  <option value={1.8}>Flyback - K=1.8</option>
                  <option value={2.8}>Single-Switch Forward - K=2.8</option>
                  <option value={4.0}>Full-Bridge / Half-Bridge / Push-Pull - K=4.0</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Output Power Pout (W)</label>
                  <input type="number" value={apPout} onChange={(e) => setApPout(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={apFsw} onChange={(e) => setApFsw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Flux Swing ΔB (T)</label>
                  <input type="number" step="0.05" value={apDb} onChange={(e) => setApDb(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Current Density J (A/mm²)</label>
                  <input type="number" step="0.5" value={apJ} onChange={(e) => setApJ(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
              </div>
            </div>
          </Card>
        );

      case 'result_ap':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Recommended Core Sizes</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-300 font-mono">
              {apError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{apError}</span>
                </div>
              )}
              {apRes && (
                <div className="space-y-4 flex flex-col h-full">
                  <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col flex-shrink-0">
                    <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Required Minimum AP Value</span>
                    <span className="text-xl font-bold text-cyan-400 mt-1">{(apRes.ap_calc_cm4 ?? 0).toFixed(4)} cm⁴</span>
                  </div>
                  <div className="flex flex-col gap-2 flex-1 overflow-hidden">
                    <div className="text-[10px] text-slate-400 font-bold flex-shrink-0">Matching Standard Cores:</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 overflow-y-auto scrollbar-thin pr-1">
                      {apRes.candidates?.map((cand: any, i: number) => (
                        <div 
                          key={i} 
                          className={`p-3 rounded-lg border text-xs flex flex-col transition-all duration-150 ${i === 0 ? 'bg-gradient-to-br from-emerald-950/30 to-slate-900/80 border-emerald-500/30' : 'bg-slate-900/40 border-slate-800'}`}
                        >
                          <div className="flex justify-between font-bold">
                            <span className="text-slate-200">{cand.name}</span>
                            <span className="text-cyan-400">AP={cand.ap_cm4?.toFixed(3)}</span>
                          </div>
                          <div className="text-[10px] text-slate-500 mt-1">
                            Ae={cand.ae_mm2}mm² | Aw={cand.aw_mm2}mm² | Ve={cand.ve_mm3}mm³
                          </div>
                          {i === 0 && <span className="text-[9px] text-emerald-400 font-semibold uppercase mt-1">⭐ Preferred</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        );

      case 'formula_ap':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <Info className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-white">AP Method Sizing Formulas</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-3 text-[11px] text-slate-350 leading-relaxed font-mono">
              <p>Area Product (AP) Core Geometric Sizing Equation:</p>
              <Latex math="A_p = A_e \cdot A_w = \frac{P_{out} \cdot 10^4}{K_{topo} \cdot f_{sw} \cdot \Delta B \cdot J \cdot K_u}" block />
              <p className="text-[10px] text-slate-500">Calculates minimum required area product based on power throughput, switching frequency, flux swing, and current density.</p>
            </div>
          </Card>
        );

      // --- Winding Fill Factor Cards ---
      case 'input_fill':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Bobbin & Winding Dimensions</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Bobbin Width W (mm)</label>
                  <input type="number" value={fillWinW} onChange={(e) => setFillWinW(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Bobbin Depth D (mm)</label>
                  <input type="number" value={fillWinD} onChange={(e) => setFillWinD(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Total Turns N (Ts)</label>
                  <input type="number" value={fillTurns} onChange={(e) => setFillTurns(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Wire Outer Diam. OD (mm)</label>
                  <input type="number" step="0.05" value={fillWireOd} onChange={(e) => setFillWireOd(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Parallel Strands</label>
                  <input type="number" value={fillStrands} onChange={(e) => setFillStrands(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Layer Tape Thickness (mm)</label>
                  <input type="number" step="0.01" value={fillTape} onChange={(e) => setFillTape(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
              </div>
            </div>
          </Card>
        );

      case 'result_fill':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Fill Factor & Build Height Results</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-350 font-mono">
              {fillError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{fillError}</span>
                </div>
              )}
              {fillRes && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400">Turns per Layer</span>
                      <span className="text-md font-bold text-slate-200 mt-0.5">{fillRes.turns_per_layer} turns/layer</span>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400">Required Layers</span>
                      <span className="text-md font-bold text-slate-200 mt-0.5">{fillRes.needed_layers} layers</span>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400">Build Height</span>
                      <span className="text-md font-bold text-cyan-400 mt-0.5">{(fillRes.build_height_mm ?? 0).toFixed(2)} mm</span>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400">Window Fill Factor</span>
                      <span className="text-md font-bold text-cyan-400 mt-0.5">{((fillRes.fill_factor ?? 0) * 100.0).toFixed(1)} %</span>
                    </div>
                  </div>

                  {fillRes.is_safe ? (
                    <div className="p-3 bg-emerald-950/20 border border-emerald-500/20 text-emerald-300 rounded-lg text-xs flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>Fill factor and build height are well within safe assembly margins.</span>
                    </div>
                  ) : (
                    <div className="p-3 bg-red-950/20 border border-red-500/30 text-red-200 rounded-lg text-[11px] flex flex-col gap-1">
                      <div className="flex items-center gap-1.5 font-bold text-red-400">
                        <ShieldAlert className="w-4 h-4 shrink-0" />
                        <span>⚠️ Bobbin Winding Overfill Warning!</span>
                      </div>
                      <p>Build height (with 1.15x packing factor) exceeds 85% of bobbin depth. Assembly interference or difficulty fitting into the core window will occur. Reduce wire gauge or use a larger bobbin.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        );

      // --- Core Loss Cards ---
      case 'input_core':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Magnetic Core Parameters & Material</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="flex flex-col gap-1">
                <label className="text-slate-400">Ferrite Material Preset</label>
                <select value={selectedMaterial} onChange={(e) => setSelectedMaterial(e.target.value)} className="neon-input">
                  <option value="PC40 (TDK)">PC40 (TDK)</option>
                  <option value="PC95 (TDK)">PC95 (TDK)</option>
                  <option value="3C90 (Ferroxcube)">3C90 (Ferroxcube)</option>
                  <option value="3C94 (Ferroxcube)">3C94 (Ferroxcube)</option>
                  <option value="N87 (Epcos)">N87 (Epcos)</option>
                  <option value="Custom">Custom</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Core Volume Ve (cm³)</label>
                  <input type="number" value={lossVol} onChange={(e) => setLossVol(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Operating Frequency fsw (kHz)</label>
                  <input type="number" value={lossFreq} onChange={(e) => setLossFreq(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">AC Flux Density Bac (T)</label>
                  <input type="number" step="0.01" value={lossB} onChange={(e) => setLossB(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Steinmetz Factor k</label>
                  <input type="number" step="0.001" value={lossK} onChange={(e) => setLossK(parseFloat(e.target.value) || 0)} disabled={selectedMaterial !== 'Custom'} className="neon-input disabled:opacity-50" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Frequency Exponent α</label>
                  <input type="number" step="0.01" value={lossAlpha} onChange={(e) => setLossAlpha(parseFloat(e.target.value) || 0)} disabled={selectedMaterial !== 'Custom'} className="neon-input disabled:opacity-50" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Flux Exponent β</label>
                  <input type="number" step="0.01" value={lossBeta} onChange={(e) => setLossBeta(parseFloat(e.target.value) || 0)} disabled={selectedMaterial !== 'Custom'} className="neon-input disabled:opacity-50" />
                </div>
              </div>
            </div>
          </Card>
        );

      case 'result_core':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Core Thermal Dissipation Results</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-350 font-mono">
              {lossError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{lossError}</span>
                </div>
              )}
              {lossRes && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col col-span-2">
                      <span className="text-[10px] text-slate-400 font-semibold">Volumetric Core Loss Density (Pv)</span>
                      <span className="text-xl font-bold text-cyan-400 mt-1">{(lossRes.pv_mw_cm3 ?? 0).toFixed(1)} mW/cm³</span>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col col-span-2">
                      <span className="text-[10px] text-slate-400 font-semibold">Total Core Heat Loss (P_core)</span>
                      <span className="text-xl font-bold text-purple-400 mt-1">{(lossRes.p_core_w ?? 0).toFixed(3)} W</span>
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-855 flex flex-col gap-1 text-[11px] text-slate-400">
                    <div className="font-semibold text-slate-300">Steinmetz Density Design Guideline:</div>
                    <p>It is generally recommended to keep volumetric core loss density Pv within <span className="text-cyan-400 font-bold">100 ~ 300 mW/cm³</span>. If excessive temperature rise occurs, select a lower-loss high-frequency material (such as PC95) or reduce AC flux excursion Bac.</p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        );

      // --- AC Winding Loss Cards ---
      case 'input_ac_loss':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Winding Conductor Parameters</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Winding Layers (m)</label>
                  <input type="number" value={acLayers} onChange={(e) => setAcLayers(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Switching Frequency fsw (kHz)</label>
                  <input type="number" value={acFreq} onChange={(e) => setAcFreq(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Conductor Strand Dia. (mm)</label>
                  <input type="number" step="0.05" value={acDia} onChange={(e) => setAcDia(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Porosity Factor (η)</label>
                  <input type="number" step="0.05" value={acPorosity} onChange={(e) => setAcPorosity(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
              </div>
            </div>
          </Card>
        );

      case 'result_ac_loss':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Proximity Effect & Dowell Factor</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-355 font-mono">
              {acError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{acError}</span>
                </div>
              )}
              {acRes && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400">Skin Depth (δ)</span>
                      <span className="text-sm font-bold text-slate-200 mt-1">{(acRes.skin_depth_mm ?? 0).toFixed(4)} mm</span>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[10px] text-slate-400">Normalized Height (Δ)</span>
                      <span className="text-sm font-bold text-slate-200 mt-1">{(acRes.phi ?? 0).toFixed(3)}</span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col col-span-2">
                      <span className="text-[10px] text-slate-400">AC Resistance Ratio (Fr = Rac/Rdc)</span>
                      <span className={`text-xl font-bold mt-1 ${acRes.fr > 3.0 ? 'text-red-400 animate-pulse' : acRes.fr > 1.5 ? 'text-yellow-400' : 'text-emerald-400'}`}>{(acRes.fr ?? 0).toFixed(2)}</span>
                    </div>
                  </div>
                  {acRes.fr > 3.0 ? (
                    <div className="p-3 rounded-lg bg-red-950/20 border border-red-500/30 text-red-200 text-[11px]">
                      ⚠️ <b>High Loss Warning:</b> Severe AC resistance multiplier. Use finer Litz strands or interleaved sandwich windings to reduce layer count m.
                    </div>
                  ) : acRes.fr > 1.5 ? (
                    <div className="p-3 rounded-lg bg-yellow-950/20 border border-yellow-500/30 text-yellow-300 text-[11px]">
                      ⚠️ <b>Design Caution:</b> Moderate AC resistance factor (Fr={(acRes.fr ?? 0).toFixed(2)}). Consider optimizing strand count or winding geometry.
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-emerald-355 text-[11px]">
                      ✅ <b>Design Optimized:</b> Skin and proximity losses are well controlled.
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        );

      case 'chart_ac_loss':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <LineChart className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-white">1kHz~10MHz AC Resistance Factor (Fr) Sweep</span>
            </div>
            <div className="flex-1 overflow-hidden bg-slate-950/60 rounded-xl border border-slate-850 h-[300px]">
              {acRes && (
                <ReactECharts notMerge={true} option={getAcLossChartOption()} style={{ height: '100%', width: '100%' }} />
              )}
            </div>
          </Card>
        );

      // --- Leakage Inductance Cards ---
      case 'input_leakage':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Leakage Inductance Geometry</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Total Turns N (Ts)</label>
                  <input type="number" value={lkTurns} onChange={(e) => setLkTurns(parseInt(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Mean Length Turn MLT (mm)</label>
                  <input type="number" value={lkMlt} onChange={(e) => setLkMlt(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Window Width bw (mm)</label>
                  <input type="number" value={lkBw} onChange={(e) => setLkBw(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Primary Height hp (mm)</label>
                  <input type="number" step="0.1" value={lkHp} onChange={(e) => setLkHp(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Secondary Height hs (mm)</label>
                  <input type="number" step="0.1" value={lkHs} onChange={(e) => setLkHs(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Insulation Thick tins (mm)</label>
                  <input type="number" step="0.05" value={lkTins} onChange={(e) => setLkTins(parseFloat(e.target.value) || 0)} className="neon-input" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-slate-400">Winding Build Arrangement</label>
                  <select 
                    value={lkIsSandwich ? 'sandwich' : 'ordinary'} 
                    onChange={(e) => setLkIsSandwich(e.target.value === 'sandwich')} 
                    className="neon-input w-full"
                  >
                    <option value="ordinary">Concentric Layered (K=1.0)</option>
                    <option value="sandwich">Primary-Secondary Sandwich (P/2-S-P/2)</option>
                  </select>
                </div>
                {lkIsSandwich && (
                  <div className="flex flex-col gap-1">
                    <label className="text-slate-400">Interleaving Sections m (K = 1/m²)</label>
                    <input type="number" min="2" max="10" value={lkInterleaveM} onChange={(e) => setLkInterleaveM(parseInt(e.target.value) || 2)} className="neon-input" />
                  </div>
                )}
              </div>
            </div>
          </Card>
        );

      case 'result_leakage':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Estimated Leakage Results</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-350 font-mono">
              {lkError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{lkError}</span>
                </div>
              )}
              {lkRes && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col">
                    <span className="text-xs text-slate-400 font-semibold uppercase">Estimated Primary Leakage (Lk)</span>
                    <span className="text-xl font-bold text-cyan-400 mt-1">{(lkRes.leakage_uh ?? 0).toFixed(3)} uH</span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-855 flex flex-col gap-1.5 text-xs text-slate-400">
                    <div className="font-semibold text-slate-300">Leakage & Resonant Design Notes:</div>
                    <p>Interleaved sandwich builds (P/2 - S - P/2) reduce leakage inductance to approximately 1/4 of concentric windings. In resonant topologies such as LLC and DAB, leakage inductance can serve as the integrated tank inductor, eliminating bulky external inductors.</p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        );

      // --- Curve Fitting Cards ---
      case 'input_fit':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-white">Datasheet Sample Data Points</span>
              </div>
              <div className="flex gap-2">
                <button onClick={handleAddFitRow} className="px-2 py-1 bg-cyan-600 hover:bg-cyan-500 rounded text-xs flex items-center gap-1 text-white border-0 cursor-pointer">
                  <Plus className="w-3 h-3" /> Row
                </button>
                <button onClick={handleClearFitTable} className="px-2 py-1 bg-red-650 hover:bg-red-600 rounded text-xs flex items-center gap-1 text-white border-0 cursor-pointer">
                  <Trash2 className="w-3 h-3" /> Clear
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-slate-300 text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800">
                      <th className="py-2 px-1">Freq f (kHz)</th>
                      <th className="py-2 px-1">Flux B (mT)</th>
                      <th className="py-2 px-1">Loss Pv (mW/cm³)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fitRows.map((row, i) => (
                      <tr key={i} className="border-b border-slate-900">
                        <td className="py-1.5 px-1">
                          <input 
                            type="number" 
                            value={row.f} 
                            onChange={(e) => {
                              const newRows = [...fitRows];
                              newRows[i].f = e.target.value;
                              setFitRows(newRows);
                            }} 
                            placeholder="f (kHz)" 
                            className="w-full bg-slate-950/60 border border-slate-850 rounded px-2 py-1 text-white outline-none text-xs" 
                          />
                        </td>
                        <td className="py-1.5 px-1">
                          <input 
                            type="number" 
                            value={row.b} 
                            onChange={(e) => {
                              const newRows = [...fitRows];
                              newRows[i].b = e.target.value;
                              setFitRows(newRows);
                            }} 
                            placeholder="B (mT)" 
                            className="w-full bg-slate-950/60 border border-slate-855 rounded px-2 py-1 text-white outline-none text-xs" 
                          />
                        </td>
                        <td className="py-1.5 px-1">
                          <input 
                            type="number" 
                            value={row.pv} 
                            onChange={(e) => {
                              const newRows = [...fitRows];
                              newRows[i].pv = e.target.value;
                              setFitRows(newRows);
                            }} 
                            placeholder="Pv" 
                            className="w-full bg-slate-950/60 border border-slate-855 rounded px-2 py-1 text-white outline-none text-xs" 
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <button onClick={handleFitCalculate} className="w-full py-2 bg-purple-600 hover:bg-purple-500 font-semibold rounded text-xs text-white border-0 cursor-pointer flex-shrink-0">
                Fit Steinmetz Coefficients
              </button>
            </div>
          </Card>
        );

      case 'result_fit':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden font-mono">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <span className="text-xs font-bold text-white">Least-Squares Fit Results</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin pr-1.5 space-y-4 text-xs text-slate-350">
              {fitError && (
                <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-200 rounded-lg text-xs">
                  <span>{fitError}</span>
                </div>
              )}
              {fitRes ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[9px] text-slate-500 uppercase">Factor k</span>
                      <div className="text-xs font-bold text-cyan-400 mt-1">{(fitRes.k ?? 0).toExponential(4)}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[9px] text-slate-500 uppercase">Fit Error (MAPE)</span>
                      <div className="text-xs font-bold text-cyan-400 mt-1">{(fitRes.mape ?? 0).toFixed(2)} %</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[9px] text-slate-500 uppercase">Freq Exponent α (Alpha)</span>
                      <div className="text-xs font-bold text-purple-400 mt-1">{(fitRes.alpha ?? 0).toFixed(4)}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-[9px] text-slate-500 uppercase">Flux Exponent β (Beta)</span>
                      <div className="text-xs font-bold text-purple-400 mt-1">{(fitRes.beta ?? 0).toFixed(4)}</div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-855 flex flex-col gap-2">
                    <div className="font-semibold text-slate-300 border-b border-slate-800 pb-1 mb-1">Operating Point Verification</div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex flex-col">
                        <label className="text-[9px] text-slate-500">Test Freq f (kHz)</label>
                        <input type="number" value={valF} onChange={(e) => setValF(parseFloat(e.target.value) || 0)} className="neon-input py-1 px-2 text-xs mt-1" />
                      </div>
                      <div className="flex flex-col">
                        <label className="text-[9px] text-slate-500">Test Flux B (mT)</label>
                        <input type="number" value={valB} onChange={(e) => setValB(parseFloat(e.target.value) || 0)} className="neon-input py-1 px-2 text-xs mt-1" />
                      </div>
                    </div>
                    {valPv !== null && (
                      <div className="mt-2 text-xs">
                        Predicted Loss Pv: <span className="text-emerald-400 font-bold">{valPv.toFixed(2)} mW/cm³</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex h-32 items-center justify-center text-slate-500 text-xs">
                  Enter sample points and click fit calculation.
                </div>
              )}
            </div>
          </Card>
        );

      case 'chart_fit':
        return (
          <Card className="h-full flex flex-col bg-[#0b0f19]/60 border-slate-800/80 p-5 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5 mb-4 flex-shrink-0">
              <LineChart className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-white">Steinmetz Measured Data vs. Fitted Curve</span>
            </div>
            <div className="flex-1 overflow-hidden bg-slate-950/60 rounded-xl border border-slate-850 h-[300px]">
              {fitRes && (
                <ReactECharts notMerge={true} option={getFitChartOption()} style={{ height: '100%', width: '100%' }} />
              )}
            </div>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Top Header Section */}
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
            <h1 className="text-base font-bold text-white tracking-tight">High-Frequency Integrated Transformer Design</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Design forward, flyback, and resonant LLC transformers, evaluating AP sizing, AC winding proximity factors, and integrated leakage inductance.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetLayout}
            className="text-xs text-slate-350 border-slate-805 hover:bg-slate-800 hover:text-white flex items-center gap-1 bg-transparent"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Layout
          </Button>
        </div>
      </div>

      {/* Subtabs Navigation Selector */}
      <div className="flex items-center gap-1 p-2 bg-[#050914] border-b border-slate-850/60 overflow-x-auto scrollbar-none flex-shrink-0">
        {[
          { id: 'forward', label: 'Forward / Bridge', color: 'text-cyan-400' },
          { id: 'flyback', label: 'Isolated Flyback', color: 'text-cyan-400' },
          { id: 'llc_integration', label: 'LLC Integration', color: 'text-cyan-400' },
          { id: 'ap', label: 'AP Core Sizing', color: 'text-purple-400' },
          { id: 'fill', label: 'Fill & Build Height', color: 'text-purple-400' },
          { id: 'core_loss', label: 'Core Loss', color: 'text-purple-400' },
          { id: 'ac_loss', label: 'Winding Fr Loss', color: 'text-purple-400' },
          { id: 'leakage', label: 'Primary Leakage', color: 'text-purple-400' },
          { id: 'fit', label: 'Steinmetz Fit', color: 'text-purple-400' }
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as TabType)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all border-0 cursor-pointer ${
              activeTab === t.id
                ? 'bg-slate-800 text-white shadow-md border-l-2 border-cyan-500'
                : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 bg-transparent'
            }`}
          >
            <span className={t.color}>•</span> {t.label}
          </button>
        ))}
      </div>

      {/* Main DragDeck Viewport Container */}
      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 p-3 pt-0 min-h-0">
        <DragDeck
          isDesktop={isDesktop}
          leftSpan={leftSpan}
          rightSpan={rightSpan}
          leftCards={leftCards}
          rightCards={rightCards}
          draggedKey={draggedKey}
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
              {renderCardContent(key)}
            </DragCard>
          )}
        />
      </div>
    </div>
  );
}

const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: string; size?: string }
>(({ className, variant, size, ...props }, ref) => {
  const base = "inline-flex items-center justify-center rounded-lg font-medium transition-colors outline-none border-0 cursor-pointer";
  const sizeClass = size === 'sm' ? "h-8 px-3 text-xs" : "h-10 px-4 py-2 text-sm";
  const variantClass = variant === 'ghost' 
    ? "bg-transparent hover:bg-slate-800 text-slate-400 hover:text-white" 
    : "border border-slate-800 bg-transparent hover:bg-slate-800 text-slate-300";
  return (
    <button
      ref={ref}
      className={`${base} ${sizeClass} ${variantClass} ${className || ''}`}
      {...props}
    />
  );
});
Button.displayName = "Button";
