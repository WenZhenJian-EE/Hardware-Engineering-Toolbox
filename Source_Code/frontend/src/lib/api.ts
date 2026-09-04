// Centralized API client for Hardware Engineering Toolbox

declare global {
  interface Window {
    electronAPI?: {
      getBackendPort: () => number | string;
    };
  }
}

/**
 * Retrieves the base URL for the backend API.
 * Prioritizes dynamic port injected by Electron main process via window.electronAPI,
 * otherwise falls back to default port 8000.
 */
export function getApiBaseUrl(): string {
  let port = 8000;
  if (window.electronAPI && typeof window.electronAPI.getBackendPort === 'function') {
    try {
      const p = window.electronAPI.getBackendPort();
      if (p) {
        port = Number(p);
      }
    } catch (e) {
      console.error("Failed to get port from electronAPI, falling back to 8000:", e);
    }
  }
  return `http://127.0.0.1:${port}`;
}

/**
 * Unified fetch wrapper that resolves the base URL and executes HTTP request.
 * @param path API endpoint relative path, e.g. '/api/calculate/buck'
 * @param options Native fetch RequestInit configuration
 */
export async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const baseUrl = getApiBaseUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${baseUrl}${cleanPath}`;
  return fetch(url, options);
}
