'use client';

import { useEffect, useState } from 'react';

export default function AdminPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    successful: 0,
    failed: 0
  });

  useEffect(() => {
    // Fetch feedback data from backend
    fetch('/api/feedback/all')
      .then(res => res.json())
      .then(data => {
        const feedbacks = data.feedbacks || [];
        setRequests(feedbacks);
        setStats({
          total: feedbacks.length,
          successful: feedbacks.length,
          failed: 0
        });
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <a className="text-emerald-500 hover:text-emerald-600 font-semibold mb-4 inline-block" href="/">
            ← back to app
          </a>
          <h1 className="text-4xl font-black text-gray-900 mb-2">admin dashboard</h1>
          <p className="text-gray-600">user feedback</p>
        </div>

        {/* Stats cards - unified style */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
            <p className="text-sm text-gray-700 font-bold mb-2">total feedback</p>
            <p className="text-5xl font-black text-gray-900">{stats.total}</p>
          </div>
          
          <div className="bg-emerald-50 rounded-2xl p-6 border-2 border-emerald-400 shadow-sm">
            <p className="text-sm text-emerald-800 font-bold mb-2">received</p>
            <p className="text-5xl font-black text-emerald-700">{stats.successful}</p>
          </div>
          
          <div className="bg-red-50 rounded-2xl p-6 border-2 border-red-400 shadow-sm">
            <p className="text-sm text-red-800 font-bold mb-2">failed</p>
            <p className="text-5xl font-black text-red-700">{stats.failed}</p>
          </div>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">loading feedback...</p>
          </div>
        )}

        {/* Feedback list */}
        {!loading && requests.length > 0 && (
          <div className="space-y-4">
            {requests.map((req: any, i: number) => (
              <div key={i} className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <p className="font-bold text-gray-900">{req.name || 'Anonymous'}</p>
                    {req.email && <p className="text-sm text-gray-600">{req.email}</p>}
                  </div>
                  <p className="text-xs text-gray-500">{new Date(req.timestamp).toLocaleString()}</p>
                </div>
                <p className="text-gray-700">{req.message}</p>
              </div>
            ))}
          </div>
        )}

        {!loading && requests.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">no feedback yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
