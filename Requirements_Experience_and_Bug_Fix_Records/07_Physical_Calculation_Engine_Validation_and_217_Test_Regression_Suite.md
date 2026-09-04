# 07_Physical_Calculation_Engine_Validation_and_217_Test_Regression_Suite

---

## 1. Mathematical Rigor & Physical Modeling Principles

The **Hardware Engineering Toolbox** differentiates itself from superficial web calculators by enforcing 100% white-box physical derivations based on established industrial standards and academic literature:
- **IEC 60664-1 & IEC 62368-1**: Insulation coordination, clearance and creepage distance sizing with altitude barometric correction factors ($k_d$).
- **IPC-2152**: Standard for Determining Current-Carrying Capacity in Printed Board Design (trace thermal rise modeling).
- **Dowell Equation**: High-frequency winding AC-to-DC resistance ratio factor $F_r$ taking into account skin and proximity effects.
- **Improved Generalized Steinmetz Equation (iGSE)**: Volumetric core loss prediction under non-sinusoidal excitation:
  $$P_v = \frac{1}{T} \int_0^T k_i \left| \frac{dB}{dt} \right|^\alpha (\Delta B)^{\beta - \alpha} dt$$
- **Middlebrook Stability Criterion**: Subsystem impedance interaction ratio $T_m(s) = Z_{out}(s) / Z_{in}(s) \ll 1$ to guarantee cascade converter stability.

---

## 2. The 217 Pytest Test Suite Architecture

The backend test suite is located in `Source_Code/backend/` and consists of 217 automated unit and integration tests executing across 16 parallel workers via `pytest-xdist`.

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\Data\Agent\MyDev\Hardware-Engineering-Toolbox-Desktop\Source_Code
configfile: pytest.ini
plugins: anyio-4.13.0, xdist-3.8.0
16 workers [217 items]
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
.                                                                        [100%]
====================== 217 passed, 16 warnings in 3.94s =======================
```

### 2.1 Test Domain Breakdown

| Engineering Test Domain | Test Modules | Coverage Highlights |
| :--- | :--- | :--- |
| **Magnetics & Transformers** | `test_mag_inductor.py`, `test_mag_core_loss.py` | Inductor $A_L$, air gap length $l_g$, fringing flux factor $F$, Dowell factor $F_r$, iGSE core loss integrals. |
| **Switching & Power Devices** | `test_power_device.py`, `test_gate_drive.py`, `test_dpt.py` | MOSFET $R_{ds(on)}(T_j)$, IGBT $V_{ce(sat)}$, turn-on/off overlap energy ($E_{on}, E_{off}$), gate Miller plateau charge. |
| **Thermal Networks** | `test_transient_thermal.py`, `test_multiphysics_thermal.py` | 4th-order Foster RC network state-space differential equations, transient pulse thermal impedance $Z_{th(j-a)}(t)$. |
| **Control & Signals** | `test_loop_compensation.py`, `test_digital_pid.py`, `test_opamp.py` | Type II/III transfer function poles/zeros, Tustin bilinear transformation $s \to \frac{2}{T}\frac{z-1}{z+1}$, Bode gain/phase margins. |
| **Stability & Filters** | `test_cascade_stability.py`, `test_emc_toolbox.py` | Middlebrook source-load impedance ratios, differential-mode/common-mode filter attenuation. |
| **Passives & Safety** | `test_safety_spacing.py`, `test_wire_copper_bar.py`, `test_dclink_life.py` | Pollution degrees 1–3, material group I–IIIb, altitude factor $k_d$, Arrhenius capacitor lifespan $L = L_0 \cdot 2^{\frac{T_{max} - T_h}{10}}$. |
| **Database CRUD** | `test_database.py`, `test_project_state.py` | SQLite schema migration, semiconductor parameter persistence, project save/load JSON serialization. |

---

## 3. Regression Execution Commands

To execute the test suite across the entire backend:
```bash
# Move to backend directory:
cd Source_Code/backend

# Standard execution:
python -m pytest

# Parallel multi-core execution (fastest):
python -m pytest -n auto
```
All 217 tests must pass with 100% success rate before any code merge or binary packaging.
