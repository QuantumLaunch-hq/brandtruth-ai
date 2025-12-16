'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export const tools = [
  { href: '/dashboard', label: 'Dashboard', icon: '🎯', category: 'core' },
  { href: '/hooks', label: 'Hook Generator', icon: '🪝', category: 'create' },
  { href: '/predict', label: 'Performance Score', icon: '📊', category: 'analyze' },
  { href: '/attention', label: 'Attention Heatmap', icon: '👁️', category: 'analyze' },
  { href: '/landing', label: 'Landing Analyzer', icon: '🔍', category: 'analyze' },
  { href: '/budget', label: 'Budget Simulator', icon: '💰', category: 'plan' },
  { href: '/platforms', label: 'Platform Recommender', icon: '📱', category: 'plan' },
  { href: '/abtest', label: 'A/B Test Planner', icon: '🧪', category: 'plan' },
  { href: '/audience', label: 'Audience Targeting', icon: '👥', category: 'plan' },
  { href: '/iterate', label: 'Iteration Assistant', icon: '🔄', category: 'optimize' },
  { href: '/social', label: 'Social Proof', icon: '⭐', category: 'create' },
  { href: '/export', label: 'Multi-Format Export', icon: '📦', category: 'core' },
  { href: '/video', label: 'AI Video', icon: '🎬', category: 'create' },
  { href: '/intel', label: 'Competitor Intel', icon: '🕵️', category: 'analyze' },
  { href: '/fatigue', label: 'Creative Fatigue', icon: '😴', category: 'analyze' },
  { href: '/proof', label: 'Proof Pack', icon: '📋', category: 'create' },
  { href: '/sentiment', label: 'Sentiment Monitor', icon: '💜', category: 'monitor' },
  { href: '/publish', label: 'Meta Publisher', icon: '📤', category: 'publish' },
];

export default function ToolsNav() {
  const pathname = usePathname();

  return (
    <div className="bg-gray-800 border-b border-gray-700 overflow-x-auto">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center gap-1 py-2">
          <Link href="/" className="px-3 py-2 text-gray-400 hover:text-white">
            ← Home
          </Link>
          <div className="w-px h-6 bg-gray-700 mx-2" />
          {tools.slice(0, 12).map((tool) => (
            <Link
              key={tool.href}
              href={tool.href}
              className={`px-3 py-2 rounded-lg text-sm whitespace-nowrap transition ${
                pathname === tool.href
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <span className="mr-1">{tool.icon}</span>
              <span className="hidden md:inline">{tool.label}</span>
            </Link>
          ))}
          <Link href="/tools" className="px-3 py-2 text-gray-400 hover:text-white text-sm">
            More →
          </Link>
        </div>
      </div>
    </div>
  );
}

export function ToolsGrid() {
  const categories = [
    { id: 'core', label: 'Core', color: 'bg-violet-500' },
    { id: 'create', label: 'Create', color: 'bg-green-500' },
    { id: 'analyze', label: 'Analyze', color: 'bg-blue-500' },
    { id: 'plan', label: 'Plan', color: 'bg-orange-500' },
    { id: 'optimize', label: 'Optimize', color: 'bg-pink-500' },
    { id: 'monitor', label: 'Monitor', color: 'bg-purple-500' },
    { id: 'publish', label: 'Publish', color: 'bg-teal-500' },
  ];

  return (
    <div className="space-y-8">
      {categories.map((cat) => {
        const catTools = tools.filter((t) => t.category === cat.id);
        if (catTools.length === 0) return null;
        return (
          <div key={cat.id}>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span className={`w-3 h-3 rounded-full ${cat.color}`}></span>
              {cat.label}
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {catTools.map((tool) => (
                <Link
                  key={tool.href}
                  href={tool.href}
                  className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-500 transition group"
                >
                  <div className="text-2xl mb-2">{tool.icon}</div>
                  <div className="font-medium text-white group-hover:text-blue-400 transition">{tool.label}</div>
                </Link>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
