import { useTabHistoryState } from '../lib/tabHistory';
import { apiFetch } from '../lib/api';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
import { Button } from './ui/Button';
import { Card, CardHeader, CardContent } from './ui/Card';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import {
  ArrowLeft,
  RotateCcw
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
  return <span ref={containerRef} className={block ? "block my-2 overflow-x-auto text-center" : "inline-block"} />;
};

export default function PowerAc3PhPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<'params' | 'pfc' | 'yd' | 'pll'>('params', 'activeTab');
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
    handleDropOnColumn,
    handleResetLayout
  } = useDragDeckLayout({
    panelKey: 'layout_powerac3phpanel_v4_' + activeTab,
    defaultCards: ['input', 'results', 'visual_panel'],
    defaultColumns: { input: 'left', results: 'right', visual_panel: 'right' },
    defaultSpans: { input: 4, results: 8, visual_panel: 8 },
    defaultHeights: { input: 820, results: 320, visual_panel: 550 }
  });

  // Tab 1: Parameters State
  const [vLl, setVLl] = useState<number>(380);
  const [iLine, setILine] = useState<number>(10);
  const [pf, setPf] = useState<number>(0.8);
  const [freq, setFreq] = useState<number>(50);
  const [connection, setConnection] = useState<string>('star');

  // Tab 1 Results
  const [paramsRes, setParamsRes] = useState<{
    v_ph: number;
    i_ph: number;
    s_val_kva: number;
    p_val_kw: number;
    q_val_kvar: number;
    z_ph_ohm: number;
    r_ph_ohm: number;
    x_ph_ohm: number;
    equivalent_l_mh: number;
    equivalent_c_uf: number;
  } | null>(null);

  // Tab 2: PFC State
  const [pfcP, setPfcP] = useState<number>(10);
  const [pfcV, setPfcV] = useState<number>(380);
  const [pfcOld, setPfcOld] = useState<number>(0.8);
  const [pfcTarget, setPfcTarget] = useState<number>(0.95);
  const [pfcFreq, setPfcFreq] = useState<number>(50);
  const [pfcConn, setPfcConn] = useState<string>('delta');
  const [pfcWarning, setPfcWarning] = useState<string | null>(null);

  // Tab 2 Results
  const [pfcRes, setPfcRes] = useState<{
    q_c_kvar: number;
    c_phase_uf: number;
    v_cap_rms: number;
    recommended_voltage_rating: number;
  } | null>(null);

  // Tab 3: Y-Delta State
  const [ydZVal, setYdZVal] = useState<number>(10);
  const [ydDir, setYdDir] = useState<string>('y_to_delta');

  // Tab 3 Results
  const [ydRes, setYdRes] = useState<{
    z_out_ohm: number;
  } | null>(null);

  // Tab 4: PLL & Transform State
  const [tfA, setTfA] = useState<number>(220);
  const [tfB, setTfB] = useState<number>(-110);
  const [tfC, setTfC] = useState<number>(-110);
  const [tfTheta, setTfTheta] = useState<number>(30);
  const [clarkeMode, setClarkeMode] = useState<string>('amplitude_invariant');
  const [pllVm, setPllVm] = useState<number>(311.12);
  const [pllFbw, setPllFbw] = useState<number>(20);
  const [pllZeta, setPllZeta] = useState<number>(0.707);

  // Tab 4 Results
  const [tfRes, setTfRes] = useState<{
    alpha: number;
    beta: number;
    d: number;
    q: number;
  } | null>(null);
  const [pllRes, setPllRes] = useState<{
    kp: number;
    ki: number;
    drc_warnings?: string[];
  } | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // API Call - Tab 1
  const handleParamsCalculate = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_ac_3ph/params', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v_ll: vLl,
          i_line: iLine,
          pf: pf,
          freq: freq,
          connection: connection
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const data = await response.json();
      if (activeTabRef.current !== 'params') return;
      setParamsRes(data);
    } catch (e: any) {
      if (activeTabRef.current !== 'params') return;
      setError(e.message);
    }
  };

  // API Call - Tab 2
  const handlePfcCalculate = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_ac_3ph/pfc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          p_kw: pfcP,
          v_ll: pfcV,
          pf_old: pfcOld,
          pf_target: pfcTarget,
          freq: pfcFreq,
          connection: pfcConn
        })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const data = await response.json();
      if (activeTabRef.current !== 'pfc') return;
      setPfcRes(data);
      if (pfcOld >= pfcTarget) {
        setPfcWarning("Target power factor must be greater than current power factor.");
      } else {
        setPfcWarning(null);
      }
    } catch (e: any) {
      if (activeTabRef.current !== 'pfc') return;
      setError(e.message);
    }
  };

  // API Call - Tab 3
  const handleYdCalculate = async () => {
    try {
      const response = await apiFetch('/api/calculate/power_ac_3ph/yd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ z_val: ydZVal, direction: ydDir })
      });
      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const data = await response.json();
      if (activeTabRef.current !== 'yd') return;
      setYdRes(data);
    } catch (e: any) {
      if (activeTabRef.current !== 'yd') return;
      setError(e.message);
    }
  };

  // API Call - Tab 4 (Coordinate & PLL)
  const handlePllCalculate = async () => {
    try {
      const resTf = await apiFetch('/api/calculate/power_ac_3ph/coordinate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ a: tfA, b: tfB, c: tfC, theta_deg: tfTheta, mode: clarkeMode })
      });
      if (!resTf.ok) {
        const errDetail = await resTf.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const dataTf = await resTf.json();
      if (activeTabRef.current !== 'pll') return;
      setTfRes(dataTf);

      const resPll = await apiFetch('/api/calculate/power_ac_3ph/pll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ v_m: pllVm, f_bw: pllFbw, zeta: pllZeta })
      });
      if (!resPll.ok) {
        const errDetail = await resPll.json().catch(() => ({}));
        throw new Error(errDetail.detail || 'Calculation failed, please check parameter validity');
      }
      const dataPll = await resPll.json();
      if (activeTabRef.current !== 'pll') return;
      setPllRes(dataPll);
    } catch (e: any) {
      if (activeTabRef.current !== 'pll') return;
      setError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'params') handleParamsCalculate();
  }, [vLl, iLine, pf, freq, connection, activeTab]);

  useEffect(() => {
    if (activeTab === 'pfc') handlePfcCalculate();
  }, [pfcP, pfcV, pfcOld, pfcTarget, pfcFreq, pfcConn, activeTab]);

  useEffect(() => {
    if (activeTab === 'yd') handleYdCalculate();
  }, [ydZVal, ydDir, activeTab]);

  useEffect(() => {
    if (activeTab === 'pll') handlePllCalculate();
  }, [tfA, tfB, tfC, tfTheta, clarkeMode, pllVm, pllFbw, pllZeta, activeTab]);

  const getPllStepResponseData = () => {
    if (!pllRes) return [];
    const kp = pllRes.kp;
    const ki = pllRes.ki;
    
    const dt = 0.0001;
    const tMax = 0.10;
    const steps = Math.ceil(tMax / dt);
    const points = [];
    
    let theta_in = 0.5236; 
    let theta_out = 0;
    let freq_out = 0;
    let integral = 0;
    
    for (let i = 0; i < steps; i++) {
      const time_ms = i * dt * 1000;
      const error = theta_in - theta_out;
      integral += error * dt;
      const pi_out = kp * error + ki * integral;
      freq_out = pi_out;
      theta_out += freq_out * dt;
      
      if (i % 5 === 0) {
        points.push({
          time_ms,
          phase_err_deg: (error * 180.0 / Math.PI),
          freq_dev_hz: freq_out / (2.0 * Math.PI)
        });
      }
    }
    return points;
  };

  const getPllChartOption = () => {
    const data = getPllStepResponseData();
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const t = params[0].axisValue;
          const pe = params[0].data[1];
          const fe = params[1].data[1];
          return `Time: ${parseFloat(t).toFixed(1)} ms<br/>Phase Error: ${parseFloat(pe).toFixed(2)} °<br/>Frequency Deviation: ${parseFloat(fe).toFixed(2)} Hz`;
        }
      },
      legend: {
        textStyle: { color: '#94a3b8', fontSize: 10 },
        data: ['Phase Error (deg)', 'Frequency Deviation (Hz)'],
        top: 0
      },
      grid: { left: '12%', right: '12%', top: '22%', bottom: '18%', containLabel: true },
      xAxis: {
        type: 'value',
        name: 'Time (ms)',
        nameTextStyle: { color: '#94a3b8', fontSize: 9 },
        axisLabel: { color: '#94a3b8', fontSize: 9 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      yAxis: [
        {
          type: 'value',
          name: 'Phase (°)',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 },
          axisLabel: { color: '#ef4444', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
        },
        {
          type: 'value',
          name: 'Frequency (Hz)',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 },
          axisLabel: { color: '#0ea5e9', fontSize: 9 },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Phase Error (deg)',
          type: 'line',
          data: data.map(d => [d.time_ms, d.phase_err_deg]),
          lineStyle: { color: '#ef4444', width: 2 },
          showSymbol: false
        },
        {
          name: 'Frequency Deviation (Hz)',
          type: 'line',
          yAxisIndex: 1,
          data: data.map(d => [d.time_ms, d.freq_dev_hz]),
          lineStyle: { color: '#0ea5e9', width: 2 },
          showSymbol: false
        }
      ]
    };
  };

  const renderVisualPanel = () => {
    switch (activeTab) {
      case 'params':
        return (
          <div className="space-y-4 flex flex-col">
            <Card className="bg-slate-900/40 border-slate-800 p-4 flex-shrink-0">
              <span className="text-xs font-bold text-slate-300 block border-b border-slate-800 pb-1.5 mb-2.5">Three-Phase Fundamental Electrical Derivations</span>
              <div className="grid grid-cols-2 gap-4 text-slate-400 text-xs">
                <div className="space-y-2">
                  <div>Phase Voltage:</div>
                  <Latex math={"V_{ph} = \\frac{V_{LL}}{\\sqrt{3}} \\approx 0.577 \\cdot V_{LL}"} />
                </div>
                <div className="space-y-2">
                  <div>Symmetric 3-Phase Apparent Power:</div>
                  <Latex math={"S = \\sqrt{3} \\cdot V_{LL} \\cdot I_{line}"} />
                </div>
                <div className="space-y-2">
                  <div>Symmetric 3-Phase Active Power:</div>
                  <Latex math={"P = S \\cdot \\cos\\varphi = \\sqrt{3} V_{LL} I_{line} \\cos\\varphi"} />
                </div>
                <div className="space-y-2">
                  <div>Per-Phase Equivalent Impedance:</div>
                  <Latex math={"Z_{ph} = \\frac{V_{ph}}{I_{ph}}, \\quad X_{ph} = \\sqrt{Z_{ph}^2 - R_{ph}^2}"} />
                </div>
              </div>
            </Card>
            
            <div className="flex-1 min-h-[250px] bg-slate-950/60 rounded-xl border border-slate-850 flex flex-col items-center justify-center p-4">
              <span className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wide">Symmetric 3-Phase Phasor Voltage & Line Vector Diagram</span>
              <svg viewBox="0 0 320 200" className="w-full max-w-[280px] h-auto">
                <circle cx="160" cy="100" r="70" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
                <line x1="160" y1="30" x2="160" y2="170" stroke="rgba(255,255,255,0.06)" strokeWidth="0.8" strokeDasharray="2,2" />
                <line x1="90" y1="100" x2="230" y2="100" stroke="rgba(255,255,255,0.06)" strokeWidth="0.8" strokeDasharray="2,2" />
                
                {/* Va vector (0 deg) */}
                <line x1="160" y1="100" x2="225" y2="100" stroke="#f87171" strokeWidth="2" markerEnd="url(#va-arrow)" />
                <text x="232" y="103" fill="#f87171" fontSize="9" fontWeight="bold">Va</text>
                
                {/* Vb vector (-120 deg) */}
                <line x1="160" y1="100" x2="125" y2="160.6" stroke="#60a5fa" strokeWidth="2" markerEnd="url(#vb-arrow)" />
                <text x="115" y="172" fill="#60a5fa" fontSize="9" fontWeight="bold">Vb</text>
                
                {/* Vc vector (+120 deg) */}
                <line x1="160" y1="100" x2="125" y2="39.4" stroke="#34d399" strokeWidth="2" markerEnd="url(#vc-arrow)" />
                <text x="115" y="32" fill="#34d399" fontSize="9" fontWeight="bold">Vc</text>

                {/* Vab line */}
                <line x1="225" y1="100" x2="125" y2="160.6" stroke="#a78bfa" strokeWidth="1.2" strokeDasharray="3,3" />
                <text x="185" y="142" fill="#a78bfa" fontSize="7" fontWeight="semibold">Vab = √3 Va</text>

                {/* Vbc line */}
                <line x1="125" y1="160.6" x2="125" y2="39.4" stroke="#a78bfa" strokeWidth="1.2" strokeDasharray="3,3" />
                <text x="92" y="104" fill="#a78bfa" fontSize="7" fontWeight="semibold">Vbc</text>

                {/* Vca line */}
                <line x1="125" y1="39.4" x2="225" y2="100" stroke="#a78bfa" strokeWidth="1.2" strokeDasharray="3,3" />
                <text x="185" y="66" fill="#a78bfa" fontSize="7" fontWeight="semibold">Vca</text>

                <defs>
                  <marker id="va-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 6 5 L 0 8.5 z" fill="#f87171" />
                  </marker>
                  <marker id="vb-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 6 5 L 0 8.5 z" fill="#60a5fa" />
                  </marker>
                  <marker id="vc-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 6 5 L 0 8.5 z" fill="#34d399" />
                  </marker>
                </defs>
              </svg>
            </div>
          </div>
        );

      case 'pfc':
        return (
          <div className="space-y-4 flex flex-col">
            <Card className="bg-slate-900/40 border-slate-800 p-4 flex-shrink-0">
              <span className="text-xs font-bold text-slate-300 block border-b border-slate-800 pb-1.5 mb-2.5">Power Factor Correction Sizing Equations</span>
              <div className="grid grid-cols-2 gap-4 text-slate-400 text-xs">
                <div className="space-y-2 col-span-2">
                  <div>Required Reactive Power Qc (kvar):</div>
                  <Latex math={"Q_c = P \\cdot (\\tan\\varphi_1 - \\tan\\varphi_2) = P \\cdot \\left(\\frac{\\sqrt{1-PF_1^2}}{PF_1} - \\frac{\\sqrt{1-PF_2^2}}{PF_2}\\right)"} />
                </div>
                <div className="space-y-2">
                  <div>Delta Phase Capacitance (C_Δ):</div>
                  <Latex math={"C_{\\Delta} = \\frac{Q_c \\cdot 10^9}{3 \\cdot 2\\pi f \\cdot V_{LL}^2}"} />
                </div>
                <div className="space-y-2">
                  <div>Star Phase Capacitance (C_Y):</div>
                  <Latex math={"C_Y = \\frac{Q_c \\cdot 10^9}{2\\pi f \\cdot V_{LL}^2} = 3 \\cdot C_{\\Delta}"} />
                </div>
              </div>
            </Card>

            <div className="flex-1 min-h-[250px] bg-slate-950/60 rounded-xl border border-slate-850 flex flex-col items-center justify-center p-4">
              <span className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wide">Power Factor Triangle & Capacitive Sizing Diagram</span>
              <svg viewBox="0 0 320 200" className="w-full max-w-[280px] h-auto">
                <line x1="40" y1="160" x2="260" y2="160" stroke="#94a3b8" strokeWidth="1.5" markerEnd="url(#p-arrow)" />
                <text x="264" y="163" fill="#cbd5e1" fontSize="8" fontWeight="bold">Active P</text>
                
                <line x1="220" y1="160" x2="220" y2="40" stroke="#f87171" strokeWidth="1.2" strokeDasharray="3,3" />
                <line x1="220" y1="160" x2="220" y2="100" stroke="#34d399" strokeWidth="1.5" />
                
                <line x1="40" y1="160" x2="220" y2="40" stroke="#ef4444" strokeWidth="2" markerEnd="url(#s1-arrow)" />
                <line x1="40" y1="160" x2="220" y2="100" stroke="#10b981" strokeWidth="2" markerEnd="url(#s2-arrow)" />

                {/* Arc for phi1 */}
                <path d="M 70 160 A 30 30 0 0 0 65.5 149.3" fill="none" stroke="#ef4444" strokeWidth="1" />
                <text x="73" y="152" fill="#ef4444" fontSize="7">φ1</text>

                {/* Arc for phi2 */}
                <path d="M 90 160 A 50 50 0 0 0 84.2 143.5" fill="none" stroke="#10b981" strokeWidth="1" />
                <text x="94" y="156" fill="#10b981" fontSize="7">φ2</text>

                <text x="110" y="86" fill="#ef4444" fontSize="8" fontWeight="bold">Initial S1</text>
                <text x="125" y="125" fill="#10b981" fontSize="8" fontWeight="bold">Compensated S2</text>
                
                <text x="228" y="134" fill="#34d399" fontSize="8" fontWeight="semibold">Remaining Q2</text>
                <text x="228" y="70" fill="#f87171" fontSize="8" fontWeight="semibold">Initial Q1</text>

                {/* Qc double-headed arrow */}
                <line x1="245" y1="100" x2="245" y2="40" stroke="#a78bfa" strokeWidth="1.5" markerEnd="url(#qc-up)" markerStart="url(#qc-down)" />
                <text x="252" y="74" fill="#a78bfa" fontSize="8" fontWeight="bold">Qc (Comp)</text>

                <defs>
                  <marker id="p-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 6 5 L 0 8.5 z" fill="#94a3b8" />
                  </marker>
                  <marker id="s1-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 6 5 L 0 8.5 z" fill="#ef4444" />
                  </marker>
                  <marker id="s2-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 1.5 L 6 5 L 0 8.5 z" fill="#10b981" />
                  </marker>
                  <marker id="qc-up" viewBox="0 0 10 10" refX="5" refY="2" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                    <path d="M 0 8 L 5 2 L 10 8 z" fill="#a78bfa" />
                  </marker>
                  <marker id="qc-down" viewBox="0 0 10 10" refX="5" refY="8" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                    <path d="M 0 2 L 5 8 L 10 2 z" fill="#a78bfa" />
                  </marker>
                </defs>
              </svg>
            </div>
          </div>
        );

      case 'yd':
        return (
          <div className="space-y-4 flex flex-col">
            <Card className="bg-slate-900/40 border-slate-800 p-4 flex-shrink-0">
              <span className="text-xs font-bold text-slate-300 block border-b border-slate-800 pb-1.5 mb-2.5">Star-Delta (Y-Δ) Equivalent Impedance Conversion Equations</span>
              <div className="grid grid-cols-2 gap-4 text-slate-400 text-xs">
                <div className="space-y-2 col-span-2">
                  <div>In symmetric three-phase balanced networks, equivalent impedance satisfies:</div>
                </div>
                <div className="space-y-2">
                  <div>Star (Y) to Delta (Δ):</div>
                  <Latex math={"Z_{\\Delta} = 3 \\cdot Z_Y"} />
                </div>
                <div className="space-y-2">
                  <div>Delta (Δ) to Star (Y):</div>
                  <Latex math={"Z_Y = \\frac{Z_{\\Delta}}{3}"} />
                </div>
              </div>
            </Card>

            <div className="flex-1 min-h-[250px] bg-slate-950/60 rounded-xl border border-slate-850 flex flex-col items-center justify-center p-4">
              <span className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-wide">Y & Δ Balanced Load Transformation Equivalent Circuits</span>
              <svg viewBox="0 0 320 160" className="w-full max-w-[280px] h-auto">
                {/* Left Y Load */}
                <g transform="translate(10, 0)">
                  <text x="65" y="15" fill="#e2e8f0" fontSize="8" fontWeight="bold" textAnchor="middle">Star (Y)</text>
                  <circle cx="65" cy="85" r="3" fill="#cbd5e1" /> 
                  <text x="71" y="88" fill="#94a3b8" fontSize="7">N</text>
                  
                  {/* Resistor A */}
                  <line x1="65" y1="35" x2="65" y2="85" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="3,1" />
                  <rect x="61" y="50" width="8" height="18" fill="#1e1e38" stroke="#a78bfa" strokeWidth="1" />
                  <text x="73" y="61" fill="#a78bfa" fontSize="8">Zy</text>
                  <circle cx="65" cy="35" r="2.5" fill="#f87171" />
                  <text x="65" y="29" fill="#f87171" fontSize="8" textAnchor="middle">A</text>

                  {/* Resistor B */}
                  <line x1="65" y1="85" x2="25" y2="120" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="3,1" />
                  <g transform="translate(45, 102.5) rotate(41.2)">
                    <rect x="-4" y="-9" width="8" height="18" fill="#1e1e38" stroke="#a78bfa" strokeWidth="1" />
                  </g>
                  <circle cx="25" cy="120" r="2.5" fill="#60a5fa" />
                  <text x="20" y="131" fill="#60a5fa" fontSize="8">B</text>

                  {/* Resistor C */}
                  <line x1="65" y1="85" x2="105" y2="120" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="3,1" />
                  <g transform="translate(85, 102.5) rotate(-41.2)">
                    <rect x="-4" y="-9" width="8" height="18" fill="#1e1e38" stroke="#a78bfa" strokeWidth="1" />
                  </g>
                  <circle cx="105" cy="120" r="2.5" fill="#34d399" />
                  <text x="105" y="131" fill="#34d399" fontSize="8">C</text>
                </g>

                {/* Transition Arrow */}
                <path d="M 150 85 L 170 85" stroke="#475569" strokeWidth="2" markerEnd="url(#trans-arrow)" />
                <text x="160" y="78" fill="#94a3b8" fontSize="7" textAnchor="middle">Equiv</text>

                {/* Right Delta Load */}
                <g transform="translate(180, 0)">
                  <text x="65" y="15" fill="#e2e8f0" fontSize="8" fontWeight="bold" textAnchor="middle">Delta (Δ)</text>
                  
                  {/* Node A */}
                  <circle cx="65" cy="35" r="2.5" fill="#f87171" />
                  <text x="65" y="29" fill="#f87171" fontSize="8" textAnchor="middle">A</text>

                  {/* Node B */}
                  <circle cx="25" cy="120" r="2.5" fill="#60a5fa" />
                  <text x="20" y="131" fill="#60a5fa" fontSize="8">B</text>

                  {/* Node C */}
                  <circle cx="105" cy="120" r="2.5" fill="#34d399" />
                  <text x="105" y="131" fill="#34d399" fontSize="8">C</text>

                  {/* Resistor AB */}
                  <line x1="65" y1="35" x2="25" y2="120" stroke="#f472b6" strokeWidth="1.5" />
                  <g transform="translate(45, 77.5) rotate(25.2)">
                    <rect x="-4" y="-9" width="8" height="18" fill="#1e1e38" stroke="#f472b6" strokeWidth="1" />
                    <text x="7" y="3" fill="#f472b6" fontSize="7" transform="rotate(-25.2)">ZΔ</text>
                  </g>

                  {/* Resistor AC */}
                  <line x1="65" y1="35" x2="105" y2="120" stroke="#f472b6" strokeWidth="1.5" />
                  <g transform="translate(85, 77.5) rotate(-25.2)">
                    <rect x="-4" y="-9" width="8" height="18" fill="#f472b6" stroke="#f472b6" strokeWidth="1" />
                  </g>

                  {/* Resistor BC */}
                  <line x1="25" y1="120" x2="105" y2="120" stroke="#f472b6" strokeWidth="1.5" />
                  <g transform="translate(65, 120)">
                    <rect x="-9" y="-4" width="18" height="8" fill="#1e1e38" stroke="#f472b6" strokeWidth="1" />
                  </g>
                </g>

                <defs>
                  <marker id="trans-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                    <path d="M 0 2 L 6 5 L 0 8 z" fill="#475569" />
                  </marker>
                </defs>
              </svg>
            </div>
          </div>
        );

      case 'pll':
        return (
          <div className="space-y-4 flex flex-col">
            <Card className="bg-slate-900/40 border-slate-800 p-4 flex-shrink-0">
              <span className="text-xs font-bold text-slate-300 block border-b border-slate-800 pb-1.5 mb-2.5">Three-Phase Clarke / Park Transforms & PI Phase-Locked Loop Tuning</span>
              <div className="grid grid-cols-2 gap-4 text-slate-400 text-xs">
                <div className="space-y-2">
                  <div>Clarke 2-Phase Stationary Projection (Amplitude Invariant):</div>
                  <Latex math={"u_\\alpha = \\frac{2}{3}\\left(u_a - \\frac{1}{2}u_b - \\frac{1}{2}u_c\\right)"} block={true} />
                  <Latex math={"u_\\beta = \\frac{\\sqrt{3}}{3}(u_b - u_c)"} block={true} />
                </div>
                <div className="space-y-2">
                  <div>Park Rotating dq Frame & Loop Parameters:</div>
                  <Latex math={"u_q = -u_\\alpha \\sin\\theta + u_\\beta \\cos\\theta"} block={true} />
                  <Latex math={"K_p = \\frac{2\\zeta\\omega_n}{V_m}, \\quad K_i = \\frac{\\omega_n^2}{V_m}"} block={true} />
                </div>
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-slate-950/60 rounded-xl border border-slate-850 flex flex-col items-center justify-center p-3 min-h-[220px]">
                <span className="text-[9px] font-bold text-slate-400 mb-1.5 uppercase tracking-wide">Three-Phase SRF-PLL Control Loop Block Diagram</span>
                <svg viewBox="0 0 240 100" className="w-full h-auto">
                  {/* input u_abc */}
                  <text x="5" y="44" fill="#f87171" fontSize="7" fontWeight="bold">u_abc</text>
                  <line x1="8" y1="50" x2="35" y2="50" stroke="#f87171" strokeWidth="1" markerEnd="url(#pll-arrow)" />

                  {/* abc -> dq */}
                  <rect x="35" y="38" width="40" height="24" rx="2" fill="#1e293b" stroke="#38bdf8" strokeWidth="1" />
                  <text x="55" y="52" fill="#38bdf8" fontSize="7" fontWeight="bold" textAnchor="middle">abc/dq</text>
                  
                  {/* uq error */}
                  <line x1="75" y1="50" x2="100" y2="50" stroke="#cbd5e1" strokeWidth="1" markerEnd="url(#pll-arrow)" />
                  <text x="84" y="44" fill="#cbd5e1" fontSize="7">uq</text>
                  
                  {/* PI Controller */}
                  <rect x="100" y="38" width="45" height="24" rx="2" fill="#1e293b" stroke="#a78bfa" strokeWidth="1" />
                  <text x="122" y="52" fill="#a78bfa" fontSize="7" fontWeight="bold" textAnchor="middle">Kp + Ki/s</text>

                  {/* delta_w to w_grid */}
                  <line x1="145" y1="50" x2="170" y2="50" stroke="#cbd5e1" strokeWidth="1" markerEnd="url(#pll-arrow)" />
                  
                  {/* VCO integrator 1/s */}
                  <rect x="170" y="38" width="30" height="24" rx="2" fill="#1e293b" stroke="#34d399" strokeWidth="1" />
                  <text x="185" y="52" fill="#34d399" fontSize="8" fontWeight="bold" textAnchor="middle">1/s</text>

                  {/* output phase theta */}
                  <line x1="200" y1="50" x2="225" y2="50" stroke="#34d399" strokeWidth="1" markerEnd="url(#pll-arrow)" />
                  <text x="227" y="52" fill="#34d399" fontSize="8" fontWeight="bold">θ</text>

                  {/* Feedback path */}
                  <line x1="210" y1="50" x2="210" y2="80" stroke="#94a3b8" strokeWidth="0.8" />
                  <line x1="210" y1="80" x2="55" y2="80" stroke="#94a3b8" strokeWidth="0.8" />
                  <line x1="55" y1="80" x2="55" y2="62" stroke="#94a3b8" strokeWidth="0.8" markerEnd="url(#pll-arrow)" />

                  <defs>
                    <marker id="pll-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                      <path d="M 0 1.5 L 6 5 L 0 8.5 z" fill="#cbd5e1" />
                    </marker>
                  </defs>
                </svg>
              </div>

              <div className="bg-slate-950/60 rounded-xl border border-slate-855 flex flex-col p-2 h-[220px]">
                {pllRes && (
                  <ReactECharts notMerge={true} option={getPllChartOption()} style={{ height: '100%', width: '100%' }} />
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const renderInput = () => {
    switch (activeTab) {
      case 'params':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Three-Phase Electrical Parameters</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Line Voltage (V)</label>
                  <input type="number" value={vLl} onChange={(e) => setVLl(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Line Current (A)</label>
                  <input type="number" value={iLine} onChange={(e) => setILine(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Power Factor</label>
                  <input type="number" step="0.05" value={pf} onChange={(e) => setPf(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Grid Frequency (Hz)</label>
                  <input type="number" value={freq} onChange={(e) => setFreq(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1 col-span-2">
                  <label className="text-[9px] text-slate-400">Connection Topology</label>
                  <select value={connection} onChange={(e) => setConnection(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                    <option value="star">Star Connection (Y)</option>
                    <option value="delta">Delta Connection (Δ)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        );

      case 'pfc':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Active Power & Voltage</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Active Power (kW)</label>
                  <input type="number" value={pfcP} onChange={(e) => setPfcP(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Line Voltage (V)</label>
                  <input type="number" value={pfcV} onChange={(e) => setPfcV(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Current Power Factor</label>
                  <input type="number" step="0.05" value={pfcOld} onChange={(e) => setPfcOld(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Target Power Factor</label>
                  <input type="number" step="0.01" value={pfcTarget} onChange={(e) => setPfcTarget(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Frequency (Hz)</label>
                  <input type="number" value={pfcFreq} onChange={(e) => setPfcFreq(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Capacitor Bank Connection</label>
                  <select value={pfcConn} onChange={(e) => setPfcConn(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                    <option value="delta">Delta Connection (Δ)</option>
                    <option value="star">Star Connection (Y)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        );

      case 'yd':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Impedance Transformation</span>
              <div className="flex flex-col gap-1">
                <label className="text-[9px] text-slate-400">Conversion Direction</label>
                <select value={ydDir} onChange={(e) => setYdDir(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none">
                  <option value="y_to_delta">Star (Y) to Delta (Δ)</option>
                  <option value="delta_to_y">Delta (Δ) to Star (Y)</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[9px] text-slate-400">Per-Phase Impedance (Ω)</label>
                <input type="number" value={ydZVal} onChange={(e) => setYdZVal(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
              </div>
            </div>
          </div>
        );

      case 'pll':
        return (
          <div className="space-y-4">
            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Three-Phase Coordinate Transform</span>
              <div className="grid grid-cols-3 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Phase A Voltage (V)</label>
                  <input type="number" value={tfA} onChange={(e) => setTfA(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Phase B Voltage (V)</label>
                  <input type="number" value={tfB} onChange={(e) => setTfB(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Phase C Voltage (V)</label>
                  <input type="number" value={tfC} onChange={(e) => setTfC(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Rotation Angle θ (°)</label>
                  <input type="number" value={tfTheta} onChange={(e) => setTfTheta(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] text-slate-400">Clarke Transform Mode</label>
                  <select value={clarkeMode} onChange={(e) => setClarkeMode(e.target.value)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none cursor-pointer">
                    <option value="amplitude_invariant">Amplitude-Invariant (2/3)</option>
                    <option value="power_invariant">Power-Invariant (√(2/3))</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="border border-slate-800/80 rounded-lg p-3.5 bg-slate-900/10 space-y-3">
              <span className="text-[10px] font-bold text-slate-300 block border-b border-slate-800 pb-1">Phase-Locked Loop (PLL) Parameters</span>
              <div className="grid grid-cols-3 gap-2">
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Voltage Amplitude Vm (V)</label>
                  <input type="number" value={pllVm} onChange={(e) => setPllVm(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Loop Bandwidth f_bw (Hz)</label>
                  <input type="number" value={pllFbw} onChange={(e) => setPllFbw(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-[8px] text-slate-400">Damping Ratio ζ</label>
                  <input type="number" step="0.05" value={pllZeta} onChange={(e) => setPllZeta(e.target.value as any)} className="bg-slate-950 border border-slate-800 rounded p-1.5 text-xs text-white outline-none" />
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const renderResults = () => {
    return (
      <div className="space-y-6">
        <Card className="border-slate-800 bg-[#0b0f19]/60 flex flex-col flex-1">
          <CardHeader className="border-b border-slate-800/80 pb-3 flex flex-row items-center justify-between space-y-0">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              Calculation & Conversion Results
            </h2>
            <div className="text-[10px] text-slate-500 font-mono">
              {activeTab.toUpperCase()} ACTIVE
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            
            {activeTab === 'params' && paramsRes && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Phase Voltage V_ph</span>
                    <span className="text-sm font-bold text-cyan-400">{paramsRes.v_ph.toFixed(2)} V</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Phase Current I_ph</span>
                    <span className="text-sm font-bold text-cyan-400">{paramsRes.i_ph.toFixed(2)} A</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Apparent Power S</span>
                    <span className="text-sm font-bold text-amber-400">{paramsRes.s_val_kva.toFixed(3)} kVA</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Active Power P</span>
                    <span className="text-sm font-bold text-emerald-400">{paramsRes.p_val_kw.toFixed(3)} kW</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-3">
                  <span className="text-xs font-semibold text-slate-350 block border-b border-slate-850 pb-1">Per-Phase Equivalent Impedance & Elements</span>
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                    <div>Impedance Magnitude Z: <span className="text-slate-200 font-bold">{paramsRes.z_ph_ohm.toFixed(2)} Ω</span></div>
                    <div>Equivalent Resistance R: <span className="text-slate-200 font-semibold">{paramsRes.r_ph_ohm.toFixed(2)} Ω</span></div>
                    <div>Equivalent Reactance X: <span className="text-slate-200 font-semibold">{paramsRes.x_ph_ohm.toFixed(2)} Ω</span></div>
                    {paramsRes.equivalent_l_mh > 0 ? (
                      <div>Inductive Equivalent L: <span className="text-cyan-400 font-semibold">{paramsRes.equivalent_l_mh.toFixed(3)} mH</span></div>
                    ) : (
                      <div>Capacitive Equivalent C: <span className="text-emerald-400 font-semibold">{paramsRes.equivalent_c_uf.toFixed(3)} uF</span></div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'pfc' && pfcWarning && (
              <div className="p-3 bg-red-950/40 border border-red-800/80 rounded-lg text-xs text-red-300 font-bold">
                ⚠️ {pfcWarning}
              </div>
            )}

            {activeTab === 'pfc' && pfcRes && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Required Reactive Power Qc</span>
                    <span className="text-sm font-bold text-cyan-400">{pfcRes.q_c_kvar.toFixed(3)} kvar</span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded border border-slate-900 flex flex-col">
                    <span className="text-[10px] text-slate-500">Per-Phase Capacitance C</span>
                    <span className="text-sm font-bold text-emerald-400">{pfcRes.c_phase_uf.toFixed(3)} uF</span>
                  </div>
                </div>
                <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-2 text-xs text-slate-400">
                  <div>Capacitor Voltage Rating V_rms: <span className="text-slate-200 font-semibold">{pfcRes.v_cap_rms.toFixed(1)} V</span></div>
                  <div>Recommended Derating Rating (1.2x): <span className="text-amber-400 font-bold">{pfcRes.recommended_voltage_rating.toFixed(0)} V</span></div>
                </div>
              </div>
            )}

            {activeTab === 'yd' && ydRes && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-950/60 rounded border border-slate-900 flex flex-col items-center">
                  <span className="text-[10px] text-slate-500">Equivalent Per-Phase Impedance</span>
                  <span className="text-lg font-bold text-cyan-400">{ydRes.z_out_ohm.toFixed(3)} Ω</span>
                </div>
              </div>
            )}

            {activeTab === 'pll' && tfRes && pllRes && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-2">
                    <span className="text-xs font-semibold text-slate-350 block border-b border-slate-850 pb-1">Clarke / Park Transform</span>
                    <div className="text-xs text-slate-450 space-y-1">
                      <div>u_alpha: <span className="text-slate-200 font-mono font-bold">{tfRes.alpha.toFixed(2)} V</span></div>
                      <div>u_beta: <span className="text-slate-200 font-mono font-bold">{tfRes.beta.toFixed(2)} V</span></div>
                      <div>u_d: <span className="text-cyan-400 font-mono font-bold">{tfRes.d.toFixed(2)} V</span></div>
                      <div>u_q: <span className="text-cyan-400 font-mono font-bold">{tfRes.q.toFixed(2)} V</span></div>
                    </div>
                  </div>

                  <div className="p-4 bg-slate-950/40 border border-slate-800 rounded-xl space-y-2">
                    <span className="text-xs font-semibold text-slate-350 block border-b border-slate-850 pb-1">PLL PI Parameters (S-Domain)</span>
                    <div className="text-xs text-slate-450 space-y-1">
                      <div>Proportional Kp: <span className="text-amber-400 font-mono font-bold">{pllRes.kp.toFixed(5)}</span></div>
                      <div>Integral Ki: <span className="text-amber-400 font-mono font-bold">{pllRes.ki.toFixed(3)}</span></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Top Banner */}
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
            <h1 className="text-base font-bold text-white tracking-tight">Three-Phase AC & Coordinate Transformations</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
              Compute three-phase Y-Delta transformations, Clarke/Park coordinate frames, reactive power PFC compensation, and synchronous PLL loop tuning.
            </p>
          </div>
        </div>
        <Button
          onClick={handleResetLayout}
          variant="outline"
          size="sm"
          className="text-xs text-slate-350 border-slate-800 hover:bg-slate-850 hover:text-white flex items-center gap-1 bg-transparent shrink-0"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Layout
        </Button>
      </div>

      {/* Tabs navigation at the top */}
      <div className="flex-shrink-0">
        <Tabs value={activeTab} onValueChange={(val: any) => setActiveTab(val)} className="w-auto">
          <TabsList className="bg-[#020617] border border-slate-800 h-auto p-1 flex flex-wrap gap-1 justify-start">
            <TabsTrigger value="params" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">1. Parameter Sizing (V/I/P/Z)</TabsTrigger>
            <TabsTrigger value="pfc" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">2. PFC Reactive Compensation</TabsTrigger>
            <TabsTrigger value="yd" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">3. Y-Δ Impedance Conversion</TabsTrigger>
            <TabsTrigger value="pll" className="text-xs data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400 font-bold cursor-pointer">4. Coordinate Transform & PLL</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 min-h-0">
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
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
                    <span className="text-xs font-bold text-white">Operating Input Conditions</span>
                  </div>
                  {renderInput()}
                </div>
              )}

              {key === 'results' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
                  {renderResults()}
                </div>
              )}

              {key === 'visual_panel' && (
                <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
                  {renderVisualPanel()}
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
