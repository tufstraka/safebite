'use client';

import { useState, useEffect } from 'react';
import { Shield, Upload, AlertTriangle, CheckCircle, XCircle, HelpCircle, X, Camera } from 'lucide-react';
import Toast from './components/Toast';
import ConsoleEasterEgg from './components/ConsoleEasterEgg';
import CameraView from './components/CameraView';

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
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-pink-50 to-purple-50 relative overflow-hidden">
      {/* Kenyan-inspired illustrations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Soft gradient orbs */}
        <div className="absolute top-20 right-10 w-96 h-96 bg-gradient-to-br from-purple-200/40 to-pink-200/40 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 left-10 w-80 h-80 bg-gradient-to-br from-emerald-200/40 to-cyan-200/40 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-gradient-to-br from-yellow-200/30 to-orange-200/30 rounded-full blur-3xl"></div>
        
        {/* Kenyan patterns - geometric African motifs */}
        <svg className="absolute top-32 left-20 w-32 h-32 opacity-5 text-orange-600" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="2"/>
          <circle cx="50" cy="50" r="30" fill="none" stroke="currentColor" strokeWidth="2"/>
          <circle cx="50" cy="50" r="15" fill="none" stroke="currentColor" strokeWidth="2"/>
          <line x1="50" y1="5" x2="50" y2="95" stroke="currentColor" strokeWidth="1"/>
          <line x1="5" y1="50" x2="95" y2="50" stroke="currentColor" strokeWidth="1"/>
        </svg>
        
        <svg className="absolute bottom-32 right-20 w-40 h-40 opacity-5 text-emerald-600" viewBox="0 0 100 100">
          <polygon points="50,10 90,35 75,75 25,75 10,35" fill="none" stroke="currentColor" strokeWidth="2"/>
          <polygon points="50,25 75,40 65,65 35,65 25,40" fill="none" stroke="currentColor" strokeWidth="2"/>
          <circle cx="50" cy="50" r="10" fill="currentColor" opacity="0.3"/>
        </svg>
        
        <svg className="absolute top-1/3 right-1/4 w-24 h-24 opacity-5 text-red-600" viewBox="0 0 100 100">
          <rect x="20" y="20" width="60" height="60" fill="none" stroke="currentColor" strokeWidth="2" transform="rotate(45 50 50)"/>
          <rect x="35" y="35" width="30" height="30" fill="none" stroke="currentColor" strokeWidth="2" transform="rotate(45 50 50)"/>
        </svg>
        
        {/* Maasai-inspired zigzag patterns */}
        <svg className="absolute bottom-1/4 left-1/3 w-48 h-16 opacity-5 text-yellow-700" viewBox="0 0 200 50">
          <path d="M0,25 L20,10 L40,25 L60,10 L80,25 L100,10 L120,25 L140,10 L160,25 L180,10 L200,25" 
                fill="none" stroke="currentColor" strokeWidth="3"/>
          <path d="M0,35 L20,20 L40,35 L60,20 L80,35 L100,20 L120,35 L140,20 L160,35 L180,20 L200,35" 
                fill="none" stroke="currentColor" strokeWidth="2"/>
        </svg>
        
        {/* Additional Kenyan patterns */}
        <svg className="absolute top-1/2 left-20 w-28 h-28 opacity-5 text-red-700" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="2"/>
          <path d="M50,10 L50,90 M10,50 L90,50 M20,20 L80,80 M80,20 L20,80" stroke="currentColor" strokeWidth="1"/>
        </svg>
        
        <svg className="absolute top-3/4 right-1/3 w-36 h-36 opacity-5 text-green-700" viewBox="0 0 100 100">
          <polygon points="50,5 95,35 80,85 20,85 5,35" fill="none" stroke="currentColor" strokeWidth="2"/>
          <polygon points="50,20 80,40 70,75 30,75 20,40" fill="none" stroke="currentColor" strokeWidth="2"/>
          <circle cx="50" cy="55" r="8" fill="currentColor" opacity="0.4"/>
        </svg>
        
        <svg className="absolute bottom-1/3 right-10 w-32 h-32 opacity-5 text-purple-700" viewBox="0 0 100 100">
          <rect x="10" y="10" width="80" height="80" fill="none" stroke="currentColor" strokeWidth="2"/>
          <rect x="25" y="25" width="50" height="50" fill="none" stroke="currentColor" strokeWidth="2"/>
          <rect x="40" y="40" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"/>
        </svg>
        
        <svg className="absolute top-1/4 left-1/2 w-24 h-40 opacity-5 text-orange-700" viewBox="0 0 100 150">
          <path d="M10,10 L50,30 L90,10 L90,50 L50,70 L10,50 Z" fill="none" stroke="currentColor" strokeWidth="2"/>
          <path d="M30,30 L50,40 L70,30 L70,60 L50,70 L30,60 Z" fill="none" stroke="currentColor" strokeWidth="2"/>
        </svg>
        
        {/* More zigzag patterns */}
        <svg className="absolute top-16 right-1/2 w-40 h-12 opacity-5 text-emerald-700" viewBox="0 0 200 50">
          <path d="M0,10 L15,25 L30,10 L45,25 L60,10 L75,25 L90,10 L105,25 L120,10 L135,25 L150,10 L165,25 L180,10 L195,25" 
                fill="none" stroke="currentColor" strokeWidth="2"/>
        </svg>
      </div>
      {/* Simple header */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50 relative shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-3">
          <Shield className="w-6 h-6 text-emerald-400" />
          <div className="flex items-center gap-1.5">
            <h1 className="text-xl font-bold text-gray-900">SafeBite</h1>
            <span className="text-xs text-slate-500">by</span>
            <a 
              href="https://github.com/tufstraka" 
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:text-emerald-300 transition-colors font-bold text-sm"
              title="by @dobynog"
            >
              .
            </a>
          </div>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-12 relative z-10">
        {!results ? (
          <>
            {/* Direct intro */}
            <div className="mb-8">
              <h2 className="text-4xl font-bold text-gray-900 mb-3">snap your food</h2>
              <p className="text-lg text-gray-600">take a pic. we'll check the allergens.</p>
            </div>

            {/* Upload */}
            <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-200 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">1. snap it</h3>
              
              {menuFile ? (
                <div className="border-2 border-emerald-500 bg-emerald-50 rounded-xl p-6 text-center">
                  <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                  <p className="text-gray-900 font-medium">{menuFile.name}</p>
                  <p className="text-gray-500 text-sm mt-1">{(menuFile.size / 1024 / 1024).toFixed(2)} MB</p>
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
                      <p className="text-gray-500 text-sm">or upload a photo/pdf</p>
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
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
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
                <label className="block text-sm text-gray-600 mb-2">Add Custom</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCustomAllergen()}
                    placeholder="MSG, Cilantro, etc."
                    className="flex-1 px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 text-sm focus:border-emerald-400 focus:ring-2 focus:ring-emerald-200 focus:outline-none"
                  />
                  <button
                    onClick={addCustomAllergen}
                    className="px-4 py-2 bg-emerald-500 text-gray-900 rounded-lg text-sm font-medium hover:bg-emerald-600 transition-colors"
                  >
                    Add
                  </button>
                </div>
                {customAllergens.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {customAllergens.map((allergen) => (
                      <div key={allergen} className="px-3 py-1 bg-emerald-600 text-gray-900 text-sm rounded-full flex items-center gap-1">
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
                  <p className="text-gray-500 text-sm">{results.total_dishes} items • {[...selectedAllergens, ...customAllergens].join(', ')}</p>
                </div>
                <button
                  onClick={() => { setResults(null); setMenuFile(null); setSelectedAllergens([]); setCustomAllergens([]); }}
                  className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                >
                  try another
                </button>
              </div>



              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-emerald-900/30 p-4 rounded-lg border border-emerald-800">
                  <div className="text-2xl font-bold text-emerald-400">{results.safe_dishes.length}</div>
                  <div className="text-xs text-emerald-300">safe ✓</div>
                </div>
                <div className="bg-yellow-900/30 p-4 rounded-lg border border-yellow-800">
                  <div className="text-2xl font-bold text-yellow-400">{results.unknown_dishes.length}</div>
                  <div className="text-xs text-yellow-300">check these</div>
                </div>
                <div className="bg-red-900/30 p-4 rounded-lg border border-red-800">
                  <div className="text-2xl font-bold text-red-400">{results.unsafe_dishes.length}</div>
                  <div className="text-xs text-red-300">skip ✗</div>
                </div>
              </div>


            </div>

            {/* Safe */}
            {results.safe_dishes.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  Good to Go
                </h3>
                <div className="space-y-3">
                  {results.safe_dishes.map((dish: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-lg bg-gray-100 border border-gray-300">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-gray-900 font-semibold">{dish.name}</h4>
                        <div className={`px-3 py-1 ${getSafetyColor(dish.safety_level)} text-gray-900 rounded-full text-xs font-bold flex items-center gap-1`}>
                          {getSafetyIcon(dish.safety_level)}
                          {dish.safety_score}%
                        </div>
                      </div>
                      <p className="text-gray-600 text-sm mb-2">{dish.description}</p>
                      <p className="text-gray-500 text-sm italic">{dish.recommendations}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Unsafe */}
            {results.unsafe_dishes.length > 0 && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-red-400" />
                  Skip These
                </h3>
                <div className="space-y-3">
                  {results.unsafe_dishes.map((dish: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-lg bg-gray-100 border border-red-900">
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
                            <span key={i} className="px-2 py-1 bg-red-900 text-red-200 rounded text-xs font-medium">
                              {allergen}
                            </span>
                          ))}
                        </div>
                      )}
                      <p className="text-red-300 text-sm font-medium">{dish.recommendations}</p>
                    </div>
                  ))}
                </div>
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
        <div className="fixed bottom-6 left-6 right-6 z-50 animate-slide-up">
          <div className="bg-white rounded-2xl p-4 shadow-2xl border border-gray-200 flex items-center gap-3">
            <div className="flex-1">
              <p className="text-gray-900 font-semibold text-sm mb-1">install SafeBite</p>
              <p className="text-gray-600 text-xs">quick access from your home screen 🎴</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowPWAPrompt(false)}
                className="px-3 py-2 text-gray-500 text-sm font-medium"
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
    </div>
  );
}
