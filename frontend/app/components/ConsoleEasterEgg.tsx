'use client';

import { useEffect } from 'react';

export default function ConsoleEasterEgg() {
  useEffect(() => {
    console.log('%c yo, checking the code? 🎴', 'color: #10b981; font-size: 16px; font-weight: bold;');
    console.log('%c hit me up @dobynog', 'color: #94a3b8; font-size: 12px;');
    console.log('%c github.com/tufstraka', 'color: #64748b; font-size: 10px;');
  }, []);

  return null;
}
