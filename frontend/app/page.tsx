'use client'

import { useState, useEffect } from 'react'
import { Shield, Search, Zap, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

interface Finding {
  title: string
  severity: string
  category: string
  description: string
  evidence?: string
}

interface ScanStatus {
  scan_id: string
  status: string
  progress: number
  findings: number
  started_at: string
}

interface ScanResult {
  scan_id: string
  target: string
  findings: Finding[]
  statistics: {
    total_findings: number
    critical: number
    high: number
    medium: number
    low: number
    info: number
  }
  completed_at: string
}

export default function Home() {
  const [targetUrl, setTargetUrl] = useState('')
  const [scanning, setScanning] = useState(false)
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null)
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const startScan = async () => {
    if (!targetUrl) {
      setError('Please enter a target URL')
      return
    }

    try {
      setError(null)
      setScanning(true)
      setScanResult(null)

      const response = await fetch(`${API_URL}/scans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_url: targetUrl,
          scan_type: 'quick',
          include_subdomains: true,
          include_screenshots: true,
          max_depth: 3
        })
      })

      const data: ScanStatus = await response.json()
      setScanStatus(data)

      // Poll for status updates
      pollScanStatus(data.scan_id)
    } catch (err) {
      setError('Failed to start scan. Make sure the backend is running.')
      setScanning(false)
    }
  }

  const pollScanStatus = async (scanId: string) => {
    const interval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`${API_URL}/scans/${scanId}/status`)
        const status: ScanStatus = await statusResponse.json()
        setScanStatus(status)

        if (status.status === 'completed') {
          clearInterval(interval)
          
          // Fetch final results
          const resultsResponse = await fetch(`${API_URL}/scans/${scanId}/results`)
          const results: ScanResult = await resultsResponse.json()
          setScanResult(results)
          setScanning(false)
        } else if (status.status === 'failed') {
          clearInterval(interval)
          setError('Scan failed')
          setScanning(false)
        }
      } catch (err) {
        clearInterval(interval)
        setError('Failed to fetch scan status')
        setScanning(false)
      }
    }, 2000)
  }

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'text-red-600 bg-red-50 border-red-200',
      high: 'text-orange-600 bg-orange-50 border-orange-200',
      medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      low: 'text-blue-600 bg-blue-50 border-blue-200',
      info: 'text-gray-600 bg-gray-50 border-gray-200'
    }
    return colors[severity] || colors.info
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-indigo-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Bounty Recon AI</h1>
              <p className="text-sm text-gray-600">Powered by Amazon Nova Act</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 rounded-full text-indigo-700 text-sm font-medium mb-4">
            <Zap className="w-4 h-4" />
            Amazon Nova Hackathon 2026
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            AI-Powered Bug Bounty Reconnaissance
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Automate the tedious initial phases of security research with intelligent recon powered by Nova Act
          </p>
        </div>

        {/* Scan Input */}
        <div className="max-w-2xl mx-auto mb-12">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target URL
            </label>
            <div className="flex gap-3">
              <input
                type="url"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://example.com"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                disabled={scanning}
              />
              <button
                onClick={startScan}
                disabled={scanning}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {scanning ? (
                  <>
                    <Clock className="w-5 h-5 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Start Scan
                  </>
                )}
              </button>
            </div>
            {error && (
              <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" />
                {error}
              </p>
            )}
          </div>
        </div>

        {/* Scan Progress */}
        {scanStatus && scanning && (
          <div className="max-w-2xl mx-auto mb-12">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h3 className="text-lg font-semibold mb-4">Scan Progress</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Status: {scanStatus.status}</span>
                  <span>{scanStatus.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${scanStatus.progress}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600">
                  Found {scanStatus.findings} findings so far...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Scan Results */}
        {scanResult && (
          <div className="space-y-6">
            {/* Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { label: 'Total', value: scanResult.statistics.total_findings, color: 'indigo' },
                { label: 'Critical', value: scanResult.statistics.critical, color: 'red' },
                { label: 'High', value: scanResult.statistics.high, color: 'orange' },
                { label: 'Medium', value: scanResult.statistics.medium, color: 'yellow' },
                { label: 'Low', value: scanResult.statistics.low, color: 'blue' },
              ].map((stat) => (
                <div key={stat.label} className="bg-white rounded-lg shadow p-6 text-center">
                  <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                  <p className="text-sm text-gray-600 mt-1">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Findings */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <CheckCircle className="w-6 h-6 text-green-600" />
                Scan Complete - {scanResult.findings.length} Findings
              </h3>
              <div className="space-y-4">
                {scanResult.findings.map((finding, index) => (
                  <div
                    key={index}
                    className={`p-4 border rounded-lg ${getSeverityColor(finding.severity)}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold">{finding.title}</h4>
                      <span className="text-xs font-medium uppercase px-2 py-1 rounded">
                        {finding.severity}
                      </span>
                    </div>
                    <p className="text-sm mb-2">{finding.description}</p>
                    {finding.evidence && (
                      <pre className="text-xs bg-black/5 p-2 rounded mt-2 overflow-x-auto">
                        {finding.evidence}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-gray-600">
          <p>Built for Amazon Nova Hackathon 2026 • #AmazonNova</p>
          <p className="mt-1">Category: UI Automation</p>
        </footer>
      </main>
    </div>
  )
}
