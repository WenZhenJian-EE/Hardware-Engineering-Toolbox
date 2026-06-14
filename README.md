# Hardware Engineering Toolbox (Pro v10.4 Modular)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

A comprehensive, modular GUI desktop toolbox for hardware design and power electronics engineers. Built with PyQt5 and Matplotlib, this toolbox contains dozens of specialized calculation and design modules spanning magnetics, power converter topologies, analog/digital control loops, thermal analysis, and compliance/safety standards.

[简体中文](#简体中文) | [English](#english)

---

## English

### Core Features

The toolbox is organized into logical engineering domains, providing instant analytical calculations and interactive plots:

*   **⚡ Power Electronics & Converter Design**
    *   **DCDC Basic Design**: Buck, Boost, and Buck-Boost parameter calculators (inductance, capacitance, ripple).
    *   **Gate Driver Design**: Compute gate charge, driving currents, and gate driver power dissipation.
    *   **Waveform RMS**: RMS, average, and peak value calculators for complex periodic waveforms (triangle, trapezoid, sine, etc.).
    *   **Efficiency Budget**: Aggregate loss analysis across components to estimate system efficiency.
    *   **Double Pulse Test (DPT)**: Parameter configurations and load calculations for semiconductor switching tests.
    *   **DC-Link Ripple**: DC-Link capacitor ripple current estimation under various load conditions.
*   **🧲 Magnetic Components Design**
    *   **Inductor Design**: Core selection, winding counts, air gap calculations, and saturation checks.
    *   **Transformer Design**: Core dimensions, primary/secondary turns, copper/core loss estimation.
    *   **LLC & PFC Magnetics**: Advanced resonance frequency and boost inductor design helpers.
*   **📈 Control Loops & Filters**
    *   **PID Controller Design**: Digital PID parameters, discretization methods, and frequency response analysis.
    *   **Loop Compensators**: Compensator design (Type I, Type II, Type III) for power supply regulation.
    *   **Active & Passive Filters**: Low-pass, high-pass, band-pass, and band-stop filter response tools.
*   **🛡️ Thermal, Safety & Protection**
    *   **Thermal Heatsink**: Steady-state thermal resistances and junction temperature estimation.
    *   **Creepage & Clearance**: Standard-based creepage distance checks (IEC 60664 / UL 60950).
    *   **Input Protection & TVS**: Fuse ratings, inrush NTCs, varistors, and transient voltage suppressor selection.

### Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/WenZhenJian-EE/Hardware-Engineering-Toolbox.git
    cd Hardware-Engineering-Toolbox
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python main.py
    ```

### Packaging / Building EXE

You can build a standalone Windows executable using PyInstaller. Simply run the provided script:
```bash
python build_exe.py
```
The executable will be located in the `dist/` directory.

---

## 简体中文

### 核心功能

本工具箱专为硬件与电力电子工程师打造，采用动态模块化架构，提供丰富的交互计算与可视化图形界面：

*   **⚡ 电力电子与拓扑设计**
    *   **DCDC 基础计算**：Buck、Boost、Buck-Boost 基本拓扑的电感量、电容量及纹波计算。
    *   **驱动设计**：栅极驱动电阻、驱动电流及驱动器损耗计算。
    *   **波形有效值**：各种周期性复杂波形（三角波、梯形波、正弦分段等）的有效值（RMS）、平均值及峰值计算。
    *   **效率预算**：整机损耗分布与效率预估模型。
    *   **双脉冲测试 (DPT)**：半导体开关测试参数配置与负载计算。
*   **🧲 磁性器件设计**
    *   **电感设计**：基于磁芯库的电感匝数、气隙宽度及饱和电流核算。
    *   **变压器设计**：高频变压器物理参数计算与铜损/铁损分析。
    *   **LLC & PFC 磁件**：谐振参数匹配与升压电感设计。
*   **📈 控制环路与滤波器**
    *   **数字 PID 控制**：PID 数字化参数整定、离散化方法与频率响应分析。
    *   **环路补偿器**：用于开关电源环路控制的 Type I、II、III 补偿器网络设计。
    *   **滤波器设计**：无源/有源滤波器（低通、高通、带通、带阻）幅频响应分析。
*   **🛡️ 热设计、安全与防护**
    *   **散热器分析**：稳态热阻模型与结温估算。
    *   **爬电距离与电气间隙**：基于 IEC 60664 标准的爬电距离安全评估。
    *   **输入保护与 TVS**：保险丝、NTC 浪涌电阻、压敏电阻与 TVS 瞬态抑制二极管选型。

### 运行指南

1.  克隆仓库：
    ```bash
    git clone https://github.com/WenZhenJian-EE/Hardware-Engineering-Toolbox.git
    cd Hardware-Engineering-Toolbox
    ```
2.  安装依赖库：
    ```bash
    pip install -r requirements.txt
    ```
3.  启动主程序：
    ```bash
    python main.py
    ```

### 独立程序打包

你可以使用 PyInstaller 将本工具箱打包为无依赖的 Windows `.exe` 程序。运行以下脚本即可：
```bash
python build_exe.py
```
生成的文件将输出在 `dist/` 文件夹内。

---

## Tech Stack / 技术栈

*   **Language**: Python 3.8+
*   **GUI Library**: PyQt5 (Python binding for Qt v5)
*   **Plotting**: Matplotlib (agg backend for formula rendering)
*   **Packaging**: PyInstaller

## License / 授权协议

Licensed under the [MIT License](LICENSE).
