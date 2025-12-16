'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

interface Issue {
  category: string;
  severity: string;
  message: string;
  recommendation: string;
}

interface AnalysisResult {
  url: string;
  overall_score: number;
  message_match_score: number;
  message_match_level: string;
  above_fold_score: number;
  cta_score: number;
  mobile_score: number;
  load_speed_score: number;
  issues: Issue[];
  recommendations: string[];
  summary: string;
}

export default function LandingPage() {
  const [url, setUrl] = useState('');
  const [headline, setHeadline] = useState('');
  const [primaryText, setPrimaryText] = useState('');
  const [cta, setCta] = useState('Learn More');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/landing/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ landing_page_url: url, ad_headline: headline, ad_primary_text: primaryText, ad_cta: cta }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const runDemo = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/landing/demo', { method: 'POST' });
      const data = await res.json();
      setResult({ ...data, url: 'https://careerfied.ai', issues: [], recommendations: [], above_fold_score: 85, cta_score: 80, mobile_score: 85, load_speed_score: 80, message_match_score: data.score || 75, message_match_level: data.match_level || 'good', overall_score: data.score || 75 });
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const ScoreBar = ({ label, score }: { label: string; score: number }) => (
    <div className="mb-3">
      <div className="flex justify-between mb-1 text-sm">
        <span>{label}</span>
        <span className={score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : 'text-red-400'}>{score}/100</span>
      </div>
      <div className="h-2 bg-gray-700 rounded">
        <div className={`h-2 rounded ${score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <ToolsNav />
      <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">🔍 Landing Page Analyzer</h1>
        <p className="text-gray-400 mb-8">Check ad-to-page message match and conversion optimization</p>

        <div className="space-y-4 mb-6">
          <input type="text" placeholder="Landing Page URL" value={url} onChange={(e) => setUrl(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          <input type="text" placeholder="Ad Headline" value={headline} onChange={(e) => setHeadline(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          <textarea placeholder="Ad Primary Text" value={primaryText} onChange={(e) => setPrimaryText(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" rows={2} />
          <input type="text" placeholder="Ad CTA" value={cta} onChange={(e) => setCta(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={analyze} disabled={loading || !url} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Analyzing...' : 'Analyze Page'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Overall Score</h2>
                <span className={`text-4xl font-bold ${result.overall_score >= 80 ? 'text-green-400' : result.overall_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>{result.overall_score}</span>
              </div>
              <p className="text-gray-400 mb-4">Message Match: <span className={`font-semibold ${result.message_match_level === 'excellent' ? 'text-green-400' : result.message_match_level === 'good' ? 'text-blue-400' : 'text-yellow-400'}`}>{result.message_match_level.toUpperCase()}</span></p>
              <ScoreBar label="Message Match" score={result.message_match_score} />
              <ScoreBar label="Above Fold" score={result.above_fold_score} />
              <ScoreBar label="CTA Clarity" score={result.cta_score} />
              <ScoreBar label="Mobile Experience" score={result.mobile_score} />
              <ScoreBar label="Load Speed" score={result.load_speed_score} />
            </div>

            {result.issues?.length > 0 && (
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h2 className="text-xl font-semibold mb-4">Issues Found</h2>
                {result.issues.map((issue, i) => (
                  <div key={i} className={`p-4 rounded mb-3 ${issue.severity === 'critical' ? 'bg-red-900/30 border border-red-800' : 'bg-yellow-900/30 border border-yellow-800'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 text-xs rounded ${issue.severity === 'critical' ? 'bg-red-600' : 'bg-yellow-600'}`}>{issue.severity}</span>
                      <span className="font-semibold">{issue.category}</span>
                    </div>
                    <p className="text-gray-300 mb-2">{issue.message}</p>
                    <p className="text-gray-500 text-sm">💡 {issue.recommendation}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
