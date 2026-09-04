@echo off
title "Hardware Engineering Toolbox - Desktop App Launcher"
echo =========================================================
echo       正在拉起 Electron + React + FastAPI 混合桌面端服务...
echo =========================================================
cd /d "%~dp0"
if not exist node_modules (
  echo 正在首次安装桌面端依赖环境...
  cmd /c "npm install"
)
cmd /c "npm run start"
