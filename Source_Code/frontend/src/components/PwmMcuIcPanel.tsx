import { useTabHistoryState } from '../lib/tabHistory';
import { apiFetch } from '../lib/api';
import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  ShieldAlert,
  Copy,
  Compass,
  TrendingUp,
  LineChart,
  ShoppingBag
} from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { useDragDeckLayout, DragDeck, DragCard } from './ui/LayoutEngine';
import { Button } from './ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/Accordion';

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

function useScrollChaining() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleWheel = (e: WheelEvent) => {
      const { scrollTop, scrollHeight, clientHeight } = el;
      const isScrollable = scrollHeight > clientHeight;

      if (!isScrollable) {
        let parent = el.parentElement;
        while (parent) {
          if (parent.scrollHeight > parent.clientHeight && 
              (window.getComputedStyle(parent).overflowY === 'auto' || 
               window.getComputedStyle(parent).overflowY === 'scroll')) {
            break;
          }
          parent = parent.parentElement;
        }
        if (parent) {
          parent.scrollTop += e.deltaY;
          e.preventDefault();
        }
      } else {
        const isAtTop = e.deltaY < 0 && scrollTop === 0;
        const isAtBottom = e.deltaY > 0 && scrollTop + clientHeight >= scrollHeight;
        if (isAtTop || isAtBottom) {
          let parent = el.parentElement;
          while (parent) {
            if (parent.scrollHeight > parent.clientHeight && 
                (window.getComputedStyle(parent).overflowY === 'auto' || 
                 window.getComputedStyle(parent).overflowY === 'scroll')) {
              break;
            }
            parent = parent.parentElement;
          }
          if (parent) {
            parent.scrollTop += e.deltaY;
            e.preventDefault();
          }
        }
      }
    };

    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => {
      el.removeEventListener('wheel', handleWheel);
    };
  }, []);

  return containerRef;
}

const ScrollableContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = "" }) => {
  const ref = useScrollChaining();
  return (
    <div ref={ref} className={`overflow-y-auto h-full scrollbar-thin ${className}`}>
      {children}
    </div>
  );
};

interface FilterResponse {
  recommended_topo: string;
  r_calc_ohm: number;
  r_nearest_ohm: number;
  fc_hz: number;
  ripple_actual_mv: number;
  settle_actual_ms: number;
}

interface TimerResponse {
  arr_val: number;
  dt_red_ticks: number;
  dt_fed_ticks: number;
  resolution_bits: number;
  step_ns: number;
  c2000_rows: Array<{ reg: string; val: string; desc: string }>;
  stm32_rows: Array<{ reg: string; val: string; desc: string }>;
}

interface IcFreqRow {
  c_str: string;
  rt_ideal_kohm: number;
  rt_nearest_kohm: number;
  fsw_actual_khz: number;
}

