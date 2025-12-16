'use client';

import Link from 'next/link';
import { 
  Zap,
  Globe,
  Sparkles,
  TrendingUp,
  Shield,
  DollarSign,
  Users,
  Target,
  Video,
  BarChart3,
  Eye,
  RefreshCw,
  FileText,
  Download,
  TestTube,
  Lightbulb,
  MessageSquare,
  Award,
  Layers,
  ArrowLeft,
} from 'lucide-react';

interface Tool {
  id: string;
  name: string;
  quantumName: string;
  description: string;
  icon: any;
  href: string;
  category: 'core' | 'generation' | 'analysis' | 'optimization' | 'publishing';
}

const tools: Tool[] = [
  // Core
  {
    id: 'pipeline',
    name: 'Full Pipeline',
    quantumName: 'Quantum Pipeline',
    description: 'End-to-end URL to ads generation with all tools orchestrated automatically.',
    icon: Layers,
    href: '/studio',
    category: 'core',
  },
  {
    id: 'extractor',
    name: 'Brand Extractor',
    quantumName: 'Quantum Extractor',
    description: 'Extract brand claims, value propositions, and messaging from any website.',
    icon: Globe,
    href: '/dashboard',
    category: 'core',
  },
  
  // Generation
  {
    id: 'hooks',
    name: 'Hook Generator',
    quantumName: 'Quantum Hooks',
    description: 'Generate high-converting headlines using proven persuasion patterns.',
    icon: Sparkles,
    href: '/hooks',
    category: 'generation',
  },
  {
    id: 'video',
    name: 'Video Generator',
    quantumName: 'Quantum Video',
    description: 'Create UGC-style video ads with AI avatars and dynamic scripts.',
    icon: Video,
    href: '/video',
    category: 'generation',
  },
  {
    id: 'iterate',
    name: 'Iteration Assistant',
    quantumName: 'Quantum Iterate',
    description: 'Get improvement suggestions for underperforming ads.',
    icon: RefreshCw,
    href: '/iterate',
    category: 'generation',
  },
  {
    id: 'social',
    name: 'Social Proof Collector',
    quantumName: 'Quantum Proof',
    description: 'Collect and format testimonials, stats, and trust signals.',
    icon: MessageSquare,
    href: '/social',
    category: 'generation',
  },
  
  // Analysis
  {
    id: 'predict',
    name: 'Performance Predictor',
    quantumName: 'Quantum Score',
    description: 'Predict ad performance before spending a dollar.',
    icon: TrendingUp,
    href: '/predict',
    category: 'analysis',
  },
  {
    id: 'attention',
    name: 'Attention Analyzer',
    quantumName: 'Quantum Vision',
    description: 'Predict where eyes will look with attention heatmaps.',
    icon: Eye,
    href: '/attention',
    category: 'analysis',
  },
  {
    id: 'landing',
    name: 'Landing Page Analyzer',
    quantumName: 'Quantum Landing',
    description: 'Score landing page quality and message match.',
    icon: FileText,
    href: '/landing',
    category: 'analysis',
  },
  {
    id: 'intel',
    name: 'Competitor Intelligence',
    quantumName: 'Quantum Radar',
    description: 'Analyze competitor ads and identify winning patterns.',
    icon: BarChart3,
    href: '/intel',
    category: 'analysis',
  },
  {
    id: 'fatigue',
    name: 'Fatigue Predictor',
    quantumName: 'Quantum Pulse',
    description: 'Predict when creative will fatigue and need refresh.',
    icon: RefreshCw,
    href: '/fatigue',
    category: 'analysis',
  },
  {
    id: 'sentiment',
    name: 'Sentiment Monitor',
    quantumName: 'Quantum Sentinel',
    description: 'Monitor brand sentiment 24/7 with auto-pause on crisis.',
    icon: Shield,
    href: '/sentiment',
    category: 'analysis',
  },
  
  // Optimization
  {
    id: 'budget',
    name: 'Budget Simulator',
    quantumName: 'Quantum Budget',
    description: 'Simulate budget scenarios with expected CPA and ROAS.',
    icon: DollarSign,
    href: '/budget',
    category: 'optimization',
  },
  {
    id: 'audience',
    name: 'Audience Targeting',
    quantumName: 'Quantum Audience',
    description: 'Get optimal audience suggestions for your product.',
    icon: Users,
    href: '/audience',
    category: 'optimization',
  },
  {
    id: 'platforms',
    name: 'Platform Recommender',
    quantumName: 'Quantum Platform',
    description: 'Find the best ad platform for your product and budget.',
    icon: Target,
    href: '/platforms',
    category: 'optimization',
  },
  {
    id: 'abtest',
    name: 'A/B Test Planner',
    quantumName: 'Quantum Test',
    description: 'Plan statistically valid A/B tests with sample size calculations.',
    icon: TestTube,
    href: '/abtest',
    category: 'optimization',
  },
  
  // Publishing
  {
    id: 'publish',
    name: 'Meta Publishing',
    quantumName: 'Quantum Publish',
    description: 'One-click publishing to Meta Ads (Facebook & Instagram).',
    icon: Zap,
    href: '/publish',
    category: 'publishing',
  },
  {
    id: 'export',
    name: 'Format Exporter',
    quantumName: 'Quantum Export',
    description: 'Export ads to all platform formats with one click.',
    icon: Download,
    href: '/export',
    category: 'publishing',
  },
  {
    id: 'proof',
    name: 'Proof Pack Generator',
    quantumName: 'Quantum Compliance',
    description: 'Generate compliance documentation for legal review.',
    icon: Award,
    href: '/proof',
    category: 'publishing',
  },
];

