'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function AdminPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, successful: 0, failed: 0 });

  useEffect(() => {
    fetch('/api/admin/requests?limit=200')
      .then(r => r.json())
      .then(data => {
        const reqs = data.requests || [];
        setRequests(reqs);
        
        // Calculate stats
        const successful = reqs.filter((r: any) => r.status_code >= 200 && r.status_code < 300).length;
        const failed = reqs.filter((r: any) => r.status_code >= 400).length;
        setStats({ total: reqs.length, successful, failed });
        
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const getStatusColor = (code: number) => {
    if (code >= 200 && code < 300) return 'bg-emerald-100 text-emerald-800';
    if (code >= 400) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getMethodColor = (method: string) => {
    if (method === 'GET') return 'bg-blue-100 text-blue-800';
    if (method === 'POST') return 'bg-purple-100 text-purple-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <Link href="/" className="text-emerald-500 hover:text-emerald-600 font-semibold mb-4 inline-block">
            ← back to app
          </Link>
          <h1 className="text-4xl font-black text-gray-900 mb-2">admin dashboard</h1>
          <p className="text-gray-600">api request logs</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <p className="text-sm text-gray-600 font-semibold mb-1">total requests</p>
            <p className="text-4xl font-black text-gray-900">{stats.total}</p>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <p className="text-sm text-gray-600 font-semibold mb-1">successful</p>
            <p className="text-4xl font-black text-emerald-600">{stats.successful}</p>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <p className="text-sm text-gray-600 font-semibold mb-1">failed</p>
            <p className="text-4xl font-black text-red-600">{stats.failed}</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">loading requests...</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Time</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Method</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Path</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">Duration</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-gray-600 uppercase">IP</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {requests.map((req, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(req.timestamp).toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        })}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${getMethodColor(req.method)}`}>
                          {req.method}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-gray-900">{req.path}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusColor(req.status_code)}`}>
                          {req.status_code}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{req.duration_seconds}s</td>
                      <td className="px-4 py-3 text-sm font-mono text-gray-600">{req.client_ip}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
