-- SQL DDL schema for Hardware Engineering Toolbox database

-- Enable Foreign Key support in SQLite (this must be executed at connection runtime too)
PRAGMA foreign_keys = ON;

-- 1. Manufacturers Table
CREATE TABLE IF NOT EXISTS manufacturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT
);

-- 2. Magnetic Materials Table (for PC40, Sendust, etc.)
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL, -- Ferrite, Powder, Amorphous, etc.
    permeability REAL NOT NULL, -- Initial/effective permeability
    b_sat_25 REAL, -- Saturation flux density at 25 C (Tesla)
    b_sat_100 REAL, -- Saturation flux density at 100 C (Tesla)
    steinmetz_cm_25 REAL, -- Steinmetz parameter Cm at 25 C
    steinmetz_x_25 REAL, -- Steinmetz parameter x at 25 C
    steinmetz_y_25 REAL, -- Steinmetz parameter y at 25 C
    steinmetz_cm_100 REAL, -- Steinmetz parameter Cm at 100 C
    steinmetz_x_100 REAL, -- Steinmetz parameter x at 100 C
    steinmetz_y_100 REAL -- Steinmetz parameter y at 100 C
);

-- 3. Magnetic Cores Table
CREATE TABLE IF NOT EXISTS cores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    shape TEXT NOT NULL, -- EE, EI, PQ, RM, EFD, Toroid, etc.
    material_id INTEGER,
    ae REAL NOT NULL, -- Effective area (mm^2)
    le REAL NOT NULL, -- Effective magnetic path length (mm)
    ve REAL NOT NULL, -- Effective volume (mm^3)
    wa REAL NOT NULL, -- Winding window area (mm^2)
    al REAL, -- Inductance factor (nH/N^2)
    FOREIGN KEY (material_id) REFERENCES materials (id) ON DELETE SET NULL
);

-- 4. Switches Table (MOSFET, SiC MOSFET, GaN HEMT, IGBT, etc.)
CREATE TABLE IF NOT EXISTS switches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer_id INTEGER,
    type TEXT NOT NULL, -- Si, SiC, GaN, IGBT, etc.
    v_ds_max REAL NOT NULL, -- Maximum drain-source voltage (V)
    i_d_max REAL NOT NULL, -- Maximum continuous drain current (A)
    r_ds_on REAL NOT NULL, -- On-state resistance (Ohm)
    q_g REAL, -- Total gate charge (nC)
    c_oss REAL, -- Output capacitance (pF)
    package TEXT, -- TO-247, TO-220, DFN8x8, etc.
    r_jc REAL, -- Junction-to-case thermal resistance (K/W)
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id) ON DELETE SET NULL
);

-- 5. Diodes Table (Schottky, SiC Schottky, Fast Recovery, etc.)
CREATE TABLE IF NOT EXISTS diodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer_id INTEGER,
    type TEXT NOT NULL, -- Schottky, FastRecovery, SiC, etc.
    v_r_max REAL NOT NULL, -- Maximum reverse voltage (V)
    i_f_max REAL NOT NULL, -- Maximum forward current (A)
    v_f REAL NOT NULL, -- Forward voltage drop (V)
    package TEXT, -- TO-220, TO-247, SMA, SMB, etc.
    r_jc REAL, -- Junction-to-case thermal resistance (K/W)
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id) ON DELETE SET NULL
);

-- 6. Capacitors Table (Electrolytic, Film, Ceramic, etc.)
CREATE TABLE IF NOT EXISTS capacitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer_id INTEGER,
    type TEXT NOT NULL, -- Electrolytic, Film, MLCC, etc.
    capacitance REAL NOT NULL, -- Capacitance (F)
    voltage_rating REAL NOT NULL, -- Rated voltage (V)
    esr REAL, -- Equivalent Series Resistance (Ohm)
    esl REAL, -- Equivalent Series Inductance (H)
    ripple_current REAL, -- Rated RMS ripple current (A)
    temp_max REAL, -- Maximum operating temperature (C)
    lifetime_hours INTEGER, -- Rated lifetime at max temperature (hours)
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id) ON DELETE SET NULL
);

-- 5a. Zener Diodes Table
CREATE TABLE IF NOT EXISTS zener_diodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer_id INTEGER,
    vz REAL NOT NULL, -- Nominal Zener Voltage (V)
    izt REAL, -- Test current (mA)
    izk REAL, -- Knee current (mA)
    zzt REAL, -- Dynamic Impedance (Ohm)
    p_d REAL, -- Max Power Dissipation (W)
    package TEXT,
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id) ON DELETE SET NULL
);

-- 5b. TVS Diodes Table
CREATE TABLE IF NOT EXISTS tvs_diodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer_id INTEGER,
    vrwm REAL NOT NULL, -- Reverse Standoff Voltage (V)
    vbr REAL NOT NULL, -- Min Breakdown Voltage (V)
    vc REAL NOT NULL, -- Max Clamping Voltage (V)
    ipp REAL NOT NULL, -- Max Peak Pulse Current (A)
    pppm REAL NOT NULL, -- Peak Pulse Power (W)
    package TEXT,
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id) ON DELETE SET NULL
);

-- 7. Fuses Table
CREATE TABLE IF NOT EXISTS fuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer_id INTEGER,
    i_rated REAL NOT NULL, -- Rated current (A)
    v_rated REAL NOT NULL, -- Rated voltage (V)
    i2t REAL NOT NULL, -- Melting energy I2t (A^2s)
    package TEXT,
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id) ON DELETE SET NULL
);

-- 8. NTC Resistors Table
CREATE TABLE IF NOT EXISTS ntc_resistors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer_id INTEGER,
    r25 REAL NOT NULL, -- Resistance at 25 C (Ohm)
    i_max REAL NOT NULL, -- Max continuous current (A)
    joule_rating REAL NOT NULL, -- Joule energy capacity (J)
    dissipation REAL NOT NULL, -- Dissipation factor (mW/C)
    package TEXT,
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id) ON DELETE SET NULL
);

-- Indexes to optimize queries for components by ratings
CREATE INDEX IF NOT EXISTS idx_switches_ratings ON switches (v_ds_max, i_d_max);
CREATE INDEX IF NOT EXISTS idx_diodes_ratings ON diodes (v_r_max, i_f_max);
CREATE INDEX IF NOT EXISTS idx_capacitors_ratings ON capacitors (voltage_rating, capacitance);
CREATE INDEX IF NOT EXISTS idx_cores_material ON cores (material_id);
CREATE INDEX IF NOT EXISTS idx_cores_shape ON cores (shape);
CREATE INDEX IF NOT EXISTS idx_zeners_vz ON zener_diodes (vz);
CREATE INDEX IF NOT EXISTS idx_tvs_vrwm ON tvs_diodes (vrwm);
CREATE INDEX IF NOT EXISTS idx_fuses_current ON fuses (i_rated);
CREATE INDEX IF NOT EXISTS idx_ntc_r25 ON ntc_resistors (r25);
