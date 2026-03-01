'use client';

import { useState } from 'react';
import { Shield, Upload, AlertTriangle, CheckCircle, XCircle, HelpCircle, X } from 'lucide-react';

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

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setMenuFile(e.target.files[0]);
    }
  };

  const analyzeMenu = async () => {
    const allAllergens = [...selectedAllergens, ...customAllergens];
    
    if (!menuFile || allAllergens.length === 0) {
      alert('need a menu and at least one allergen');
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
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response:', {
        restaurant: data.restaurant_name,
        total_dishes: data.total_dishes,
        first_dish: data.safe_dishes[0]?.name || data.unsafe_dishes[0]?.name
      });
      
      setResults(data);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert("hmm, that didn't work. try again?");
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Simple header */}
      <nav className="border-b border-slate-700 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-emerald-400" />
            <div>
              <h1 className="text-xl font-bold text-white">SafeBite</h1>
              <p className="text-xs text-slate-500">by @dobynog</p>
            </div>
          </div>
          <a 
            href="https://github.com/tufstraka" 
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-400 hover:text-slate-300 transition-colors"
          >
            github ↗
          </a>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-12">
        {!results ? (
          <>
            {/* Direct intro */}
            <div className="mb-8">
              <h2 className="text-4xl font-bold text-white mb-3">Check Your Menu</h2>
              <p className="text-lg text-slate-300">Upload. Pick. Done.</p>
            </div>

            {/* Upload */}
            <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">1. Upload Menu</h3>
              <label className="block cursor-pointer">
                <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center hover:border-emerald-500 hover:bg-slate-700/50 transition-colors">
                  {menuFile ? (
                    <div>
                      <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
                      <p className="text-white font-medium">{menuFile.name}</p>
                      <p className="text-slate-400 text-sm mt-1">Click to change</p>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                      <p className="text-white font-medium">Drop file or click to browse</p>
                      <p className="text-slate-400 text-sm mt-1">Photos or PDFs up to 50MB</p>
                    </div>
                  )}
                </div>
                <input type="file" accept="image/*,.pdf" onChange={handleFileUpload} className="hidden" />
              </label>
            </div>

            {/* Allergens */}
            <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">2. Pick Your Allergies</h3>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-2 mb-4">
                {ALLERGENS.map((allergen) => (
                  <button
                    key={allergen}
                    onClick={() => toggleAllergen(allergen)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      selectedAllergens.includes(allergen)
                        ? 'bg-emerald-500 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {allergen}
                  </button>
                ))}
              </div>

              {/* Custom */}
              <div className="border-t border-slate-700 pt-4">
                <label className="block text-sm text-slate-300 mb-2">Add Custom</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addCustomAllergen()}
                    placeholder="MSG, Cilantro, etc."
                    className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                  <button
                    onClick={addCustomAllergen}
                    className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-colors"
                  >
                    Add
                  </button>
                </div>
                {customAllergens.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {customAllergens.map((allergen) => (
                      <div key={allergen} className="px-3 py-1 bg-emerald-600 text-white text-sm rounded-full flex items-center gap-1">
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
              className="w-full py-4 bg-emerald-500 text-white rounded-xl font-bold text-lg hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {analyzing ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  hold up, scanning...
                </>
              ) : (
                'Check It'
              )}
            </button>
          </>
        ) : (
          // Results
          <div className="space-y-6">
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-1">{results.restaurant_name}</h2>
                  <p className="text-slate-400 text-sm">{results.total_dishes} items • {[...selectedAllergens, ...customAllergens].join(', ')}</p>
                </div>
                <button
                  onClick={() => { setResults(null); setMenuFile(null); setSelectedAllergens([]); setCustomAllergens([]); }}
                  className="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-600 transition-colors"
                >
                  Try Another
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

              <div className="bg-slate-700/50 rounded-lg p-4">
                <p className="text-slate-300 text-sm">{results.voice_summary}</p>
              </div>
            </div>

            {/* Safe */}
            {results.safe_dishes.length > 0 && (
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  Good to Go
                </h3>
                <div className="space-y-3">
                  {results.safe_dishes.map((dish: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-lg bg-slate-700 border border-slate-600">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-white font-semibold">{dish.name}</h4>
                        <div className={`px-3 py-1 ${getSafetyColor(dish.safety_level)} text-white rounded-full text-xs font-bold flex items-center gap-1`}>
                          {getSafetyIcon(dish.safety_level)}
                          {dish.safety_score}%
                        </div>
                      </div>
                      <p className="text-slate-300 text-sm mb-2">{dish.description}</p>
                      <p className="text-slate-400 text-sm italic">{dish.recommendations}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Unsafe */}
            {results.unsafe_dishes.length > 0 && (
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-red-400" />
                  Skip These
                </h3>
                <div className="space-y-3">
                  {results.unsafe_dishes.map((dish: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-lg bg-slate-700 border border-red-900">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-white font-semibold">{dish.name}</h4>
                        <div className={`px-3 py-1 ${getSafetyColor(dish.safety_level)} text-white rounded-full text-xs font-bold flex items-center gap-1`}>
                          {getSafetyIcon(dish.safety_level)}
                          {dish.safety_score}%
                        </div>
                      </div>
                      <p className="text-slate-300 text-sm mb-2">{dish.description}</p>
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
        <footer className="border-t border-slate-700 mt-12 pt-6">
          <div className="flex justify-between items-center text-xs text-slate-400">
            <p>always double-check with staff</p>
            <div className="flex items-center gap-4">
              <a 
                href="https://github.com/tufstraka/bounty-recon-ai" 
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-slate-300 transition-colors"
              >
                source
              </a>
              <a 
                href="https://x.com/dobynog" 
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-slate-300 transition-colors"
              >
                @dobynog
              </a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
