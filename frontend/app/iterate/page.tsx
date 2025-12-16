'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

interface Diagnosis {
  issue: string;
  severity: string;
  description: string;
  likely_cause: string;
  impact: string;
}

interface Improvement {
  element: string;
  original: string;
  improved: string;
  rationale: string;
  expected_improvement: string;
}

interface Result {
  diagnoses: Diagnosis[];
  improved_variants: Improvement[];
  priority_fixes: string[];
  testing_roadmap: string[];
  quick_wins: string[];
  estimated_improvement: string;
  summary: string;
}

export default function IteratePage() {
  const [headline, setHeadline] = useState('');
  const [primaryText, setPrimaryText] = useState('');
  const [cta, setCta] = useState('Learn More');
  const [currentCtr, setCurrentCtr] = useState(0.8);
  const [currentCvr, setCurrentCvr] = useState(1.5);
  const [currentCpa, setCurrentCpa] = useState(80);
  const [targetCpa, setTargetCpa] = useState(50);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/iterate/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ headline, primary_text: primaryText, cta, current_ctr: currentCtr, current_cvr: currentCvr, current_cpa: currentCpa, target_cpa: targetCpa, impressions: 10000, frequency: 2.0, days_running: 7 }),
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
      const res = await fetch('http://localhost:8000/iterate/demo', { method: 'POST' });
      const data = await res.json();
      setResult({
        ...data,
        diagnoses: [
          { issue: 'low_ctr', severity: 'critical', description: 'CTR of 0.5% is below average', likely_cause: 'Weak headline', impact: 'Wasted impressions' },
          { issue: 'high_cpa', severity: 'warning', description: 'CPA of $120 is above target', likely_cause: 'Low conversion rate', impact: 'Unprofitable' },
        ],
        improved_variants: [
          { element: 'headline', original: 'Check out our product', improved: '🔥 Stop. Check out our product', rationale: 'Added urgency', expected_improvement: '+20-40% CTR' },
          { element: 'cta', original: 'Learn More', improved: 'See How It Works', rationale: 'More action-oriented', expected_improvement: '+10-20%' },
        ],
        priority_fixes: ['1. Fix CTR first - test new headlines', '2. Check landing page message match'],
        testing_roadmap: ['Week 1: Headline A/B test', 'Week 2: Primary text test', 'Week 3: CTA test', 'Week 4: Scale winners'],
        quick_wins: ['Add a question to headline', 'Use specific CTA'],
        estimated_improvement: 'Potential 40-60% improvement in CPA',
      });
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <ToolsNav />
      <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">🔄 Ad Iteration Assistant</h1>
        <p className="text-gray-400 mb-8">Diagnose underperforming ads and get improvement suggestions</p>

        <div className="space-y-4 mb-6">
          <input type="text" placeholder="Current Headline" value={headline} onChange={(e) => setHeadline(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          <textarea placeholder="Current Primary Text" value={primaryText} onChange={(e) => setPrimaryText(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" rows={2} />
          <input type="text" placeholder="Current CTA" value={cta} onChange={(e) => setCta(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Current CTR (%)</label>
            <input type="number" step="0.1" value={currentCtr} onChange={(e) => setCurrentCtr(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Current CVR (%)</label>
            <input type="number" step="0.1" value={currentCvr} onChange={(e) => setCurrentCvr(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Current CPA ($)</label>
            <input type="number" value={currentCpa} onChange={(e) => setCurrentCpa(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Target CPA ($)</label>
            <input type="number" value={targetCpa} onChange={(e) => setTargetCpa(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={analyze} disabled={loading || !headline} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Analyzing...' : 'Diagnose & Improve'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {result && (
          <div className="space-y-6">
            {result.estimated_improvement && (
              <div className="p-4 bg-green-900/30 rounded border border-green-700">
                <p className="text-green-400 font-semibold">{result.estimated_improvement}</p>
              </div>
            )}

            {result.diagnoses?.length > 0 && (
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Issues Diagnosed</h3>
                {result.diagnoses.map((diag, i) => (
                  <div key={i} className={`p-4 rounded mb-3 ${diag.severity === 'critical' ? 'bg-red-900/30 border border-red-800' : 'bg-yellow-900/30 border border-yellow-800'}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 text-xs rounded font-bold ${diag.severity === 'critical' ? 'bg-red-600' : 'bg-yellow-600'}`}>{diag.severity.toUpperCase()}</span>
                      <span className="font-semibold">{diag.issue.replace('_', ' ').toUpperCase()}</span>
                    </div>
                    <p className="text-gray-300 mb-2">{diag.description}</p>
                    <p className="text-gray-500 text-sm">Cause: {diag.likely_cause}</p>
                  </div>
                ))}
              </div>
            )}

            {result.improved_variants?.length > 0 && (
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Suggested Improvements</h3>
                {result.improved_variants.map((imp, i) => (
                  <div key={i} className="p-4 bg-gray-700/50 rounded mb-3">
                    <p className="font-semibold capitalize mb-3">{imp.element}</p>
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div className="p-3 bg-red-900/20 rounded border border-red-800/50">
                        <p className="text-xs text-gray-400 mb-1">Original</p>
                        <p className="text-red-300">{imp.original}</p>
                      </div>
                      <div className="p-3 bg-green-900/20 rounded border border-green-800/50">
                        <p className="text-xs text-gray-400 mb-1">Improved</p>
                        <p className="text-green-300">{imp.improved}</p>
                      </div>
                    </div>
                    <p className="text-gray-400 text-sm">{imp.rationale}</p>
                    <p className="text-green-400 text-sm mt-1">Expected: {imp.expected_improvement}</p>
                  </div>
                ))}
              </div>
            )}

            <div className="grid grid-cols-2 gap-6">
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Priority Fixes</h3>
                <ol className="space-y-2">
                  {result.priority_fixes?.map((fix, i) => (
                    <li key={i} className="text-gray-300">{fix}</li>
                  ))}
                </ol>
              </div>
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Quick Wins</h3>
                <ul className="space-y-2">
                  {result.quick_wins?.map((win, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-yellow-400">⚡</span>
                      <span className="text-gray-300">{win}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
