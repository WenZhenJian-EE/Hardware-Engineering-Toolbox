# 01_Overall_Architecture_Evolution_and_User_Requirements_Specification

---

## 1. Executive Summary & User Requirements Panorama

### 1.1 Project Mission & Handover Objective
The **Hardware Engineering Toolbox (Desktop Hybrid Edition)** was conceptualized to address a critical inefficiency in power electronics and analog hardware engineering: fragmented design tools. Historically, engineers have relied on scattered Excel spreadsheets, unversioned Mathcad workbooks, isolated SPICE scripts, and vendor-specific calculators.

The ultimate user objective for this phase is **Code Freeze and Open-Source Readiness**:
1. **Zero Half-Finished Residues**: Every visible module must be 100% operational with rigorous mathematical and physical solvers. Half-finished or stub modules must be completely excised.
2. **Open-Source Handover Standard**: Clean architecture, self-documenting code, exhaustive automated unit test coverage (217 Pytest cases), and zero console warnings/errors.
3. **Bilingual Accessibility**: Instant one-click English/Chinese switching to ensure frictionless adoption by international hardware engineers and open-source contributors.
4. **Single Portable Executable**: Standalone Windows binary (`Hardware_Engineering_Toolbox.exe`) that executes out-of-the-box without requiring local Python or Node.js runtimes.

---

## 2. Hybrid Desktop Architectural Stack

The platform employs a decoupled, multi-tier hybrid architecture balancing high-performance scientific computation with modern reactive UI capabilities:

```
+-------------------------------------------------------------------------+
|                  Electron Host Shell (Chromium 124 / Node 20)          |
|  - Process lifecycle management & dynamic port assignment (8000+ / 5173)|
|  - Standalone single-instance windowing with hardware acceleration      |
+------------------------------------+------------------------------------+
                                     | Local IPC & TCP Loopback
+------------------------------------v------------------------------------+
|                Frontend Presentation Tier (React 19 + Vite 6)           |
|  - UI Component Library: Lucide Icons, Radix UI Primitives, TailwindCSS|
|  - Responsive Data Grid: DragDeck layout engine with persistency       |
|  - Dynamic Visualizations: Apache ECharts & Interactive SVG Sandboxes  |
|  - Internationalization: Zero-overhead I18n Context with Alt+L shortcut |
|  - State Synchronization: TabHistory transactional stack & undo/redo   |
+------------------------------------+------------------------------------+
                                     | HTTP REST API (JSON / Localhost)
+------------------------------------v------------------------------------+
|               Backend Scientific Engine (Python 3.11 + FastAPI)         |
|  - Mathematical Modeling: NumPy, SciPy, Symbolic Derivations           |
|  - Standards Compliance: IEC 60664-1, IEC 62368-1, IPC-2152, iGSE      |
|  - Hardware Database: Embedded SQLite (switches, diodes, magnetic cores)|
|  - Parent Process Suicide Guard: Stdin pipe EOF watchdog thread         |
+-------------------------------------------------------------------------+
```

### 2.1 Backend Daemon Lifecycle & Zombie Process Prevention
To eliminate background zombie processes when the Electron shell is closed or force-terminated by Windows Task Manager, the FastAPI backend implements an active stdin monitor thread (`start_stdin_monitor`):

```python
def start_stdin_monitor():
    if "pytest" in sys.modules or os.environ.get("DAEMON_MODE") == "1":
        return
        
    def monitor():
        try:
            # sys.stdin.read() blocks until EOF when standard input pipe is closed
            sys.stdin.read()
        except Exception:
            pass
        # Immediate process termination upon pipe closure
        os._exit(0)
        
    t = threading.Thread(target=monitor, name="ParentProcessMonitor", daemon=True)
    t.start()
```

---

## 3. The 40 Production Engineering Workstations

All 40 modules are categorized into 5 standardized hardware engineering domains:

### Category 1: ⚡ Power Co-Design
- **`buck` (Buck Synchronous Converter)**: Steady-state CCM/DCM analysis, output filter ripple stress, dynamic closed-loop Bode sweep, interactive schematic sandbox, and 20-item secondary verification hub.
- **`flyback` (Flyback Isolated Converter)**: AP-method core sizing, secondary synchronous rectifier conduction/reverse recovery losses, primary RCD clamp dissipation, closed-loop optocoupler-TL431 feedback, and secondary verification hub.

### Category 2: 🧲 Magnetics & Basics
- **`mag_inductor`**: Inductor core, air gap, Dowell high-frequency winding AC resistance factor $F_r$, and DC-bias soft saturation.
- **`mag_transformer`**: Integrated transformer sizing, AP method, leakage inductance estimation, and multi-winding interleaved window configurations.
- **`mag_core_loss`**: Core volumetric loss based on the Improved Generalized Steinmetz Equation (iGSE) under arbitrary non-sinusoidal waveforms.
- **`snubber`**: Turn-off ringing RC damping and flyback primary RCD snubber parameter synthesis.
- **`power_dclink`**: Interleaved DC-DC and 3-Phase SPWM/SVPWM inverter bus capacitor RMS ripple stress, thermal dissipation, and electrolytic capacitor Arrhenius operating lifetime.
- **`power_ac_3ph`**: 3-Phase Y-Delta impedance transformation, Clarke/Park ($\alpha\beta$ / $dq$) projections, and phase-locked loop (PLL) filter parameters.

