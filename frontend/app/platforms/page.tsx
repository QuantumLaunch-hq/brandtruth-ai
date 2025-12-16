'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

interface PlatformRec {
  platform: string;
  score: number;
  rank: number;
  min_budget: number;
  cpa_range: string;
  strengths: string[];
  best_formats: string[];
}

interface Result {
  primary_platform: string;
  strategy: string;
  budget_allocation: Record<string, number>;
  recommendations: PlatformRec[];
  summary: string;
}

export default function PlatformsPage() {
  const [productType, setProductType] = useState('b2b_saas');
  const [audienceType, setAudienceType] = useState('founders');
  const [monthlyBudget, setMonthlyBudget] = useState(1000);
  const [productPrice, setProductPrice] = useState(99);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);

  const recommend = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/platforms/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_type: productType, audience_type: audienceType, monthly_budget: monthlyBudget, product_price: productPrice, is_visual: true }),
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
      const res = await fetch('http://localhost:8000/platforms/demo', { method: 'POST' });
      const data = await res.json();
      setResult({ ...data, budget_allocation: { meta: 60, linkedin: 25, google: 15 }, recommendations: [
        { platform: 'meta', score: 85, rank: 1, min_budget: 300, cpa_range: '$20-100', strengths: ['Massive reach', 'Visual formats'], best_formats: ['Feed ads', 'Reels'] },
        { platform: 'linkedin', score: 75, rank: 2, min_budget: 1000, cpa_range: '$100-300', strengths: ['B2B targeting', 'Professional context'], best_formats: ['Sponsored content'] },
        { platform: 'google', score: 70, rank: 3, min_budget: 500, cpa_range: '$50-200', strengths: ['High intent', 'Search capture'], best_formats: ['Search ads'] },
      ]});
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const productTypes = [
    { id: 'b2b_saas', label: 'B2B SaaS' },
    { id: 'b2c_saas', label: 'B2C SaaS' },
    { id: 'ecommerce', label: 'E-commerce' },
    { id: 'mobile_app', label: 'Mobile App' },
    { id: 'course', label: 'Course/Info Product' },
    { id: 'agency', label: 'Agency/Services' },
  ];

  const audienceTypes = [
    { id: 'developers', label: 'Developers' },
    { id: 'marketers', label: 'Marketers' },
    { id: 'founders', label: 'Founders/Entrepreneurs' },
    { id: 'enterprise', label: 'Enterprise Buyers' },
    { id: 'consumers', label: 'Consumers' },
    { id: 'creators', label: 'Creators' },
  ];

  const platformColors: Record<string, string> = {
    meta: 'bg-blue-600',
    google: 'bg-red-500',
    linkedin: 'bg-blue-700',
    tiktok: 'bg-pink-600',
    twitter: 'bg-sky-500',
    reddit: 'bg-orange-500',
    youtube: 'bg-red-600',
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <ToolsNav />
      <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">📱 Platform Recommender</h1>
        <p className="text-gray-400 mb-8">Find the best ad platforms for your product</p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Product Type</label>
            <select value={productType} onChange={(e) => setProductType(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none">
              {productTypes.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Target Audience</label>
            <select value={audienceType} onChange={(e) => setAudienceType(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none">
              {audienceTypes.map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Monthly Budget ($)</label>
            <input type="number" value={monthlyBudget} onChange={(e) => setMonthlyBudget(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Product Price ($)</label>
            <input type="number" value={productPrice} onChange={(e) => setProductPrice(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          </div>
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={recommend} disabled={loading} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Analyzing...' : 'Get Recommendations'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-xl font-bold ${platformColors[result.primary_platform] || 'bg-gray-600'}`}>
                  {result.primary_platform?.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm text-gray-400">Primary Platform</p>
                  <p className="text-2xl font-bold uppercase">{result.primary_platform}</p>
                </div>
              </div>
              <p className="text-gray-300">{result.strategy}</p>
            </div>

            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Budget Allocation</h3>
              <div className="space-y-3">
                {Object.entries(result.budget_allocation || {}).map(([platform, pct]) => (
                  <div key={platform}>
                    <div className="flex justify-between mb-1">
                      <span className="uppercase font-medium">{platform}</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="h-3 bg-gray-700 rounded">
                      <div className={`h-3 rounded ${platformColors[platform] || 'bg-gray-500'}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold">Platform Rankings</h3>
              {result.recommendations?.map((rec, i) => (
                <div key={i} className="p-4 bg-gray-800 rounded border border-gray-700">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${i === 0 ? 'bg-yellow-500' : i === 1 ? 'bg-gray-400' : 'bg-amber-700'}`}>#{rec.rank}</span>
                      <span className="text-lg font-semibold uppercase">{rec.platform}</span>
                    </div>
                    <span className={`text-2xl font-bold ${rec.score >= 80 ? 'text-green-400' : rec.score >= 60 ? 'text-yellow-400' : 'text-gray-400'}`}>{rec.score}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400 mb-1">Min Budget</p>
                      <p>${rec.min_budget}/mo</p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Expected CPA</p>
                      <p>{rec.cpa_range}</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <p className="text-gray-400 text-sm mb-1">Strengths</p>
                    <div className="flex flex-wrap gap-2">
                      {rec.strengths?.slice(0, 3).map((s, j) => <span key={j} className="px-2 py-1 bg-gray-700 rounded text-sm">{s}</span>)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
