'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

interface TestPair {
  element: string;
  variant_a: string;
  variant_b: string;
  hypothesis: string;
  priority: string;
  expected_lift: string;
}

interface Result {
  test_pairs: TestPair[];
  required_sample_size: number;
  estimated_days: number;
  daily_budget_needed: number;
  testing_sequence: string[];
  recommendations: string[];
  summary: string;
}

export default function ABTestPage() {
  const [headlineA, setHeadlineA] = useState('');
  const [headlineB, setHeadlineB] = useState('');
  const [textA, setTextA] = useState('');
  const [textB, setTextB] = useState('');
  const [ctaA, setCtaA] = useState('Get Started');
  const [ctaB, setCtaB] = useState('Try Free');
  const [dailyBudget, setDailyBudget] = useState(50);
  const [baselineCtr, setBaselineCtr] = useState(1.0);
  const [baselineCvr, setBaselineCvr] = useState(2.0);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);

  const planTest = async () => {
    setLoading(true);
    try {
      const variants = [
        { headline: headlineA, primary_text: textA, cta: ctaA },
        { headline: headlineB, primary_text: textB, cta: ctaB },
      ];
      const res = await fetch('http://localhost:8000/abtest/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variants, baseline_ctr: baselineCtr, baseline_cvr: baselineCvr, daily_budget: dailyBudget, confidence_level: 0.95, minimum_lift: 0.20 }),
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
      const res = await fetch('http://localhost:8000/abtest/demo', { method: 'POST' });
      const data = await res.json();
      setResult({
        ...data,
        required_sample_size: 1500,
        daily_budget_needed: 50,
        test_pairs: [
          { element: 'headline', variant_a: 'Stop Getting Rejected', variant_b: 'Land More Interviews', hypothesis: 'Different headlines impact CTR', priority: 'high', expected_lift: '10-30%' },
          { element: 'cta', variant_a: 'Get Started', variant_b: 'Try Free', hypothesis: 'CTA wording impacts clicks', priority: 'medium', expected_lift: '5-20%' },
        ],
        testing_sequence: ['1. Test headlines first', '2. Winner + new primary text', '3. Winner + CTA variations', '4. Scale winning combo'],
        recommendations: ['Run tests for minimum 7 days', 'Don\'t stop early'],
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
        <h1 className="text-3xl font-bold mb-2">🧪 A/B Test Planner</h1>
        <p className="text-gray-400 mb-8">Plan statistically valid ad tests</p>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="p-4 bg-gray-800 rounded border border-gray-700">
            <h3 className="font-semibold mb-3 text-blue-400">Variant A (Control)</h3>
            <input type="text" placeholder="Headline A" value={headlineA} onChange={(e) => setHeadlineA(e.target.value)} className="w-full p-2 mb-2 bg-gray-700 rounded border border-gray-600 outline-none" />
            <textarea placeholder="Primary Text A" value={textA} onChange={(e) => setTextA(e.target.value)} className="w-full p-2 mb-2 bg-gray-700 rounded border border-gray-600 outline-none" rows={2} />
            <input type="text" placeholder="CTA A" value={ctaA} onChange={(e) => setCtaA(e.target.value)} className="w-full p-2 bg-gray-700 rounded border border-gray-600 outline-none" />
          </div>
          <div className="p-4 bg-gray-800 rounded border border-gray-700">
            <h3 className="font-semibold mb-3 text-green-400">Variant B (Test)</h3>
            <input type="text" placeholder="Headline B" value={headlineB} onChange={(e) => setHeadlineB(e.target.value)} className="w-full p-2 mb-2 bg-gray-700 rounded border border-gray-600 outline-none" />
            <textarea placeholder="Primary Text B" value={textB} onChange={(e) => setTextB(e.target.value)} className="w-full p-2 mb-2 bg-gray-700 rounded border border-gray-600 outline-none" rows={2} />
            <input type="text" placeholder="CTA B" value={ctaB} onChange={(e) => setCtaB(e.target.value)} className="w-full p-2 bg-gray-700 rounded border border-gray-600 outline-none" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Daily Budget ($)</label>
            <input type="number" value={dailyBudget} onChange={(e) => setDailyBudget(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Baseline CTR (%)</label>
            <input type="number" step="0.1" value={baselineCtr} onChange={(e) => setBaselineCtr(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Baseline CVR (%)</label>
            <input type="number" step="0.1" value={baselineCvr} onChange={(e) => setBaselineCvr(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={planTest} disabled={loading || (!headlineA && !headlineB)} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Planning...' : 'Plan Test'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-gray-800 rounded border border-gray-700 text-center">
                <p className="text-3xl font-bold text-blue-400">{result.estimated_days}</p>
                <p className="text-gray-400 text-sm">Days Needed</p>
              </div>
              <div className="p-4 bg-gray-800 rounded border border-gray-700 text-center">
                <p className="text-3xl font-bold text-green-400">{result.required_sample_size?.toLocaleString()}</p>
                <p className="text-gray-400 text-sm">Sample Size/Variant</p>
              </div>
              <div className="p-4 bg-gray-800 rounded border border-gray-700 text-center">
                <p className="text-3xl font-bold text-yellow-400">${result.daily_budget_needed}</p>
                <p className="text-gray-400 text-sm">Daily Budget</p>
              </div>
            </div>

            {result.test_pairs?.length > 0 && (
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Test Pairs</h3>
                {result.test_pairs.map((pair, i) => (
                  <div key={i} className="p-4 bg-gray-700/50 rounded mb-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold capitalize">{pair.element}</span>
                      <span className={`px-2 py-1 text-xs rounded ${pair.priority === 'high' ? 'bg-red-600' : 'bg-yellow-600'}`}>{pair.priority}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                      <div><span className="text-gray-400">A:</span> {pair.variant_a}</div>
                      <div><span className="text-gray-400">B:</span> {pair.variant_b}</div>
                    </div>
                    <p className="text-gray-400 text-sm">Expected lift: <span className="text-green-400">{pair.expected_lift}</span></p>
                  </div>
                ))}
              </div>
            )}

            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Testing Sequence</h3>
              <ol className="space-y-2">
                {result.testing_sequence?.map((step, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-sm">{i + 1}</span>
                    <span>{step.replace(/^\d+\.\s*/, '')}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