### Category 3: 🔥 Power & Thermal
- **`power_foster_thermal`**: High-order Foster RC thermal network state-space transient junction temperature prediction.
- **`gate_drive_miller`**: SiC/GaN gate $dv/dt$ parasitic Miller turn-on threshold verification, dead-time dissipation, and ZVS criteria.
- **`heatsink`**: Natural and forced convection thermal resistance modeling, fin geometry fluid dynamics Reynolds calculation.
- **`ldo_thermal`**: LDO power dissipation, PCB copper polygon thermal spreading, and thermal shutdown margin.
- **`power_relay_driver`**: Dual-voltage pull-in/hold-in PWM drive circuit, coil dissipation, and ripple reduction.
- **`power_device`**: MOSFET/IGBT semiconductor conduction and switching loss model with device database integration.
- **`power_dpt`**: Double Pulse Test (DPT) timing synthesis, loop inductance extraction, and $E_{on}/E_{off}$ overlap verification.
- **`battery_pack`**: Lithium-ion series-parallel sizing, passive balancing shunt resistor sizing, and thermal rise estimation.
- **`power_budget`**: Converter-level multi-subsystem loss breakdown and full-load efficiency profiling.

### Category 4: 📈 Loop & Signals
- **`power_waveform_rms`**: Analytical RMS, average, and harmonic distortion for non-sinusoidal waveforms (trapezoidal, phase-fired sine, triangular).
- **`loop_compensation`**: Type II / Type III compensator design, pole-zero placement, crossover frequency optimization, and phase margin targeting.
- **`digital_pid`**: S-domain to Z-domain discretization (Tustin/Bilinear), Butterworth digital filter synthesis, and PID difference equations.
- **`filter_passive`**: Active/passive analog filters, common-mode/differential-mode EMI filters, and Middlebrook impedance stability ratio checking ($Z_{out} \ll Z_{in}$).
- **`emc_toolbox`**: RF unit conversions, insertion loss, aperture shielding effectiveness, and damping snubber sizing.
- **`load_transient`**: Voltage overshoot/undershoot under sudden load steps, minimum output capacitance requirement, and control loop bandwidth boundaries.
- **`adc_conditioning`**: Front-end anti-aliasing RC filter, op-amp impedance matching, channel noise calculation, and two-point calibration.
- **`opamp`**: Inverting/non-inverting op-amp DC error budgets, differential resistor matching CMRR analysis, and Schmitt trigger hysteresis thresholds.
- **`current_shunt`**: Current shunt resistor self-heating drift, non-Kelvin routing error, and current transformer (CT) burden resistor saturation.
- **`ntc`**: Steinhart-Hart and Beta parameter curve fitting, linearization circuitry, and automatic C-code lookup table generator.
- **`pwm_mcu_ic`**: PWM timer resolution, dead-time register decoding, DAC RC low-pass ripple sizing, and UC3842 oscillator timing.
- **`interface_level_shift`**: $I^2C$ bus pull-up sizing, RS-485 / CAN bus termination characteristic impedance matching.
- **`comm_powercomm`**: SCI serial bit-field parser, Modbus RTU frame generator, CRC-16 calculation, and IEEE 754 floating-point encoder/decoder.

### Category 5: 🛡️ Passives & Safety
- **`creepage`**: IEC 60664-1 & IEC 62368 insulation coordination, clearance/creepage distance sizing with altitude barometric correction factors.
- **`tvs_zener`**: Zener power dissipation and TVS transient pulse clamp peak power and junction temperature margin.
- **`input_protection`**: Inrush surge limiting NTC sizing, fuse $I^2t$ let-through energy rating, and X-capacitor safety discharge resistors.
- **`pcb_toolbox`**: IPC-2152 trace temperature rise, via parasitic inductance/capacitance, and microstrip/coplanar waveguide characteristic impedance.
- **`wire_copper_bar`**: High-frequency Litz wire skin and proximity effect losses, AWG circular conductor ampacity, and heavy copper busbar thermal rise.
- **`rc_charge`**: Bus pre-charge inrush limiting, soft-start RC timing, active bus discharge, and safety decay time.
- **`capacitor_toolbox`**: Electrolytic capacitor Arrhenius lifetime scaling, multi-frequency ripple current root-sum-square RMS summation, and MLCC DC bias capacitance derating.
- **`resistor_toolbox`**: Resistor divider networks, Worst-Case Analysis (WCA) tolerance stacking, standard E96/E24 decade approximations, and pulse energy limits.
- **`lc_basics`**: Time-domain second-order step response, reactive impedance, and LC natural resonance calculations.
- **`db_manager`**: Local SQLite management of semiconductors, diodes, core materials, and core geometries.

---

## 4. Verification and Release Gateways

Prior to open-source tagging, the entire project must pass three mandatory gateways:
1. **Algorithmic Correctness**: `python -m pytest` executes 217 automated unit tests with 100% pass rate.
2. **Frontend Type Safety**: `npm run build` completes with zero TypeScript errors.
3. **Browser Automation End-to-End**: Real-time validation via Chrome DevTools protocol with zero console warnings and complete reactive rendering across all dynamic ECharts instances.
