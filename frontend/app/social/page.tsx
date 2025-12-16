'use client';

import { useState } from 'react';
import ToolsNav from '../../components/ToolsNav';

interface Proof {
  type: string;
  content: string;
  source: string;
  ad_ready: string;
  verified: boolean;
}

interface Result {
  proofs: Proof[];
  best_testimonial: string | null;
  best_stat: string | null;
  ad_snippets: string[];
  trust_score: number;
  recommendations: string[];
  summary: string;
}

export default function SocialPage() {
  const [brandName, setBrandName] = useState('');
  const [brandUrl, setBrandUrl] = useState('');
  const [productDescription, setProductDescription] = useState('');
  const [testimonials, setTestimonials] = useState('');
  const [userCount, setUserCount] = useState<number | ''>('');
  const [rating, setRating] = useState<number | ''>('');
  const [customers, setCustomers] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);

  const collect = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/social/collect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name: brandName,
          brand_url: brandUrl,
          product_description: productDescription,
          existing_testimonials: testimonials.split('\n').map(t => t.trim()).filter(Boolean),
          user_count: userCount || null,
          rating: rating || null,
          notable_customers: customers.split(',').map(c => c.trim()).filter(Boolean),
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
      const res = await fetch('http://localhost:8000/social/demo', { method: 'POST' });
      const data = await res.json();
      setResult({
        ...data,
        proofs: [
          { type: 'testimonial', content: 'This helped me land my dream job!', source: 'Customer', ad_ready: '"This helped me land my dream job!"', verified: false },
          { type: 'testimonial', content: 'Got 3 interviews in the first week', source: 'Customer', ad_ready: '"Got 3 interviews in the first week"', verified: false },
          { type: 'stat', content: '1K+ users trust Careerfied', source: 'Internal', ad_ready: '1K+ users trust Careerfied', verified: true },
          { type: 'review', content: 'Rated 4.8/5 ⭐⭐⭐⭐', source: 'Reviews', ad_ready: 'Rated 4.8/5 ⭐⭐⭐⭐', verified: false },
          { type: 'logo', content: 'Trusted by Google', source: 'Google', ad_ready: 'Trusted by Google', verified: true },
        ],
        best_testimonial: '"This helped me land my dream job!"',
        best_stat: '1K+ users trust Careerfied',
        ad_snippets: data.snippets || ['Join 1,500+ users', '⭐ 4.8/5 rating', 'Used by Google, Meta, Microsoft'],
        recommendations: ['Collect more testimonials', 'Add G2/Capterra rating', 'Video testimonials convert 2x better'],
      });
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const copySnippet = (text: string) => navigator.clipboard.writeText(text);

  const proofTypeColors: Record<string, string> = {
    testimonial: 'bg-purple-600',
    stat: 'bg-blue-600',
    review: 'bg-yellow-600',
    logo: 'bg-green-600',
    award: 'bg-red-600',
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <ToolsNav />
      <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">⭐ Social Proof Collector</h1>
        <p className="text-gray-400 mb-8">Gather and format social proof for your ads</p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <input type="text" placeholder="Brand Name" value={brandName} onChange={(e) => setBrandName(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          <input type="text" placeholder="Brand URL" value={brandUrl} onChange={(e) => setBrandUrl(e.target.value)} className="p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
        </div>

        <textarea placeholder="Product Description" value={productDescription} onChange={(e) => setProductDescription(e.target.value)} className="w-full p-3 mb-4 bg-gray-800 rounded border border-gray-700 outline-none" rows={2} />

        <textarea placeholder="Testimonials (one per line)" value={testimonials} onChange={(e) => setTestimonials(e.target.value)} className="w-full p-3 mb-4 bg-gray-800 rounded border border-gray-700 outline-none" rows={3} />

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">User Count</label>
            <input type="number" placeholder="e.g., 1500" value={userCount} onChange={(e) => setUserCount(e.target.value ? Number(e.target.value) : '')} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Rating (1-5)</label>
            <input type="number" step="0.1" min="1" max="5" placeholder="e.g., 4.8" value={rating} onChange={(e) => setRating(e.target.value ? Number(e.target.value) : '')} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Notable Customers</label>
            <input type="text" placeholder="Google, Meta, etc." value={customers} onChange={(e) => setCustomers(e.target.value)} className="w-full p-3 bg-gray-800 rounded border border-gray-700 outline-none" />
          </div>
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={collect} disabled={loading || !brandName} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded font-semibold transition">{loading ? 'Collecting...' : 'Collect Proof'}</button>
          <button onClick={runDemo} disabled={loading} className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition">Run Demo</button>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">Trust Score</h3>
                <span className={`text-4xl font-bold ${result.trust_score >= 80 ? 'text-green-400' : result.trust_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>{result.trust_score}/100</span>
              </div>
              <div className="h-3 bg-gray-700 rounded">
                <div className={`h-3 rounded ${result.trust_score >= 80 ? 'bg-green-500' : result.trust_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${result.trust_score}%` }} />
              </div>
            </div>

            <div className="p-6 bg-gray-800 rounded border border-gray-700">
              <h3 className="text-xl font-semibold mb-4">Ad-Ready Snippets</h3>
              <div className="space-y-3">
                {result.ad_snippets?.map((snippet, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                    <span>{snippet}</span>
                    <button onClick={() => copySnippet(snippet)} className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-500 rounded">Copy</button>
                  </div>
                ))}
              </div>
            </div>

            {result.proofs?.length > 0 && (
              <div className="p-6 bg-gray-800 rounded border border-gray-700">
                <h3 className="text-xl font-semibold mb-4">Collected Proof</h3>
                <div className="space-y-3">
                  {result.proofs.map((proof, i) => (
                    <div key={i} className="p-4 bg-gray-700/50 rounded">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 text-xs rounded ${proofTypeColors[proof.type] || 'bg-gray-600'}`}>{proof.type}</span>
                        {proof.verified && <span className="px-2 py-1 text-xs bg-green-600 rounded">Verified</span>}
                      </div>
                      <p className="text-gray-200">{proof.ad_ready}</p>
                      <p className="text-gray-500 text-sm mt-1">Source: {proof.source}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(result.best_testimonial || result.best_stat) && (
              <div className="grid grid-cols-2 gap-6">
                {result.best_testimonial && (
                  <div className="p-6 bg-purple-900/30 rounded border border-purple-700">
                    <h4 className="text-sm text-purple-400 mb-2">Best Testimonial</h4>
                    <p className="text-lg">{result.best_testimonial}</p>
                  </div>
                )}
                {result.best_stat && (
                  <div className="p-6 bg-blue-900/30 rounded border border-blue-700">
                    <h4 className="text-sm text-blue-400 mb-2">Best Stat</h4>
                    <p className="text-lg">{result.best_stat}</p>
                  </div>
                )}
              </div>
            )}

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
