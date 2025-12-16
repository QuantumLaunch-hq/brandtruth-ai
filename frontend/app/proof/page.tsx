'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  Shield, 
  FileCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  FileText,
  Scale,
  Building2,
  ExternalLink,
  ChevronDown,
  ChevronRight
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ClaimDetail {
  claim: string;
  status: string;
  risk_level: string;
  notes: string;
  requires_disclaimer: boolean;
  suggested_disclaimer: string | null;
}

interface RegulatoryCheck {
  regulation: string;
  name: string;
  status: string;
  requirements_met: string[];
  requirements_failed: string[];
  recommendations: string[];
}

interface BrandSafetyCheck {
  category: string;
  status: string;
  details: string;
  risk_factors: string[];
}

interface ProofPackResult {
  pack_id: string;
  generated_at: string;
  summary: string;
  overall_compliance: string;
  risk_summary: string;
  ad_content: {
    headline: string;
    primary_text: string;
    cta: string;
  };
  claims: {
    total: number;
    verified: number;
    high_risk: number;
    details: ClaimDetail[];
  };
  regulatory: {
    status: string;
    checks: RegulatoryCheck[];
  };
  brand_safety: {
    score: number;
    checks: BrandSafetyCheck[];
  };
  action_items: string[];
  approval_history: { action: string; timestamp: string; user: string }[];
}

