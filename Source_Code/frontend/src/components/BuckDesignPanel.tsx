import { useTabHistoryState } from '../lib/tabHistory';
import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/Accordion';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { DragCard, DragDeck, useDragDeckLayout } from './ui/LayoutEngine';
import { Tabs, TabsList, TabsTrigger } from './ui/Tabs';
import { apiFetch } from '../lib/api';
import BuckSchematicSandbox from './BuckSchematicSandbox';
import SecondaryVerificationHub from './SecondaryVerificationHub';
import {
  ArrowLeft,
  CheckCircle2,
  RefreshCw,
  ShieldAlert
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

interface SwitchDevice {
  name: string;
  type: string;
  v_ds_max: number;
  i_d_max: number;
  r_ds_on: number;
  package: string;
  r_jc: number;
}

interface DiodeDevice {
  name: string;
  type: string;
  v_r_max: number;
  i_f_max: number;
  v_f: number;
  package: string;
  r_jc: number;
}

interface CalculateResponse {
  basic: {
    duty: number;
    l_min_uh: number;
    c_min_uf: number;
    i_peak_a: number;
    cin_rms_a: number;
    cout_rms_a: number;
    c_in_uf: number;
  };
  actual_l_uh: number;
  actual_c_uf: number;
  time_domain: {
    t_us: number[];
    i_l_a: number[];
    v_ripple_mv: number[];
  };
  bode: {
    f_hz: number[];
    gain_db: number[];
    phase_deg: number[];
  };
  stresses: {
    sw_v: number;
    sw_i_pk: number;
    sw_i_rms: number;
    diode_v: number;
    i_diode_pk: number;
    diode_i_avg: number;
  };
  drc_warnings: string[];
}

interface BomResponse {
  switches: SwitchDevice[];
  diodes: DiodeDevice[];
  requirements: {
    sw_v: number;
    sw_i: number;
    diode_v: number;
    diode_i: number;
  };
}

export default function BuckDesignPanel({ onBack, setActiveModule }: { onBack: () => void; setActiveModule?: any }) {
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
    panelKey: 'layout_buckdesignpanel_v5',
    defaultCards: ['input', 'theory', 'charts', 'drc'],
    defaultColumns: {
      input: 'left',
      theory: 'left',
      charts: 'right',
      drc: 'right'
    } as Record<string, 'left' | 'right'>,
    defaultSpans: {
      input: 4,
      theory: 4,
      charts: 8,
      drc: 8
    },
    defaultHeights: {
      input: 560,
      theory: 380,
      charts: 480,
      drc: 220
    }
  });

  const [mainTab, setMainTab] = useTabHistoryState<'schematic' | 'specs' | 'bom' | 'verification'>('schematic', 'mainTab');
  const mainTabRef = useRef(mainTab);
  useEffect(() => { mainTabRef.current = mainTab; }, [mainTab]);
  const [vin, setVin] = useState<number>(24);
  const [vout, setVout] = useState<number>(12);
  const [iout, setIout] = useState<number>(5);
  const [fsw, setFsw] = useState<number>(100);
  const [lir, setLir] = useState<number>(30);
  const [vrip, setVrip] = useState<number>(1);
  
  const [lUh, setLUh] = useState<string>('');
  const [cUf, setCUf] = useState<string>('');
  const [esr, setEsr] = useState<number>(20);

  const [calcData, setCalcData] = useState<CalculateResponse | null>(null);
  const [bomData, setBomData] = useState<BomResponse | null>(null);
  const [activeTab, setActiveTab] = useTabHistoryState<'time' | 'bode'>('time', 'activeTab');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [numCycles, setNumCycles] = useState<number>(3);

  // Chart Custom Scales
  const [ilMin, setIlMin] = useState<string>('');
  const [ilMax, setIlMax] = useState<string>('');
  const [vripMin, setVripMin] = useState<string>('');
  const [vripMax, setVripMax] = useState<string>('');
  const [gainMin, setGainMin] = useState<string>('');
  const [gainMax, setGainMax] = useState<string>('');
  const [phaseMin, setPhaseMin] = useState<string>('');
  const [phaseMax, setPhaseMax] = useState<string>('');

  // Schematic Sandbox States
  const [cinUf, setCinUf] = useState<string>('100');
  const [cinEsr, setCinEsr] = useState<number>(10);
  const [swRdsOn, setSwRdsOn] = useState<number>(80);
  const [swTimes, setSwTimes] = useState<number>(60);
  const [diodeVf, setDiodeVf] = useState<number>(0.8);
  const [indDcr, setIndDcr] = useState<number>(50);
  const [diodeType, setDiodeType] = useState<string>('schottky');
  const [diodeQrr, setDiodeQrr] = useState<number>(0);
  const [syncRdsOn, setSyncRdsOn] = useState<number>(10);
  const [syncDeadTime, setSyncDeadTime] = useState<number>(50);
  const [syncBodyVf, setSyncBodyVf] = useState<number>(0.8);

  const renderBomContent = () => {
    return (
      <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200 w-full flex flex-col">
        <CardHeader className="p-4 pb-2 border-b border-slate-800/60 shrink-0">
          <CardTitle className="text-xs font-bold text-white border-l-2 border-cyan-500 pl-2 flex items-center gap-2">
            Commercial BOM Sizing & Selection
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 flex-1 overflow-y-auto flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Switches Recommendation */}
            <div className="flex flex-col gap-2">
              <h3 className="text-xs font-semibold text-cyan-300 border-l-2 border-cyan-500 pl-2 mb-1">
                Power MOSFET / SiC Selection
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[11px] border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2">Part Number</th>
                      <th className="py-2">Vds Max</th>
                      <th className="py-2">Id Max</th>
                      <th className="py-2">Rds(on)</th>
                      <th className="py-2">Package</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bomData?.switches?.map((item, idx) => (
                      <tr key={idx} className={`border-b border-slate-800/40 hover:bg-slate-800/20 ${idx === 0 ? 'bg-cyan-500/5 text-cyan-300 font-medium' : 'text-slate-300'}`}>
                        <td className="py-2.5">{item.name} {idx === 0 && <span className="text-[9px] bg-cyan-500/20 text-cyan-400 px-1 rounded">Preferred</span>}</td>
                        <td className="py-2.5">{item.v_ds_max}V</td>
                        <td className="py-2.5">{item.i_d_max}A</td>
                        <td className="py-2.5">{(item.r_ds_on * 1000).toFixed(1)}mΩ</td>
                        <td className="py-2.5 text-slate-500">{item.package}</td>
                      </tr>
                    ))}
                    {!bomData?.switches?.length && (
                      <tr>
                        <td colSpan={5} className="py-4 text-center text-slate-500">No components meet safety margin criteria. Consider adjusting voltage/current specs.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Diodes Recommendation */}
            <div className="flex flex-col gap-2">
              <h3 className="text-xs font-semibold text-purple-300 border-l-2 border-purple-500 pl-2 mb-1">
                Freewheeling Diode Selection
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[11px] border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2">Part Number</th>
                      <th className="py-2">Vr Max</th>
                      <th className="py-2">If Max</th>
                      <th className="py-2">Forward Vf</th>
                      <th className="py-2">Package</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bomData?.diodes?.map((item, idx) => (
                      <tr key={idx} className={`border-b border-slate-800/40 hover:bg-slate-800/20 ${idx === 0 ? 'bg-purple-500/5 text-purple-300 font-medium' : 'text-slate-300'}`}>
                        <td className="py-2.5">{item.name} {idx === 0 && <span className="text-[9px] bg-purple-500/20 text-purple-400 px-1 rounded">Preferred</span>}</td>
                        <td className="py-2.5">{item.v_r_max}V</td>
                        <td className="py-2.5">{item.i_f_max}A</td>
                        <td className="py-2.5">{item.v_f}V</td>
                        <td className="py-2.5 text-slate-500">{item.package}</td>
                      </tr>
                    ))}
                    {!bomData?.diodes?.length && (
                      <tr>
                        <td colSpan={5} className="py-4 text-center text-slate-500">No diodes meet safety margin criteria.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </CardContent>
      </Card>
    );
  };

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const calcParams = {
        vin,
        vout,
        iout,
        fsw_khz: fsw,
        lir_pct: lir,
        v_rip_pct: vrip,
        l_uh: lUh ? parseFloat(lUh) : null,
        c_uf: cUf ? parseFloat(cUf) : null,
        rc_esr_mohm: esr,
        sw_rds_on_mohm: swRdsOn,
        sw_times_ns: swTimes,
        diode_vf_v: diodeVf,
        ind_dcr_mohm: indDcr,
        diode_type: diodeType,
        diode_qrr_nc: diodeQrr,
        sync_rds_on_mohm: syncRdsOn,
        sync_dead_time_ns: syncDeadTime,
        sync_body_vf_v: syncBodyVf,
        num_cycles: numCycles
      };
      
      const calcRes = await apiFetch('/api/calculate/buck', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(calcParams),
      });

      if (!calcRes.ok) {
        const errDetail = await calcRes.json();
        throw new Error(errDetail.detail || 'Calculation failed');
      }

      const data: CalculateResponse = await calcRes.json();
      setCalcData(data);

      if (!lUh) setLUh(data.actual_l_uh.toFixed(2));
      if (!cUf) setCUf(data.actual_c_uf.toFixed(2));

      const bomParams = {
        min_v_sw: data.stresses.sw_v,
        min_i_sw: data.stresses.sw_i_pk,
        min_v_diode: data.stresses.diode_v,
        min_i_diode: data.stresses.sw_i_pk
      };

      const bomRes = await apiFetch('/api/bom/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bomParams),
      });

      if (bomRes.ok) {
        const bData: BomResponse = await bomRes.json();
        setBomData(bData);
      }

    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleCalculate();
  }, []);

  let fc = 0;
  let pm = 0;
  if (calcData && calcData.bode && calcData.bode.f_hz.length > 0) {
    const fArr = calcData.bode.f_hz;
    const gainArr = calcData.bode.gain_db;
    const phaseArr = calcData.bode.phase_deg;
    
    for (let i = 0; i < gainArr.length - 1; i++) {
      if ((gainArr[i] >= 0 && gainArr[i+1] < 0) || (gainArr[i] <= 0 && gainArr[i+1] > 0)) {
        const ratio = (0 - gainArr[i]) / (gainArr[i+1] - gainArr[i]);
        fc = fArr[i] + ratio * (fArr[i+1] - fArr[i]);
        pm = phaseArr[i] + ratio * (fArr[i+1] - fArr[i]);
        pm = 180 + pm;
        break;
      }
    }
  }

  const timeChartOption = {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#1e293b' } },
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9', fontFamily: 'Inter', fontSize: 12 }
    },
    legend: {
      data: ['Inductor Current i_L (A)', 'Output Ripple Voltage v_ripple (mV)'],
      textStyle: { color: '#94a3b8', fontFamily: 'Inter', fontSize: 11 },
      top: 0
    },
    grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: calcData?.time_domain?.t_us?.map(t => t.toFixed(2)) || [],
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      name: 'Time (μs)',
      nameTextStyle: { color: '#94a3b8', fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Inductor Current (A)',
        position: 'left',
        min: ilMin !== '' ? parseFloat(ilMin) : undefined,
        max: ilMax !== '' ? parseFloat(ilMax) : undefined,
        axisLine: { show: true, lineStyle: { color: '#00f2fe' } },
        axisLabel: { color: '#00f2fe', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      {
        type: 'value',
        name: 'Ripple Voltage (mV)',
        position: 'right',
        min: vripMin !== '' ? parseFloat(vripMin) : undefined,
        max: vripMax !== '' ? parseFloat(vripMax) : undefined,
        axisLine: { show: true, lineStyle: { color: '#9b59b6' } },
        axisLabel: { color: '#9b59b6', fontSize: 10 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: 'Inductor Current i_L (A)',
        type: 'line',
        data: calcData?.time_domain?.i_l_a || [],
        symbol: 'none',
        lineStyle: { width: 2.5, color: '#00f2fe' },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 242, 254, 0.25)' },
              { offset: 1, color: 'rgba(0, 242, 254, 0)' }
            ]
          }
        }
      },
      {
        name: 'Output Ripple Voltage v_ripple (mV)',
        type: 'line',
        yAxisIndex: 1,
        data: calcData?.time_domain?.v_ripple_mv || [],
        symbol: 'none',
        lineStyle: { width: 2, type: 'dashed', color: '#9b59b6' }
      }
    ]
  };

  const bodeChartOption = {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#1e293b' } },
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9', fontFamily: 'Inter', fontSize: 12 }
    },
    legend: {
      data: ['Gain (dB)', 'Phase (deg)'],
      textStyle: { color: '#94a3b8', fontFamily: 'Inter', fontSize: 11 },
      top: 0
    },
    grid: { left: '10%', right: '10%', bottom: '15%', top: '15%', containLabel: true },
    xAxis: {
      type: 'log',
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10,
        formatter: (value: number) => {
          const log10 = Math.log10(value);
          if (Math.abs(log10 - Math.round(log10)) < 1e-6) {
            return value >= 1000 ? (value / 1000) + 'kHz' : value + 'Hz';
          }
          return '';
        }
      },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } },
      name: 'Frequency (Hz)',
      nameTextStyle: { color: '#94a3b8', fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Magnitude Gain (dB)',
        position: 'left',
        min: gainMin !== '' ? parseFloat(gainMin) : undefined,
        max: gainMax !== '' ? parseFloat(gainMax) : undefined,
        axisLine: { show: true, lineStyle: { color: '#4facfe' } },
        axisLabel: { color: '#4facfe', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
      },
      {
        type: 'value',
        name: 'Phase Angle (deg)',
        position: 'right',
        min: phaseMin !== '' ? parseFloat(phaseMin) : undefined,
        max: phaseMax !== '' ? parseFloat(phaseMax) : undefined,
        axisLine: { show: true, lineStyle: { color: '#f093fb' } },
        axisLabel: { color: '#f093fb', fontSize: 10 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: 'Gain (dB)',
        type: 'line',
        data: calcData?.bode?.f_hz?.map((f, i) => [f, calcData.bode.gain_db[i]]) || [],
        symbol: 'none',
        lineStyle: { width: 2.5, color: '#4facfe' },
        markLine: fc > 0 ? {
          symbol: ['none', 'none'],
          label: {
            show: true,
            position: 'end',
            formatter: `fc = ${fc.toFixed(1)} Hz`,
            color: '#10b981',
            fontSize: 10,
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            padding: [2, 4],
            borderRadius: 3
          },
          lineStyle: { type: 'dotted', color: '#10b981', width: 1.5 },
          data: [{ xAxis: fc }]
        } : undefined
      },
      {
        name: 'Phase (deg)',
        type: 'line',
        yAxisIndex: 1,
        data: calcData?.bode?.f_hz?.map((f, i) => [f, calcData.bode.phase_deg[i]]) || [],
        symbol: 'none',
        lineStyle: { width: 2.5, color: '#f093fb' },
        markPoint: fc > 0 ? {
          data: [
            {
              coord: [fc, pm - 180],
              value: `P.M. = ${pm.toFixed(1)}°`,
              symbol: 'pin',
              symbolSize: 45,
              label: { fontSize: 9, offset: [0, 2], color: '#ffffff' },
              itemStyle: { color: '#10b981' }
            }
          ]
        } : undefined
      }
    ]
  };

  return (
    <div className="w-full h-full flex flex-col gap-4 overflow-hidden p-4">
      {/* Title Header */}
      <div className="flex justify-between items-center bg-[#0f172a]/80 p-4 rounded-xl border border-slate-800/80 backdrop-blur w-full shrink-0">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={onBack} className="bg-slate-900 border-slate-800 text-slate-300 hover:text-white cursor-pointer">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-md font-bold text-white flex items-center gap-2">
              Buck Synchronous Converter
            </h1>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Steady-state analysis of synchronous buck converter, supporting CCM/DCM inductor current simulation, closed-loop Bode sweep, capacitor ripple sizing, and BOM selection.
            </p>
          </div>
        </div>

        {/* Parent Tab Switcher */}
        <div className="flex bg-[#020617] border border-slate-850 p-0.5 rounded-lg h-9 shrink-0">
          <button
            onClick={() => setMainTab('schematic')}
            className={`px-4 text-xs font-semibold rounded-md transition-all flex items-center cursor-pointer ${
              mainTab === 'schematic'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Interactive Schematic
          </button>
          <button
            onClick={() => setMainTab('specs')}
            className={`px-4 text-xs font-semibold rounded-md transition-all flex items-center cursor-pointer ${
              mainTab === 'specs'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Specs & Operating Conditions
          </button>
          <button
            onClick={() => setMainTab('bom')}
            className={`px-4 text-xs font-semibold rounded-md transition-all flex items-center cursor-pointer ${
              mainTab === 'bom'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Commercial BOM
          </button>
          <button
            onClick={() => setMainTab('verification')}
            className={`px-4 text-xs font-semibold rounded-md transition-all flex items-center cursor-pointer ${
              mainTab === 'verification'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Secondary Verification Hub
          </button>
        </div>

        <div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetLayout}
            className="bg-slate-900 border-slate-800 text-slate-300 hover:text-white flex items-center gap-1 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset Layout
          </Button>
        </div>
      </div>

      {error && (
        <div className="w-full p-4 rounded-lg bg-red-950/40 border border-red-500/30 text-red-200 text-sm flex items-center gap-3 shrink-0">
          <ShieldAlert className="w-5 h-5 text-red-500 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {/* Workspace Area */}
      <div className="flex-1 overflow-hidden min-h-0 flex flex-col relative w-full">
        {mainTab === 'schematic' ? (
          <div className="w-full flex-1 flex flex-col min-h-0 overflow-hidden relative">
            <BuckSchematicSandbox
              vin={vin} setVin={setVin}
              vout={vout} setVout={setVout}
              iout={iout} setIout={setIout}
              fsw={fsw} setFsw={setFsw}
              lir={lir} setLir={setLir}
              vrip={vrip} setVrip={setVrip}
              lUh={lUh} setLUh={setLUh}
              cUf={cUf} setCUf={setCUf}
              esr={esr} setEsr={setEsr}
              cinUf={cinUf} setCinUf={setCinUf}
              cinEsr={cinEsr} setCinEsr={setCinEsr}
              swRdsOn={swRdsOn} setSwRdsOn={setSwRdsOn}
              swTimes={swTimes} setSwTimes={setSwTimes}
              diodeVf={diodeVf} setDiodeVf={setDiodeVf}
              indDcr={indDcr} setIndDcr={setIndDcr}
              calcData={calcData}
              diodeType={diodeType} setDiodeType={setDiodeType}
              diodeQrr={diodeQrr} setDiodeQrr={setDiodeQrr}
              syncRdsOn={syncRdsOn} setSyncRdsOn={setSyncRdsOn}
              syncDeadTime={syncDeadTime} setSyncDeadTime={setSyncDeadTime}
              syncBodyVf={syncBodyVf} setSyncBodyVf={setSyncBodyVf}
            />
          </div>
        ) : mainTab === 'bom' ? (
          <div className="w-full flex-1 overflow-y-auto p-4 scrollbar-thin">
            {renderBomContent()}
          </div>
        ) : mainTab === 'verification' ? (
          <div className="w-full flex-1 overflow-y-auto p-4 scrollbar-thin">
            <SecondaryVerificationHub
              vinMin={vin * 0.9}
              vinNom={vin}
              vinMax={vin * 1.1}
              vout={vout}
              iout={iout}
              fsw={fsw}
              power={vout * iout}
              topology="buck"
              setActiveModule={setActiveModule}
            />
          </div>
        ) : (
          <div className="w-full flex-1 overflow-y-auto min-h-0 scrollbar-thin">
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
                  onResetLayout={handleResetLayout}
                >
                  {key === 'input' && (
                    <div className="h-full p-4 overflow-hidden">
                      <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200 h-full flex flex-col">
                        <CardHeader className="p-4 pb-2 shrink-0">
                          <CardTitle className="text-xs font-bold text-white border-l-2 border-cyan-500 pl-2 flex items-center gap-2">
                            Operating Specs & Parameters
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0 flex-1 overflow-y-auto space-y-4">
                          <div className="space-y-4 pt-2">
                            <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Input Voltage V_in (V)</label>
                              <input 
                                type="number" 
                                value={vin} 
                                onChange={(e) => setVin(parseFloat(e.target.value) || 0)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Output Voltage V_out (V)</label>
                              <input 
                                type="number" 
                                value={vout} 
                                onChange={(e) => setVout(parseFloat(e.target.value) || 0)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Output Current I_out (A)</label>
                              <input 
                                type="number" 
                                value={iout} 
                                onChange={(e) => setIout(parseFloat(e.target.value) || 0)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Switching Frequency f_sw (kHz)</label>
                              <input 
                                type="number" 
                                value={fsw} 
                                onChange={(e) => setFsw(parseFloat(e.target.value) || 0)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Current Ripple Ratio LIR (%)</label>
                              <input 
                                type="number" 
                                value={lir} 
                                onChange={(e) => setLir(parseFloat(e.target.value) || 0)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Voltage Ripple Ratio V_rip (%)</label>
                              <input 
                                type="number" 
                                value={vrip} 
                                onChange={(e) => setVrip(parseFloat(e.target.value) || 0)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                          </div>

                          <div className="h-px bg-slate-800 my-1" />

                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold text-slate-300">Filter Component Sizing</span>
                            <Button 
                              variant="link" 
                              onClick={() => {
                                if (calcData) {
                                  setLUh(calcData.basic.l_min_uh.toFixed(2));
                                  setCUf(calcData.basic.c_min_uf.toFixed(2));
                                }
                              }}
                              className="h-auto p-0 text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 border-0 cursor-pointer"
                            >
                              <RefreshCw className="w-3.5 h-3.5" /> Auto-fill Estimated Values
                            </Button>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Actual Inductor Lo (μH)</label>
                              <input 
                                type="text" 
                                placeholder="Auto"
                                value={lUh} 
                                onChange={(e) => setLUh(e.target.value)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-cyan-400 font-semibold outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                            <div className="flex flex-col gap-1.5">
                              <label className="text-[10px] text-slate-400">Actual Capacitor Co (μF)</label>
                              <input 
                                type="text" 
                                placeholder="Auto"
                                value={cUf} 
                                onChange={(e) => setCUf(e.target.value)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-cyan-400 font-semibold outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                            <div className="flex flex-col gap-1.5 col-span-2">
                              <label className="text-[10px] text-slate-400">Capacitor ESR (mΩ)</label>
                              <input 
                                type="number" 
                                value={esr} 
                                onChange={(e) => setEsr(parseFloat(e.target.value) || 0)} 
                                className="flex h-8 w-full rounded-md border border-slate-800 bg-[#020617] px-3 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500 transition-colors"
                              />
                            </div>
                          </div>

                          <Button 
                            onClick={handleCalculate} 
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs cursor-pointer shrink-0"
                          >
                            {loading ? 'Calculating...' : 'Run Design & Simulation'}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {key === 'theory' && (
                  <div className="h-full p-4 overflow-hidden">
                    <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200 h-full flex flex-col">
                      <CardHeader className="p-4 pb-2 shrink-0">
                        <CardTitle className="text-xs font-bold text-white border-l-2 border-cyan-500 pl-2">
                          Physical Derivations & Formulas
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 pt-0 flex-1 overflow-y-auto space-y-4">
                        {calcData ? (
                          <div className="space-y-4">
                            <Accordion type="single" collapsible className="w-full text-xs">
                              {/* Duty Cycle D */}
                              <AccordionItem value="duty" className="border-slate-800">
                                <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2.5">
                                  <div className="flex flex-col items-start gap-0.5 text-left">
                                    <span className="text-[10px] text-slate-400">Switching Duty Cycle (D)</span>
                                    <span className="font-semibold text-cyan-300">D = {(calcData.basic.duty * 100).toFixed(1)}%</span>
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                                  <div>Under steady-state operation, the inductor must satisfy Volt-Second Balance:</div>
                                  <Latex math="\int_0^{T_{sw}} v_L(t) dt = 0" block />
                                  <div>During high-side switch ON period (<Latex math="t \in [0, D \cdot T_{sw}]" />), inductor voltage is:</div>
                                  <Latex math="v_{L,on} = V_{in} - V_{out}" block />
                                  <div>During freewheeling diode/sync FET conduction (<Latex math="t \in [D \cdot T_{sw}, T_{sw}]" />), inductor voltage is:</div>
                                  <Latex math="v_{L,off} = -V_{out}" block />
                                  <div>Substituting into the Volt-Second balance integral:</div>
                                  <Latex math="(V_{in} - V_{out}) \cdot D T_{sw} + (-V_{out}) \cdot (1 - D) T_{sw} = 0" block />
                                  <div>Simplifying by canceling the switching period <Latex math="T_{sw}" />:</div>
                                  <Latex math="D V_{in} - D V_{out} - V_{out} + D V_{out} = 0 \implies D = \frac{V_{out}}{V_{in}}" block />
                                </AccordionContent>
                              </AccordionItem>

                              {/* Critical Inductance Lmin */}
                              <AccordionItem value="lmin" className="border-slate-800">
                                <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2.5">
                                  <div className="flex flex-col items-start gap-0.5 text-left">
                                    <span className="text-[10px] text-slate-400">CCM Critical Inductance (L_min)</span>
                                    <span className="font-semibold text-cyan-300">L_min = {calcData.basic.l_min_uh.toFixed(2)} μH</span>
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                                  <div>From fundamental inductor electromagnetic physics:</div>
                                  <Latex math="v_L(t) = L \frac{di(t)}{dt}" block />
                                  <div>During ON-time <Latex math="D \cdot T_{sw}" />, inductor current ramps linearly with peak-to-peak ripple:</div>
                                  <Latex math="\Delta I_L = \frac{(V_{in} - V_{out}) \cdot D}{L \cdot f_{sw}} = \frac{V_{out} \cdot (1 - D)}{L \cdot f_{sw}}" block />
                                  <div>To guarantee continuous conduction mode (CCM), inductor valley current must remain positive (<Latex math="\Delta I_L \le 2 I_{out}" />):</div>
                                  <Latex math="\Delta I_L \le 2 I_{out} \implies \frac{V_{out} \cdot (1 - D)}{L \cdot f_{sw}} \le 2 I_{out}" block />
                                  <div>Yielding the critical CCM boundary minimum inductance:</div>
                                  <Latex math="L_{crit} = \frac{V_{out} \cdot (1 - D)}{2 \cdot I_{out} \cdot f_{sw}}" block />
                                  <div>In practical design, choosing ripple ratio coefficient <Latex math="K_{ripple} = \Delta I_L / I_{out}" /> (recommended <Latex math="0.2 \sim 0.4" />):</div>
                                  <Latex math="L_{design} = \frac{V_{out} \cdot (1 - D)}{K_{ripple} \cdot I_{out} \cdot f_{sw}}" block />
                                </AccordionContent>
                              </AccordionItem>

                              {/* Output Capacitor & ESR Ripple */}
                              <AccordionItem value="c_esr" className="border-slate-800">
                                <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2.5">
                                  <div className="flex flex-col items-start gap-0.5 text-left">
                                    <span className="text-[10px] text-slate-400">Output Filter Capacitor Sizing</span>
                                    <span className="font-semibold text-cyan-300">C_min = {calcData.basic.c_min_uf.toFixed(2)} μF</span>
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                                  <div>Total output voltage AC ripple comprises capacitive charge variation and ESR drop:</div>
                                  <div>**1. Pure Capacitive Ripple** <Latex math="\Delta V_C" />: Excess current charges the capacitor during positive half-cycle triangle area:</div>
                                  <Latex math="\Delta Q = \frac{1}{2} \cdot \left(\frac{T_{sw}}{2}\right) \cdot \left(\frac{\Delta I_L}{2}\right) = \frac{\Delta I_L}{8 f_{sw}} \implies \Delta V_C = \frac{\Delta I_L}{8 f_{sw} C}" block />
                                  <div>**2. ESR Drop Ripple** <Latex math="\Delta V_{ESR}" />: Inductor ripple current flowing through capacitor ESR:</div>
                                  <Latex math="\Delta V_{ESR} = \Delta I_L \cdot \text{ESR}" block />
                                  <div>Combined peak-to-peak transient output voltage ripple:</div>
                                  <Latex math="\Delta V_{out} = \frac{\Delta I_L}{8 f_{sw} C} + \Delta I_L \cdot \text{ESR}" block />
                                </AccordionContent>
                              </AccordionItem>

                              {/* Semiconductor Current Stress */}
                              <AccordionItem value="semi_stress" className="border-slate-800">
                                <AccordionTrigger className="text-xs text-slate-200 hover:no-underline py-2.5">
                                  <div className="flex flex-col items-start gap-0.5 text-left">
                                    <span className="text-[10px] text-slate-400">Semiconductor RMS Current Stress</span>
                                    <span className="font-semibold text-cyan-300">
                                      I_Q,rms = {(iout * Math.sqrt(calcData.basic.duty)).toFixed(2)}A / I_D,rms = {(iout * Math.sqrt(1 - calcData.basic.duty)).toFixed(2)}A
                                    </span>
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent className="text-slate-400 space-y-2 bg-[#020617]/50 p-3 rounded-md border border-slate-900 mt-1 leading-relaxed">
                                  <div>During switching period, high-side switch conducts inductor current during <Latex math="t_{on} = D \cdot T_{sw}" />; freewheeling diode/sync FET conducts during <Latex math="t_{off} = (1-D) \cdot T_{sw}" />.</div>
                                  <div>Integrating squared current over one period (approximating ripple current):</div>
                                  <div>- **Switch RMS Current**:</div>
                                  <Latex math="I_{Q,rms} = I_{out} \sqrt{D}" block />
                                  <div>- **Freewheeling Device RMS Current**:</div>
                                  <Latex math="I_{D,rms} = I_{out} \sqrt{1 - D}" block />
                                  <div>These RMS currents govern conduction losses (<Latex math="I_{rms}^2 \cdot R_{ds(on)}" />), serving as critical inputs for thermal design and device selection.</div>
                                </AccordionContent>
                              </AccordionItem>
                            </Accordion>

                            <div className="flex justify-between border-t border-slate-800 pt-3 text-[11px]">
                              <span className="text-slate-400">Peak Inductor Current (I_peak)</span>
                              <span className="font-bold text-slate-200">{calcData.basic.i_peak_a.toFixed(2)} A</span>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center h-40 text-slate-500 text-xs">Run design simulation to display physical derivations.</div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                )}

                {key === 'charts' && (
                  <div className="h-full p-4 overflow-hidden">
                    <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200 h-full flex flex-col">
                      <CardHeader className="p-4 pb-2 border-b border-slate-800/60 flex flex-row items-center justify-between shrink-0">
                        <CardTitle className="text-xs font-bold text-white border-l-2 border-cyan-500 pl-2 flex items-center gap-2">
                          Time & Frequency Domain Simulation
                        </CardTitle>
                        
                        <Tabs value={activeTab} onValueChange={(v: any) => setActiveTab(v)} className="w-auto">
                          <TabsList className="bg-[#020617] border border-slate-800 h-8 p-0.5">
                            <TabsTrigger value="time" className="text-[10px] px-3 h-7 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400">
                              Transient Waveforms
                            </TabsTrigger>
                            <TabsTrigger value="bode" className="text-[10px] px-3 h-7 data-[state=active]:bg-cyan-500/10 data-[state=active]:text-cyan-400">
                              Loop Bode Plot
                            </TabsTrigger>
                          </TabsList>
                        </Tabs>
                      </CardHeader>
                      <CardContent className="p-4 flex-1 relative min-h-[300px] overflow-hidden flex flex-col">
                        {/* Scale and Cycle Tuning Panel */}
                        <div className="mb-3 px-3 py-2 bg-slate-900/60 border border-slate-800/80 rounded-lg flex flex-wrap items-center gap-4 text-[10px] shrink-0 text-slate-300">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-400 font-medium">Display Cycles (N):</span>
                            <input
                              type="number"
                              min={1}
                              max={20}
                              value={numCycles}
                              onChange={(e) => {
                                const val = Math.max(1, parseInt(e.target.value) || 1);
                                setNumCycles(val);
                              }}
                              className="w-10 h-5 px-1 bg-[#020617] border border-slate-800 rounded text-cyan-400 text-center outline-none focus:border-cyan-500 font-mono"
                            />
                            <button
                              onClick={handleCalculate}
                              className="px-1.5 py-0.5 bg-cyan-950/40 border border-cyan-800/60 hover:bg-cyan-500/20 text-cyan-400 font-semibold rounded cursor-pointer transition-colors text-[9px]"
                              title="Re-run simulation with updated cycle count"
                            >
                              Re-simulate
                            </button>
                          </div>

                          {activeTab === 'time' ? (
                            <>
                              <div className="w-px h-3.5 bg-slate-800" />
                              <div className="flex items-center gap-1">
                                <span className="text-slate-400">IL Range (A):</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={ilMin}
                                  onChange={(e) => setIlMin(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                                <span>to</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={ilMax}
                                  onChange={(e) => setIlMax(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                              </div>
                              <div className="w-px h-3.5 bg-slate-800" />
                              <div className="flex items-center gap-1">
                                <span className="text-slate-400">Vrip Range (mV):</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={vripMin}
                                  onChange={(e) => setVripMin(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                                <span>to</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={vripMax}
                                  onChange={(e) => setVripMax(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                              </div>
                            </>
                          ) : (
                            <>
                              <div className="w-px h-3.5 bg-slate-800" />
                              <div className="flex items-center gap-1">
                                <span className="text-slate-400">Gain Range (dB):</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={gainMin}
                                  onChange={(e) => setGainMin(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                                <span>to</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={gainMax}
                                  onChange={(e) => setGainMax(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                              </div>
                              <div className="w-px h-3.5 bg-slate-800" />
                              <div className="flex items-center gap-1">
                                <span className="text-slate-400">Phase Range (deg):</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={phaseMin}
                                  onChange={(e) => setPhaseMin(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                                <span>to</span>
                                <input
                                  type="text"
                                  placeholder="Auto"
                                  value={phaseMax}
                                  onChange={(e) => setPhaseMax(e.target.value)}
                                  className="w-12 h-5 px-1 bg-[#020617] border border-slate-850 rounded text-cyan-400 outline-none focus:border-cyan-500 text-center font-mono placeholder:text-slate-600 placeholder:text-[9px]"
                                />
                              </div>
                            </>
                          )}
                        </div>

                        <div className="flex-1 min-h-0 relative">
                          {activeTab === 'time' ? (
                            <ReactECharts option={timeChartOption} style={{ height: '100%', width: '100%' }} notMerge={true} />
                          ) : (
                            <div className="h-full flex flex-col gap-2">
                              <ReactECharts option={bodeChartOption} style={{ height: '85%', width: '100%' }} notMerge={true} />
                              <div className="flex justify-between items-center text-[9px] text-slate-400 bg-slate-900/50 p-2 rounded border border-slate-800 shrink-0">
                                <div>
                                  <span>Crossover Frequency fc: </span>
                                  <span className="font-bold text-emerald-400">{fc > 0 ? `${fc.toFixed(1)} Hz` : 'N/A'}</span>
                                </div>
                                <div>
                                  <span>Phase Margin PM: </span>
                                  <span className="font-bold text-emerald-400">{fc > 0 ? `${pm.toFixed(1)}°` : 'N/A'}</span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {key === 'drc' && (
                  <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
                    <Card className="bg-[#0f172a]/95 border-slate-800/80 shadow-lg text-slate-200 h-full flex flex-col">
                      <CardHeader className="p-4 pb-2 border-b border-slate-800/60 shrink-0">
                        <CardTitle className="text-xs font-bold text-white border-l-2 border-yellow-500 pl-2 flex items-center gap-2">
                          <ShieldAlert className="w-4 h-4 text-yellow-500" />
                          DRC Rule Verification
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 flex-1 overflow-y-auto flex flex-col gap-3 justify-center">
                        {calcData && calcData.drc_warnings.length > 0 ? (
                          calcData.drc_warnings.map((warn, i) => (
                            <div key={i} className="p-3.5 rounded-lg bg-yellow-950/20 border border-yellow-500/20 text-yellow-400 text-xs leading-relaxed">
                              {warn}
                            </div>
                          ))
                        ) : (
                          <div className="flex flex-col items-center justify-center gap-2 py-4 text-slate-400">
                            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                            <span className="text-xs">No design safety risks detected (DRC Clear)</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                )}
              </DragCard>
            )}
          />
        </div>
      )}
    </div>
  </div>
);
}