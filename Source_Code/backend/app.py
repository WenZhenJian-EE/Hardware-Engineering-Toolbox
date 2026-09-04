"""
Hardware Engineering Toolbox - Backend API Service
===================================================
Author: WenZhenJian-EE (https://github.com/WenZhenJian-EE)
License: MIT

This backend service provides calculation endpoints for the
Hardware Engineering Toolbox desktop application (power converters,
magnetics, thermal analysis, loop compensation, and passive components).

Open-sourced under the MIT License for community use and maintenance.
"""

import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Ensure 'backend', 'database', and 'formula' are resolvable in both PyInstaller and dev mode
import types
if 'backend' not in sys.modules:
    _backend_mod = types.ModuleType('backend')
    _backend_mod.__path__ = [_current_dir]
    sys.modules['backend'] = _backend_mod

# Explicitly load formula.py if needed
if 'formula' not in sys.modules:
    for candidate in [os.path.join(_current_dir, 'formula.py'), os.path.join(_parent_dir, 'backend', 'formula.py')]:
        if os.path.isfile(candidate):
            import importlib.util
            spec = importlib.util.spec_from_file_location("formula", candidate)
            if spec and spec.loader:
                _formula_mod = importlib.util.module_from_spec(spec)
                sys.modules["formula"] = _formula_mod
                sys.modules["backend.formula"] = _formula_mod
                spec.loader.exec_module(_formula_mod)
            break
else:
    sys.modules["backend.formula"] = sys.modules["formula"]

# Explicitly load database.py to resolve collision with directory 'database'
if 'database' not in sys.modules or not hasattr(sys.modules['database'], 'ComponentDatabase'):
    for candidate in [os.path.join(_current_dir, 'database.py'), os.path.join(_parent_dir, 'backend', 'database.py')]:
        if os.path.isfile(candidate):
            import importlib.util
            spec = importlib.util.spec_from_file_location("database", candidate)
            if spec and spec.loader:
                _db_mod = importlib.util.module_from_spec(spec)
                sys.modules["database"] = _db_mod
                sys.modules["backend.database"] = _db_mod
                spec.loader.exec_module(_db_mod)
            break

import math
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.formula import (
    calc_t_type_converter, simulate_t_type_waveforms, calc_multi_output_aux,
    calc_buck_converter, simulate_buck_time_domain, simulate_buck_bode, calc_buck_losses,
    calculate_heatsink_rth, calculate_forced_air_cooling,
    calculate_enclosure_temp_rise, calculate_transient_overload,
    calculate_system_airflow,
    calculate_fuse_i2t, calculate_ntc_inrush, calculate_xcap_discharge,
    calculate_zener_regulator, calculate_tvs_clamping,
    calc_flyback_converter, simulate_flyback_time_domain, simulate_flyback_bode,
    calc_acf_converter, simulate_acf_time_domain, simulate_acf_bode,
    calc_forward_converter, simulate_forward_time_domain, simulate_forward_bode,
    calc_interleaved_sbb, simulate_sbb_waveforms,
    calc_interleaved_boost_pfc, simulate_pfc_waveforms,
    calc_totem_pole_pfc, simulate_totem_pole_waveforms,
    calc_vienna_pfc, simulate_vienna_waveforms,
    calc_afe_rectifier, simulate_afe_waveforms,
    calc_dab_converter, solve_dab_time_domain, solve_optimal_phase_shift,
    calc_cllc_converter, calc_dab_cllc_magnetic_integration,
    calc_snubber_overshoot_efficiency, calc_snubber_measure, calc_rcd_parameters,
    calc_cascade_impedance_stability,
    calc_psfb_converter, simulate_psfb_time_domain, simulate_psfb_bode,
    calc_trap_waveform, calc_dcm_waveform, calc_rect_waveforms, calc_sine_waveforms,
    calc_decouple_waveform, calc_ripple_waveform,
    calculate_rc_economizer, calculate_pwm_holding,
    calculate_ldo_thermal, estimate_pcb_copper_rth,
    calculate_type2_loop, simulate_type2_loop_bode, simulate_type2_loop_step,
    calculate_type3_loop, simulate_type3_loop_bode, simulate_type3_loop_step,
    calculate_tl431_loop, simulate_tl431_loop_bode, simulate_tl431_loop_step,
    calculate_opto_dc_bias, calculate_hv_divider,
    discretize_type2, discretize_type3, generate_c_code,
    calc_digital_pid_design, simulate_digital_pid_bode, simulate_digital_pid_step,
    calc_s2z_conversion, calc_adc_filter_design,
    generate_digital_filter_c_code, generate_pid_c_code,
    calc_passive_filter_design, simulate_passive_filter_bode,
    calc_active_filter_design, calc_cmc_saturation,
    calc_spwm_filter, calc_bead_damping,
    calc_input_damping_stability, simulate_pdn_anti_resonance,
    STANDARDS_DB, get_emc_limit_at_freq, calc_emc_unit_conversion,
    calc_emc_filter_attenuation, calc_emc_radiated_wavelength,
    calc_emc_radiated_field_strength, calc_emc_filter_sizing,
    calc_emc_conducted_fix, calc_emc_filter_bode,
    calc_load_transient, calc_adc_rc_filter, calc_adc_sampling_budget,
    calc_adc_afe_reconstruct, calc_adc_two_point_fit,
    calc_basic_opamp, calc_diff_opamp, calc_summing_opamp,
    calc_hysteresis_comparator, calc_error_budget, calc_opamp_selection,
    calc_ct_design, calc_shunt_error,
    calc_ntc_single_point, calc_ntc_table_gen, calc_ntc_steinhart_hart,
    calc_ntc_sh_verify, calc_ntc_opt_divider,
    calc_pwm_dac_filter, calc_mcu_timer_registers, calc_zvs_deadtime_opt, calc_pwm_ic_frequency,
    calc_i2c_pullup, calc_interface_termination,
    calc_pcb_trace_capacity, calc_pcb_via_analysis, calc_pcb_impedance_analysis,
    calc_wire_litz_design, calc_wire_awg_capacity, calc_busbar_capacity,
    calc_rc_standard, calc_rc_dc_precharge, calc_rc_ac_precharge,
    calc_rc_bus_discharge, calc_rc_xcap_discharge,
    calc_capacitor_lifetime, calc_capacitor_rms_sum, calc_capacitor_topology_rms,
    calc_capacitor_mlcc_bias, calc_capacitor_holdup,
    calc_resistor_divider_theory, calc_resistor_divider_find, calc_resistor_wca,
    calc_resistor_combiner, calc_resistor_standard_find, calc_resistor_pulse_withstand,
    calc_lc_time_domain, calc_lc_reactance,
    calculate_buck_ccm, calculate_gap_and_fringing, calculate_air_core_inductor,
    calculate_air_core_turns, calculate_planar_inductor, calculate_dc_bias_curve,
    calculate_skin_depth, calculate_dowell_factor, optimize_litz_wire,
    calculate_coupled_inductor,
    calculate_transformer_ap, calculate_transformer_fill, calculate_transformer_core_loss,
    calculate_transformer_leakage, calculate_steinmetz_fit, calculate_llc_gain_points,
    calculate_psfb_zvs_check, calculate_pfc_inductor_sizing,
    calc_llc_magnetic_integration, calc_llc_multi_out, calc_llc_vco_loop, design_llc_tank,
    calculate_llc_gain
)
from database import ComponentDatabase

app = FastAPI(title="Hardware Engineering Toolbox Web API")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = ComponentDatabase()

import math
from typing import Any
from fastapi.responses import JSONResponse

def clean_dict(d: Any) -> Any:
    if isinstance(d, dict):
        return {k: clean_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_dict(v) for v in d]
    elif isinstance(d, float):
        if math.isnan(d) or math.isinf(d):
            return 0.0
        return d
    else:
        return d

class CleanJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return super().render(clean_dict(content))

app.router.default_response_class = CleanJSONResponse


import threading
import time
import os
import signal

last_heartbeat = time.time()

@app.post("/api/heartbeat")
def heartbeat():
    global last_heartbeat
    last_heartbeat = time.time()
    return {"status": "ok"}

def monitor_heartbeat():
    global last_heartbeat
    # Buffer time for startup loading (15 seconds)
    time.sleep(15)
    while True:
        time.sleep(2)
        if time.time() - last_heartbeat > 18.0:
            print("[System] No heartbeat detected for 18 seconds. Shutting down...")
            os.kill(os.getpid(), signal.SIGTERM)
            break

heartbeat_thread = threading.Thread(target=monitor_heartbeat, daemon=True)
heartbeat_thread.start()


# ------------------------------------------------------------------
# Component Database CRUD API
# ------------------------------------------------------------------

class ManufacturerModel(BaseModel):
    name: str
    url: Optional[str] = None

class SwitchDeviceModel(BaseModel):
    name: str
    manufacturer_id: int
    type: str
    v_ds_max: float
    i_d_max: float
    r_ds_on: float
    q_g: Optional[float] = None
    c_oss: Optional[float] = None
    package: Optional[str] = None
    r_jc: Optional[float] = None

class DiodeDeviceModel(BaseModel):
    name: str
    manufacturer_id: int
    type: str
    v_r_max: float
    i_f_max: float
    v_f: float
    package: Optional[str] = None
    r_jc: Optional[float] = None

class MaterialModel(BaseModel):
    name: str
    type: str
    permeability: float
    b_sat_25: Optional[float] = None
    b_sat_100: Optional[float] = None
    steinmetz_cm_25: Optional[float] = None
    steinmetz_x_25: Optional[float] = None
    steinmetz_y_25: Optional[float] = None
    steinmetz_cm_100: Optional[float] = None
    steinmetz_x_100: Optional[float] = None
    steinmetz_y_100: Optional[float] = None

class CoreModel(BaseModel):
    name: str
    shape: str
    material_id: int
    ae: float
    le: float
    ve: float
    wa: float
    al: Optional[float] = None

class CapacitorDeviceModel(BaseModel):
    name: str
    manufacturer_id: int
    type: str
    capacitance: float
    voltage_rating: float
    esr: Optional[float] = None
    esl: Optional[float] = None
    ripple_current: Optional[float] = None
    temp_max: Optional[float] = None
    lifetime_hours: Optional[int] = None

class ZenerDeviceModel(BaseModel):
    name: str
    manufacturer_id: int
    vz: float
    izt: Optional[float] = 5.0
    izk: Optional[float] = 1.0
    zzt: Optional[float] = 10.0
    p_d: Optional[float] = 1.0
    package: Optional[str] = ""

class TvsDeviceModel(BaseModel):
    name: str
    manufacturer_id: int
    vrwm: float
    vbr: float
    vc: float
    ipp: float
    pppm: float
    package: Optional[str] = ""

class FuseDeviceModel(BaseModel):
    name: str
    manufacturer_id: int
    i_rated: float
    v_rated: float
    i2t: float
    package: Optional[str] = ""

class NtcDeviceModel(BaseModel):
    name: str
    manufacturer_id: int
    r25: float
    i_max: float
    joule_rating: float
    dissipation: float
    package: Optional[str] = ""

class ConfirmImportRequest(BaseModel):
    category: str  # 'switch' | 'diode' | 'zener' | 'tvs' | 'capacitor' | 'fuse' | 'ntc'
    pdf_filename: str
    name: str
    manufacturer: str  # Manufacturer name string
    package: Optional[str] = ""
    # Switches
    type: Optional[str] = "Si"
    v_ds_max: Optional[float] = 0.0
    i_d_max: Optional[float] = 0.0
    r_ds_on: Optional[float] = 0.0
    q_g: Optional[float] = 0.0
    c_oss: Optional[float] = 0.0
    r_jc: Optional[float] = 0.0
    # Diodes
    v_r_max: Optional[float] = 0.0
    i_f_max: Optional[float] = 0.0
    v_f: Optional[float] = 0.0
    # Zener
    vz: Optional[float] = 0.0
    izt: Optional[float] = 0.0
    izk: Optional[float] = 0.0
    zzt: Optional[float] = 0.0
    p_d: Optional[float] = 0.0
    # TVS
    vrwm: Optional[float] = 0.0
    vbr: Optional[float] = 0.0
    vc: Optional[float] = 0.0
    ipp: Optional[float] = 0.0
    pppm: Optional[float] = 0.0
    # Fuse
    i_rated: Optional[float] = 0.0
    v_rated: Optional[float] = 0.0
    i2t: Optional[float] = 0.0
    # NTC
    r25: Optional[float] = 0.0
    i_max: Optional[float] = 0.0
    joule_rating: Optional[float] = 0.0
    dissipation: Optional[float] = 0.0
    # Capacitors
    capacitance: Optional[float] = 0.0
    voltage_rating: Optional[float] = 0.0
    esr: Optional[float] = 0.0
    ripple_current: Optional[float] = 0.0
    temp_max: Optional[float] = 0.0
    lifetime_hours: Optional[int] = 0


@app.get("/api/database/manufacturers")
def get_manufacturers():
    return db.list_manufacturers()

@app.post("/api/database/manufacturers")
def add_manufacturer(req: ManufacturerModel):
    res_id = db.add_manufacturer(req.name, req.url)
    if res_id is None:
        raise HTTPException(status_code=400, detail="Failed to add manufacturer or manufacturer already exists.")
    return {"id": res_id, "status": "success"}

@app.get("/api/database/switches")
def get_switches():
    return db.list_switches_full()

