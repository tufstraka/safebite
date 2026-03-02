'use client';

import { useState, useEffect } from 'react';
import { Shield, Upload, AlertTriangle, CheckCircle, XCircle, HelpCircle, X, Camera } from 'lucide-react';
import Toast from './components/Toast';
import ConsoleEasterEgg from './components/ConsoleEasterEgg';
import CameraView from './components/CameraView';
import FeedbackForm from './components/FeedbackForm';

const ALLERGENS = [
  'Peanuts', 'Tree Nuts', 'Milk', 'Eggs', 'Wheat', 'Soy',
  'Fish', 'Shellfish', 'Sesame', 'Gluten', 'Mustard', 'Celery'
];

export default function Home() {
  const [selectedAllergens, setSelectedAllergens] = useState<string[]>([]);
  const [customAllergens, setCustomAllergens] = useState<string[]>([]);
  const [customInput, setCustomInput] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [menuFile, setMenuFile] = useState<File | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'error' | 'success' | 'info' } | null>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [scanHistory, setScanHistory] = useState<any[]>([]);

  // Pagination state
  const [safePage, setSafePage] = useState(1);
  const [unsafePage, setUnsafePage] = useState(1);
  const [unknownPage, setUnknownPage] = useState(1);
  const ITEMS_PER_PAGE = 10;


  // Pagination helper
  const [showFeedbackWidget, setShowFeedbackWidget] = useState(true);
  const paginate = (items: any[], page: number) => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    return {
      items: items.slice(start, end),
      totalPages: Math.ceil(items.length / ITEMS_PER_PAGE),
      currentPage: page
    };
  };

  const loadHistory = () => {
    try {
      const history = JSON.parse(localStorage.getItem('safebite_history') || '[]');
      setScanHistory(history);
      setShowHistory(true);
    } catch (e) {
      console.error('Failed to load history:', e);
    }
  };

  const saveToHistory = (scanData: any) => {
    try {
      const history = JSON.parse(localStorage.getItem('safebite_history') || '[]');
      const scan = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        filename: menuFile?.name || 'Unknown',
        allergens: selectedAllergens,
        customAllergens: customAllergens,
        results: {
          total: scanData.total_dishes,
          safe: scanData.safe_count,
          unsafe: scanData.unsafe_count,
          unknown: scanData.unknown_count
        }
      };
      
      history.unshift(scan);
      if (history.length > 20) history.pop();
      
      localStorage.setItem('safebite_history', JSON.stringify(history));
    } catch (e) {
      console.error('Failed to save scan history:', e);
    }
  };

  const [showPWAPrompt, setShowPWAPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  // Detect mobile on mount
  useEffect(() => {
    setIsMobile(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent));
  }, []);
  // PWA install prompt
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
      
      // Show prompt after 30 seconds if not installed
      setTimeout(() => {
        if (!window.matchMedia('(display-mode: standalone)').matches) {
          setShowPWAPrompt(true);
        }
      }, 30000);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);
  // Load saved allergen profile on mount
  useEffect(() => {
    const saved = localStorage.getItem('safebite_allergens');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSelectedAllergens(parsed.standard || []);
        setCustomAllergens(parsed.custom || []);
      } catch (e) {
        console.error('Failed to load saved allergens:', e);
      }
    }
  }, []);

  // Save allergen profile whenever it changes
  useEffect(() => {
    if (selectedAllergens.length > 0 || customAllergens.length > 0) {
      localStorage.setItem('safebite_allergens', JSON.stringify({
        standard: selectedAllergens,
        custom: customAllergens
      }));
    }
  }, [selectedAllergens, customAllergens]);


  const handleInstallPWA = async () => {
    if (!deferredPrompt) return;
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
    }
    setShowPWAPrompt(false);
  };


  const toggleAllergen = (allergen: string) => {
    if (selectedAllergens.includes(allergen)) {
      setSelectedAllergens(selectedAllergens.filter(a => a !== allergen));
    } else {
      setSelectedAllergens([...selectedAllergens, allergen]);
    }
  };

  const addCustomAllergen = () => {
    if (customInput.trim() && !customAllergens.includes(customInput.trim())) {
      setCustomAllergens([...customAllergens, customInput.trim()]);
      setCustomInput('');
    }
  };

  const removeCustomAllergen = (allergen: string) => {
    setCustomAllergens(customAllergens.filter(a => a !== allergen));
  };

  const handleCameraClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment'; // Use back camera
    input.onchange = (e: any) => {
      if (e.target.files?.[0]) {
        setMenuFile(e.target.files[0]);
      }
    };
    input.click();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setMenuFile(e.target.files[0]);
    }
  };

  const analyzeMenu = async () => {
    const allAllergens = [...selectedAllergens, ...customAllergens];
    
    if (!menuFile || allAllergens.length === 0) {
      setToast({ message: 'bruh, need a menu & allergen first', type: 'error' });
      return;
    }

    setAnalyzing(true);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('file', menuFile);
      formData.append('allergens', selectedAllergens.map(a => a.toLowerCase()).join(','));
      formData.append('custom_allergens', customAllergens.join(','));

      console.log('Sending to API:', {
        file: menuFile.name,
        allergens: selectedAllergens.map(a => a.toLowerCase()).join(','),
        custom_allergens: customAllergens.join(',')
      });

      const response = await fetch('/api/analyze/image', {
        method: 'POST',
        body: formData,
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'something broke' }));
        throw new Error(errorData.detail || 'something broke');
      }

      const data = await response.json();
      console.log('API Response:', {
        restaurant: data.restaurant_name,
        total_dishes: data.total_dishes,
        first_dish: data.safe_dishes[0]?.name || data.unsafe_dishes[0]?.name
      });
      
      setResults(data);
      // Reset pagination when new results come in
      setSafePage(1);
      setUnsafePage(1);
      setUnknownPage(1);
      saveToHistory(data);
      setToast({ message: `sawa! found ${data.total_dishes} dishes`, type: 'success' });
    } catch (error) {
      console.error('Analysis failed:', error);
      const errorMessage = error instanceof Error ? error.message : "hmm, that didn't work. try again?";
      setToast({ message: errorMessage, type: 'error' });
    } finally {
      setAnalyzing(false);
    }
  };

  const getSafetyColor = (level: string) => {
    const colors: any = {
      'Safe': 'bg-emerald-500',
      'Likely Safe': 'bg-blue-500',
      'Unknown': 'bg-yellow-500',
      'Caution': 'bg-orange-500',
      'Unsafe': 'bg-red-500'
    };
    return colors[level] || 'bg-gray-500';
  };

  const getSafetyIcon = (level: string) => {
    if (level === 'Safe' || level === 'Likely Safe') return <CheckCircle className="w-5 h-5" />;
    if (level === 'Unknown') return <HelpCircle className="w-5 h-5" />;
    return <AlertTriangle className="w-5 h-5" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-100 via-pink-100 to-purple-100 relative overflow-hidden">
      {/* Food illustrations - caricature style */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Soft gradient orbs */}
        <div className="absolute top-20 right-10 w-96 h-96 bg-gradient-to-br from-purple-300/50 to-pink-300/50 rounded-full blur-3xl"></div>

        {/* Pizza slice */}
        <svg className="absolute top-32 left-20 w-24 h-24 opacity-20" viewBox="0 0 100 100">
          <path d="M50,10 L90,90 L10,90 Z" fill="#FFA500" stroke="#FF8C00" strokeWidth="2"/>
          <circle cx="40" cy="70" r="5" fill="#FF0000"/>
          <circle cx="60" cy="65" r="4" fill="#FF0000"/>
          <circle cx="50" cy="50" r="4" fill="#FFFF00"/>
          <path d="M30,80 Q35,75 40,80" fill="#FFE4B5" stroke="#FFD700" strokeWidth="1"/>
        </svg>
        
        {/* Burger */}
        <svg className="absolute bottom-32 right-20 w-28 h-28 opacity-20" viewBox="0 0 100 100">
          <ellipse cx="50" cy="30" rx="35" ry="8" fill="#D2691E"/>
          <rect x="15" y="35" width="70" height="10" fill="#90EE90" rx="2"/>
          <rect x="15" y="45" width="70" height="15" fill="#8B4513" rx="2"/>
          <rect x="15" y="60" width="70" height="8" fill="#FFD700" rx="2"/>
          <ellipse cx="50" cy="73" rx="35" ry="8" fill="#F4A460"/>
        </svg>
        
        {/* Ice cream cone */}
        <svg className="absolute top-1/3 right-1/4 w-20 h-20 opacity-20" viewBox="0 0 100 100">
          <path d="M35,50 L50,90 L65,50 Z" fill="#D2691E" stroke="#8B4513" strokeWidth="2"/>
          <circle cx="50" cy="45" r="20" fill="#FFB6C1"/>
          <circle cx="45" cy="35" r="15" fill="#FF69B4"/>
          <circle cx="55" cy="35" r="12" fill="#FFE4E1"/>
        </svg>
        
        {/* Donut */}
        <svg className="absolute bottom-1/4 left-1/3 w-24 h-24 opacity-20" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="30" fill="#FFB6D9" stroke="#FF69B4" strokeWidth="3"/>
          <circle cx="50" cy="50" r="12" fill="#FFF5EE"/>
          <circle cx="40" cy="35" r="3" fill="#FF1493"/>
          <circle cx="60" cy="40" r="3" fill="#00CED1"/>
          <circle cx="55" cy="60" r="3" fill="#FFD700"/>
          <circle cx="35" cy="55" r="3" fill="#9370DB"/>
        </svg>
        
        {/* Apple */}
        <svg className="absolute top-1/2 left-20 w-20 h-20 opacity-20" viewBox="0 0 100 100">
          <ellipse cx="50" cy="55" rx="25" ry="28" fill="#FF0000"/>
          <ellipse cx="48" cy="52" rx="8" ry="10" fill="#FF6B6B" opacity="0.5"/>
          <path d="M50,25 Q48,20 50,15" stroke="#8B4513" strokeWidth="3" fill="none"/>
          <path d="M55,20 Q60,18 58,15" fill="#228B22"/>
        </svg>
        
        {/* Coffee cup */}
        <svg className="absolute top-3/4 right-1/3 w-22 h-22 opacity-20" viewBox="0 0 100 100">
          <rect x="25" y="40" width="40" height="35" rx="5" fill="#8B4513" stroke="#654321" strokeWidth="2"/>
          <ellipse cx="45" cy="40" rx="20" ry="5" fill="#6F4E37"/>
          <path d="M65,50 Q75,50 75,60 Q75,70 65,70" stroke="#654321" strokeWidth="2" fill="none"/>
          <path d="M35,30 Q35,25 40,25 Q45,25 45,30" stroke="#D3D3D3" strokeWidth="1.5" fill="none"/>
        </svg>
        
        {/* Taco */}
        <svg className="absolute bottom-1/3 right-10 w-26 h-26 opacity-20" viewBox="0 0 100 100">
          <path d="M20,60 Q50,30 80,60 L75,70 Q50,50 25,70 Z" fill="#F4A460" stroke="#D2691E" strokeWidth="2"/>
          <rect x="30" y="58" width="40" height="5" fill="#90EE90"/>
          <rect x="35" y="53" width="30" height="5" fill="#8B4513"/>
          <rect x="32" y="63" width="36" height="4" fill="#FFD700"/>
        </svg>
        
        {/* Sushi */}
        <svg className="absolute top-1/4 left-1/2 w-24 h-24 opacity-20" viewBox="0 0 100 100">
          <ellipse cx="50" cy="50" rx="30" ry="12" fill="#FFFFFF" stroke="#000000" strokeWidth="1.5"/>
          <rect x="30" y="45" width="40" height="10" fill="#FF6347"/>
          <ellipse cx="50" cy="45" rx="30" ry="3" fill="#2F4F4F" opacity="0.7"/>
        </svg>
        
        {/* Banana */}
        <svg className="absolute top-16 right-1/2 w-28 h-16 opacity-20" viewBox="0 0 120 60">
          <path d="M10,30 Q20,10 40,15 Q60,20 80,25 Q100,30 110,40" stroke="#FFD700" strokeWidth="12" fill="none" strokeLinecap="round"/>
          <path d="M15,30 Q25,15 40,18 Q60,22 80,27 Q95,32 105,40" stroke="#FFA500" strokeWidth="2" fill="none" opacity="0.6"/>
        </svg>
        
        {/* Watermelon slice */}
        <svg className="absolute bottom-16 left-1/4 w-24 h-24 opacity-20" viewBox="0 0 100 100">
          <path d="M20,70 Q50,20 80,70 Z" fill="#FF6B6B"/>
          <path d="M25,70 Q50,30 75,70 Z" fill="#FF4444"/>
          <path d="M20,70 Q50,20 80,70" stroke="#228B22" strokeWidth="6" fill="none"/>
          <circle cx="35" cy="60" r="2" fill="#000000"/>
          <circle cx="50" cy="50" r="2" fill="#000000"/>
          <circle cx="65" cy="58" r="2" fill="#000000"/>
        </svg>
        <div className="absolute bottom-20 left-10 w-80 h-80 bg-gradient-to-br from-emerald-300/50 to-cyan-300/50 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-br from-yellow-300/40 to-orange-300/40 rounded-full blur-3xl"></div>
        
        {/* Kenyan patterns - geometric African motifs */}
        
        
        
        
        
        
        {/* Maasai-inspired zigzag patterns */}
        
        
        {/* Additional Kenyan patterns */}
        
        
        
        
        
        
        
        
        {/* More zigzag patterns */}
        
      </div>
      {/* Simple header */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50 relative shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-3">
          <Shield className="w-6 h-6 text-emerald-600" />
          
          <div className="flex flex-col items-start gap-0.5">
            <h1 className="text-xl font-bold text-gray-900">SafeBite</h1>
            <a 
              href="https://github.com/tufstraka" 
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-emerald-600 transition-colors font-medium text-xs"
              title="by @dobynog"
            >
              by .
            </a>
          </div>
          
          <button
            onClick={loadHistory}
            className="text-sm text-gray-600 hover:text-emerald-500 transition-colors font-medium"
          >
            📚 history
          </button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12 relative z-10">
        {!results ? (
          <>
            {/* Direct intro */}
            <div className="mb-8">
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">snap your food</h2>
              <p className="text-base sm:text-lg text-gray-600">take a pic. we'll check the allergens.</p>
            </div>

            {/* Upload */}
            <div className="bg-white rounded-2xl p-4 sm:p-6 mb-4 sm:mb-6 border border-gray-200 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">1. snap it</h3>
              
              {menuFile ? (
                <div className="border-2 border-emerald-500 bg-emerald-100 rounded-xl p-6 text-center">
                  <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                  <p className="text-gray-900 font-medium">{menuFile.name}</p>
                  <p className="text-gray-700 text-sm font-medium mt-1">{(menuFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Camera button - primary on mobile */}
                  <label className="w-full bg-emerald-500 hover:bg-emerald-600 text-gray-900 rounded-xl p-6 transition-colors flex flex-col items-center gap-3 cursor-pointer shadow-lg shadow-emerald-500/20">
                    <Camera className="w-12 h-12" />
                    <div>
                      <p className="font-bold text-lg">take a pic</p>
                      <p className="text-sm text-emerald-50">quick snap of menu or food</p>
                    </div>
                    <input 
                      type="file" 
                      accept="image/*" 
                      capture="environment"
                      onChange={handleFileUpload}
                      className="hidden" 
                    />
                  </label>

                  {/* Upload option - secondary */}
                  <label className="block cursor-pointer">
                    <div className="border border-gray-300 rounded-xl p-4 text-center hover:border-gray-400 hover:bg-gray-50 transition-colors">
                      <p className="text-gray-700 text-sm font-medium">or upload a photo/pdf</p>
                    </div>
                    <input type="file" accept="image/*,.pdf" onChange={handleFileUpload} className="hidden" />
                  </label>
                </div>
              )}
            </div>

            {/* Allergens */}
            <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">2. Pick Your Allergies</h3>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-2 mb-4">
                {ALLERGENS.map((allergen) => (
                  <button
                    key={allergen}
                    onClick={() => toggleAllergen(allergen)}
                    className={`px-3 py-2 rounded-lg text-base font-semibold transition-all ${
                      selectedAllergens.includes(allergen)
                        ? 'bg-emerald-500 text-gray-900'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {allergen}
                  </button>
                ))}
              </div>

              {/* Custom */}
              <div className="border-t border-gray-200 pt-4">
                <label className="block text-sm text-gray-600 mb-2">got something else?</label>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="text"
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCustomAllergen()}
                    placeholder="msg, cilantro, whatever"
                    className="flex-1 px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 text-sm focus:border-emerald-400 focus:ring-2 focus:ring-emerald-200 focus:outline-none"
                  />
                  <button
                    onClick={addCustomAllergen}
                    className="px-4 py-2 bg-emerald-500 text-gray-900 rounded-lg text-base font-semibold hover:bg-emerald-600 transition-colors"
                  >
                    Add
                  </button>
                </div>
                {customAllergens.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {customAllergens.map((allergen) => (
                      <div key={allergen} className="inline-flex items-center gap-1 px-3 py-1 bg-teal-100 border-2 border-teal-400 text-teal-800 text-sm rounded-full flex items-center gap-1">
                        {allergen}
                        <button onClick={() => removeCustomAllergen(allergen)} className="hover:bg-emerald-700 rounded-full">
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Scan button */}
            <button
              onClick={analyzeMenu}
              disabled={!menuFile || (selectedAllergens.length === 0 && customAllergens.length === 0) || analyzing}
              className="w-full py-4 bg-emerald-500 text-gray-900 rounded-xl font-bold text-lg hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {analyzing ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  reading menu...
                </>
              ) : (
                'scan'
              )}
            </button>
          </>
        ) : (
          // Results
          <div className="space-y-6">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-1">{results.restaurant_name}</h2>
                  <p className="text-gray-700 text-sm font-medium">{results.total_dishes} items • {[...selectedAllergens, ...customAllergens].join(', ')}</p>
                </div>
                <button
                  onClick={() => { setResults(null); setMenuFile(null); setSelectedAllergens([]); setCustomAllergens([]); }}
                  className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-base font-semibold hover:bg-gray-200 transition-colors"
                >
                  try another
                </button>
                <button
                  onClick={() => {
                    const text = `SafeBite Scan: ${results.safe_dishes.length} safe, ${results.unsafe_dishes.length} unsafe, ${results.unknown_dishes.length} unknown`;
                    if (navigator.share) {
                      navigator.share({ text, title: 'SafeBite Results' });
                    } else {
                      navigator.clipboard.writeText(text);
                      alert('Results copied!');
                    }
                  }}
                  className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-semibold hover:bg-emerald-600 transition-colors"
                >
                  📤 share
                </button>
              </div>



              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-emerald-50 p-6 rounded-2xl shadow-sm border-2 border-emerald-400">
                  <div className="text-4xl font-black text-emerald-700">{results.safe_dishes.length}</div>
                  <div className="text-sm font-bold text-emerald-800">safe ✓</div>
                </div>
                <div className="bg-amber-50 p-6 rounded-2xl shadow-sm border-2 border-amber-400">
                  <div className="text-4xl font-black text-amber-700">{results.unknown_dishes.length}</div>
                  <div className="text-sm font-bold text-amber-800">check these</div>
                </div>
                <div className="bg-red-50 p-6 rounded-2xl shadow-sm border-2 border-red-400">
                  <div className="text-4xl font-black text-red-700">{results.unsafe_dishes.length}</div>
                  <div className="text-sm font-bold text-red-800">skip ✗</div>
                </div>
              </div>


            </div>


            {/* AI Recommendation */}
            {results.recommendation && (
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 mb-6 border-2 border-purple-400 shadow-sm">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">✨</span>
                  <div className="flex-1">
                    <h3 className="text-lg font-black text-purple-900 mb-2">recommended for you</h3>
                    <p className="text-purple-800 font-medium">{results.recommendation}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Safe */}
            {results.safe_dishes.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                  Good to Go
                </h3>
                <div className="space-y-3">
                  {paginate(results.safe_dishes, safePage).items.map((dish: any, idx: number) => (
                    <div key={idx} className="p-6 rounded-2xl shadow-sm bg-gray-100 border border-gray-300">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-gray-900 font-semibold">{dish.name}</h4>
                        <div className={`px-3 py-1 ${getSafetyColor(dish.safety_level)} text-gray-900 rounded-full text-xs font-bold flex items-center gap-1`}>
                          {getSafetyIcon(dish.safety_level)}
                          {dish.safety_score}%
                        </div>
                      </div>
                      <p className="text-gray-600 text-sm mb-2">{dish.description}</p>
                      {dish.ai_reasoning && (
                        <div className="bg-emerald-100 rounded-lg p-3 mb-2 border border-emerald-300">
                          <p className="text-emerald-800 text-sm font-medium">
                            <span className="font-bold">why it's safe:</span> {dish.ai_reasoning}
                          </p>
                        </div>
                      )}
                      <p className="text-gray-700 text-sm font-medium italic">{dish.recommendations}</p>
                    </div>
                  ))}
                </div>
                {/* Safe Pagination */}
                {paginate(results.safe_dishes, safePage).totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 mt-4 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => setSafePage(p => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      className="px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-emerald-200 transition-colors"
                    >
                      ← prev
                    </button>
                    <span className="text-sm text-gray-600 font-medium">
                      {safePage} / {paginate(results.safe_dishes, safePage).totalPages}
                    </span>
                    <button
                      onClick={() => setSafePage(p => Math.min(paginate(results.safe_dishes, safePage).totalPages, p + 1))}
                      disabled={safePage === paginate(results.safe_dishes, safePage).totalPages}
                      className="px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-emerald-200 transition-colors"
                    >
                      next →
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Unknown - Check These */}
            {results.unknown_dishes.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200 mt-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <HelpCircle className="w-5 h-5 text-amber-600" />
                  Check These
                </h3>
                <div className="space-y-3">
                  {paginate(results.unknown_dishes, unknownPage).items.map((dish: any, idx: number) => (
                    <div key={idx} className="p-6 rounded-2xl shadow-sm bg-gray-100 border border-amber-400">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-gray-900 font-semibold">{dish.name}</h4>
                        <div className={`px-3 py-1 ${getSafetyColor(dish.safety_level)} text-gray-900 rounded-full text-xs font-bold flex items-center gap-1`}>
                          {getSafetyIcon(dish.safety_level)}
                          {dish.safety_score}%
                        </div>
                      </div>
                      <p className="text-gray-600 text-sm mb-2">{dish.description}</p>
                      {dish.ai_reasoning && (
                        <div className="bg-amber-100 rounded-lg p-3 mb-2 border border-amber-300">
                          <p className="text-amber-800 text-sm font-medium">
                            <span className="font-bold">why uncertain:</span> {dish.ai_reasoning}
                          </p>
                        </div>
                      )}
                      <p className="text-amber-700 text-sm font-semibold">{dish.recommendations}</p>
                    </div>
                  ))}
                </div>
                {/* Unknown Pagination */}
                {paginate(results.unknown_dishes, unknownPage).totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 mt-4 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => setUnknownPage(p => Math.max(1, p - 1))}
                      disabled={unknownPage === 1}
                      className="px-4 py-2 bg-amber-100 text-amber-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-amber-200 transition-colors"
                    >
                      ← prev
                    </button>
                    <span className="text-sm text-gray-600 font-medium">
                      {unknownPage} / {paginate(results.unknown_dishes, unknownPage).totalPages}
                    </span>
                    <button
                      onClick={() => setUnknownPage(p => Math.min(paginate(results.unknown_dishes, unknownPage).totalPages, p + 1))}
                      disabled={unknownPage === paginate(results.unknown_dishes, unknownPage).totalPages}
                      className="px-4 py-2 bg-amber-100 text-amber-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-amber-200 transition-colors"
                    >
                      next →
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Unsafe */}
            {results.unsafe_dishes.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-red-600" />
                  Skip These
                </h3>
                <div className="space-y-3">
                  {paginate(results.unsafe_dishes, unsafePage).items.map((dish: any, idx: number) => (
                    <div key={idx} className="p-6 rounded-2xl shadow-sm bg-gray-100 border border-red-900">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-gray-900 font-semibold">{dish.name}</h4>
                        <div className={`px-3 py-1 ${getSafetyColor(dish.safety_level)} text-gray-900 rounded-full text-xs font-bold flex items-center gap-1`}>
                          {getSafetyIcon(dish.safety_level)}
                          {dish.safety_score}%
                        </div>
                      </div>
                      <p className="text-gray-600 text-sm mb-2">{dish.description}</p>
                      {dish.detected_allergens.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {dish.detected_allergens.map((allergen: string, i: number) => (
                            <span key={i} className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                              {allergen}
                            </span>
                          ))}
                        </div>
                      )}
                      {dish.ai_reasoning && (
                        <div className="bg-red-100 rounded-lg p-3 mb-2 border border-red-300">
                          <p className="text-red-800 text-sm font-medium">
                            <span className="font-bold">why to skip:</span> {dish.ai_reasoning}
                          </p>
                        </div>
                      )}
                      <p className="text-red-700 text-sm font-semibold">{dish.recommendations}</p>
                    </div>
                  ))}
                </div>
                {/* Unsafe Pagination */}
                {paginate(results.unsafe_dishes, unsafePage).totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 mt-4 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => setUnsafePage(p => Math.max(1, p - 1))}
                      disabled={unsafePage === 1}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-200 transition-colors"
                    >
                      ← prev
                    </button>
                    <span className="text-sm text-gray-600 font-medium">
                      {unsafePage} / {paginate(results.unsafe_dishes, unsafePage).totalPages}
                    </span>
                    <button
                      onClick={() => setUnsafePage(p => Math.min(paginate(results.unsafe_dishes, unsafePage).totalPages, p + 1))}
                      disabled={unsafePage === paginate(results.unsafe_dishes, unsafePage).totalPages}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-200 transition-colors"
                    >
                      next →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <footer className="border-t border-gray-200 mt-12 pt-6">
          <div className="flex justify-between items-center text-xs text-gray-500">
            <p>always double-check with staff</p>
            <span className="text-gray-500">made in ke 🎴</span>
          </div>
        </footer>
      </div>

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Console Easter Egg */}
      <ConsoleEasterEgg />
      {/* PWA Install Prompt */}
      {showPWAPrompt && (
        <div className="fixed bottom-6 left-6 right-6 z-50 animate-slide-up" style={{zIndex: 60}}>
          <div className="bg-white rounded-2xl p-4 shadow-2xl border border-gray-200 flex items-center gap-3">
            <div className="flex-1">
              <p className="text-gray-900 font-semibold text-sm mb-1">install SafeBite</p>
              <p className="text-gray-600 text-xs">quick access from your home screen 🎴</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={() => setShowPWAPrompt(false)}
                className="px-3 py-2 text-gray-500 text-base font-semibold"
              >
                later
              </button>
              <button
                onClick={handleInstallPWA}
                className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-semibold"
              >
                install
              </button>
            </div>
          </div>
        </div>
      )}

      
      {/* Scan History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-6" onClick={() => setShowHistory(false)}>
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white z-10">
              <h2 className="text-2xl font-bold text-gray-900">scan history</h2>
              <button onClick={() => setShowHistory(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
            </div>
            <div className="p-6">
              {scanHistory.length === 0 ? (
                <p className="text-gray-500 text-center py-12">no scans yet. snap your first menu!</p>
              ) : (
                <div className="space-y-3">
                  {scanHistory.map((scan: any) => (
                    <div key={scan.id} className="border-2 border-gray-200 rounded-xl p-4 hover:border-emerald-400 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-bold text-gray-900">{scan.filename}</p>
                          <p className="text-xs text-gray-500">{new Date(scan.timestamp).toLocaleString()}</p>
                        </div>
                        <span className="text-sm font-semibold text-gray-700">{scan.results.total} dishes</span>
                      </div>
                      <div className="flex gap-2 text-sm mb-2">
                        <span className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded-lg font-semibold">✓ {scan.results.safe}</span>
                        <span className="px-2 py-1 bg-red-100 text-red-800 rounded-lg font-semibold">✗ {scan.results.unsafe}</span>
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-lg font-semibold">? {scan.results.unknown}</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {scan.allergens?.map((a: string) => (
                          <span key={a} className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full font-medium">{a}</span>
                        ))}
                        {scan.customAllergens?.map((a: string) => (
                          <span key={a} className="text-xs px-2 py-1 bg-pink-100 text-pink-800 rounded-full font-medium">{a}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {scanHistory.length > 0 && (
              <div className="p-6 border-t border-gray-200 flex justify-between">
                <button
                  onClick={() => {
                    if (confirm('Clear all scan history?')) {
                      localStorage.removeItem('safebite_history');
                      setScanHistory([]);
                      setShowHistory(false);
                    }
                  }}
                  className="text-sm text-red-600 hover:text-red-700 font-semibold"
                >
                  🗑️ clear all
                </button>
                <p className="text-xs text-gray-500">{scanHistory.length} scans saved</p>
              </div>
            )}

          </div>
        </div>
      )}


      {/* Camera View Modal */}
      {showCamera && (
        <CameraView
          onCapture={(file) => {
            setMenuFile(file);
            setShowCamera(false);
          }}
          onClose={() => setShowCamera(false)}
        />
      )}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <ConsoleEasterEgg />
      <FeedbackForm />
    </div>
  );
}
