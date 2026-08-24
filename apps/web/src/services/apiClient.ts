/**
 * Core API Client for communicating with the FastAPI backend.
 */

// In production, this should be an environment variable.
const API_BASE_URL = 'http://localhost:8000/api/v1';

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

export const apiClient = {
  async get<T>(endpoint: string, headers?: HeadersInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    });
    return handleResponse<T>(response);
  },

  async post<T>(endpoint: string, data: any, headers?: HeadersInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  async put<T>(endpoint: string, data: any, headers?: HeadersInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  async delete<T>(endpoint: string, headers?: HeadersInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    });
    return handleResponse<T>(response);
  },
};