@app.post("/api/database/switches")
def add_switch(req: SwitchDeviceModel):
    success = db.add_switch(
        name=req.name,
        manufacturer_id=req.manufacturer_id,
        type_=req.type,
        v_ds_max=req.v_ds_max,
        i_d_max=req.i_d_max,
        r_ds_on=req.r_ds_on,
        q_g=req.q_g,
        c_oss=req.c_oss,
        package=req.package,
        r_jc=req.r_jc
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add switch.")
    return {"status": "success"}

@app.delete("/api/database/switches/{name}")
def delete_switch(name: str):
    deleted = db.delete_switch(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Switch '{name}' not found.")
    return {"status": "success"}

@app.get("/api/database/diodes")
def get_diodes():
    return db.list_diodes_full()

@app.post("/api/database/diodes")
def add_diode(req: DiodeDeviceModel):
    success = db.add_diode(
        name=req.name,
        manufacturer_id=req.manufacturer_id,
        type_=req.type,
        v_r_max=req.v_r_max,
        i_f_max=req.i_f_max,
        v_f=req.v_f,
        package=req.package,
        r_jc=req.r_jc
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add diode.")
    return {"status": "success"}

@app.delete("/api/database/diodes/{name}")
def delete_diode(name: str):
    deleted = db.delete_diode(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Diode '{name}' not found.")
    return {"status": "success"}

@app.get("/api/database/materials")
def get_materials():
    return db.list_materials()

@app.post("/api/database/materials")
def add_material(req: MaterialModel):
    success = db.add_material(
        name=req.name,
        type_=req.type,
        permeability=req.permeability,
        b_sat_25=req.b_sat_25,
        b_sat_100=req.b_sat_100,
        steinmetz_cm_25=req.steinmetz_cm_25,
        steinmetz_x_25=req.steinmetz_x_25,
        steinmetz_y_25=req.steinmetz_y_25,
        steinmetz_cm_100=req.steinmetz_cm_100,
        steinmetz_x_100=req.steinmetz_x_100,
        steinmetz_y_100=req.steinmetz_y_100
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add material.")
    return {"status": "success"}

@app.get("/api/database/cores")
def get_cores():
    return db.list_cores_full()

@app.post("/api/database/cores")
def add_core(req: CoreModel):
    success = db.add_core(
        name=req.name,
        shape=req.shape,
        material_id=req.material_id,
        ae=req.ae,
        le=req.le,
        ve=req.ve,
        wa=req.wa,
        al=req.al
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add core.")
    return {"status": "success"}

@app.delete("/api/database/cores/{name}")
def delete_core(name: str):
    deleted = db.delete_core(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Core '{name}' not found.")
    return {"status": "success"}

@app.delete("/api/database/materials/{name}")
def delete_material(name: str):
    deleted = db.delete_material(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Material '{name}' not found.")
    return {"status": "success"}

@app.get("/api/database/capacitors")
def get_capacitors():
    return db.list_capacitors_full()

@app.post("/api/database/capacitors")
def add_capacitor(req: CapacitorDeviceModel):
    success = db.add_capacitor(
        name=req.name,
        manufacturer_id=req.manufacturer_id,
        type_=req.type,
        capacitance=req.capacitance,
        voltage_rating=req.voltage_rating,
        esr=req.esr,
        esl=req.esl,
        ripple_current=req.ripple_current,
        temp_max=req.temp_max,
        lifetime_hours=req.lifetime_hours
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add capacitor.")
    return {"status": "success"}

@app.delete("/api/database/capacitors/{name}")
def delete_capacitor(name: str):
    deleted = db.delete_capacitor(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Capacitor '{name}' not found.")
    return {"status": "success"}


# === Zener Diodes REST APIs ===
@app.get("/api/database/zeners")
def get_zeners():
    return db.list_zeners_full()

@app.post("/api/database/zeners")
def add_zener(req: ZenerDeviceModel):
    success = db.add_zener(
        name=req.name,
        manufacturer_id=req.manufacturer_id,
        vz=req.vz,
        izt=req.izt,
        izk=req.izk,
        zzt=req.zzt,
        p_d=req.p_d,
        package=req.package
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add Zener diode.")
    return {"status": "success"}

@app.delete("/api/database/zeners/{name}")
def delete_zener(name: str):
    deleted = db.delete_zener(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Zener diode '{name}' not found.")
    return {"status": "success"}

# === TVS Diodes REST APIs ===
@app.get("/api/database/tvs")
def get_tvs_diodes():
    return db.list_tvs_full()

@app.post("/api/database/tvs")
def add_tvs_diode(req: TvsDeviceModel):
    success = db.add_tvs(
        name=req.name,
        manufacturer_id=req.manufacturer_id,
        vrwm=req.vrwm,
        vbr=req.vbr,
        vc=req.vc,
        ipp=req.ipp,
        pppm=req.pppm,
        package=req.package
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add TVS diode.")
    return {"status": "success"}

@app.delete("/api/database/tvs/{name}")
def delete_tvs_diode(name: str):
    deleted = db.delete_tvs(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"TVS diode '{name}' not found.")
    return {"status": "success"}

# === Fuses REST APIs ===
@app.get("/api/database/fuses")
def get_fuses():
    return db.list_fuses_full()

@app.post("/api/database/fuses")
def add_fuse_api(req: FuseDeviceModel):
    success = db.add_fuse(
        name=req.name,
        manufacturer_id=req.manufacturer_id,
        i_rated=req.i_rated,
        v_rated=req.v_rated,
        i2t=req.i2t,
        package=req.package
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add fuse.")
    return {"status": "success"}

@app.delete("/api/database/fuses/{name}")
def delete_fuse_api(name: str):
    deleted = db.delete_fuse(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Fuse '{name}' not found.")
    return {"status": "success"}

# === NTC Resistors REST APIs ===
@app.get("/api/database/ntcs")
def get_ntcs():
    return db.list_ntc_full()

@app.post("/api/database/ntcs")
def add_ntc_api(req: NtcDeviceModel):
    success = db.add_ntc(
        name=req.name,
        manufacturer_id=req.manufacturer_id,
        r25=req.r25,
        i_max=req.i_max,
        joule_rating=req.joule_rating,
        dissipation=req.dissipation,
        package=req.package
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add NTC resistor.")
    return {"status": "success"}

@app.delete("/api/database/ntcs/{name}")
def delete_ntc_api(name: str):
    deleted = db.delete_ntc(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"NTC resistor '{name}' not found.")
    return {"status": "success"}


# === AI PDF Auto-Import Confirmation & File Purging Endpoint ===
@app.post("/api/db/confirm_import")
@app.post("/api/database/confirm_import")
def confirm_import(req: ConfirmImportRequest):
    import os
    
    # 1. 查找或自动创建厂商 Manufacturer
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM manufacturers WHERE name = ?;", (req.manufacturer,))
        m_row = cursor.fetchone()
        if m_row:
            mfg_id = m_row["id"]
        else:
            cursor.execute("INSERT INTO manufacturers (name, url) VALUES (?, ?);", (req.manufacturer, "https://www.google.com/search?q=" + req.manufacturer))
            conn.commit()
            mfg_id = cursor.lastrowid
    except Exception as e:
        print(f"[Confirm Import] Find manufacturer error: {e}")
        mfg_id = 1  # fallback to first manufacturer
    finally:
        conn.close()

    # 2. 插入元器件到对应数据表中
    category = req.category
    success = False
    
    if category == "switch":
        success = db.add_switch(
            name=req.name,
            manufacturer_id=mfg_id,
            type_=req.type,
            v_ds_max=req.v_ds_max,
            i_d_max=req.i_d_max,
            r_ds_on=req.r_ds_on,
            q_g=req.q_g,
            c_oss=req.c_oss,
            package=req.package,
            r_jc=req.r_jc
        )
    elif category == "diode":
        success = db.add_diode(
            name=req.name,
            manufacturer_id=mfg_id,
            type_=req.type,
            v_r_max=req.v_r_max,
            i_f_max=req.i_f_max,
            v_f=req.v_f,
            package=req.package,
            r_jc=req.r_jc
        )
    elif category == "zener":
        success = db.add_zener(
            name=req.name,
            manufacturer_id=mfg_id,
            vz=req.vz,
            izt=req.izt,
            izk=req.izk,
            zzt=req.zzt,
            p_d=req.p_d,
            package=req.package
        )
    elif category == "tvs":
        success = db.add_tvs(
            name=req.name,
            manufacturer_id=mfg_id,
            vrwm=req.vrwm,
            vbr=req.vbr,
            vc=req.vc,
            ipp=req.ipp,
            pppm=req.pppm,
            package=req.package
        )
    elif category == "fuse":
        success = db.add_fuse(
            name=req.name,
            manufacturer_id=mfg_id,
            i_rated=req.i_rated,
            v_rated=req.v_rated,
            i2t=req.i2t,
            package=req.package
        )
    elif category == "ntc":
        success = db.add_ntc(
            name=req.name,
            manufacturer_id=mfg_id,
            r25=req.r25,
            i_max=req.i_max,
            joule_rating=req.joule_rating,
            dissipation=req.dissipation,
            package=req.package
        )
    elif category == "capacitor":
        success = db.add_capacitor(
            name=req.name,
            manufacturer_id=mfg_id,
            type_=req.type or "Electrolytic",
            capacitance=req.capacitance,
            voltage_rating=req.voltage_rating,
            esr=req.esr,
            esl=0.0,
            ripple_current=req.ripple_current,
            temp_max=req.temp_max,
            lifetime_hours=req.lifetime_hours
        )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to insert validated component draft to SQLite database.")

    # 3. 物理移出/删除已导入的数据手册，保证 Datasheets_Import 目录清空
    current_dir = os.path.dirname(os.path.abspath(__file__))
    import_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "Datasheets_Import"))
    if not os.path.exists(import_dir):
        import_dir = os.path.abspath(os.path.join(current_dir, "Datasheets_Import"))
        
    safe_filename = os.path.basename(req.pdf_filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid path")
        
    abs_import_dir = os.path.abspath(import_dir)
    target_path = os.path.abspath(os.path.join(abs_import_dir, safe_filename))
    if not target_path.startswith(abs_import_dir):
        raise HTTPException(status_code=400, detail="Invalid path")

    if os.path.exists(target_path):
        try:
            os.remove(target_path)
            print(f"[API confirm_import] Purged {safe_filename} from Datasheets_Import.")
        except Exception as e:
            print(f"[API confirm_import] Failed to delete file {safe_filename}: {e}")
            
    return {"status": "success", "message": f"器件 '{req.name}' 校验并成功导入，对应手册已被物理删除。"}





class BuckCalcRequest(BaseModel):
    vin: float
    vout: float
    iout: float
    fsw_khz: float
    lir_pct: float = 30.0
    v_rip_pct: float = 1.0
    l_uh: Optional[float] = None
    c_uf: Optional[float] = None
    rc_esr_mohm: float = 20.0
    sw_rds_on_mohm: float = 80.0
    sw_times_ns: float = 60.0
    diode_vf_v: float = 0.8
    ind_dcr_mohm: float = 50.0
    diode_type: str = "schottky"
    diode_qrr_nc: float = 0.0
    sync_rds_on_mohm: float = 10.0
    sync_dead_time_ns: float = 50.0
    sync_body_vf_v: float = 0.8
    num_cycles: int = 3


class BuckMultiphysicsRequest(BaseModel):
    vin: float
    vout: float
    iout: float
    fsw_khz: float
    l_uh: float
    c_uf: float
    rc_esr_mohm: float = 30.0
    sw_rds_on_25c_mohm: float = 15.0
    sw_times_ns: float = 30.0
    sw_r_jc: float = 0.8
    sw_r_ca: float = 15.0
    diode_vf_25c_v: float = 0.8
    diode_r_jc: float = 1.2
    diode_r_ca: float = 20.0
    ind_dcr_25c_mohm: float = 10.0
    ind_r_th: float = 25.0
    t_ambient: float = 25.0


@app.post("/api/calculate/buck/multiphysics")
def calculate_buck_multiphysics(req: BuckMultiphysicsRequest):
    try:
        from backend.formula import calc_buck_multiphysics_co_simulation
        res = calc_buck_multiphysics_co_simulation(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            l_uh=req.l_uh,
            c_uf=req.c_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            sw_rds_on_25c_mohm=req.sw_rds_on_25c_mohm,
            sw_times_ns=req.sw_times_ns,
            sw_r_jc=req.sw_r_jc,
            sw_r_ca=req.sw_r_ca,
            diode_vf_25c_v=req.diode_vf_25c_v,
            diode_r_jc=req.diode_r_jc,
            diode_r_ca=req.diode_r_ca,
            ind_dcr_25c_mohm=req.ind_dcr_25c_mohm,
            ind_r_th=req.ind_r_th,
            t_ambient=req.t_ambient
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"多物理场迭代计算失败: {str(e)}")


class CascadeStabilityRequest(BaseModel):
    pfc_vbus: float = 400.0
    pfc_pout: float = 1000.0
    pfc_cout_uf: float = 220.0
    pfc_fc_hz: float = 10.0
    dcdc_cin_uf: float = 10.0
    dcdc_cin_esr_mohm: float = 50.0
    dcdc_fc_khz: float = 3.0


@app.post("/api/calculate/cascade/stability")
def calculate_cascade_stability_route(req: CascadeStabilityRequest):
    try:
        from backend.formula import calc_cascade_stability
        res = calc_cascade_stability(
            pfc_vbus=req.pfc_vbus,
            pfc_pout=req.pfc_pout,
            pfc_cout_uf=req.pfc_cout_uf,
            pfc_fc_hz=req.pfc_fc_hz,
            dcdc_cin_uf=req.dcdc_cin_uf,
            dcdc_cin_esr_mohm=req.dcdc_cin_esr_mohm,
            dcdc_fc_khz=req.dcdc_fc_khz
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"级联阻抗稳定性扫频分析失败: {str(e)}")


@app.post("/api/calculate/buck")
def calculate_buck(req: BuckCalcRequest):
    try:
        # 1. 基础电气计算
        basic_res = calc_buck_converter(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lir_pct=req.lir_pct,
            v_rip_pct=req.v_rip_pct
        )
        
        # 若前端没有传入电感/电容，使用推荐的最小值
        l_uh = req.l_uh if req.l_uh is not None else basic_res['l_min_uh']
        c_uf = req.c_uf if req.c_uf is not None else basic_res['c_min_uf']
        
        # 2. 时域仿真
        time_res = simulate_buck_time_domain(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            l_uh=l_uh,
            c_uf=c_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            num_cycles=req.num_cycles
        )
        
        # 3. Bode 扫频仿真
        bode_res = simulate_buck_bode(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            l_uh=l_uh,
            c_uf=c_uf,
            rc_esr_mohm=req.rc_esr_mohm
        )
        
        # 4. 损耗计算
        losses_res = calc_buck_losses(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            duty=basic_res['duty'],
            sw_rds_on_mohm=req.sw_rds_on_mohm,
            sw_times_ns=req.sw_times_ns,
            diode_vf_v=req.diode_vf_v,
            ind_dcr_mohm=req.ind_dcr_mohm,
            esr_mohm=req.rc_esr_mohm,
            cout_rms_a=basic_res['cout_rms_a'],
            diode_type=req.diode_type,
            diode_qrr_nc=req.diode_qrr_nc,
            sync_rds_on_mohm=req.sync_rds_on_mohm,
            sync_dead_time_ns=req.sync_dead_time_ns,
            sync_body_vf_v=req.sync_body_vf_v
        )
        
        # 应力计算
        v_sw_stress = req.vin
        i_sw_pk = basic_res['i_peak_a']
        i_sw_rms = req.iout * math.sqrt(basic_res['duty'])
        
        v_diode_stress = req.vin
        i_diode_pk = basic_res['i_peak_a']
        i_diode_avg = req.iout * (1.0 - basic_res['duty'])
        
        # 5. DRC 校验
        drc_warnings = []
        k_ripple = basic_res['duty'] * (req.vin - req.vout) / (req.fsw_khz * 1000.0 * (l_uh * 1e-6) * req.iout) if req.iout > 0 and l_uh > 0 else 0.0
        
        if k_ripple < 0.1:
            drc_warnings.append("LIR 纹波系数过低 (<10%)：虽然输出纹波小，但会导致电感体积过大、成本偏高。建议降低电感感值。")
        elif k_ripple > 0.4:
            drc_warnings.append("LIR 纹波系数过高 (>40%)：电感电流纹波大，高频磁芯损耗增加且有饱和隐患。建议提高电感感值。")
            
        if req.vout >= req.vin:
            drc_warnings.append("严重错误：Buck 输出电压 Vout 必须严格小于输入电压 Vin！")
            
        # 如果效率太低产生警告
        if losses_res['efficiency'] < 0.85 and req.iout > 0:
            drc_warnings.append(f"⚠️ [效率偏低警告] 当前仿真计算的整机效率仅为 {losses_res['efficiency']*100:.1f}%，低于 85%。请检查 MOSFET 导通阻抗、电感 DCR 或开关频率是否设定过高，导致过大发热损耗。")
            
        return {
            "basic": basic_res,
            "actual_l_uh": l_uh,
            "actual_c_uf": c_uf,
            "time_domain": time_res,
            "bode": bode_res,
            "stresses": {
                "sw_v": v_sw_stress,
                "sw_i_pk": i_sw_pk,
                "sw_i_rms": i_sw_rms,
                "diode_v": v_diode_stress,
                "diode_i_pk": i_diode_pk,
                "diode_i_avg": i_diode_avg
            },
            "losses": losses_res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BomRequest(BaseModel):
    min_v_sw: Optional[float] = None
    min_i_sw: Optional[float] = None
    min_v_diode: Optional[float] = None
    min_i_diode: Optional[float] = None
    sw_v: Optional[float] = None
    sw_i: Optional[float] = None
    diode_v: Optional[float] = None
    diode_i: Optional[float] = None

    min_v_sw_sec: Optional[float] = None
    min_i_sw_sec: Optional[float] = None

@app.post("/api/bom/recommend")
def recommend_bom(req: BomRequest):
    # 兼容处理两种参数风格
    v_sw = req.min_v_sw if req.min_v_sw is not None else (req.sw_v or 0.0)
    i_sw = req.min_i_sw if req.min_i_sw is not None else (req.sw_i or 0.0)
    v_diode = req.min_v_diode if req.min_v_diode is not None else (req.diode_v or 0.0)
    i_diode = req.min_i_diode if req.min_i_diode is not None else (req.diode_i or 0.0)

    # 加入 1.2x 耐压与 1.5x 电流安全裕量
    req_v_sw = v_sw * 1.2
    req_i_sw = i_sw * 1.5
    
    req_v_diode = v_diode * 1.2
    req_i_diode = i_diode * 1.5
    
    switches = db.get_recommended_switches(req_v_sw, req_i_sw)
    diodes = db.get_recommended_diodes(req_v_diode, req_i_diode)
    
    res = {
        "switches": switches[:5],
        "diodes": diodes[:5],
        "requirements": {
            "sw_v": req_v_sw,
            "sw_i": req_i_sw,
            "diode_v": req_v_diode,
            "diode_i": req_i_diode
        }
    }

    if req.min_v_sw_sec is not None and req.min_i_sw_sec is not None:
        req_v_sw_sec = req.min_v_sw_sec * 1.2
        req_i_sw_sec = req.min_i_sw_sec * 1.5
        switches_sec = db.get_recommended_switches(req_v_sw_sec, req_i_sw_sec)
        res["switches_sec"] = switches_sec[:5]
        res["requirements"]["sw_v_sec"] = req_v_sw_sec
        res["requirements"]["sw_i_sec"] = req_i_sw_sec

    return res

class CreepageCalcRequest(BaseModel):
    voltage_rms: float
    voltage_peak: float
    pollution_degree: int  # 1, 2, 3
    cti_group: int        # 0: I, 1: II, 2: IIIa, 3: IIIb
    insulation_type: int   # 0: Basic, 1: Supplementary, 2: Reinforced
    altitude_m: float

def interpolate_table(v, table_v, table_d):
    if v <= table_v[0]: return table_d[0]
    if v >= table_v[-1]:
        # 高压超限斜率外推
        denom = table_v[-1] - table_v[-2]
        if denom != 0:
            slope = (table_d[-1] - table_d[-2]) / denom
            return table_d[-1] + slope * (v - table_v[-1])
        return table_d[-1]
    for i in range(len(table_v) - 1):
        if table_v[i] <= v <= table_v[i+1]:
            denom = table_v[i+1] - table_v[i]
            if denom != 0:
                ratio = (v - table_v[i]) / denom
                return table_d[i] + ratio * (table_d[i+1] - table_d[i])
            return table_d[i]
    return table_d[-1]

@app.post("/api/calculate/creepage")
def calculate_creepage(req: CreepageCalcRequest):
    try:
        v_rms = req.voltage_rms
        v_peak = req.voltage_peak
        alt = req.altitude_m
        
        pd_idx = req.pollution_degree
        cti_idx = req.cti_group
        ins_type = req.insulation_type
        
        is_reinforced = (ins_type == 2)
        
        # 1. 爬电距离 Creepage (拓展低压点阵 10V~40V)
        v_crp = [10, 12.5, 16, 20, 25, 32, 40, 50, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000]
        
        if pd_idx == 1:
            crp_data = [0.08, 0.09, 0.10, 0.11, 0.125, 0.14, 0.15, 0.18, 0.25, 0.28, 0.32, 0.42, 0.56, 0.75, 1.0, 1.3, 1.8, 2.4, 3.2]
            active_crp_data = crp_data
            creepage = interpolate_table(v_rms, v_crp, crp_data)
        elif pd_idx == 2:
            if cti_idx == 0:   d_data = [0.18, 0.20, 0.22, 0.25, 0.28, 0.35, 0.45, 0.6, 0.7, 0.8, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0]
            elif cti_idx == 1: d_data = [0.28, 0.32, 0.35, 0.40, 0.45, 0.56, 0.71, 0.9, 1.0, 1.1, 1.1, 1.4, 1.8, 2.2, 2.8, 3.6, 4.5, 5.6, 7.1]
            else:              d_data = [0.40, 0.45, 0.50, 0.56, 0.63, 0.80, 1.00, 1.2, 1.4, 1.5, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10.0]
            active_crp_data = d_data
            creepage = interpolate_table(v_rms, v_crp, d_data)
        else:
            if cti_idx == 0:   d_data = [0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.25, 1.5, 1.8, 1.9, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10.0, 12.5]
            elif cti_idx == 1: d_data = [0.70, 0.80, 0.90, 1.00, 1.10, 1.25, 1.40, 1.7, 2.0, 2.1, 2.2, 2.8, 3.6, 4.5, 5.6, 7.1, 9.0, 11.0, 14.0]
            else:              d_data = [0.80, 0.90, 1.00, 1.10, 1.25, 1.40, 1.60, 1.9, 2.2, 2.4, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10.0, 12.5, 16.0]
            active_crp_data = d_data
            creepage = interpolate_table(v_rms, v_crp, d_data)

        # 2. 电气间隙 Clearance
        v_clr = [50, 100, 150, 300, 600, 1000]
        if pd_idx == 1:
            clr_data = [0.18, 0.2, 0.5, 1.5, 3.0, 4.0]
        elif pd_idx == 2:
            clr_data = [0.2,  0.2, 0.5, 1.5, 3.0, 4.0]
        else:
            clr_data = [0.8,  0.8, 0.8, 1.5, 3.0, 4.0]
            
        base_clearance = interpolate_table(v_peak, v_clr, clr_data)

        # 3. 海拔修正系数 (Altitude Multiplier)
        alt_table = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 20000]
        factor_table = [1.00, 1.14, 1.29, 1.48, 1.70, 1.95, 2.25, 2.62, 3.02, 6.53, 17.0]
        
        if alt <= 2000:
            alt_factor = 1.0
        elif alt >= 20000:
            alt_factor = 17.0
        else:
            alt_factor = 1.0
            for i in range(len(alt_table) - 1):
                if alt_table[i] <= alt <= alt_table[i+1]:
                    ratio = (alt - alt_table[i]) / (alt_table[i+1] - alt_table[i])
                    alt_factor = factor_table[i] + ratio * (factor_table[i+1] - factor_table[i])
                    break
        
        final_clearance = base_clearance * alt_factor

        # 4. 加强绝缘加倍
        if is_reinforced:
            final_clearance *= 2.0
            creepage *= 2.0

        # 5. 爬电距离不得小于电气间隙
        if creepage < final_clearance:
            creepage = final_clearance

        # 开槽建议与 DRC
        slotting_advice = ""
        if creepage > final_clearance + 0.5:
            slotting_advice = f"提示: 爬电距离 ({creepage:.1f}mm) 远大于电气间隙 ({final_clearance:.1f}mm)!!!\n空间不够时，可以【在 PCB 开槽 (Slotting)】将爬电路径阻断转化为空间间隙从而符合安规要求。"

        drc_warnings = []
        if v_rms > 1000 or v_peak > 1000:
            drc_warnings.append(f"超高压警告：系统工作电压 ({v_rms:.0f}V RMS / {v_peak:.0f}V Peak) 已超过 IEC 60664-1 1000V 基础表项，已使用斜率外推解算。请务必加强物理绝缘与高压安全留裕！")

        # 6. 生成扫描图表数据 scan (修正 RMS 与 Peak 物理转换)
        cl_list = []
        cr_list = []
        for v in v_crp:
            cr_v = interpolate_table(v, v_crp, active_crp_data)
            # 电气间隙查表使用峰值电压 V_peak = sqrt(2) * V_rms
            base_clr_v = interpolate_table(v * math.sqrt(2.0), v_clr, clr_data)
            cl_v = base_clr_v * alt_factor
            
            if is_reinforced:
                cl_v *= 2.0
                cr_v *= 2.0
                
            if cr_v < cl_v:
                cr_v = cl_v
                
            cl_list.append(round(cl_v, 2))
            cr_list.append(round(cr_v, 2))
            
        scan_data = {
            "v": v_crp,
            "cl": cl_list,
            "cr": cr_list
        }

        return {
            "creepage_mm": creepage,
            "clearance_mm": final_clearance,
            "altitude_factor": alt_factor,
            "slotting_advice": slotting_advice,
            "drc_warnings": drc_warnings,
            "scan": scan_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class HeatsinkRthRequest(BaseModel):
    p_diss: float
    t_j_max: float
    t_amb: float
    r_jc: float
    r_cs: float

@app.post("/api/calculate/thermal/heatsink_rth")
def calculate_heatsink_rth_route(req: HeatsinkRthRequest):
    try:
        return calculate_heatsink_rth(
            p_diss=req.p_diss,
            t_j_max=req.t_j_max,
            t_amb=req.t_amb,
            r_jc=req.r_jc,
            r_cs=req.r_cs
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ForcedAirRequest(BaseModel):
    cfm: float
    duct_w_mm: float
    duct_h_mm: float
    r_nat: float
    air_vel_ms: float

@app.post("/api/calculate/thermal/forced_air")
def calculate_forced_air_route(req: ForcedAirRequest):
    try:
        return calculate_forced_air_cooling(
            cfm=req.cfm,
            duct_w_mm=req.duct_w_mm,
            duct_h_mm=req.duct_h_mm,
            r_nat=req.r_nat,
            air_vel_ms=req.air_vel_ms
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EnclosureRequest(BaseModel):
    length_mm: float
    width_mm: float
    height_mm: float
    p_in: float
    k_factor: float
    t_amb: float

@app.post("/api/calculate/thermal/enclosure")
def calculate_enclosure_route(req: EnclosureRequest):
    try:
        return calculate_enclosure_temp_rise(
            length_mm=req.length_mm,
            width_mm=req.width_mm,
            height_mm=req.height_mm,
            p_in=req.p_in,
            k_factor=req.k_factor,
            t_amb=req.t_amb
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class TransientRequest(BaseModel):
    c_spec: float
    mass_g: float
    p_shock: float
    duration_s: float
    t_start: float

@app.post("/api/calculate/thermal/transient")
def calculate_transient_route(req: TransientRequest):
    try:
        return calculate_transient_overload(
            c_spec=req.c_spec,
            mass_g=req.mass_g,
            p_shock=req.p_shock,
            duration_s=req.duration_s,
            t_start=req.t_start
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class SystemAirflowRequest(BaseModel):
    p_loss: float
    dt_allowed: float
    altitude_m: float
    margin_pct: float

@app.post("/api/calculate/thermal/system_airflow")
def calculate_system_airflow_route(req: SystemAirflowRequest):
    try:
        return calculate_system_airflow(
            p_loss=req.p_loss,
            dt_allowed=req.dt_allowed,
            altitude_m=req.altitude_m,
            margin_pct=req.margin_pct
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class FuseRequest(BaseModel):
    vin: float
    is_ac: bool
    c_bulk_uf: float
    r_series: float
    factor: float

@app.post("/api/calculate/protection/fuse")
def calculate_fuse_route(req: FuseRequest):
    try:
        return calculate_fuse_i2t(
            vin=req.vin,
            is_ac=req.is_ac,
            c_bulk_uf=req.c_bulk_uf,
            r_series=req.r_series,
            factor=req.factor
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class NtcRequest(BaseModel):
    v_in_max: float
    is_ac: bool
    c_bulk_uf: float
    j_rating: float
    diss_mw: float
    t_ambient: Optional[float] = 25.0

@app.post("/api/calculate/protection/ntc")
def calculate_ntc_route(req: NtcRequest):
    try:
        return calculate_ntc_inrush(
            v_in_max=req.v_in_max,
            is_ac=req.is_ac,
            c_bulk_uf=req.c_bulk_uf,
            j_rating=req.j_rating,
            diss_mw=req.diss_mw,
            t_ambient=req.t_ambient or 25.0
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class XcapRequest(BaseModel):
    vac: float
    cx_uf: float
    t_limit: float
    v_safe: float
    n_series: int
    custom_r_m: Optional[float] = None

@app.post("/api/calculate/protection/xcap")
def calculate_xcap_route(req: XcapRequest):
    try:
        return calculate_xcap_discharge(
            vac=req.vac,
            cx_uf=req.cx_uf,
            t_limit=req.t_limit,
            v_safe=req.v_safe,
            n_series=req.n_series,
            custom_r_m=req.custom_r_m
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ZenerRequest(BaseModel):
    vin_min: float
    vin_max: float
    vz: float
    iz_min_ma: float
    iload_min_ma: float
    iload_max_ma: float
    r_sel: float
    p_max_w: float = 0.5
    zzt: Optional[float] = 0.0

@app.post("/api/calculate/tvs_zener/zener")
def calculate_zener_route(req: ZenerRequest):
    try:
        return calculate_zener_regulator(
            vin_min=req.vin_min,
            vin_max=req.vin_max,
            vz=req.vz,
            iz_min_ma=req.iz_min_ma,
            iload_min_ma=req.iload_min_ma,
            iload_max_ma=req.iload_max_ma,
            r_sel=req.r_sel,
            p_max_w=req.p_max_w,
            zzt=req.zzt or 0.0
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class TvsRequest(BaseModel):
    v_surge: float
    r_src: float
    vbr: float
    vc_spec: float
    ipp_spec: float
    pppm_rated: float
    pulse_type: Optional[str] = "10/1000us"

@app.post("/api/calculate/tvs_zener/tvs")
def calculate_tvs_route(req: TvsRequest):
    try:
        return calculate_tvs_clamping(
            v_surge=req.v_surge,
            r_src=req.r_src,
            vbr=req.vbr,
            vc_spec=req.vc_spec,
            ipp_spec=req.ipp_spec,
            pppm_rated=req.pppm_rated,
            pulse_type=req.pulse_type or "10/1000us"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class FlybackRequest(BaseModel):
    vin: float
    vor: float
    vout: float
    iout: float
    fsw_khz: float
    krf: float
    bmax: float
    ae: float
    lp_uh: Optional[float] = None
    c_uf: Optional[float] = None
    rc_esr_mohm: float = 30.0
    rcd_l_lk: float = 5.0
    rcd_v_spike: float = 50.0
    eff: float = 0.85

@app.post("/api/calculate/flyback")
def calculate_flyback(req: FlybackRequest):
    try:
        # 1. 基础物理设计计算
        design_res = calc_flyback_converter(
            vin_min=req.vin,
            vor=req.vor,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            krf=req.krf,
            bmax=req.bmax,
            ae=req.ae,
            eff=req.eff
        )
        
        # 若用户未指定实际 Lp 和 Co，使用设计推荐值
        lp_uh = req.lp_uh if req.lp_uh is not None else design_res['lp_design_uh']
        c_uf = req.c_uf if req.c_uf is not None else design_res['c_out_design_uf']
        
        # 2. 运行实际工况时域仿真和应力核对
        time_res = simulate_flyback_time_domain(
            vin=req.vin,
            vor=req.vor,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lp_uh=lp_uh,
            co_uf=c_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            l_leak_uh=req.rcd_l_lk,
            v_spike=req.rcd_v_spike,
            eff=req.eff
        )
        
        # 3. 运行控制环路 Bode 扫频仿真
        bode_res = simulate_flyback_bode(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            lp_uh=lp_uh,
            co_uf=c_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            vor=req.vor,
            mode_str=time_res['mode'],
            d_act=time_res['d_act']
        )
        
        # 4. DRC 校验逻辑
        drc_warnings = []
        d_act = time_res['d_act']
        
        if d_act > 0.5:
            drc_warnings.append(f"⚠️ [警告] 实际占空比 D_act ({d_act:.2f}) 超过了 0.5。反激电路在此占空比下会增大变压器磁芯重置难度，建议适当调高输入电压或降低反射电压 Vor。")
            
        b_pk = (lp_uh * 1e-6 * time_res['ipk']) / (design_res['np_design_turns'] * req.ae * 1e-6) if design_res['np_design_turns'] > 0 and req.ae > 0 else 0.0
        limit_b = min(0.32, req.bmax)
        if b_pk > limit_b:
            drc_warnings.append(f"🔴 [饱和风险] 变压器峰值工作磁密 B_pk ({b_pk:.3f} T) 超过设计安全阈值 ({limit_b:.2f} T)，铁氧体磁芯在高温下极易发生饱和！建议增大磁芯有效面积 Ae 或增加设计匝数 Np。")
            
        if time_res['mode'] == "CCM":
            fsw = req.fsw_khz * 1000.0
            lp_crit = (req.vin**2 * d_act**2) / (2.0 * ((req.vout * req.iout) / req.eff) * fsw)
            delta_ip = (req.vin * d_act) / (lp_uh * 1e-6 * fsw) if lp_uh > 0 else 0.0
            iedc = ((req.vout * req.iout) / req.eff) / (req.vin * d_act) if d_act > 0 else 0.0
            krf_act = delta_ip / iedc if iedc > 0 else 0.0
            if krf_act < 0.1:
                drc_warnings.append(f"⚠️ [设计偏大] 实际电流纹波率系数 ({krf_act:.2f}) 小于 0.1，电感感值偏大，这会造成变压器体积过度冗余 and 成本攀升，建议减小实际电感 Lp。")
            elif krf_act > 0.5:
                drc_warnings.append(f"⚠️ [设计偏小] 实际电流纹波率系数 ({krf_act:.2f}) 大于 0.5，高频纹波电流过大会导致线圈交流铜损和核心磁损剧增，建议增大实际电感 Lp。")
                
        if req.rcd_v_spike < 0.2 * req.vor:
            drc_warnings.append(f"⚠️ [钳位过紧] 电压尖峰允许值 V_spike ({req.rcd_v_spike:.1f} V) 小于 0.2 * Vor，这会导致 RCD 缓冲器损耗过高（吸收电阻严重发热），建议适当放宽 V_spike 在 30V~50V 左右。")
            
        p_loss = req.vout * req.iout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")

        return {
            "design": design_res,
            "actual_lp_uh": lp_uh,
            "actual_c_uf": c_uf,
            "simulation_time": time_res,
            "simulation_bode": bode_res,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AcfRequest(BaseModel):
    vin: float
    vor: float
    vout: float
    iout: float
    fsw_khz: float
    krf: float
    bmax: float
    ae: float
    lp_uh: Optional[float] = None
    c_uf: Optional[float] = None
    rc_esr_mohm: float = 30.0
    l_lk_uh: float = 5.0
    coss_pf: float = 100.0
    eff: float = 0.90

@app.post("/api/calculate/acf_flyback")
def calculate_acf_flyback(req: AcfRequest):
    try:
        # 1. 基础物理设计计算
        design_res = calc_acf_converter(
            vin_min=req.vin,
            vor=req.vor,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            krf=req.krf,
            bmax=req.bmax,
            ae=req.ae,
            l_lk_uh=req.l_lk_uh,
            coss_pf=req.coss_pf,
            eff=req.eff
        )
        
        # 若用户未指定实际 Lp 和 Co，使用设计推荐值
        lp_uh = req.lp_uh if req.lp_uh is not None else design_res['lp_design_uh']
        c_uf = req.c_uf if req.c_uf is not None else design_res['c_out_design_uf']
        
        # 2. 运行实际工况时域 ZVS 瞬态仿真
        time_res = simulate_acf_time_domain(
            vin=req.vin,
            vor=req.vor,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lp_uh=lp_uh,
            co_uf=c_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            coss_pf=req.coss_pf,
            l_lk_uh=req.l_lk_uh,
            eff=req.eff
        )
        
        # 3. 运行控制环路 Bode 扫频仿真 (含有源钳位 Notch 谐振效应)
        bode_res = simulate_acf_bode(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            lp_uh=lp_uh,
            co_uf=c_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            coss_pf=req.coss_pf,
            l_lk_uh=req.l_lk_uh,
            vor=req.vor,
            d_act=design_res['duty_max'],
            c_clamp_f=design_res['c_clamp_f']
        )
        
        # 4. DRC 校验逻辑
        drc_warnings = []
        d_act = design_res['duty_max']
        
        if d_act > 0.5:
            drc_warnings.append(f"⚠️ [警告] ACF 实际占空比 D_act ({d_act:.2f}) 超过了 0.5。这会造成辅助钳位开关管的反向脉冲励磁电流过大，建议调高输入电压或降低反射电压 Vor。")
            
        b_pk = (lp_uh * 1e-6 * design_res['ipk_a']) / (design_res['np_design_turns'] * req.ae * 1e-6) if design_res['np_design_turns'] > 0 and req.ae > 0 else 0.0
        limit_b = min(0.32, req.bmax)
        if b_pk > limit_b:
            drc_warnings.append(f"🔴 [饱和风险] 变压器峰值工作磁密 B_pk ({b_pk:.3f} T) 超过设计安全阈值 ({limit_b:.2f} T)，有高温下磁芯饱和隐患！建议增大磁芯有效面积 Ae 或增加设计匝数 Np。")
            
        # ZVS 校验
        if not design_res['acf_zvs_possible']:
            drc_warnings.append(f"⚠️ [软开关失效] 当前漏感能量 (0.5*Lk*i_neg^2) 不足以释放开关管 Coss 电压至零，主有源管无法实现完整 ZVS。建议适当增大变压器漏感 L_leak_uh 或选用结电容 Coss_pf 更小的开关管。")
            
        p_loss = req.vout * req.iout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")

        return {
            "design": design_res,
            "actual_lp_uh": lp_uh,
            "actual_c_uf": c_uf,
            "simulation_time": time_res,
            "simulation_bode": bode_res,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ForwardRequest(BaseModel):
    vin_min: float
    vin_nom: float
    vin_max: float
    vout: float
    iout: float
    fsw_khz: float
    dmax: float
    lir_pct: float
    ae: float
    lo_uh: Optional[float] = None
    co_uf: Optional[float] = None
    rc_esr_mohm: float = 30.0
    b_peak: float = 0.3
    bpeak: Optional[float] = None
    eff: float = 0.85

@app.post("/api/calculate/forward")
def calculate_forward(req: ForwardRequest):
    try:
        b_peak_val = req.b_peak if req.bpeak is None else req.bpeak
        # 1. 基础物理设计计算
        design_res = calc_forward_converter(
            vin_min=req.vin_min,
            vin_nom=req.vin_nom,
            vin_max=req.vin_max,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            dmax=req.dmax,
            lir_pct=req.lir_pct,
            ae=req.ae
        )
        
        # 若用户未指定实际 Lo 和 Co，使用设计推荐值
        lo_uh = req.lo_uh if req.lo_uh is not None else design_res['lo_min_uh']
        co_uf = req.co_uf if req.co_uf is not None else design_res['c_out_design_uf']
        
        # 2. 运行实际工况时域瞬态仿真
        time_res = simulate_forward_time_domain(
            vin_nom=req.vin_nom,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lo_uh=lo_uh,
            co_uf=co_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            n=design_res['turns_ratio_n'],
            d_nom=design_res['d_nom']
        )
        
        # 3. 运行控制环路 Bode 扫频仿真
        bode_res = simulate_forward_bode(
            vin_nom=req.vin_nom,
            vout=req.vout,
            iout=req.iout,
            lo_uh=lo_uh,
            co_uf=co_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            n=design_res['turns_ratio_n']
        )
        
        # 4. DRC 校验逻辑
        drc_warnings = []
        d_nom = design_res['d_nom']
        
        if d_nom > req.dmax:
            drc_warnings.append(f"⚠️ [警告] 标称占空比 D_nom ({d_nom:.2f}) 超过了最大设计值 D_max ({req.dmax:.2f})。请核算输入电压或反射变比以防变压器复位不足。")
            
        # 磁芯磁通复位检验（磁复位一般要求 D_max < 0.5 针对 1:1 去磁绕组）
        if req.dmax > 0.5:
            drc_warnings.append(f"⚠️ [磁复位风险] 最大设计占空比 D_max ({req.dmax:.2f}) 超过 0.5。对于双绕组 1:1 去磁复位的单端正激，必须满足 D_max < 0.5 才能保证磁芯完全复位。")
            
        fsw_hz = req.fsw_khz * 1000.0
        np_val = (req.vin_min * req.dmax) / (fsw_hz * req.ae * 1e-6 * b_peak_val)
        np_calc = math.ceil(np_val)
        b_pk_actual = (req.vin_min * req.dmax) / (fsw_hz * req.ae * 1e-6 * np_calc) if np_calc > 0 else 0.0
        limit_b = min(0.32, b_peak_val)
        if b_pk_actual > limit_b:
            drc_warnings.append(f"🔴 [饱和风险] 变压器实际峰值磁密 B_pk_actual ({b_pk_actual:.3f} T) 超过设计安全阈值 ({limit_b:.2f} T)，有高温下磁芯饱和隐患！")
        p_loss = req.vout * req.iout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("警告：推荐散热片热阻小于 2.0 C/W，发热损耗严重，建议采取强迫风冷。")

        # 对 design_res 注入别名以适应前端
        design_res['lo_design_uh'] = design_res['lo_min_uh']
        design_res['co_design_uf'] = design_res['c_out_design_uf']
        
        # 计算励磁电感 Lm
        fsw = req.fsw_khz * 1000.0
        n = design_res['turns_ratio_n']
        i_mag_pk = 0.05 * (req.iout / n) if n > 0 else 0.1
        lm_val = (req.vin_nom * d_nom) / (fsw * i_mag_pk) if (fsw * i_mag_pk) > 0 else 1.5e-3
        design_res['lm_u_h'] = lm_val * 1e6

        # 重新组装并注入时域仿真别名
        t_arr = [t_us * 1e-6 for t_us in time_res["t_us"]]
        T_sw = 1.0 / fsw
        imag_pk = (req.vin_nom / lm_val) * (d_nom * T_sw) if lm_val > 0 else 0.0
        
        imag_list = []
        for ti in t_arr:
            if ti < d_nom * T_sw:
                val = (req.vin_nom / lm_val) * ti if lm_val > 0 else 0.0
            elif ti < 2.0 * d_nom * T_sw:
                val = imag_pk - (req.vin_nom / lm_val) * (ti - d_nom * T_sw) if lm_val > 0 else 0.0
                if val < 0: val = 0.0
            else:
                val = 0.0
            imag_list.append(val)
            
        il_list = time_res["i_lo_a"]
        is_free_list = [0.0 if ti < d_nom * T_sw else il_list[idx] for idx, ti in enumerate(t_arr)]
        
        time_res["time"] = t_arr
        time_res["ip"] = time_res["i_pri_a"]
        time_res["imag"] = imag_list
        time_res["is_free"] = is_free_list
        time_res["vo_ripple"] = [v / 1000.0 for v in time_res["v_ripple_mv"]]

        stresses = {
            "sw_v": design_res["v_ds_max"],
            "sw_i_pk": design_res["i_d_max"],
            "sw_i_rms": (req.iout / design_res["turns_ratio_n"]) * math.sqrt(d_nom),
            "rect_diode_v": design_res["v_rev_max"],
            "rect_diode_i_avg": req.iout * d_nom,
            "free_diode_v": design_res["v_rev_max"],
            "free_diode_i_avg": req.iout * (1.0 - d_nom)
        }

        return {
            "design": design_res,
            "actual_lo_uh": lo_uh,
            "actual_co_uf": co_uf,
            "simulation": time_res,
            "simulation_bode": bode_res,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs,
            "stresses": stresses
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class InterleavedSbbRequest(BaseModel):
    vin: float
    vin_min: float
    vin_max: float
    vout: float
    iout: float
    fsw_khz: float
    lo_uh: float
    co_uf: float
    rc_esr_mohm: float
    topo_type: str
    coupled_coeff: float = 0.0
    num_phases: int = 2
    flying_c_uf: float = 10.0
    eff: float = 0.95

@app.post("/api/calculate/interleaved_sbb")
def calculate_interleaved_sbb_route(req: InterleavedSbbRequest):
    try:
        # 1. 物理参数设计与应力核算
        calcs = calc_interleaved_sbb(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            L_uh=req.lo_uh,
            C_uf=req.co_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            topo_type=req.topo_type,
            coupled_coeff=req.coupled_coeff,
            num_phases=req.num_phases,
            flying_c_uf=req.flying_c_uf,
            eff=req.eff
        )
        
        # 2. 时域和扫频波形仿真
        sim_res = simulate_sbb_waveforms(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            L_uh=req.lo_uh,
            C_uf=req.co_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            topo_type=req.topo_type,
            coupled_coeff=req.coupled_coeff,
            num_phases=req.num_phases,
            flying_c_uf=req.flying_c_uf,
            calcs=calcs
        )
        
        # 3. DRC 校验逻辑
        drc_warnings = []
        is_three_level = "Three-Level" in req.topo_type or "三电平" in req.topo_type
        
        # 纯 Buck 模式下的 Vout 限制校验
        if "4-Switch" not in req.topo_type and "升降压" not in req.topo_type:
            if req.vout >= req.vin:
                drc_warnings.append("❌ [电路限制] 纯 Buck 拓扑输出电压 Vout 必须小于输入电压 Vin！")
                
        # 纹波率校验
        lir_val = calcs['delta_il_phase'] / calcs['i_phase_dc'] if calcs['i_phase_dc'] > 0 else 0.0
        if lir_val < 0.1:
            drc_warnings.append("⚠️ [设计优化] 单相电流纹波率较低 (<10%)：虽然输出平滑，但会导致滤波电感体积过大且成本偏高。")
        elif lir_val > 0.4:
            drc_warnings.append("⚠️ [饱和风险] 单相电流纹波率偏高 (>40%)：磁芯磁通摆幅过大，高频磁芯损耗增加且有磁饱和隐患。")
            
        # 飞跨电容电压平衡校验
        if is_three_level and calcs['vcf_ripple'] > 0.1 * (req.vin / 2.0):
            drc_warnings.append("⚠️ [电容纹波警告] 飞跨电容 C_fly 的电压纹波较大 (已超过 10% Vdc/2)，可能引起中点电位发生偏移危险。建议适当增大 C_fly 的电容量！")
            
        return {
            "design": calcs,
            "simulation": sim_res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class InterleavedPfcRequest(BaseModel):
    vac_min: float
    vac_max: float
    vbus: float
    pout: float
    eff: float
    fsw_khz: float
    k_ripple: float
    mode: str
    c_uf: float
    esr_mohm: float
    t_hold_ms: float = 20.0
    lo_uh: Optional[float] = 0.0

@app.post("/api/calculate/interleaved_pfc")
def calculate_interleaved_pfc(req: InterleavedPfcRequest):
    try:
        vin_pk_min = req.vac_min * math.sqrt(2.0)
        if vin_pk_min >= req.vbus:
            raise HTTPException(status_code=400, detail="最小交流峰值电压不能大于等于输出直流电压")
            
        # 1. 物理参数设计
        calcs = calc_interleaved_boost_pfc(
            vac_min=req.vac_min,
            vac_max=req.vac_max,
            vbus=req.vbus,
            pout=req.pout,
            eff=req.eff,
            fsw_khz=req.fsw_khz,
            k_ripple=req.k_ripple,
            mode=req.mode,
            c_uf=req.c_uf,
            esr_mohm=req.esr_mohm,
            t_hold_ms=req.t_hold_ms
        )
        
        # 确定实际电感量，若前端传入为0，则使用设计推荐值
        lo_uh_actual = req.lo_uh if (req.lo_uh is not None and req.lo_uh > 0) else (calcs['l_val'] * 1e6)
        
        # 2. 运行工况时频域仿真
        sim_res = simulate_pfc_waveforms(
            vac_min=req.vac_min,
            vbus=req.vbus,
            iin_pk=calcs['iin_pk'],
            fsw_khz=req.fsw_khz,
            Lo=lo_uh_actual * 1e-6,
            Co=req.c_uf * 1e-6,
            rc_esr=req.esr_mohm * 1e-3,
            delta_vbus_pp=calcs['delta_vbus_pp'],
            pout=req.pout
        )
        
        # 3. DRC 校验逻辑
        drc_warnings = []
        
        # 纹波率警告
        if "CCM" in req.mode:
            if req.k_ripple > 0.4:
                drc_warnings.append("⚠️ [电感电流纹波过高] 单相高频电流纹波系数超出 40%。将增加电感的磁芯高频损耗并存在轻载下提早进入断续模式的隐患。建议适当提高电感量 Lo！")
            elif req.k_ripple < 0.1:
                drc_warnings.append("⚠️ [电感设计偏保守] 电流纹波系数低于 10%。这虽然可以降低高频纹波，但会使滤波电感量需求偏大、体积及铁铜损成本剧增。")
                
        # 工频纹波率警告
        vbus_ripple_ratio = calcs['delta_vbus_pp'] / req.vbus
        if vbus_ripple_ratio > 0.05:
            drc_warnings.append(f"⚠️ [电压纹波过大] 直流母线电压的二次工频纹波率 ({vbus_ripple_ratio * 100:.1f}%) 已超出 5%。可能会对后级谐振变换器运行或网侧 EMI 造成不利影响。建议增大母线大电容量 C_bus！")
            
        # 维持电容警告
        if req.c_uf < calcs['c_hold_f'] * 1e6:
            drc_warnings.append(f"⚠️ [维持时间警告] 实际配置的母线大电容量 ({req.c_uf:.1f} uF) 小于维持时间 {req.t_hold_ms}ms 理论计算的最小电容需求 ({calcs['c_hold_f']*1e6:.1f} uF)。在网侧瞬坠或短暂断电时可能会发生母线电压过快跌落引起后级停机故障。")
            
        return {
            "design": calcs,
            "actual_lo_uh": lo_uh_actual,
            "simulation": sim_res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class TotemPolePfcRequest(BaseModel):
    vac_min: float
    vac_max: float
    vbus: float
    pout: float
    eff: float
    fsw_khz: float
    k_ripple: float
    mode: str
    c_uf: float
    esr_mohm: float
    t_hold_ms: float = 20.0
    lo_uh: Optional[float] = 0.0

@app.post("/api/calculate/totem_pole")
def calculate_totem_pole(req: TotemPolePfcRequest):
    try:
        vin_pk_min = req.vac_min * math.sqrt(2.0)
        if vin_pk_min >= req.vbus:
            raise HTTPException(status_code=400, detail="最小交流峰值电压不能大于等于输出直流电压")
            
        # 1. 物理参数设计
        calcs = calc_totem_pole_pfc(
            vac_min=req.vac_min,
            vac_max=req.vac_max,
            vbus=req.vbus,
            pout=req.pout,
            eff=req.eff,
            fsw_khz=req.fsw_khz,
            k_ripple=req.k_ripple,
            mode=req.mode,
            c_uf=req.c_uf,
            esr_mohm=req.esr_mohm,
            t_hold_ms=req.t_hold_ms
        )
        
        # 确定实际配置的电感量，若前端传入0，则使用设计推荐值
        lo_uh_actual = req.lo_uh if (req.lo_uh is not None and req.lo_uh > 0) else (calcs['l_min_h'] * 1e6)
        
        # 2. 运行工况时频域仿真
        sim_res = simulate_totem_pole_waveforms(
            vac_min=req.vac_min,
            vbus=req.vbus,
            iin_pk=calcs['iin_pk'],
            fsw_khz=req.fsw_khz,
            Lo=lo_uh_actual * 1e-6,
            Co=req.c_uf * 1e-6,
            rc_esr=req.esr_mohm * 1e-3,
            delta_vbus_pp=calcs['delta_vbus_pp'],
            pout=req.pout
        )
        
        # 3. DRC 校验逻辑
        drc_warnings = []
        
        # 纹波率警告(CCM)
        if "CCM" in req.mode:
            if req.k_ripple > 0.4:
                drc_warnings.append("⚠️ [电感电流纹波过高] 电流纹波率超过 40%。高频纹波电流大，将增加电感磁芯损耗并可能在轻载下提前进入断续模式。建议适当提高电感值 Lo。")
            elif req.k_ripple < 0.1:
                drc_warnings.append("⚠️ [电感设计偏保守] 电流纹波率低于 10%。这会使电感体积和铜重明显偏大，导致成本及铜损显著增加。")
                
        # 工频纹波率警告
        vbus_ripple_ratio = calcs['delta_vbus_pp'] / req.vbus
        if vbus_ripple_ratio > 0.05:
            drc_warnings.append(f"⚠️ [电压纹波过大] 直流母线电压的二次工频纹波率 ({vbus_ripple_ratio * 100:.1f}%) 已超过 5%。可能会对后级系统或环路稳定性造成不利影响。建议增大母线滤波电容量 C_bus。")
            
        # 维持电容警告
        if req.c_uf < calcs['c_hold_f'] * 1e6:
            drc_warnings.append(f"⚠️ [维持时间警告] 实际母线电容量 ({req.c_uf:.1f} uF) 小于维持时间 {req.t_hold_ms}ms 要求的最小电容量 ({calcs['c_hold_f']*1e6:.1f} uF)。在网侧瞬坠或短暂断电时可能会导致母线电压过快跌落引起后级停机故障。")
            
        # 补全散热与系统损耗核算
        p_loss = req.pout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")
            
        return {
            "design": calcs,
            "actual_lo_uh": lo_uh_actual,
            "simulation": sim_res,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ViennaPfcRequest(BaseModel):
    vac_line: float
    vbus: float
    power: float
    eff: float
    fsw_khz: float
    k_ripple: float
    c_uf: float
    esr_mohm: float
    t_hold_ms: float = 10.0
    lo_uh: Optional[float] = 0.0
    fc_mid_hz: float = 10.0

@app.post("/api/calculate/vienna")
def calculate_vienna(req: ViennaPfcRequest):
    try:
        if req.vbus < req.vac_line * math.sqrt(2.0):
            raise HTTPException(status_code=400, detail="直流母线电压 Vbus 必须大于交流线电压峰值 (Vac_line * sqrt(2))")
            
        # 1. 物理参数设计
        calcs = calc_vienna_pfc(
            vac_line=req.vac_line,
            vbus=req.vbus,
            power=req.power,
            eff=req.eff,
            fsw_khz=req.fsw_khz,
            lir_pct=req.k_ripple * 100.0,
            c_uf=req.c_uf,
            esr_mohm=req.esr_mohm,
            t_hold_ms=req.t_hold_ms
        )
        
        # 确定实际配置的电感量，若前端传入0，则使用设计推荐值
        lo_uh_actual = req.lo_uh if (req.lo_uh is not None and req.lo_uh > 0) else (calcs['l_min_h'] * 1e6)
        
        # 2. 运行工况时频域仿真
        sim_res = simulate_vienna_waveforms(
            vac_line=req.vac_line,
            vbus=req.vbus,
            iin_pk=calcs['iin_pk'],
            fsw_khz=req.fsw_khz,
            Lo=lo_uh_actual * 1e-6,
            Co=req.c_uf * 1e-6,
            rc_esr_mohm=req.esr_mohm,
            delta_il=calcs['delta_il'],
            power=req.power,
            eff=req.eff,
            fc_mid_hz=req.fc_mid_hz
        )
        
        # 将平衡环路仿真计算出的交叉截止频率注入设计结果中，供前端界面展示
        calcs['fc_midpoint_hz'] = sim_res['bode_midpoint']['fc_hz']
        
        # 3. DRC 校验逻辑
        drc_warnings = []
        
        # 纹波率警告
        if req.k_ripple > 0.4:
            drc_warnings.append("⚠️ [电感电流纹波过高] 交流电流纹波系数超出 40%。高频纹波电流过大会大幅增加输入滤波电感的高频磁损与绕组铜损，并有可能导致磁饱和。建议适当增加实际电感感值 Lo。")
        elif req.k_ripple < 0.1:
            drc_warnings.append("⚠️ [电感感值设计偏大] 电流纹波系数低于 10%。这虽然能获得极为平滑的电流，但是会导致输入电感感值偏高、体积大且铁铜重量过重，使得设计成本虚高。")
            
        # 维持电容校验
        if req.c_uf < calcs['c_single_req_uf']:
            drc_warnings.append(f"⚠️ [维持电容不足] 实际单个母线分压电容量 ({req.c_uf:.1f} uF) 低于维持时间 {req.t_hold_ms}ms 要求的最小容量 ({calcs['c_single_req_uf']:.1f} uF)。在网侧电压瞬坠时可能发生母线电压过快下降故障。")
            
        # 最小母线电压校验(防止整流桥失效)
        vbus_limit = req.vac_line * math.sqrt(2.0)
        if req.vbus < vbus_limit * 1.05:
            drc_warnings.append(f"🔴 [母线电压过低] 直流母线电压 Vbus ({req.vbus:.1f} V) 过于接近交流输入线电压峰值 ({vbus_limit:.1f} V)。Vienna PFC 作为升压型整流器，必须确保母线电压有足够的升压余量，否则可能发生电流畸变且中点电位失控！")
            
        # SVPWM 调制比越界校验
        if calcs['m'] > 1.155:
            drc_warnings.append(f"❌ [过调制警告] 当前调制指数 m ({calcs['m']:.3f}) 超过了线性调制区上限 1.155 (2/sqrt(3))。整流器将进入严重的过调制区，在网侧相电流中引入大量高频低谐波畸变，请提高直流侧电压 Vbus 或降低输入交流电压！")
            
        # 补全散热与系统损耗核算
        p_loss = req.power * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")
            
        return {
            "design": calcs,
            "actual_lo_uh": lo_uh_actual,
            "simulation": sim_res,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class AfeCalcRequest(BaseModel):
    vac_line: float
    vbus: float
    pout: float
    eff: float
    fsw_khz: float
    lac_uh: float
    lac_esr_mohm: float
    cdc_uf: float
    cdc_esr_mohm: float
    t_hold_ms: float = 20.0
    lcl_enable: bool = False
    lcl_l2_uh: float = 250.0
    lcl_cf_uf: float = 10.0

@app.post("/api/calculate/afe")
def calculate_afe(req: AfeCalcRequest):
    try:
        vin_pk_line = req.vac_line * math.sqrt(2.0)
        if req.vbus <= vin_pk_line:
            raise HTTPException(status_code=400, detail="直流母线电压 Vbus 必须大于交流输入线电压峰值 (Vac_line * sqrt(2))，否则二极管反压整流失控")
            
        # 1. 主回路计算
        calcs = calc_afe_rectifier(
            vac_line=req.vac_line,
            vbus=req.vbus,
            pout=req.pout,
            eff=req.eff,
            fsw_khz=req.fsw_khz,
            lac_uh=req.lac_uh,
            lac_esr_mohm=req.lac_esr_mohm,
            cdc_uf=req.cdc_uf,
            cdc_esr_mohm=req.cdc_esr_mohm,
            t_hold_ms=req.t_hold_ms,
            lcl_enable=req.lcl_enable,
            lcl_l2_uh=req.lcl_l2_uh,
            lcl_cf_uf=req.lcl_cf_uf
        )
        
        # 2. 时频域仿真
        sim_res = simulate_afe_waveforms(
            vac_line=req.vac_line,
            vbus=req.vbus,
            iin_pk=calcs['i_ac_pk'],
            fsw_khz=req.fsw_khz,
            L1=req.lac_uh * 1e-6,
            R1=req.lac_esr_mohm * 1e-3,
            Co=req.cdc_uf * 1e-6,
            delta_i_l=calcs['delta_i_l'],
            pout=req.pout,
            eff=req.eff
        )
        
        # 3. DRC 校验逻辑
        drc_warnings = []
        
        # 纹波率校验
        if calcs['k_ripple'] > 0.4:
            drc_warnings.append("⚠️ [电感高频电流纹波过大] 输入桥侧电感高频电流纹波率超出 40%。高频损耗会使电感发热严重，且可能在高载下磁饱和，建议增大 L1 感值！")
        elif calcs['k_ripple'] < 0.1:
            drc_warnings.append("⚠️ [电感感值偏大] 电流纹波率低于 10%。这虽然有利于平滑电流，但会导致电感体积巨大、铁铜材料成本虚高，建议适当降低 L1！")
            
        # SVPWM 调制比越界校验
        if calcs['m'] > 1.155:
            drc_warnings.append(f"❌ [过调制警告] 当前调制指数 m ({calcs['m']:.3f}) 超过了线性调制区上限 1.155 (2/sqrt(3))。整流器将进入严重的过调制区，在网侧相电流中引入大量高频低谐波畸变，请提高直流侧电压 Vbus 或降低输入交流电压！")
            
        # LCL 谐振频率设计规范
        if req.lcl_enable and calcs['lcl_f_res'] > 0:
            # 谐振频率应处于 fc 的 1/6 和 1/2 之间以避免与环路控制谐振
            fc_khz = req.fsw_khz / 10.0
            f_res = calcs['lcl_f_res']
            if f_res < (fc_khz * 1000.0) * 0.5 or f_res > (req.fsw_khz * 1000.0) * 0.5:
                drc_warnings.append(f"⚠️ [LCL谐振区危险] 滤波器谐振频率 ({f_res:.1f} Hz) 不在推荐的安全区间 (处于电流控制带宽 {fc_khz*1000*0.5:.1f}Hz 与开关频率一半 {req.fsw_khz*1000*0.5:.1f}Hz 之间)。可能会导致系统高频振荡甚至失去控制，建议调整网侧 L2 或 Cf 电容参数！")
                
        # 维持电容校验
        if req.cdc_uf < calcs['c_hold_f'] * 1e6:
            drc_warnings.append(f"⚠️ [维持电容不足] 实际直流母线电容量 ({req.cdc_uf:.1f} uF) 低于维持时间 {req.t_hold_ms}ms 要求的最小电容限制 ({calcs['c_hold_f']*1e6:.1f} uF)。在网侧瞬时坠压时母线电压会发生危险跌落导致保护停机。")
            
        return {
            "design": calcs,
            "simulation": sim_res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class TTypeCalcRequest(BaseModel):
    vac_line: float
    vbus: float
    pout: float
    eff: float
    fsw_khz: float
    lac_uh: float
    lac_esr_mohm: float
    cdc_uf: float
    cdc_esr_mohm: float
    cos_phi: float
    lcl_enable: bool = False
    lcl_l2_uh: float = 250.0
    lcl_cf_uf: float = 10.0
    rds_on_main: float = 0.08
    rds_on_mid: float = 0.04

@app.post("/api/calculate/t_type_converter")
def calculate_t_type_converter(req: TTypeCalcRequest):
    try:
        vin_pk_line = req.vac_line * math.sqrt(2.0)
        if req.vbus <= vin_pk_line:
            raise HTTPException(status_code=400, detail="直流母线电压 Vbus 必须大于交流输入线电压峰值 (Vac_line * sqrt(2))，否则二极管反压整流失控")
            
        # 1. 主回路计算与损耗周期积分
        calcs = calc_t_type_converter(
            vac_line=req.vac_line,
            vbus=req.vbus,
            pout=req.pout,
            eff=req.eff,
            fsw_khz=req.fsw_khz,
            lac_uh=req.lac_uh,
            lac_esr_mohm=req.lac_esr_mohm,
            cdc_uf=req.cdc_uf,
            cdc_esr_mohm=req.cdc_esr_mohm,
            cos_phi=req.cos_phi,
            lcl_enable=req.lcl_enable,
            lcl_l2_uh=req.lcl_l2_uh,
            lcl_cf_uf=req.lcl_cf_uf,
            rds_on_main=req.rds_on_main,
            rds_on_mid=req.rds_on_mid
        )
        
        # 2. 时频域仿真
        sim_res = simulate_t_type_waveforms(
            vac_line=req.vac_line,
            vbus=req.vbus,
            iin_pk=calcs['i_ac_pk'],
            fsw_khz=req.fsw_khz,
            L1=req.lac_uh * 1e-6,
            R1=req.lac_esr_mohm * 1e-3,
            Co=req.cdc_uf * 1e-6,
            delta_i_l=calcs['delta_i_l'],
            pout=req.pout,
            eff=req.eff
        )
        
        # 3. 动态应力拆解与 DRC 合并
        drc_warnings = calcs['drc_warnings']
        
        # LCL 谐振频率设计规范
        if req.lcl_enable and calcs['lcl_f_res'] > 0:
            fc_khz = req.fsw_khz / 10.0
            f_res = calcs['lcl_f_res']
            if f_res < (fc_khz * 1000.0) * 0.5 or f_res > (req.fsw_khz * 1000.0) * 0.5:
                drc_warnings.append(f"⚠️ [LCL谐振危险] LCL 滤波器谐振频率 ({f_res:.1f} Hz) 不在推荐安全区间 (控制带宽 {fc_khz*1000*0.5:.1f}Hz 与开关频率一半 {req.fsw_khz*1000*0.5:.1f}Hz 之间)，系统易发生高频振荡振铃！")
                
        # 结温过高预警 (基于单管损耗的一维热阻粗估，假设 heatsink 热阻 1.5 C/W)
        t_ambient = 50.0
        r_th_heatsink = 1.5
        # 估算单个主管结温
        p_loss_main_single = calcs['p_con_main'] + calcs['p_sw_main']
        t_j_main = t_ambient + p_loss_main_single * (0.85 + r_th_heatsink) # 假设 Rjc = 0.85
        if t_j_main > 125.0:
            drc_warnings.append(f"❌ [外侧主管结温过高] 估算的主功率开关管结温 ({t_j_main:.1f} °C) 超过 125 °C 工业安全阈值！请选用更低 Rds(on) 的器件或改善散热风道环境！")
            
        p_loss_mid_single = calcs['p_con_mid'] + calcs['p_sw_mid']
        t_j_mid = t_ambient + p_loss_mid_single * (1.2 + r_th_heatsink) # 假设 Rjc = 1.2
        if t_j_mid > 125.0:
            drc_warnings.append(f"❌ [中点开关管结温过高] 估算的中点钳位管结温 ({t_j_mid:.1f} °C) 超过 125 °C 工业安全阈值！请考虑增大并联或提高风速！")
            
        return {
            "design": calcs,
            "simulation": sim_res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


from typing import List

class OutputChannelSpec(BaseModel):
    v_out: float
    i_out: float
    v_d: float = 0.6

class MultiOutputAuxCalcRequest(BaseModel):
    vin_min: float
    vin_nom: float
    vin_max: float
    fsw_khz: float
    v_or: float = 80.0
    ns1_ref: int = 10
    j_density: float = 4.0
    k_fill: float = 0.3
    delta_b: float = 0.2
    outputs: List[OutputChannelSpec]

@app.post("/api/calculate/multi_output_aux")
def calculate_multi_output_aux(req: MultiOutputAuxCalcRequest):
    try:
        # 将 outputs 列表转换为 dict 形式，以传递给后端函数
        outputs_list = [{"v_out": out.v_out, "i_out": out.i_out, "v_d": out.v_d} for out in req.outputs]
        
        calcs = calc_multi_output_aux(
            vin_min=req.vin_min,
            vin_nom=req.vin_nom,
            vin_max=req.vin_max,
            fsw_khz=req.fsw_khz,
            outputs=outputs_list,
            v_or=req.v_or,
            ns1_ref=req.ns1_ref,
            j_density=req.j_density,
            k_fill=req.k_fill,
            delta_b=req.delta_b
        )
        return calcs
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DabCalcRequest(BaseModel):
    vin_min: float
    vin_nom: float
    vin_max: float
    vout: float
    iout: float
    fsw_khz: float
    turns_ratio: float
    l_leakage_uh: float
    phase_shift_d: float = 0.15
    mod_mode: str = "SPS"
    d1: float = 0.0
    d3: float = 0.0
    eff: float = 0.94

@app.post("/api/calculate/dab")
def calculate_dab(req: DabCalcRequest):
    try:
        # 1. 基础物理参数计算
        calcs = calc_dab_converter(
            vin_min=req.vin_min,
            vin_nom=req.vin_nom,
            vin_max=req.vin_max,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            turns_ratio=req.turns_ratio,
            l_leakage_uh=req.l_leakage_uh,
            phase_shift_d=req.phase_shift_d
        )
        
        # 2. 时域解析仿真波形
        sim_res = solve_dab_time_domain(
            vin=req.vin_nom,
            vout=req.vout,
            fsw_khz=req.fsw_khz,
            l_leakage_uh=req.l_leakage_uh,
            turns_ratio=req.turns_ratio,
            mod_mode=req.mod_mode,
            d1=req.d1,
            d2=req.phase_shift_d,
            d3=req.d3
        )
        
        # 注入高频时域仿真所得到的有效值应力与实际峰值应力
        calcs['i_rms_pri'] = sim_res['i_rms']
        calcs['i_rms_sec'] = sim_res['i_rms'] * req.turns_ratio
        calcs['i_sw_rms_pri'] = sim_res['i_rms'] / math.sqrt(2.0)
        calcs['i_sw_rms_sec'] = calcs['i_rms_sec'] / math.sqrt(2.0)
        calcs['i_d_max'] = sim_res['i_pk']
        calcs['i_d_max_sec'] = sim_res['i_pk'] * req.turns_ratio

        # 3. DRC 校验
        drc_warnings = []
        if not sim_res['zvs_ok']:
            drc_warnings.append("⚠️ [轻载下失效 ZVS 开关特性] 当前有功功率及移相配置下，主开关管无法实现零电压软开关 (ZVS)，将增加高频开关损耗与 EMI 噪声。")
        if req.l_leakage_uh > calcs['l_min_uh'] * 2.0:
            drc_warnings.append(f"⚠️ [漏感感值偏大] 实际漏电感值 ({req.l_leakage_uh:.1f} uH) 显著大于 SPS 额定最大电感限制 ({calcs['l_min_uh']:.2f} uH)，这会导致无法输出所需的标称额定功率，系统处于欠额工作状态！")
            
        # 补全系统损耗与热阻核算
        p_loss = req.vout * req.iout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")
            
        return {
            "design": calcs,
            "simulation": sim_res,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class DabOptimizeRequest(BaseModel):
    vin: float
    vout: float
    pout_target: float
    fsw_khz: float
    turns_ratio: float
    l_leakage_uh: float
    mod_mode: str = "EPS"

@app.post("/api/calculate/dab_optimize")
def optimize_dab(req: DabOptimizeRequest):
    try:
        d1, d2, d3 = solve_optimal_phase_shift(
            vin=req.vin,
            vout=req.vout,
            pout_target=req.pout_target,
            fsw_khz=req.fsw_khz,
            turns_ratio=req.turns_ratio,
            l_leakage_uh=req.l_leakage_uh,
            mod_mode=req.mod_mode
        )
        return {
            "d1": d1,
            "d2": d2,
            "d3": d3
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CllcCalcRequest(BaseModel):
    vin_min: float
    vin_nom: float
    vin_max: float
    vout: float
    iout: float
    fr_khz: float
    turns_ratio: float
    ln_ratio: float
    q_factor: float
    fsw_khz: float
    eff: float = 0.94

@app.post("/api/calculate/cllc")
def calculate_cllc(req: CllcCalcRequest):
    try:
        calcs = calc_cllc_converter(
            vin_min=req.vin_min,
            vin_nom=req.vin_nom,
            vin_max=req.vin_max,
            vout=req.vout,
            iout=req.iout,
            fr_khz=req.fr_khz,
            turns_ratio=req.turns_ratio,
            ln_ratio=req.ln_ratio,
            q_factor=req.q_factor,
            fsw_khz=req.fsw_khz
        )
        
        # DRC 校验
        drc_warnings = []
        nom_gain_req = req.vout * req.turns_ratio / req.vin_nom
        gain_diff = abs(calcs['gain'] - nom_gain_req) / max(0.1, nom_gain_req)
        if gain_diff > 0.15:
            drc_warnings.append(f"⚠️ [增益偏离警告] CLLC 谐振槽在当前开关频率下的增益 ({calcs['gain']:.3f}) 与标称电压变比增益 ({nom_gain_req:.3f}) 偏离大于 15%。系统可能会在此工作频率下产生严重的无功回流 and 环流损耗，请核对 fr 与 fsw 的配置。")
            
        # 补全系统损耗与热阻核算
        p_loss = req.vout * req.iout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")
            
        return {
            "design": calcs,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class MagneticIntegrationRequest(BaseModel):
    turns_p: float
    turns_s: float
    l_w_mm: float
    b_w_mm: float
    delta_mm: float
    h_p_mm: float
    h_s_mm: float
    fsw_khz: float
    d_litz_mm: float
    layers: float
    lg_mm: float
    d_gap_dist_mm: float
    i_rms_a: float
    winding_type: str = "Concentric"
    h_w_mm: float = 20.0
    d_sec_mm: float = 2.0
    wp_mm: float = 10.0
    ws_mm: float = 10.0

@app.post("/api/calculate/dab_cllc_magnetic")
def calculate_magnetic(req: MagneticIntegrationRequest):
    try:
        calcs = calc_dab_cllc_magnetic_integration(
            turns_p=req.turns_p,
            turns_s=req.turns_s,
            l_w_mm=req.l_w_mm,
            b_w_mm=req.b_w_mm,
            delta_mm=req.delta_mm,
            h_p_mm=req.h_p_mm,
            h_s_mm=req.h_s_mm,
            fsw_khz=req.fsw_khz,
            d_litz_mm=req.d_litz_mm,
            layers=req.layers,
            lg_mm=req.lg_mm,
            d_gap_dist_mm=req.d_gap_dist_mm,
            i_rms_a=req.i_rms_a,
            winding_type=req.winding_type,
            h_w_mm=req.h_w_mm,
            d_sec_mm=req.d_sec_mm,
            wp_mm=req.wp_mm,
            ws_mm=req.ws_mm
        )
        
        # DRC 校验
        drc_warnings = []
        if calcs['fringing_flux_warning']:
            drc_warnings.append(f"⚠️ [变压器边缘场磁通涡流发热危险] 导线距离气隙的距离 {req.d_gap_dist_mm:.1f} mm 小于安全边缘距离限制 {calcs['min_safe_dist_mm']:.1f} mm (三倍气隙宽度 lg)，且气隙边缘涡流损耗预测达 {calcs['p_fringing_loss']:.2f} W。这会在紧邻气隙的利兹线圈中产生剧烈的局部高频过热，甚至熔毁绝缘，请务必增大绕组到气隙的间距或优化气隙结构！")
            
        return {
            "design": calcs,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SnubberEstimateRequest(BaseModel):
    coss_pf: float
    l_loop_nh: float
    vin: float
    fsw_khz: float
    ipk: float
    vds_rating: float
    pin_w: float
    r_snub: float
    c_snub: float
    v_swing: Optional[float] = None

@app.post("/api/calculate/snubber/estimate")
def calculate_snubber_estimate(req: SnubberEstimateRequest):
    try:
        calcs = calc_snubber_overshoot_efficiency(
            vin=req.vin,
            ipk=req.ipk,
            coss_pf=req.coss_pf,
            l_loop_nh=req.l_loop_nh,
            vds_rating=req.vds_rating,
            r_snub_ohm=req.r_snub,
            c_snub_pf=req.c_snub,
            p_in_w=req.pin_w,
            fsw_khz=req.fsw_khz,
            v_swing=req.v_swing
        )
        
        # DRC
        drc_warnings = []
        if calcs['v_max_no_snub'] > req.vds_rating:
            drc_warnings.append(f"⚠️ [无阻尼电压过冲危险] 未加吸收时 MOSFET 漏源电压过冲 ({calcs['v_max_no_snub']:.1f} V) 将超过器件额定耐压 ({req.vds_rating:.1f} V)！建议务必并联 RC 吸收电路，以防止关断瞬态发生过压击穿！")
        if calcs['v_max_with_snub'] > req.vds_rating:
            drc_warnings.append(f"❌ [吸收后电压仍超标警告] 并联 RC 吸收后，估算最大电压尖峰仍达 {calcs['v_max_with_snub']:.1f} V，超出了器件额定耐压 {req.vds_rating:.1f} V！请更换耐压更高的 MOSFET，或减小回路寄生电感 L_loop (优化 PCB 紧凑布局)！")
        if abs(calcs['delta_eff_pct']) > 0.5:
            drc_warnings.append(f"⚠️ [效率跌落过大] 吸收电路产生高频功耗 {calcs['p_snub_loss_w']:.2f} W，导致整机效率损失达 {abs(calcs['delta_eff_pct']):.3f}%。建议适当减小 C_snub 或提高电阻阻值以权衡效率与过冲抑制效果。")
            
        # 补全前端渲染所需的推荐 R/C 参数
        calcs['r_snub_ohm'] = float(req.r_snub)
        calcs['c_snub_pf'] = float(req.c_snub)
        
        return {
            "design": calcs,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SnubberMeasureRequest(BaseModel):
    f_ring_mhz: float
    c_add_pf: float
    f_shift_mhz: float
    vin: float
    fsw_khz: float
    ipk: float
    vds_rating: float
    pin_w: float
    v_swing: Optional[float] = None

@app.post("/api/calculate/snubber/measure")
def calculate_snubber_measure(req: SnubberMeasureRequest):
    try:
        calcs = calc_snubber_measure(
            f_ring_mhz=req.f_ring_mhz,
            c_add_pf=req.c_add_pf,
            f_shift_mhz=req.f_shift_mhz,
            vin=req.vin,
            fsw_khz=req.fsw_khz,
            ipk=req.ipk,
            vds_rating=req.vds_rating,
            pin_w=req.pin_w,
            v_swing=req.v_swing
        )
        
        # DRC
        drc_warnings = []
        details = calcs['overshoot_details']
        if details['v_max_no_snub'] > req.vds_rating:
            drc_warnings.append(f"⚠️ [测量推算: 无阻尼过冲危险] 依据实测寄生参数推算，未加吸收时主管关断电压尖峰达 {details['v_max_no_snub']:.1f} V，已超过开关管耐压 ({req.vds_rating:.1f} V)！建议务必按推荐参数并联 RC 吸收焊盘！")
        if details['v_max_with_snub'] > req.vds_rating:
            drc_warnings.append(f"❌ [测量推算: 阻尼后过压危险] 即使并联了吸收 RC，关断尖峰仍达 {details['v_max_with_snub']:.1f} V。寄生电感 L_p ({calcs['l_p_nh']:.1f} nH) 偏大，请更换更高耐压的管子，或重新布板优化回路寄生电感！")
        if abs(details['delta_eff_pct']) > 0.5:
            drc_warnings.append(f"⚠️ [实测吸收效率影响] 吸收电阻产生的损耗达 {details['p_snub_loss_w']:.2f} W，效率下降 {abs(details['delta_eff_pct']):.3f}%，建议高效率应用中轻微上调吸收阻值。")
            
        return {
            "design": calcs,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RcdCalcRequest(BaseModel):
    l_lk_uh: float
    ipk: float
    vor: float
    fsw_khz: float
    v_spike: float
    ripple_pct: float = 0.1
    vin: float = 0.0
    vds_rating: float = 0.0

@app.post("/api/calculate/snubber/rcd")
def calculate_rcd(req: RcdCalcRequest):
    try:
        calcs = calc_rcd_parameters(
            l_lk_uh=req.l_lk_uh,
            ipk=req.ipk,
            vor=req.vor,
            fsw_khz=req.fsw_khz,
            v_spike=req.v_spike,
            ripple_pct=req.ripple_pct
        )
        
        # DRC
        drc_warnings = []
        if req.vin > 0 and req.vds_rating > 0:
            total_stress = req.vin + calcs['v_clamp']
            if total_stress > req.vds_rating:
                drc_warnings.append(f"❌ [RCD钳位过压击穿危险] 反激主管关断承受总峰值电压 ({total_stress:.1f} V) 已超过 MOSFET 额定耐压 ({req.vds_rating:.1f} V)！会发生瞬间击穿，请务必调小 V_spike（会增加钳位阻容功耗发热）或选用更高耐压的 MOSFET 管！")
            elif total_stress > req.vds_rating * 0.9:
                drc_warnings.append(f"⚠️ [耐压裕量过小预警] 总关断应力 ({total_stress:.1f} V) 已超过 MOSFET 耐压限值 ({req.vds_rating:.1f} V) 的 90%。反激漏感震荡可能在主管上产生未被 RCD 完全吸收的极窄电压毛刺，容易导致器件雪崩烧毁，建议留有 1.2 倍裕量！")
                
        return {
            "design": calcs,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CoDesignCalcRequest(BaseModel):
    vbus: float
    pout: float
    pfc_c_uf: float
    pfc_esr_mohm: float
    dcdc_c_uf: float
    dcdc_esr_mohm: float
    pfc_fc_v: float = 10.0

@app.post("/api/calculate/codesign")
def calculate_codesign(req: CoDesignCalcRequest):
    try:
        calcs = calc_cascade_impedance_stability(
            vbus=req.vbus,
            pout=req.pout,
            pfc_c_uf=req.pfc_c_uf,
            pfc_esr_mohm=req.pfc_esr_mohm,
            dcdc_c_uf=req.dcdc_c_uf,
            dcdc_esr_mohm=req.dcdc_esr_mohm,
            pfc_fc_v=req.pfc_fc_v
        )
        
        # DRC
        drc_warnings = []
        if calcs['status'] == "Unstable":
            drc_warnings.append(f"❌ [Middlebrook 失稳严重警告] 系统级联稳定性核算显示阻抗匹配不合格 (裕量为 {calcs['min_margin']:.2f} dB，小于 0dB 且有交越点)！可能会由于前级输出阻抗和后级负阻特性相互作用发生严重高频自激振荡，请增大前级输出电容、降低电容ESR，或减小后级输入电容！")
        elif calcs['status'] == "Marginal":
            drc_warnings.append(f"⚠️ [级联临界稳定警告] 级联阻抗匹配裕量为 {calcs['min_margin']:.2f} dB (小于推荐 of 3.0 dB)。在电网起伏或大负载跳变时容易发生暂态振荡，建议提高 PFC 电压环带宽或优化前级输出电容参数！")

        from backend.formula import calc_cascade_stability
        stability_res = calc_cascade_stability(
            pfc_vbus=req.vbus,
            pfc_pout=req.pout,
            pfc_cout_uf=req.pfc_c_uf,
            pfc_fc_hz=req.pfc_fc_v,
            dcdc_cin_uf=req.dcdc_c_uf,
            dcdc_cin_esr_mohm=req.dcdc_esr_mohm,
            dcdc_fc_khz=3.0
        )
            
        return {
            "design": calcs,
            "stability_analysis": stability_res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PsfbCalcRequest(BaseModel):
    vin_min: float
    vin_nom: float
    vin_max: float
    vout: float
    iout: float
    fsw_khz: float
    turns_ratio: float
    lr_uh: float
    llk_uh: float
    lo_uh: float
    co_uf: float
    rc_esr_mohm: float
    coss_pf: float
    tdead_ns: float
    ae: float
    b_peak: float
    eff: float = 0.94

@app.post("/api/calculate/psfb")
def calculate_psfb(req: PsfbCalcRequest):
    try:
        # 1. 基础物理参数计算
        calcs = calc_psfb_converter(
            vin_min=req.vin_min,
            vin_nom=req.vin_nom,
            vin_max=req.vin_max,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            turns_ratio=req.turns_ratio,
            lr_uh=req.lr_uh,
            llk_uh=req.llk_uh,
            lo_uh=req.lo_uh,
            co_uf=req.co_uf,
            coss_pf=req.coss_pf
        )
        
        # 2. 变压器原副边匝数计算 (Ae, B_peak)
        fsw_hz = req.fsw_khz * 1000.0
        np_val = (req.vout * req.turns_ratio) / (4.0 * fsw_hz * req.ae * 1e-6 * req.b_peak) if (fsw_hz * req.ae * req.b_peak > 0) else 0.0
        np_calc = math.ceil(np_val) if np_val > 0 else 0
        ns_calc = math.ceil(np_calc / req.turns_ratio) if (np_calc > 0 and req.turns_ratio > 0) else 0
        
        calcs['np_calc'] = np_calc
        calcs['ns_calc'] = ns_calc
        
        # 3. 时域仿真
        time_res = simulate_psfb_time_domain(
            vin_nom=req.vin_nom,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            turns_ratio=req.turns_ratio,
            lr_uh=req.lr_uh,
            llk_uh=req.llk_uh,
            lo_uh=req.lo_uh,
            co_uf=req.co_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            d_nom=calcs['d_nom'],
            d_eff=calcs['d_eff_nom'],
            delta_il=calcs['delta_il']
        )
        
        # 4. Bode 扫频仿真
        bode_res = simulate_psfb_bode(
            vin_nom=req.vin_nom,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            turns_ratio=req.turns_ratio,
            lr_uh=req.lr_uh,
            llk_uh=req.llk_uh,
            lo_uh=req.lo_uh,
            co_uf=req.co_uf,
            rc_esr_mohm=req.rc_esr_mohm
        )
        
        # DRC 校验
        drc_warnings = []
        
        # 占空比丢失校验
        if calcs['delta_d_nom'] > 0.15:
            drc_warnings.append(f"⚠️ [占空比丢失过大] 当前标称占空比丢失达到 {calcs['delta_d_nom']*100:.1f}%，这将大幅压缩有效输出电压摆幅。建议增大变压器匝比，或者减小谐振电感 Lr/变压器漏感 Llk。")
            
        # ZVS 状态校验
        if not calcs['zvs_achieved']:
            drc_warnings.append(f"🔴 [ZVS 软开关失败] 滞后桥臂 MOSFET 在当前电感储能不足以放电 Coss 能量 (Lr={req.lr_uh+req.llk_uh:.1f}uH, Coss={req.coss_pf:.1f}pF)！这会导致严重的硬开关损耗和 EMI 干扰，建议增大外加谐振电感 Lr 或优选 Coss 较小的开关管。")
            
        # 纹波率校验
        lir = calcs['delta_il'] / req.iout if req.iout > 0 else 0.0
        if lir < 0.1:
            drc_warnings.append("LIR 纹波系数过低 (<10%)：输出电流极其平滑，但会导致次边滤波电感体积与成本呈指数级上升。")
        elif lir > 0.4:
            drc_warnings.append("⚠️ LIR 纹波系数过高 (>40%)：电感电流纹波大，磁芯与导线高频损耗激增，存在磁饱和风险。建议增大 Lo 感值。")
            
        # 死区时间校验
        if req.tdead_ns < calcs['t_req_ns']:
            drc_warnings.append(f"🔴 [死区时间不足] 当前死区设置 ({req.tdead_ns:.1f} ns) 小于 ZVS 抽头所需最小死区时间 ({calcs['t_req_ns']:.1f} ns)，桥臂开关管可能发生直通短路烧毁，请增大死区时间！")
            
        # 补全散热与系统损耗核算
        p_loss = req.vout * req.iout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            drc_warnings.append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")
            
        return {
            "design": calcs,
            "time_domain": time_res,
            "bode": bode_res,
            "drc_warnings": drc_warnings,
            "p_loss": p_loss,
            "r_th_hs": r_th_hs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class TrapCalcRequest(BaseModel):
    d: float
    imax: float
    imin: float

@app.post("/api/calculate/waveform_rms/trap")
def calculate_trap(req: TrapCalcRequest):
    try:
        if req.d < 0 or req.d > 1:
            raise ValueError("占空比 D 必须在 0 ~ 1 之间")
        if req.imax < req.imin:
            raise ValueError("峰值电流 Imax 不能小于谷值电流 Imin")
        res = calc_trap_waveform(req.d, req.imax, req.imin)
        drc_warnings = []
        if req.imin < 0:
            drc_warnings.append("⚠️ 谷值电流 Imin < 0，电路中可能存在反向电流或不连续导通 (DCM) 趋势。")
        return {
            "design": res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DcmCalcRequest(BaseModel):
    d1: float
    d2: float
    ipk: float

@app.post("/api/calculate/waveform_rms/dcm")
def calculate_dcm(req: DcmCalcRequest):
    try:
        if req.d1 < 0 or req.d2 < 0 or (req.d1 + req.d2) <= 0 or (req.d1 + req.d2) > 1:
            raise ValueError("上升与下降占空比之和 (D1+D2) 必须大于 0 且不能超过 1")
        res = calc_dcm_waveform(req.d1, req.d2, req.ipk)
        
        # DRC
        drc_warnings = []
        if (req.d1 + req.d2) > 0.95:
            drc_warnings.append("⚠️ 占空比之和 (D1+D2) 过于接近 1，电路可能工作在临界导通模式 (BCM) 或进入连续导通模式 (CCM)，请留有一定的死区裕量。")
            
        return {
            "design": res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RectCalcRequest(BaseModel):
    ipk: float
    d: float

@app.post("/api/calculate/waveform_rms/rect")
def calculate_rect(req: RectCalcRequest):
    try:
        if req.d < 0 or req.d > 1:
            raise ValueError("占空比 D 必须在 0 ~ 1 之间")
        res = calc_rect_waveforms(req.ipk, req.d)
        return {
            "design": res,
            "drc_warnings": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SineCalcRequest(BaseModel):
    ipk: float
    alpha_deg: float

@app.post("/api/calculate/waveform_rms/sine")
def calculate_sine(req: SineCalcRequest):
    try:
        if req.alpha_deg < 0 or req.alpha_deg > 180:
            raise ValueError("触发角 alpha 必须在 0 ~ 180 度之间")
        res = calc_sine_waveforms(req.ipk, req.alpha_deg)
        return {
            "design": res,
            "drc_warnings": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DecoupleCalcRequest(BaseModel):
    total: float
    avg: float

@app.post("/api/calculate/waveform_rms/decouple")
def calculate_decouple(req: DecoupleCalcRequest):
    try:
        if req.total < 0 or req.avg < 0:
            raise ValueError("输入参数必须大于 0")
        if req.avg > req.total:
            raise ValueError("直流平均值 (AVG) 不能大于总有效值 (Total RMS)")
        res = calc_decouple_waveform(req.total, req.avg)
        return {
            "design": res,
            "drc_warnings": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RippleCalcRequest(BaseModel):
    ip: float
    delta: float

@app.post("/api/calculate/waveform_rms/ripple")
def calculate_ripple(req: RippleCalcRequest):
    try:
        if req.ip < 0 or req.delta < 0:
            raise ValueError("输入参数必须大于 0")
        res = calc_ripple_waveform(req.ip, req.delta)
        return {
            "design": res,
            "drc_warnings": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RelayRcRequest(BaseModel):
    vcc: float
    r_coil: float
    v_hold: float
    v_min: float
    t_pull_ms: float

@app.post("/api/calculate/relay_driver/rc")
def calculate_relay_rc(req: RelayRcRequest):
    try:
        res = calculate_rc_economizer(
            vcc=req.vcc,
            r_coil=req.r_coil,
            v_hold=req.v_hold,
            v_min=req.v_min,
            t_pull_ms=req.t_pull_ms
        )
        
        # DRC
        drc_warnings = []
        # 若 V_hold 离 V_min 过近或 V_min 离 Vcc 过近
        if req.v_min >= req.vcc * 0.9:
            drc_warnings.append("⚠️ 最小吸合电压 (V_pull_min) 过于接近电源电压 Vcc (>=90%)，在电源电压轻微起伏波动时可能会导致吸合失败，请增大 Vcc 或改用更低额定电压的继电器线圈！")
        if req.v_hold < req.vcc * 0.3:
            drc_warnings.append("⚠️ 目标保持电压 (V_hold) 偏低 (<30% Vcc)。虽然能节省更多功耗，但在设备受到机械振动冲击时很容易发生接触器衔铁松动或异常释放，建议取 40% ~ 50% 额定电压。")
        if res['c_start_uf'] > 1000:
            drc_warnings.append(f"⚠️ 计算出的启动电容 C_start ({res['c_start_uf']:.1f} uF) 过大，在 PCB 板卡上体积和成本较高。请优化线圈参数，或者选用启动时间更短的继电器型号。")
            
        design_mapped = {
            "r_eco_ohm": res["r_eco_ohm"],
            "c_eco_uf": res["c_start_uf"],
            "power_saved_pct": res["power_saving_pct"],
            "c_start_uf": res["c_start_uf"],
            "power_saving_pct": res["power_saving_pct"],
            "p_r_eco_w": res["p_r_eco_w"],
            "p_orig_w": res["p_orig_w"],
            "p_new_w": res["p_new_w"]
        }
        return {
            "design": design_mapped,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RelayPwmRequest(BaseModel):
    vcc: float
    r_coil: float
    l_coil_mh: float
    f_pwm_khz: float
    v_hold: float

@app.post("/api/calculate/relay_driver/pwm")
def calculate_relay_pwm(req: RelayPwmRequest):
    try:
        if req.l_coil_mh <= 0:
            raise ValueError("线圈电感值必须严格大于 0 mH")
        if req.f_pwm_khz <= 0:
            raise ValueError("PWM 频率必须严格大于 0 kHz")
        res = calculate_pwm_holding(
            vcc=req.vcc,
            r_coil=req.r_coil,
            l_coil_mh=req.l_coil_mh,
            f_pwm_khz=req.f_pwm_khz,
            v_hold=req.v_hold
        )
        
        # DRC
        drc_warnings = []
        if req.f_pwm_khz < 20.0:
            drc_warnings.append("⚠️ PWM 驱动频率低于 20kHz。这处于人耳听力范围内 (20Hz~20kHz)，可能会引起线圈在交变电磁力作用下产生刺耳的尖叫或啸叫声，建议将频率提高到 20kHz 以上。")
        if res['ripple_pct'] > 100.0:
            drc_warnings.append(f"❌ 电流纹波百分比过高 ({res['ripple_pct']:.1f}%)，电感电流已处于严重断续 (DCM) 状态！容易在续流二极管断开期间因为磁通减小导致衔铁松动、打火或异常脱扣，请显著提高 PWM 频率或增大串联扼流电感！")
        elif res['ripple_pct'] > 30.0:
            drc_warnings.append(f"⚠️ 电流纹波偏高 ({res['ripple_pct']:.1f}%)，线圈磁力会随纹波波动，有潜在的微小异响，建议控制纹波在 30% 以内。")
            
        design_mapped = {
            "holding_duty": res["duty_pct"] / 100.0,
            "current_ripple_ma": res["ripple_ma"],
            "power_diss_w": res["p_hold_w"],
            "duty_pct": res["duty_pct"],
            "ripple_ma": res["ripple_ma"],
            "p_hold_w": res["p_hold_w"],
            "i_avg_ma": res["i_avg_ma"],
            "ripple_pct": res["ripple_pct"]
        }
        return {
            "design": design_mapped,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LdoThermalRequest(BaseModel):
    vin: float
    vout: float
    iout: float
    iq: float
    rja: float
    ta: float

@app.post("/api/calculate/ldo_thermal")
def calculate_ldo_thermal_route(req: LdoThermalRequest):
    try:
        if req.vin <= req.vout:
            raise ValueError("输入电压 Vin 必须严格大于输出电压 Vout")
        res = calculate_ldo_thermal(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            iq=req.iq,
            rja=req.rja,
            ta=req.ta
        )
        
        # DRC
        drc_warnings = []
        tj = res['t_j']
        if tj >= 150.0:
            drc_warnings.append("❌ [芯片熔毁严重警告] 结温已超过绝对最大额定值 (Abs Max, >=150°C)！芯片会由于热过载瞬间烧毁，或者频繁触发过热关断保护停机！请极大增加敷铜散热面积、降低环境温度，或将拓扑更换为 DC-DC 降压开关芯片！")
        elif tj >= 125.0:
            drc_warnings.append("⚠️ [高结温警告] 芯片结温超过 125°C 的高可靠性运行上限。虽然可能不至于立即烧毁，但长期在此高温下运行会导致半导体载流子迁移率失真且寿命发生指数级衰减，请增加 PCB 散热片敷铜！")
        elif tj >= 100.0:
            drc_warnings.append("⚠️ [注意] 芯片结温较高 (100°C ~ 125°C)，外壳表面会极度烫手 (可能会有触碰烫伤隐患)，请做好机械防接触栏栅。")
            
        p_diss = res['p_diss_w']
        if p_diss > 1.5 and req.rja > 50.0:
            drc_warnings.append(f"⚠️ [大功耗警告] 当前 LDO 总散热功耗达 {p_diss:.2f} W，对于缺少大散热铜皮的普通贴片封装 (如 SOT-223) 的温升极快。极度推荐使用大散热焊盘敷铜来降低 θ_JA 阻抗值！")
            
        return {
            "design": res,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LdoPcbCopperRequest(BaseModel):
    area_cm2: float
    copper_oz: float
    theta_jc: float

@app.post("/api/calculate/ldo_thermal/pcb_copper")
def calculate_ldo_pcb_copper(req: LdoPcbCopperRequest):
    try:
        res = estimate_pcb_copper_rth(
            area_cm2=req.area_cm2,
            copper_oz=req.copper_oz,
            theta_jc=req.theta_jc
        )
        return {
            "design": res,
            "drc_warnings": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# Control Loop Compensation API
# ==============================================================================

class Type2CompRequest(BaseModel):
    vout: float
    iout: float
    cout_uf: float
    esr_mohm: float
    fsw_khz: float
    ri: float
    fc_khz: float
    pm_target: float
    vref: float
    r1_k: float
    digital_delay_on: Optional[bool] = False
    fs_khz: Optional[float] = None

@app.post("/api/calculate/loop_compensation/type2")
@app.post("/api/calculate/loop/type2")
def calculate_loop_type2(req: Type2CompRequest):
    try:
        design = calculate_type2_loop(
            vout=req.vout, iout=req.iout, cout_uf=req.cout_uf, esr_mohm=req.esr_mohm,
            fsw_khz=req.fsw_khz, ri=req.ri, fc_khz=req.fc_khz, pm_target=req.pm_target,
            vref=req.vref, r1_k=req.r1_k
        )
        bode = simulate_type2_loop_bode(
            vout=req.vout, iout=req.iout, cout_uf=req.cout_uf, esr_mohm=req.esr_mohm,
            fsw_khz=req.fsw_khz, ri=req.ri, r1_k=req.r1_k,
            r3_val=design['r3_ohm'], c1_val=design['c1_f'], c2_val=design['c2_f'],
            digital_delay_on=req.digital_delay_on or False, fs_khz=req.fs_khz
        )
        step = simulate_type2_loop_step(
            vout=req.vout, iout=req.iout, cout_uf=req.cout_uf, esr_mohm=req.esr_mohm,
            ri=req.ri, r1_k=req.r1_k,
            r3_val=design['r3_ohm'], c1_val=design['c1_f'], c2_val=design['c2_f']
        )
        
        # DRC 校验
        drc_warnings = []
        if req.fc_khz >= req.fsw_khz / 5.0:
            drc_warnings.append(f"❌ [穿越频率过高] 目标穿越频率 fc ({req.fc_khz:.1f} kHz) 设置偏高（已达 1/5 开关频率）。在实际电路中极易受高频开关纹波与噪声干扰，导致 system 脉宽发生大小波抖动，甚至反馈失控！")
        elif req.fc_khz >= req.fsw_khz / 10.0:
            drc_warnings.append(f"⚠️ [穿越频率偏高] 目标穿越频率 fc ({req.fc_khz:.1f} kHz) 偏大（大于 1/10 开关频率）。请务必注意环路高频降噪和采样延迟对相位裕度的扣减影响。")
            
        pm = bode['pm_deg']
        if pm < 45.0:
            drc_warnings.append(f"❌ [相位裕度低自激风险] 仿真环路相位裕度仅为 {pm:.1f}°，低于电力电子行业 45° 的安全下限！系统在突加减负载时会发生剧烈的震荡，甚至导致系统自激损毁，请降低目标 fc！")
        elif pm > 85.0:
            drc_warnings.append(f"⚠️ [相位裕度偏大] 仿真相位裕度高达 {pm:.1f}°。这虽然能保证系统的绝对平稳性，但由于阻尼过大，瞬态响应的电压恢复过程会变得异常迟缓。")
            
        return {
            "design": design,
            "bode": bode,
            "step": step,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class Type3CompRequest(BaseModel):
    l_uh: float
    cout_uf: float
    esr_mohm: float
    vin: float
    vramp: float
    fsw_khz: float
    fc_khz: float
    pm_target: float
    r1_k: float
    vref: float
    vout: float
    digital_delay_on: Optional[bool] = False
    fs_khz: Optional[float] = None

@app.post("/api/calculate/loop_compensation/type3")
@app.post("/api/calculate/loop/type3")
def calculate_loop_type3(req: Type3CompRequest):
    try:
        if req.vramp <= 0 or req.vin <= 0:
            raise ValueError("锯齿波幅值 Vramp 与 输入电压 Vin 必须大于 0")
        design = calculate_type3_loop(
            l_uh=req.l_uh, cout_uf=req.cout_uf, esr_mohm=req.esr_mohm, vin=req.vin,
            vramp=req.vramp, fsw_khz=req.fsw_khz, fc_khz=req.fc_khz, pm_target=req.pm_target,
            r1_k=req.r1_k, vref=req.vref, vout=req.vout
        )
        bode = simulate_type3_loop_bode(
            l_uh=req.l_uh, cout_uf=req.cout_uf, esr_mohm=req.esr_mohm, vin=req.vin,
            vramp=req.vramp, fsw_khz=req.fsw_khz, r1_k=req.r1_k,
            r3_val=design['r3_ohm'], c1_val=design['c1_f'], c2_val=design['c2_f'], c3_val=design['c3_f'],
            digital_delay_on=req.digital_delay_on or False, fs_khz=req.fs_khz
        )
        step = simulate_type3_loop_step(
            l_uh=req.l_uh, cout_uf=req.cout_uf, esr_mohm=req.esr_mohm, vin=req.vin,
            vramp=req.vramp, r1_k=req.r1_k,
            r3_val=design['r3_ohm'], c1_val=design['c1_f'], c2_val=design['c2_f'], c3_val=design['c3_f']
        )
        
        # DRC
        drc_warnings = []
        if req.fc_khz >= req.fsw_khz / 5.0:
            drc_warnings.append(f"❌ [穿越频率过高] 目标穿越频率 fc ({req.fc_khz:.1f} kHz) 设置偏高（已达 1/5 开关频率）。在高占空比或剧烈开关噪环境下，环路极易自激！")
        elif req.fc_khz >= req.fsw_khz / 10.0:
            drc_warnings.append(f"⚠️ [穿越频率偏高] 目标穿越频率 fc ({req.fc_khz:.1f} kHz) 偏大。建议控制在 1/10 开关频率内以换取更安全的降噪能力。")
            
        pm = bode['pm_deg']
        if pm < 45.0:
            drc_warnings.append(f"❌ [相位裕度低自激风险] 仿真环路相位裕度仅为 {pm:.1f}°，低于 45° 稳定红线！请适当调低 fc 并优化零极点位置！")
        elif pm > 85.0:
            drc_warnings.append(f"⚠️ [相位裕度偏大] 相位裕度达 {pm:.1f}°，动态恢复时间会偏慢。")
            
        return {
            "design": design,
            "bode": bode,
            "step": step,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class Tl431LoopRequest(BaseModel):
    vout: float
    r_up_k: float
    fc_khz: float
    pm_deg: float
    gain_db: float
    fp_opto_khz: float

@app.post("/api/calculate/loop_compensation/tl431")
@app.post("/api/calculate/loop/tl431")
def calculate_loop_tl431(req: Tl431LoopRequest):
    try:
        design = calculate_tl431_loop(
            vout=req.vout, r_up_k=req.r_up_k, fc_khz=req.fc_khz, pm_deg=req.pm_deg,
            gain_db=req.gain_db, fp_opto_khz=req.fp_opto_khz
        )
        bode = simulate_tl431_loop_bode(
            vout=req.vout, r_up_k=req.r_up_k, fc_khz=req.fc_khz, fp_opto_khz=req.fp_opto_khz,
            gain_db=req.gain_db, r_comp=design['r_comp_ohm'], c_comp=design['c_comp_f'], c_hf=design['c_hf_f']
        )
        step = simulate_tl431_loop_step(
            r_up_k=req.r_up_k, r_comp=design['r_comp_ohm'], c_comp=design['c_comp_f'], c_hf=design['c_hf_f'],
            fp_opto_khz=req.fp_opto_khz, fc_khz=req.fc_khz, gain_db=req.gain_db
        )
        
        # DRC
        drc_warnings = []
        if req.fc_khz > 5.0:
            drc_warnings.append(f"⚠️ [隔离环路带宽过高] 目标带宽 fc ({req.fc_khz:.1f} kHz) 偏大。由于光耦存在低频极点（通常在 5-15kHz），隔离反馈环路穿越频率通常推荐设计在 1kHz ~ 2kHz 之间，过高的 fc 极易震荡！")
            
        pm = bode['pm_deg']
        if pm < 45.0:
            drc_warnings.append(f"❌ [相位裕度低自激风险] 隔离环路相位裕度仅为 {pm:.1f}°！极易自激，请降低 fc 或选用高带宽光耦！")
            
        return {
            "design": design,
            "bode": bode,
            "step": step,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OptoDcRequest(BaseModel):
    vout: float
    vf: float
    r_led_k: float
    ctr: float
    r_pull_k: float
    vdd: float
    r_par_k: float

@app.post("/api/calculate/loop_compensation/tl431_dc")
def calculate_loop_tl431_dc(req: OptoDcRequest):
    try:
        design = calculate_opto_dc_bias(
            vout=req.vout, vf=req.vf, r_led_k=req.r_led_k, ctr=req.ctr,
            r_pull_k=req.r_pull_k, vdd=req.vdd, r_par_k=req.r_par_k
        )
        
        # DRC 校验
        drc_warnings = []
        if design['status'] == "Fail":
            for r in design['reasons']:
                if "驱动能力不足" in r:
                    drc_warnings.append(f"❌ [光耦驱动不足] 最大可供 LED 电流 ({design['if_max_avail_ma']:.2f} mA) 小于所需最小电流 ({design['if_req_ma']:.2f} mA)。环路直流静态增益断流，系统无法正常稳压反馈！请调小 R_led 阻值、调高原边上拉电阻 R_pullup，或选更高 CTR 规格的光耦！")
                elif "偏置电流不足" in r:
                    drc_warnings.append(f"❌ [TL431工作电流偏小] 阴极工作电流 Ika ({design['ika_actual_ma']:.2f} mA) 小于 1.0 mA（低于 TL431 的基准静态电流阀门值）。这会导致 TL431 偏置失常发生直流漂移，引起稳压值飘移与瞬态失真！推荐在光耦 LED 两端并联一个阻值约为 {design['rec_r_par_k']:.2f} kΩ 的偏置电阻 (R_par)！")
                    
        return {
            "design": design,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class HvDividerRequest(BaseModel):
    r1_k: float
    c1_pf: float
    r2_k: float

@app.post("/api/calculate/loop_compensation/hv_divider")
@app.post("/api/calculate/loop/hv_divider")
def calculate_loop_hv_divider(req: HvDividerRequest):
    try:
        design = calculate_hv_divider(
            r1_k=req.r1_k, c1_pf=req.c1_pf, r2_k=req.r2_k
        )
        return {
            "design": design,
            "drc_warnings": []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DigitalControlRequest(BaseModel):
    controller_type: str
    k_dc: float
    fs_khz: float
    fz1_khz: float
    fz2_khz: float
    fp1_khz: float
    fp2_khz: float

@app.post("/api/calculate/loop_compensation/digital")
@app.post("/api/calculate/loop/digital_pid")
def calculate_loop_digital(req: DigitalControlRequest):
    try:
        is_type3 = req.controller_type == "Type III"
        fs_hz = req.fs_khz * 1000.0
        
        # 离散化转换
        if not is_type3:
            coeffs = discretize_type2(
                k_dc=req.k_dc, f_z_hz=req.fz1_khz * 1000.0, f_p_hz=req.fp1_khz * 1000.0, f_s_hz=fs_hz
            )
        else:
            coeffs = discretize_type3(
                k_dc=req.k_dc, f_z1_hz=req.fz1_khz * 1000.0, f_z2_hz=req.fz2_khz * 1000.0,
                f_p1_hz=req.fp1_khz * 1000.0, f_p2_hz=req.fp2_khz * 1000.0, f_s_hz=fs_hz
            )
            
        c_code = generate_c_code(coeffs, is_type3)
        
        # DRC 校验
        drc_warnings = []
        # 若极点频率太靠近采样频率
        if req.fs_khz < 10.0 * req.fp1_khz:
            drc_warnings.append(f"⚠️ [离散化失真警告] 极点 1 频率 ({req.fp1_khz:.1f} kHz) 与数字采样率 ({req.fs_khz:.1f} kHz) 过于接近（不足 10 倍）。这会导致双线性变换失真明显，离散化后的 Z 域频带相位严重退化！建议调高采样频率或调小模拟极点。")
            
        if is_type3 and req.fs_khz < 10.0 * req.fp2_khz:
            drc_warnings.append(f"⚠️ [离散化失真警告] 极点 2 频率 ({req.fp2_khz:.1f} kHz) 过于靠近采样频率。可能在控制器采样周期中引入混叠，请增大采样频率 fs。")
            
        return {
            "design": coeffs,
            "c_code": c_code,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



class DigitalPidDesignRequest(BaseModel):
    mode: int # 0: CM Buck, 1: VM Buck, 2: CM Boost
    vin: float
    vout: float
    iout: float
    l_uh: float
    c_uf: float
    fs_khz: float
    v_ref_adc: float
    k_div: float
    fc_khz: float
    pm_deg: float

@app.post("/api/calculate/digital_pid/design")
def calculate_digital_pid_design_api(req: DigitalPidDesignRequest):
    try:
        res = calc_digital_pid_design(
            mode=req.mode, vin=req.vin, vout=req.vout, iout=req.iout,
            l_uh=req.l_uh, c_uf=req.c_uf, fs_khz=req.fs_khz,
            v_ref_adc=req.v_ref_adc, k_div=req.k_div,
            fc_khz=req.fc_khz, pm_deg=req.pm_deg
        )
        
        bode = simulate_digital_pid_bode(
            mode=req.mode, vin=req.vin, vout=req.vout, iout=req.iout,
            l_uh=req.l_uh, c_uf=req.c_uf, fs_khz=req.fs_khz,
            v_ref_adc=req.v_ref_adc, k_div=req.k_div,
            kp_analog=res["kp_analog"], ki_analog=res["ki_analog"]
        )
        
        step = simulate_digital_pid_step(
            mode=req.mode, vin=req.vin, vout=req.vout, iout=req.iout,
            l_uh=req.l_uh, c_uf=req.c_uf, v_ref_adc=req.v_ref_adc, k_div=req.k_div,
            kp_analog=res["kp_analog"], ki_analog=res["ki_analog"]
        )
        
        c_code = generate_pid_c_code(res["kp_dig"], res["ki_dig"], res["kd_dig"])
        
        drc_warnings = []
        fs_hz = req.fs_khz * 1e3
        fc_hz = req.fc_khz * 1e3
        
        if fc_hz > fs_hz / 10.0:
            drc_warnings.append(
                f"⚠️ [带宽过高预警] 目标带宽 fc ({req.fc_khz:.1f} kHz) 已经超过了采样频率 Fs ({req.fs_khz:.1f} kHz) 的 1/10。由于数字控制离散化延迟和采样保持效应，可能会导致环路相位裕度严重退化甚至系统失稳！建议 fc <= Fs/20。"
            )
        elif fc_hz < fs_hz / 100.0:
            drc_warnings.append(
                f"ℹ️ [带宽偏低提示] 目标带宽 fc ({req.fc_khz:.1f} kHz) 低于采样频率 Fs ({req.fs_khz:.1f} kHz) 的 1/100。系统响应速度可能偏慢，未能充分发挥数字控制的快速瞬态响应优势。"
            )
            
        if req.pm_deg < 45.0:
            drc_warnings.append(
                f"⚠️ [稳定性警告] 目标相位裕度 PM ({req.pm_deg:.1f} deg) 偏低（小于 45 deg）。系统可能在负载突变时产生严重的阶跃振荡或过冲，建议设置在 45 ~ 60 deg 之间。"
            )
        elif req.pm_deg > 75.0:
            drc_warnings.append(
                f"ℹ️ [阻尼过大提示] 目标相位裕度 PM ({req.pm_deg:.1f} deg) 偏高（大于 75 deg）。系统响应可能过于迟钝，调节时间偏长。"
            )
            
        if res["required_phase_boost"] > 80.0:
            drc_warnings.append(
                f"⚠️ [相位提升超限] 所需相位提升 ({res['required_phase_boost']:.1f} deg) 超过 80 deg。PI/Type II 控制器最多能提供 90 deg 提升。可能需要降低 fc，或增加 Kd 项升级为 PID 控制器以提供更高的微分相位。"
            )
            
        r_load = req.vout / req.iout if req.iout > 0 else 100.0
        c_val = req.c_uf * 1e-6
        fp = 1.0 / (2.0 * math.pi * r_load * c_val)
        if fp > fc_hz:
            drc_warnings.append(
                f"⚠️ [负载极点警告] 输出滤波极点 fp ({fp/1e3:.2f} kHz) 高于环路穿越频率 fc ({req.fc_khz:.1f} kHz)。环路可能在低频失去高增益积分作用，导致稳态误差增加。"
            )

        return {
            "kp_dig": res["kp_dig"],
            "ki_dig": res["ki_dig"],
            "kd_dig": res["kd_dig"],
            "fz_hz": res["fz_hz"],
            "h_fb": res["h_fb"],
            "gain_plant_mag_fc": res["gain_plant_mag_fc"],
            "phase_plant_deg_fc": res["phase_plant_deg_fc"],
            "required_phase_boost": res["required_phase_boost"],
            "bode_data": bode["bode_data"],
            "step_data": step,
            "c_code": c_code,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class S2zConversionRequest(BaseModel):
    fz_khz: float
    fp_khz: float
    gain: float
    fs_khz: float
    method: str # "tustin" | "euler"

@app.post("/api/calculate/digital_pid/s2z")
def calculate_s2z_conversion_api(req: S2zConversionRequest):
    try:
        res = calc_s2z_conversion(
            fz_khz=req.fz_khz, fp_khz=req.fp_khz, gain=req.gain,
            fs_khz=req.fs_khz, method=req.method
        )
        
        drc_warnings = []
        zp_mag = abs(-res["a1"])
        if zp_mag >= 1.0:
            drc_warnings.append(
                f"❌ [Z域极点发散] 离散极点模值 |zp| = {zp_mag:.3f} >= 1.0 位于单位圆外/圆上，数字控制器在 MCU 中运行将发散失稳！建议提高采样率 Fs 或改用 Tustin 双线性变换。"
            )
        if req.fs_khz < 10.0 * req.fp_khz:
            drc_warnings.append(
                f"⚠️ [离散失真警告] 极点频率 fp ({req.fp_khz:.1f} kHz) 过于靠近采样频率 Fs ({req.fs_khz:.1f} kHz) 的 1/10。由于离散化在接近奈奎斯特频率处存在严重的非线性畸变，可能会导致零极点发生偏移。建议提高采样频率 Fs。"
            )
            
        c_coeffs = {"b0": res["b0"], "b1": res["b1"], "b2": res["b2"], "a1": res["a1"], "a2": res["a2"]}
        c_code = generate_c_code(c_coeffs, is_type3=False)
        
        return {
            "b0": res["b0"],
            "b1": res["b1"],
            "b2": res["b2"],
            "a1": res["a1"],
            "a2": res["a2"],
            "bode_data": res["bode_data"],
            "c_code": c_code,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class AdcFilterRequest(BaseModel):
    filter_type: str # "1st" | "2nd"
    fs_hz: float
    fc_hz: float

@app.post("/api/calculate/digital_pid/filter")
def calculate_adc_filter_api(req: AdcFilterRequest):
    try:
        if req.fc_hz >= req.fs_hz / 2.0:
            raise HTTPException(status_code=400, detail="截止频率 fc 必须严格小于奈奎斯特极限 (fs / 2)")
            
        res = calc_adc_filter_design(
            filter_type=req.filter_type, fs_hz=req.fs_hz, fc_hz=req.fc_hz
        )
        
        c_code = generate_digital_filter_c_code(res["coeffs"], req.filter_type)
        
        drc_warnings = []
        if req.fc_hz > req.fs_hz / 10.0:
            drc_warnings.append(
                f"⚠️ [相位延迟警告] 滤波器截止频率 fc ({req.fc_hz:.1f} Hz) 大于采样率 ({req.fs_hz:.1f} Hz) 的 1/10。虽然滤波效果较弱，但会在闭环环路中引入过大的相位延迟，可能会蚕食主控制环路的相位裕度导致不稳定。"
            )
        elif req.fc_hz < req.fs_hz / 200.0:
            drc_warnings.append(
                f"ℹ️ [阻尼偏重提示] 截止频率 fc ({req.fc_hz:.1f} Hz) 极低（低于采样率的 1/200）。虽然能够完美滤除一切高频开关噪声，但会给反馈通道带来巨大的群延迟，系统动态响应速度将受到极严重的拖累。"
            )
            
        return {
            "coeffs": res["coeffs"],
            "bode_data": res["bode_data"],
            "c_code": c_code,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class PassiveFilterRequest(BaseModel):
    filter_type: str # "rc" | "lc" | "rl"
    mode: int # 0: Calc fc, 1: Calc R/L, 2: Calc C/L
    r: float
    l_uh: float
    c_uf: float
    fc_hz: float
    rl_mohm: Optional[float] = 100.0
    esr_mohm: Optional[float] = 50.0

@app.post("/api/calculate/filter_design/passive")
def calculate_passive_filter_api(req: PassiveFilterRequest):
    try:
        # L/C 单位变换
        l_h = req.l_uh * 1e-6
        c_f = req.c_uf * 1e-6
        
        res = calc_passive_filter_design(
            filter_type=req.filter_type, mode=req.mode,
            r=req.r if req.r > 0 else 1e6, l=l_h, c=c_f, fc=req.fc_hz
        )
        
        # 扫频 Bode
        bode = simulate_passive_filter_bode(
            filter_type=req.filter_type, r=res["r"], l=res["l"], c=res["c"],
            rl_mohm=req.rl_mohm or 100.0, esr_mohm=req.esr_mohm or 50.0
        )
        
        drc_warnings = []
        if req.filter_type == "lc" and res["z0"] > 50.0:
            drc_warnings.append(
                f"⚠️ [高阻抗警告] LC 滤波器的特征阻抗 Zo ({res['z0']:.1f} Ω) 偏高。如果后级是低阻抗负载或动态电流负载，可能会由于滤波器 Q 值过高在 fc 处产生严重的电压隆起与振荡，建议减小 L 增大 C。"
            )
            
        return {
            "res_val": res["res_val"],
            "z0": res["z0"],
            "r": res["r"],
            "l_uh": res["l"] * 1e6,
            "c_uf": res["c"] * 1e6,
            "fc_hz": res["fc"],
            "bode": bode,
            "bode_data": bode,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ActiveFilterRequest(BaseModel):
    topo: int # 0: Sallen-Key, 1: MFB
    fc_hz: float
    q: float
    c1_nf: float
    c2_nf_opt: Optional[float] = 0.0

@app.post("/api/calculate/filter_design/active")
def calculate_active_filter_api(req: ActiveFilterRequest):
    try:
        res = calc_active_filter_design(
            topo=req.topo, fc=req.fc_hz, q=req.q,
            c1_nf=req.c1_nf, c2_nf_opt=req.c2_nf_opt
        )
        
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class PowerFilterRequest(BaseModel):
    calc_type: str # "emi_dm" | "emi_cm" | "cmc_sat" | "spwm" | "bead"
    # EMI dm/cm 字段
    emi_l_uh: Optional[float] = 0.0
    emi_c_uf: Optional[float] = 0.0
    emi_fc_hz: Optional[float] = 0.0
    # CMC 字段
    cmc_l_mh: Optional[float] = 0.0
    cmc_leak_ratio: Optional[float] = 0.0
    cmc_idm: Optional[float] = 0.0
    cmc_n: Optional[float] = 0.0
    cmc_ae: Optional[float] = 0.0
    cmc_bsat: Optional[float] = 0.0
    # SPWM 字段
    spwm_vdc: Optional[float] = 0.0
    spwm_vac_ll: Optional[float] = 0.0
    spwm_p_kw: Optional[float] = 0.0
    spwm_fsw_khz: Optional[float] = 0.0
    spwm_fout_hz: Optional[float] = 0.0
    spwm_ripple_pct: Optional[float] = 0.0
    spwm_is_lcl: Optional[bool] = False
    # 磁珠字段
    bead_l_uh: Optional[float] = 0.0
    bead_c_uf: Optional[float] = 0.0

@app.post("/api/calculate/filter_design/power")
def calculate_power_filter_api(req: PowerFilterRequest):
    try:
        drc_warnings = []
        if req.calc_type == "emi_dm":
            c_f = req.emi_c_uf * 1e-6
            res = calc_passive_filter_design("lc", 0 if req.emi_l_uh == 0 else 1, 0, req.emi_l_uh*1e-6, c_f, req.emi_fc_hz)
            bode = simulate_passive_filter_bode("lc", 50.0, res["l"], res["c"])
            return {
                "l_uh": res["l"] * 1e6,
                "c_uf": res["c"] * 1e6,
                "fc_hz": res["fc"],
                "bode": bode,
                "bode_data": bode,
                "drc_warnings": drc_warnings
            }
        elif req.calc_type == "emi_cm":
            # 对于共模滤波器，C_y 容值通常限制在极小范围内（如几 nF）以满足安规漏电流限制！
            c_f = req.emi_c_uf * 1e-9 # Cy 通常是 nF 级
            res = calc_passive_filter_design("lc", 0 if req.emi_l_uh == 0 else 1, 0, req.emi_l_uh*1e-6, c_f, req.emi_fc_hz)
            
            # Cy 安规限值 DRC (一般 Cy <= 4.7nF)
            if res["c"] > 4.7e-9:
                drc_warnings.append(
                    f"⚠️ [安规警告] 共模 Y 电容 Cy ({res['c']*1e9:.2f} nF) 偏大。根据 IEC 62368-1，为防止 50Hz 工频漏电流超过人体安全阈值 (一般为 0.25mA - 3.5mA 视场合而定)，单相交流输入端的 Y 电容之和通常推荐 <= 4.7 nF！"
                )
            bode = simulate_passive_filter_bode("lc", 25.0, res["l"], res["c"])
            return {
                "l_mh": res["l"] * 1e3,
                "c_nf": res["c"] * 1e9,
                "fc_hz": res["fc"],
                "bode": bode,
                "bode_data": bode,
                "drc_warnings": drc_warnings
            }
        elif req.calc_type == "cmc_sat":
            res = calc_cmc_saturation(
                lcm_mh=req.cmc_l_mh, leak_ratio=req.cmc_leak_ratio,
                idm=req.cmc_idm, n=req.cmc_n, ae_mm2=req.cmc_ae, bsat=req.cmc_bsat
            )
            if res["status"] == "danger":
                drc_warnings.append(
                    f"❌ [磁饱和高危警告] 共模漏磁场强度 B_leak ({res['b_leak']:.3f} T) 已经超过了磁芯的饱和磁感应强度 Bsat ({req.cmc_bsat:.2f} T)！共模电感在工作时可能会饱和失控，导致漏感衰减，EMI 滤波完全失效！请增加匝数 N 或选用更大 Ae 的磁芯。"
                )
            elif res["status"] == "warning":
                drc_warnings.append(
                    f"⚠️ [磁饱和临界提示] 共模漏磁场强度 B_leak ({res['b_leak']:.3f} T) 已接近饱和边缘（剩余裕量不足 30%）。请密切关注高温下 Bsat 退化情况，必要时留出更多裕量。"
                )
            return {
                "l_leak_uh": res["l_leak_uh"],
                "b_leak": res["b_leak"],
                "drc_warnings": drc_warnings
            }
        elif req.calc_type == "spwm":
            res = calc_spwm_filter(
                vdc=req.spwm_vdc, vac_ll=req.spwm_vac_ll,
                p_rate_kw=req.spwm_p_kw, fsw_khz=req.spwm_fsw_khz,
                fout_hz=req.spwm_fout_hz, ripple_pct=req.spwm_ripple_pct,
                is_lcl=req.spwm_is_lcl
            )
            # 谐振频率 DRC：f_res 应该在 fout_hz 到 fsw_khz/2 之间 (通常在 10倍基波到 1/2 开关频率之间)
            fsw_hz = req.spwm_fsw_khz * 1000.0
            if res["f_res_hz"] >= fsw_hz / 2.0:
                drc_warnings.append(
                    f"❌ [滤波失效警告] 谐振频率 ({res['f_res_hz']/1e3:.2f} kHz) 超过了 Nyquist 极限 (Fs/2 = {fsw_hz/2000:.2f} kHz)。该滤波器无法滤除高频开关分量，甚至会造成开关噪声放大。请增大 L 或 C 以降低谐振频率。"
                )
            elif res["f_res_hz"] < req.spwm_fout_hz * 10.0:
                drc_warnings.append(
                    f"⚠️ [基波衰减警告] 谐振频率 ({res['f_res_hz']/1e3:.2f} kHz) 太靠近逆变基波频率 ({req.spwm_fout_hz:.1f} Hz) 的 10 倍。这会在基波带内引入显著的增益衰减和无功消耗。建议提高谐振频率。"
                )
            return {
                "l1_mh": res["l1_mh"],
                "cf_uf": res["cf_uf"],
                "l2_mh": res["l2_mh"],
                "f_res_hz": res["f_res_hz"],
                "drc_warnings": drc_warnings
            }
        elif req.calc_type == "bead":
            res = calc_bead_damping(l_uh=req.bead_l_uh, c_uf=req.bead_c_uf)
            return {
                "f_res_hz": res["f_res_hz"],
                "z0": res["z0"],
                "r_crit": res["r_crit"],
                "r_opt": res["r_opt"],
                "drc_warnings": drc_warnings
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class InputStabilityRequest(BaseModel):
    vin: float
    pout: float
    l_uh: float
    c_uf: float

@app.post("/api/calculate/filter_design/input_stability")
def calculate_input_stability_api(req: InputStabilityRequest):
    try:
        res = calc_input_damping_stability(
            vin=req.vin, pout=req.pout, l_uh=req.l_uh, c_uf=req.c_uf
        )
        
        drc_warnings = []
        if not res["stable"]:
            drc_warnings.append(
                f"❌ [Middlebrook 失稳警告] 滤波器输出特征阻抗 Zo ({res['z_o']:.1f} Ω) 已经大于或等于变换器的等效输入负阻 |Zin| ({res['z_in_mag']:.1f} Ω)！如果没有加入足够的并联阻尼，系统将在突加负载时发生灾难性的负阻抗振荡。建议并联 Rd-Cd 阻尼网络，或减小 L/C 比值。"
            )
        else:
            # 裕度检查，通常推荐 Zo < 0.5 * Zin
            if res["z_o"] > 0.5 * res["z_in_mag"]:
                drc_warnings.append(
                    f"⚠️ [稳定度裕度不足] 特征阻抗 Zo ({res['z_o']:.1f} Ω) 超过了变换器输入负阻的一半 ({0.5*res['z_in_mag']:.1f} Ω)。虽然理论上稳定，但在极端电网瞬态或低压满载下仍有轻微振荡风险。"
                )
                
        return {
            "z_in_mag": res["z_in_mag"],
            "z_o": res["z_o"],
            "r_d": res["r_d"],
            "c_d_uf": res["c_d_uf"],
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class PdnRequest(BaseModel):
    calc_type: str # "target_z" | "cap_num" | "anti_res"
    # target_z 字段
    di: Optional[float] = 0.0
    dv_ripple_mv: Optional[float] = 0.0
    # cap_num 字段
    z_target_mohm: Optional[float] = 0.0
    cap_esr_mohm: Optional[float] = 0.0
    cap_esl_nh: Optional[float] = 0.0
    # anti_res 字段
    c1_uf: Optional[float] = 0.0
    esr1_mohm: Optional[float] = 0.0
    esl1_nh: Optional[float] = 0.0
    c2_uf: Optional[float] = 0.0
    esr2_mohm: Optional[float] = 0.0
    esl2_nh: Optional[float] = 0.0

@app.post("/api/calculate/filter_design/pdn")
def calculate_pdn_api(req: PdnRequest):
    try:
        drc_warnings = []
        if req.calc_type == "target_z":
            z_target_ohm = (req.dv_ripple_mv * 1e-3) / req.di if req.di > 0 else 0.0
            return {
                "z_target_mohm": z_target_ohm * 1e3,
                "drc_warnings": drc_warnings
            }
        elif req.calc_type == "cap_num":
            n_req = math.ceil(req.cap_esr_mohm / req.z_target_mohm) if req.z_target_mohm > 0 else 1
            if n_req < 1: n_req = 1
            
            esl_total = (req.cap_esl_nh * 1e-9) / n_req
            z_target_ohm = req.z_target_mohm * 1e-3
            f_eff = z_target_ohm / (2.0 * math.pi * esl_total) if esl_total > 0 else 0.0
            
            return {
                "n_req": n_req,
                "n_caps": n_req,
                "f_eff_mhz": f_eff / 1e6,
                "drc_warnings": drc_warnings
            }
        elif req.calc_type == "anti_res":
            res = simulate_pdn_anti_resonance(
                c1_uf=req.c1_uf, esr1_mohm=req.esr1_mohm, esl1_nh=req.esl1_nh,
                c2_uf=req.c2_uf, esr2_mohm=req.esr2_mohm, esl2_nh=req.esl2_nh
            )
            # 反谐振峰阻抗预警 (如果反谐振峰值超过 1 Ohm，或者高于用户设定的目标值)
            if res["z_peak_ohm"] > 1.0:
                drc_warnings.append(
                    f"⚠️ [并联反谐振过高] 并联反谐振峰 Z_peak ({res['z_peak_ohm']:.2f} Ω) 超过了 1.0 Ω。在反谐振点 ({res['f_peak_hz']/1e6:.2f} MHz) 附近，去耦网络相当于断路，会引起极高的电压瞬态纹波！建议优化两个电容的参数，减小它们的 ESL，或者串联小电阻进行有源损耗阻尼。"
                )
            return {
                "srf1_mhz": res["srf1_hz"] / 1e6,
                "srf2_mhz": res["srf2_hz"] / 1e6,
                "f_peak_mhz": res["f_peak_hz"] / 1e6,
                "z_peak_ohm": res["z_peak_ohm"],
                "bode": res["bode_data"],
                "bode_data": res["bode_data"],
                "drc_warnings": drc_warnings
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# EMC Calculation Toolbox Endpoints
# ==============================================================================

@app.get("/api/calculate/emc_toolbox/standards")
def get_emc_standards():
    return STANDARDS_DB

class EmcCheckLimitRequest(BaseModel):
    freq_mhz: float
    std_key: str

@app.post("/api/calculate/emc_toolbox/check_limit")
def check_emc_limit(req: EmcCheckLimitRequest):
    try:
        limit = get_emc_limit_at_freq(req.freq_mhz, req.std_key)
        return {"limit": limit}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EmcConversionRequest(BaseModel):
    val: float
    mode: str

@app.post("/api/calculate/emc_toolbox/conversion")
def calculate_emc_conversion(req: EmcConversionRequest):
    try:
        res = calc_emc_unit_conversion(req.val, req.mode)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EmcAttenuationRequest(BaseModel):
    l_uh: float
    c_nf: float
    f_khz: float
    z_ohm: float = 50.0

@app.post("/api/calculate/emc_toolbox/attenuation")
def calculate_emc_attenuation(req: EmcAttenuationRequest):
    try:
        res = calc_emc_filter_attenuation(req.l_uh, req.c_nf, req.f_khz, req.z_ohm)
        return {
            "f_res_hz": res["f_res_hz"],
            "attenuation_db": res["attenuation_db"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EmcRadiatedRequest(BaseModel):
    f_mhz: float
    v_rx_dbuv: float
    af_db_m: float
    cable_loss_db: float
    amp_gain_db: float
    slot_len_mm: Optional[float] = 0.0
    gap_count: Optional[int] = 1

@app.post("/api/calculate/emc_toolbox/radiated")
def calculate_emc_radiated(req: EmcRadiatedRequest):
    try:
        wl_res = calc_emc_radiated_wavelength(req.f_mhz)
        field_res = calc_emc_radiated_field_strength(
            req.v_rx_dbuv, req.af_db_m, req.cable_loss_db, req.amp_gain_db
        )
        se_slot = calc_emc_slot_shielding(req.f_mhz, req.slot_len_mm or 0.0, req.gap_count or 1)
        return {
            "wavelength_m": wl_res["wavelength_m"],
            "safe_gap_mm": wl_res["safe_gap_mm"],
            "field_strength_dbuv_m": field_res,
            "se_slot_db": se_slot
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EmcFilterSizingRequest(BaseModel):
    v_line: float
    f_line: float
    i_leak_ma: float
    f_noise_khz: float
    att_cm_db: float
    att_dm_db: float
    cx_uf: float
    k_leak_pct: float

@app.post("/api/calculate/emc_toolbox/filter_sizing")
def calculate_emc_filter_sizing(req: EmcFilterSizingRequest):
    try:
        res = calc_emc_filter_sizing(
            v_line=req.v_line,
            f_line=req.f_line,
            i_leak_ma=req.i_leak_ma,
            f_noise_khz=req.f_noise_khz,
            att_cm_db=req.att_cm_db,
            att_dm_db=req.att_dm_db,
            cx_uf=req.cx_uf,
            k_leak_pct=req.k_leak_pct
        )
        drc_warnings = []
        if res['cy_rec_nf'] <= 0.1:
            drc_warnings.append(
                "⚠️ [Y电容容量极低警告] 由于安规漏电流限制极严或电网电压过高，设计出的 Y 电容量 cy_rec 极小。这会导致共模截止频率极难通过 Y 电容滤波实现，建议核实漏电流要求是否合理，或使用多级/差共模混合拓扑滤波。"
            )
        if res['lcm_h'] > 0.05: # > 50 mH
            drc_warnings.append(
                f"⚠️ [共模感值过高警告] 设计出的共模电感 LCM 达 {res['lcm_h']*1e3:.1f} mH，感值过大，在工程上极难绕制，或者体积巨大、高频寄生电容过大导致高频失效。建议在安规允许范围内适当增大 Y 电容 (Cy)，或者考虑二级级联共模扼流扼制。"
            )
        if res['ldm_add_h'] > 0.002: # > 2 mH
            drc_warnings.append(
                f"⚠️ [差模补偿感值偏大] 所需额外增加的差模电感达到 {res['ldm_add_h']*1e6:.1f} uH。由于差模回路通过线网总电流，这么大的电感很容易在额定大工作电流下发生磁饱和！建议增大差模电容 X-Cap (Cx)，降低所需电感量，或者选用高饱和磁密的粉芯类磁件做差模电感。"
            )
            
        return {
            "cy_max_nf": res["cy_max_nf"],
            "cy_rec_nf": res["cy_rec_nf"],
            "fc_cm_khz": res["fc_cm_hz"] / 1e3,
            "lcm_mh": res["lcm_h"] * 1e3,
            "fc_dm_khz": res["fc_dm_hz"] / 1e3,
            "ldm_uh": res["ldm_h"] * 1e6,
            "ldm_leak_uh": res["ldm_leak_h"] * 1e6,
            "ldm_add_uh": res["ldm_add_h"] * 1e6,
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EmcConductedFixRequest(BaseModel):
    std_key: str
    freq_mhz: float
    measured_dbuv: float
    margin_db: float
    cm_share_pct: float
    v_line: float
    f_line: float
    i_leak_ma: float
    cx_uf: float
    k_leak_pct: float

@app.post("/api/calculate/emc_toolbox/conducted_fix")
def calculate_emc_conducted_fix(req: EmcConductedFixRequest):
    try:
        res = calc_emc_conducted_fix(
            std_key=req.std_key,
            freq_mhz=req.freq_mhz,
            measured_dbuv=req.measured_dbuv,
            margin_db=req.margin_db,
            cm_share_pct=req.cm_share_pct,
            v_line=req.v_line,
            f_line=req.f_line,
            i_leak_ma=req.i_leak_ma,
            cx_uf=req.cx_uf,
            k_leak_pct=req.k_leak_pct
        )
        drc_warnings = []
        if res["over"] > 25.0:
            drc_warnings.append(
                f"🔥 [超标量极大警告] 当前频率超标量达 {res['over']:.1f} dB，属于严重超标！单级 LC 滤波器的极限衰减通常也就 40-50 dB（考虑高频寄生参数直通漏感）。强烈建议在源头上进行整改（如调整开关管门极驱动电阻 Rg、优化 PCB 回路铺地屏蔽），再配合滤波器整改！"
            )
        if res.get("lcm_mh", 0) > 20.0:
            drc_warnings.append(
                f"⚠️ [单级电感过大] 计算所得共模电感 Lcm ({res['lcm_mh']:.1f} mH) > 20 mH。建议将单级 LC 滤波器拆分为两级级联 EMI 滤波 (Two-stage EMI Filter)，以降低单颗电感体积与高频寄生电容。"
            )
        if res["cy_nf"] <= 0.22:
            drc_warnings.append(
                "⚠️ [整改 Y 电容受限] 安全允许 of Y 电容量极小。若共模噪声依然无法压下，可以尝试改变共模绕线工艺、使用更小高频寄生电容的共模电感，或者引入有源EMI滤波器（Active EMI Filter）进行主动抵消。"
            )
            
        return {
            "limit": res["limit"],
            "over": res["over"],
            "need": res["need"],
            "cm_att": res["cm_att"],
            "dm_att": res["dm_att"],
            "cy_nf": res["cy_nf"],
            "lcm_mh": res["lcm_mh"],
            "ldm_uh": res["ldm_uh"],
            "ldm_add_uh": res["ldm_add_uh"],
            "r_damp_ohm": res["r_damp_ohm"],
            "c_damp_uf": res["c_damp_uf"],
            "drc_warnings": drc_warnings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class EmcFilterBodeRequest(BaseModel):
    l_val: float
    c_val: float
    r_damp: float
    c_damp: float
    is_cm: bool
    z_source: Optional[float] = 50.0
    z_load: Optional[float] = 50.0

@app.post("/api/calculate/emc_toolbox/filter_bode")
def calculate_emc_filter_bode(req: EmcFilterBodeRequest):
    try:
        res = calc_emc_filter_bode(
            l_val=req.l_val,
            c_val=req.c_val,
            r_damp=req.r_damp,
            c_damp=req.c_damp,
            is_cm=req.is_cm,
            z_source=req.z_source,
            z_load=req.z_load
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================================
# Load Transient & ADC Conditioning Endpoints
# =====================================================================

class LoadTransientRequest(BaseModel):
    v_out: float
    i_step: float
    f_c_khz: float
    c_out_uf: float
    esr_mohm: float
    f_sw_khz: Optional[float] = None
    v_in: Optional[float] = None
    l_uh: Optional[float] = None


@app.post("/api/calculate/load_transient")
def calculate_load_transient_endpoint(req: LoadTransientRequest):
    try:
        res = calc_load_transient(
            v_out=req.v_out,
            i_step=req.i_step,
            f_c_khz=req.f_c_khz,
            c_out_uf=req.c_out_uf,
            esr_mohm=req.esr_mohm,
            f_sw_khz=req.f_sw_khz,
            v_in=req.v_in,
            l_uh=req.l_uh
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AdcRcFilterRequest(BaseModel):
    r_ohm: float
    c_nf: float
    csh_pf: float
    bits: int
    vref: float


@app.post("/api/calculate/adc_conditioning/rc_filter")
def calculate_adc_rc_filter_endpoint(req: AdcRcFilterRequest):
    try:
        res = calc_adc_rc_filter(
            r_ohm=req.r_ohm,
            c_nf=req.c_nf,
            csh_pf=req.csh_pf,
            bits=req.bits,
            vref=req.vref
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AdcBudgetRequest(BaseModel):
    r_src: float
    r_flt: float
    c_flt_nf: float
    c_sh_pf: float
    t_sample_ns: float
    f_s_khz: float
    f_signal_hz: float
    bits: int
    vref: float
    gain: float
    op_noise_nv: float
    bw_noise_khz: float
    loop_fc_khz: float


@app.post("/api/calculate/adc_conditioning/budget")
def calculate_adc_budget_endpoint(req: AdcBudgetRequest):
    try:
        res = calc_adc_sampling_budget(
            r_src=req.r_src,
            r_flt=req.r_flt,
            c_flt_nf=req.c_flt_nf,
            c_sh_pf=req.c_sh_pf,
            t_sample_ns=req.t_sample_ns,
            f_s_khz=req.f_s_khz,
            f_signal_hz=req.f_signal_hz,
            bits=req.bits,
            vref=req.vref,
            gain=req.gain,
            op_noise_nv=req.op_noise_nv,
            bw_noise_khz=req.bw_noise_khz,
            loop_fc_khz=req.loop_fc_khz
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AdcAfeReconstructRequest(BaseModel):
    vref: float
    bits: int
    mode: int
    p1: float
    p2: float
    bias: float
    phys_in: float


@app.post("/api/calculate/adc_conditioning/afe_reconstruct")
def calculate_adc_afe_reconstruct_endpoint(req: AdcAfeReconstructRequest):
    try:
        res = calc_adc_afe_reconstruct(
            vref=req.vref,
            bits=req.bits,
            mode=req.mode,
            p1=req.p1,
            p2=req.p2,
            bias=req.bias,
            phys_in=req.phys_in
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class AdcTwoPointRequest(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


@app.post("/api/calculate/adc_conditioning/two_point")
def calculate_adc_two_point_endpoint(req: AdcTwoPointRequest):
    try:
        res = calc_adc_two_point_fit(
            x1=req.x1,
            y1=req.y1,
            x2=req.x2,
            y2=req.y2
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =====================================================================
# Op-Amp & Comparator Endpoints
# =====================================================================

class OpampBasicRequest(BaseModel):
    vin: float
    gbp: float
    mode: str
    rin: Optional[float] = None
    rf: Optional[float] = None


@app.post("/api/calculate/opamp/basic")
def calculate_opamp_basic_endpoint(req: OpampBasicRequest):
    try:
        res = calc_basic_opamp(
            vin=req.vin,
            gbp=req.gbp,
            mode=req.mode,
            rin=req.rin,
            rf=req.rf
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OpampDiffRequest(BaseModel):
    r1: float
    r2: float
    r3: float
    r4: float
    v1: float
    v2: float


@app.post("/api/calculate/opamp/diff")
def calculate_opamp_diff_endpoint(req: OpampDiffRequest):
    try:
        res = calc_diff_opamp(
            r1=req.r1,
            r2=req.r2,
            r3=req.r3,
            r4=req.r4,
            v1=req.v1,
            v2=req.v2
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SummingChannel(BaseModel):
    r: float
    v: float


class OpampSummingRequest(BaseModel):
    rf: float
    channels: list[SummingChannel]


@app.post("/api/calculate/opamp/summing")
def calculate_opamp_summing_endpoint(req: OpampSummingRequest):
    try:
        channels_list = [ch.model_dump() for ch in req.channels]
        res = calc_summing_opamp(
            rf=req.rf,
            channels=channels_list
        )
        return {"vout_v": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OpampHysteresisRequest(BaseModel):
    vh: float
    vl: float
    voh: float
    vol: float
    vref: float
    r1: float
    is_noninv: bool = True


@app.post("/api/calculate/opamp/hysteresis")
def calculate_opamp_hysteresis_endpoint(req: OpampHysteresisRequest):
    try:
        res = calc_hysteresis_comparator(
            vh=req.vh,
            vl=req.vl,
            voh=req.voh,
            vol=req.vol,
            vref=req.vref,
            r1=req.r1,
            is_noninv=req.is_noninv
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OpampErrorBudgetRequest(BaseModel):
    vos: float
    drift: float
    ib: float
    cmrr_db: float
    psrr_db: float
    rin: float
    rf: float
    rs: float
    tol: float
    dt: float
    vin: float
    vcm: float
    dvcc: float


@app.post("/api/calculate/opamp/error_budget")
def calculate_opamp_error_budget_endpoint(req: OpampErrorBudgetRequest):
    try:
        res = calc_error_budget(
            vos=req.vos,
            drift=req.drift,
            ib=req.ib,
            cmrr_db=req.cmrr_db,
            psrr_db=req.psrr_db,
            rin=req.rin,
            rf=req.rf,
            rs=req.rs,
            tol=req.tol,
            dt=req.dt,
            vin=req.vin,
            vcm=req.vcm,
            dvcc=req.dvcc
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OpampSelectionRequest(BaseModel):
    fsw: float
    gain: float
    v_pp: float
    bits: int


@app.post("/api/calculate/opamp/selection")
def calculate_opamp_selection_endpoint(req: OpampSelectionRequest):
    try:
        res = calc_opamp_selection(
            fsw=req.fsw,
            gain=req.gain,
            v_pp=req.v_pp,
            bits=req.bits
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CtDesignRequest(BaseModel):
    i_pri_rms: float
    n_ratio: float
    f: float
    v_out_pk: float
    ae_mm2: float
    b_max: float
    r_sec: float


@app.post("/api/calculate/current_shunt/ct")
def calculate_ct_design_endpoint(req: CtDesignRequest):
    try:
        res = calc_ct_design(
            i_pri_rms=req.i_pri_rms,
            n_ratio=req.n_ratio,
            f=req.f,
            v_out_pk=req.v_out_pk,
            ae_mm2=req.ae_mm2,
            b_max=req.b_max,
            r_sec=req.r_sec
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ShuntErrorRequest(BaseModel):
    i_max: float
    r_mohm: float
    p_rating: float
    tcr: float
    r_theta: float
    t_amb: float
    esl_nh: float
    didt_aus: float
    pcb_l: float
    pcb_w: float


@app.post("/api/calculate/current_shunt/shunt")
def calculate_shunt_error_endpoint(req: ShuntErrorRequest):
    try:
        res = calc_shunt_error(
            i_max=req.i_max,
            r_mohm=req.r_mohm,
            p_rating=req.p_rating,
            tcr=req.tcr,
            r_theta=req.r_theta,
            t_amb=req.t_amb,
            esl_nh=req.esl_nh,
            didt_aus=req.didt_aus,
            pcb_l=req.pcb_l,
            pcb_w=req.pcb_w
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class NtcSingleRequest(BaseModel):
    r25: float
    beta: float
    r_div: float
    vref: float
    mode: int
    inp_val: float
    is_pullup: bool


@app.post("/api/calculate/ntc/single")
def calculate_ntc_single_endpoint(req: NtcSingleRequest):
    try:
        res = calc_ntc_single_point(
            r25=req.r25,
            beta=req.beta,
            r_div=req.r_div,
            vref=req.vref,
            mode=req.mode,
            inp_val=req.inp_val,
            is_pullup=req.is_pullup
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class NtcTableRequest(BaseModel):
    r25: float
    beta: float
    r_div: float
    is_pullup: bool
    start_t: int
    end_t: int
    step: int
    adc_max: int


@app.post("/api/calculate/ntc/table")
def calculate_ntc_table_endpoint(req: NtcTableRequest):
    try:
        res = calc_ntc_table_gen(
            r25=req.r25,
            beta=req.beta,
            r_div=req.r_div,
            is_pullup=req.is_pullup,
            start_t=req.start_t,
            end_t=req.end_t,
            step=req.step,
            adc_max=req.adc_max
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class NtcSteinhartRequest(BaseModel):
    t_points: list[float]
    r_points: list[float]


@app.post("/api/calculate/ntc/steinhart")
def calculate_ntc_steinhart_endpoint(req: NtcSteinhartRequest):
    try:
        res = calc_ntc_steinhart_hart(
            t_points=req.t_points,
            r_points=req.r_points
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class NtcShVerifyRequest(BaseModel):
    r_in: float
    coeff_a: float
    coeff_b: float
    coeff_c: float


@app.post("/api/calculate/ntc/sh_verify")
def calculate_ntc_sh_verify_endpoint(req: NtcShVerifyRequest):
    try:
        res = calc_ntc_sh_verify(
            r_in=req.r_in,
            a=req.coeff_a,
            b=req.coeff_b,
            c=req.coeff_c
        )
        return {"t_c": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class NtcOptDividerRequest(BaseModel):
    r25: float
    beta: float
    t_center: float
    vref: float


@app.post("/api/calculate/ntc/opt_divider")
def calculate_ntc_opt_divider_endpoint(req: NtcOptDividerRequest):
    try:
        res = calc_ntc_opt_divider(
            r25=req.r25,
            beta=req.beta,
            t_center=req.t_center,
            vref=req.vref
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PwmDacFilterRequest(BaseModel):
    f_pwm_hz: float
    v_cc: float
    bits: int
    c_sel_uf: float
    v_rip_target_mv: float
    t_set_target_ms: float


@app.post("/api/calculate/pwm_mcu_ic/filter")
def calculate_pwm_dac_filter_endpoint(req: PwmDacFilterRequest):
    try:
        return calc_pwm_dac_filter(
            f_pwm_hz=req.f_pwm_hz,
            v_cc=req.v_cc,
            bits=req.bits,
            c_sel_uf=req.c_sel_uf,
            v_rip_target_mv=req.v_rip_target_mv,
            t_set_target_ms=req.t_set_target_ms
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class McuTimerRegisterRequest(BaseModel):
    sysclk_mhz: float
    fsw_khz: float
    dt_red_ns: float
    dt_fed_ns: float
    mode: int
    hrpwm: bool
    topo: str
    duty: float
    phi: float = 0.0
    da: float = 0.0
    db: float = 0.0
    dc: float = 0.0


@app.post("/api/calculate/pwm_mcu_ic/timer")
def calculate_mcu_timer_registers_endpoint(req: McuTimerRegisterRequest):
    try:
        return calc_mcu_timer_registers(
            sysclk_mhz=req.sysclk_mhz,
            fsw_khz=req.fsw_khz,
            dt_red_ns=req.dt_red_ns,
            dt_fed_ns=req.dt_fed_ns,
            mode=req.mode,
            hrpwm=req.hrpwm,
            topo=req.topo,
            duty=req.duty,
            phi=req.phi,
            da=req.da,
            db=req.db,
            dc=req.dc
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ZvsDeadtimeOptRequest(BaseModel):
    v_bus: float
    i_zvs_light: float
    i_zvs_full: float
    q_oss_nc: float
    t_off_delay_ns: float
    fsw_khz: float


@app.post("/api/calculate/pwm_mcu_ic/zvs_opt")
def calculate_zvs_deadtime_opt_endpoint(req: ZvsDeadtimeOptRequest):
    try:
        return calc_zvs_deadtime_opt(
            v_bus=req.v_bus,
            i_zvs_light=req.i_zvs_light,
            i_zvs_full=req.i_zvs_full,
            q_oss_nc=req.q_oss_nc,
            t_off_delay_ns=req.t_off_delay_ns,
            fsw_khz=req.fsw_khz
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PwmIcFrequencyRequest(BaseModel):
    chip_key: str
    fsw_target_khz: float


@app.post("/api/calculate/pwm_mcu_ic/ic_freq")
def calculate_pwm_ic_frequency_endpoint(req: PwmIcFrequencyRequest):
    try:
        return calc_pwm_ic_frequency(
            chip_key=req.chip_key,
            fsw_target_khz=req.fsw_target_khz
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class I2cPullupRequest(BaseModel):
    vcc: float
    vol: float
    iol_ma: float
    cb_pf: float
    tr_limit_ns: float


@app.post("/api/calculate/interface_level_shift/i2c")
def calculate_i2c_pullup_endpoint(req: I2cPullupRequest):
    try:
        return calc_i2c_pullup(
            vcc=req.vcc,
            vol=req.vol,
            iol_ma=req.iol_ma,
            cb_pf=req.cb_pf,
            tr_limit_ns=req.tr_limit_ns
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class InterfaceTerminationRequest(BaseModel):
    vcc: float
    z0: float
    vab_target_v: float
    nodes: int
    rin_kohm: float = 12.0
    c_split_nf: float = 4.7


@app.post("/api/calculate/interface_level_shift/termination")
def calculate_interface_termination_endpoint(req: InterfaceTerminationRequest):
    try:
        return calc_interface_termination(
            vcc=req.vcc,
            z0=req.z0,
            vab_target_v=req.vab_target_v,
            nodes=req.nodes,
            rin_kohm=req.rin_kohm,
            c_split_nf=req.c_split_nf
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PcbTraceCapacityRequest(BaseModel):
    current: float
    temp_rise: float
    copper_oz: float
    length_mm: float
    is_internal: bool
    temp_amb: float = 25.0


@app.post("/api/calculate/pcb_toolbox/trace")
def calculate_pcb_trace_capacity_endpoint(req: PcbTraceCapacityRequest):
    try:
        return calc_pcb_trace_capacity(
            current=req.current,
            temp_rise=req.temp_rise,
            copper_oz=req.copper_oz,
            length_mm=req.length_mm,
            is_internal=req.is_internal,
            temp_amb=req.temp_amb
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PcbViaAnalysisRequest(BaseModel):
    dia_mm: float
    plating_um: float
    height_mm: float
    count: int
    current: float
    temp_rise: float
    is_internal: bool = False
    is_solder_filled: bool = False
    pad_dia_mm: Optional[float] = None
    anti_pad_dia_mm: Optional[float] = None


@app.post("/api/calculate/pcb_toolbox/via")
def calculate_pcb_via_analysis_endpoint(req: PcbViaAnalysisRequest):
    try:
        return calc_pcb_via_analysis(
            dia_mm=req.dia_mm,
            plating_um=req.plating_um,
            height_mm=req.height_mm,
            count=req.count,
            current=req.current,
            temp_rise=req.temp_rise,
            is_internal=req.is_internal,
            is_solder_filled=req.is_solder_filled,
            pad_dia_mm=req.pad_dia_mm,
            anti_pad_dia_mm=req.anti_pad_dia_mm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PcbImpedanceRequest(BaseModel):
    er: float
    w_mm: float
    h_mm: float
    t_um: float
    struct_type: str
    is_diff: bool = False
    s_mm: float = 0.2


@app.post("/api/calculate/pcb_toolbox/impedance")
def calculate_pcb_impedance_endpoint(req: PcbImpedanceRequest):
    try:
        return calc_pcb_impedance_analysis(
            er=req.er,
            w_mm=req.w_mm,
            h_mm=req.h_mm,
            t_um=req.t_um,
            struct_type=req.struct_type,
            is_diff=req.is_diff,
            s_mm=req.s_mm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# Wire & Busbar Calculator Endpoints
# ==============================================================================

class WireLitzDesignRequest(BaseModel):
    freq_khz: float
    i_rms: float
    j_density: float
    strand_dia: float
    length_m: float
    temp_c: float
    ac_factor: float
    layers: float = 1.0
    porosity: float = 0.8
    has_outer_serving: Optional[bool] = False


@app.post("/api/calculate/wire_copper_bar/litz")
def calculate_wire_litz_endpoint(req: WireLitzDesignRequest):
    try:
        return calc_wire_litz_design(
            freq_khz=req.freq_khz,
            i_rms=req.i_rms,
            j_density=req.j_density,
            strand_dia=req.strand_dia,
            length_m=req.length_m,
            temp_c=req.temp_c,
            ac_factor=req.ac_factor,
            layers=req.layers,
            porosity=req.porosity,
            has_outer_serving=bool(req.has_outer_serving)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class WireAwgCapacityRequest(BaseModel):
    awg_val: int
    custom_dia: float
    current: float
    length_m: float
    temp_amb: float
    material: str


@app.post("/api/calculate/wire_copper_bar/awg")
def calculate_wire_awg_endpoint(req: WireAwgCapacityRequest):
    try:
        return calc_wire_awg_capacity(
            awg_val=req.awg_val,
            custom_dia=req.custom_dia,
            current=req.current,
            length_m=req.length_m,
            temp_amb=req.temp_amb,
            material=req.material
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BusbarCapacityRequest(BaseModel):
    width_mm: float
    thick_mm: float
    length_mm: float
    current: float


@app.post("/api/calculate/wire_copper_bar/busbar")
def calculate_busbar_endpoint(req: BusbarCapacityRequest):
    try:
        return calc_busbar_capacity(
            width_mm=req.width_mm,
            thick_mm=req.thick_mm,
            length_mm=req.length_mm,
            current=req.current
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# RC Charge & Discharge Calculator Endpoints
# ==============================================================================

class RcStandardRequest(BaseModel):
    us: float
    r: float
    c: float
    tau: float
    r_unit: str
    c_unit: str
    mode: int


@app.post("/api/calculate/rc_charge/standard")
def calculate_rc_standard_endpoint(req: RcStandardRequest):
    try:
        return calc_rc_standard(
            us=req.us,
            r=req.r,
            c=req.c,
            tau=req.tau,
            r_unit=req.r_unit,
            c_unit=req.c_unit,
            mode=req.mode
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RcDcPrechargeRequest(BaseModel):
    us: float
    c_uf: float
    t_s: float
    target_type: str
    target_custom: float


@app.post("/api/calculate/rc_charge/dc_precharge")
def calculate_rc_dc_precharge_endpoint(req: RcDcPrechargeRequest):
    try:
        return calc_rc_dc_precharge(
            us=req.us,
            c_uf=req.c_uf,
            t_s=req.t_s,
            target_type=req.target_type,
            target_custom=req.target_custom
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RcAcPrechargeRequest(BaseModel):
    v_rms: float
    c_uf: float
    t_s: float
    i_limit: float


@app.post("/api/calculate/rc_charge/ac_precharge")
def calculate_rc_ac_precharge_endpoint(req: RcAcPrechargeRequest):
    try:
        return calc_rc_ac_precharge(
            v_rms=req.v_rms,
            c_uf=req.c_uf,
            t_s=req.t_s,
            i_limit=req.i_limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RcBusDischargeRequest(BaseModel):
    v_bus: float
    c_bus_uf: float
    v_safe: float
    t_s: float


@app.post("/api/calculate/rc_charge/bus_discharge")
def calculate_rc_bus_discharge_endpoint(req: RcBusDischargeRequest):
    try:
        return calc_rc_bus_discharge(
            v_bus=req.v_bus,
            c_bus_uf=req.c_bus_uf,
            v_safe=req.v_safe,
            t_s=req.t_s
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RcXcapDischargeRequest(BaseModel):
    vac: float
    c_nom_uf: float
    tol_c: float
    tol_r: float
    t_limit: float
    v_safe: float


@app.post("/api/calculate/rc_charge/xcap_discharge")
def calculate_rc_xcap_discharge_endpoint(req: RcXcapDischargeRequest):
    try:
        return calc_rc_xcap_discharge(
            vac=req.vac,
            c_nom_uf=req.c_nom_uf,
            tol_c=req.tol_c,
            tol_r=req.tol_r,
            t_limit=req.t_limit,
            v_safe=req.v_safe
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# Capacitor Toolbox Endpoints
# ==============================================================================

class CapacitorLifetimeRequest(BaseModel):
    l0: float
    t0: float
    ta: float
    dt: float = 0.0
    use_thermal: bool = False
    i_rms: float = 0.0
    esr_mohm: float = 0.0
    rth_kw: float = 0.0
    use_voltage: bool = False
    v_nominal: float = 1.0
    v_actual: float = 1.0
    cap_type: str = "Electrolytic"


@app.post("/api/calculate/capacitor_toolbox/lifetime")
def calculate_capacitor_lifetime_endpoint(req: CapacitorLifetimeRequest):
    try:
        return calc_capacitor_lifetime(
            l0=req.l0,
            t0=req.t0,
            ta=req.ta,
            dt=req.dt,
            use_thermal=req.use_thermal,
            i_rms=req.i_rms,
            esr_mohm=req.esr_mohm,
            rth_kw=req.rth_kw,
            use_voltage=req.use_voltage,
            v_nominal=req.v_nominal,
            v_actual=req.v_actual,
            cap_type=req.cap_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CapacitorRmsComponent(BaseModel):
    name: str
    freq: str
    i_rms: float


class CapacitorRmsSumRequest(BaseModel):
    components: list[CapacitorRmsComponent]


@app.post("/api/calculate/capacitor_toolbox/rms_sum")
def calculate_capacitor_rms_sum_endpoint(req: CapacitorRmsSumRequest):
    try:
        comp_list = [item.model_dump() for item in req.components]
        return calc_capacitor_rms_sum(components=comp_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CapacitorTopologyRmsRequest(BaseModel):
    mode: str
    vin: float
    vout: float
    iout: float
    duty: float
    lir: float
    m: float
    pf: float
    esr_mohm: float
    rth: float
    ta: float


@app.post("/api/calculate/capacitor_toolbox/topology_rms")
def calculate_capacitor_topology_rms_endpoint(req: CapacitorTopologyRmsRequest):
    try:
        return calc_capacitor_topology_rms(
            mode=req.mode,
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            duty=req.duty,
            lir=req.lir,
            m=req.m,
            pf=req.pf,
            esr_mohm=req.esr_mohm,
            rth=req.rth,
            ta=req.ta
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CapacitorMlccBiasRequest(BaseModel):
    cnom: float
    vrated: float
    vdc: float
    dielectric: str
    package: str


@app.post("/api/calculate/capacitor_toolbox/mlcc_bias")
def calculate_capacitor_mlcc_bias_endpoint(req: CapacitorMlccBiasRequest):
    try:
        return calc_capacitor_mlcc_bias(
            cnom=req.cnom,
            vrated=req.vrated,
            vdc=req.vdc,
            dielectric=req.dielectric,
            package=req.package
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CapacitorHoldupRequest(BaseModel):
    v_start: float
    v_stop: float
    p_out: float
    eff: float
    esr: float
    target_val: float
    is_calc_cap: bool


@app.post("/api/calculate/capacitor_toolbox/holdup")
def calculate_capacitor_holdup_endpoint(req: CapacitorHoldupRequest):
    try:
        return calc_capacitor_holdup(
            v_start=req.v_start,
            v_stop=req.v_stop,
            p_out=req.p_out,
            eff=req.eff,
            esr=req.esr,
            target_val=req.target_val,
            is_calc_cap=req.is_calc_cap
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# 电阻综合工具箱与 L/C 基础理论 API 注册
# ==============================================================================

class ResistorDividerTheoryRequest(BaseModel):
    vin: float
    vout: float
    r1: float
    r2: float
    target_calc: str
    pkg_power: float
    qty_r1: int
    qty_r2: int

@app.post("/api/calculate/resistor_toolbox/theory")
def calculate_resistor_divider_theory_endpoint(req: ResistorDividerTheoryRequest):
    try:
        return calc_resistor_divider_theory(
            vin=req.vin,
            vout=req.vout,
            r1=req.r1,
            r2=req.r2,
            target_calc=req.target_calc,
            pkg_power=req.pkg_power,
            qty_r1=req.qty_r1,
            qty_r2=req.qty_r2
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ResistorDividerFindRequest(BaseModel):
    vin: float
    vout: float
    max_error_percent: float

@app.post("/api/calculate/resistor_toolbox/find")
def calculate_resistor_divider_find_endpoint(req: ResistorDividerFindRequest):
    try:
        return calc_resistor_divider_find(
            vin=req.vin,
            vout=req.vout,
            max_error_percent=req.max_error_percent
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ResistorWcaRequest(BaseModel):
    vref: float
    vref_tol: float
    ibias: float
    r1: float
    r1_tol: float
    r2: float
    r2_tol: float

@app.post("/api/calculate/resistor_toolbox/wca")
def calculate_resistor_wca_endpoint(req: ResistorWcaRequest):
    try:
        return calc_resistor_wca(
            vref=req.vref,
            vref_tol=req.vref_tol,
            ibias=req.ibias,
            r1=req.r1,
            r1_tol=req.r1_tol,
            r2=req.r2,
            r2_tol=req.r2_tol
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ResistorCombinerRequest(BaseModel):
    target_val: float
    comp_type: str
    series_type: str

@app.post("/api/calculate/resistor_toolbox/combiner")
def calculate_resistor_combiner_endpoint(req: ResistorCombinerRequest):
    try:
        return calc_resistor_combiner(
            target_val=req.target_val,
            comp_type=req.comp_type,
            series_type=req.series_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ResistorStandardFindRequest(BaseModel):
    val_str: str
    series_type: str

@app.post("/api/calculate/resistor_toolbox/standard_find")
def calculate_resistor_standard_find_endpoint(req: ResistorStandardFindRequest):
    try:
        return calc_resistor_standard_find(
            val_str=req.val_str,
            series_type=req.series_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ResistorPulseRequest(BaseModel):
    p_peak: float
    t_ms: float
    energy: float
    mode: str
    package: str

@app.post("/api/calculate/resistor_toolbox/pulse")
def calculate_resistor_pulse_endpoint(req: ResistorPulseRequest):
    try:
        return calc_resistor_pulse_withstand(
            p_peak=req.p_peak,
            t_ms=req.t_ms,
            energy=req.energy,
            mode=req.mode,
            package=req.package
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LcTimeDomainRequest(BaseModel):
    mode: str
    fsw: float
    d: float
    l: float
    di: float
    dt: float
    i_inst: float
    c: float
    dv: float
    v_inst: float
    calc_target: str

@app.post("/api/calculate/lc_basics/time_domain")
def calculate_lc_time_domain_endpoint(req: LcTimeDomainRequest):
    try:
        return calc_lc_time_domain(
            mode=req.mode,
            fsw=req.fsw,
            d=req.d,
            l=req.l,
            di=req.di,
            dt=req.dt,
            i_inst=req.i_inst,
            c=req.c,
            dv=req.dv,
            v_inst=req.v_inst,
            calc_target=req.calc_target
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LcReactanceRequest(BaseModel):
    mode: str
    freq: float
    freq_unit: str
    l: float
    xl: float
    c: float
    xc: float

@app.post("/api/calculate/lc_basics/reactance")
def calculate_lc_reactance_endpoint(req: LcReactanceRequest):
    try:
        return calc_lc_reactance(
            mode=req.mode,
            freq=req.freq,
            freq_unit=req.freq_unit,
            l=req.l,
            xl=req.xl,
            c=req.c,
            xc=req.xc
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# 通用磁性电感设计 API
# ==============================================================================

class MagInductorCcmRequest(BaseModel):
    vin: float
    vout: float
    iout: float
    fsw_hz: float
    k_ripple: float

@app.post("/api/calculate/mag_inductor/ccm")
def calculate_mag_inductor_ccm_endpoint(req: MagInductorCcmRequest):
    try:
        return calculate_buck_ccm(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_hz=req.fsw_hz,
            k_ripple=req.k_ripple
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagInductorGapRequest(BaseModel):
    ae_mm2: float
    turns: int
    target_l_uh: float
    window_h_mm: float
    le_mm: float
    ur: float
    mode: str

@app.post("/api/calculate/mag_inductor/gap")
def calculate_mag_inductor_gap_endpoint(req: MagInductorGapRequest):
    try:
        return calculate_gap_and_fringing(
            ae_mm2=req.ae_mm2,
            turns=req.turns,
            target_l_uh=req.target_l_uh,
            window_h_mm=req.window_h_mm,
            le_mm=req.le_mm,
            ur=req.ur,
            mode=req.mode
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagInductorAirCoreRequest(BaseModel):
    dia_mm: float
    turns: int
    wire_d_mm: float
    length_mm: float
    close_wound: bool

@app.post("/api/calculate/mag_inductor/air_core")
def calculate_mag_inductor_air_core_endpoint(req: MagInductorAirCoreRequest):
    try:
        return calculate_air_core_inductor(
            dia_mm=req.dia_mm,
            turns=req.turns,
            wire_d_mm=req.wire_d_mm,
            length_mm=req.length_mm,
            close_wound=req.close_wound
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagInductorAirCoreTurnsRequest(BaseModel):
    target_l_uh: float
    dia_mm: float
    wire_d_mm: float
    length_mm: float
    close_wound: bool

@app.post("/api/calculate/mag_inductor/air_core_turns")
def calculate_mag_inductor_air_core_turns_endpoint(req: MagInductorAirCoreTurnsRequest):
    try:
        return calculate_air_core_turns(
            target_l_uh=req.target_l_uh,
            dia_mm=req.dia_mm,
            wire_d_mm=req.wire_d_mm,
            length_mm=req.length_mm,
            close_wound=req.close_wound
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagInductorPlanarRequest(BaseModel):
    shape: str
    turns: int
    w_mm: float
    s_mm: float
    din_mm: float
    t_cu_mm: float

@app.post("/api/calculate/mag_inductor/planar")
def calculate_mag_inductor_planar_endpoint(req: MagInductorPlanarRequest):
    try:
        return calculate_planar_inductor(
            shape=req.shape,
            turns=req.turns,
            w_mm=req.w_mm,
            s_mm=req.s_mm,
            din_mm=req.din_mm,
            t_cu_mm=req.t_cu_mm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagInductorDcBiasRequest(BaseModel):
    coefs: list
    l0_uh: float
    turns: int
    le_mm: float
    i_max: float
    i_design: float
    steps: int = 50

@app.post("/api/calculate/mag_inductor/dc_bias")
def calculate_mag_inductor_dc_bias_endpoint(req: MagInductorDcBiasRequest):
    try:
        return calculate_dc_bias_curve(
            coefs=req.coefs,
            l0_uh=req.l0_uh,
            turns=req.turns,
            le_mm=req.le_mm,
            i_max=req.i_max,
            i_design=req.i_design,
            steps=req.steps
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagInductorLitzRequest(BaseModel):
    i_rms_a: float
    f_hz: float
    layers: float = 1.0

@app.post("/api/calculate/mag_inductor/litz")
def calculate_mag_inductor_litz_endpoint(req: MagInductorLitzRequest):
    try:
        return optimize_litz_wire(
            i_rms_a=req.i_rms_a,
            f_hz=req.f_hz,
            layers=req.layers
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagInductorCoupledRequest(BaseModel):
    vin: float
    vout: float
    iout: float
    fsw_hz: float
    L_self_uh: float
    coupled_coeff: float
    ae_mm2: float
    le_mm: float
    ur: float
    turns: int

@app.post("/api/calculate/mag_inductor/coupled")
def calculate_mag_inductor_coupled_endpoint(req: MagInductorCoupledRequest):
    try:
        return calculate_coupled_inductor(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            fsw_hz=req.fsw_hz,
            L_self_uh=req.L_self_uh,
            coupled_coeff=req.coupled_coeff,
            ae_mm2=req.ae_mm2,
            le_mm=req.le_mm,
            ur=req.ur,
            turns=req.turns
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagTransformerApRequest(BaseModel):
    pout: float
    fsw_khz: float
    db_t: float
    j_amm2: float
    k_topo: float

@app.post("/api/calculate/mag_transformer/ap")
def calculate_mag_transformer_ap_endpoint(req: MagTransformerApRequest):
    try:
        return calculate_transformer_ap(
            pout=req.pout,
            fsw_khz=req.fsw_khz,
            db_t=req.db_t,
            j_amm2=req.j_amm2,
            k_topo=req.k_topo
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagTransformerFillRequest(BaseModel):
    win_w: float
    win_d: float
    turns: float
    wire_od: float
    strands: float
    tape_thickness: float

@app.post("/api/calculate/mag_transformer/fill")
def calculate_mag_transformer_fill_endpoint(req: MagTransformerFillRequest):
    try:
        return calculate_transformer_fill(
            win_w=req.win_w,
            win_d=req.win_d,
            turns=req.turns,
            wire_od=req.wire_od,
            strands=req.strands,
            tape_thickness=req.tape_thickness
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagTransformerCoreLossRequest(BaseModel):
    volume_cm3: float
    f_khz: float
    b_t: float
    k_stein: float
    alpha: float
    beta: float

@app.post("/api/calculate/mag_transformer/core_loss")
def calculate_mag_transformer_core_loss_endpoint(req: MagTransformerCoreLossRequest):
    try:
        return calculate_transformer_core_loss(
            volume_cm3=req.volume_cm3,
            f_khz=req.f_khz,
            b_t=req.b_t,
            k_stein=req.k_stein,
            alpha=req.alpha,
            beta=req.beta
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagTransformerForwardRequest(BaseModel):
    topo: str
    vin_min: float
    vout: float
    iout: float
    fsw_khz: float
    dmax: float
    bpeak: float
    ae_mm2: float
    aw_mm2: float

@app.post("/api/calculate/mag_transformer/forward")
def calculate_mag_transformer_forward_endpoint(req: MagTransformerForwardRequest):
    try:
        from backend.formula import calc_mag_transformer_forward
        return calc_mag_transformer_forward(
            topo=req.topo,
            vin_min=req.vin_min,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            dmax=req.dmax,
            bpeak=req.bpeak,
            ae_mm2=req.ae_mm2,
            aw_mm2=req.aw_mm2
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagTransformerFlybackRequest(BaseModel):
    vin: float
    vor: float
    vout: float
    iout: float
    fsw_khz: float
    krf: float
    bmax: float
    ae_mm2: float

@app.post("/api/calculate/mag_transformer/flyback")
def calculate_mag_transformer_flyback_endpoint(req: MagTransformerFlybackRequest):
    try:
        from backend.formula import calc_mag_transformer_flyback
        return calc_mag_transformer_flyback(
            vin=req.vin,
            vor=req.vor,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            krf=req.krf,
            bmax=req.bmax,
            ae_mm2=req.ae_mm2
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagTransformerLeakageRequest(BaseModel):
    turns: int
    mlt_mm: float
    bw_mm: float
    hp_mm: float
    hs_mm: float
    tins_mm: float
    is_sandwich: bool
    interleave_m: Optional[int] = 2

@app.post("/api/calculate/mag_transformer/leakage")
def calculate_mag_transformer_leakage_endpoint(req: MagTransformerLeakageRequest):
    try:
        return calculate_transformer_leakage(
            turns=req.turns,
            mlt_mm=req.mlt_mm,
            bw_mm=req.bw_mm,
            hp_mm=req.hp_mm,
            hs_mm=req.hs_mm,
            tins_mm=req.tins_mm,
            is_sandwich=req.is_sandwich,
            interleave_m=req.interleave_m or 2
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagTransformerSteinmetzFitRequest(BaseModel):
    f_list: list
    b_list: list
    pv_list: list

@app.post("/api/calculate/mag_transformer/fit")
def calculate_mag_transformer_fit_endpoint(req: MagTransformerSteinmetzFitRequest):
    try:
        return calculate_steinmetz_fit(
            f_list=req.f_list,
            b_list=req.b_list,
            pv_list=req.pv_list
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MagLlcIntegrationRequest(BaseModel):
    turns_p: float
    turns_s: float
    l_w_mm: float
    b_w_mm: float
    delta_mm: float
    h_p_mm: float
    h_s_mm: float
    fsw_khz: float
    d_litz_mm: float
    layers: float
    l_g_mm: float
    d_gap_dist_mm: float
    i_rms_a: float = 1.0

@app.post("/api/calculate/mag_transformer/llc_integration")
def calculate_mag_transformer_llc_integration_endpoint(req: MagLlcIntegrationRequest):
    try:
        return calc_llc_magnetic_integration(
            turns_p=req.turns_p,
            turns_s=req.turns_s,
            l_w_mm=req.l_w_mm,
            b_w_mm=req.b_w_mm,
            delta_mm=req.delta_mm,
            h_p_mm=req.h_p_mm,
            h_s_mm=req.h_s_mm,
            fsw_khz=req.fsw_khz,
            d_litz_mm=req.d_litz_mm,
            layers=req.layers,
            l_g_mm=req.l_g_mm,
            d_gap_dist_mm=req.d_gap_dist_mm,
            i_rms_a=req.i_rms_a
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerTopologyLlcDesignRequest(BaseModel):
    v_in_min: float
    v_in_max: float
    v_in_nom: float
    v_out: float
    i_out: float
    f_r_hz: float
    k_ratio: float = 5.0
    q_guess: float = 0.45
    half_bridge: bool = False

@app.post("/api/calculate/power_topology/llc_design")
def calculate_power_topology_llc_design_endpoint(req: PowerTopologyLlcDesignRequest):
    try:
        return design_llc_tank(
            v_in_min=req.v_in_min,
            v_in_max=req.v_in_max,
            v_in_nom=req.v_in_nom,
            v_out=req.v_out,
            i_out=req.i_out,
            f_r_hz=req.f_r_hz,
            k_ratio=req.k_ratio,
            q_guess=req.q_guess,
            half_bridge=req.half_bridge
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerTopologyLlcGainRequest(BaseModel):
    lr_uh: float
    cr_nf: float
    lm_uh: float
    turns_ratio_n: float
    r_load_ohm: float
    f_min_khz: float
    f_max_khz: float
    points_count: int = 100

@app.post("/api/calculate/power_topology/llc_gain")
def calculate_power_topology_llc_gain_endpoint(req: PowerTopologyLlcGainRequest):
    try:
        return calculate_llc_gain_points(
            lr_uh=req.lr_uh,
            cr_nf=req.cr_nf,
            lm_uh=req.lm_uh,
            turns_ratio_n=req.turns_ratio_n,
            r_load_ohm=req.r_load_ohm,
            f_min_khz=req.f_min_khz,
            f_max_khz=req.f_max_khz,
            points_count=req.points_count
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerTopologyPsfbZvsRequest(BaseModel):
    vin: float
    vout: float
    iout: float
    n_ratio: float
    lr_uh: float
    coss_pf: float
    ctr_pf: float
    tdead_ns: float

@app.post("/api/calculate/power_topology/psfb_zvs")
def calculate_power_topology_psfb_zvs_endpoint(req: PowerTopologyPsfbZvsRequest):
    try:
        return calculate_psfb_zvs_check(
            vin=req.vin,
            vout=req.vout,
            iout=req.iout,
            n_ratio=req.n_ratio,
            lr_uh=req.lr_uh,
            coss_pf=req.coss_pf,
            ctr_pf=req.ctr_pf,
            tdead_ns=req.tdead_ns
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerTopologyPfcInductorRequest(BaseModel):
    vac_min: float
    vbus: float
    pout: float
    eff: float
    fsw_khz: float
    k_ripple: float
    is_crm: bool

@app.post("/api/calculate/power_topology/pfc_inductor")
def calculate_power_topology_pfc_inductor_endpoint(req: PowerTopologyPfcInductorRequest):
    try:
        return calculate_pfc_inductor_sizing(
            vac_min=req.vac_min,
            vbus=req.vbus,
            pout=req.pout,
            eff=req.eff,
            fsw_khz=req.fsw_khz,
            k_ripple=req.k_ripple,
            is_crm=req.is_crm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerTopologyLlcLoopRequest(BaseModel):
    vin_nom: float
    vout: float
    pout: float
    fr_khz: float
    fsw_khz: float
    k_ratio: float
    q_nom: float
    n_ratio: float
    is_hb: bool
    k_vco: float
    c_uf: float
    rc_esr_mohm: float
    comp_kp: float
    comp_ki: float

@app.post("/api/calculate/power_topology/llc_loop")
def calculate_power_topology_llc_loop_endpoint(req: PowerTopologyLlcLoopRequest):
    try:
        import numpy as np
        res = calc_llc_vco_loop(
            vin_nom=req.vin_nom,
            vout=req.vout,
            pout=req.pout,
            fr_khz=req.fr_khz,
            fsw_khz=req.fsw_khz,
            k_ratio=req.k_ratio,
            q_nom=req.q_nom,
            n_ratio=req.n_ratio,
            is_hb=req.is_hb,
            k_vco=req.k_vco,
            c_uf=req.c_uf,
            rc_esr_mohm=req.rc_esr_mohm,
            comp_kp=req.comp_kp,
            comp_ki=req.comp_ki
        )
        
        return {
            "f_vals": res["f_vals"].tolist(),
            "g_vc0": float(res["g_vc0"]),
            "f_p_load": float(res["f_p_load"]),
            "f_beat": float(res["f_beat"]),
            "f_z": float(res["f_z"]),
            "mag_db": (20.0 * np.log10(np.abs(res["T_loop"]))).tolist(),
            "phase_deg": (np.angle(res["T_loop"], deg=True)).tolist(),
            "cl_mag_db": (20.0 * np.log10(np.abs(res["T_cl"]))).tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerLlcMultiOutRequest(BaseModel):
    vin_nom: float
    vin_min: float
    vin_max: float
    vbus_mid: float
    fr_khz: float
    k_ratio: float
    q_guess: float
    hb_mode: bool
    b1_vout: float
    b1_iout: float
    b1_fsw_khz: float
    b1_k_ripple: float
    b2_vout: float
    b2_iout: float
    b2_fsw_khz: float
    b2_k_ripple: float
    ldo_vout: float
    ldo_iout: float

@app.post("/api/calculate/power_llc_multi_out/cascade")
def calculate_power_llc_multi_out_endpoint(req: PowerLlcMultiOutRequest):
    try:
        return calc_llc_multi_out(
            vin_nom=req.vin_nom,
            vin_min=req.vin_min,
            vin_max=req.vin_max,
            vbus_mid=req.vbus_mid,
            fr_khz=req.fr_khz,
            k_ratio=req.k_ratio,
            q_guess=req.q_guess,
            hb_mode=req.hb_mode,
            b1_vout=req.b1_vout,
            b1_iout=req.b1_iout,
            b1_fsw_khz=req.b1_fsw_khz,
            b1_k_ripple=req.b1_k_ripple,
            b2_vout=req.b2_vout,
            b2_iout=req.b2_iout,
            b2_fsw_khz=req.b2_fsw_khz,
            b2_k_ripple=req.b2_k_ripple,
            ldo_vout=req.ldo_vout,
            ldo_iout=req.ldo_iout
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))











# ==========================================
# Batch 2 - Power Topologies & Multi-phase Circuits
# ==========================================

class PowerInverterRequest(BaseModel):
    is_3phase: bool
    vdc: float
    vac: float
    pout: float
    fout: float
    fsw_khz: float
    lir_pct: float
    mod_method: str
    f_cutoff_khz: float
    level_type: str = "2-Level"

@app.post("/api/calculate/power_inverter")
def calculate_power_inverter_endpoint(req: PowerInverterRequest):
    try:
        from backend.formula import calc_single_phase_inverter, calc_three_phase_inverter
        if req.is_3phase:
            return calc_three_phase_inverter(
                vdc=req.vdc,
                vac_line=req.vac,
                pout=req.pout,
                fsw_khz=req.fsw_khz,
                lir_pct=req.lir_pct,
                mod_method=req.mod_method,
                f_cutoff_khz=req.f_cutoff_khz,
                level_type=req.level_type
            )
        else:
            return calc_single_phase_inverter(
                vdc=req.vdc,
                vac=req.vac,
                pout=req.pout,
                fsw_khz=req.fsw_khz,
                lir_pct=req.lir_pct,
                mod_method=req.mod_method,
                f_cutoff_khz=req.f_cutoff_khz,
                level_type=req.level_type
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerDualBoostPfcRequest(BaseModel):
    vac_min: float
    vac_max: float
    vbus: float
    pout: float
    eff: float
    fsw_khz: float
    k_ripple: float
    mode: str
    c_uf: float
    esr_mohm: float
    t_hold_ms: float = 20.0
    f_line: float = 50.0

@app.post("/api/calculate/power_dual_boost_pfc")
def calculate_power_dual_boost_pfc_endpoint(req: PowerDualBoostPfcRequest):
    try:
        from backend.formula import calc_dual_boost_pfc
        return calc_dual_boost_pfc(
            vac_min=req.vac_min,
            vac_max=req.vac_max,
            vbus=req.vbus,
            pout=req.pout,
            eff=req.eff,
            fsw_khz=req.fsw_khz,
            k_ripple=req.k_ripple,
            mode=req.mode,
            c_uf=req.c_uf,
            esr_mohm=req.esr_mohm,
            t_hold_ms=req.t_hold_ms,
            f_line=req.f_line
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerInterleavedBoostRequest(BaseModel):
    vin_min: float
    vin_nom: float
    vin_max: float
    vout: float
    iout: float
    fsw_khz: float
    lo_uh: float
    co_uf: float
    co_esr_mohm: float

@app.post("/api/calculate/power_interleaved_boost")
def calculate_power_interleaved_boost_endpoint(req: PowerInterleavedBoostRequest):
    try:
        from backend.formula import calc_interleaved_boost
        return calc_interleaved_boost(
            vin_min=req.vin_min,
            vin_nom=req.vin_nom,
            vin_max=req.vin_max,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lo_uh=req.lo_uh,
            co_uf=req.co_uf,
            co_esr_mohm=req.co_esr_mohm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerBidirectionalBuckBoostRequest(BaseModel):
    vhigh: float
    vlow: float
    power: float
    fsw_khz: float
    lir_pct: float
    direction: str = "Forward"

@app.post("/api/calculate/power_bidirectional_buck_boost")
def calculate_power_bidirectional_buck_boost_endpoint(req: PowerBidirectionalBuckBoostRequest):
    try:
        from backend.formula import calc_bidirectional_buck_boost
        return calc_bidirectional_buck_boost(
            vhigh=req.vhigh,
            vlow=req.vlow,
            power=req.power,
            fsw_khz=req.fsw_khz,
            lir_pct=req.lir_pct,
            direction=req.direction
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class PowerNonisolatedBuckBoostRequest(BaseModel):
    vin_min: float
    vin_nom: float
    vin_max: float
    vout: float
    iout: float
    fsw_khz: float
    lo_uh: float
    co_uf: float
    co_esr_mohm: float

@app.post("/api/calculate/power_nonisolated_buck_boost")
def calculate_power_nonisolated_buck_boost_endpoint(req: PowerNonisolatedBuckBoostRequest):
    try:
        from backend.formula import calc_nonisolated_buck_boost
        return calc_nonisolated_buck_boost(
            vin_min=req.vin_min,
            vin_nom=req.vin_nom,
            vin_max=req.vin_max,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lo_uh=req.lo_uh,
            co_uf=req.co_uf,
            co_esr_mohm=req.co_esr_mohm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# 功率器件综合、双脉冲测试与直流母线纹波寿命 API 端点
# ==============================================================================

class GateDriverRequest(BaseModel):
    vcc: float
    vee: float
    rg_ext: float
    rg_int: float
    qg_nc: float
    fsw_khz: float

@app.post("/api/calculate/power_device/driver")
def calculate_gate_driver_endpoint(req: GateDriverRequest):
    try:
        from backend.formula import calc_gate_driver
        return calc_gate_driver(
            vcc=req.vcc,
            vee=req.vee,
            rg_ext=req.rg_ext,
            rg_int=req.rg_int,
            qg_nc=req.qg_nc,
            fsw_khz=req.fsw_khz
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DesatProtectionRequest(BaseModel):
    vth: float
    ichg_ua: float
    tblank_us: float
    vf: float
    vce_sat: float

@app.post("/api/calculate/power_device/desat")
def calculate_desat_protection_endpoint(req: DesatProtectionRequest):
    try:
        from backend.formula import calc_desat_protection
        return calc_desat_protection(
            vth=req.vth,
            ichg_ua=req.ichg_ua,
            tblank_us=req.tblank_us,
            vf=req.vf,
            vce_sat=req.vce_sat
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BootstrapRequest(BaseModel):
    qg_nc: float
    fsw_khz: float
    duty_pct: float
    i_leak_ua: float
    qrr_nc: float
    vdrop: float
    vcc: float
    vf: float

@app.post("/api/calculate/power_device/bootstrap")
def calculate_bootstrap_endpoint(req: BootstrapRequest):
    try:
        from backend.formula import calc_bootstrap_circuit
        return calc_bootstrap_circuit(
            qg_nc=req.qg_nc,
            fsw_khz=req.fsw_khz,
            duty_pct=req.duty_pct,
            i_leak_ua=req.i_leak_ua,
            qrr_nc=req.qrr_nc,
            vdrop=req.vdrop,
            vcc=req.vcc,
            vf=req.vf
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class GdtRequest(BaseModel):
    v_drv: float
    fsw_khz: float
    d_max: float
    ae_mm2: float
    bsat_t: float
    np: float
    al_nh: float

@app.post("/api/calculate/power_device/gdt")
def calculate_gdt_endpoint(req: GdtRequest):
    try:
        from backend.formula import calc_gdt_transformer
        return calc_gdt_transformer(
            v_drv=req.v_drv,
            fsw_khz=req.fsw_khz,
            d_max=req.d_max,
            ae_mm2=req.ae_mm2,
            bsat_t=req.bsat_t,
            np=req.np,
            al_nh=req.al_nh
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DeviceLossRequest(BaseModel):
    device_type: str
    v_act: float
    i_act: float
    f_sw_hz: float
    duty: float
    cond_param: float
    v_test: float
    i_test: float
    e_on_uj: float
    e_off_uj: float

@app.post("/api/calculate/power_device/loss")
def calculate_device_loss_endpoint(req: DeviceLossRequest):
    try:
        from backend.formula import calculate_mosfet_igbt_loss
        return calculate_mosfet_igbt_loss(
            device_type=req.device_type,
            v_act=req.v_act,
            i_act=req.i_act,
            f_sw_hz=req.f_sw_hz,
            duty=req.duty,
            cond_param=req.cond_param,
            v_test=req.v_test,
            i_test=req.i_test,
            e_on_uj=req.e_on_uj,
            e_off_uj=req.e_off_uj
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DeadtimeLossRequest(BaseModel):
    vsd: float
    i_load: float
    f_sw_hz: float
    t_dt_on_ns: float
    t_dt_off_ns: float

@app.post("/api/calculate/power_device/deadtime_loss")
def calculate_deadtime_loss_endpoint(req: DeadtimeLossRequest):
    try:
        from backend.formula import calculate_deadtime_loss
        return calculate_deadtime_loss(
            vsd=req.vsd,
            i_load=req.i_load,
            f_sw_hz=req.f_sw_hz,
            t_dt_on_ns=req.t_dt_on_ns,
            t_dt_off_ns=req.t_dt_off_ns
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class MillerRiskRequest(BaseModel):
    c_rss_pf: float
    c_iss_pf: float
    vth_min: float
    rg_off: float
    dv_dt_vns: float

@app.post("/api/calculate/power_device/miller_risk")
def calculate_miller_risk_endpoint(req: MillerRiskRequest):
    try:
        from backend.formula import evaluate_miller_risk
        return evaluate_miller_risk(
            c_rss_pf=req.c_rss_pf,
            c_iss_pf=req.c_iss_pf,
            vth_min=req.vth_min,
            rg_off=req.rg_off,
            dv_dt_vns=req.dv_dt_vns
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class FosterZthRequest(BaseModel):
    pulse_power: float
    pulse_time_ms: float
    t_init: float
    rc_elements: list
    repetitive: bool
    freq_hz: float
    duty: float

@app.post("/api/calculate/power_device/zth")
def calculate_foster_zth_endpoint(req: FosterZthRequest):
    try:
        from backend.formula import calculate_foster_zth
        return calculate_foster_zth(
            pulse_power=req.pulse_power,
            pulse_time_ms=req.pulse_time_ms,
            t_init=req.t_init,
            rc_elements=req.rc_elements,
            repetitive=req.repetitive,
            freq_hz=req.freq_hz,
            duty=req.duty
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DiodeLossRequest(BaseModel):
    vr: float
    if_val: float
    fsw_hz: float
    duty: float
    vf: float
    qrr_nc: float

@app.post("/api/calculate/power_device/diode_loss")
def calculate_diode_loss_endpoint(req: DiodeLossRequest):
    try:
        from backend.formula import calculate_diode_loss
        return calculate_diode_loss(
            vr=req.vr,
            if_val=req.if_val,
            fsw_hz=req.fsw_hz,
            duty=req.duty,
            vf=req.vf,
            qrr_nc=req.qrr_nc
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SoaSafetyRequest(BaseModel):
    vds: float
    id_curr: float
    t_ms: float
    tc: float
    tj_max: float
    zth: float

@app.post("/api/calculate/power_device/soa_safety")
def calculate_soa_safety_endpoint(req: SoaSafetyRequest):
    try:
        from backend.formula import check_soa_safety
        return check_soa_safety(
            vds=req.vds,
            id_curr=req.id_curr,
            t_ms=req.t_ms,
            tc=req.tc,
            tj_max=req.tj_max,
            zth=req.zth
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CoupledSolverRequest(BaseModel):
    device_type: str
    v_act: float
    i_act: float
    f_sw_hz: float
    duty: float
    cond_param_25: float
    v_test: float
    i_test: float
    e_on_uj: float
    e_off_uj: float
    t_amb: float
    r_jc: float
    r_cs: float
    r_sa: float
    alpha: float
    max_iter: int = 20
    tolerance: float = 0.1

@app.post("/api/calculate/power_device/coupled_solver")
def calculate_coupled_solver_endpoint(req: CoupledSolverRequest):
    try:
        from backend.formula import solve_coupled_loss_thermal
        return solve_coupled_loss_thermal(
            device_type=req.device_type,
            v_act=req.v_act,
            i_act=req.i_act,
            f_sw_hz=req.f_sw_hz,
            duty=req.duty,
            cond_param_25=req.cond_param_25,
            v_test=req.v_test,
            i_test=req.i_test,
            e_on_uj=req.e_on_uj,
            e_off_uj=req.e_off_uj,
            t_amb=req.t_amb,
            r_jc=req.r_jc,
            r_cs=req.r_cs,
            r_sa=req.r_sa,
            alpha=req.alpha,
            max_iter=req.max_iter,
            tolerance=req.tolerance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DptPulseWidthsRequest(BaseModel):
    vdc: float
    imax: float
    l_uh: float
    r_mohm: float

@app.post("/api/calculate/power_dpt/pulse_widths")
def calculate_dpt_pulse_widths_endpoint(req: DptPulseWidthsRequest):
    try:
        from backend.formula import calc_dpt_pulse_widths
        return calc_dpt_pulse_widths(
            vdc=req.vdc,
            imax=req.imax,
            l_uh=req.l_uh,
            r_mohm=req.r_mohm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DptSwitchingEvalRequest(BaseModel):
    v_sw: float
    i_sw: float
    dt_v_ns: float
    dt_i_ns: float
    is_turn_on: bool

@app.post("/api/calculate/power_dpt/switching_eval")
def calculate_dpt_switching_eval_endpoint(req: DptSwitchingEvalRequest):
    try:
        from backend.formula import calc_dpt_switching_eval
        return calc_dpt_switching_eval(
            v_sw=req.v_sw,
            i_sw=req.i_sw,
            dt_v_ns=req.dt_v_ns,
            dt_i_ns=req.dt_i_ns,
            is_turn_on=req.is_turn_on
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DclinkInterleavedRequest(BaseModel):
    n: int
    d: float
    i_total: float
    ripple_pct: float

@app.post("/api/calculate/power_dclink/interleaved")
def calculate_dclink_interleaved_endpoint(req: DclinkInterleavedRequest):
    try:
        from backend.formula import calc_dclink_interleaved
        return calc_dclink_interleaved(
            n=req.n,
            d=req.d,
            i_total=req.i_total,
            ripple_pct=req.ripple_pct
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DclinkInverterRequest(BaseModel):
    i_out_rms: float
    vdc: float
    m: float
    pf: float

@app.post("/api/calculate/power_dclink/inverter")
def calculate_dclink_inverter_endpoint(req: DclinkInverterRequest):
    try:
        from backend.formula import calc_dclink_inverter
        return calc_dclink_inverter(
            i_out_rms=req.i_out_rms,
            vdc=req.vdc,
            m=req.m,
            pf=req.pf
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# 5. 电池包与 BMS (Battery Pack & BMS) 接口及路由
# ==============================================================================

class BatteryPackConfigRequest(BaseModel):
    cell_v_nom: float
    cell_v_min: float
    cell_v_max: float
    cell_cap: float
    cell_ir_mohm: float
    mode: str
    s: int
    p: int
    target_v: float
    target_wh: float

@app.post("/api/calculate/battery_pack/config")
def calculate_battery_pack_config_endpoint(req: BatteryPackConfigRequest):
    try:
        from backend.formula import calc_battery_pack_config
        return calc_battery_pack_config(
            cell_v_nom=req.cell_v_nom,
            cell_v_min=req.cell_v_min,
            cell_v_max=req.cell_v_max,
            cell_cap=req.cell_cap,
            cell_ir_mohm=req.cell_ir_mohm,
            mode=req.mode,
            s=req.s,
            p=req.p,
            target_v=req.target_v,
            target_wh=req.target_wh
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BatteryPackLoadRequest(BaseModel):
    v_nom: float
    v_min: float
    ir_ohm: float
    ah: float
    r_busbar_mohm: float
    mode: str
    load_curr: float
    load_power: float

@app.post("/api/calculate/battery_pack/load")
def calculate_battery_pack_load_endpoint(req: BatteryPackLoadRequest):
    try:
        from backend.formula import calc_battery_pack_load
        return calc_battery_pack_load(
            v_nom=req.v_nom,
            v_min=req.v_min,
            ir_ohm=req.ir_ohm,
            ah=req.ah,
            r_busbar_mohm=req.r_busbar_mohm,
            mode=req.mode,
            load_curr=req.load_curr,
            load_power=req.load_power
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BatteryPackBalanceRequest(BaseModel):
    cap: float
    q_diff_pct: float
    time_h: float
    v_cell: float

@app.post("/api/calculate/battery_pack/balance")
def calculate_battery_pack_balance_endpoint(req: BatteryPackBalanceRequest):
    try:
        from backend.formula import calc_battery_pack_balance
        return calc_battery_pack_balance(
            cap=req.cap,
            q_diff_pct=req.q_diff_pct,
            time_h=req.time_h,
            v_cell=req.v_cell
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# 6. 三相交流与 PLL (3-Phase & PLL) 接口及路由
# ==============================================================================

class ThreePhaseParamsRequest(BaseModel):
    v_ll: float
    i_line: float
    pf: float
    freq: float
    connection: str

@app.post("/api/calculate/power_ac_3ph/convert")
def calculate_three_phase_params_endpoint(req: ThreePhaseParamsRequest):
    try:
        from backend.formula import calc_three_phase_params
        return calc_three_phase_params(
            v_ll=req.v_ll,
            i_line=req.i_line,
            pf=req.pf,
            freq=req.freq,
            connection=req.connection
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ThreePhasePfcRequest(BaseModel):
    p_kw: float
    v_ll: float
    pf_old: float
    pf_new: float
    freq: float
    connection: str

@app.post("/api/calculate/power_ac_3ph/pfc")
def calculate_three_phase_pfc_endpoint(req: ThreePhasePfcRequest):
    try:
        from backend.formula import calc_three_phase_pfc
        return calc_three_phase_pfc(
            p_kw=req.p_kw,
            v_ll=req.v_ll,
            pf_old=req.pf_old,
            pf_new=req.pf_new,
            freq=req.freq,
            connection=req.connection
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ThreePhaseYdRequest(BaseModel):
    z_val: float
    direction: str

@app.post("/api/calculate/power_ac_3ph/yd")
def calculate_three_phase_yd_endpoint(req: ThreePhaseYdRequest):
    try:
        from backend.formula import calc_three_phase_yd
        return calc_three_phase_yd(
            z_val=req.z_val,
            direction=req.direction
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ThreePhaseCoordinateRequest(BaseModel):
    a: float
    b: float
    c: float
    theta_deg: float
    mode: Optional[str] = "amplitude_invariant"

@app.post("/api/calculate/power_ac_3ph/coordinate")
def calculate_three_phase_coordinate_endpoint(req: ThreePhaseCoordinateRequest):
    try:
        from backend.formula import calc_three_phase_coordinate
        return calc_three_phase_coordinate(
            a=req.a,
            b=req.b,
            c=req.c,
            theta_deg=req.theta_deg,
            mode=req.mode or "amplitude_invariant"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ThreePhasePllRequest(BaseModel):
    v_m: float
    f_bw: float
    zeta: float

@app.post("/api/calculate/power_ac_3ph/pll")
def calculate_three_phase_pll_endpoint(req: ThreePhasePllRequest):
    try:
        from backend.formula import calc_three_phase_pll
        return calc_three_phase_pll(
            v_m=req.v_m,
            f_bw=req.f_bw,
            zeta=req.zeta
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# 7. 效率损耗预算 (Efficiency Budget) 接口及路由
# ==============================================================================

class EfficiencyBudgetRequest(BaseModel):
    vout: float
    iout: float
    l_sw: float
    l_mag: float
    l_rect: float
    l_cap: float
    l_ctrl: float
    l_misc: float
    vin: Optional[float] = 24.0

@app.post("/api/calculate/power_budget/calc")
def calculate_efficiency_budget_endpoint(req: EfficiencyBudgetRequest):
    try:
        from backend.formula import calc_efficiency_budget
        return calc_efficiency_budget(
            vout=req.vout,
            iout=req.iout,
            l_sw=req.l_sw,
            l_mag=req.l_mag,
            l_rect=req.l_rect,
            l_cap=req.l_cap,
            l_ctrl=req.l_ctrl,
            l_misc=req.l_misc,
            vin=req.vin or 24.0
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LlcResonantRequest(BaseModel):
    vin_min: float
    vin_max: float
    vin_nom: float
    vout: float
    iout: float
    fr_khz: float
    k_ratio: float
    q_design: float
    topology_mode: str = "full_bridge"
    actual_lr_uh: Optional[float] = 0.0
    actual_lm_uh: Optional[float] = 0.0
    actual_cr_nf: Optional[float] = 0.0
    eff: float = 0.95

@app.post("/api/calculate/llc_resonant")
def calculate_llc_resonant_endpoint(req: LlcResonantRequest):
    try:
        from backend.formula import calc_llc_resonant_design
        res = calc_llc_resonant_design(
            vin_min=req.vin_min,
            vin_max=req.vin_max,
            vin_nom=req.vin_nom,
            vout=req.vout,
            iout=req.iout,
            fr_khz=req.fr_khz,
            k_ratio=req.k_ratio,
            q_design=req.q_design,
            topology_mode=req.topology_mode,
            actual_lr_uh=req.actual_lr_uh or 0.0,
            actual_lm_uh=req.actual_lm_uh or 0.0,
            actual_cr_nf=req.actual_cr_nf or 0.0
        )
        
        # 补充系统损耗与热阻核算
        p_loss = req.vout * req.iout * (1.0 - req.eff) / req.eff if req.eff > 0 else 0.0
        r_th_hs = (125.0 - 50.0) / p_loss - 1.2 if p_loss > 0 else 999.0
        if r_th_hs < 2.0:
            if 'drc_warnings' not in res:
                res['drc_warnings'] = []
            res['drc_warnings'].append("⚠️ [热管理] 推荐散热片热阻小于 2.0 °C/W，发热损耗严重，建议采取强迫风冷。")
            
        res['p_loss'] = p_loss
        res['r_th_hs'] = r_th_hs
        return res
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


class FourSwitchBuckBoostRequest(BaseModel):
    vin_min: float
    vin_max: float
    vin_nom: float
    vout: float
    iout: float
    fsw_khz: float
    lo_uh: Optional[float] = 0.0
    co_uf: Optional[float] = 0.0
    esr_mohm: float = 10.0

@app.post("/api/calculate/four_switch_buck_boost")
def calculate_four_switch_buck_boost_endpoint(req: FourSwitchBuckBoostRequest):
    try:
        from backend.formula import calc_four_switch_buck_boost
        return calc_four_switch_buck_boost(
            vin_min=req.vin_min,
            vin_max=req.vin_max,
            vin_nom=req.vin_nom,
            vout=req.vout,
            iout=req.iout,
            fsw_khz=req.fsw_khz,
            lo_uh=req.lo_uh or 0.0,
            co_uf=req.co_uf or 0.0,
            esr_mohm=req.esr_mohm
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

class CoreLossRequest(BaseModel):
    material: str
    fsw_hz: float
    delta_b: float
    duty: float
    ve_cm3: float
    as_cm2: float
    p_copper_w: float
    t_ambient_c: float
    cooling_wind_speed: Optional[float] = 0.0
    custom_k: Optional[float] = None
    custom_alpha: Optional[float] = None
    custom_beta: Optional[float] = None

@app.post("/api/calculate/mag_core_loss")
def calculate_mag_core_loss_endpoint(req: CoreLossRequest):
    try:
        from backend.formula import calculate_core_loss_igse
        return calculate_core_loss_igse(
            material=req.material,
            fsw_hz=req.fsw_hz,
            delta_b=req.delta_b,
            duty=req.duty,
            ve_cm3=req.ve_cm3,
            as_cm2=req.as_cm2,
            p_copper_w=req.p_copper_w,
            t_ambient_c=req.t_ambient_c,
            cooling_wind_speed=req.cooling_wind_speed or 0.0,
            custom_k=req.custom_k,
            custom_alpha=req.custom_alpha,
            custom_beta=req.custom_beta
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

class CoreLossScanRequest(BaseModel):
    material: str
    fsw_hz: float
    delta_b: float
    duty: float
    ve_cm3: float
    as_cm2: float
    p_copper_w: float
    t_ambient_c: float
    cooling_wind_speed: Optional[float] = 0.0
    custom_k: Optional[float] = None
    custom_alpha: Optional[float] = None
    custom_beta: Optional[float] = None
    scan_type: str  # "deltaB" or "duty"

@app.post("/api/calculate/mag_core_loss/scan")
def calculate_mag_core_loss_scan_endpoint(req: CoreLossScanRequest):
    try:
        from backend.formula import calculate_core_loss_igse
        points = 10
        results = []
        
        if req.scan_type == "deltaB":
            db_min = 0.02
            db_max = 0.35
            for i in range(points + 1):
                val = db_min + (i / points) * (db_max - db_min)
                res = calculate_core_loss_igse(
                    material=req.material,
                    fsw_hz=req.fsw_hz,
                    delta_b=val,
                    duty=req.duty,
                    ve_cm3=req.ve_cm3,
                    as_cm2=req.as_cm2,
                    p_copper_w=req.p_copper_w,
                    t_ambient_c=req.t_ambient_c,
                    cooling_wind_speed=req.cooling_wind_speed or 0.0,
                    custom_k=req.custom_k,
                    custom_alpha=req.custom_alpha,
                    custom_beta=req.custom_beta
                )
                results.append({
                    "val": float(round(val, 3)),
                    "p_core_w": res.get("p_core_w", 0.0),
                    "p_total_w": res.get("p_total_w", 0.0),
                    "t_core_c": res.get("t_core_c", 0.0)
                })
        else:
            d_min = 0.05
            d_max = 0.95
            for i in range(points + 1):
                val = d_min + (i / points) * (d_max - d_min)
                res = calculate_core_loss_igse(
                    material=req.material,
                    fsw_hz=req.fsw_hz,
                    delta_b=req.delta_b,
                    duty=val,
                    ve_cm3=req.ve_cm3,
                    as_cm2=req.as_cm2,
                    p_copper_w=req.p_copper_w,
                    t_ambient_c=req.t_ambient_c,
                    cooling_wind_speed=req.cooling_wind_speed or 0.0,
                    custom_k=req.custom_k,
                    custom_alpha=req.custom_alpha,
                    custom_beta=req.custom_beta
                )
                results.append({
                    "val": float(round(val, 2)),
                    "p_core_w": res.get("p_core_w", 0.0),
                    "p_total_w": res.get("p_total_w", 0.0),
                    "t_core_c": res.get("t_core_c", 0.0)
                })
                
        return {
            "results": results
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

class TransientThermalRequest(BaseModel):
    r_vals: list[float]
    tau_vals: list[float]
    pulse_mode: str
    t_case: float
    t_sim_max: float
    p_peak: Optional[float] = 0.0
    duty: Optional[float] = 0.0
    period: Optional[float] = 0.0
    cycles: Optional[int] = 1
    custom_pulses: Optional[list[dict]] = None
    sim_steps: Optional[int] = 500

@app.post("/api/calculate/thermal/foster_transient")
def calculate_transient_thermal_endpoint(req: TransientThermalRequest):
    try:
        from backend.formula import calculate_transient_thermal
        res = calculate_transient_thermal(
            r_vals=req.r_vals,
            tau_vals=req.tau_vals,
            pulse_mode=req.pulse_mode,
            t_case=req.t_case,
            t_sim_max=req.t_sim_max,
            p_peak=req.p_peak or 0.0,
            duty=req.duty or 0.0,
            period=req.period or 0.0,
            cycles=req.cycles or 1,
            custom_pulses=req.custom_pulses,
            sim_steps=req.sim_steps or 500
        )
        
        # 计算平均结温
        tj_vals = res.get("tj_c", [])
        tj_avg = float(sum(tj_vals) / len(tj_vals)) if tj_vals else req.t_case
        
        return {
            # 前端展示字段
            "t_axis": res["t_s"],
            "p_axis": res["p_w"],
            "tj_axis": res["tj_c"],
            "tj_max": res["max_tj_c"],
            "tj_avg": tj_avg,
            # 单元测试兼容字段
            "t_s": res["t_s"],
            "p_w": res["p_w"],
            "tj_c": res["tj_c"],
            "max_tj_c": res["max_tj_c"],
            "delta_tj_max": res["delta_tj_max"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
class MillerTurnOnRequest(BaseModel):
    v_bus: float
    dv_dt_v_ns: float
    c_gd_pf: float
    c_gs_pf: float
    r_g_off_ext: float
    r_g_off_int: float
    r_driver_off: float
    l_g_nh: float
    v_gs_off: float
    v_th: float
    sim_steps: Optional[int] = 400

class GateDriveDeadtimeRequest(BaseModel):
    t_dead_ns: float
    fsw_hz: float
    i_out_a: float
    v_sd_v: float
    v_bus: float
    c_oss_pf: float
    e_on_ref_uj: float
    e_on_current_ref: Optional[float] = 10.0

@app.post("/api/calculate/gate_drive_miller/miller")
def calculate_gate_drive_miller_endpoint(req: MillerTurnOnRequest):
    try:
        from backend.formula import calculate_miller_turn_on
        return calculate_miller_turn_on(
            v_bus=req.v_bus,
            dv_dt_v_ns=req.dv_dt_v_ns,
            c_gd_pf=req.c_gd_pf,
            c_gs_pf=req.c_gs_pf,
            r_g_off_ext=req.r_g_off_ext,
            r_g_off_int=req.r_g_off_int,
            r_driver_off=req.r_driver_off,
            l_g_nh=req.l_g_nh,
            v_gs_off=req.v_gs_off,
            v_th=req.v_th,
            sim_steps=req.sim_steps or 400
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/calculate/gate_drive_miller/deadtime_opt")
def calculate_gate_drive_deadtime_endpoint(req: GateDriveDeadtimeRequest):
    try:
        from backend.formula import calculate_deadtime_loss_opt
        return calculate_deadtime_loss_opt(
            t_dead_ns=req.t_dead_ns,
            fsw_hz=req.fsw_hz,
            i_out_a=req.i_out_a,
            v_sd_v=req.v_sd_v,
            v_bus=req.v_bus,
            c_oss_pf=req.c_oss_pf,
            e_on_ref_uj=req.e_on_ref_uj,
            e_on_current_ref=req.e_on_current_ref or 10.0
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


class DeadTimeSizingRequest(BaseModel):
    v_bus: float
    i_load: float
    f_sw_khz: float
    c_oss_pf: float
    q_oss_nc: Optional[float] = 0.0
    v_sd_v: float
    t_dead_on_ns: float
    t_dead_off_ns: float
    t_d_on_ns: float
    t_d_off_ns: float
    t_r_ns: float
    t_f_ns: float
    q_rr_nc: Optional[float] = 0.0
    t_rr_ns: Optional[float] = 10.0
    r_th_jc: Optional[float] = 1.0
    r_th_cs: Optional[float] = 0.5
    r_th_sa: Optional[float] = 5.0
    t_ambient: Optional[float] = 25.0


class DeadTimeBomRequest(BaseModel):
    v_bus: float
    i_load: float
    f_sw_khz: float
    c_oss_pf: float
    q_oss_nc: Optional[float] = 0.0
    v_sd_v: float
    t_dead_on_ns: float
    t_dead_off_ns: float
    t_d_on_ns: float
    t_d_off_ns: float
    t_r_ns: float
    t_f_ns: float
    q_rr_nc: Optional[float] = 0.0
    t_rr_ns: Optional[float] = 10.0
    r_th_jc: Optional[float] = 1.0
    r_th_cs: Optional[float] = 0.5
    r_th_sa: Optional[float] = 5.0
    t_ambient: Optional[float] = 25.0
    safety_margin_v: Optional[float] = 1.2
    safety_margin_i: Optional[float] = 1.5


@app.post("/api/calculate/dead_time/sizing")
def calculate_deadtime_sizing_endpoint(req: DeadTimeSizingRequest):
    try:
        from backend.formula import calculate_deadtime_sizing
        return calculate_deadtime_sizing(
            v_bus=req.v_bus,
            i_load=req.i_load,
            f_sw_khz=req.f_sw_khz,
            c_oss_pf=req.c_oss_pf,
            q_oss_nc=req.q_oss_nc or 0.0,
            v_sd_v=req.v_sd_v,
            t_dead_on_ns=req.t_dead_on_ns,
            t_dead_off_ns=req.t_dead_off_ns,
            t_d_on_ns=req.t_d_on_ns,
            t_d_off_ns=req.t_d_off_ns,
            t_r_ns=req.t_r_ns,
            t_f_ns=req.t_f_ns,
            q_rr_nc=req.q_rr_nc or 0.0,
            t_rr_ns=req.t_rr_ns or 10.0,
            r_th_jc=req.r_th_jc or 1.0,
            r_th_cs=req.r_th_cs or 0.5,
            r_th_sa=req.r_th_sa or 5.0,
            t_ambient=req.t_ambient or 25.0
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/calculate/dead_time/bom")
def calculate_deadtime_bom_endpoint(req: DeadTimeBomRequest):
    try:
        from database import ComponentDatabase
        from backend.formula import calculate_deadtime_sizing

        min_v = req.v_bus * (req.safety_margin_v or 1.2)
        min_i = req.i_load * (req.safety_margin_i or 1.5)

        db = ComponentDatabase()
        matched_switches = db.get_recommended_switches(min_v=min_v, min_i=min_i)

        results = []
        for sw in matched_switches:
            c_oss_val = sw.get("c_oss", req.c_oss_pf) or req.c_oss_pf
            r_jc_val = sw.get("r_jc", req.r_th_jc) or req.r_th_jc

            calc_res = calculate_deadtime_sizing(
                v_bus=req.v_bus,
                i_load=req.i_load,
                f_sw_khz=req.f_sw_khz,
                c_oss_pf=c_oss_val,
                q_oss_nc=req.q_oss_nc or 0.0,
                v_sd_v=req.v_sd_v,
                t_dead_on_ns=req.t_dead_on_ns,
                t_dead_off_ns=req.t_dead_off_ns,
                t_d_on_ns=req.t_d_on_ns,
                t_d_off_ns=req.t_d_off_ns,
                t_r_ns=req.t_r_ns,
                t_f_ns=req.t_f_ns,
                q_rr_nc=req.q_rr_nc or 0.0,
                t_rr_ns=req.t_rr_ns or 10.0,
                r_th_jc=r_jc_val,
                r_th_cs=req.r_th_cs or 0.5,
                r_th_sa=req.r_th_sa or 5.0,
                t_ambient=req.t_ambient or 25.0
            )

            results.append({
                "name": sw["name"],
                "manufacturer": "Infineon" if "BSC" in sw["name"] or "IPP" in sw["name"] or "IPW" in sw["name"] or "IRF" in sw["name"] else "Cree" if "C3M" in sw["name"] or "C2M" in sw["name"] else "ROHM" if "SCT" in sw["name"] else "Generic",
                "type": sw["type"],
                "v_ds_max": sw["v_ds_max"],
                "i_d_max": sw["i_d_max"],
                "r_ds_on": sw["r_ds_on"],
                "c_oss": c_oss_val,
                "r_jc": r_jc_val,
                "p_total_w": calc_res["p_total_w"],
                "t_j_est_c": calc_res["t_j_est_c"]
            })

        results.sort(key=lambda x: x["p_total_w"])

        return {
            "switches": results,
            "requirements": {
                "min_v": min_v,
                "min_i": min_i
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


class DclinkCapacitorLifeRequest(BaseModel):
    cap_type: str
    l_nominal_h: float
    t_max_c: float
    v_nominal_v: float
    v_actual_v: float
    i_rms_phase_a: float
    m_index: float
    cos_phi: float
    esr_mohm: float
    rth_hotspot_kw: float
    t_ambient_c: float

@app.post("/api/calculate/dclink_capacitor_life")
def calculate_dclink_capacitor_life_endpoint(req: DclinkCapacitorLifeRequest):
    try:
        from backend.formula import calculate_dclink_capacitor_life
        return calculate_dclink_capacitor_life(
            cap_type=req.cap_type,
            l_nominal_h=req.l_nominal_h,
            t_max_c=req.t_max_c,
            v_nominal_v=req.v_nominal_v,
            v_actual_v=req.v_actual_v,
            i_rms_phase_a=req.i_rms_phase_a,
            m_index=req.m_index,
            cos_phi=req.cos_phi,
            esr_mohm=req.esr_mohm,
            rth_hotspot_kw=req.rth_hotspot_kw,
            t_ambient_c=req.t_ambient_c
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# ==================================================================
# ProjectState 保存/载入 API
# ==================================================================
class ProjectSaveRequest(BaseModel):
    filepath: str
    state: dict

class ProjectLoadRequest(BaseModel):
    filepath: str

@app.post("/api/project/save")
def save_project(req: ProjectSaveRequest):
    try:
        import json
        # 确保父目录存在
        dir_name = os.path.dirname(req.filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        with open(req.filepath, 'w', encoding='utf-8') as f:
            json.dump(req.state, f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": f"Project saved successfully to {req.filepath}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/project/load")
def load_project(req: ProjectLoadRequest):
    if not os.path.exists(req.filepath):
        raise HTTPException(status_code=404, detail=f"Project file not found: {req.filepath}")
    try:
        import json
        with open(req.filepath, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        return {"status": "success", "state": state_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def start_stdin_monitor():
    import sys
    import os
    import threading
    
    # Only monitor if not running tests
    if "pytest" in sys.modules or os.environ.get("DAEMON_MODE") == "1":
        return
        
    def monitor():
        try:
            # sys.stdin.read() blocks until EOF when standard input is closed/piped
            sys.stdin.read()
        except Exception:
            pass
        # Suicide when parent process exits/closes stdin pipe
        os._exit(0)
        
    t = threading.Thread(target=monitor, name="ParentProcessMonitor", daemon=True)
    t.start()

start_stdin_monitor()

if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
