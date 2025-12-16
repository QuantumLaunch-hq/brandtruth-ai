'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

interface Audience {
  name: string;
  type: string;
  estimated_size: string;
  relevance_score: number;
  targeting_tips?: string[];
}

interface Exclusion {
  name: string;
  reason: string;
  impact: string;
}

interface Result {
  primary_audiences: Audience[];
  secondary_audiences: Audience[];
  exclusions: Exclusion[];
  lookalike_strategy: string;
  budget_allocation: Record<string, number>;
  testing_order: string[];
  recommendations: string[];
  summary: string;
}

export default function AudiencePage() {
  const [productName, setProductName] = useState('');
  const [productDescription, setProductDescription] = useState('');
  const [targetPersona, setTargetPersona] = useState('');
  const [pricePoint, setPricePoint] = useState(99);
  const [hasCustomers, setHasCustomers] = useState(false);
  const [hasTraffic, setHasTraffic] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);

  const suggestAudiences = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/audience/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: productName,
          product_description: productDescription,
          product_type: 'saas',
          target_persona: targetPersona,
          price_point: pricePoint,
          existing_customers: hasCustomers,
          website_traffic: hasTraffic,
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
      const res = await fetch('http://localhost:8000/audience/demo', { method: 'POST' });
      const data = await res.json();
      setResult({
        ...data,
        primary_audiences: [
          { name: 'Job seekers', type: 'interest', estimated_size: '100-200M', relevance_score: 95, targeting_tips: ['Combine with behavior targeting'] },
          { name: 'Career development', type: 'interest', estimated_size: '50-100M', relevance_score: 90, targeting_tips: ['Layer with education level'] },
          { name: 'Resume writing', type: 'interest', estimated_size: '10-30M', relevance_score: 92, targeting_tips: ['High intent audience'] },
        ],
        secondary_audiences: [
          { name: 'LinkedIn users', type: 'interest', estimated_size: '200M+', relevance_score: 75 },
          { name: 'Recent graduates', type: 'interest', estimated_size: '30-60M', relevance_score: 80 },
        ],
        exclusions: [
          { name: 'Existing customers', reason: 'Already converted', impact: 'Saves 5-15% budget' },
          { name: 'Competitors employees', reason: 'Unlikely to convert', impact: 'Cleaner data' },
        ],
        lookalike_strategy: 'No seed audience yet. Focus on interest targeting first.',
        budget_allocation: { 'Primary Interests': 70, 'Testing': 30 },
        testing_order: ['1. Retargeting', '2. Lookalike 1%', '3. Top interests', '4. Stacked interests'],
        recommendations: ['Upload customer list for lookalikes', 'Install Meta Pixel'],
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
        <h1 className="text-3xl font-bold mb-2">👥 Audience Targeting AI</h1>
        <p className="text-gray-400 mb-8">Get optimal audience targeting recommendations</p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <input type="text" placeholder="Product Name" value={productName} onChange={(e) => setProductName(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          <input type="text" placeholder="Target Persona" value={targetPersona} onChange={(e) => setTargetPersona(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
        </div>

        <textarea placeholder="Product Description" value={productDescription} onChange={(e) => setProductDescription(e.target.value)} className="w-full p-3 mb-4 bg-gray-800 rounded border border-gray-700 outline-none" rows={2} />

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Price Point ($)</label>
            <input type="number" value={pricePoint} onChange={(e) => setPricePoint(Number(e.target.value))} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <label className="flex items-center gap-2 p-3 bg-gray-800 rounded border border-gray-700 cursor-pointer">
            <input type="checkbox" checked={hasCustomers} onChange={(e) => setHasCustomers(e.target.checked)} />
            <span>Have customer list</span>
          </label>
          <label className="flex items-center gap-2 p-3 bg-gray-800 rounded border border-gray-700 cursor-pointer">
            <input type="checkbox" checked={hasTraffic} onChange={(e) => setHasTraffic(e.target.checked)} />
            <span>Have website traffic</span>
          </label>
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={suggestAudiences} disabled={loading || !productName} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Analyzing...' : 'Get Suggestions'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Primary Audiences</h3>
              <div className="space-y-3">
                {result.primary_audiences?.map((aud, i) => (
                  <div key={i} className="p-4 bg-gray-700/50 rounded">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold">{aud.name}</span>
                      <span className={`text-lg font-bold ${aud.relevance_score >= 90 ? 'text-green-400' : 'text-yellow-400'}`}>{aud.relevance_score}</span>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-400">
                      <span className="px-2 py-1 bg-gray-600 rounded">{aud.type}</span>
                      <span>{aud.estimated_size}</span>
                    </div>
                    {aud.targeting_tips && (
                      <p className="text-sm text-gray-500 mt-2">💡 {aud.targeting_tips[0]}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Exclusions</h3>
              <div className="space-y-3">
                {result.exclusions?.map((exc, i) => (
                  <div key={i} className="flex justify-between items-center p-3 bg-red-900/20 rounded border border-red-800/50">
                    <div>
                      <p className="font-medium">{exc.name}</p>
                      <p className="text-sm text-gray-400">{exc.reason}</p>
                    </div>
                    <span className="text-green-400 text-sm">{exc.impact}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Lookalike Strategy</h3>
              <p className="text-gray-300">{result.lookalike_strategy}</p>
            </div>

            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Testing Order</h3>
              <ol className="space-y-2">
                {result.testing_order?.map((step, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-sm">{i + 1}</span>
                    <span>{step.replace(/^\d+\.\s*/, '')}</span>
                  </li>
                ))}
              </ol>
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