const categories = [
  { id: 'core', name: 'Core', description: 'Essential pipeline tools' },
  { id: 'generation', name: 'Generation', description: 'Create ad content' },
  { id: 'analysis', name: 'Analysis', description: 'Understand performance' },
  { id: 'optimization', name: 'Optimization', description: 'Improve results' },
  { id: 'publishing', name: 'Publishing', description: 'Go live' },
];

function ToolCard({ tool }: { tool: Tool }) {
  const Icon = tool.icon;
  
  return (
    <Link href={tool.href}>
      <div className="group h-full p-6 bg-dark-surface border border-dark-hover rounded-xl hover:border-quantum-500/30 hover:shadow-quantum transition-all cursor-pointer">
        <div className="flex items-start justify-between mb-4">
          <div className="w-12 h-12 rounded-lg bg-quantum-500/10 flex items-center justify-center group-hover:bg-quantum-500/20 transition">
            <Icon className="w-6 h-6 text-quantum-400" />
          </div>
        </div>
        
        <h3 className="text-lg font-semibold text-white mb-1">{tool.quantumName}</h3>
        <p className="text-xs text-zinc-500 mb-3">{tool.name}</p>
        <p className="text-sm text-zinc-400">{tool.description}</p>
      </div>
    </Link>
  );
}

export default function ToolsPage() {
  return (
    <div className="min-h-screen bg-dark-primary">
      {/* Header */}
      <header className="border-b border-dark-hover px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-zinc-400 hover:text-white transition">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-quantum-500/20 border border-quantum-500/30 flex items-center justify-center">
                <Zap className="w-5 h-5 text-quantum-400" />
              </div>
              <span className="text-xl font-bold text-white">QuantumLaunch</span>
            </div>
          </div>
          
          <nav className="flex items-center gap-4">
            <Link href="/studio" className="text-sm text-zinc-400 hover:text-white transition">
              Studio
            </Link>
            <Link href="/dashboard" className="text-sm text-zinc-400 hover:text-white transition">
              Dashboard
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-white mb-4">
            23 Quantum-Powered Tools
          </h1>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
            Every tool runs automatically in the Studio. Use them individually when you need more control.
          </p>
          
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link 
              href="/studio"
              className="px-6 py-3 bg-quantum-500 hover:bg-quantum-600 text-black font-medium rounded-lg transition flex items-center gap-2"
            >
              <Zap className="w-5 h-5" />
              Launch Studio
            </Link>
          </div>
        </div>

        {/* Tools by Category */}
        {categories.map((category) => {
          const categoryTools = tools.filter(t => t.category === category.id);
          if (categoryTools.length === 0) return null;
          
          return (
            <div key={category.id} className="mb-12">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-white">{category.name}</h2>
                <p className="text-sm text-zinc-500">{category.description}</p>
              </div>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categoryTools.map((tool) => (
                  <ToolCard key={tool.id} tool={tool} />
                ))}
              </div>
            </div>
          );
        })}
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-hover py-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-zinc-500">
          <p>Powered by Quantum Multi-Model Intelligence</p>
          <p className="mt-1">© 2025 QuantumLaunch • Part of the Quantum family</p>
        </div>
      </footer>
    </div>
  );
}
