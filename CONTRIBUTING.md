# Contributing to Hardware Engineering Toolbox

Thank you for your interest in contributing to **Hardware Engineering Toolbox**!

This document outlines the workflow and coding conventions for adding new power topologies, mathematical calculators, and improving existing tools.

> 💡 **New Module Development**: Looking to create a new converter topology or engineering calculator station? Follow the step-by-step [Module Development Guide](docs/MODULE_DEVELOPMENT_GUIDE.md).

---

## 🌟 Note from the Author: Open-Source Status

> *"I created this project to help with everyday hardware engineering calculations and reduce repetitive formula work. The core modules and test suites are functional, though the software architecture has areas that can still be improved and cleaned up. Because I do not currently have the time to actively maintain this repository, I have open-sourced it under the MIT License for the community to use and improve."*

Community contributions and suggestions are welcome:
- **Topology Expansions**: Half-Bridge/Full-Bridge LLC Resonant, Dual Active Bridge (DAB), Phase-Shifted Full-Bridge (PSFB), Totem-Pole Bridgeless PFC.
- **Advanced Magnetics**: Planar transformer winding calculators, non-linear BH curve solvers, and leakage inductance approximations.
- **Component Libraries**: Expanding the local SQLite database with modern SiC MOSFETs, GaN HEMTs, and high-frequency ferrite/nanocrystalline materials.
- **Code Refactoring**: Cleaning up legacy state management, improving typing, and simplifying frontend layouts.

Whether you are fixing an equation, refining a UI layout, or adding a new feature, your PRs and issues are welcome!

---

## 🛠️ Development Setup

### Prerequisites
- **Node.js**: >= 18.0.0
- **Python**: >= 3.10 (3.11 recommended)
- **Git**: Latest version

### Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/WenZhenJian-EE/Hardware-Engineering-Toolbox.git
   cd Hardware-Engineering-Toolbox
   ```
2. Double-click `start_dev.bat` on Windows, or start services manually:
   ```bash
   # Terminal 1: Backend
   cd Source_Code/backend
   pip install -r requirements.txt
   uvicorn app:app --port 8000 --reload

   # Terminal 2: Frontend
   cd Source_Code/frontend
   npm install
   npm run dev

   # Terminal 3: Electron Shell
   cd Source_Code
   npm install
   npm start
   ```

---

## 📐 Architecture & Coding Standards

### 1. Backend Physics Engine (`Source_Code/backend`)
- **Mathematical Integrity**: Analytical derivations, transfer functions, and stress calculations reside in `formula.py`.
- **API Layer**: FastAPI endpoints in `app.py`. Ensure inputs/outputs use strict Pydantic models.
- **Safety Margins**: Component stress checking should incorporate appropriate voltage ($\ge 1.2\times$) and current ($\ge 1.5\times$) derating.
- **Zero NaN/Inf Guarantee**: Protect against division by zero and singularity points (e.g. $D \in [0.01, 0.99]$, $\epsilon = 10^{-12}$).

### 2. Frontend Interface (`Source_Code/frontend`)
- **Theme & Styling**: Dark interface theme, subtle borders (`border-slate-800`), and clean styling with TailwindCSS.
- **Layout (DragDeck)**: Responsive card layout using `LayoutEngine.tsx`.
- **LaTeX Math Rendering**: Use `<Latex math={...} />` with curly braces `{}` to avoid escaping glitches.
- **ECharts Stability**: Always pass `notMerge={true}` to prevent cross-tab series collision.

---

## 🧪 Testing & Verification

Every pull request should pass the automated unit tests and build cleanly:

1. **Backend Tests (217 items)**:
   ```bash
   cd Source_Code
   python -m pytest
   ```
2. **Frontend Build & Type Check**:
   ```bash
   cd Source_Code/frontend
   npm run build
   ```

---

## 📜 License

By contributing to Hardware Engineering Toolbox, you agree that your contributions will be licensed under the [MIT License](LICENSE).
