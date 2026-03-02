'use client';

import { useState } from 'react';
import { X } from 'lucide-react';

export default function FeedbackForm() {
  const [show, setShow] = useState(false);
  const [showWidget, setShowWidget] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const submitFeedback = async () => {
    if (!message.trim()) return;

    setSending(true);
    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name || 'Anonymous',
          email: email || '',
          message: message.trim(),
          timestamp: new Date().toISOString()
        })
      });

      if (response.ok) {
        setMessage('');
        setName('');
        setEmail('');
        setShow(false);
        // Show toast instead of alert
        const toast = document.createElement('div');
        toast.textContent = 'thanks for the feedback';
        toast.className = 'fixed top-6 right-6 bg-emerald-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
      }
    } catch (e) {
      console.error('Feedback failed:', e);
      const toast = document.createElement('div');
      toast.textContent = 'hmm, that didn\'t work. try again?';
      toast.className = 'fixed top-6 right-6 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      {/* Dismissable Floating Widget */}
      {showWidget && (
        <div className="fixed bottom-6 right-6 flex items-center gap-2 z-50">
          <button
            onClick={() => setShowWidget(false)}
            className="bg-gray-700 hover:bg-gray-800 text-white p-2 rounded-full shadow-lg transition-all"
            title="Dismiss feedback"
          >
            ✕
          </button>
          <button
            onClick={() => setShow(true)}
            className="bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-full shadow-lg font-semibold transition-all"
          >
            💬 feedback
          </button>
        </div>
      )}

      {/* Modal */}
      {show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">send feedback</h3>
              <button onClick={() => setShow(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <input
                type="text"
                placeholder="your name (optional)"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900"
              />
              
              <input
                type="email"
                placeholder="your email (optional)"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900"
              />
              
              <textarea
                placeholder="what's on your mind?"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 resize-none"
              />

              <button
                onClick={submitFeedback}
                disabled={!message.trim() || sending}
                className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? 'sending...' : 'send feedback'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
