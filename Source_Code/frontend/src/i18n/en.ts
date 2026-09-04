import type { ModuleTranslation } from './types';

export const enDict: Record<string, string> = {
  // Navigation & Shell
  'app.title': 'HW ToolBox Hardware Suite',
  'app.navTitle': 'Navigation Index',
  'app.allModules': 'Workbench Home',
  'app.dashboard': 'Dashboard',
  'app.author': 'Creator: WenZhenJian-EE',
  'app.github': 'GitHub Repository',
  'app.all': 'All',
  'app.addGroup': 'Add Group',
  'app.arch': 'Architecture',
  'app.archValue': 'Hybrid Desktop (React 19 + Python)',
  'app.switchLang': 'Switch Language',
  'app.backendConnected': 'Compute Engine Ready',
  'app.backendConnecting': 'Connecting Engine...',

  // Dashboard Welcome Card
  'app.welcomeTitle': 'Power Electronics Co-Design & Engineering Suite',
  'app.welcomeDesc': 'Seamless integration of analytical physical equations, topology simulations, time/frequency domain Bode sweeps, and commercial BOM databases. Choose or search a module below.',
  'app.totalModules': 'Active Modules',
  'app.verifiedModels': 'Pass Rate',
  'app.activeTopologies': 'Native English',

  // Controls & Toolbar
  'app.searchPlaceholder': 'Search modules, terminology, physics...',
  'app.resetLayout': 'Reset Default Layout',
  'app.columns': 'Columns',
  'app.uncategorized': 'Uncategorized',

  // Module Badges & Status
  'app.badgeTemplate': 'Template',
  'app.badgeDev': 'Ready',

  // Error Boundary
  'app.errorTitle': 'Module Rendering Error',
  'app.errorDesc': 'An uncaught runtime exception occurred while rendering this module.',
  'app.errorRetry': 'Retry Current Module',

  // Categories
  'cat.all': 'All',
  'cat.co_design': '⚡ Power Co-Design',
  'cat.magnetics': '🧲 Magnetics & Basics',
  'cat.power_thermal': '🔥 Power & Thermal',
  'cat.loop_signal': '📈 Loop & Signals',
  'cat.passives_safety': '🛡️ Passives & Safety',

  // Common Engineering Terms
  'common.calculate': 'Calculate / Simulate',
  'common.reset': 'Reset Defaults',
  'common.export': 'Export Data',
  'common.schematic': 'Interactive Schematic',
  'common.specs': 'Operating Specs & Conditions',
  'common.bom': 'Commercial BOM Selection',
  'common.waveforms': 'Time & Frequency Analysis',
  'common.drc': 'Safety DRC Verification',
  'common.results': 'Design & Sizing Results',
  'common.parameters': 'Input Parameters',
  'common.theory': 'Physical Derivations & Theory',
};

