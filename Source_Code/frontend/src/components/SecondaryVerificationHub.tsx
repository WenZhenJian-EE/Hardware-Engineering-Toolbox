import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import {
  Cpu,
  Flame,
  Layers,
  ShieldAlert,
  Sliders,
  Zap
} from 'lucide-react';

// Verification Card Metadata Definition
interface VerificationCard {
  id: string;
  title: string;
  zone: 'stress' | 'physics' | 'thermal' | 'control' | 'safety';
  description: string;
  equation: string;
  targetModule: string;
  // Navigation payload generator for localStorage
  getPayload: (params: HubParams) => any;
  // SVG schematic diagram renderer
  renderSvg: () => React.ReactNode;
}

interface HubParams {
  vinMin: number;
  vinNom: number;
  vinMax: number;
  vout: number;
  iout: number;
  fsw: number;
  power: number;
}

interface SecondaryVerificationHubProps {
  vinMin?: number;
  vinNom?: number;
  vinMax?: number;
  vout?: number;
  iout?: number;
  fsw?: number;
  power?: number;
  topology?: string;
  setActiveModule?: (module: string) => void;
}

export default function SecondaryVerificationHub({
  vinMin = 380,
  vinNom = 400,
  vinMax = 420,
  vout = 12,
  iout = 20,
  fsw = 100,
  power = 240,
  topology,
  setActiveModule
}: SecondaryVerificationHubProps) {
  const params: HubParams = { vinMin, vinNom, vinMax, vout, iout, fsw, power };
  const containerRef = useRef<HTMLDivElement>(null);

  // 1. Initial 20 Secondary Verification Cards
  const defaultCards: VerificationCard[] = [
    // === 1. Passive Electrical Stress ===
    {
      id: 'stress_inductor',
      title: 'DC-Bias Soft Saturation',
      zone: 'stress',
      description: 'Estimate inductor core and copper losses at ripple current ratio, checking DC bias soft-saturation.',
      equation: 'ΔI_L = (V_in - V_out) * D / (L * f_sw)',
      targetModule: 'mag_inductor',
      getPayload: (p) => ({
        tab: 'dc_bias',
        params: { l_uh: 15.0, iout: p.iout, ipeak: p.iout * 1.25 }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <path d="M 10 30 Q 25 15, 40 30 Q 55 15, 70 30 Q 85 15, 100 30 Q 115 15, 130 30 H 190" strokeWidth="1.5" />
          <path d="M 10 50 L 50 35 L 90 50 L 130 35 L 170 50" stroke="#f43f5e" strokeWidth="1" strokeDasharray="3,3" />
          <text x="145" y="25" fill="#94a3b8" fontSize="8" stroke="none">L_filter</text>
          <text x="140" y="47" fill="#f43f5e" fontSize="7" stroke="none">ΔI_L Ripple</text>
        </svg>
      )
    },
    {
      id: 'stress_capacitor',
      title: 'DC-Link Ripple Stress',
      zone: 'stress',
      description: 'Verify input and output capacitor high-frequency AC RMS ripple current and thermal dissipation.',
      equation: 'P_loss = I_rms^2 * ESR',
      targetModule: 'capacitor_toolbox',
      getPayload: (p) => ({
        tab: 'topology',
        cap_type: 'Electrolytic',
        cap_val: 220.0,
        esr_mohm: 25.0,
        i_rms: p.iout * 0.6,
        v_dc: p.vinNom
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <rect x="50" y="15" width="20" height="35" rx="2" strokeWidth="1.5" />
          <rect x="80" y="15" width="20" height="35" rx="2" strokeWidth="1.5" />
          <rect x="110" y="15" width="20" height="35" rx="2" strokeWidth="1.5" />
          <path d="M 30 32.5 H 50 M 70 32.5 H 80 M 100 32.5 H 110 M 130 32.5 H 170" strokeWidth="1.5" />
          <path d="M 30 48 Q 50 58, 70 48 T 110 48" stroke="#f43f5e" strokeWidth="1" />
          <text x="135" y="25" fill="#94a3b8" fontSize="8" stroke="none">C_bank</text>
          <text x="125" y="52" fill="#f43f5e" fontSize="7" stroke="none">I_rms Stress</text>
        </svg>
      )
    },
    {
      id: 'stress_lc',
      title: 'LC Filter Resonance',
      zone: 'stress',
      description: 'Analyze LC differential 2nd-order filter cutoff frequency and damping stability margin.',
      equation: 'f_c = 1 / (2*π * sqrt(L * C))',
      targetModule: 'filter_passive',
      getPayload: (p) => ({
        l_uh: 10.0,
        c_uf: 100.0,
        fsw_khz: p.fsw
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <path d="M 10 32.5 Q 25 15, 40 32.5 Q 55 15, 70 32.5 H 120 M 120 32.5 H 190" strokeWidth="1.5" />
          <path d="M 120 32.5 V 45" strokeWidth="1.5" />
          <rect x="105" y="45" width="30" height="4" fill="rgba(6, 182, 212, 0.2)" strokeWidth="1.5" />
          <rect x="105" y="53" width="30" height="4" fill="rgba(6, 182, 212, 0.2)" strokeWidth="1.5" />
          <path d="M 120 57 V 65 M 105 65 H 135" strokeWidth="1" />
          <text x="40" y="52" fill="#94a3b8" fontSize="8" stroke="none">f_cutoff</text>
        </svg>
      )
    },

    // === 2. Magnetics & Capacitor Physical Lifetime ===
    {
      id: 'life_inductor',
      title: 'Core Air Gap & Dowell AC Loss',
      zone: 'physics',
      description: 'Custom magnetic inductor sizing: air gap depth, Dowell AC skin effect factor Fr, and window fill factor.',
      equation: 'B_max = L * I_pk / (N * A_e)',
      targetModule: 'mag_inductor',
      getPayload: (p) => ({
        tab: 'gap',
        params: { l_uh: 15.0, iout: p.iout, fsw: p.fsw }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-emerald-400 stroke-current fill-none">
          <rect x="30" y="10" width="140" height="45" rx="5" strokeWidth="1.5" />
          <rect x="50" y="20" width="100" height="25" rx="2" strokeWidth="1.5" />
          <line x1="100" y1="10" x2="100" y2="20" stroke="#f43f5e" strokeWidth="2" />
          <line x1="100" y1="45" x2="100" y2="55" stroke="#f43f5e" strokeWidth="2" />
          <text x="105" y="18" fill="#f43f5e" fontSize="7" stroke="none">Air Gap</text>
          <text x="65" y="35" fill="#94a3b8" fontSize="8" stroke="none">Core Ae</text>
        </svg>
      )
    },
    {
      id: 'life_transformer',
      title: 'High-Frequency Transformer',
      zone: 'physics',
      description: 'Verify transformer primary/secondary magnetizing and leakage inductance, current density, and Steinmetz core loss.',
      equation: 'P_core = V_e * K * f^a * B^b',
      targetModule: 'mag_transformer',
      getPayload: (p) => ({
        tab: (topology === 'flyback' || topology === 'acf') ? 'flyback' : 'forward',
        params: { 
          vin_min: p.vinMin, 
          vbus: p.vinNom, 
          pout: p.power, 
          fsw_khz: p.fsw,
          fly_vin: p.vinNom,
          fly_vor: p.vinNom * 0.5,
          fly_vout: p.vout,
          fly_iout: p.iout,
          fly_fsw: p.fsw
        }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-emerald-400 stroke-current fill-none">
          <rect x="40" y="10" width="120" height="45" strokeWidth="1.5" />
          <circle cx="65" cy="32.5" r="10" strokeWidth="1.5" />
          <circle cx="135" cy="32.5" r="10" strokeWidth="1.5" strokeDasharray="2,2" />
          <path d="M 65 32.5 H 135" stroke="#a855f7" strokeWidth="1" />
          <text x="58" y="35" fill="#10b981" fontSize="8" stroke="none">Np</text>
          <text x="128" y="35" fill="#10b981" fontSize="8" stroke="none">Ns</text>
        </svg>
      )
    },
    {
      id: 'life_capacitor',
      title: 'Capacitor Thermal Lifetime',
      zone: 'physics',
      description: 'Evaluate capacitor core thermal rise, electrolyte evaporation, and Arrhenius 10°C lifetime doubling rule.',
      equation: 'Life = Life_0 * 2^((T_max - T_actual)/10)',
      targetModule: 'capacitor_toolbox',
      getPayload: (p) => ({
        tab: 'life',
        cap_type: 'Electrolytic',
        cap_val: 470.0,
        esr_mohm: 15.0,
        v_actual: p.vout,
        v_nominal: p.vout * 1.25,
        i_rms_phase: p.iout * 0.7
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-emerald-400 stroke-current fill-none">
          <rect x="80" y="10" width="40" height="50" rx="3" strokeWidth="1.5" />
          <line x1="95" y1="60" x2="95" y2="65" strokeWidth="1.5" />
          <line x1="105" y1="60" x2="105" y2="65" strokeWidth="1.5" />
          <path d="M 75 25 Q 60 20, 50 30 M 75 40 Q 60 40, 50 50" stroke="#f43f5e" strokeWidth="1" />
          <text x="125" y="30" fill="#94a3b8" fontSize="8" stroke="none">Temp Rise</text>
        </svg>
      )
    },

    // === 3. Semiconductor Gate Drive & Thermal ===
    {
      id: 'mosfet_miller',
      title: 'Gate Miller Verification',
      zone: 'thermal',
      description: 'Simulate high dV/dt turn-off transient and check whether Cgd displacement current causes false gate turn-on.',
      equation: 'V_gs_spike = R_g * C_gd * dV_ds/dt',
      targetModule: 'gate_drive_miller',
      getPayload: (p) => ({
        tab: 'miller',
        params: {
          v_bus: p.vinNom,
          f_sw: p.fsw
        }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-rose-400 stroke-current fill-none">
          <path d="M 60 15 V 50 M 60 32.5 H 90 M 90 20 V 45" strokeWidth="1.5" />
          <line x1="105" y1="20" x2="105" y2="45" strokeWidth="1.5" />
          <line x1="97" y1="25" x2="105" y2="25" strokeWidth="1" />
          <line x1="97" y1="40" x2="105" y2="40" strokeWidth="1" />
          <path d="M 70 32.5 Q 70 10, 100 10" stroke="#f43f5e" strokeWidth="1" strokeDasharray="2,2" />
          <text x="75" y="8" fill="#f43f5e" fontSize="7" stroke="none">C_gd Miller</text>
        </svg>
      )
    },
    {
      id: 'dead_time',
      title: 'Dead-Time Optimization',
      zone: 'thermal',
      description: 'Tune minimum dead-time to avoid half-bridge shoot-through, balancing body diode conduction loss.',
      equation: 't_dead_min = t_d_off_max - t_d_on_min',
      targetModule: 'gate_drive_miller',
      getPayload: (p) => ({
        tab: 'deadtime',
        params: {
          f_sw: p.fsw
        }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 stroke-current fill-none">
          <path d="M 10 20 H 60 V 40 H 130 V 20 H 190" stroke="#3b82f6" strokeWidth="1.5" />
          <path d="M 10 50 H 75 V 30 H 145 V 50 H 190" stroke="#10b981" strokeWidth="1.5" />
          <rect x="60" y="15" width="15" height="40" fill="rgba(244, 63, 94, 0.15)" stroke="none" />
          <text x="62" y="10" fill="#f43f5e" fontSize="7" stroke="none">Deadtime</text>
        </svg>
      )
    },
    {
      id: 'transient_tj',
      title: 'Steady-State Thermal Network',
      zone: 'thermal',
      description: 'Solve Foster/Cauer thermal impedance network to verify semiconductor junction temperature under peak overload.',
      equation: 'T_j(t) = P_loss * Z_th_jc(t) + T_c',
      targetModule: 'heatsink',
      getPayload: (p) => ({
        tab: 'steady',
        params: { p_diss: p.power * 0.05, t_j_max: 150.0, t_amb: 50.0, r_jc: 1.0, r_cs: 0.5 }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-rose-400 stroke-current fill-none">
          <rect x="30" y="45" width="30" height="15" fill="rgba(244, 63, 94, 0.2)" strokeWidth="1" />
          <rect x="85" y="45" width="30" height="15" fill="rgba(244, 63, 94, 0.2)" strokeWidth="1" />
          <path d="M 45 45 Q 60 20, 100 20 T 170 20" stroke="#f43f5e" strokeWidth="1.5" />
          <text x="105" y="15" fill="#94a3b8" fontSize="8" stroke="none">T_j Peak</text>
        </svg>
      )
    },
    {
      id: 'semi_soa',
      title: 'Switching SOA Boundary',
      zone: 'thermal',
      description: 'Inspect transient turn-off V-I trajectory to ensure operation remains strictly within Safe Operating Area.',
      equation: 'V_ds * I_d < P_max_pulse',
      targetModule: 'power_device',
      getPayload: (p) => ({
        tab: 'soa',
        params: {
          v_ds: p.vinNom * 1.25,
          i_d: p.iout * 1.5
        }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-rose-400 stroke-current fill-none">
          <path d="M 20 10 V 55 H 180" stroke="#94a3b8" strokeWidth="1.2" />
          <path d="M 20 20 H 70 L 120 40 L 160 55" strokeWidth="1.5" />
          <path d="M 120 15 L 140 30" stroke="#f43f5e" strokeWidth="1" />
          <text x="145" y="20" fill="#f43f5e" fontSize="7" stroke="none">Unsafe SOA</text>
        </svg>
      )
    },

    // === 4. Control Loop & Precision Signal Sensing ===
    {
      id: 'control_pid',
      title: 'S-Z Bilinear Transform',
      zone: 'control',
      description: 'Discretize continuous analog compensation poles and zeros via Tustin transform into discrete difference equations.',
      equation: 'G(z) = (b0 + b1*z^-1 + b2*z^-2)/(1 - z^-1)',
      targetModule: 'digital_pid',
      getPayload: (p) => ({
        tab: 's2z',
        kp: 1.5,
        ki: 100.0,
        kd: 0.0,
        ts: 1.0 / p.fsw
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-amber-400 stroke-current fill-none">
          <rect x="25" y="20" width="35" height="25" rx="3" strokeWidth="1.5" />
          <rect x="80" y="20" width="35" height="25" rx="3" strokeWidth="1.5" />
          <rect x="135" y="20" width="35" height="25" rx="3" strokeWidth="1.5" />
          <path d="M 10 32.5 H 25 M 60 32.5 H 80 M 115 32.5 H 135 M 170 32.5 H 190" strokeWidth="1" />
          <text x="35" y="35" fill="#f59e0b" fontSize="10" stroke="none">P</text>
          <text x="92" y="35" fill="#f59e0b" fontSize="10" stroke="none">I</text>
          <text x="147" y="35" fill="#f59e0b" fontSize="10" stroke="none">D</text>
        </svg>
      )
    },
    {
      id: 'current_shunt',
      title: 'Current Shunt & Kelvin Sense',
      zone: 'control',
      description: 'Assess shunt thermal drift, dissipation, and size 4-terminal Kelvin sensing copper trace routing.',
      equation: 'R_t = R_0 * (1 + TCR * (T - 25))',
      targetModule: 'current_shunt',
      getPayload: (p) => ({
        tab: 'shunt',
        i_max: p.iout * 1.2,
        r_shunt_mohm: 1.0
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-amber-400 stroke-current fill-none">
          <rect x="40" y="25" width="120" height="15" fill="rgba(245, 158, 11, 0.2)" strokeWidth="1.5" />
          <circle cx="50" cy="32.5" r="2.5" fill="#f43f5e" stroke="none" />
          <circle cx="150" cy="32.5" r="2.5" fill="#f43f5e" stroke="none" />
          <path d="M 50 32.5 V 15 H 65 M 150 32.5 V 15 H 135" stroke="#f43f5e" strokeWidth="1" />
          <text x="75" y="13" fill="#f43f5e" fontSize="7" stroke="none">Kelvin Sensing</text>
        </svg>
      )
    },
    {
      id: 'signal_opamp',
      title: 'Op-Amp & ADC Signal Error',
      zone: 'control',
      description: 'Calculate input offset voltage, resistor drift error, and set ADC anti-aliasing filter cutoff.',
      equation: 'f_lp = 1 / (2*π * R_adc * C_adc)',
      targetModule: 'adc_conditioning',
      getPayload: (p) => ({
        tab: 'error',
        gain: 10.0,
        f_cutoff: p.fsw / 2.0
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-amber-400 stroke-current fill-none">
          <path d="M 40 15 L 90 32.5 L 40 50 Z M 90 32.5 H 140 Q 155 32.5, 170 32.5" strokeWidth="1.5" />
          <line x1="20" x2="40" y1="25" y2="25" strokeWidth="1.5" />
          <line x1="20" x2="40" y1="40" y2="40" strokeWidth="1.5" />
          <path d="M 140 32.5 V 45" strokeWidth="1.2" />
          <circle cx="140" cy="52" r="3" strokeWidth="1.2" />
          <line x1="140" y1="55" x2="140" y2="60" strokeWidth="1.2" />
          <text x="98" y="28" fill="#94a3b8" fontSize="8" stroke="none">Opamp</text>
        </svg>
      )
    },
    {
      id: 'pwm_mcu',
      title: 'MCU PWM Timer & Deadband',
      zone: 'control',
      description: 'Verify MCU PWM dead-time registers and evaluate gate driver peak source/sink current drive capability.',
      equation: 'I_peak = V_drv / (R_g_ext + R_g_int)',
      targetModule: 'pwm_mcu_ic',
      getPayload: (p) => ({
        tab: 'timer',
        fsw_khz: p.fsw
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-amber-400 stroke-current fill-none">
          <rect x="20" y="15" width="40" height="35" rx="3" strokeWidth="1.5" />
          <rect x="100" y="15" width="50" height="35" rx="3" strokeWidth="1.5" />
          <path d="M 60 32.5 H 100 M 150 32.5 H 180" strokeWidth="1.2" />
          <path d="M 67 25 L 75 32.5 L 67 40" strokeWidth="1" />
          <text x="28" y="36" fill="#94a3b8" fontSize="8" stroke="none">MCU</text>
          <text x="108" y="36" fill="#94a3b8" fontSize="8" stroke="none">Driver IC</text>
        </svg>
      )
    },

    // === 5. System Safety & High-Current PCB/Busbar ===
    {
      id: 'fuse_ntc',
      title: 'Inrush NTC Limiting',
      zone: 'safety',
      description: 'Model startup bulk capacitor charging inrush surge current to size power NTC resistance and fuse I²t rating.',
      equation: 'I_surge_max = V_in_pk / R_ntc',
      targetModule: 'input_protection',
      getPayload: (p) => ({
        tab: 'ntc',
        v_in_pk: p.vinMax * 1.414,
        c_bulk_uf: 470.0
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <rect x="40" y="27.5" width="50" height="10" rx="2" strokeWidth="1.5" />
          <path d="M 40 32.5 H 90 M 10 32.5 H 40 M 90 32.5 H 120" strokeWidth="1.5" />
          <circle cx="140" cy="32.5" r="10" strokeWidth="1.5" fill="rgba(168, 85, 247, 0.2)" />
          <path d="M 120 32.5 H 130 M 150 32.5 H 190" strokeWidth="1.2" />
          <text x="50" y="22" fill="#94a3b8" fontSize="8" stroke="none">Fuse</text>
          <text x="131" y="35" fill="#a855f7" fontSize="8" stroke="none">NTC</text>
        </svg>
      )
    },
    {
      id: 'tvs_zener',
      title: 'Transient TVS Clamping',
      zone: 'safety',
      description: 'Size TVS diode peak pulse power dissipation and verify clamping voltage under transient voltage surges.',
      equation: 'V_clamp < V_ds_max_mosfet',
      targetModule: 'tvs_zener',
      getPayload: (p) => ({
        tab: 'tvs',
        v_working: p.vout * 1.15
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <path d="M 20 32.5 H 90 M 110 32.5 H 180" strokeWidth="1.5" />
          <path d="M 90 20 H 110 M 90 45 H 110 M 100 20 V 45" strokeWidth="1.5" />
          <path d="M 90 20 L 110 45 M 110 20 L 90 45" stroke="#f43f5e" strokeWidth="1" strokeDasharray="2,2" />
          <path d="M 40 10 Q 70 10, 100 25 T 160 25" stroke="#f43f5e" strokeWidth="1.5" />
          <text x="115" y="18" fill="#f43f5e" fontSize="7" stroke="none">Clamped</text>
        </svg>
      )
    },
    {
      id: 'rcd_snubber',
      title: 'RCD Clamp & Snubber',
      zone: 'safety',
      description: 'Suppress diode reverse recovery or MOSFET turn-off inductive voltage spikes with RC or RCD snubber networks.',
      equation: 'C_sn = 3 * C_oss , R_sn = 1 / (2*π * f_ring * C_sn)',
      targetModule: 'snubber',
      getPayload: (p) => ({
        tab: 'rcd',
        params: { rcd_llk: 5.0, rcd_ipk: p.iout * 0.1, rcd_vor: p.vout * 2.0, rcd_fsw: p.fsw, rcd_vin: p.vinNom, rcd_vds_rating: 650.0 }
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <path d="M 30 32.5 H 70 V 15 H 130 V 32.5 M 130 32.5 H 170" strokeWidth="1.5" />
          <path d="M 90 15 V 30" strokeWidth="1.5" />
          <rect x="80" y="30" width="20" height="8" strokeWidth="1.5" />
          <rect x="82" y="38" width="16" height="4" strokeWidth="1.5" />
          <text x="105" y="25" fill="#94a3b8" fontSize="8" stroke="none">R_sn</text>
          <text x="105" y="47" fill="#94a3b8" fontSize="8" stroke="none">C_sn</text>
        </svg>
      )
    },
    {
      id: 'creepage_clearance',
      title: 'Creepage & Clearance Spacing',
      zone: 'safety',
      description: 'Calculate PCB insulation creepage and clearance distances based on IEC 62368 with altitude correction.',
      equation: 'Clearance_adj = Clearance * Altitude_Factor',
      targetModule: 'pcb_toolbox',
      getPayload: (p) => ({
        voltage: p.vinMax,
        altitude: 2000
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <rect x="20" y="40" width="160" height="15" fill="rgba(168, 85, 247, 0.2)" strokeWidth="1.2" />
          <path d="M 70 40 V 50 H 130 V 40" stroke="#f43f5e" strokeWidth="1.5" />
          <path d="M 70 25 H 130" stroke="#10b981" strokeWidth="1" strokeDasharray="3,3" />
          <text x="80" y="20" fill="#10b981" fontSize="8" stroke="none">Clearance (Air)</text>
          <text x="80" y="60" fill="#f43f5e" fontSize="8" stroke="none">Creepage (Groove)</text>
        </svg>
      )
    },
    {
      id: 'pcb_temp',
      title: 'PCB Trace Ampacity',
      zone: 'safety',
      description: 'Compute internal and external high-current copper track width and thickness for allowed thermal rise per IPC-2152.',
      equation: 'I = K * ΔT^0.44 * A^0.725',
      targetModule: 'pcb_toolbox',
      getPayload: (p) => ({
        tab: 'trace',
        i_trace: p.iout,
        delta_t: 20.0
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <rect x="30" y="30" width="140" height="10" fill="rgba(168, 85, 247, 0.3)" strokeWidth="1.5" />
          <path d="M 20 40 H 180" stroke="#94a3b8" strokeWidth="1.5" />
          <text x="35" y="22" fill="#94a3b8" fontSize="8" stroke="none">Copper Trace (Width W)</text>
          <text x="142" y="22" fill="#f43f5e" fontSize="7" stroke="none">Thickness T</text>
        </svg>
      )
    },
    {
      id: 'wire_copper',
      title: 'AWG Wire & Busbar Sizing',
      zone: 'safety',
      description: 'Evaluate round copper wire skin depth derating and size high-current copper busbar cross-section ampacity.',
      equation: 'δ = 66.1 / sqrt(f_sw)',
      targetModule: 'wire_copper_bar',
      getPayload: (p) => ({
        tab: 'awg',
        current: p.iout,
        i_rms: p.iout,
        f_hz: p.fsw * 1000
      }),
      renderSvg: () => (
        <svg viewBox="0 0 200 65" className="w-full h-14 text-cyan-400 stroke-current fill-none">
          <circle cx="100" cy="32.5" r="20" strokeWidth="1.5" fill="rgba(168, 85, 247, 0.1)" />
          <circle cx="100" cy="32.5" r="14" stroke="#f43f5e" strokeWidth="1.2" strokeDasharray="3,3" />
          <text x="125" y="26" fill="#94a3b8" fontSize="8" stroke="none">AWG Wire</text>
          <text x="125" y="45" fill="#f43f5e" fontSize="7" stroke="none">Skin Depth δ</text>
        </svg>
      )
    }
  ];

  // Filter verification items not applicable to the current converter topology
  const isCardApplicable = (cardId: string, topo: string | undefined): boolean => {
    if (!topo) return true;
    const lowerTopo = topo.toLowerCase();
    const isIsolated = ['flyback', 'acf', 'llc', 'forward', 'psfb', 'dab', 'cllc'].includes(lowerTopo);
    const hasInductor = ['buck', 'boost', 'buck_boost', 'bidirectional_buck_boost', 'nonisolated_buck_boost', 'four_switch_buck_boost', 'forward', 'vienna', 'totempole', 'afe', 'ttype', 'interleaved_pfc', 'dual_boost', 'interleaved_boost', 'interleaved_sbb'].includes(lowerTopo);
    const hasTransformer = isIsolated;
    const hasSyncRectOrBridge = ['buck', 'llc', 'dab', 'cllc', 'vienna', 'totempole', 'afe', 'psfb', 'acf', 'ttype', 'interleaved_pfc', 'dual_boost', 'interleaved_boost', 'interleaved_sbb'].includes(lowerTopo);
    const hasLcFilter = ['buck', 'forward', 'boost', 'buck_boost', 'totempole', 'afe', 'interleaved_sbb'].includes(lowerTopo);
    const hasSnubber = ['buck', 'boost', 'buck_boost', 'flyback', 'acf', 'forward', 'psfb', 'dab', 'interleaved_sbb'].includes(lowerTopo);

    switch (cardId) {
      case 'stress_inductor':
      case 'life_inductor':
        return hasInductor;
      case 'life_transformer':
        return hasTransformer;
      case 'stress_lc':
        return hasLcFilter;
      case 'dead_time':
        return hasSyncRectOrBridge;
      case 'rcd_snubber':
        return hasSnubber;
      default:
        return true;
    }
  };

  const filteredDefaultCards = defaultCards.filter(c => isCardApplicable(c.id, topology));

  // State
  const [cards, setCards] = useState<VerificationCard[]>([]);
  const [cardsWidth, setCardsWidth] = useState<Record<string, number>>({});
  const [isResizing, setIsResizing] = useState<boolean>(false);

  // Initialize and load preferences from localStorage
  useEffect(() => {
    const savedOrder = localStorage.getItem('secondary_verification_cards_order');
    let orderedCards = [...filteredDefaultCards];
    if (savedOrder) {
      try {
        const orderIds: string[] = JSON.parse(savedOrder);
        orderedCards = orderIds
          .map(id => filteredDefaultCards.find(c => c.id === id))
          .filter((c): c is VerificationCard => !!c);
        filteredDefaultCards.forEach(dc => {
          if (!orderedCards.find(oc => oc.id === dc.id)) {
            orderedCards.push(dc);
          }
        });
      } catch (e) {
        console.warn('Failed to parse cards order preference from localStorage', e);
      }
    }
    setCards(orderedCards);

    const savedWidths = localStorage.getItem('secondary_verification_cards_widths');
    let widths: Record<string, number> = {};
    if (savedWidths) {
      try {
        widths = JSON.parse(savedWidths);
      } catch (e) {
        console.warn('Failed to parse cards widths from localStorage', e);
      }
    }
    const finalWidths: Record<string, number> = { ...widths };
    orderedCards.forEach(c => {
      if (finalWidths[c.id] === undefined) {
        finalWidths[c.id] = ['creepage_clearance', 'pcb_temp', 'dead_time', 'semi_soa'].includes(c.id) ? 6 : 4;
      }
    });
    setCardsWidth(finalWidths);
  }, [topology]);

  // 2. HTML5 Drag and Drop reordering logic
  const [draggedCardId, setDraggedCardId] = useState<string | null>(null);

  const handleDragStart = (e: React.DragEvent, id: string) => {
    if (isResizing) {
      e.preventDefault();
      return;
    }
    setDraggedCardId(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggedCardId || draggedCardId === targetId) return;

    const draggedIdx = cards.findIndex(c => c.id === draggedCardId);
    const targetIdx = cards.findIndex(c => c.id === targetId);
    if (draggedIdx !== -1 && targetIdx !== -1) {
      const updatedCards = [...cards];
      const [movedCard] = updatedCards.splice(draggedIdx, 1);
      updatedCards.splice(targetIdx, 0, movedCard);
      setCards(updatedCards);
    }
  };

  const handleDragEnd = () => {
    setDraggedCardId(null);
    const orderIds = cards.map(c => c.id);
    localStorage.setItem('secondary_verification_cards_order', JSON.stringify(orderIds));
  };

  // 3. Grid Resize logic
  const resizeStartRef = useRef<{
    cardId: string;
    startWidthPx: number;
    startCols: number;
    gridUnitPx: number;
  } | null>(null);

  const handleResizeMouseDown = (e: React.MouseEvent, cardId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);

    const cardElement = (e.target as HTMLElement).closest('.verification-card') as HTMLElement;
    if (!cardElement || !containerRef.current) return;

    const containerWidth = containerRef.current.clientWidth;
    const gridUnit = (containerWidth - 24) / 12;
    const currentCols = cardsWidth[cardId] || 4;

    resizeStartRef.current = {
      cardId,
      startWidthPx: e.clientX,
      startCols: currentCols,
      gridUnitPx: gridUnit > 0 ? gridUnit : 80
    };

    window.addEventListener('mousemove', handleResizeMouseMove);
    window.addEventListener('mouseup', handleResizeMouseUp);
  };

  const handleResizeMouseMove = (e: MouseEvent) => {
    if (!resizeStartRef.current) return;
    const { cardId, startWidthPx, startCols, gridUnitPx } = resizeStartRef.current;
    
    const deltaX = e.clientX - startWidthPx;
    const deltaCols = Math.round(deltaX / gridUnitPx);
    let newCols = startCols + deltaCols;

    newCols = Math.max(2, Math.min(12, newCols));

    setCardsWidth(prev => ({
      ...prev,
      [cardId]: newCols
    }));
  };

  const handleResizeMouseUp = () => {
    window.removeEventListener('mousemove', handleResizeMouseMove);
    window.removeEventListener('mouseup', handleResizeMouseUp);
    setIsResizing(false);

    if (resizeStartRef.current) {
      const currentWidths = { ...cardsWidth };
      localStorage.setItem('secondary_verification_cards_widths', JSON.stringify(currentWidths));
    }
    resizeStartRef.current = null;
  };

  // 4. Navigation handler
  const handleVerifyJump = (card: VerificationCard) => {
    const payload = card.getPayload(params);
    if (card.id === 'stress_capacitor' || card.id === 'life_capacitor') {
      localStorage.setItem('target_dclink_capacitor_life_data', JSON.stringify(payload));
    } else if (card.id === 'stress_inductor' || card.id === 'life_inductor') {
      localStorage.setItem('target_mag_inductor_data', JSON.stringify(payload));
    } else if (card.id === 'stress_lc') {
      localStorage.setItem('target_filter_passive_data', JSON.stringify(payload));
    } else if (card.id === 'life_transformer') {
      localStorage.setItem('target_mag_transformer_data', JSON.stringify(payload));
    } else if (card.id === 'mosfet_miller' || card.id === 'dead_time') {
      localStorage.setItem('target_gate_drive_miller_data', JSON.stringify(payload));
    } else if (card.id === 'transient_tj') {
      localStorage.setItem('target_heatsink_thermal_data', JSON.stringify(payload));
    } else {
      localStorage.setItem(`target_${card.targetModule}_data`, JSON.stringify(payload));
    }
    setActiveModule?.(card.targetModule);
  };

  // Zone Section Renderer
  const renderZoneSection = (
    title: string,
    zoneKey: 'stress' | 'physics' | 'thermal' | 'control' | 'safety',
    zoneColor: string,
    icon: React.ReactNode
  ) => {
    const zoneCards = cards.filter(c => c.zone === zoneKey);
    if (zoneCards.length === 0) return null;

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <div className={`${zoneColor} shrink-0`}>{icon}</div>
          <span className="text-xs font-bold text-slate-200">{title}</span>
          <span className="text-[10px] text-slate-400 font-mono">({zoneCards.length} items)</span>
        </div>

        <div className="grid grid-cols-12 gap-4">
          {zoneCards.map(card => {
            const cols = cardsWidth[card.id] || 4;
            const colSpanClass = {
              2: 'col-span-2',
              3: 'col-span-3',
              4: 'col-span-4',
              5: 'col-span-5',
              6: 'col-span-6',
              7: 'col-span-7',
              8: 'col-span-8',
              9: 'col-span-9',
              10: 'col-span-10',
              11: 'col-span-11',
              12: 'col-span-12'
            }[cols] || 'col-span-4';

            return (
              <Card 
                key={card.id}
                draggable
                onDragStart={(e) => handleDragStart(e, card.id)}
                onDragOver={(e) => handleDragOver(e, card.id)}
                onDragEnd={handleDragEnd}
                className={`verification-card ${colSpanClass} relative group bg-slate-900/40 border border-slate-850 hover:border-slate-700/80 shadow-md hover:shadow-lg transition-all select-none duration-150 ${draggedCardId === card.id ? 'opacity-30 border-cyan-500 scale-[0.98]' : ''}`}
              >
                {/* Drag handle */}
                <div className="absolute left-2 top-2 opacity-0 group-hover:opacity-100 cursor-grab active:cursor-grabbing text-slate-400 transition-opacity p-0.5 rounded hover:bg-slate-800/80">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                    <circle cx="2" cy="2" r="1"/>
                    <circle cx="2" cy="5" r="1"/>
                    <circle cx="2" cy="8" r="1"/>
                    <circle cx="5" cy="2" r="1"/>
                    <circle cx="5" cy="5" r="1"/>
                    <circle cx="5" cy="8" r="1"/>
                    <circle cx="8" cy="2" r="1"/>
                    <circle cx="8" cy="5" r="1"/>
                    <circle cx="8" cy="8" r="1"/>
                  </svg>
                </div>

                {/* Grid width indicator */}
                <div className="absolute right-3 top-2.5 text-[8px] font-mono text-slate-400 group-hover:opacity-100 opacity-0 pointer-events-none transition-opacity">
                  {cols}/12 cols
                </div>

                <CardHeader className="p-3 pb-1.5 flex flex-row items-center justify-between mt-2.5">
                  <CardTitle className="text-[11px] font-bold text-slate-200 border-l border-cyan-500 pl-1.5 truncate">
                    {card.title}
                  </CardTitle>
                </CardHeader>
                
                <CardContent className="p-3 pt-0 flex flex-col gap-2 relative">
                  <p className="text-[10px] text-slate-400 leading-relaxed min-h-[30px] line-clamp-2">
                    {card.description}
                  </p>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleVerifyJump(card)}
                    className="w-full text-[10px] h-7 cursor-pointer mt-1 border-slate-800 text-slate-200 hover:bg-slate-800 hover:text-slate-100"
                  >
                    <span>Start Verification</span>
                  </Button>
                </CardContent>

                {/* Right Edge Snap-to-Grid Resize Handle */}
                <div
                  onMouseDown={(e) => handleResizeMouseDown(e, card.id)}
                  className="absolute right-0 top-0 bottom-0 w-1.5 cursor-col-resize opacity-0 group-hover:opacity-100 bg-cyan-500/20 hover:bg-cyan-500/40 active:bg-cyan-500 border-r border-cyan-500/30 transition-all"
                  title="Drag to resize card width (Snap-to-Grid)"
                />
              </Card>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <Card className="bg-[#0b0f19]/30 border-slate-800/80 shadow-lg text-slate-200">
      <CardHeader className="p-5 pb-3 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <CardTitle className="text-xs font-bold text-white border-l-2 border-cyan-500 pl-2 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <span>Secondary Verification & Advanced Physical Co-Design Hub</span>
          </CardTitle>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            [Design Note] Basic sizing completes only the nominal parameters. Use the secondary workstations below to perform high-frequency magnetics, Miller dv/dt, Kelvin shunt sensing, and PCB safety spacing verification. Cards support drag-and-drop reordering and snap-to-grid edge resizing.
          </p>
        </div>
      </CardHeader>
      <CardContent className="p-5 space-y-6" ref={containerRef}>
        {renderZoneSection('1. Passive High-Frequency Electrical Stress', 'stress', 'text-cyan-400', <Zap className="w-4 h-4" />)}
        {renderZoneSection('2. Passive Magnetics & Capacitor Physical Lifetime', 'physics', 'text-emerald-400', <Layers className="w-4 h-4 font-mono" />)}
        {renderZoneSection('3. Active Semiconductor Drive Matching & Thermodynamics', 'thermal', 'text-rose-400', <Flame className="w-4 h-4" />)}
        {renderZoneSection('4. Digital Control Loop & Precision Signal Sensing', 'control', 'text-amber-400', <Cpu className="w-4 h-4" />)}
        {renderZoneSection('5. System Safety Protection & High-Current PCB/Busbar', 'safety', 'text-cyan-400', <ShieldAlert className="w-4 h-4" />)}
      </CardContent>
    </Card>
  );
}