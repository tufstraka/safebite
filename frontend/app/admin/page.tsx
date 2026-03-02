'use client';

import { useEffect, useState } from 'react';

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch real stats from database
    fetch('/api/admin/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
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
            <p className="text-5xl font-black text-gray-900">{stats?.total_scans || 0}</p>
          </div>
          
          <div className="bg-emerald-50 rounded-2xl p-6 border-2 border-emerald-400 shadow-sm">
            <p className="text-sm text-emerald-800 font-bold mb-2">dishes analyzed</p>
            <p className="text-5xl font-black text-emerald-700">{stats?.total_dishes || 0}</p>
          </div>
          
          <div className="bg-purple-50 rounded-2xl p-6 border-2 border-purple-400 shadow-sm">
            <p className="text-sm text-purple-800 font-bold mb-2">last 24h</p>
            <p className="text-5xl font-black text-purple-700">{stats?.recent_scans_24h || 0}</p>
          </div>
          
          <div className="bg-yellow-50 rounded-2xl p-6 border-2 border-yellow-400 shadow-sm">
            <p className="text-sm text-yellow-800 font-bold mb-2">avg safe</p>
            <p className="text-5xl font-black text-yellow-700">{stats?.average_safe || 0}</p>
          </div>
        </div>

        {/* Top allergens */}
        <div className="bg-white rounded-2xl p-6 mb-8 border-2 border-gray-300 shadow-sm">
          <h2 className="text-2xl font-black text-gray-900 mb-4">top allergens checked</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {stats?.top_allergens?.slice(0, 10).map((item: any, i: number) => (
              <div key={i} className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                <p className="text-sm text-gray-600 capitalize">{item.allergen}</p>
                <p className="text-2xl font-black text-gray-900">{item.count}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recent activity */}
        <div className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
          <h2 className="text-2xl font-black text-gray-900 mb-4">recent scans</h2>
          <div className="space-y-3">
            {stats?.recent_activity?.map((scan: any) => (
              <div key={scan.id} className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="font-bold text-gray-900">{scan.filename}</p>
                    <p className="text-sm text-gray-600">{new Date(scan.timestamp).toLocaleString()}</p>
                  </div>
                  <div className="flex gap-2">
                    <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-xs font-bold">
                      {scan.safe_count} safe
                    </span>
                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-bold">
                      {scan.unsafe_count} unsafe
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  {scan.total_dishes} dishes • {scan.allergens?.join(', ')}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