export const enModules: Record<string, ModuleTranslation> = {
  buck: {
    name: 'Buck Synchronous Converter',
    description: 'Buck converter steady-state analysis, CCM/DCM inductor current waveforms, closed-loop Bode sweep, output capacitor ESR ripple sizing, and commercial BOM matching.'
  },
  flyback: {
    name: 'Flyback Isolated Converter',
    description: 'Isolated Flyback converter design, AP-method transformer selection, synchronous rectifier loss calculation, RCD snubber clamping, and closed-loop Bode analysis.'
  },
  mag_inductor: {
    name: 'Power Inductor Magnetic Design',
    description: 'Calculate magnetic core, air gap, and winding wire specifications with Dowell high-frequency AC winding loss, fringing flux correction, and DC-bias saturation checking.'
  },
  mag_transformer: {
    name: 'High-Frequency Integrated Transformer',
    description: 'Design forward, flyback, and LLC integrated transformers, calculating AP core geometry sizing, AC resistance factor Fr, and equivalent leakage inductance.'
  },
  mag_core_loss: {
    name: 'Magnetic Core Loss Evaluation (iGSE)',
    description: 'Calculate core volumetric loss under non-sinusoidal excitation using the Improved Generalized Steinmetz Equation (iGSE) coupled with steady-state thermal rise.'
  },
  snubber: {
    name: 'Switch Snubber & Clamp Design',
    description: 'Design RC snubber and RCD clamp snubbers for turn-off ringing suppression using resonance frequency shift or analytical capacitor charging models.'
  },
  power_dclink: {
    name: 'DC-Link Capacitor Ripple & Lifetime',
    description: 'Calculate RMS ripple currents for single/three-phase inverters, evaluate ESR thermal dissipation, and predict aluminum electrolytic capacitor operating lifetimes.'
  },
  power_ac_3ph: {
    name: '3-Phase AC & Vector Transforms',
    description: 'Solve 3-phase Y-Delta impedance transformations, Clarke/Park alpha-beta/dq vector projections, reactive power compensation, and phase-locked loop (PLL) parameters.'
  },
  power_foster_thermal: {
    name: 'Transient Thermal & Foster RC Network',
    description: 'Simulate power semiconductor dynamic junction temperature swings under transient pulse overload using high-order Foster RC thermal impedance state-space solvers.'
  },
  gate_drive_miller: {
    name: 'Gate Drive & Miller Effect Verification',
    description: 'Verify high-speed switching transistors (SiC/GaN) against gate dv/dt parasitic Miller turn-on, dead-time switching losses, and ZVS turn-on criteria.'
  },
  heatsink: {
    name: 'Heatsink Thermal Resistance & Sizing',
    description: 'Calculate natural and forced-convection equivalent thermal resistance, fin geometry spacing, air velocity Reynolds numbers, and multi-node thermal models.'
  },
  ldo_thermal: {
    name: 'LDO Linear Regulator & Thermal Dissipation',
    description: 'Compute linear voltage drop thermal loss, PCB copper polygon heatsinking area boundaries, and junction-to-ambient thermal resistance design rule limits.'
  },
  power_device: {
    name: 'Power Semiconductor Loss & Thermal Sizing',
    description: 'Evaluate MOSFET and IGBT conduction, switching (Eon/Eoff), and gate drive losses, assessing Miller plateau times and junction temperature derating.'
  },
  power_dpt: {
    name: 'Double Pulse Test (DPT) Calculator',
    description: 'Calculate inductive switching circuit charging pulse width, freewheeling interval timing, and extract turn-on/turn-off cross-overlap energies.'
  },
  battery_pack: {
    name: 'Battery Pack & BMS Sizing Calculator',
    description: 'Model lithium battery pack series/parallel cell topologies, internal resistance self-heating dissipation, and passive bleeding resistor balancing.'
  },
  power_budget: {
    name: 'Power Converter Loss & Efficiency Budget',
    description: 'Aggregate converter semiconductor switches, magnetic inductors/transformers, snubbers, and auxiliary control power losses into a comprehensive efficiency budget.'
  },
  loop_compensation: {
    name: 'Analog Control Loop Compensation',
    description: 'Synthesize Type II/III op-amp compensators and optocoupler-isolated TL431 networks, placing poles and zeroes to optimize crossover frequency and phase margin.'
  },
  digital_pid: {
    name: 'Digital PID & Discretization Calculator',
    description: 'Transform continuous S-domain transfer functions into discrete Z-domain difference equations via Tustin/Bilinear methods, outputting ready-to-run C firmware code.'
  },
  filter_passive: {
    name: 'Passive & Active Filter Design',
    description: 'Design low-pass/high-pass Butterworth, Chebyshev, and passive LC/pi filters, evaluating input decoupling impedance and Middlebrook stability criteria.'
  },
  emc_toolbox: {
    name: 'EMC Filter & Damping Toolbox',
    description: 'Convert EMI unit domains (dBm, dBuV, V, W), model common-mode and differential-mode attenuation, enclosure aperture shielding, and RC damping networks.'
  },
  adc_conditioning: {
    name: 'ADC Signal Conditioning & Charge Bucket',
    description: 'Size anti-aliasing RC filter bandwidth, input charge bucket settling times, op-amp gain scaling, full-scale dynamic range, and two-point calibration offsets.'
  },
  current_shunt: {
    name: 'Current Shunt & Current Transformer (CT)',
    description: 'Size current sensing shunts and current transformer burden resistors, evaluating thermal dissipation, Kelvin sense routing trace error, and saturation flux.'
  },
  ntc: {
    name: 'NTC Temperature & Steinhart-Hart Fitting',
    description: 'Extract Beta constants or perform 3-point polynomial curve fitting using the Steinhart-Hart equation, sizing linearization dividers and generating C lookup tables.'
  },
  pwm_mcu_ic: {
    name: 'PWM Timer & Controller IC Peripherals',
    description: 'Size PWM DAC RC low-pass filter ripple; calculate digital micro-controller timer dead-time registers; and size analog controller oscillator RT/CT networks.'
  },
  tvs_zener: {
    name: 'TVS & Zener Surge Protection Sizing',
    description: 'Size Zener steady-state current-limiting resistors and evaluate TVS diode peak pulse power (Ppp), clamping voltage, and transient junction thermal rise.'
  },
  input_protection: {
    name: 'Input Protection & Safety Bleed Sizing',
    description: 'Verify inrush fuse I^2t energy pulse withstand, size inrush power NTC thermistors, and design AC safety discharge bleeding resistor time constants.'
  },
  pcb_toolbox: {
    name: 'PCB Trace & Via Current Thermal Sizing',
    description: 'Compute internal/external trace ampacity and thermal temperature rise based on IPC-2152, via parasitic inductance, and microstrip RF impedance.'
  },
  wire_copper_bar: {
    name: 'Winding Wire & High-Current Copper Busbar',
    description: 'Analyze high-frequency Litz wire skin and proximity effect AC resistance, evaluate solid copper wire ampacity, and size high-current busbar steady-state heating.'
  },
  capacitor_toolbox: {
    name: 'Capacitor Life & Voltage Derating',
    description: 'Model Arrhenius thermal lifespan acceleration for electrolytic capacitors, multi-frequency RMS ripple aggregation, and MLCC DC-bias capacitance derating.'
  },
  db_manager: {
    name: 'Component & Magnetic Material Database',
    description: 'Manage and query local SQLite records of power MOSFETs, IGBTs, Schottky diodes, core material Steinmetz coefficients, and geometric bobbins.'
  }
};