export default function ProofPage() {
  const [adId, setAdId] = useState('careerfied_001');
  const [campaignName, setCampaignName] = useState('Launch Campaign');
  const [brandName, setBrandName] = useState('Careerfied');
  const [headline, setHeadline] = useState('Stop Getting Rejected by ATS');
  const [primaryText, setPrimaryText] = useState('Build resumes that get interviews with AI-powered optimization. Join 10,000+ job seekers who landed their dream jobs.');
  const [cta, setCta] = useState('Get Started');
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProofPackResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['claims', 'regulatory', 'safety']));

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/proof/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ad_id: adId,
          campaign_name: campaignName,
          brand_name: brandName,
          headline,
          primary_text: primaryText,
          cta,
          claims: [
            { claim: "Join 10,000+ job seekers", source_text: "Based on user surveys", risk_level: "low" },
            { claim: "AI-powered optimization", source_text: "Uses GPT-4", risk_level: "low" },
            { claim: "Guaranteed results", source_text: "", risk_level: "high" },
          ],
        }),
      });

      if (!response.ok) throw new Error('Generation failed');
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/proof/demo`, { method: 'POST' });
      const demoData = await response.json();
      
      // Fetch full proof pack
      const fullResponse = await fetch(`${API_BASE}/proof/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ad_id: "demo_careerfied_001",
          campaign_name: "Careerfied Launch Campaign",
          brand_name: "Careerfied",
          headline: "Stop Getting Rejected by ATS",
          primary_text: "Your dream job slips away because your resume can't pass automated screening. Build resumes that get interviews with AI-powered optimization. Join 10,000+ job seekers who landed their dream jobs.",
          cta: "Get Started",
          claims: [
            { claim: "Join 10,000+ job seekers who landed their dream jobs", source_text: "Based on user surveys from 2024", risk_level: "low" },
            { claim: "AI-powered resume optimization", source_text: "Uses GPT-4 for analysis", risk_level: "low" },
            { claim: "Guaranteed to pass ATS screening", source_text: "", risk_level: "high" },
          ],
        }),
      });
      const data = await fullResponse.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    if (status === 'pass') return <CheckCircle className="w-5 h-5 text-green-400" />;
    if (status === 'warning') return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
    if (status === 'fail') return <XCircle className="w-5 h-5 text-red-400" />;
    return <AlertCircle className="w-5 h-5 text-blue-400" />;
  };

  const getStatusBg = (status: string) => {
    if (status === 'pass') return 'bg-green-500/20 border-green-500/30 text-green-400';
    if (status === 'warning') return 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400';
    if (status === 'fail') return 'bg-red-500/20 border-red-500/30 text-red-400';
    return 'bg-blue-500/20 border-blue-500/30 text-blue-400';
  };

  const getRiskColor = (risk: string) => {
    if (risk === 'low') return 'text-green-400';
    if (risk === 'medium') return 'text-yellow-400';
    if (risk === 'high') return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-white">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              Proof Pack Generator
            </h1>
            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
              Slice 15
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Ad Details */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Ad Details</h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Ad ID</label>
                    <input
                      type="text"
                      value={adId}
                      onChange={(e) => setAdId(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Campaign Name</label>
                    <input
                      type="text"
                      value={campaignName}
                      onChange={(e) => setCampaignName(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Brand Name</label>
                  <input
                    type="text"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Headline</label>
                  <input
                    type="text"
                    value={headline}
                    onChange={(e) => setHeadline(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Primary Text</label>
                  <textarea
                    value={primaryText}
                    onChange={(e) => setPrimaryText(e.target.value)}
                    rows={3}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">CTA</label>
                  <input
                    type="text"
                    value={cta}
                    onChange={(e) => setCta(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleDemo}
                disabled={loading}
                className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium disabled:opacity-50 transition"
              >
                Run Demo
              </button>
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-400 hover:to-indigo-400 rounded-lg font-medium disabled:opacity-50 transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileCheck className="w-5 h-5" />
                    Generate Proof Pack
                  </>
                )}
              </button>
            </div>

            {/* Info Box */}
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
              <h3 className="font-medium text-blue-400 mb-2">What's in a Proof Pack?</h3>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• <strong>Claim Verification:</strong> Source attribution for all claims</li>
                <li>• <strong>Regulatory Checks:</strong> FTC, Meta Policy compliance</li>
                <li>• <strong>Brand Safety:</strong> Content appropriateness score</li>
                <li>• <strong>Action Items:</strong> Required fixes before publishing</li>
                <li>• <strong>Approval Trail:</strong> Audit-ready documentation</li>
              </ul>
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            {/* Error */}
            {error && (
              <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <p>{error}</p>
                </div>
              </div>
            )}

            {/* Placeholder */}
            {!result && !loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Shield className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-400 mb-2">No proof pack yet</h3>
                <p className="text-gray-500">Generate a compliance proof pack for your ad</p>
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-12 text-center">
                <Loader2 className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">Generating proof pack...</h3>
                <p className="text-gray-500">Running compliance checks</p>
              </div>
            )}

            {/* Results */}
            {result && !loading && (
              <>
                {/* Overall Status */}
                <div className={`border rounded-lg p-6 ${getStatusBg(result.overall_compliance)}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(result.overall_compliance)}
                      <div>
                        <div className="font-semibold uppercase">{result.overall_compliance}</div>
                        <div className="text-sm opacity-80">{result.risk_summary}</div>
                      </div>
                    </div>
                    <div className="text-right text-sm opacity-80">
                      <div>Pack ID: {result.pack_id.slice(0, 20)}...</div>
                      <div>{new Date(result.generated_at).toLocaleString()}</div>
                    </div>
                  </div>
                </div>

                {/* Claims Section */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg">
                  <button
                    onClick={() => toggleSection('claims')}
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-purple-400" />
                      <span className="font-semibold">Claims Verification</span>
                      <span className="text-sm text-gray-400">
                        ({result.claims.verified}/{result.claims.total} verified, {result.claims.high_risk} high-risk)
                      </span>
                    </div>
                    {expandedSections.has('claims') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </button>
                  
                  {expandedSections.has('claims') && (
                    <div className="border-t border-gray-800 p-4 space-y-3">
                      {result.claims.details.map((claim, i) => (
                        <div key={i} className="bg-gray-800 rounded-lg p-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                {getStatusIcon(claim.status)}
                                <span className={`text-sm font-medium ${getRiskColor(claim.risk_level)}`}>
                                  {claim.risk_level.toUpperCase()} RISK
                                </span>
                              </div>
                              <p className="text-sm text-gray-300">{claim.claim}</p>
                              <p className="text-xs text-gray-500 mt-1">{claim.notes}</p>
                              {claim.suggested_disclaimer && (
                                <p className="text-xs text-yellow-400 mt-2">
                                  ⚠️ Suggested: "{claim.suggested_disclaimer}"
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Regulatory Section */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg">
                  <button
                    onClick={() => toggleSection('regulatory')}
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <Scale className="w-5 h-5 text-yellow-400" />
                      <span className="font-semibold">Regulatory Compliance</span>
                      <span className={`text-sm px-2 py-0.5 rounded ${getStatusBg(result.regulatory.status)}`}>
                        {result.regulatory.status.toUpperCase()}
                      </span>
                    </div>
                    {expandedSections.has('regulatory') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </button>
                  
                  {expandedSections.has('regulatory') && (
                    <div className="border-t border-gray-800 p-4 space-y-3">
                      {result.regulatory.checks.map((check, i) => (
                        <div key={i} className="bg-gray-800 rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2">
                            {getStatusIcon(check.status)}
                            <span className="font-medium">{check.name}</span>
                          </div>
                          {check.requirements_met.length > 0 && (
                            <div className="mb-2">
                              {check.requirements_met.map((req, j) => (
                                <div key={j} className="text-xs text-green-400 flex items-center gap-1">
                                  <CheckCircle className="w-3 h-3" /> {req}
                                </div>
                              ))}
                            </div>
                          )}
                          {check.requirements_failed.length > 0 && (
                            <div className="mb-2">
                              {check.requirements_failed.map((req, j) => (
                                <div key={j} className="text-xs text-red-400 flex items-center gap-1">
                                  <XCircle className="w-3 h-3" /> {req}
                                </div>
                              ))}
                            </div>
                          )}
                          {check.recommendations.length > 0 && (
                            <div className="text-xs text-gray-400 mt-2">
                              💡 {check.recommendations.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Brand Safety Section */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg">
                  <button
                    onClick={() => toggleSection('safety')}
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <Building2 className="w-5 h-5 text-green-400" />
                      <span className="font-semibold">Brand Safety</span>
                      <span className="text-sm text-gray-400">Score: {result.brand_safety.score}/100</span>
                    </div>
                    {expandedSections.has('safety') ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </button>
                  
                  {expandedSections.has('safety') && (
                    <div className="border-t border-gray-800 p-4 space-y-2">
                      {result.brand_safety.checks.map((check, i) => (
                        <div key={i} className="flex items-center justify-between py-2">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(check.status)}
                            <span>{check.category}</span>
                          </div>
                          <span className="text-sm text-gray-400">{check.details}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action Items */}
                {result.action_items.length > 0 && (
                  <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
                    <h3 className="font-semibold text-yellow-400 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Action Items ({result.action_items.length})
                    </h3>
                    <ul className="space-y-2">
                      {result.action_items.map((item, i) => (
                        <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                          <span className="text-yellow-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Export Button */}
                <a
                  href={`${API_BASE}/proof/html/${result.pack_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 bg-blue-500 hover:bg-blue-400 text-white font-medium rounded-lg transition"
                >
                  <ExternalLink className="w-5 h-5" />
                  View HTML Report
                </a>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
