'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

interface Hook {
  text: string;
  pattern: string;
  score: number;
  explanation: string;
}

export default function HooksPage() {
  const [productName, setProductName] = useState('');
  const [productDescription, setProductDescription] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [painPoints, setPainPoints] = useState('');
  const [benefits, setBenefits] = useState('');
  const [includeEmojis, setIncludeEmojis] = useState(false);
  const [hooks, setHooks] = useState<Hook[]>([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState('');

  const generateHooks = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/hooks/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: productName,
          product_description: productDescription,
          target_audience: targetAudience,
          pain_points: painPoints.split(',').map(p => p.trim()).filter(Boolean),
          benefits: benefits.split(',').map(b => b.trim()).filter(Boolean),
          include_emojis: includeEmojis,
          num_hooks: 10,
        }),
      });
      const data = await res.json();
      setHooks(data.hooks || []);
      setSummary(data.summary || '');
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const runDemo = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/hooks/demo', { method: 'POST' });
      const data = await res.json();
      setSummary(data.summary || '');
      setHooks(data.hooks?.map((text: string, i: number) => ({ text, pattern: 'demo', score: 80 - i * 5, explanation: 'Demo hook' })) || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const copyHook = (text: string) => navigator.clipboard.writeText(text);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <ToolsNav />
      <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">🪝 Hook Generator</h1>
        <p className="text-gray-400 mb-8">Create scroll-stopping ad hooks using proven patterns</p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <input type="text" placeholder="Product Name" value={productName} onChange={(e) => setProductName(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          <input type="text" placeholder="Target Audience" value={targetAudience} onChange={(e) => setTargetAudience(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
        </div>

        <textarea placeholder="Product Description" value={productDescription} onChange={(e) => setProductDescription(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none mb-4" rows={2} />

        <div className="grid grid-cols-2 gap-4 mb-4">
          <input type="text" placeholder="Pain Points (comma-separated)" value={painPoints} onChange={(e) => setPainPoints(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
          <input type="text" placeholder="Benefits (comma-separated)" value={benefits} onChange={(e) => setBenefits(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 focus:border-blue-500 outline-none" />
        </div>

        <label className="flex items-center gap-2 mb-6 cursor-pointer">
          <input type="checkbox" checked={includeEmojis} onChange={(e) => setIncludeEmojis(e.target.checked)} className="w-4 h-4" />
          <span>Include Emojis</span>
        </label>

        <div className="flex gap-4 mb-8">
          <button onClick={generateHooks} disabled={loading || !productName} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Generating...' : 'Generate Hooks'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {summary && <div className="mb-6 p-4 bg-gray-800 rounded border border-gray-700"><p className="text-green-400">{summary}</p></div>}

        {hooks.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Generated Hooks</h2>
            {hooks.map((hook, i) => (
              <div key={i} className="p-4 bg-gray-800 rounded border border-gray-700 hover:border-gray-600 transition">
                <div className="flex justify-between items-start mb-2">
                  <p className="text-lg font-medium flex-1">{hook.text}</p>
                  <button onClick={() => copyHook(hook.text)} className="ml-4 px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 rounded">Copy</button>
                </div>
                <div className="flex gap-4 text-sm text-gray-400">
                  <span className="px-2 py-1 bg-gray-700 rounded">{hook.pattern}</span>
                  <span className={`px-2 py-1 rounded ${hook.score >= 80 ? 'bg-green-900 text-green-300' : hook.score >= 60 ? 'bg-yellow-900 text-yellow-300' : 'bg-red-900 text-red-300'}`}>Score: {hook.score}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
