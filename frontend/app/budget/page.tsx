'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SimulationResult {
  daily_budget: number;
  monthly_budget: number;
  tier: string;
  expected_impressions: number;
  expected_clicks: number;
  expected_conversions: number;
  expected_cpa: number;
  expected_roas: number;
  break_even_days: number;
  confidence_level: string;
  recommendations: string[];
  summary: string;
}

export default function BudgetPage() {
  const [industry, setIndustry] = useState('saas');
  const [goal, setGoal] = useState('leads');
  const [productPrice, setProductPrice] = useState(99);
  const [targetConversions, setTargetConversions] = useState(50);
  const [targetCpa, setTargetCpa] = useState<number | ''>('');
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const simulate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/budget/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          industry,
          goal,
          product_price: productPrice,
          target_monthly_conversions: targetConversions,
          target_cpa: targetCpa || null,
        }),
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
      const res = await fetch(`${API_BASE}/budget/demo`, { method: 'POST' });
      const data = await res.json();
      setResult({ ...data, tier: 'growth', expected_impressions: 50000, expected_clicks: 500, expected_conversions: 12, expected_roas: 1.5, break_even_days: 21, confidence_level: 'Medium', recommendations: ['Start with 1-2 ad sets'], monthly_budget: data.daily_budget * 30 });
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const industries = [
    { id: 'saas', label: 'SaaS' },
    { id: 'ecommerce', label: 'E-commerce' },
    { id: 'fintech', label: 'Fintech' },
    { id: 'healthcare', label: 'Healthcare' },
    { id: 'education', label: 'Education' },
    { id: 'consumer_app', label: 'Consumer App' },
  ];

  const goals = [
    { id: 'awareness', label: 'Brand Awareness' },
    { id: 'traffic', label: 'Website Traffic' },
    { id: 'leads', label: 'Lead Generation' },
    { id: 'sales', label: 'Sales' },
    { id: 'app_installs', label: 'App Installs' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <ToolsNav />
      <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">💰 Budget Simulator</h1>
        <p className="text-gray-400 mb-8">Predict ad performance and calculate optimal budget</p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Industry</label>
            <select value={industry} onChange={(e) => setIndustry(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none">
              {industries.map(i => <option key={i.id} value={i.id}>{i.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Campaign Goal</label>
            <select value={goal} onChange={(e) => setGoal(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none">
              {goals.map(g => <option key={g.id} value={g.id}>{g.label}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Product Price ($)</label>
            <input type="number" value={productPrice} onChange={(e) => setProductPrice(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Target Monthly Conversions</label>
            <input type="number" value={targetConversions} onChange={(e) => setTargetConversions(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Target CPA ($, optional)</label>
            <input type="number" value={targetCpa} onChange={(e) => setTargetCpa(e.target.value ? Number(e.target.value) : '')} placeholder="Auto" className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          </div>
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={simulate} disabled={loading} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Simulating...' : 'Simulate Budget'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-gray-400 text-sm mb-2">Recommended Daily Budget</h3>
                <p className="text-4xl font-bold text-green-400">${result.daily_budget}</p>
                <p className="text-gray-500 mt-1">${result.monthly_budget?.toFixed(0)}/month</p>
              </div>
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-gray-400 text-sm mb-2">Budget Tier</h3>
                <p className="text-4xl font-bold text-blue-400 capitalize">{result.tier}</p>
                <p className="text-gray-500 mt-1">{result.confidence_level}</p>
              </div>
            </div>

            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Expected Performance</h3>
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-700/50 rounded">
                  <p className="text-2xl font-bold">{result.expected_impressions?.toLocaleString()}</p>
                  <p className="text-gray-400 text-sm">Impressions</p>
                </div>
                <div className="text-center p-4 bg-gray-700/50 rounded">
                  <p className="text-2xl font-bold">{result.expected_clicks?.toLocaleString()}</p>
                  <p className="text-gray-400 text-sm">Clicks</p>
                </div>
                <div className="text-center p-4 bg-gray-700/50 rounded">
                  <p className="text-2xl font-bold">{result.expected_conversions}</p>
                  <p className="text-gray-400 text-sm">Conversions</p>
                </div>
                <div className="text-center p-4 bg-gray-700/50 rounded">
                  <p className="text-2xl font-bold">${result.expected_cpa}</p>
                  <p className="text-gray-400 text-sm">Est. CPA</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-gray-400 text-sm mb-2">Expected ROAS</h3>
                <p className={`text-3xl font-bold ${result.expected_roas >= 2 ? 'text-green-400' : result.expected_roas >= 1 ? 'text-yellow-400' : 'text-red-400'}`}>{result.expected_roas}x</p>
              </div>
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-gray-400 text-sm mb-2">Break-even</h3>
                <p className="text-3xl font-bold text-blue-400">{result.break_even_days} days</p>
              </div>
            </div>

            {result.recommendations?.length > 0 && (
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Recommendations</h3>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-green-400">💡</span>
                      <span className="text-gray-300">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
