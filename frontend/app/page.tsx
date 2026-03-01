'use client';

import { useState } from 'react';
import { Shield, Search, AlertTriangle, CheckCircle, XCircle, FileText, Download, Clock, Target, Activity, TrendingUp } from 'lucide-react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState('');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<any>(null);

  const startScan = async () => {
    if (!url) return;
    
    setScanning(true);
    setProgress(0);
    setResults(null);
    
    try {
      const response = await fetch('/api/scans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_url: url,
          scan_type: 'deep',
          include_subdomains: true,
          include_screenshots: true,
          max_depth: 3
        })
      });
      
      const data = await response.json();
      setScanId(data.scan_id);
      
      // Poll for results
      pollScanStatus(data.scan_id);
    } catch (error) {
      console.error('Scan failed:', error);
      setScanning(false);
    }
  };
  
  const pollScanStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`/api/scans/${id}/status`);
        const status = await statusResponse.json();
        
        setProgress(status.progress);
        
        if (status.status === 'completed') {
          clearInterval(interval);
          
          const resultsResponse = await fetch(`/api/scans/${id}/results`);
          const results = await resultsResponse.json();
          
          setResults(results);
          setScanning(false);
        } else if (status.status === 'failed') {
          clearInterval(interval);
          setScanning(false);
        }
      } catch (error) {
        console.error('Polling failed:', error);
      }
    }, 1000);
  };

  const getSeverityColor = (severity: string) => {
    const colors: any = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200',
      info: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[severity] || colors.info;
  };

  const getSeverityIcon = (severity: string) => {
    if (severity === 'critical' || severity === 'high') return <AlertTriangle className="w-5 h-5" />;
    if (severity === 'medium') return <XCircle className="w-5 h-5" />;
    return <CheckCircle className="w-5 h-5" />;
  };

  const exportReport = async () => {
    if (!results) return;
    
    try {
      const response = await fetch(`/api/scans/${results.scan_id}/report/pdf`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bounty-recon-${results.scan_id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('PDF export failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl shadow-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Bounty Recon AI
                </h1>
                <p className="text-xs text-gray-500">Powered by Amazon Nova Pro</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-semibold rounded-full shadow-md">
                Amazon Nova Hackathon 2026
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {!results && (
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-md mb-6 border border-indigo-100">
              <Activity className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-gray-700">AI-Powered Security Reconnaissance</span>
            </div>
            
            <h2 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Automate Your Bug Bounty
              <br />
              <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Reconnaissance Workflow
              </span>
            </h2>
            
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Leverage Amazon Nova Pro to intelligently crawl, analyze, and discover security vulnerabilities 
              in your target applications. Save hours of manual reconnaissance work.
            </p>
          </div>
        )}

        {/* Scan Input */}
        {!results && (
          <div className="max-w-3xl mx-auto mb-16">
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
              <label className="block text-sm font-semibold text-gray-700 mb-3">Target URL</label>
              
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <Target className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="url"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={scanning}
                    className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-lg transition-all disabled:bg-gray-50 disabled:cursor-not-allowed"
                  />
                </div>
                
                <button
                  onClick={startScan}
                  disabled={!url || scanning}
                  className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-2 transition-all"
                >
                  {scanning ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Scanning...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      Start Recon
                    </>
                  )}
                </button>
              </div>
              
              {scanning && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Scan Progress</span>
                    <span className="text-sm font-bold text-indigo-600">{progress}%</span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 transition-all duration-500 rounded-full"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Results Section */}
        {results && (
          <div className="space-y-8">
            {/* Header */}
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Reconnaissance Report</h2>
                  <p className="text-gray-600">Target: <span className="font-mono font-semibold text-indigo-600">{results.target}</span></p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={exportReport}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg flex items-center gap-2 transition-all"
                  >
                    <Download className="w-4 h-4" />
                    Export Report
                  </button>
                  <button
                    onClick={() => { setResults(null); setUrl(''); }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-all"
                  >
                    New Scan
                  </button>
                </div>
              </div>

              {/* Statistics Cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-xl border border-red-200">
                  <div className="text-3xl font-bold text-red-700">{results.statistics.critical || 0}</div>
                  <div className="text-sm font-medium text-red-600">Critical</div>
                </div>
                
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl border border-orange-200">
                  <div className="text-3xl font-bold text-orange-700">{results.statistics.high || 0}</div>
                  <div className="text-sm font-medium text-orange-600">High</div>
                </div>
                
                <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-xl border border-yellow-200">
                  <div className="text-3xl font-bold text-yellow-700">{results.statistics.medium || 0}</div>
                  <div className="text-sm font-medium text-yellow-600">Medium</div>
                </div>
                
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl border border-blue-200">
                  <div className="text-3xl font-bold text-blue-700">{results.statistics.low || 0}</div>
                  <div className="text-sm font-medium text-blue-600">Low</div>
                </div>
                
                <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-xl border border-gray-200">
                  <div className="text-3xl font-bold text-gray-700">{results.statistics.info || 0}</div>
                  <div className="text-sm font-medium text-gray-600">Info</div>
                </div>
              </div>
            </div>

            {/* Findings */}
            <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
              <div className="flex items-center gap-3 mb-6">
                <FileText className="w-6 h-6 text-indigo-600" />
                <h3 className="text-2xl font-bold text-gray-900">Detailed Findings</h3>
                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-semibold">
                  {results.findings.length} issues
                </span>
              </div>

              <div className="space-y-4">
                {results.findings.map((finding: any, index: number) => (
                  <div
                    key={index}
                    className={`p-6 rounded-xl border-2 transition-all hover:shadow-md ${getSeverityColor(finding.severity)}`}
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 mt-1">
                        {getSeverityIcon(finding.severity)}
                      </div>
                      
                      <div className="flex-1 space-y-3">
                        <div className="flex items-start justify-between">
                          <h4 className="text-lg font-bold">{finding.title}</h4>
                          <div className="flex items-center gap-2">
                            <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                              {finding.severity}
                            </span>
                            {finding.cvss_score && (
                              <span className="px-2 py-1 bg-white/70 rounded text-xs font-semibold">
                                CVSS: {finding.cvss_score}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <p className="text-sm leading-relaxed">{finding.description}</p>
                          
                          <div className="bg-white/50 rounded-lg p-3 border">
                            <p className="text-xs font-semibold text-red-700 mb-1">Security Implications:</p>
                            <p className="text-xs leading-relaxed">{finding.implications}</p>
                          </div>
                          
                          <div className="bg-white/50 rounded-lg p-3 border">
                            <p className="text-xs font-semibold text-green-700 mb-1">Recommendations:</p>
                            <p className="text-xs leading-relaxed">{finding.recommendations}</p>
                          </div>
                        </div>
                        
                        {finding.evidence && (
                          <div className="bg-white/50 rounded-lg p-3 font-mono text-xs border">
                            <p className="font-semibold mb-1">Evidence:</p>
                            {finding.evidence}
                          </div>
                        )}
                        
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <Target className="w-3 h-3" />
                            {finding.category}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(finding.discovered_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Features */}
        {!results && !scanning && (
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center mb-4 shadow-md">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Intelligent Crawling</h3>
              <p className="text-gray-600 leading-relaxed">
                Nova Pro autonomously navigates and discovers endpoints, subdomains, and hidden paths with AI-powered decision making.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center mb-4 shadow-md">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Security Analysis</h3>
              <p className="text-gray-600 leading-relaxed">
                Automatically detect missing security headers, exposed sensitive files, and common misconfigurations.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center mb-4 shadow-md">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Comprehensive Reports</h3>
              <p className="text-gray-600 leading-relaxed">
                Generate detailed findings with severity ratings, evidence, and actionable recommendations for your bug bounty reports.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-md mt-20">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center">
          <p className="text-sm text-gray-600">
            Built for Amazon Nova Hackathon 2026 | Category: UI Automation
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Powered by Amazon Nova Pro Foundation Model
          </p>
        </div>
      </footer>
    </div>
  );
}
