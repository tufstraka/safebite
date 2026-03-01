'use client';

import { useState } from 'react';
import { Shield, Upload, AlertTriangle, CheckCircle, XCircle, HelpCircle, Volume2, Sparkles, Plus, X } from 'lucide-react';

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
      alert('Please upload a menu and select at least one allergen');
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
      alert('Analysis failed. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const getSafetyColor = (level: string) => {
    const colors: any = {
      'Safe': 'from-green-400 to-emerald-500',
      'Likely Safe': 'from-blue-400 to-cyan-500',
      'Unknown': 'from-yellow-400 to-orange-500',
      'Caution': 'from-orange-500 to-red-500',
      'Unsafe': 'from-red-500 to-rose-600'
    };
    return colors[level] || 'from-gray-400 to-gray-500';
  };

  const getSafetyIcon = (level: string) => {
    if (level === 'Safe' || level === 'Likely Safe') return <CheckCircle className="w-6 h-6" />;
    if (level === 'Unknown') return <HelpCircle className="w-6 h-6" />;
    return <AlertTriangle className="w-6 h-6" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 relative overflow-hidden">
      {/* Abstract Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-0 left-1/3 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Navigation */}
        <nav className="border-b border-white/10 bg-black/20 backdrop-blur-xl sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-2xl shadow-purple-500/50">
                  <Shield className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-300 via-pink-300 to-blue-300">
                    SafeBite AI
                  </h1>
                  <p className="text-xs text-purple-300/70">Powered by Amazon Nova</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="px-4 py-2 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-400/30 rounded-full backdrop-blur-sm">
                  <span className="text-sm font-semibold text-purple-200">Multimodal AI</span>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-6 py-16">
          {!results && (
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 px-5 py-2 bg-white/10 backdrop-blur-md rounded-full border border-white/20 mb-8">
                <Sparkles className="w-4 h-4 text-purple-300" />
                <span className="text-sm font-medium text-purple-200">AI-Powered Menu Safety Analysis</span>
              </div>

              <h2 className="text-6xl font-black text-white mb-6 leading-tight">
                Eat Safely.<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-300 via-pink-300 to-blue-300">
                  Every Time.
                </span>
              </h2>

              <p className="text-xl text-purple-200/80 max-w-3xl mx-auto leading-relaxed">
                Upload a menu photo or PDF. Select your allergies. Get instant dish-by-dish safety analysis powered by Amazon Nova's multimodal AI.
              </p>
            </div>
          )}

          {/* Analysis Interface */}
          {!results && (
            <div className="max-w-4xl mx-auto space-y-8">
              {/* Menu Upload */}
              <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
                <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                  <Upload className="w-6 h-6 text-purple-300" />
                  Upload Menu
                </h3>

                <label className="block cursor-pointer">
                  <div className="border-2 border-dashed border-white/20 rounded-2xl p-12 text-center hover:border-purple-400/50 hover:bg-white/5 transition-all">
                    {menuFile ? (
                      <div className="space-y-3">
                        <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
                        <p className="text-white font-semibold">{menuFile.name}</p>
                        <p className="text-purple-300/70 text-sm">
                          {menuFile.name.toLowerCase().endsWith('.pdf') ? 'PDF Document' : 'Image File'} • Click to change
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <Upload className="w-12 h-12 text-purple-300/50 mx-auto" />
                        <p className="text-white font-semibold">Drop menu image or PDF, or click to browse</p>
                        <p className="text-purple-300/70 text-sm">Supports JPG, PNG, PDF (max 50MB)</p>
                      </div>
                    )}
                  </div>
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              </div>

              {/* Allergen Selection */}
              <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
                <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-purple-300" />
                  Select Your Allergies
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-6">
                  {ALLERGENS.map((allergen) => (
                    <button
                      key={allergen}
                      onClick={() => toggleAllergen(allergen)}
                      className={`px-4 py-3 rounded-xl font-semibold transition-all ${
                        selectedAllergens.includes(allergen)
                          ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/50 scale-105'
                          : 'bg-white/10 text-purple-200 hover:bg-white/20 border border-white/20'
                      }`}
                    >
                      {allergen}
                    </button>
                  ))}
                </div>

                {/* Custom Allergen Input */}
                <div className="border-t border-white/10 pt-6">
                  <label className="block text-sm font-semibold text-purple-200 mb-3">Add Custom Allergen</label>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={customInput}
                      onChange={(e) => setCustomInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addCustomAllergen()}
                      placeholder="e.g., Cilantro, MSG, Nightshades..."
                      className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-purple-300/50 focus:border-purple-400/50 focus:outline-none"
                    />
                    <button
                      onClick={addCustomAllergen}
                      className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-purple-500/50 transition-all flex items-center gap-2"
                    >
                      <Plus className="w-5 h-5" />
                      Add
                    </button>
                  </div>

                  {/* Custom Allergens List */}
                  {customAllergens.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {customAllergens.map((allergen) => (
                        <div
                          key={allergen}
                          className="px-4 py-2 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-semibold flex items-center gap-2 shadow-lg shadow-pink-500/30"
                        >
                          {allergen}
                          <button
                            onClick={() => removeCustomAllergen(allergen)}
                            className="hover:bg-white/20 rounded-full p-1 transition-all"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Analyze Button */}
              <button
                onClick={analyzeMenu}
                disabled={!menuFile || (selectedAllergens.length === 0 && customAllergens.length === 0) || analyzing}
                className="w-full py-6 bg-gradient-to-r from-purple-500 via-pink-500 to-blue-500 text-white rounded-2xl font-bold text-xl hover:shadow-2xl hover:shadow-purple-500/50 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 transition-all flex items-center justify-center gap-3"
              >
                {analyzing ? (
                  <>
                    <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                    Analyzing Menu...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-6 h-6" />
                    Analyze Safety
                  </>
                )}
              </button>
            </div>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-8">
              {/* Header */}
              <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-4xl font-black text-white mb-3">{results.restaurant_name}</h2>
                    <p className="text-purple-300/80">Found {results.total_dishes} dishes • Analyzed for {[...selectedAllergens, ...customAllergens].join(', ')}</p>
                  </div>
                  <button
                    onClick={() => { setResults(null); setMenuFile(null); setSelectedAllergens([]); setCustomAllergens([]); }}
                    className="px-6 py-3 bg-white/10 text-white rounded-xl font-semibold hover:bg-white/20 transition-all border border-white/20"
                  >
                    New Scan
                  </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 p-6 rounded-2xl border border-green-400/30">
                    <div className="text-4xl font-black text-green-300 mb-1">{results.safe_dishes.length}</div>
                    <div className="text-sm font-semibold text-green-200">Safe Dishes</div>
                  </div>

                  <div className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 p-6 rounded-2xl border border-yellow-400/30">
                    <div className="text-4xl font-black text-yellow-300 mb-1">{results.unknown_dishes.length}</div>
                    <div className="text-sm font-semibold text-yellow-200">Unknown</div>
                  </div>

                  <div className="bg-gradient-to-br from-red-500/20 to-rose-500/20 p-6 rounded-2xl border border-red-400/30">
                    <div className="text-4xl font-black text-red-300 mb-1">{results.unsafe_dishes.length}</div>
                    <div className="text-sm font-semibold text-red-200">Unsafe</div>
                  </div>
                </div>

                {/* Voice Summary */}
                <div className="mt-6 flex items-start gap-4 p-5 bg-purple-500/20 rounded-2xl border border-purple-400/30">
                  <Volume2 className="w-6 h-6 text-purple-300 flex-shrink-0 mt-1" />
                  <p className="text-purple-100 leading-relaxed">{results.voice_summary}</p>
                </div>
              </div>

              {/* Safe Dishes */}
              {results.safe_dishes.length > 0 && (
                <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
                  <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                    <CheckCircle className="w-6 h-6 text-green-400" />
                    Safe Dishes
                  </h3>

                  <div className="space-y-4">
                    {results.safe_dishes.map((dish: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-6 rounded-2xl bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-400/20 hover:border-green-400/40 transition-all"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h4 className="text-xl font-bold text-white mb-2">{dish.name}</h4>
                            <p className="text-green-200/70 text-sm">{dish.description}</p>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className={`px-4 py-2 bg-gradient-to-r ${getSafetyColor(dish.safety_level)} rounded-xl font-bold text-white flex items-center gap-2`}>
                              {getSafetyIcon(dish.safety_level)}
                              {dish.safety_score}%
                            </div>
                          </div>
                        </div>
                        <p className="text-green-300/80 text-sm italic">{dish.recommendations}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Unsafe Dishes */}
              {results.unsafe_dishes.length > 0 && (
                <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
                  <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                    <XCircle className="w-6 h-6 text-red-400" />
                    Dishes to Avoid
                  </h3>

                  <div className="space-y-4">
                    {results.unsafe_dishes.map((dish: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-6 rounded-2xl bg-gradient-to-r from-red-500/10 to-rose-500/10 border border-red-400/20"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h4 className="text-xl font-bold text-white mb-2">{dish.name}</h4>
                            <p className="text-red-200/70 text-sm">{dish.description}</p>
                          </div>
                          <div className={`px-4 py-2 bg-gradient-to-r ${getSafetyColor(dish.safety_level)} rounded-xl font-bold text-white flex items-center gap-2`}>
                            {getSafetyIcon(dish.safety_level)}
                            {dish.safety_score}%
                          </div>
                        </div>
                        {dish.detected_allergens.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-3">
                            {dish.detected_allergens.map((allergen: string, i: number) => (
                              <span key={i} className="px-3 py-1 bg-red-500/30 text-red-200 rounded-lg text-xs font-semibold border border-red-400/30">
                                {allergen}
                              </span>
                            ))}
                          </div>
                        )}
                        <p className="text-red-300/80 text-sm italic font-semibold">{dish.recommendations}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="border-t border-white/10 bg-black/20 backdrop-blur-xl mt-20">
          <div className="max-w-7xl mx-auto px-6 py-8 text-center">
            <p className="text-sm text-purple-300/70">
              Built for Amazon Nova Hackathon 2026 | Category: Multimodal Understanding
            </p>
            <p className="text-xs text-purple-400/50 mt-2">
              Powered by Amazon Nova Pro, Lite, Act, Sonic, and Embeddings
            </p>
          </div>
        </footer>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(20px, -50px) scale(1.1); }
          50% { transform: translate(-20px, 20px) scale(0.9); }
          75% { transform: translate(50px, 50px) scale(1.05); }
        }
        .animate-blob {
          animation: blob 20s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}
