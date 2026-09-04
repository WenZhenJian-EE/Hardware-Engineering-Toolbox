const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getBackendPort: () => {
    try {
      return ipcRenderer.sendSync('get-backend-port');
    } catch (e) {
      console.error("Failed to fetch backend port from Main process via IPC:", e);
      return 8000;
    }
  }
});
