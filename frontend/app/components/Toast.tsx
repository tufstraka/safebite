'use client';

import { useEffect } from 'react';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';

interface ToastProps {
  message: string;
  type?: 'error' | 'success' | 'info';
  onClose: () => void;
  duration?: number;
}

export default function Toast({ message, type = 'error', onClose, duration = 5000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const styles = {
    error: 'bg-red-900/90 border-red-700',
    success: 'bg-emerald-900/90 border-emerald-700',
    info: 'bg-blue-900/90 border-blue-700',
  };

  const icons = {
    error: <AlertCircle className="w-5 h-5 text-red-400" />,
    success: <CheckCircle className="w-5 h-5 text-emerald-400" />,
    info: <Info className="w-5 h-5 text-blue-400" />,
  };

  return (
    <div className="fixed top-6 right-6 z-50 max-w-md animate-slide-in">
      <div className={`${styles[type]} backdrop-blur-sm border rounded-xl p-4 shadow-2xl flex items-start gap-3`}>
        {icons[type]}
        <p className="text-white text-sm flex-1 leading-relaxed">{message}</p>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
