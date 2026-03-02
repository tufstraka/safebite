'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

const PASSCODE = '8992';
const AUTH_KEY = 'safebite_auth';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [passcode, setPasscode] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check if already authenticated
    const stored = localStorage.getItem(AUTH_KEY);
    if (stored === PASSCODE) {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passcode === PASSCODE) {
      setIsAuthenticated(true);
      setError('');
      
      if (rememberMe) {
        localStorage.setItem(AUTH_KEY, passcode);
      } else {
        sessionStorage.setItem(AUTH_KEY, passcode);
      }
    } else {
      setError('wrong passcode');
      setPasscode('');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(AUTH_KEY);
    sessionStorage.removeItem(AUTH_KEY);
    setIsAuthenticated(false);
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-100 via-pink-100 to-purple-100 flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl p-8 shadow-lg border-2 border-gray-200 max-w-md w-full">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-600">
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
            </div>
            <h1 className="text-2xl font-black text-gray-900">restricted area</h1>
            <p className="text-gray-600 text-sm mt-1">enter passcode to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <input
                type="password"
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                placeholder="passcode"
                className="w-full px-4 py-3 bg-gray-50 border-2 border-gray-200 rounded-xl text-center text-2xl font-bold tracking-widest focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 focus:outline-none"
                maxLength={4}
                autoFocus
              />
              {error && (
                <p className="text-red-600 text-sm font-medium mt-2 text-center">{error}</p>
              )}
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="remember"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 text-emerald-500 border-gray-300 rounded focus:ring-emerald-500"
              />
              <label htmlFor="remember" className="text-sm text-gray-700 font-medium cursor-pointer">
                remember me
              </label>
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-bold text-lg transition-colors"
            >
              unlock
            </button>

            <button
              type="button"
              onClick={() => router.push('/')}
              className="w-full py-2 text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors"
            >
              ← back to app
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div>
      {children}
      <button
        onClick={handleLogout}
        className="fixed bottom-6 left-6 px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded-full text-sm font-semibold shadow-lg transition-colors z-50"
      >
        🔒 logout
      </button>
    </div>
  );
}
