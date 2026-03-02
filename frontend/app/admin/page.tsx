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

interface UserStats {
  total_users: number;
  active_users: number;
  returning_users: number;
  new_users: number;
  avg_scans_per_user: number;
}

interface User {
  id: number;
  user_hash: string;
  first_seen: string;
  last_seen: string;
  total_scans: number;
  total_dishes_checked: number;
  top_allergens: { [key: string]: number };
  ip_address: string;
  user_agent: string;
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch all data
    Promise.all([
      fetch('/api/admin/stats').then(res => res.json()),
      fetch('/api/admin/users/stats').then(res => res.json()),
      fetch('/api/admin/users/list?limit=10').then(res => res.json())
    ])
      .then(([scanStats, userStatsData, usersData]) => {
        setStats(scanStats);
        setUserStats(userStatsData);
        setUsers(usersData.users || []);
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

        {/* User stats section */}
        {userStats && (
          <>
            <h2 className="text-2xl font-black text-gray-900 mb-4">👥 user statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
              <div className="bg-blue-50 rounded-2xl p-6 border-2 border-blue-400 shadow-sm">
                <p className="text-sm text-blue-800 font-bold mb-2">total users</p>
                <p className="text-5xl font-black text-blue-700">{userStats.total_users}</p>
              </div>
              
              <div className="bg-green-50 rounded-2xl p-6 border-2 border-green-400 shadow-sm">
                <p className="text-sm text-green-800 font-bold mb-2">active (30d)</p>
                <p className="text-5xl font-black text-green-700">{userStats.active_users}</p>
              </div>
              
              <div className="bg-purple-50 rounded-2xl p-6 border-2 border-purple-400 shadow-sm">
                <p className="text-sm text-purple-800 font-bold mb-2">returning</p>
                <p className="text-5xl font-black text-purple-700">{userStats.returning_users}</p>
              </div>
              
              <div className="bg-cyan-50 rounded-2xl p-6 border-2 border-cyan-400 shadow-sm">
                <p className="text-sm text-cyan-800 font-bold mb-2">new users</p>
                <p className="text-5xl font-black text-cyan-700">{userStats.new_users}</p>
              </div>
              
              <div className="bg-orange-50 rounded-2xl p-6 border-2 border-orange-400 shadow-sm">
                <p className="text-sm text-orange-800 font-bold mb-2">avg scans</p>
                <p className="text-5xl font-black text-orange-700">{userStats.avg_scans_per_user}</p>
              </div>
            </div>
          </>
        )}

        {/* Scan stats section */}
        <h2 className="text-2xl font-black text-gray-900 mb-4">📊 scan statistics</h2>
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

        {/* Top allergens */}
        {stats.top_allergens.length > 0 && (
          <div className="bg-white rounded-2xl p-6 mb-8 border-2 border-gray-300 shadow-sm">
            <h2 className="text-2xl font-black text-gray-900 mb-4">🥜 top allergens checked</h2>
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

        {/* Recent users */}
        {users.length > 0 && (
          <div className="bg-white rounded-2xl p-6 mb-8 border-2 border-gray-300 shadow-sm">
            <h2 className="text-2xl font-black text-gray-900 mb-4">👤 recent users</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-3 px-2 text-sm font-bold text-gray-700">User ID</th>
                    <th className="text-left py-3 px-2 text-sm font-bold text-gray-700">Last Seen</th>
                    <th className="text-left py-3 px-2 text-sm font-bold text-gray-700">Scans</th>
                    <th className="text-left py-3 px-2 text-sm font-bold text-gray-700">Dishes</th>
                    <th className="text-left py-3 px-2 text-sm font-bold text-gray-700">Top Allergens</th>
                    <th className="text-left py-3 px-2 text-sm font-bold text-gray-700">Location</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-2">
                        <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                          {user.user_hash}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-sm text-gray-600">
                        {new Date(user.last_seen).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="py-3 px-2">
                        <span className="font-bold text-emerald-700">{user.total_scans}</span>
                      </td>
                      <td className="py-3 px-2">
                        <span className="font-bold text-gray-700">{user.total_dishes_checked}</span>
                      </td>
                      <td className="py-3 px-2">
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(user.top_allergens || {})
                            .sort(([, a], [, b]) => b - a)
                            .slice(0, 3)
                            .map(([allergen, count]) => (
                              <span key={allergen} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full capitalize">
                                {allergen} ({count})
                              </span>
                            ))}
                        </div>
                      </td>
                      <td className="py-3 px-2 text-xs text-gray-500">
                        {user.ip_address}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recent activity */}
        {stats.recent_activity.length > 0 ? (
          <div className="bg-white rounded-2xl p-6 border-2 border-gray-300 shadow-sm">
            <h2 className="text-2xl font-black text-gray-900 mb-4">📝 recent scans</h2>
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
            <h2 className="text-2xl font-black text-gray-900 mb-4">📄 file types</h2>
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
