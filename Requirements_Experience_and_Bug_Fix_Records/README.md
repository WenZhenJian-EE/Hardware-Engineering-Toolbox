# 📌 Hardware Engineering Toolbox - Technical Whitepapers & Engineering Retrospectives

---

## 📑 Technical Documentation & Engineering Retrospective Index

This directory serves as the persistent engineering repository for the **Hardware Engineering Toolbox (Desktop Hybrid Edition)**. Following the architectural and operational standards established in high-reliability projects, this knowledge base captures user requirements evolution, architectural design decisions, critical bug post-mortems, and deployment packaging guidelines.

All documents are authored in technical English to support global open-source contributors and secondary developers.

| Index | Technical Whitepaper & Retrospective Document | Executive Summary |
| :---: | :--- | :--- |
| **01** | [**01_Overall_Architecture_Evolution_and_User_Requirements_Specification.md**](./01_Overall_Architecture_Evolution_and_User_Requirements_Specification.md) | User pain points, open-source handover criteria, hybrid Electron + React 19 + FastAPI architecture, and 40-module co-design workstation overview. |
| **02** | [**02_Purge_of_Obsolete_Topologies_and_LocalStorage_State_Migration.md**](./02_Purge_of_Obsolete_Topologies_and_LocalStorage_State_Migration.md) | Deletion of 18 incomplete topology stubs, automatic client `localStorage` cache scrubbing, zero-placeholder sidebar design, and technical debt elimination. |
| **03** | [**03_One_Click_Bilingual_Internationalization_and_Global_Shortcut_Architecture.md**](./03_One_Click_Bilingual_Internationalization_and_Global_Shortcut_Architecture.md) | Frictionless Chinese/English toggling, `Alt + L` global shortcut, intelligent OS locale detection, persistent dictionary mappings, and open-source readiness. |
| **04** | [**04_Bug_Fix_Retrospective_DCLink_Capacitor_Stress_and_Formula_Dynamic_Resolution.md**](./04_Bug_Fix_Retrospective_DCLink_Capacitor_Stress_and_Formula_Dynamic_Resolution.md) | Root cause post-mortem of blank 3-Phase Inverter ripple calculation, dynamic formula resolution, visible error banners, and SPWM/SVPWM harmonic stress validation. |
| **05** | [**05_Bug_Fix_Retrospective_React_Render_Cycle_Decoupling_and_Layout_Key_Integrity.md**](./05_Bug_Fix_Retrospective_React_Render_Cycle_Decoupling_and_Layout_Key_Integrity.md) | Eradication of React `setState-in-render` warnings via microtask decoupling in `tabHistory.ts`, and strict unique key enforcement in `LayoutEngine.tsx`. |
| **06** | [**06_Packaging_Architecture_and_Single_Portable_EXE_Pipeline.md**](./06_Packaging_Architecture_and_Single_Portable_EXE_Pipeline.md) | End-to-end build pipeline: PyInstaller backend packaging (`--hidden-import` hardening), Electron-builder portable target, obsolete binary removal, and zero-residue workspace delivery. |
| **07** | [**07_Physical_Calculation_Engine_Validation_and_217_Test_Regression_Suite.md**](./07_Physical_Calculation_Engine_Validation_and_217_Test_Regression_Suite.md) | Comprehensive test matrix covering 217 Pytest unit test suites, mathematical derivations, Middlebrook stability criteria, and SQLite hardware database integrity. |
| **08** | [**08_Secondary_Verification_Hub_and_Flagship_Topology_CoDesign_Integration.md**](./08_Secondary_Verification_Hub_and_Flagship_Topology_CoDesign_Integration.md) | Integration of interactive schematic sandboxes, 20 high-order engineering verification checks, closed-loop Bode sweeps, and commercial BOM selection in Buck and Flyback stations. |
| **09** | [**09_Standalone_EXE_Packaging_Defect_and_Module_Resolution_Postmortem.md**](./09_Standalone_EXE_Packaging_Defect_and_Module_Resolution_Postmortem.md) | In-depth post-mortem of silent EXE launch failure: PyInstaller directory namespace collisions, dynamic importlib module loading, and Electron timeout recovery. |
| **10** | [**10_Global_RealTime_DOM_Auto_Translation_Architecture.md**](./10_Global_RealTime_DOM_Auto_Translation_Architecture.md) | Zero-refactor internationalization architecture: TreeWalker DOM text traversal, dynamic mutation observer, and strict numeric/formula isolation shields. |
| **11** | [**11_Exhaustive_Bilingual_Architecture_and_Visual_Verification.md**](./11_Exhaustive_Bilingual_Architecture_and_Visual_Verification.md) | Multi-tier dictionary hierarchy (`b.length - a.length`), elimination of compound word fragmentation, two-state language indicators, and visual verification. |
| **12** | [**12_Native_English_Baseline_and_High_Value_Workstation_Pruning_Postmortem.md**](./12_Native_English_Baseline_and_High_Value_Workstation_Pruning_Postmortem.md) | Elimination of DOM runtime translation layer, 10-module basic calculator pruning, 30 advanced industrial power electronics workstations in 100% Native English, and PowerDeviceSuite modular refactoring. |

---

## 🚀 Official Release Artifacts
- **Official Standalone Portable Executable**: [`Hardware_Engineering_Toolbox.exe`](file:///d:/Data/Agent/MyDev/Hardware-Engineering-Toolbox-Desktop/Hardware_Engineering_Toolbox.exe) (~96 MB)
- **Developer Dev Server Launcher**: [`start_dev.bat`](file:///d:/Data/Agent/MyDev/Hardware-Engineering-Toolbox-Desktop/start_dev.bat)
- **Developer Guidelines**: [`docs/MODULE_DEVELOPMENT_GUIDE.md`](file:///d:/Data/Agent/MyDev/Hardware-Engineering-Toolbox-Desktop/docs/MODULE_DEVELOPMENT_GUIDE.md)