export default function PwmMcuIcPanel({ onBack }: { onBack: () => void; setActiveModule?: any }) {
  const [activeTab, setActiveTab] = useTabHistoryState<'timer' | 'filter' | 'ic_freq'>('timer', 'activeTab');

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
    panelKey: `layout_pwmmcuic_v5_${activeTab}`,
    activeTab: activeTab,
    defaultCards: activeTab === 'ic_freq' ? ['input', 'results', 'schematic'] : ['input', 'results', 'chart', 'schematic'],
    defaultColumns: { input: 'left', results: 'right', chart: 'right', schematic: 'right' },
    defaultSpans: { input: 4, results: 8, chart: 8, schematic: 8 },
    defaultHeights: { input: 500, results: 460, chart: 300, schematic: 300 }
  });

  const [activeTimingTab, setActiveTimingTab] = useTabHistoryState<'complementary' | 'hrpwm'>('complementary', 'activeTimingTab');

  const [fPwmHz, setFPwmHz] = useState<number>(100000);
  const [vCc, setVCc] = useState<number>(3.3);
  const [bits, setBits] = useState<number>(12);
  const [cSelUf, setCSelUf] = useState<number>(0.1);
  const [vRipTargetMv, setVRipTargetMv] = useState<number>(1.0);
  const [tSetTargetMs, setTSetTargetMs] = useState<number>(10.0);

  const [sysclkMhz, setSysclkMhz] = useState<number>(200.0);
  const [fswKhz, setFswKhz] = useState<number>(100.0);
  const [dtRedNs, setDtRedNs] = useState<number>(100.0);
  const [dtFedNs, setDtFedNs] = useState<number>(100.0);
  const [timerMode, setTimerMode] = useState<number>(0);
  const [hrpwm, setHrpwm] = useState<boolean>(false);
  const [mcuTopo, setMcuTopo] = useState<string>('General-Purpose Timer');
  const [duty, setDuty] = useState<number>(0.4);
  const [phi, setPhi] = useState<number>(45.0);
  const [da, setDa] = useState<number>(0.3);
  const [db, setDb] = useState<number>(0.4);
  const [dcVal, setDcVal] = useState<number>(0.5);

  const [chipKey, setChipKey] = useState<string>('UC3842 / UC3843 / UC284x');
  const [icFswTarget, setIcFswTarget] = useState<number>(50.0);

  const [filterRes, setFilterRes] = useState<FilterResponse | null>(null);
  const [filterError, setFilterError] = useState<string | null>(null);
  const [timerRes, setTimerRes] = useState<TimerResponse | null>(null);
  const [timerError, setTimerError] = useState<string | null>(null);
  const [icRes, setIcRes] = useState<IcFreqRow[]>([]);
  const [icError, setIcError] = useState<string | null>(null);

  const applyPreset = (presetKey: string) => {
    switch (presetKey) {
      case 'c2000_epwm':
        setSysclkMhz(200.0);
        setFswKhz(100.0);
        setDtRedNs(100.0);
        setDtFedNs(100.0);
        setTimerMode(1);
        setHrpwm(true);
        setMcuTopo('TI C2000 ePWM');
        setDuty(0.4);
        break;
      case 'stm32_hrtim':
        setSysclkMhz(170.0);
        setFswKhz(200.0);
        setDtRedNs(50.0);
        setDtFedNs(50.0);
        setTimerMode(0);
        setHrpwm(true);
        setMcuTopo('STM32 HRTIM');
        setDuty(0.35);
        break;
      case 'stm32f4_tim':
        setSysclkMhz(84.0);
        setFswKhz(20.0);
        setDtRedNs(200.0);
        setDtFedNs(200.0);
        setTimerMode(0);
        setHrpwm(false);
        setMcuTopo('General-Purpose Timer');
        setDuty(0.5);
        break;
      case 'dac_high_res':
        setFPwmHz(100000);
        setVCc(3.3);
        setBits(12);
        setCSelUf(0.1);
        setVRipTargetMv(1.0);
        setTSetTargetMs(10.0);
        break;
      case 'dac_low_speed':
        setFPwmHz(1000);
        setVCc(5.0);
        setBits(8);
        setCSelUf(1.0);
        setVRipTargetMv(5.0);
        setTSetTargetMs(50.0);
        break;
      case 'dac_fast_settle':
        setFPwmHz(200000);
        setVCc(3.3);
        setBits(10);
        setCSelUf(0.01);
        setVRipTargetMv(2.0);
        setTSetTargetMs(2.0);
        break;
      case 'ic_uc3842':
        setChipKey('UC3842 / UC3843 / UC284x');
        setIcFswTarget(100.0);
        break;
      case 'ic_tl494':
        setChipKey('TL494 / KA7500 (Push-Pull)');
        setIcFswTarget(50.0);
        break;
      case 'ic_sg3525':
        setChipKey('SG3525 / KA3525 (Push-Pull)');
        setIcFswTarget(100.0);
        break;
      default:
        break;
    }
  };

  const handleFilterCalc = async () => {
    setFilterError(null);
    try {
      const response = await apiFetch('/api/calculate/pwm_mcu_ic/filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          f_pwm_hz: fPwmHz,
          v_cc: vCc,
          bits,
          c_sel_uf: cSelUf,
          v_rip_target_mv: vRipTargetMv,
          t_set_target_ms: tSetTargetMs,
        }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Low-pass filter calculation failed');
      }
      const data = await response.json();
      setFilterRes(data);
    } catch (e: any) {
      setFilterError(e.message);
    }
  };

  const handleTimerCalc = async () => {
    setTimerError(null);
    try {
      const response = await apiFetch('/api/calculate/pwm_mcu_ic/timer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sysclk_mhz: sysclkMhz,
          fsw_khz: fswKhz,
          dt_red_ns: dtRedNs,
          dt_fed_ns: dtFedNs,
          mode: timerMode,
          hrpwm,
          topo: mcuTopo,
          duty,
          phi,
          da,
          db,
          dc: dcVal,
        }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Timer ticks calculation failed');
      }
      const data = await response.json();
      setTimerRes(data);
    } catch (e: any) {
      setTimerError(e.message);
    }
  };

  const handleIcCalc = async () => {
    setIcError(null);
    try {
      const response = await apiFetch('/api/calculate/pwm_mcu_ic/ic_freq', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chip_key: chipKey,
          fsw_target_khz: icFswTarget,
        }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'IC frequency configuration calculation failed');
      }
      const data = await response.json();
      setIcRes(data);
    } catch (e: any) {
      setIcError(e.message);
    }
  };

  useEffect(() => {
    if (activeTab === 'filter') handleFilterCalc();
    else if (activeTab === 'timer') handleTimerCalc();
    else if (activeTab === 'ic_freq') handleIcCalc();
  }, [fPwmHz, vCc, bits, cSelUf, vRipTargetMv, tSetTargetMs, sysclkMhz, fswKhz, dtRedNs, dtFedNs, timerMode, hrpwm, mcuTopo, duty, phi, da, db, dcVal, chipKey, icFswTarget, activeTab]);

  const [chartOpt, setChartOpt] = useState<any>({});

  const getTimerCode = () => {
    if (mcuTopo === 'TI C2000 ePWM') {
      const arr = timerRes?.arr_val ?? 2000;
      const dbRed = timerRes?.dt_red_ticks ?? 20;
      const dbFed = timerRes?.dt_fed_ticks ?? 20;
      return `// TI C2000 ePWM Initialisation Code (SysClk = ${sysclkMhz}MHz, Fsw = ${fswKhz}kHz)
void InitEPwm1(void) {
    EPwm1Regs.TBPRD = ${arr};                   // Set timer period
    EPwm1Regs.TBPHS.bit.TBPHS = 0;             // Phase is 0
    EPwm1Regs.TBCTR = 0;                       // Clear counter
    EPwm1Regs.TBCTL.bit.CTRMODE = ${timerMode === 1 ? 'TB_COUNT_UPDOWN' : 'TB_COUNT_UP'}; // ${timerMode === 1 ? 'Center' : 'Edge'} Aligned
    EPwm1Regs.TBCTL.bit.HSPCLKDIV = TB_DIV1;   // SysClk Pre-scale /1
    EPwm1Regs.TBCTL.bit.CLKDIV = TB_DIV1;      
    
    // Setup shadow register loads
    EPwm1Regs.CMPCTL.bit.LOADAMODE = CC_CTR_ZERO;
    EPwm1Regs.CMPA.bit.CMPA = ${(arr * duty).toFixed(0)};              // Set compare A value (Duty = ${(duty*100).toFixed(1)}%)
    
    // Active high complementary with dead-time
    EPwm1Regs.DBCTL.bit.OUT_MODE = DB_FULL_ENABLE;
    EPwm1Regs.DBCTL.bit.POLSEL = DB_ACTV_HIC;  // Complementary
    EPwm1Regs.DBCTL.bit.IN_MODE = DBA_ALL;
    EPwm1Regs.DBRED.bit.DBRED = ${dbRed.toFixed(0)};               // RED = ${dtRedNs} ns
    EPwm1Regs.DBFED.bit.DBFED = ${dbFed.toFixed(0)};               // FED = ${dtFedNs} ns
    
    ${hrpwm ? `// Enable HRPWM
    EPwm1Regs.HRCNFG.all = 0x0;
    EPwm1Regs.HRCNFG.bit.EDGMODE = HR_BEG;     // MEP control on rising/falling edge
    EPwm1Regs.HRCNFG.bit.CTLMODE = HR_CMP;
    EPwm1Regs.HRCNFG.bit.HRLOAD = HR_CTR_ZERO;` : ''}
}`;
    } else if (mcuTopo === 'STM32 HRTIM') {
      const arr = timerRes?.arr_val ?? 1700;
      const dbRed = timerRes?.dt_red_ticks ?? 17;
      const dbFed = timerRes?.dt_fed_ticks ?? 17;
      return `/* STM32 HRTIM (High Resolution Timer) Initialisation (SysClk = ${sysclkMhz}MHz) */
void MX_HRTIM1_Init(void) {
    HRTIM_TimeBaseCfgTypeDef pTimeBaseCfg = {0};
    HRTIM_CompareCfgTypeDef pCompareCfg = {0};
    HRTIM_DeadTimeCfgTypeDef pDeadTimeCfg = {0};

    // Configure Timer A
    pTimeBaseCfg.Period = ${arr};              // Fsw = ${fswKhz}kHz
    pTimeBaseCfg.PrescalerRatio = HRTIM_PRESCALERRATIO_DIV1;
    pTimeBaseCfg.RepetitionCounter = 0;
    HAL_HRTIM_TimeBaseConfig(&hhrtim, HRTIM_TIMERINDEX_TIMER_A, &pTimeBaseCfg);

    pCompareCfg.CompareValue = ${(arr * duty).toFixed(0)};          // Duty = ${(duty*100).toFixed(1)}%
    HAL_HRTIM_CompareConfig(&hhrtim, HRTIM_TIMERINDEX_TIMER_A, HRTIM_COMPAREUNIT_1, &pCompareCfg);

    // Deadtime insertion
    pDeadTimeCfg.Prescaler = HRTIM_TIMDEADTIME_PRESCALER_DIV1;
    pDeadTimeCfg.RisingValue = ${dbRed.toFixed(0)};            // RED = ${dtRedNs} ns
    pDeadTimeCfg.RisingSign = HRTIM_TIMDEADTIME_RISINGSIGN_POSITIVE;
    pDeadTimeCfg.FallingValue = ${dbFed.toFixed(0)};           // FED = ${dtFedNs} ns
    pDeadTimeCfg.FallingSign = HRTIM_TIMDEADTIME_FALLINGSIGN_POSITIVE;
    HAL_HRTIM_DeadTimeConfig(&hhrtim, HRTIM_TIMERINDEX_TIMER_A, &pDeadTimeCfg);
}`;
    } else {
      const arr = timerRes?.arr_val ?? 840;
      return `// STM32 Standard General Purpose Timer Init (SysClk = ${sysclkMhz}MHz)
void MX_TIM1_Init(void) {
    TIM_OC_InitTypeDef sConfigOC = {0};
    TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

    htim1.Instance = TIM1;
    htim1.Init.Prescaler = 0;
    htim1.Init.CounterMode = ${timerMode === 1 ? 'TIM_COUNTERMODE_CENTERALIGNED1' : 'TIM_COUNTERMODE_UP'};
    htim1.Init.Period = ${arr};                 // Fsw = ${fswKhz}kHz
    htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim1.Init.RepetitionCounter = 0;
    HAL_TIM_PWM_Init(&htim1);

    sConfigOC.OCMode = TIM_OCMODE_PWM1;
    sConfigOC.Pulse = ${(arr * duty).toFixed(0)};               // Duty = ${(duty*100).toFixed(1)}%
    sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
    sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH; // Complementary
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
    sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
    HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1);

    // Deadtime configuration
    sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
    sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
    sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
    sBreakDeadTimeConfig.DeadTime = ${(dtRedNs * sysclkMhz / 1000).toFixed(0)}; // Deadtime = ${dtRedNs} ns
    sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
    HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig);
}`;
    }
  };

  const renderTabChart = () => {
    if (activeTab === 'timer') {
      const period = 1000;
      const d_ticks = period * duty;
      const red_prop = (dtRedNs / (1e6 / fswKhz)) * period;
      const fed_prop = (dtFedNs / (1e6 / fswKhz)) * period;
      
      const xData: number[] = [];
      const highSide: number[] = [];
      const lowSide: number[] = [];
      
      for (let i = 0; i <= 200; i++) {
        const t = (i / 200) * period;
        xData.push(parseFloat((t / period).toFixed(3)));
        
        let valA = 0;
        if (t >= red_prop && t < d_ticks) {
          valA = 1;
        }
        highSide.push(valA);
        
        let valB = 0;
        if (t >= (d_ticks + fed_prop) && t < period) {
          valB = 1;
        }
        lowSide.push(valB);
      }
      
      const option = {
        backgroundColor: 'transparent',
        title: {
          text: 'Complementary PWM Dead-Time Timing Waveforms',
          textStyle: { color: '#f1f5f9', fontSize: 11, fontWeight: 'bold' },
          left: 'center',
          top: '2%'
        },
        legend: {
          data: ['PWM_A (High-Side)', 'PWM_B (Low-Side)'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          bottom: '2%'
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: 'rgba(56, 189, 248, 0.4)',
          borderWidth: 1,
          textStyle: { color: '#f1f5f9', fontSize: 11 },
          extraCssText: 'backdrop-filter: blur(8px);',
          formatter: (params: any) => {
            const phase = (params[0].axisValue * 360).toFixed(0);
            return `<div class="p-1">
              <div class="text-[9px] text-slate-400 font-bold mb-1">Phase Angle: <span class="text-white">${phase}°</span></div>
              <div class="flex items-center gap-1.5 text-xs text-rose-400">
                <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                <span>PWM_A: </span>
                <span class="font-mono font-bold">${params[0].data === 1 ? 'ON (High)' : 'OFF (Low)'}</span>
              </div>
              <div class="flex items-center gap-1.5 text-xs text-cyan-400 mt-0.5">
                <span class="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span>PWM_B: </span>
                <span class="font-mono font-bold">${params[1].data === 1 ? 'ON (High)' : 'OFF (Low)'}</span>
              </div>
            </div>`;
          }
        },
        grid: { left: '8%', right: '8%', bottom: '22%', top: '22%', containLabel: true },
        xAxis: {
          type: 'category',
          data: xData,
          axisLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9, formatter: (val: any) => `${(val * 100).toFixed(0)}%` },
          name: 'Period',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 }
        },
        yAxis: {
          type: 'value',
          min: -0.2,
          max: 1.2,
          axisLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
          axisLabel: { show: false },
          splitLine: { show: false }
        },
        series: [
          {
            name: 'PWM_A (High-Side)',
            type: 'line',
            step: 'end',
            data: highSide,
            lineStyle: {
              color: '#fb7185',
              width: 3,
              shadowBlur: 8,
              shadowColor: 'rgba(251, 113, 133, 0.5)'
            },
            showSymbol: false
          },
          {
            name: 'PWM_B (Low-Side)',
            type: 'line',
            step: 'end',
            data: lowSide,
            lineStyle: {
              color: '#38bdf8',
              width: 3,
              shadowBlur: 8,
              shadowColor: 'rgba(56, 189, 248, 0.5)'
            },
            showSymbol: false
          }
        ]
      };
      setChartOpt(option);
    } else if (activeTab === 'filter') {
      if (!filterRes) return;
      const fc_hz = filterRes.fc_hz;
      const f_arr: number[] = [];
      const mag_db: number[] = [];
      const phase_deg: number[] = [];
      
      const steps = 100;
      const f_start = Math.max(10, fc_hz / 50.0);
      const f_end = fc_hz * 100.0;
      const logStart = Math.log10(f_start);
      const logEnd = Math.log10(f_end);
      const logStep = (logEnd - logStart) / steps;
      
      for (let i = 0; i <= steps; i++) {
        const f = Math.pow(10, logStart + i * logStep);
        f_arr.push(Math.round(f));
        const w = 2.0 * Math.PI * f;
        const R = filterRes.r_nearest_ohm;
        const C = cSelUf * 1e-6;
        const ratio = w * R * C;
        
        const gain = 20.0 * Math.log10(1.0 / Math.sqrt(1.0 + ratio * ratio));
        const phase = -Math.atan(ratio) * 180.0 / Math.PI;
        
        mag_db.push(parseFloat(gain.toFixed(2)));
        phase_deg.push(parseFloat(phase.toFixed(1)));
      }
      
      const option = {
        backgroundColor: 'transparent',
        title: {
          text: 'PWM DAC LPF RC Bode Frequency Response',
          textStyle: { color: '#f1f5f9', fontSize: 11, fontWeight: 'bold' },
          left: 'center',
          top: '2%'
        },
        legend: {
          data: ['Magnitude (dB)', 'Phase (°)'],
          textStyle: { color: '#94a3b8', fontSize: 9 },
          bottom: '2%'
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: 'rgba(56, 189, 248, 0.4)',
          borderWidth: 1,
          textStyle: { color: '#f1f5f9', fontSize: 11 },
          extraCssText: 'backdrop-filter: blur(8px);',
          formatter: (params: any) => {
            const f = params[0].axisValue;
            return `<div class="p-1">
              <div class="text-[9px] text-slate-400 font-bold mb-1">Frequency: <span class="text-white">${f} Hz</span></div>
              <div class="flex items-center gap-1.5 text-xs text-rose-450">
                <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                <span>Gain: </span>
                <span class="font-mono font-bold">${params[0].data.toFixed(2)} dB</span>
              </div>
              <div class="flex items-center gap-1.5 text-xs text-cyan-400 mt-0.5">
                <span class="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span>Phase: </span>
                <span class="font-mono font-bold">${params[1].data.toFixed(1)} °</span>
              </div>
            </div>`;
          }
        },
        grid: { left: '8%', right: '8%', bottom: '22%', top: '22%', containLabel: true },
        xAxis: {
          type: 'category',
          data: f_arr,
          axisLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          name: 'Hz',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 }
        },
        yAxis: [
          {
            type: 'value',
            name: 'Gain (dB)',
            nameTextStyle: { color: '#94a3b8', fontSize: 9 },
            axisLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(30, 41, 59, 0.6)', type: 'dashed' } }
          },
          {
            type: 'value',
            name: 'Phase (°)',
            min: -90,
            max: 0,
            nameTextStyle: { color: '#94a3b8', fontSize: 9 },
            axisLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
            axisLabel: { color: '#94a3b8', fontSize: 9 },
            splitLine: { show: false }
          }
        ],
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          {
            type: 'slider',
            start: 0,
            end: 100,
            height: 14,
            bottom: 4,
            textStyle: { color: '#64748b', fontSize: 8 },
            borderColor: 'rgba(30, 41, 59, 0.5)',
            handleSize: '100%',
            handleStyle: { color: 'rgba(56, 189, 248, 0.6)' }
          }
        ],
        series: [
          {
            name: 'Magnitude (dB)',
            type: 'line',
            data: mag_db,
            lineStyle: {
              color: '#fb7185',
              width: 3,
              shadowBlur: 8,
              shadowColor: 'rgba(251, 113, 133, 0.5)'
            },
            showSymbol: false
          },
          {
            name: 'Phase (°)',
            type: 'line',
            yAxisIndex: 1,
            data: phase_deg,
            lineStyle: {
              color: '#38bdf8',
              width: 3,
              shadowBlur: 8,
              shadowColor: 'rgba(56, 189, 248, 0.5)'
            },
            showSymbol: false
          }
        ]
      };
      setChartOpt(option);
    } else if (activeTab === 'ic_freq') {
      const rt_arr: number[] = [];
      const fsw_arr: number[] = [];
      const cStr = icRes?.[0]?.c_str || "1000 pF";
      const ct_val_pf = cStr === "Internal" ? 1000 : parseFloat(cStr) * (cStr.includes('nF') ? 1000 : 1);
      const ct_val_nf = ct_val_pf / 1000.0;
      
      for (let r = 5; r <= 150; r += 5) {
        rt_arr.push(r);
        let fsw = 0;
        switch (chipKey) {
          case 'UC3842 / UC3843 / UC284x':
            fsw = 1.72 / (r * ct_val_nf);
            break;
          case 'UC3844 / UC3845 (Max Duty 50%)':
            fsw = 0.86 / (r * ct_val_nf);
            break;
          case 'TL494 / KA7500 (Push-Pull)':
            fsw = 0.55 / (r * ct_val_nf);
            break;
          case 'SG3525 / KA3525 (Push-Pull)':
            fsw = 0.714 / (r * ct_val_nf);
            break;
          case 'NCP1252 (Current Mode)':
            fsw = 6250 / r;
            break;
          default:
            fsw = 1.72 / (r * ct_val_nf);
            break;
        }
        fsw_arr.push(parseFloat((fsw * 1000).toFixed(1)));
      }
      
      const option = {
        backgroundColor: 'transparent',
        title: {
          text: `Timing Resistor RT vs. Switching Frequency fsw (CT = ${icRes?.[0]?.c_str ?? '1 nF'})`,
          textStyle: { color: '#f1f5f9', fontSize: 11, fontWeight: 'bold' },
          left: 'center',
          top: '2%'
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          borderColor: 'rgba(56, 189, 248, 0.4)',
          borderWidth: 1,
          textStyle: { color: '#f1f5f9', fontSize: 11 },
          extraCssText: 'backdrop-filter: blur(8px);',
          formatter: (params: any) => {
            const rt = params[0].axisValue;
            const f = params[0].data;
            return `<div class="p-1">
              <div class="text-[9px] text-slate-400 font-bold mb-1">Timing Resistor RT: <span class="text-white">${rt} kΩ</span></div>
              <div class="flex items-center gap-1.5 text-xs text-cyan-400">
                <span class="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span>Switching Frequency: </span>
                <span class="font-mono font-bold">${f} kHz</span>
              </div>
            </div>`;
          }
        },
        grid: { left: '8%', right: '8%', bottom: '22%', top: '22%', containLabel: true },
        xAxis: {
          type: 'category',
          data: rt_arr,
          axisLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          name: 'kΩ',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 }
        },
        yAxis: {
          type: 'value',
          name: 'fsw (kHz)',
          nameTextStyle: { color: '#94a3b8', fontSize: 9 },
          axisLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.5)' } },
          axisLabel: { color: '#94a3b8', fontSize: 9 },
          splitLine: { lineStyle: { color: 'rgba(30, 41, 59, 0.6)', type: 'dashed' } }
        },
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          {
            type: 'slider',
            start: 0,
            end: 100,
            height: 14,
            bottom: 4,
            textStyle: { color: '#64748b', fontSize: 8 },
            borderColor: 'rgba(30, 41, 59, 0.5)',
            handleSize: '100%',
            handleStyle: { color: 'rgba(56, 189, 248, 0.6)' }
          }
        ],
        series: [
          {
            name: 'Switching Frequency',
            type: 'line',
            data: fsw_arr,
            smooth: true,
            lineStyle: {
              color: '#38bdf8',
              width: 3,
              shadowBlur: 8,
              shadowColor: 'rgba(56, 189, 248, 0.5)'
            },
            showSymbol: false,
            markLine: {
              silent: true,
              lineStyle: { color: '#f43f5e', type: 'dashed', width: 1.5 },
              label: {
                formatter: `Target: ${icFswTarget}kHz`,
                position: 'insideEndTop',
                color: '#fb7185',
                fontSize: 9
              },
              data: [{ yAxis: icFswTarget }]
            }
          }
        ]
      };
      setChartOpt(option);
    }
  };

  useEffect(() => {
    renderTabChart();
  }, [activeTab, sysclkMhz, fswKhz, dtRedNs, dtFedNs, duty, hrpwm, mcuTopo, timerMode, filterRes, icRes, chipKey, icFswTarget]);

  const getIcFormulaLatex = () => {
    switch (chipKey) {
      case 'UC3842 / UC3843 / UC284x':
        return 'F_{sw} = F_{osc} = \\frac{1.72}{R_T C_T}';
      case 'UC3844 / UC3845 (Max Duty 50%)':
        return 'F_{sw} = \\frac{F_{osc}}{2} = \\frac{0.86}{R_T C_T}';
      case 'TL494 / KA7500 (Push-Pull)':
        return 'F_{sw} = \\frac{F_{osc}}{2} = \\frac{0.55}{R_T C_T}';
      case 'SG3525 / KA3525 (Push-Pull)':
        return 'F_{sw} = \\frac{F_{osc}}{2} \\approx \\frac{0.714}{R_T C_T}';
      case 'NCP1252 (Current Mode)':
        return 'F_{sw}\\text{(kHz)} = \\frac{6250}{R_T\\text{(k}\\Omega\\text{)}}';
      default:
        return '';
    }
  };

  const renderCardContent = (key: string) => {
    switch (key) {
      case 'input':
        return (
          <ScrollableContent className="p-4 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2 mb-3">
              <span className="text-xs font-bold text-white">Input Configuration Parameters</span>
            </div>

            {/* Presets Bar */}
            <div className="bg-slate-950/40 p-2.5 rounded-lg border border-slate-850">
              <span className="text-[9px] text-slate-500 font-bold block mb-2 uppercase">Industrial Typical Topology & Driver Presets</span>
              {activeTab === 'timer' ? (
                <div className="flex flex-wrap gap-1.5">
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('c2000_epwm')}>C2000 ePWM</Button>
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('stm32_hrtim')}>STM32 HRTIM</Button>
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('stm32f4_tim')}>STM32F4 Standard</Button>
                </div>
              ) : activeTab === 'filter' ? (
                <div className="flex flex-wrap gap-1.5">
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('dac_high_res')}>High-Precision DAC</Button>
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('dac_low_speed')}>Low-Speed DAC</Button>
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('dac_fast_settle')}>Fast-Settling DAC</Button>
                </div>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('ic_uc3842')}>UC3842 (100kHz)</Button>
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('ic_tl494')}>TL494 (50kHz)</Button>
                  <Button size="sm" variant="outline" className="text-[9px] h-6 border-slate-855 hover:bg-slate-900 px-2 py-0" onClick={() => applyPreset('ic_sg3525')}>SG3525 (100kHz)</Button>
                </div>
              )}
            </div>

            {activeTab === 'timer' && (
              <div className="space-y-4 animate-fade-in">
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-355 block">Timer Clock & Presets</span>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[8px] text-slate-550">Peripheral Clock SysClk (MHz)</label>
                    <input type="number" value={sysclkMhz} onChange={(e) => setSysclkMhz(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[8px] text-slate-550">MCU Peripheral Preset</label>
                    <select value={mcuTopo} onChange={(e) => setMcuTopo(e.target.value)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-300 outline-none focus:border-cyan-500">
                      <option value="General-Purpose Timer">General-Purpose Timer</option>
                      <option value="TI C2000 ePWM">TI C2000 ePWM</option>
                      <option value="STM32 HRTIM">STM32 HRTIM High-Resolution Timer</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2 pt-1">
                    <input type="checkbox" id="hrpwm-chk" checked={hrpwm} onChange={(e) => setHrpwm(e.target.checked)} className="cursor-pointer" />
                    <label htmlFor="hrpwm-chk" className="text-[9px] text-slate-350 cursor-pointer">Enable High-Resolution Microsteps (HRPWM / HRTIM)</label>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-355 block">Switching Frequency & Duty</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Frequency fsw (kHz)</label>
                      <input type="number" value={fswKhz} onChange={(e) => setFswKhz(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Duty Cycle (0~1)</label>
                      <input type="number" step="0.05" value={duty} onChange={(e) => setDuty(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500" />
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-355 block">Dead-Time & Counter Mode</span>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[8px] text-slate-550">Counter Direction Mode</label>
                    <select value={timerMode} onChange={(e) => setTimerMode(parseInt(e.target.value))} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-300 outline-none focus:border-cyan-500">
                      <option value={0}>Up-Counting (Edge-Aligned)</option>
                      <option value={1}>Up-Down Counting (Center-Aligned)</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Rising Edge Dead-Time RED (ns)</label>
                      <input type="number" value={dtRedNs} onChange={(e) => setDtRedNs(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Falling Edge Dead-Time FED (ns)</label>
                      <input type="number" value={dtFedNs} onChange={(e) => setDtFedNs(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500" />
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-355 block">Multi-Phase Interleaved Phase Shift</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Phase Shift Phi (deg)</label>
                      <input type="number" value={phi} onChange={(e) => setPhi(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Phase A Duty da</label>
                      <input type="number" step="0.05" value={da} onChange={(e) => setDa(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Phase B Duty db</label>
                      <input type="number" step="0.05" value={db} onChange={(e) => setDb(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Phase C Duty dc</label>
                      <input type="number" step="0.05" value={dcVal} onChange={(e) => setDcVal(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'filter' && (
              <div className="space-y-4 animate-fade-in">
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-355 block">PWM DAC Carrier & Capacitance</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Carrier Frequency (Hz)</label>
                      <input type="number" value={fPwmHz} onChange={(e) => setFPwmHz(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">PWM Amplitude Vcc (V)</label>
                      <input type="number" value={vCc} onChange={(e) => setVCc(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">DAC Resolution (Bits)</label>
                      <input type="number" value={bits} onChange={(e) => setBits(parseInt(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Capacitance C (μF)</label>
                      <input type="number" step="0.01" value={cSelUf} onChange={(e) => setCSelUf(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-355 block">DAC Filter Attenuation Limits</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Ripple Limit (mV)</label>
                      <input type="number" step="0.1" value={vRipTargetMv} onChange={(e) => setVRipTargetMv(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-[8px] text-slate-550">Settling Limit (ms)</label>
                      <input type="number" step="0.1" value={tSetTargetMs} onChange={(e) => setTSetTargetMs(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none" />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'ic_freq' && (
              <div className="space-y-4 animate-fade-in">
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/10 space-y-2.5">
                  <span className="text-[10px] font-bold text-slate-355 block">Active PWM Controller IC Preset</span>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[8px] text-slate-550">Controller IC Part Number</label>
                    <select value={chipKey} onChange={(e) => setChipKey(e.target.value)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-300 outline-none focus:border-cyan-500">
                      <option value="UC3842 / UC3843 / UC284x">UC3842 / UC3843 / UC284x Series</option>
                      <option value="UC3844 / UC3845 (Max Duty 50%)">UC3844 / UC3845 (Divided Flyback)</option>
                      <option value="TL494 / KA7500 (Push-Pull)">TL494 / KA7500 (Dual Output)</option>
                      <option value="SG3525 / KA3525 (Push-Pull)">SG3525 / KA3525 (Push-Pull / Half-Bridge)</option>
                      <option value="NCP1252 (Current Mode)">NCP1252 (Current Mode)</option>
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[8px] text-slate-550">Target Switching Frequency fsw (kHz)</label>
                    <input type="number" value={icFswTarget} onChange={(e) => setIcFswTarget(parseFloat(e.target.value) || 0)} className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 outline-none focus:border-cyan-500" />
                  </div>
                </div>
              </div>
            )}
          </ScrollableContent>
        );

      case 'schematic':
        return (
          <ScrollableContent className="p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Compass className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-white">
                  {activeTab === 'timer' ? 'Equivalent Schematic & Register C Init' : 'Equivalent Circuit Schematic'}
                </span>
              </div>
              {activeTab === 'timer' && (
                <div className="flex gap-1 bg-slate-950/40 p-0.5 rounded border border-slate-800">
                  <button
                    onClick={() => setActiveTimingTab('complementary')}
                    className={`px-2 py-0.5 rounded text-[8px] font-bold border-0 cursor-pointer ${
                      activeTimingTab === 'complementary' ? 'bg-cyan-500/20 text-cyan-300' : 'bg-transparent text-slate-500 hover:text-slate-350'
                    }`}
                  >
                    Complementary Dead-Time
                  </button>
                  <button
                    onClick={() => setActiveTimingTab('hrpwm')}
                    className={`px-2 py-0.5 rounded text-[8px] font-bold border-0 cursor-pointer ${
                      activeTimingTab === 'hrpwm' ? 'bg-cyan-500/20 text-cyan-300' : 'bg-transparent text-slate-500 hover:text-slate-350'
                    }`}
                  >
                    HRPWM Microsteps
                  </button>
                </div>
              )}
            </div>
            
            <div className={activeTab === 'timer' ? "grid grid-cols-1 lg:grid-cols-2 gap-4" : "grid grid-cols-1 gap-4"}>
              <div className="flex flex-col bg-slate-900/20 p-3 rounded-xl border border-slate-850 justify-center items-center">
                <span className="text-[10px] font-bold text-slate-455 self-start mb-2">Equivalent Circuit Schematic</span>
                <div className="flex justify-center items-center w-full min-h-[160px]">
                  {activeTab === 'timer' ? (
                    activeTimingTab === 'complementary' ? (
                      <svg width="100%" height="150" viewBox="0 0 600 150">
                        <path d="M 50 30 L 150 30 L 150 70 L 300 70 L 300 30 L 400 30 L 400 70 L 550 70" fill="none" stroke="#fb7185" strokeWidth="2.5" />
                        <text x="560" y="45" className="text-[9px] fill-rose-400 font-mono font-bold">PWM_A (High-Side)</text>
                        <path d="M 50 120 L 165 120 L 165 80 L 285 80 L 285 120 L 415 120 L 415 80 L 550 80" fill="none" stroke="#38bdf8" strokeWidth="2.5" />
                        <text x="560" y="95" className="text-[9px] fill-sky-400 font-mono font-bold">PWM_B (Low-Side)</text>
                        <line x1="150" y1="20" x2="150" y2="130" stroke="#f59e0b" strokeWidth="1" strokeDasharray="3" />
                        <line x1="165" y1="20" x2="165" y2="130" stroke="#f59e0b" strokeWidth="1" strokeDasharray="3" />
                        <path d="M 150 55 L 165 55" stroke="#f59e0b" strokeWidth="1.5" />
                        <text x="145" y="15" className="text-[8px] fill-amber-500 font-mono font-bold">RED ({dtRedNs} ns)</text>
                        <line x1="285" y1="20" x2="285" y2="130" stroke="#f59e0b" strokeWidth="1" strokeDasharray="3" />
                        <line x1="300" y1="20" x2="300" y2="130" stroke="#f59e0b" strokeWidth="1" strokeDasharray="3" />
                        <path d="M 300 55 L 285 55" stroke="#f59e0b" strokeWidth="1.5" />
                        <text x="280" y="15" className="text-[8px] fill-amber-500 font-mono font-bold">FED ({dtFedNs} ns)</text>
                      </svg>
                    ) : (
                      <svg width="100%" height="150" viewBox="0 0 600 150">
                        {[100, 150, 200, 250, 300, 350, 400, 450, 500].map((x) => (
                          <line key={x} x1={x} y1="20" x2={x} y2="120" stroke="#1e293b" strokeWidth="0.8" strokeDasharray="2" />
                        ))}
                        <text x="100" y="15" textAnchor="middle" className="text-[8px] fill-slate-500 font-mono">CLK Tick N</text>
                        <text x="200" y="15" textAnchor="middle" className="text-[8px] fill-slate-500 font-mono">Tick N+1</text>
                        <text x="300" y="15" textAnchor="middle" className="text-[8px] fill-slate-500 font-mono">Tick N+2</text>
                        <text x="400" y="15" textAnchor="middle" className="text-[8px] fill-slate-500 font-mono">Tick N+3</text>
                        <path d="M 50 80 L 200 80 L 200 40 L 450 40" fill="none" stroke="#64748b" strokeWidth="1.5" strokeDasharray="3" />
                        <text x="460" y="45" className="text-[9px] fill-slate-500 font-mono">Coarse CMPA Boundary</text>
                        <path d="M 50 110 L 235 110 L 235 70 L 450 70" fill="none" stroke="#a855f7" strokeWidth="2.5" />
                        <text x="460" y="75" className="text-[9px] fill-purple-400 font-mono font-bold">HRPWM Microstep Edge (MEP)</text>
                        <line x1="200" y1="90" x2="235" y2="90" stroke="#a855f7" strokeWidth="1.5" />
                        <text x="195" y="102" className="text-[8px] fill-purple-300 font-mono">MEP Delay Step</text>
                      </svg>
                    )
                  ) : activeTab === 'filter' ? (
                    <svg width="100%" height="150" viewBox="0 0 600 150">
                      <rect x="50" y="60" width="45" height="30" rx="4" fill="#020617" stroke="#fb7185" strokeWidth="1.5" />
                      <path d="M 55 80 L 65 80 L 65 70 L 75 70 L 75 80 L 90 80" fill="none" stroke="#fb7185" strokeWidth="1.5" />
                      <text x="72" y="105" textAnchor="middle" className="text-[8px] fill-slate-400 font-sans">PWM Source</text>
                      <line x1="95" y1="75" x2="160" y2="75" stroke="#cbd5e1" strokeWidth="1.5" />
                      <rect x="160" y="65" width="60" height="20" rx="2" fill="#020617" stroke="#a855f7" strokeWidth="1.5" />
                      <text x="190" y="77" textAnchor="middle" className="text-[9px] fill-purple-300 font-bold font-mono">R_std</text>
                      <line x1="220" y1="75" x2="320" y2="75" stroke="#cbd5e1" strokeWidth="1.5" />
                      <line x1="320" y1="75" x2="320" y2="95" stroke="#cbd5e1" strokeWidth="1.5" />
                      <line x1="305" y1="95" x2="335" y2="95" stroke="#38bdf8" strokeWidth="2.5" />
                      <line x1="305" y1="102" x2="335" y2="102" stroke="#38bdf8" strokeWidth="2.5" />
                      <line x1="320" y1="102" x2="320" y2="120" stroke="#cbd5e1" strokeWidth="1.5" />
                      <line x1="300" y1="120" x2="340" y2="120" stroke="#475569" strokeWidth="1.5" />
                      <line x1="320" y1="120" x2="320" y2="130" stroke="#cbd5e1" strokeWidth="1.5" />
                      <line x1="300" y1="130" x2="340" y2="130" stroke="#475569" strokeWidth="1.5" />
                      <text x="345" y="103" className="text-[9px] fill-sky-400 font-bold font-mono">C_lpf ({cSelUf} uF)</text>
                      <line x1="320" y1="75" x2="420" y2="75" stroke="#cbd5e1" strokeWidth="1.5" />
                      <text x="430" y="78" className="text-[10px] fill-emerald-300 font-mono font-bold">V_dac (DC Level)</text>
                    </svg>
                  ) : (
                    <svg width="100%" height="150" viewBox="0 0 600 150">
                      <rect x="180" y="40" width="160" height="80" rx="8" fill="#020617" stroke="#38bdf8" strokeWidth="1.5" />
                      <text x="260" y="65" textAnchor="middle" className="text-xs fill-sky-400 font-bold font-mono">{chipKey}</text>
                      <text x="260" y="80" textAnchor="middle" className="text-[8px] fill-slate-500 font-mono">RT/CT Timing Pins</text>
                      <line x1="120" y1="60" x2="180" y2="60" stroke="#cbd5e1" strokeWidth="1.2" />
                      <rect x="80" y="50" width="40" height="20" rx="1" fill="#020617" stroke="#a855f7" strokeWidth="1.2" />
                      <text x="100" y="62" textAnchor="middle" className="text-[8px] fill-purple-300 font-mono font-bold">RT</text>
                      <line x1="50" y1="60" x2="80" y2="60" stroke="#cbd5e1" strokeWidth="1.2" />
                      <text x="35" y="63" className="text-[9px] fill-slate-450 font-mono">Vref</text>
                      <line x1="120" y1="100" x2="180" y2="100" stroke="#cbd5e1" strokeWidth="1.2" />
                      <line x1="105" y1="100" x2="120" y2="100" stroke="#cbd5e1" strokeWidth="1.2" />
                      <line x1="105" y1="92" x2="105" y2="108" stroke="#38bdf8" strokeWidth="2" />
                      <line x1="98" y1="92" x2="98" y2="108" stroke="#38bdf8" strokeWidth="2" />
                      <line x1="70" y1="100" x2="98" y2="100" stroke="#cbd5e1" strokeWidth="1.2" />
                      <line x1="60" y1="100" x2="70" y2="100" stroke="#cbd5e1" strokeWidth="1.2" />
                      <line x1="60" y1="95" x2="60" y2="105" stroke="#475569" strokeWidth="1.5" />
                      <text x="85" y="120" textAnchor="middle" className="text-[8px] fill-sky-400 font-mono font-bold">CT</text>
                    </svg>
                  )}
                </div>
              </div>
              
              {activeTab === 'timer' && (
                <div className="flex flex-col bg-slate-900/20 p-3 rounded-xl border border-slate-855 relative">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-bold text-slate-400">MCU Timer Register Initialization C Source</span>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-6 text-[9px] px-2 py-0 border border-slate-800 hover:bg-slate-800 flex items-center gap-1 text-slate-350 cursor-pointer animate-pulse"
                      onClick={() => {
                        navigator.clipboard.writeText(getTimerCode());
                      }}
                    >
                      <Copy className="w-3 h-3 text-cyan-400" />
                      Copy Code
                    </Button>
                  </div>
                  <pre className="p-3 bg-slate-950/80 rounded border border-slate-850 text-[10px] text-emerald-400 font-mono overflow-auto max-h-[160px] whitespace-pre select-all scrollbar-thin">
                    {getTimerCode()}
                  </pre>
                </div>
              )}
            </div>
          </ScrollableContent>
        );

      case 'results':
        return (
          <ScrollableContent className="p-4 space-y-6">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-white">Results & DRC Rule Checks</span>
            </div>
            
            {activeTab === 'timer' && timerRes && (
              <div className="space-y-4 animate-fade-in font-mono">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">ARR/PRD Register</span>
                    <div className="text-lg font-bold text-cyan-400">
                      {timerRes?.arr_val} <span className="text-[8px] text-slate-500 font-normal font-sans">Ticks</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">RED Dead-Time</span>
                    <div className="text-lg font-bold text-slate-200">
                      {(timerRes?.dt_red_ticks ?? 0).toFixed(1)} <span className="text-[8px] text-slate-500 font-normal font-sans">Ticks</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">FED Dead-Time</span>
                    <div className="text-lg font-bold text-slate-200">
                      {(timerRes?.dt_fed_ticks ?? 0).toFixed(1)} <span className="text-[8px] text-slate-500 font-normal font-sans">Ticks</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Effective Resolution</span>
                    <div className="text-lg font-bold text-emerald-400">
                      {(timerRes?.resolution_bits ?? 0).toFixed(1)} <span className="text-[8px] text-slate-500 font-normal font-sans">Bits</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Compare Value CMPA</span>
                    <div className="text-lg font-bold text-purple-400">
                      {((timerRes?.arr_val ?? 0) * duty).toFixed(0)} <span className="text-[8px] text-slate-500 font-normal font-sans">Ticks</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Clock Step Size</span>
                    <div className="text-lg font-bold text-rose-455">
                      {(timerRes?.step_ns ?? 0).toFixed(3)} <span className="text-[8px] text-slate-500 font-normal font-sans">ns</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                  <Card className="bg-[#0b0f19]/30 border-slate-850">
                    <CardHeader className="py-1.5 border-b border-slate-850">
                      <CardTitle className="text-[9px] font-bold text-slate-400 font-sans">TI C2000 ePWM Registers</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0 max-h-[140px] overflow-y-auto scrollbar-thin">
                      <table className="w-full text-[9px] text-left border-collapse text-slate-300">
                        <thead>
                          <tr className="bg-slate-950/40 text-slate-450 border-b border-slate-900">
                            <th className="px-2.5 py-1">Register</th>
                            <th className="px-2.5 py-1">Value</th>
                            <th className="px-2.5 py-1">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(timerRes?.c2000_rows ?? []).map((row) => (
                            <tr key={row.reg} className="border-b border-slate-900/60 hover:bg-slate-800/10">
                              <td className="px-2.5 py-1 text-cyan-400 font-bold">{row.reg}</td>
                              <td className="px-2.5 py-1">{row.val}</td>
                              <td className="px-2.5 py-1 text-slate-400 font-sans">{row.desc}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </CardContent>
                  </Card>

                  <Card className="bg-[#0b0f19]/30 border-slate-850">
                    <CardHeader className="py-1.5 border-b border-slate-850">
                      <CardTitle className="text-[9px] font-bold text-slate-400 font-sans">STM32 HRTIM Registers</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0 max-h-[140px] overflow-y-auto scrollbar-thin">
                      <table className="w-full text-[9px] text-left border-collapse text-slate-330">
                        <thead>
                          <tr className="bg-slate-950/40 text-slate-450 border-b border-slate-900">
                            <th className="px-2.5 py-1">Register</th>
                            <th className="px-2.5 py-1">Value</th>
                            <th className="px-2.5 py-1">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(timerRes?.stm32_rows ?? []).map((row) => (
                            <tr key={row.reg} className="border-b border-slate-900/60 hover:bg-slate-800/10">
                              <td className="px-2.5 py-1 text-rose-455 font-bold">{row.reg}</td>
                              <td className="px-2.5 py-1">{row.val}</td>
                              <td className="px-2.5 py-1 text-slate-400 font-sans">{row.desc}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'filter' && filterRes && (
              <div className="space-y-4 animate-fade-in font-mono">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Recommended RC Topology</span>
                    <div className="text-xs font-bold text-cyan-400 truncate pt-1 font-sans">
                      {filterRes?.recommended_topo}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Calculated Resistance R_calc</span>
                    <div className="text-lg font-bold text-slate-200">
                      {((filterRes?.r_calc_ohm ?? 0) / 1000.0).toFixed(2)} <span className="text-[8px] text-slate-500 font-normal font-sans">kΩ</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Standard Match R_std</span>
                    <div className="text-lg font-bold text-slate-200">
                      {((filterRes?.r_nearest_ohm ?? 0) / 1000.0).toFixed(2)} <span className="text-[8px] text-slate-500 font-normal font-sans">kΩ</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Cutoff Frequency fc</span>
                    <div className="text-lg font-bold text-emerald-400">
                      {((filterRes?.fc_hz ?? 0) / 1000.0).toFixed(2)} <span className="text-[8px] text-slate-500 font-normal font-sans">kHz</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Residual Carrier Ripple</span>
                    <div className="text-lg font-bold text-purple-400">
                      {(filterRes?.ripple_actual_mv ?? 0.0).toFixed(3)} <span className="text-[8px] text-slate-500 font-normal font-sans">mV</span>
                    </div>
                  </div>
                  <div className={`p-2.5 rounded-lg border bg-slate-900/30 flex flex-col gap-0.5 ${
                    (filterRes?.settle_actual_ms ?? 0) > tSetTargetMs ? 'border-red-500/40 bg-red-950/10' : 'border-slate-850'
                  }`}>
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Actual Settling Time</span>
                    <div className="text-lg font-bold text-rose-455">
                      {(filterRes?.settle_actual_ms ?? 0.0).toFixed(2)} <span className="text-[8px] text-slate-500 font-normal font-sans">ms</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'ic_freq' && icRes && icRes.length > 0 && (
              <div className="space-y-4 animate-fade-in font-mono">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Target Frequency</span>
                    <div className="text-lg font-bold text-cyan-400">
                      {(icFswTarget ?? 0.0).toFixed(1)} <span className="text-[8px] text-slate-500 font-normal font-sans">kHz</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Recommended RT</span>
                    <div className="text-lg font-bold text-slate-200">
                      {(icRes?.[0]?.rt_nearest_kohm ?? 0.0).toFixed(2)} <span className="text-[8px] text-slate-500 font-normal font-sans">kΩ</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Matched CT</span>
                    <div className="text-lg font-bold text-slate-200 font-sans">
                      {icRes?.[0]?.c_str}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Actual Oscillation Freq</span>
                    <div className="text-lg font-bold text-emerald-400">
                      {(icRes?.[0]?.fsw_actual_khz ?? 0.0).toFixed(2)} <span className="text-[8px] text-slate-500 font-normal font-sans">kHz</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Frequency Deviation</span>
                    <div className="text-lg font-bold text-purple-400">
                      {(Math.abs((icRes?.[0]?.fsw_actual_khz ?? 0) - icFswTarget) / Math.max(icFswTarget, 1e-6) * 100.0).toFixed(2)} <span className="text-[8px] text-slate-500 font-normal font-sans">%</span>
                    </div>
                  </div>
                  <div className="p-2.5 rounded-lg border border-slate-850 bg-slate-900/30 flex flex-col gap-0.5">
                    <span className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold font-sans">Recommended Tolerance</span>
                    <div className="text-lg font-bold text-rose-455">
                      1.0 <span className="text-[8px] text-slate-500 font-normal font-sans">%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* DRC Section */}
            <div className="p-3.5 rounded-xl border border-slate-850 bg-slate-900/10 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
                <span>Real-Time DRC Rule Verification</span>
              </div>
              
              <div className="space-y-2 text-[10px]">
                {activeTab === 'timer' && (
                  <>
                    {(() => {
                      const tSwNs = (1 / (fswKhz * 1000)) * 1e9;
                      const totalDtNs = dtRedNs + dtFedNs;
                      const dtRatio = totalDtNs / tSwNs * 100;
                      if (dtRatio >= 30) {
                        return (
                          <div className="p-2 bg-red-950/20 border border-red-500/30 rounded text-rose-355">
                            <span className="font-bold">Excessive Dead-Time Warning: </span>
                            Total dead-time {totalDtNs.toFixed(0)} ns occupies {dtRatio.toFixed(1)}% of switching period (recommended &lt; 30%), significantly reducing available duty cycle and inverter voltage gain.
                          </div>
                        );
                      }
                      if (totalDtNs > (duty * tSwNs)) {
                        return (
                          <div className="p-2 bg-red-950/20 border border-red-500/30 rounded text-rose-355">
                            <span className="font-bold">Fatal: Dead-Time Overlap! </span>
                            Dead-time ({totalDtNs.toFixed(0)} ns) exceeds pulse width ({(duty * tSwNs).toFixed(0)} ns), causing pulse skipping or shoot-through.
                          </div>
                        );
                      }
                      return (
                        <div className="p-2 bg-emerald-950/20 border border-emerald-500/20 rounded text-emerald-400">
                          <span className="font-bold">Dead-time verified: </span>
                          Dead-time ({totalDtNs.toFixed(0)} ns) represents {dtRatio.toFixed(1)}% of the period, ensuring safe half-bridge commutation.
                        </div>
                      );
                    })()}

                    {timerRes && (
                      timerRes.resolution_bits < 9 ? (
                        <div className="p-2 bg-amber-955/20 border border-amber-500/30 rounded text-amber-300">
                          <span className="font-bold">Low Timer Resolution: </span>
                          Effective modulation resolution is {timerRes.resolution_bits.toFixed(1)} bits (recommended &ge; 9.0 bits), risking limit-cycle oscillations in closed-loop voltage regulation.
                        </div>
                      ) : (
                        <div className="p-2 bg-emerald-950/20 border border-emerald-500/20 rounded text-emerald-400">
                          <span className="font-bold">High Timer Precision: </span>
                          Equivalent resolution reaches {timerRes.resolution_bits.toFixed(1)} bits, supporting fine loop adjustments.
                        </div>
                      )
                    )}
                  </>
                )}

                {activeTab === 'filter' && filterRes && (
                  <>
                    {(filterRes.settle_actual_ms ?? 0) > tSetTargetMs ? (
                      <div className="p-2 bg-red-955/20 border border-red-500/30 rounded text-rose-355">
                        <span className="font-bold">Settling Time Exceeded: </span>
                        LPF settling time {(filterRes.settle_actual_ms ?? 0).toFixed(2)} ms exceeds limit of {tSetTargetMs} ms.
                      </div>
                    ) : (
                      <div className="p-2 bg-emerald-950/20 border border-emerald-500/20 rounded text-emerald-400">
                        <span className="font-bold">Fast Settling Response: </span>
                        Settling time is {(filterRes.settle_actual_ms ?? 0).toFixed(2)} ms, meeting target limit.
                      </div>
                    )}

                    {(filterRes.ripple_actual_mv ?? 0) > vRipTargetMv ? (
                      <div className="p-2 bg-amber-955/20 border border-amber-500/30 rounded text-amber-300">
                        <span className="font-bold">Carrier Ripple Exceeded: </span>
                        Residual ripple {(filterRes.ripple_actual_mv ?? 0).toFixed(3)} mV exceeds limit of {vRipTargetMv} mV. Consider increasing C or raising PWM carrier frequency.
                      </div>
                    ) : (
                      <div className="p-2 bg-emerald-950/20 border border-emerald-500/20 rounded text-emerald-400">
                        <span className="font-bold">Clean DC Output: </span>
                        Residual carrier ripple is {(filterRes.ripple_actual_mv ?? 0).toFixed(3)} mV.
                      </div>
                    )}

                    {filterRes.r_nearest_ohm < 1000 ? (
                      <div className="p-2 bg-amber-955/20 border border-amber-500/30 rounded text-amber-300">
                        <span className="font-bold">Low Series Impedance: </span>
                        Resistance R_std is {filterRes.r_nearest_ohm} Ω, risking GPIO output pin overcurrent (recommended &gt; 1 kΩ).
                      </div>
                    ) : (
                      <div className="p-2 bg-emerald-950/20 border border-emerald-500/20 rounded text-emerald-400">
                        <span className="font-bold">Safe GPIO Drive Load: </span>
                        Resistance R_std {filterRes.r_nearest_ohm} Ω operates well within GPIO drive specs.
                      </div>
                    )}
                  </>
                )}

                {activeTab === 'ic_freq' && icRes && icRes.length > 0 && (
                  <>
                    {(() => {
                      const errorPct = Math.abs((icRes[0]?.fsw_actual_khz ?? 0) - icFswTarget) / Math.max(icFswTarget, 1e-6) * 100;
                      if (errorPct > 5) {
                        return (
                          <div className="p-2 bg-red-955/20 border border-red-500/30 rounded text-rose-355">
                            <span className="font-bold">Frequency Deviation Exceeded: </span>
                            Actual frequency under standard E-series RC {icRes[0]?.fsw_actual_khz?.toFixed(2)} kHz deviates by {errorPct.toFixed(2)}% (recommended &le; 5%).
                          </div>
                        );
                      }
                      return (
                        <div className="p-2 bg-emerald-950/20 border border-emerald-500/20 rounded text-emerald-400">
                          <span className="font-bold">Frequency Match Verified: </span>
                          Oscillation frequency is {icRes[0]?.fsw_actual_khz?.toFixed(2)} kHz (deviation {errorPct.toFixed(2)}%).
                        </div>
                      );
                    })()}

                    {(() => {
                      const rtVal = icRes[0]?.rt_nearest_kohm ?? 0;
                      if (rtVal < 5) {
                        return (
                          <div className="p-2 bg-amber-955/20 border border-amber-500/30 rounded text-amber-300">
                            <span className="font-bold">RT Too Small: </span>
                            RT is {rtVal.toFixed(2)} kΩ, increasing IC internal charge circuit power dissipation (recommended &ge; 5 kΩ).
                          </div>
                        );
                      }
                      if (rtVal > 150) {
                        return (
                          <div className="p-2 bg-amber-955/20 border border-amber-500/30 rounded text-amber-300">
                            <span className="font-bold">RT Too Large: </span>
                            RT is {rtVal.toFixed(2)} kΩ, making the circuit susceptible to dv/dt noise jitter (recommended &le; 150 kΩ).
                          </div>
                        );
                      }
                      return null;
                    })()}
                  </>
                )}
              </div>
            </div>

            {/* BOM Table */}
            <div className="p-3.5 rounded-xl border border-slate-850 bg-slate-900/10 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300">
                <ShoppingBag className="w-3.5 h-3.5 text-rose-455" />
                <span>Commercial BOM Recommendations</span>
              </div>
              
              {activeTab === 'timer' && (
                <div className="overflow-x-auto text-[10px] text-slate-300 font-mono">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-slate-950/60 text-slate-450 border-b border-slate-850 font-sans">
                        <th className="px-3 py-1.5 text-left">Component</th>
                        <th className="px-3 py-1.5 text-center">Standard Value</th>
                        <th className="px-3 py-1.5 text-right font-sans">Tolerance & Package</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-slate-900/40 bg-cyan-500/[0.02]">
                        <td className="px-3 py-2 font-bold text-cyan-200">MCU High-Speed Crystal OSC</td>
                        <td className="px-3 py-2 text-center text-slate-200">20.00 MHz</td>
                        <td className="px-3 py-2 text-right text-slate-400 font-sans">±10 ppm, 8 pF Load, 3225-SMD</td>
                      </tr>
                      <tr className="border-b border-slate-900/40">
                        <td className="px-3 py-2 font-bold">Crystal Load Cap CL1</td>
                        <td className="px-3 py-2 text-center">15 pF</td>
                        <td className="px-3 py-2 text-right text-slate-400 font-sans">50V, C0G/NP0, ±5%, 0603</td>
                      </tr>
                      <tr className="border-b border-slate-900/40">
                        <td className="px-3 py-2 font-bold">Crystal Load Cap CL2</td>
                        <td className="px-3 py-2 text-center">15 pF</td>
                        <td className="px-3 py-2 text-right text-slate-400 font-sans">50V, C0G/NP0, ±5%, 0603</td>
                      </tr>
                      <tr className="border-b border-slate-900/40">
                        <td className="px-3 py-2 font-bold">Oscillator Feedback Resistor Rf</td>
                        <td className="px-3 py-2 text-center">1.00 MΩ</td>
                        <td className="px-3 py-2 text-right text-slate-400 font-sans">1/10W, ±5%, 0603 Thick Film</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'filter' && filterRes && (
                <div className="overflow-x-auto text-[10px] text-slate-300 font-mono">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-slate-950/60 text-slate-450 border-b border-slate-850 font-sans">
                        <th className="px-3 py-1.5 text-left">Component</th>
                        <th className="px-3 py-1.5 text-center">Calculated</th>
                        <th className="px-3 py-1.5 text-center">Standard</th>
                        <th className="px-3 py-1.5 text-right font-sans">Deviation</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-slate-900/40 bg-cyan-500/[0.02]">
                        <td className="px-3 py-2 font-bold text-cyan-200">1st-Order Filter Resistor R</td>
                        <td className="px-3 py-2 text-center">{((filterRes?.r_calc_ohm ?? 0) / 1000.0).toFixed(2)} kΩ</td>
                        <td className="px-3 py-2 text-center text-purple-400">{(filterRes?.r_nearest_ohm / 1000.0).toFixed(2)} kΩ</td>
                        <td className="px-3 py-2 text-right text-emerald-450 font-sans">
                          {filterRes?.r_calc_ohm ? (((filterRes.r_nearest_ohm - filterRes.r_calc_ohm) / filterRes.r_calc_ohm) * 100.0).toFixed(2) : '0.00'}% (E96 1%)
                        </td>
                      </tr>
                      <tr className="border-b border-slate-900/40">
                        <td className="px-3 py-2 font-bold">1st-Order Filter Cap C</td>
                        <td className="px-3 py-2 text-center">{cSelUf.toFixed(3)} μF</td>
                        <td className="px-3 py-2 text-center text-purple-400">{cSelUf.toFixed(2)} μF</td>
                        <td className="px-3 py-2 text-right text-slate-400 font-sans">0.00% (5% NP0/Monolithic)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'ic_freq' && icRes && icRes.length > 0 && (
                <div className="overflow-x-auto text-[10px] text-slate-300 font-mono">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-slate-950/60 text-slate-450 border-b border-slate-850 font-sans">
                        <th className="px-3 py-1.5 text-left">Timing Cap CT</th>
                        <th className="px-3 py-1.5 text-center">Ideal RT</th>
                        <th className="px-3 py-1.5 text-center">Standard E96 RT</th>
                        <th className="px-3 py-1.5 text-center">Matched Freq</th>
                        <th className="px-3 py-1.5 text-right font-sans">Error</th>
                      </tr>
                    </thead>
                    <tbody>
                      {icRes.map((row, idx) => {
                        const isBest = idx === 0;
                        return (
                          <tr key={row.c_str} className={`border-b border-slate-900/40 ${
                            isBest ? 'bg-cyan-500/[0.02] text-cyan-200 font-semibold' : 'text-slate-350'
                          }`}>
                            <td className="px-3 py-2 flex items-center gap-1">
                              {row.c_str}
                              {isBest && <span className="text-[7px] bg-cyan-500/10 text-cyan-400 px-1 rounded border border-cyan-500/20 font-sans font-bold">BEST</span>}
                            </td>
                            <td className="px-3 py-2 text-center">{row.rt_ideal_kohm.toFixed(2)} kΩ</td>
                            <td className="px-3 py-2 text-center text-purple-400">{row.rt_nearest_kohm.toFixed(2)} kΩ</td>
                            <td className="px-3 py-2 text-center">{row.fsw_actual_khz.toFixed(1)} kHz</td>
                            <td className="px-3 py-2 text-right text-emerald-450">
                              {icFswTarget ? (((row.fsw_actual_khz - icFswTarget) / icFswTarget) * 100.0).toFixed(2) : '0.00'}%
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Physics Formulation Accordion */}
            <Accordion type="single" collapsible className="w-full border-t border-slate-900 pt-2 mt-4">
              <AccordionItem value="theory" className="border-none">
                <AccordionTrigger className="py-2 hover:no-underline text-slate-450 hover:text-slate-200 text-[10px] font-bold flex justify-between items-center cursor-pointer">
                  <span>Physical Equations & Mathematical Derivations</span>
                </AccordionTrigger>
                <AccordionContent className="text-[10px] text-slate-350 leading-relaxed space-y-3 mt-2 font-mono">
                  {activeTab === 'timer' && (
                    <div className="space-y-2">
                      <p><strong>1. ARR Register Period Calculation:</strong></p>
                      <p className="pl-2">Up-Counting (Edge-Aligned) Mode:</p>
                      <Latex math={"ARR = \\frac{f_{sysclk}}{f_{sw}} - 1"} block />
                      <p className="pl-2">Up-Down Counting (Center-Aligned) Mode:</p>
                      <Latex math={"ARR = \\frac{f_{sysclk}}{2 \\cdot f_{sw}}"} block />
                      <p className="mt-2"><strong>2. Dead-Time Ticks Conversion:</strong></p>
                      <Latex math={"RED_{ticks} = \\frac{RED \\cdot f_{sysclk}}{10^9}"} block />
                      <Latex math={"FED_{ticks} = \\frac{FED \\cdot f_{sysclk}}{10^9}"} block />
                    </div>
                  )}
                  {activeTab === 'filter' && (
                    <div className="space-y-2">
                      <p><strong>1. 1st-Order RC Low-Pass Transfer Function:</strong></p>
                      <Latex math={"H(s) = \\frac{1}{1 + R \\cdot C \\cdot s}"} block />
                      <p className="pl-2">Cutoff frequency:</p>
                      <Latex math={"f_c = \\frac{1}{2\\pi \\cdot R \\cdot C}"} block />
                      <p className="mt-2"><strong>2. Residual Carrier Ripple (worst-case @ D=0.5):</strong></p>
                      <Latex math={"\\Delta V_{rip} \\approx \\frac{V_{cc}}{4 \\cdot f_{pwm} \\cdot R \\cdot C}"} block />
                      <p className="mt-2"><strong>3. Settling Time (to 1 LSB for N-bit resolution):</strong></p>
                      <Latex math={"t_{settle} = R \\cdot C \\cdot \\ln(2^N)"} block />
                    </div>
                  )}
                  {activeTab === 'ic_freq' && (
                    <div className="space-y-2">
                      <p><strong>1. PWM Controller IC Oscillation Equations:</strong></p>
                      <p className="pl-2">Selected IC: <span className="font-semibold text-cyan-400">{chipKey}</span></p>
                      <div className="p-2 bg-slate-950/40 rounded border border-slate-900 text-center my-2">
                        <Latex math={getIcFormulaLatex()} block />
                      </div>
                      <p className="text-[9px] text-slate-500 leading-relaxed font-sans">
                        Note: Timing resistor RT is specified in kΩ, and timing capacitor CT in nF or pF. Push-pull / half-bridge controller ICs (such as TL494, SG3525, UC3844) include internal flip-flop dividers, halving the switching frequency relative to oscillator F_osc.
                      </p>
                    </div>
                  )}
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </ScrollableContent>
        );

      case 'chart':
        return (
          <ScrollableContent className="p-4 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <LineChart className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold text-white">Waveforms & Sweeps (ECharts)</span>
            </div>
            {chartOpt && chartOpt.series ? (
              <div className="h-[250px] w-full bg-slate-950/20 p-2 rounded-xl border border-slate-850">
                <ReactECharts option={chartOpt} style={{ height: '100%', width: '100%' }} notMerge={true} />
              </div>
            ) : (
              <div className="p-4 text-center text-xs text-slate-500">
                No chart data available. Please verify input parameters.
              </div>
            )}
          </ScrollableContent>
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-slate-950 text-slate-100 p-4 pb-0 gap-4">
      {/* Top Header */}
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
            <h1 className="text-base font-bold text-white tracking-tight">PWM Timer & Controller IC Peripherals</h1>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">Calculate RC low-pass DAC ripple; solve MCU timer registers and dead-time values; configure UC3842 / TL494 RT/CT oscillators.</p>
          </div>
        </div>
        <Button
          onClick={handleResetLayout}
          variant="outline"
          size="sm"
          className="text-[10px] px-2.5 py-1 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-355 rounded-lg cursor-pointer shrink-0"
        >
          Reset Layout
        </Button>
      </div>

      {(filterError || timerError || icError) && (
        <div className="flex-shrink-0 p-3 bg-red-950/20 border border-red-500/30 rounded-lg flex items-center gap-2.5 text-xs text-rose-300">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>Calculation Error: {filterError || timerError || icError}</span>
        </div>
      )}

      {/* Tabs Menu */}
      <div className="flex-shrink-0 flex gap-2 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
        {([
          { key: 'timer', label: 'MCU Timer Configuration', icon: null},
          { key: 'filter', label: 'PWM DAC LPF Filter', icon: null},
          { key: 'ic_freq', label: 'PWM IC Oscillator RC', icon: null}
        ] as const).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer border-none outline-none ${
              activeTab === tab.key
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md font-bold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 bg-transparent'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main DragDeck Canvas */}
      <div className="max-w-[1600px] mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-12 pr-1 relative min-h-0">
        <DragDeck
          isDesktop={isDesktop}
          leftSpan={leftSpan}
          rightSpan={rightSpan}
          leftCards={leftCards}
          rightCards={rightCards}
          draggedKey={draggedKey}
          renderCard={(key) => (
            <DragCard
              key={key}
              cardKey={key}
              height={key === 'input' ? undefined : cardHeights[key]}
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
          onDropOnColumn={handleDropOnColumn}
        />
      </div>
    </div>
  );
}
