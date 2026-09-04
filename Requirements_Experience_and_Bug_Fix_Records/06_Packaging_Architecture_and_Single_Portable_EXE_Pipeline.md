# 06_Packaging_Architecture_and_Single_Portable_EXE_Pipeline

---

## 1. Problem Statement & User Incident

### 1.1 Stale Frozen Executable Incident
During user validation, the user reported that the English toggle button was missing and 20 obsolete topologies were still present. Investigation revealed that the user was launching `Circuit_Calculator_Pro.exe` located in the project root directory. This executable was a frozen build created months earlier:
- It did not contain any of the 40 audited modules.
- It did not include the new `I18nContext` translation layer.
- It contained deprecated topologies that had long been deleted from the source repository.

### 1.2 Binary Duplication Confusion
After initial repackaging, two executable files appeared in the root folder:
- `Hardware Engineering Toolbox 1.0.0.exe` (electron-builder default output name)
- `Hardware_Engineering_Toolbox.exe` (clean alias)

The user explicitly requested:
> *"Why are there still two .exe files? Delete all the old stuff completely. We are open-sourcing this, so delete everything that is not needed!"*

---

## 2. End-to-End Packaging Pipeline Architecture

The platform uses a two-stage hybrid packaging pipeline combining Python PyInstaller with Electron-Builder:

```
[Source Code]
      |
      +---> Frontend: [npm run build] ---> [frontend/dist/]
      |
      +---> Backend: [python package_backend.py] 
                |  (PyInstaller with hardened hidden imports)
                v
            [backend/dist/backend/backend.exe]
      |
      v
[Electron-Builder] (set CSC_IDENTITY_AUTO_DISCOVERY=false && npm run dist)
      |
      v  Bundles:
      |   - Chromium & Node runtime
      |   - frontend/dist/ (React 19 SPA)
      |   - resources/backend/ (Standalone FastAPI Engine)
      |
      v
[Output]: Source_Code/dist/Hardware Engineering Toolbox 1.0.0.exe (~96 MB)
      |
      v  Deployment to Root:
[Final]: Hardware_Engineering_Toolbox.exe (Single official executable)
```

### 2.1 Backend Packaging Hardening (`package_backend.py`)
Standard PyInstaller builds of FastAPI/Uvicorn applications frequently fail at runtime due to dynamic imports. The packaging script was fortified with mandatory hidden imports:
```python
cmd = [
    "pyinstaller",
    "--clean",
    "--noconfirm",
    "--onedir",
    "--name", "backend",
    f"--add-data=data{sep}data",
    "--hidden-import=uvicorn.logging",
    "--hidden-import=uvicorn.loops",
    "--hidden-import=uvicorn.loops.auto",
    "--hidden-import=uvicorn.protocols",
    "--hidden-import=uvicorn.protocols.http",
    "--hidden-import=uvicorn.protocols.http.auto",
    "--hidden-import=uvicorn.lifespan",
    "--hidden-import=uvicorn.lifespan.on",
    "--hidden-import=formula",
    "--hidden-import=database",
    "--hidden-import=sqlite3",
    "app.py"
]
```

### 2.2 Electron-Builder Configuration (`Source_Code/package.json`)
The desktop shell is configured to produce a zero-installation portable Windows executable:
```json
{
  "build": {
    "appId": "com.hardware.engineering.toolbox",
    "productName": "Hardware Engineering Toolbox",
    "directories": {
      "output": "dist"
    },
    "files": [
      "main.js",
      "package.json",
      "frontend/dist/**/*"
    ],
    "extraResources": [
      {
        "from": "backend/dist/backend",
        "to": "backend"
      }
    ],
    "win": {
      "target": ["portable"]
    }
  }
}
```

---

## 3. Physical Clean-up & Zero-Clutter Delivery

To adhere strictly to open-source repository hygiene:
1. **Removed Obsolete Binary**: `Circuit_Calculator_Pro.exe` (95 MB) was physically deleted from root.
2. **Removed Duplicate Executable**: `Hardware Engineering Toolbox 1.0.0.exe` was deleted, leaving **only one single official executable**:
   👉 `Hardware_Engineering_Toolbox.exe` (~96 MB).
3. **Purged Intermediate Build Caches**:
   - `Source_Code/backend/dist/` (~200 MB)
   - `Source_Code/dist/win-unpacked/` (~300 MB)
   - `Source_Code/backend/build/`
   - All `.pytest_cache` and `__pycache__` directories.
4. **Permanent Ignore Rules**: Added `build/` and `.pytest_cache/` to `.gitignore`.

---

## 4. Developer Instructions for Re-Building Release Executable

Any developer can reproduce the release binary with a single command:
```bash
# Execute from project root:
python Source_Code/parallel_build.py
```
The script will concurrently build the React frontend and Python backend, run Electron-Builder, and output the standalone executable.
