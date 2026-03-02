'use client';

import { useEffect, useState } from 'react';

interface AdminStats {
  total_scans: number;
  total_dishes: number;
  recent_scans_24h: number;
  average_safe: number;
  average_unsafe: number;
  average_unknown: number;
  top_allergens: Array<{ allergen: string; count: number }>;
  recent_activity: Array<{
    id: number;
    timestamp: string;
    filename: string;
    total_dishes: number;
    safe_count: number;
    unsafe_count: number;
    allergens: string[];
  }>;
  file_types: { [key: string]: number };
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch real stats from database
    fetch('/api/admin/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load stats:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-red-600 font-bold">Failed to load analytics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <a className="text-emerald-500 hover:text-emerald-600 font-semibold mb-4 inline-block" href="/">
            ← back to app
          </a>
          <h1 className="text-4xl font-black text-gray-900 mb-2">admin dashboard</h1>
          <p className="text-gray-600">real-time analytics from database</p>
        </div>

        {/* Main stats grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
            <p className="text-sm text-gray-700 font-bold mb-2">total scans</p>
            <p className="text-5xl font-black text-gray-900">{stats.total_scans}</p>
          </div>
          
          <div className="bg-emerald-50 rounded-2xl p-6 border-2 border-emerald-400 shadow-sm">
            <p className="text-sm text-emerald-800 font-bold mb-2">dishes analyzed</p>
            <p className="text-5xl font-black text-emerald-700">{stats.total_dishes}</p>
          </div>
          
          <div className="bg-purple-50 rounded-2xl p-6 border-2 border-purple-400 shadow-sm">
            <p className="text-sm text-purple-800 font-bold mb-2">last 24 hours</p>
            <p className="text-5xl font-black text-purple-700">{stats.recent_scans_24h}</p>
          </div>
          
          <div className="bg-yellow-50 rounded-2xl p-6 border-2 border-yellow-400 shadow-sm">
            <p className="text-sm text-yellow-800 font-bold mb-2">avg safe dishes</p>
            <p className="text-5xl font-black text-yellow-700">{stats.average_safe.toFixed(1)}</p>
          </div>
        </div>

        {/* Secondary stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
            <p className="text-sm text-gray-700 font-bold mb-2">avg unsafe dishes</p>
            <p className="text-3xl font-black text-red-600">{stats.average_unsafe.toFixed(1)}</p>
          </div>
          
          <div className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
            <p className="text-sm text-gray-700 font-bold mb-2">avg unknown dishes</p>
            <p className="text-3xl font-black text-orange-600">{stats.average_unknown.toFixed(1)}</p>
          </div>
        </div>

        {/* Top allergens */}
        {stats.top_allergens.length > 0 && (
          <div className="bg-white rounded-2xl p-6 mb-8 border-2 border-gray-300 shadow-sm">
            <h2 className="text-2xl font-black text-gray-900 mb-4">top allergens checked</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {stats.top_allergens.map((item, i) => (
                <div key={i} className="bg-gradient-to-br from-emerald-50 to-cyan-50 rounded-xl p-4 border-2 border-emerald-200">
                  <p className="text-sm text-gray-700 capitalize font-medium">{item.allergen}</p>
                  <p className="text-3xl font-black text-emerald-700">{item.count}</p>
                  <p className="text-xs text-gray-600">scans</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent activity */}
        {stats.recent_activity.length > 0 ? (
          <div className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
            <h2 className="text-2xl font-black text-gray-900 mb-4">recent scans</h2>
            <div className="space-y-3">
              {stats.recent_activity.map((scan) => (
                <div key={scan.id} className="bg-gray-50 rounded-xl p-4 border border-gray-200 hover:border-emerald-400 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <p className="font-bold text-gray-900">{scan.filename}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(scan.timestamp).toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-bold">
                        {scan.safe_count} safe
                      </span>
                      <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-bold">
                        {scan.unsafe_count} unsafe
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span className="font-medium">{scan.total_dishes} dishes</span>
                    <span className="text-gray-400">•</span>
                    <span className="text-emerald-600">{scan.allergens?.join(', ') || 'no allergens'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl p-12 border-2 border-gray-300 shadow-sm text-center">
            <p className="text-gray-500 text-lg">no scans yet</p>
            <p className="text-gray-400 text-sm mt-2">scans will appear here once users start analyzing menus</p>
          </div>
        )}

        {/* File types */}
        {Object.keys(stats.file_types).length > 0 && (
          <div className="bg-white rounded-2xl p-6 mt-8 border-2 border-gray-300 shadow-sm">
            <h2 className="text-2xl font-black text-gray-900 mb-4">file types</h2>
            <div className="flex gap-4">
              {Object.entries(stats.file_types).map(([type, count]) => (
                <div key={type} className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                  <p className="text-sm text-gray-600 font-medium">{type || 'Unknown'}</p>
                  <p className="text-2xl font-black text-gray-900">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
