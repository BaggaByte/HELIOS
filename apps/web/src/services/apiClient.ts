/**
 * Core API Client for communicating with the FastAPI backend.
 */
import { invoke } from '@tauri-apps/api/core';

// In production, this should be an environment variable.
let dynamicApiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/+$/, '');
let portInitialized = false;

export async function getApiBaseUrl(): Promise<string> {
  // @ts-ignore - Check if running inside Tauri
  if (window.__TAURI_INTERNALS__ && !portInitialized) {
    try {
      const port = await invoke<number>('get_backend_port');
      const baseUrl = `http://127.0.0.1:${port}/api/v1`;
      
      // Wait for backend readiness
      console.log(`[HELIOS] Discovered backend port ${port}. Waiting for readiness...`);
      let isReady = false;
      for (let i = 0; i < 20; i++) {
        try {
          const resp = await fetch(`${baseUrl}/system/health`);
          if (resp.ok) {
            isReady = true;
            break;
          }
        } catch (e) {
          // Connection refused, wait and retry
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
      
      if (!isReady) {
        console.warn("[HELIOS] Backend did not become ready in time.");
      } else {
        console.log(`[HELIOS] Backend sidecar on port ${port} is ready.`);
      }
      
      dynamicApiBaseUrl = baseUrl;
    } catch (e) {
      console.warn("Failed to get backend port from Tauri, falling back to default.", e);
    } finally {
      portInitialized = true;
    }
  }
  return dynamicApiBaseUrl;
}

export class ApiError extends Error {
  public status: number;
  public data: any;

  constructor(status: number, message: string, data: any = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    // Centrally handle unauthorized access
    localStorage.removeItem('helios_token');
    window.dispatchEvent(new Event('auth-unauthorized'));
    // Redirect to login could be handled by a listener or directly here
  }

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }
    
    throw new ApiError(
      response.status,
      errorData?.detail || response.statusText || 'Unknown API Error',
      errorData
    );
  }

  // If status is 204 No Content, return empty
  if (response.status === 204) {
    return {} as T;
  }

  return await response.json();
}

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('helios_token');
  if (token) {
    return { 'Authorization': `Bearer ${token}` };
  }
  return {};
}

export const apiClient = {
  async get<T>(endpoint: string, headers?: HeadersInit): Promise<T> {
    const baseUrl = await getApiBaseUrl();
    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...headers,
      },
    });
    return handleResponse<T>(response);
  },

  async getFile(endpoint: string, headers?: HeadersInit): Promise<Blob> {
    const baseUrl = await getApiBaseUrl();
    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        ...headers,
      },
    });
    
    if (response.status === 401) {
      localStorage.removeItem('helios_token');
      window.dispatchEvent(new Event('auth-unauthorized'));
    }
    
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }
    
    return await response.blob();
  },

  async post<T>(endpoint: string, data: any, headers?: HeadersInit): Promise<T> {
    const baseUrl = await getApiBaseUrl();
    const isFormData = data instanceof FormData;
    const reqHeaders: Record<string, string> = {
      ...getAuthHeaders() as Record<string, string>,
      ...(headers as Record<string, string> || {}),
    };
    
    if (!isFormData && !reqHeaders['Content-Type']) {
      reqHeaders['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: 'POST',
      headers: reqHeaders,
      body: isFormData ? data : JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  async put<T>(endpoint: string, data: any, headers?: HeadersInit): Promise<T> {
    const baseUrl = await getApiBaseUrl();
    const isFormData = data instanceof FormData;
    const reqHeaders: Record<string, string> = {
      ...getAuthHeaders() as Record<string, string>,
      ...(headers as Record<string, string> || {}),
    };
    
    if (!isFormData && !reqHeaders['Content-Type']) {
      reqHeaders['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: reqHeaders,
      body: isFormData ? data : JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  async delete<T>(endpoint: string, headers?: HeadersInit): Promise<T> {
    const baseUrl = await getApiBaseUrl();
    const response = await fetch(`${baseUrl}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...headers,
      },
    });
    return handleResponse<T>(response);
  },
};
