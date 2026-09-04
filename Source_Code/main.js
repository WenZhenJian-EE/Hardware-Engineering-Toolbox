const { app, BrowserWindow, ipcMain } = require('electron');

// 解决 Windows 下 Chromium GPU/Disk Cache 拒绝访问 (0x5) 导致的拉起延迟与卡死黑屏问题
app.commandLine.appendSwitch('disable-gpu-shader-disk-cache');
app.commandLine.appendSwitch('disable-http-cache');

const { spawn } = require('child_process');
const path = require('path');
const net = require('net');

let backendProcess = null;
let frontendProcess = null;
let mainWindow = null;
let backendPort = 8000;

const isPackaged = app.isPackaged;

// IPC handler to share the dynamically selected backend port with the renderer
ipcMain.on('get-backend-port', (event) => {
  event.returnValue = backendPort;
});

// TCP Port Checker to detect service readiness
function checkPort(port, callback) {
  const socket = new net.Socket();
  socket.setTimeout(500);
  
  socket.on('connect', () => {
    socket.destroy();
    callback(true);
  });
  
  socket.on('timeout', () => {
    socket.destroy();
    callback(false);
  });
  
  socket.on('error', () => {
    socket.destroy();
    callback(false);
  });
  
  socket.connect(port, '127.0.0.1');
}

// Find a free TCP port starting from startPort
function findFreePort(startPort, callback) {
  let port = startPort;
  const server = net.createServer();
  
  server.listen(port, '127.0.0.1', () => {
    server.once('close', () => {
      callback(port);
    });
    server.close();
  });
  
  server.on('error', () => {
    findFreePort(port + 1, callback);
  });
}

// Polling until the port is open
function waitPort(port, timeoutMs, intervalMs, callback) {
  const start = Date.now();
  const poll = () => {
    checkPort(port, (isOpen) => {
      if (isOpen) {
        callback(true);
      } else if (Date.now() - start > timeoutMs) {
        callback(false);
      } else {
        setTimeout(poll, intervalMs);
      }
    });
  };
  poll();
}

function startBackend(port) {
  console.log(`正在拉起 Python FastAPI 后端 (端口: ${port})...`);
  
  if (isPackaged) {
    const backendExeName = process.platform === 'win32' ? 'backend.exe' : 'backend';
    const backendExe = path.join(process.resourcesPath, 'backend', backendExeName);
    console.log(`[打包模式] 正在从资源路径拉起后端: ${backendExe}`);
    
    backendProcess = spawn(
      backendExe,
      ['--host', '127.0.0.1', '--port', port.toString()],
      { cwd: path.dirname(backendExe) }
    );
  } else {
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const backendDir = path.join(__dirname, 'backend');
    console.log(`[开发模式] 正在拉起 Python 后端 (CWD: ${backendDir})...`);
    
    backendProcess = spawn(
      pythonCmd,
      ['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', port.toString()],
      { cwd: backendDir, shell: true }
    );
  }

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Python Backend]: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Python Backend Error]: ${data}`);
  });

  backendProcess.on('error', (err) => {
    console.error(`[Python Backend Spawn Error]: ${err.message}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Python 后端进程退出，退出码: ${code}`);
  });
}

function startFrontend() {
  if (isPackaged) {
    console.log('[打包模式] 不需要拉起 Vite 前端开发服务器，将直接加载静态文件。');
    return;
  }
  
  console.log('正在拉起 Vite React 前端开发服务器...');
  const frontendDir = path.join(__dirname, 'frontend');
  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  
  frontendProcess = spawn(
    npmCmd,
    ['run', 'dev', '--', '--host', '127.0.0.1'],
    { cwd: frontendDir, shell: true }
  );

  frontendProcess.stdout.on('data', (data) => {
    console.log(`[Vite Frontend]: ${data}`);
  });

  frontendProcess.stderr.on('data', (data) => {
    console.error(`[Vite Frontend Error]: ${data}`);
  });

  frontendProcess.on('close', (code) => {
    console.log(`Vite 前端进程退出，退出码: ${code}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1366,
    height: 900,
    title: "Hardware Engineering Toolbox",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    backgroundColor: '#020617', // Match slate-950 background
    show: false // Show only after loading to avoid flicker
  });

  // Open the DevTools.
  // mainWindow.webContents.openDevTools();

  if (isPackaged) {
    const indexPath = path.join(__dirname, 'frontend', 'dist', 'index.html');
    console.log(`[打包模式] 载入本地静态文件: ${indexPath}`);
    mainWindow.loadFile(indexPath);
  } else {
    mainWindow.loadURL('http://localhost:5173');
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.maximize();
    mainWindow.webContents.setZoomFactor(1.12);
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  // Dynamically find a free port for the backend starting from 8000
  findFreePort(8000, (freePort) => {
    backendPort = freePort;
    
    // Start backend & frontend services
    startBackend(backendPort);
    startFrontend();

    console.log(`正在等待端口就绪 (后端端口: ${backendPort})...`);
    
    if (isPackaged) {
      // Packaged mode: only wait for FastAPI backend
      waitPort(backendPort, 20000, 500, (backendReady) => {
        if (backendReady) {
          console.log('FastAPI 后端已就绪，正在创建窗口...');
          createWindow();
        } else {
          console.error('FastAPI 后端启动超时，将以离线渲染模式创建窗口...');
          createWindow();
        }
      });
    } else {
      // Development mode: Wait for backend and frontend (5173) to be ready
      waitPort(backendPort, 20000, 500, (backendReady) => {
        if (backendReady) {
          console.log('FastAPI 后端已就绪。');
          waitPort(5173, 20000, 500, (frontendReady) => {
            if (frontendReady) {
              console.log('Vite 前端已就绪，正在创建窗口...');
              createWindow();
            } else {
              console.error('Vite 前端启动超时！');
            }
          });
        } else {
          console.error('FastAPI 后端启动超时！');
        }
      });
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Guard: ensure all child processes are killed on app exit
app.on('will-quit', () => {
  console.log('正在清理子进程，请稍候...');
  const { exec } = require('child_process');
  
  if (backendProcess) {
    try {
      console.log('正在终止 Python 后端...');
      if (process.platform === 'win32') {
        exec(`taskkill /pid ${backendProcess.pid} /t /f`, () => {});
      } else {
        backendProcess.kill('SIGINT');
      }
    } catch (e) {
      console.error(e);
    }
  }
  if (frontendProcess) {
    try {
      console.log('正在终止 Vite 前端...');
      if (process.platform === 'win32') {
        exec(`taskkill /pid ${frontendProcess.pid} /t /f`, () => {});
      } else {
        frontendProcess.kill('SIGINT');
      }
    } catch (e) {
      console.error(e);
    }
  }
});
