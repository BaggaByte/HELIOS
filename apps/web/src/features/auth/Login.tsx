import React, { useState, useEffect } from 'react';
import { Shield, Lock, User, AlertCircle, Globe, ServerOff } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { getApiBaseUrl } from '../../services/apiClient';


export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [scope, setScope] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSetupRequired, setIsSetupRequired] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);
  const [connectionError, setConnectionError] = useState(false);
  const setAuth = useAuthStore(state => state.setAuth);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      const baseUrl = await getApiBaseUrl();
      let lastError: unknown;
      for (let attempt = 0; attempt < 30 && isMounted; attempt++) {
        try {
          const res = await fetch(`${baseUrl}/system/health`);
          if (res.ok) {
            const data = await res.json();
            if (isMounted) {
              if (data.setup_required) setIsSetupRequired(true);
              setCheckingSetup(false);
            }
            return;
          }
          lastError = new Error(`Backend health check returned ${res.status}`);
        } catch (err) {
          lastError = err;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      if (isMounted) {
        console.error('Failed to connect to backend health endpoint', lastError);
        setConnectionError(true);
        setCheckingSetup(false);
      }
    };
    checkHealth();
    return () => { isMounted = false; };
  }, []);

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const baseUrl = await getApiBaseUrl();
      const response = await fetch(`${baseUrl}/auth/setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password, scope }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Setup failed');
      }
      
      const data = await response.json();
      
      const userRes = await fetch(`${baseUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });
      if (!userRes.ok) throw new Error('Failed to retrieve user profile');
      const user = await userRes.json();
      
      setAuth(data.access_token, user);
    } catch (err: any) {
      setError(err.message || 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const baseUrl = await getApiBaseUrl();
      const response = await fetch(`${baseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      
      // Fetch user profile
      const userRes = await fetch(`${baseUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });
      if (!userRes.ok) {
        throw new Error('Failed to retrieve user profile');
      }
      const user = await userRes.json();
      
      setAuth(data.access_token, user);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  if (checkingSetup) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-primary">
        <Shield className="w-10 h-10 text-border-active animate-pulse" />
      </div>
    );
  }

  if (connectionError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-surface-primary gap-4">
        <ServerOff className="w-12 h-12 text-rose-500 mb-2" />
        <h2 className="text-xl font-bold text-gray-100">Backend Sidecar Unavailable</h2>
        <p className="text-sm text-gray-400 max-w-md text-center">
          HELIOS could not connect to the local backend service. If running the desktop app, ensure the sidecar was packaged correctly. If developing, ensure the API is running.
        </p>
        <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-surface-secondary border border-border-default rounded-md text-xs text-gray-300 hover:text-white">
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-surface-primary bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-surface-tertiary/20 via-surface-primary to-surface-primary">
      <div className="w-full max-w-md p-8 space-y-6 bg-surface-secondary rounded-2xl shadow-md border border-border-default relative overflow-hidden">
        <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-border-active/10 blur-[60px] rounded-full pointer-events-none" />
        
        <div className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-border-active/10 rounded-2xl border border-border-active/30">
              <Shield className="w-10 h-10 text-border-active" />
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-100">
            {isSetupRequired ? 'Initialize HELIOS' : 'HELIOS Mission Control'}
          </h1>
          <p className="text-sm text-gray-400">
            {isSetupRequired 
              ? 'Create initial administrator and define network boundaries' 
              : 'Authenticate to access secure intelligence platform'}
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/30 rounded-xl">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <form onSubmit={isSetupRequired ? handleSetup : handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="username" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Username</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User size={16} className="text-gray-500" />
              </div>
              <input
                id="username"
                type="text"
                required
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-surface-primary border border-border-default rounded-xl focus:border-border-active focus:ring-1 focus:ring-border-active text-gray-200 text-sm transition-all outline-none"
                placeholder="operator"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Passphrase</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock size={16} className="text-gray-500" />
              </div>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-surface-primary border border-border-default rounded-xl focus:border-border-active focus:ring-1 focus:ring-border-active text-gray-200 text-sm transition-all outline-none"
                placeholder="••••••••••••"
              />
            </div>
          </div>

          {isSetupRequired && (
            <div className="space-y-1.5">
              <label htmlFor="scope" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Default Network Scope</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Globe size={16} className="text-gray-500" />
                </div>
                <input
                  id="scope"
                  type="text"
                  required
                  value={scope}
                  onChange={e => setScope(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-surface-primary border border-border-default rounded-xl focus:border-border-active focus:ring-1 focus:ring-border-active text-gray-200 text-sm transition-all outline-none"
                  placeholder="e.g. 10.0.0.0/8, 192.168.1.1"
                />
              </div>
              <p className="text-[10px] text-gray-500 mt-1">Specify allowed IP ranges or domains for the default workspace. Wildcards (0.0.0.0/0) are not permitted.</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-border-active text-white font-medium rounded-xl hover:bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-border-active focus:ring-offset-surface-primary transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {loading ? (isSetupRequired ? 'Initializing...' : 'Authenticating...') : (isSetupRequired ? 'Initialize & Engage' : 'Engage')}
          </button>
        </form>
      </div>
    </div>
  );
}
