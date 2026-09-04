/**
 * Hardware Engineering Toolbox - Desktop Frontend Interface
 * ==========================================================
 * Author: WenZhenJian-EE (https://github.com/WenZhenJian-EE)
 * License: MIT
 *
 * Desktop interface covering 30 design workstations for power electronics
 * and hardware engineering calculations (Buck, Flyback, magnetics, thermal,
 * loop compensation, and passive components).
 *
 * Open-sourced under the MIT License for community use and maintenance.
 */

import { apiFetch } from './lib/api';
import React, { useState, useEffect, useRef, Suspense, lazy } from 'react';
import { 
  Zap, 
  Activity, 
  Sliders, 
  ShieldAlert, 
  Cpu, 
  Globe, 
  CheckCircle2, 
  RefreshCw,
  Search,
  BookOpen,
  ArrowLeft,
  ChevronRight,
  Info,
  GripVertical,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Lock
} from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { useTranslation, zhModules, enModules } from './i18n';
const DigitalPidPanel = lazy(() => import('./components/DigitalPidPanel'));
const FilterPassivePanel = lazy(() => import('./components/FilterPassivePanel'));
const EmcToolboxPanel = lazy(() => import('./components/EmcToolboxPanel'));
const AdcConditioningPanel = lazy(() => import('./components/AdcConditioningPanel'));
const CurrentShuntPanel = lazy(() => import('./components/CurrentShuntPanel'));
const NtcCalculatorPanel = lazy(() => import('./components/NtcCalculatorPanel'));
const PwmMcuIcPanel = lazy(() => import('./components/PwmMcuIcPanel'));
const PcbToolboxPanel = lazy(() => import('./components/PcbToolboxPanel'));
const WireCopperBarPanel = lazy(() => import('./components/WireCopperBarPanel'));
const CapacitorToolboxPanel = lazy(() => import('./components/CapacitorToolboxPanel'));
const MagInductorPanel = lazy(() => import('./components/MagInductorPanel'));
const MagTransformerPanel = lazy(() => import('./components/MagTransformerPanel'));
const LoopCompensationPanel = lazy(() => import('./components/LoopCompensationPanel'));
const HeatsinkThermalPanel = lazy(() => import('./components/HeatsinkThermalPanel'));
const InputProtectionPanel = lazy(() => import('./components/InputProtectionPanel'));
const LdoThermalPanel = lazy(() => import('./components/LdoThermalPanel'));
const BuckDesignPanel = lazy(() => import('./components/BuckDesignPanel'));
const TvsZenerPanel = lazy(() => import('./components/TvsZenerPanel'));
const FlybackPanel = lazy(() => import('./components/FlybackPanel'));
const SnubberPanel = lazy(() => import('./components/SnubberPanel'));
const PowerDeviceSuitePanel = lazy(() => import('./components/PowerDeviceSuitePanel'));
const PowerDeviceDptPanel = lazy(() => import('./components/PowerDeviceDptPanel'));
const PowerDclinkRipplePanel = lazy(() => import('./components/PowerDclinkRipplePanel'));
const BatteryBmsPanel = lazy(() => import('./components/BatteryBmsPanel'));
const PowerAc3PhPanel = lazy(() => import('./components/PowerAc3PhPanel'));
const PowerBudgetPanel = lazy(() => import('./components/PowerBudgetPanel'));
const DatabaseManagementPanel = lazy(() => import('./components/DatabaseManagementPanel'));
const MagCoreLossPanel = lazy(() => import('./components/MagCoreLossPanel'));
const TransientThermalPanel = lazy(() => import('./components/TransientThermalPanel'));
const GateDriveMillerPanel = lazy(() => import('./components/GateDriveMillerPanel'));
// ------------------------------------------------------------------
// 0. ErrorBoundary & SkeletonLoader
// ------------------------------------------------------------------
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; activeModule: string | null; onBack: () => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  componentDidUpdate(prevProps: any) {
    if (prevProps.activeModule !== this.props.activeModule) {
      this.setState({ hasError: false, error: null });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-950/40 border border-red-500/20 rounded-xl space-y-4 min-h-[400px] w-full">
          <div className="p-3 bg-red-500/10 rounded-full text-rose-400">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h3 className="text-sm font-bold text-slate-200">Design Panel Rendering Error</h3>
          <p className="text-xs text-slate-400 max-w-lg leading-relaxed">
            An unexpected runtime error occurred while loading or rendering this panel:
            <code className="block mt-2 p-2.5 bg-slate-900 border border-slate-800 rounded font-mono text-[10px] text-rose-400 text-left overflow-x-auto max-w-full">
              {this.state.error?.message || String(this.state.error)}
            </code>
          </p>
          <div className="flex gap-3 mt-2">
            <button className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors cursor-pointer" onClick={() => this.setState({ hasError: false, error: null })}
            >
              Retry Load
            </button>
            <button
              onClick={this.props.onBack}
              className="px-4 py-1.5 bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-400 hover:to-cyan-500 text-white text-xs font-semibold rounded-lg shadow transition-colors border border-transparent cursor-pointer"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const SkeletonLoader: React.FC = () => {
  return (
    <div className="w-full min-h-[500px] grid grid-cols-1 lg:grid-cols-12 gap-6 animate-pulse">
      {/* Left Column Skeleton */}
      <div className="lg:col-span-5 flex flex-col gap-6">
        <div className="h-[480px] bg-[#0b0f19]/30 border border-slate-800/80 rounded-xl p-5 flex flex-col gap-4">
          <div className="h-3.5 bg-slate-800 rounded w-1/3"></div>
          <div className="h-[1px] bg-slate-800/80 my-1"></div>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex flex-col gap-1.5">
                <div className="h-2.5 bg-slate-800 rounded w-1/5"></div>
                <div className="h-8 bg-slate-900 border border-slate-800/50 rounded-lg"></div>
              </div>
            ))}
          </div>
          <div className="h-8 bg-slate-800 rounded mt-auto"></div>
        </div>
      </div>

      {/* Right Column Skeleton */}
      <div className="lg:col-span-7 flex flex-col gap-6">
        <div className="h-[520px] bg-[#0f172a]/40 border border-slate-800/80 rounded-xl p-5 flex flex-col gap-4">
          <div className="h-3.5 bg-slate-800 rounded w-1/4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-24 bg-slate-900 border border-slate-800/50 rounded-lg"></div>
            <div className="h-24 bg-slate-900 border border-slate-800/50 rounded-lg"></div>
          </div>
          <div className="h-3 bg-slate-800 rounded w-1/3 mt-2"></div>
          <div className="h-[220px] bg-slate-900 border border-slate-800/50 rounded-lg"></div>
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------
// 1. Latex Rendering Component (KaTeX)
// ------------------------------------------------------------------
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

// ------------------------------------------------------------------
// 2. Types
// ------------------------------------------------------------------
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

export type ModuleStatus = 'active' | 'template' | 'frozen';

interface ToolModule {
  id: string;
  name: string;
  description: string;
  category: string;
  isImplemented: boolean;
  status?: ModuleStatus;
}

const TOOL_MODULES: ToolModule[] = [
  // 1. Power Co-Design
  { 
    id: 'buck', 
    name: 'Buck Synchronous Converter', 
    description: 'Buck converter steady-state analysis, CCM/DCM inductor current waveforms, closed-loop Bode sweep, output capacitor ESR ripple sizing, and commercial BOM matching.', 
    category: '⚡ Power Co-Design', 
    isImplemented: true, 
    status: 'template' 
  },
  { 
    id: 'flyback', 
    name: 'Flyback Isolated Converter', 
    description: 'Isolated Flyback converter design, AP-method transformer selection, synchronous rectifier loss calculation, RCD snubber clamping, and closed-loop Bode analysis.', 
    category: '⚡ Power Co-Design', 
    isImplemented: true, 
    status: 'template' 
  },

  // 2. Magnetics & Basics
  { 
    id: 'mag_inductor', 
    name: 'Power Inductor Magnetic Design', 
    description: 'Calculate magnetic core, air gap, and winding wire specifications with Dowell high-frequency AC winding loss, fringing flux correction, and DC-bias saturation checking.', 
    category: '🧲 Magnetics & Basics', 
    isImplemented: true 
  },
  { 
    id: 'mag_transformer', 
    name: 'High-Frequency Integrated Transformer', 
    description: 'Design forward, flyback, and LLC integrated transformers, calculating AP core geometry sizing, AC resistance factor Fr, and equivalent leakage inductance.', 
    category: '🧲 Magnetics & Basics', 
    isImplemented: true 
  },
  { 
    id: 'mag_core_loss', 
    name: 'Magnetic Core Loss Evaluation (iGSE)', 
    description: 'Calculate core volumetric loss under non-sinusoidal excitation using the Improved Generalized Steinmetz Equation (iGSE) coupled with steady-state thermal rise.', 
    category: '🧲 Magnetics & Basics', 
    isImplemented: true 
  },
  { 
    id: 'snubber', 
    name: 'Switch Snubber & Clamp Design', 
    description: 'Design RC snubber and RCD clamp snubbers for turn-off ringing suppression using resonance frequency shift or analytical capacitor charging models.', 
    category: '🧲 Magnetics & Basics', 
    isImplemented: true 
  },
  { 
    id: 'power_dclink', 
    name: 'DC-Link Capacitor Ripple & Lifetime', 
    description: 'Calculate RMS ripple currents for single/three-phase inverters, evaluate ESR thermal dissipation, and predict aluminum electrolytic capacitor operating lifetimes.', 
    category: '🧲 Magnetics & Basics', 
    isImplemented: true 
  },
  { 
    id: 'power_ac_3ph', 
    name: '3-Phase AC & Vector Transforms', 
    description: 'Solve 3-phase Y-Delta impedance transformations, Clarke/Park alpha-beta/dq vector projections, reactive power compensation, and phase-locked loop (PLL) parameters.', 
    category: '🧲 Magnetics & Basics', 
    isImplemented: true 
  },

  // 3. Power Semiconductor & Thermal
  { 
    id: 'power_foster_thermal', 
    name: 'Transient Thermal & Foster RC Network', 
    description: 'Simulate power semiconductor dynamic junction temperature swings under transient pulse overload using high-order Foster RC thermal impedance state-space solvers.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },
  { 
    id: 'gate_drive_miller', 
    name: 'Gate Drive & Miller Effect Verification', 
    description: 'Verify high-speed switching transistors (SiC/GaN) against gate dv/dt parasitic Miller turn-on, dead-time switching losses, and ZVS turn-on criteria.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },
  { 
    id: 'heatsink', 
    name: 'Heatsink Thermal Resistance & Sizing', 
    description: 'Calculate natural and forced-convection equivalent thermal resistance, fin geometry spacing, air velocity Reynolds numbers, and multi-node thermal models.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },
  { 
    id: 'ldo_thermal', 
    name: 'LDO Linear Regulator & Thermal Dissipation', 
    description: 'Compute linear voltage drop thermal loss, PCB copper polygon heatsinking area boundaries, and junction-to-ambient thermal resistance design rule limits.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },
  { 
    id: 'power_device', 
    name: 'Power Semiconductor Loss & Thermal Sizing', 
    description: 'Evaluate MOSFET and IGBT conduction, switching (Eon/Eoff), and gate drive losses, assessing Miller plateau times and junction temperature derating.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },
  { 
    id: 'power_dpt', 
    name: 'Double Pulse Test (DPT) Calculator', 
    description: 'Calculate inductive switching circuit charging pulse width, freewheeling interval timing, and extract turn-on/turn-off cross-overlap energies.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },
  { 
    id: 'battery_pack', 
    name: 'Battery Pack & BMS Sizing Calculator', 
    description: 'Model lithium battery pack series/parallel cell topologies, internal resistance self-heating dissipation, and passive bleeding resistor balancing.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },
  { 
    id: 'power_budget', 
    name: 'Power Converter Loss & Efficiency Budget', 
    description: 'Aggregate converter semiconductor switches, magnetic inductors/transformers, snubbers, and auxiliary control power losses into a comprehensive efficiency budget.', 
    category: '🔥 Power & Thermal', 
    isImplemented: true 
  },

  // 4. Loop Control & Signals
  { 
    id: 'loop_compensation', 
    name: 'Analog Control Loop Compensation', 
    description: 'Synthesize Type II/III op-amp compensators and optocoupler-isolated TL431 networks, placing poles and zeroes to optimize crossover frequency and phase margin.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },
  { 
    id: 'digital_pid', 
    name: 'Digital PID & Discretization Calculator', 
    description: 'Transform continuous S-domain transfer functions into discrete Z-domain difference equations via Tustin/Bilinear methods, outputting ready-to-run C firmware code.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },
  { 
    id: 'filter_passive', 
    name: 'Passive & Active Filter Design', 
    description: 'Design low-pass/high-pass Butterworth, Chebyshev, and passive LC/pi filters, evaluating input decoupling impedance and Middlebrook stability criteria.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },
  { 
    id: 'emc_toolbox', 
    name: 'EMC Filter & Damping Toolbox', 
    description: 'Convert EMI unit domains (dBm, dBuV, V, W), model common-mode and differential-mode attenuation, enclosure aperture shielding, and RC damping networks.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },
  { 
    id: 'adc_conditioning', 
    name: 'ADC Signal Conditioning & Charge Bucket', 
    description: 'Size anti-aliasing RC filter bandwidth, input charge bucket settling times, op-amp gain scaling, full-scale dynamic range, and two-point calibration offsets.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },
  { 
    id: 'current_shunt', 
    name: 'Current Shunt & Current Transformer (CT)', 
    description: 'Size current sensing shunts and current transformer burden resistors, evaluating thermal dissipation, Kelvin sense routing trace error, and saturation flux.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },
  { 
    id: 'ntc', 
    name: 'NTC Temperature & Steinhart-Hart Fitting', 
    description: 'Extract Beta constants or perform 3-point polynomial curve fitting using the Steinhart-Hart equation, sizing linearization dividers and generating C lookup tables.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },
  { 
    id: 'pwm_mcu_ic', 
    name: 'PWM Timer & Controller IC Peripherals', 
    description: 'Size PWM DAC RC low-pass filter ripple; calculate digital micro-controller timer dead-time registers; and size analog controller oscillator RT/CT networks.', 
    category: '📈 Loop & Signals', 
    isImplemented: true 
  },

  // 5. Passives & Safety
  { 
    id: 'tvs_zener', 
    name: 'TVS & Zener Surge Protection Sizing', 
    description: 'Size Zener steady-state current-limiting resistors and evaluate TVS diode peak pulse power (Ppp), clamping voltage, and transient junction thermal rise.', 
    category: '🛡️ Passives & Safety', 
    isImplemented: true 
  },
  { 
    id: 'input_protection', 
    name: 'Input Protection & Safety Bleed Sizing', 
    description: 'Verify inrush fuse I^2t energy pulse withstand, size inrush power NTC thermistors, and design AC safety discharge bleeding resistor time constants.', 
    category: '🛡️ Passives & Safety', 
    isImplemented: true 
  },
  { 
    id: 'pcb_toolbox', 
    name: 'PCB Trace & Via Current Thermal Sizing', 
    description: 'Compute internal/external trace ampacity and thermal temperature rise based on IPC-2152, via parasitic inductance, and microstrip RF impedance.', 
    category: '🛡️ Passives & Safety', 
    isImplemented: true 
  },
  { 
    id: 'wire_copper_bar', 
    name: 'Winding Wire & High-Current Copper Busbar', 
    description: 'Analyze high-frequency Litz wire skin and proximity effect AC resistance, evaluate solid copper wire ampacity, and size high-current busbar steady-state heating.', 
    category: '🛡️ Passives & Safety', 
    isImplemented: true 
  },
  { 
    id: 'capacitor_toolbox', 
    name: 'Capacitor Life & Voltage Derating', 
    description: 'Model Arrhenius thermal lifespan acceleration for electrolytic capacitors, multi-frequency RMS ripple aggregation, and MLCC DC-bias capacitance derating.', 
    category: '🛡️ Passives & Safety', 
    isImplemented: true 
  },
  { 
    id: 'db_manager', 
    name: 'Component & Magnetic Material Database', 
    description: 'Manage and query local SQLite records of power MOSFETs, IGBTs, Schottky diodes, core material Steinmetz coefficients, and geometric bobbins.', 
    category: '🛡️ Passives & Safety', 
    isImplemented: true 
  }
];

const CATEGORIES = [
  'All',
  '⚡ Power Co-Design',
  '🧲 Magnetics & Basics',
  '🔥 Power & Thermal',
  '📈 Loop & Signals',
  '🛡️ Passives & Safety'
];

const gridColsClassMap: Record<number, string> = {
  5: 'grid-cols-5',
  6: 'grid-cols-6',
  7: 'grid-cols-7',
  8: 'grid-cols-8',
  9: 'grid-cols-9',
  10: 'grid-cols-10'
};

interface CustomGroup {
  id: string;
  name: string;
  moduleIds: string[];
}

interface StateTransition {
  stateKey: string;
  from: any;
  to: any;
  restore: (val: any) => void;
}

export default function App() {
  const { lang, setLang, t, getModuleInfo, getCategoryName } = useTranslation();

  const [navigation, setNavigation] = useState<{
    activeModule: string | null;
    historyStack: (string | null)[];
  }>({
    activeModule: null,
    historyStack: [null]
  });

  const activeModule = navigation.activeModule;

  const setActiveModule = (target: string | null | ((prev: string | null) => string | null)) => {
    setNavigation((prevNav) => {
      let resolvedTarget: string | null;
      if (typeof target === 'function') {
        resolvedTarget = target(prevNav.activeModule);
      } else {
        resolvedTarget = target;
      }

      if (resolvedTarget === prevNav.activeModule) {
        return prevNav;
      }

      if (resolvedTarget === null) {
        if (prevNav.historyStack.length > 1) {
          const nextStack = [...prevNav.historyStack];
          nextStack.pop(); // pop current page
          const prevPage = nextStack[nextStack.length - 1];
          return {
            activeModule: prevPage,
            historyStack: nextStack
          };
        } else {
          return {
            activeModule: null,
            historyStack: [null]
          };
        }
      } else {
        // Avoid duplicate consecutive entries in history
        const lastIdx = prevNav.historyStack.length - 1;
        if (prevNav.historyStack[lastIdx] === resolvedTarget) {
          return prevNav;
        }
        const nextStack = [...prevNav.historyStack, resolvedTarget];
        return {
          activeModule: resolvedTarget,
          historyStack: nextStack
        };
      }
    });
  };

  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [innerHistory, setInnerHistory] = useState<StateTransition[]>([]);

  // Clear inner history when activeModule changes
  useEffect(() => {
    setInnerHistory([]);
  }, [activeModule]);

  // Listen to state changes from child components
  useEffect(() => {
    const handlePush = (e: Event) => {
      const { stateKey, value, prevValue, restore } = (e as CustomEvent).detail;
      setInnerHistory((prev) => {
        // Prevent pushing duplicate transitions
        if (prev.length > 0) {
          const last = prev[prev.length - 1];
          if (last.stateKey === stateKey && last.to === value) {
            return prev;
          }
        }
        return [
          ...prev,
          { stateKey, from: prevValue, to: value, restore }
        ];
      });
    };

    window.addEventListener('app-state-push', handlePush);
    return () => window.removeEventListener('app-state-push', handlePush);
  }, []);

  const [gridRows, setGridRows] = useState<number>(() => {
    return Number(localStorage.getItem('toolbox_category_grid_rows')) || 2;
  });
  const [gridCols, setGridCols] = useState<number>(() => {
    return Number(localStorage.getItem('toolbox_category_grid_cols')) || 6;
  });

  const padOrTrimGroups = (groups: CustomGroup[], rows: number, cols: number): CustomGroup[] => {
    const targetLength = rows * cols;
    let result = [...groups];
    
    const seenIds = new Set<string>();
    result = result.filter(g => {
      if (!g || !g.id || seenIds.has(g.id)) return false;
      seenIds.add(g.id);
      return true;
    });

    const getIsPlaceholder = (g: CustomGroup) => {
      return g.name === '[spacer]' || g.name === '[placeholder]' || g.name === '[Spacer]' || g.name.trim() === '';
    };

    if (result.length > targetLength) {
      const normalCategories = result.filter(g => !getIsPlaceholder(g));
      
      if (normalCategories.length <= targetLength) {
        const placeholdersNeeded = targetLength - normalCategories.length;
        const newPlaceholders: CustomGroup[] = [];
        for (let i = 0; i < placeholdersNeeded; i++) {
          newPlaceholders.push({
            id: `group_placeholder_${Date.now()}_${i}`,
            name: '[spacer]',
            moduleIds: []
          });
        }
        result = [...normalCategories, ...newPlaceholders];
      } else {
        const newRows = Math.ceil(normalCategories.length / cols);
        const newTargetLength = newRows * cols;
        const placeholdersNeeded = newTargetLength - normalCategories.length;
        const newPlaceholders: CustomGroup[] = [];
        for (let i = 0; i < placeholdersNeeded; i++) {
          newPlaceholders.push({
            id: `group_placeholder_${Date.now()}_${i}`,
            name: '[spacer]',
            moduleIds: []
          });
        }
        result = [...normalCategories, ...newPlaceholders];
      }
    } else if (result.length < targetLength) {
      const placeholdersNeeded = targetLength - result.length;
      const newPlaceholders: CustomGroup[] = [];
      for (let i = 0; i < placeholdersNeeded; i++) {
        newPlaceholders.push({
          id: `group_placeholder_${Date.now()}_${i}`,
          name: '[spacer]',
          moduleIds: []
        });
      }
      result = [...result, ...newPlaceholders];
    }
    return result;
  };

  const handleGridDimensionsChange = (newRows: number, newCols: number) => {
    setGridRows(newRows);
    setGridCols(newCols);
    localStorage.setItem('toolbox_category_grid_rows', String(newRows));
    localStorage.setItem('toolbox_category_grid_cols', String(newCols));
    
    setCustomGroups(prev => {
      const updated = padOrTrimGroups(prev, newRows, newCols);
      localStorage.setItem('toolbox_custom_groups', JSON.stringify(updated));
      return updated;
    });
  };

  const [customGroups, setCustomGroups] = useState<CustomGroup[]>(() => {
    const saved = localStorage.getItem('toolbox_custom_groups');
    let loadedGroups: CustomGroup[] = [];
    if (saved) {
      try {
        loadedGroups = JSON.parse(saved);
      } catch (e) {
        console.error("Error parsing custom groups:", e);
      }
    }
    
    const allModuleIds = TOOL_MODULES.map(m => m.id);
    const validCategories = new Set(CATEGORIES.filter(cat => cat !== 'All'));

    const hasStaleCategories = loadedGroups && loadedGroups.some(g => 
      !validCategories.has(g.name) && g.name !== 'Uncategorized' && !g.name.startsWith('[')
    );

    if (!loadedGroups || loadedGroups.length === 0 || hasStaleCategories) {
      loadedGroups = CATEGORIES.filter(cat => cat !== 'All').map((cat, idx) => {
        const mods = TOOL_MODULES.filter(mod => mod.category === cat).map(mod => mod.id);
        return {
          id: `group_${idx}_${Date.now()}`,
          name: cat,
          moduleIds: mods
        };
      });
      localStorage.setItem('toolbox_custom_groups', JSON.stringify(loadedGroups));
    }

    // Filter out obsolete module IDs that no longer exist in TOOL_MODULES
    const allModuleIdSet = new Set(allModuleIds);
    loadedGroups = loadedGroups.map(g => ({
      ...g,
      moduleIds: (g.moduleIds || []).filter(id => allModuleIdSet.has(id))
    }));
    const groupedModuleIds = new Set<string>();
    loadedGroups.forEach(g => {
      if (g && g.moduleIds) {
        g.moduleIds.forEach(id => groupedModuleIds.add(id));
      }
    });

    const missingModuleIds = allModuleIds.filter(id => !groupedModuleIds.has(id));
    if (missingModuleIds.length > 0) {
      loadedGroups = loadedGroups.map(g => ({ ...g, moduleIds: [...g.moduleIds] }));
      
      missingModuleIds.forEach(id => {
        const mod = TOOL_MODULES.find(m => m.id === id);
        if (mod) {
          let targetGroup = loadedGroups.find(g => g.name === mod.category);
          if (targetGroup) {
            targetGroup.moduleIds.push(id);
          } else {
            let uncategorizedGroup = loadedGroups.find(g => g.name === 'Uncategorized');
            if (!uncategorizedGroup) {
              uncategorizedGroup = {
                id: `group_uncategorized_${Date.now()}`,
                name: 'Uncategorized',
                moduleIds: []
              };
              loadedGroups.push(uncategorizedGroup);
            }
            uncategorizedGroup.moduleIds.push(id);
          }
        }
      });
      localStorage.setItem('toolbox_custom_groups', JSON.stringify(loadedGroups));
    }

    const initialRows = Number(localStorage.getItem('toolbox_category_grid_rows')) || 2;
    const initialCols = Number(localStorage.getItem('toolbox_category_grid_cols')) || 6;
    
    // Format helper function must be inline or defined before initialization
    // Since we defined padOrTrimGroups above customGroups, it is safe to invoke here
    const targetLength = initialRows * initialCols;
    let result = [...loadedGroups];
    const seenIds = new Set<string>();
    result = result.filter(g => {
      if (!g || !g.id || seenIds.has(g.id)) return false;
      seenIds.add(g.id);
      return true;
    });

    const getIsPlaceholder = (g: CustomGroup) => {
      return g.name === '[spacer]' || g.name === '[placeholder]' || g.name === '[Spacer]' || g.name.trim() === '';
    };

    if (result.length > targetLength) {
      const normalCategories = result.filter(g => !getIsPlaceholder(g));
      if (normalCategories.length <= targetLength) {
        const placeholdersNeeded = targetLength - normalCategories.length;
        const newPlaceholders: CustomGroup[] = [];
        for (let i = 0; i < placeholdersNeeded; i++) {
          newPlaceholders.push({
            id: `group_placeholder_${Date.now()}_${i}`,
            name: '[spacer]',
            moduleIds: []
          });
        }
        result = [...normalCategories, ...newPlaceholders];
      } else {
        const newRows = Math.ceil(normalCategories.length / initialCols);
        const newTargetLength = newRows * initialCols;
        const placeholdersNeeded = newTargetLength - normalCategories.length;
        const newPlaceholders: CustomGroup[] = [];
        for (let i = 0; i < placeholdersNeeded; i++) {
          newPlaceholders.push({
            id: `group_placeholder_${Date.now()}_${i}`,
            name: '[spacer]',
            moduleIds: []
          });
        }
        result = [...normalCategories, ...newPlaceholders];
      }
    } else if (result.length < targetLength) {
      const placeholdersNeeded = targetLength - result.length;
      const newPlaceholders: CustomGroup[] = [];
      for (let i = 0; i < placeholdersNeeded; i++) {
        newPlaceholders.push({
          id: `group_placeholder_${Date.now()}_${i}`,
          name: '[spacer]',
          moduleIds: []
        });
      }
      result = [...result, ...newPlaceholders];
    }
    return result;
  });

  const [draggedCategoryId, setDraggedCategoryId] = useState<string | null>(null);
  const [draggedOverCategoryId, setDraggedOverCategoryId] = useState<string | null>(null);
  const [editingGroupId, setEditingGroupId] = useState<string | null>(null);
  const [editingGroupName, setEditingGroupName] = useState<string>('');
  const [deletingGroupId, setDeletingGroupId] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<{ passed: boolean; unassigned: string[] } | null>(null);

  const [moduleOrder, setModuleOrder] = useState<string[]>(() => {
    const saved = localStorage.getItem('dashboard_module_order');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error(e);
      }
    }
    return TOOL_MODULES.map(mod => mod.id);
  });

  const [draggedModuleId, setDraggedModuleId] = useState<string | null>(null);

  const handleModuleDragStart = (e: React.DragEvent, id: string) => {
    setDraggedModuleId(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleModuleDragEnter = (e: React.DragEvent, targetId: string) => {
    if (draggedModuleId === null || draggedModuleId === targetId) return;
    
    if (selectedCategory === 'All') {
      setModuleOrder((prev) => {
        const copy = [...prev];
        const dragIdx = copy.indexOf(draggedModuleId);
        const targetIdx = copy.indexOf(targetId);
        if (dragIdx !== -1 && targetIdx !== -1) {
          copy.splice(dragIdx, 1);
          copy.splice(targetIdx, 0, draggedModuleId);
          localStorage.setItem('dashboard_module_order', JSON.stringify(copy));
        }
        return copy;
      });
    } else {
      setCustomGroups((prevGroups) => {
        const nextGroups = prevGroups.map(group => {
          if (group.id === selectedCategory) {
            const copy = [...group.moduleIds];
            const dragIdx = copy.indexOf(draggedModuleId);
            const targetIdx = copy.indexOf(targetId);
            if (dragIdx !== -1 && targetIdx !== -1) {
              copy.splice(dragIdx, 1);
              copy.splice(targetIdx, 0, draggedModuleId);
            }
            return { ...group, moduleIds: copy };
          }
          return group;
        });
        localStorage.setItem('toolbox_custom_groups', JSON.stringify(nextGroups));
        return nextGroups;
      });
    }
  };

  const handleModuleDragEnd = () => {
    setDraggedModuleId(null);
    setDraggedOverCategoryId(null);
  };

  const handleCategoryDragStart = (e: React.DragEvent, id: string) => {
    setDraggedCategoryId(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleCategoryDragEnter = (e: React.DragEvent, targetId: string) => {
    if (draggedCategoryId === null || draggedCategoryId === targetId) return;

    setCustomGroups((prev) => {
      const copy = [...prev];
      const dragIdx = copy.findIndex(g => g.id === draggedCategoryId);
      const targetIdx = copy.findIndex(g => g.id === targetId);
      if (dragIdx !== -1 && targetIdx !== -1) {
        const [removed] = copy.splice(dragIdx, 1);
        copy.splice(targetIdx, 0, removed);
        localStorage.setItem('toolbox_custom_groups', JSON.stringify(copy));
      }
      return copy;
    });
  };

  const handleCategoryDragEnd = () => {
    setDraggedCategoryId(null);
  };

  const handleDropModuleOnCategory = (e: React.DragEvent, targetGroupId: string) => {
    e.preventDefault();
    setDraggedOverCategoryId(null);
    if (draggedModuleId === null) return;

    setCustomGroups((prevGroups) => {
      const nextGroups = prevGroups.map(group => {
        // Remove from current group if present
        let nextModuleIds = group.moduleIds.filter(id => id !== draggedModuleId);
        
        // Add to target group
        if (group.id === targetGroupId) {
          if (!nextModuleIds.includes(draggedModuleId)) {
            nextModuleIds = [...nextModuleIds, draggedModuleId];
          }
        }
        return { ...group, moduleIds: nextModuleIds };
      });
      localStorage.setItem('toolbox_custom_groups', JSON.stringify(nextGroups));
      return nextGroups;
    });
    setDraggedModuleId(null);
  };

  const handleCreateCategory = () => {
    const newId = `group_${Date.now()}`;
    const newGroup: CustomGroup = {
      id: newId,
      name: 'New Group',
      moduleIds: []
    };
    
    const idx = customGroups.findIndex(g => g.name === '[spacer]' || g.name === '[placeholder]' || g.name === '[Spacer]' || g.name.trim() === '');
    let nextGroups = [...customGroups];
    if (idx !== -1) {
      nextGroups[idx] = newGroup;
    } else {
      const newRows = gridRows + 1;
      setGridRows(newRows);
      localStorage.setItem('toolbox_category_grid_rows', String(newRows));
      
      const newRowPlaceholders: CustomGroup[] = [];
      for (let i = 1; i < gridCols; i++) {
        newRowPlaceholders.push({
          id: `group_placeholder_${Date.now()}_${i}`,
          name: '[spacer]',
          moduleIds: []
        });
      }
      nextGroups = [...customGroups, newGroup, ...newRowPlaceholders];
    }
    
    setCustomGroups(nextGroups);
    localStorage.setItem('toolbox_custom_groups', JSON.stringify(nextGroups));
    setSelectedCategory(newId);
    setEditingGroupId(newId);
    setEditingGroupName('New Group');
  };

  const handleDeleteCategory = (id: string) => {
    const targetGroup = customGroups.find(g => g.id === id);
    if (!targetGroup) return;

    let updatedGroups = customGroups.map(g => {
      if (g.id === id) {
        return {
          id: `group_placeholder_${Date.now()}`,
          name: '[spacer]',
          moduleIds: []
        };
      }
      return g;
    });

    if (targetGroup.moduleIds.length > 0) {
      let uncategorizedGroup = updatedGroups.find(g => g.name === 'Uncategorized');
      if (!uncategorizedGroup) {
        const placeholderIdx = updatedGroups.findIndex(g => g.name === '[spacer]' || g.name === '[placeholder]' || g.name === '[Spacer]');
        const uncategorizedId = `group_uncategorized_${Date.now()}`;
        const newUncategorized = {
          id: uncategorizedId,
          name: 'Uncategorized',
          moduleIds: targetGroup.moduleIds
        };
        if (placeholderIdx !== -1) {
          updatedGroups[placeholderIdx] = newUncategorized;
        } else {
          updatedGroups.push(newUncategorized);
        }
      } else {
        const mergedIds = Array.from(new Set([...uncategorizedGroup.moduleIds, ...targetGroup.moduleIds]));
        uncategorizedGroup.moduleIds = mergedIds;
      }
    }

    const finalGroups = padOrTrimGroups(updatedGroups, gridRows, gridCols);
    setCustomGroups(finalGroups);
    localStorage.setItem('toolbox_custom_groups', JSON.stringify(finalGroups));
    
    if (selectedCategory === id) {
      setSelectedCategory('All');
    }
  };

  const handleCheckCategorization = () => {
    const categorizedIds = new Set<string>();
    customGroups.forEach(g => {
      const isPlaceholder = g.name === '[spacer]' || g.name === '[placeholder]' || g.name === '[Spacer]' || g.name.trim() === '';
      if (!isPlaceholder && g.moduleIds) {
        g.moduleIds.forEach(id => categorizedIds.add(id));
      }
    });

    const unassigned = TOOL_MODULES.filter(mod => mod.isImplemented && !categorizedIds.has(mod.id))
                                   .map(mod => mod.name);

    setAuditResult({
      passed: unassigned.length === 0,
      unassigned: unassigned
    });
  };

  const startCategoryRename = (id: string, name: string) => {
    setEditingGroupId(id);
    setEditingGroupName(name);
  };

  const commitCategoryRename = (id: string) => {
    if (!editingGroupName.trim()) {
      setEditingGroupId(null);
      return;
    }
    const updated = customGroups.map(g => {
      if (g.id === id) {
        return { ...g, name: editingGroupName.trim() };
      }
      return g;
    });
    setCustomGroups(updated);
    localStorage.setItem('toolbox_custom_groups', JSON.stringify(updated));
    setEditingGroupId(null);
  };

  const handleCategoryRenameKeyDown = (e: React.KeyboardEvent, id: string) => {
    if (e.key === 'Enter') {
      commitCategoryRename(id);
    } else if (e.key === 'Escape') {
      setEditingGroupId(null);
    }
  };

  // Keep-alive heartbeat: send ping to backend every 2s.
  // If browser is closed, backend will auto-terminate after 8s of silence.
  useEffect(() => {
    const sendHeartbeat = () => {
      apiFetch('/api/heartbeat', { method: 'POST' }).catch(() => {});
    };
    sendHeartbeat();
    const interval = setInterval(sendHeartbeat, 2000);
    return () => clearInterval(interval);
  }, []);

  // Listen for global Backspace and Escape key press to navigate back or close modals
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeEl = document.activeElement;
      const isInputActive = activeEl && (
        activeEl.tagName === 'INPUT' || 
        activeEl.tagName === 'TEXTAREA' || 
        activeEl.tagName === 'SELECT' || 
        activeEl.getAttribute('contenteditable') === 'true'
      );

      if (e.key === 'Backspace') {
        if (isInputActive) return;
        
        // If there are state transitions within the current module, revert the last one
        if (innerHistory.length > 0) {
          setInnerHistory((prev) => {
            const nextHistory = [...prev];
            const lastTransition = nextHistory.pop();
            if (lastTransition) {
              lastTransition.restore(lastTransition.from);
            }
            return nextHistory;
          });
        } else {
          setActiveModule(null);
        }
      } else if (e.key === 'Escape') {
        // 1. Audit Result Modal
        if (auditResult !== null) {
          setAuditResult(null);
          return;
        }

        // 2. Category Delete Warning
        if (deletingGroupId !== null) {
          setDeletingGroupId(null);
          return;
        }

        // 3. Category Edit Mode
        if (editingGroupId !== null) {
          setEditingGroupId(null);
          return;
        }

        // 4. Input Focus Blur
        if (isInputActive) {
          (activeEl as HTMLElement).blur();
          return;
        }

        // 5. Navigate Back
        if (activeModule !== null) {
          setActiveModule(null);
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigation, auditResult, deletingGroupId, editingGroupId, activeModule, innerHistory]);

  // Filter and sort module list
  const filteredModules = TOOL_MODULES.filter(mod => {
    const q = searchQuery.toLowerCase().trim();
    const zh = zhModules[mod.id];
    const en = enModules[mod.id];
    const matchSearch = !q || 
                        mod.name.toLowerCase().includes(q) || 
                        mod.description.toLowerCase().includes(q) ||
                        (zh && (zh.name.toLowerCase().includes(q) || zh.description.toLowerCase().includes(q))) ||
                        (en && (en.name.toLowerCase().includes(q) || en.description.toLowerCase().includes(q)));
    if (!matchSearch) return false;

    if (selectedCategory === 'All') {
      return true;
    } else {
      const activeGroup = customGroups.find(g => g.id === selectedCategory);
      return activeGroup ? activeGroup.moduleIds.includes(mod.id) : false;
    }
  });

  const sortedFilteredModules = [...filteredModules].sort((a, b) => {
    if (selectedCategory === 'All') {
      const idxA = moduleOrder.indexOf(a.id);
      const idxB = moduleOrder.indexOf(b.id);
      return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
    } else {
      const activeGroup = customGroups.find(g => g.id === selectedCategory);
      if (activeGroup) {
        const idxA = activeGroup.moduleIds.indexOf(a.id);
        const idxB = activeGroup.moduleIds.indexOf(b.id);
        return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
      }
      return 0;
    }
  });


  const activeModInfo = TOOL_MODULES.find(m => m.id === activeModule);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#020617] text-slate-100 font-sans">
      
      {/* 1. Left Sidebar Navigation */}
      <div className="w-64 border-r border-slate-800 bg-[#090d16] flex flex-col shrink-0 h-full">
        
        {/* Logo Section & Language Switcher */}
        <div className="p-3 border-b border-slate-800 flex items-center justify-between gap-2 bg-[#090d16]">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-md bg-gradient-to-r from-cyan-500 to-cyan-600 shadow-md">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xs font-bold text-white tracking-tight">HW ToolBox</h1>
              <p className="text-[9px] text-slate-400">Desktop v1.0</p>
            </div>
          </div>
          <div className="flex items-center gap-1 px-2.5 py-1 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[11px] font-bold font-mono shrink-0">
            <Globe className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[10px] font-mono font-bold">EN</span>
          </div>
        </div>

        {/* Navigation list */}
        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-1 scrollbar-thin scrollbar-thumb-slate-800">
          <span className="text-[9px] font-semibold text-slate-400 px-2 mb-1 uppercase tracking-wider">{t('app.navTitle')}</span>
          
          <button 
            onClick={() => setActiveModule(null)}
            className={`w-full text-left px-3 py-2 rounded-md text-xs font-semibold flex items-center gap-2 border-0 cursor-pointer transition-all ${activeModule === null ? 'bg-cyan-500/10 text-cyan-400 border-l-2 border-cyan-500' : 'bg-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-850/20'}`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>{t('app.dashboard')}</span>
          </button>

          {customGroups.map(group => {
            const groupModules = group.moduleIds
              .map(id => TOOL_MODULES.find(m => m.id === id))
              .filter((mod): mod is ToolModule => !!mod && mod.isImplemented);

            const isPlaceholder = group.name === '[spacer]' || group.name === '[placeholder]' || group.name === '[Spacer]' || group.name.trim() === '';
            if (isPlaceholder || groupModules.length === 0) {
              return null;
            }

            return (
              <div 
                key={group.id} 
                className="flex flex-col gap-0.5 mt-2.5"
                onDragOver={(e) => {
                  e.preventDefault();
                  if (draggedModuleId !== null) {
                    e.dataTransfer.dropEffect = 'move';
                  }
                }}
                onDrop={(e) => handleDropModuleOnCategory(e, group.id)}
              >
                <span className="text-[9px] font-bold text-slate-400 px-2 py-1 uppercase tracking-wide flex items-center justify-between">
                  <span>{getCategoryName(group.name)}</span>
                  <span className="text-[8px] bg-slate-800 text-slate-450 px-1.5 py-0.5 rounded-full font-mono">
                    {group.moduleIds.filter(id => TOOL_MODULES.some(m => m.id === id)).length}
                  </span>
                </span>
                {groupModules.map(mod => (
                  <button
                    key={mod.id}
                    onClick={() => setActiveModule(mod.id)}
                    className={`w-full text-left pl-5 pr-2 py-1.5 rounded-md text-[11px] font-medium flex items-center justify-between border-0 cursor-pointer transition-all ${activeModule === mod.id ? 'bg-cyan-500/10 text-cyan-400 border-l-2 border-cyan-500' : 'bg-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'}`}
                  >
                    <span className="truncate text-left">{getModuleInfo(mod.id, mod.name).name}</span>
                    <ChevronRight className="w-2.5 h-2.5 opacity-40 shrink-0" />
                  </button>
                ))}
              </div>
            );
          })}
        </div>

        {/* Footer profile info */}
        <div className="p-3 border-t border-slate-800 text-[10px] text-slate-400 flex flex-col gap-1 shrink-0">
          <div className="flex justify-between items-center">
            <span>{t('app.author')}</span>
          </div>
          <a 
            href="https://github.com/WenZhenJian-EE/Hardware-Engineering-Toolbox-Desktop" 
            target="_blank" 
            rel="noreferrer"
            className="text-[10px] text-slate-400 hover:text-cyan-400 flex items-center gap-1.5 mt-1 border-0"
          >
            <BookOpen className="w-3 h-3" />
            <span>{t('app.github')}</span>
          </a>
        </div>

      </div>

      {/* 2. Right Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#070a13]">
        
        {/* Top bar header */}
        <header className="h-12 border-b border-slate-800/80 bg-[#0b0f19]/60 backdrop-blur shrink-0 px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-400">{t('app.arch')}</span>
            <span className="text-[9px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-1.5 py-0.5 rounded font-mono font-bold">{t('app.archValue')}</span>
          </div>
          <div className="flex items-center gap-3 text-[11px]">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-bold font-mono shrink-0">
              <Globe className="w-4 h-4 text-cyan-400" />
              <span>English (US)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-slate-400">{t('app.backendConnected')}</span>
            </div>
          </div>
        </header>

        {/* Panel Content container */}
        <div className={`flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800 ${activeModule === null ? 'p-6' : 'p-0 flex flex-col'}`}>
          {activeModule === null ? (
            // Dashboard page
            <div className="flex flex-col gap-6 max-w-[1440px] mx-auto w-full">
              
              {/* Welcome card */}
              <div className="p-6 rounded-xl border border-slate-800/60 bg-gradient-to-r from-[#0b1528] to-[#070b13] flex justify-between items-center shadow-lg relative overflow-hidden">
                <div className="flex flex-col gap-1.5 z-10">
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-cyan-400 animate-pulse" />
                    {t('app.welcomeTitle')}
                  </h2>
                  <p className="text-xs text-slate-400 max-w-xl leading-relaxed">
                    {t('app.welcomeDesc')}
                  </p>
                </div>
                <div className="hidden md:block absolute right-0 top-0 bottom-0 opacity-15 translate-x-10 pointer-events-none scale-150">
                  <Zap className="w-64 h-64 text-cyan-500" />
                </div>
              </div>

              {/* Categorization controls & Search Row */}
              <div className="flex flex-col gap-4 bg-[#0b0f19]/40 p-4 rounded-xl border border-slate-800/50">
                {/* 1. Grid of Category Tabs */}
                <div className={`grid ${gridColsClassMap[gridCols] || 'grid-cols-6'} gap-2.5 w-full`}>
                  <button
                    onClick={() => setSelectedCategory('All')}
                    className={`col-span-full py-2 px-3 rounded-md text-[11px] font-bold border border-slate-800/40 cursor-pointer transition-all text-center flex items-center justify-center ${
                      selectedCategory === 'All'
                        ? 'bg-cyan-500/20 text-cyan-300 font-bold border-cyan-500/30' 
                        : 'bg-slate-950/20 text-slate-400 hover:text-slate-200 hover:bg-slate-850/20'
                    }`}
                  >
                    {t('app.all')} ({TOOL_MODULES.length})
                  </button>

                  {customGroups.map(group => {
                    const isSelected = selectedCategory === group.id;
                    const isEditing = editingGroupId === group.id;
                    const isPlaceholder = group.name === '[spacer]' || group.name === '[placeholder]' || group.name === '[Spacer]' || group.name.trim() === '';

                    return (
                      <div
                        key={group.id}
                        draggable={!isEditing}
                        onDragStart={(e) => handleCategoryDragStart(e, group.id)}
                        onDragEnter={(e) => {
                          handleCategoryDragEnter(e, group.id);
                          if (draggedModuleId !== null) {
                            setDraggedOverCategoryId(group.id);
                          }
                        }}
                        onDragLeave={() => {
                          if (draggedModuleId !== null) {
                            setDraggedOverCategoryId(null);
                          }
                        }}
                        onDragEnd={handleCategoryDragEnd}
                        onDragOver={(e) => {
                          e.preventDefault();
                          if (draggedModuleId !== null) {
                            e.dataTransfer.dropEffect = 'move';
                          }
                        }}
                        onDrop={(e) => handleDropModuleOnCategory(e, group.id)}
                        className={`relative flex items-center justify-center gap-1 py-2 px-1 rounded-md text-[11px] font-bold transition-all group/tab select-none w-full ${
                          draggedOverCategoryId === group.id
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400 scale-[1.04] shadow-lg shadow-cyan-500/20 ring-2 ring-cyan-500/30'
                            : isPlaceholder
                              ? 'border border-transparent bg-transparent text-transparent hover:border-dashed hover:border-slate-850 hover:bg-slate-900/10 hover:text-slate-400/80'
                              : isSelected 
                                ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 cursor-pointer' 
                                : 'bg-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/20 cursor-pointer'
                        } ${draggedCategoryId === group.id ? 'opacity-30 border-dashed border-cyan-500/50' : ''} ${
                          draggedModuleId !== null ? '[&>*]:pointer-events-none' : ''
                        }`}
                      >
                        {deletingGroupId === group.id ? (
                          <div className={`flex items-center justify-center gap-1 animate-fade-in w-full ${draggedModuleId !== null ? 'pointer-events-none' : ''}`}>
                            <span className="text-rose-400 text-[9px] font-bold mr-0.5 shrink-0">Confirm delete?</span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteCategory(group.id);
                                setDeletingGroupId(null);
                              }}
                              className="p-0.5 text-emerald-400 hover:text-emerald-400 hover:bg-slate-800/40 rounded transition-colors bg-transparent border-0 cursor-pointer"
                              title="Confirm"
                            >
                              <Check className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeletingGroupId(null);
                              }}
                              className="p-0.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 rounded transition-colors bg-slate-900 border-0 cursor-pointer"
                              title="Cancel"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ) : isEditing ? (
                          <input className="font-mono bg-slate-900 border border-cyan-500/40 rounded px-1 py-0.5 outline-none text-[10px] w-full font-bold text-center text-cyan-400" style={{ pointerEvents: draggedModuleId !== null ? "none" : "auto" }} type="text" value={editingGroupName} onChange={(e) => setEditingGroupName(e.target.value)} onKeyDown={(e) => handleCategoryRenameKeyDown(e, group.id)} onBlur={() => commitCategoryRename(group.id)} autoFocus />
                        ) : (
                          <span 
                            onClick={() => {
                              if (!isPlaceholder) {
                                setSelectedCategory(group.id);
                              }
                            }} 
                            onDoubleClick={() => startCategoryRename(group.id, group.name)}
                            className={`${isPlaceholder ? "cursor-default select-none w-full text-center truncate" : "cursor-pointer w-full text-center truncate"} ${draggedModuleId !== null ? 'pointer-events-none' : ''}`}
                          >
                            {isPlaceholder 
                              ? '[Spacer]' 
                              : `${getCategoryName(group.name)} (${group.moduleIds.filter(id => TOOL_MODULES.some(m => m.id === id)).length})`
                            }
                          </span>
                        )}

                        {!isEditing && deletingGroupId !== group.id && (
                          <div className={`absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-0.5 opacity-0 group-hover/tab:opacity-100 transition-opacity duration-150 shrink-0 bg-slate-900/90 rounded px-0.5 shadow-md ${draggedModuleId !== null ? 'pointer-events-none' : ''}`}>
                            {!isPlaceholder && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  startCategoryRename(group.id, group.name);
                                }}
                                className="p-0.5 text-slate-400 hover:text-cyan-400 bg-transparent border-0 cursor-pointer transition-colors"
                                title="Double click or click to rename"
                              >
                                <Edit2 className="w-2.5 h-2.5" />
                              </button>
                            )}
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeletingGroupId(group.id);
                              }}
                              className="p-0.5 text-slate-400 hover:text-rose-400 bg-transparent border-0 cursor-pointer transition-colors"
                              title="Delete this category or spacer"
                            >
                              <Trash2 className="w-2.5 h-2.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* 2. Toolbar below grid */}
                <div className="flex flex-col sm:flex-row gap-4 items-center justify-between border-t border-slate-800/40 pt-3">
                  <div className="flex items-center gap-3 w-full sm:w-auto">
                    <button
                      onClick={handleCreateCategory}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-md text-[11px] font-bold border border-dashed border-slate-700 bg-transparent text-slate-400 hover:text-cyan-400 hover:border-cyan-500/40 cursor-pointer transition-all"
                    >
                      <Plus className="w-3 h-3" />
                      <span>{t('app.addGroup')}</span>
                    </button>

                    <div className="flex items-center gap-1.5 ml-2">
                      <span className="text-[10px] text-slate-400 font-bold shrink-0">Rows:</span>
                      <select className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[10px] outline-none cursor-pointer hover:border-slate-700 transition-colors font-mono text-cyan-400" value={gridRows} onChange={e => { const val = Number(e.target.value); handleGridDimensionsChange(val, gridCols); }}>
                        <option value={1}>1 Row</option>
                        <option value={2}>2 Rows</option>
                        <option value={3}>3 Rows</option>
                        <option value={4}>4 Rows</option>
                        <option value={5}>5 Rows</option>
                      </select>
                    </div>

                    <div className="flex items-center gap-1.5 ml-2">
                      <span className="text-[10px] text-slate-400 font-bold shrink-0">Cols:</span>
                      <select className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[10px] outline-none cursor-pointer hover:border-slate-700 transition-colors font-mono text-cyan-400" value={gridCols} onChange={e => { const val = Number(e.target.value); handleGridDimensionsChange(gridRows, val); }}>
                        <option value={5}>5 Cols</option>
                        <option value={6}>6 Cols</option>
                        <option value={7}>7 Cols</option>
                        <option value={8}>8 Cols</option>
                        <option value={9}>9 Cols</option>
                        <option value={10}>10 Cols</option>
                      </select>
                    </div>

                    <button
                      onClick={handleCheckCategorization}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-bold border border-slate-800 bg-transparent text-slate-400 hover:text-cyan-400 hover:border-cyan-500/30 cursor-pointer transition-all ml-2"
                      title="Audit uncategorized modules"
                    >
                      <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Audit Categories</span>
                    </button>
                  </div>

                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950/60 border border-slate-800/80 w-full sm:w-72">
                      <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <input className="bg-transparent border-0 outline-none text-xs w-full font-mono text-cyan-400" type="text" placeholder={t('app.searchPlaceholder')} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Categorization Audit Modal Overlay */}
              {auditResult && (
                <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
                  <div className="bg-[#0b101d] border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl relative">
                    <button 
                      onClick={() => setAuditResult(null)}
                      className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 bg-transparent border-0 cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </button>

                    <div className="flex items-center gap-3 mb-4">
                      {auditResult.passed ? (
                        <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                      ) : (
                        <ShieldAlert className="w-6 h-6 text-amber-500 shrink-0" />
                      )}
                      <h3 className="text-sm font-bold text-slate-200">
                        {auditResult.passed ? 'Categorization Audit Passed' : 'Uncategorized Modules Detected'}
                      </h3>
                    </div>

                    <div className="text-xs text-slate-400 mb-5 leading-relaxed">
                      {auditResult.passed ? (
                        <p>All active engineering modules are successfully organized into categories with zero omissions.</p>
                      ) : (
                        <div>
                          <p className="mb-2">{`Detected ${auditResult.unassigned.length} active module(s) not assigned to any category:`}</p>
                          <div className="max-h-48 overflow-y-auto bg-slate-950/50 p-2.5 rounded-lg border border-slate-900 gap-1.5 flex flex-col scrollbar-thin scrollbar-thumb-slate-800">
                            {auditResult.unassigned.map(name => (
                              <div key={name} className="flex items-center gap-2 px-2 py-1 bg-slate-900/60 rounded text-slate-200">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                                <span className="font-medium text-[11px]">{name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end">
                      <button
                        onClick={() => setAuditResult(null)}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-lg border-0 cursor-pointer transition-colors"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Grid cards list */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {sortedFilteredModules.map(mod => {
                  const isPlayable = mod.isImplemented;
                  return (
                    <div 
                      key={mod.id}
                      draggable={isPlayable}
                      onDragStart={(e) => handleModuleDragStart(e, mod.id)}
                      onDragEnter={(e) => handleModuleDragEnter(e, mod.id)}
                      onDragEnd={handleModuleDragEnd}
                      onDragOver={(e) => e.preventDefault()}
                      onClick={() => isPlayable && setActiveModule(mod.id)}
                      className={`p-5 rounded-xl border border-slate-800/80 bg-[#0b0f19]/40 flex flex-col gap-3 group transition-all duration-300 relative ${isPlayable ? 'cursor-pointer hover:border-cyan-500/40 hover:bg-[#0b1322]/50 hover:shadow-lg hover:shadow-cyan-500/[0.02]' : 'opacity-30 cursor-not-allowed'} ${draggedModuleId === mod.id ? 'opacity-40' : ''}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-1.5">
                          {isPlayable && (
                            <GripVertical className="w-3.5 h-3.5 text-slate-400 cursor-grab shrink-0 hover:text-cyan-400 transition-colors" />
                          )}
                          <span className="text-[9px] bg-slate-950 text-slate-400 px-2 py-0.5 rounded font-mono border border-slate-800">
                            {(() => {
                              const parentGroup = customGroups.find(g => g.moduleIds.includes(mod.id));
                              const groupDisplayName = parentGroup ? parentGroup.name : mod.category;
                              return getCategoryName(groupDisplayName);
                            })()}
                          </span>
                        </div>
                        {mod.status === 'template' ? (
                          <span className="text-[9px] bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded font-bold border border-indigo-500/20">
                            ⭐ {t('app.badgeTemplate')}
                          </span>
                        ) : mod.isImplemented ? (
                          <span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded font-bold border border-emerald-500/20">
                            {t('app.badgeDev')}
                          </span>
                        ) : (
                          <span className="text-[9px] bg-slate-900 text-slate-400 px-1.5 py-0.5 rounded font-medium border border-slate-800">
                            {t('app.badgeDev')}
                          </span>
                        )}
                      </div>
                    <div>
                      <h3 className={`text-xs font-bold transition-colors ${mod.isImplemented ? 'text-slate-200 group-hover:text-cyan-400' : 'text-slate-400'}`}>
                        {getModuleInfo(mod.id, mod.name).name}
                      </h3>
                      <p className="text-[11px] text-slate-400 leading-relaxed mt-1 flex-1">
                        {getModuleInfo(mod.id, mod.name, mod.description).description}
                      </p>
                    </div>
                  </div>
                );
              })}
              </div>

            </div>
          ) : (
            // Render active subpanel
            <div className="w-full flex-1 flex flex-col h-full overflow-hidden">
              <ErrorBoundary activeModule={activeModule} onBack={() => setActiveModule(null)}>
                <Suspense fallback={<SkeletonLoader />}>
                  <>
                    {activeModule === 'buck' && (
                      <BuckDesignPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'flyback' && (
                      <FlybackPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'mag_inductor' && (
                      <MagInductorPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'mag_transformer' && (
                      <MagTransformerPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'mag_core_loss' && (
                      <MagCoreLossPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'snubber' && (
                      <SnubberPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'power_dclink' && (
                      <PowerDclinkRipplePanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'power_ac_3ph' && (
                      <PowerAc3PhPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'power_foster_thermal' && (
                      <TransientThermalPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'gate_drive_miller' && (
                      <GateDriveMillerPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'heatsink' && (
                      <HeatsinkThermalPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'ldo_thermal' && (
                      <LdoThermalPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'power_device' && (
                      <PowerDeviceSuitePanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'power_dpt' && (
                      <PowerDeviceDptPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'battery_pack' && (
                      <BatteryBmsPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'power_budget' && (
                      <PowerBudgetPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'loop_compensation' && (
                      <LoopCompensationPanel onBack={() => setActiveModule(null)} setActiveModule={setActiveModule} />
                    )}
                    {activeModule === 'digital_pid' && (
                      <DigitalPidPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'filter_passive' && (
                      <FilterPassivePanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'emc_toolbox' && (
                      <EmcToolboxPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'adc_conditioning' && (
                      <AdcConditioningPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'current_shunt' && (
                      <CurrentShuntPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'ntc' && (
                      <NtcCalculatorPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'pwm_mcu_ic' && (
                      <PwmMcuIcPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'tvs_zener' && (
                      <TvsZenerPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'input_protection' && (
                      <InputProtectionPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'pcb_toolbox' && (
                      <PcbToolboxPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'wire_copper_bar' && (
                      <WireCopperBarPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'capacitor_toolbox' && (
                      <CapacitorToolboxPanel onBack={() => setActiveModule(null)} />
                    )}
                    {activeModule === 'db_manager' && (
                      <DatabaseManagementPanel onBack={() => setActiveModule(null)} />
                    )}
                  </>
              </Suspense>
            </ErrorBoundary>
        </div>

          )}
        </div>
      </div>
    </div>
  );
}
