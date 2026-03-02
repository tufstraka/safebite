'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function FeedbacksPage() {
  const [feedbacks, setFeedbacks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/feedback/all')
      .then(r => r.json())
      .then(data => {
        setFeedbacks(data.feedbacks || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Link href="/" className="text-emerald-500 hover:text-emerald-600 font-semibold mb-4 inline-block">
            ← back to app
          </Link>
          <h1 className="text-4xl font-black text-gray-900 mb-2">user feedback</h1>
          <p className="text-gray-600">what people are saying</p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">loading feedback...</p>
          </div>
        ) : feedbacks.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-gray-200">
            <p className="text-gray-600">no feedback yet. be the first!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {feedbacks.map((fb, idx) => (
              <div key={idx} className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-bold text-gray-900">{fb.name || 'Anonymous'}</p>
                    {fb.email && <p className="text-sm text-gray-500">{fb.email}</p>}
                  </div>
                  <p className="text-xs text-gray-400">
                    {new Date(fb.timestamp).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                <p className="text-gray-700 leading-relaxed">{fb.message}</p>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            total feedback: {feedbacks.length}
          </p>
        </div>
      </div>
    </div>
  );
}
