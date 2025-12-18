'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
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
  MessageSquare,
  Award,
  Layers,
  ArrowLeft,
  ArrowRight,
  Search,
  LucideIcon,
} from 'lucide-react';
import { Badge } from '../../components/ui';

interface Tool {
  id: string;
  name: string;
  quantumName: string;
  description: string;
  icon: LucideIcon;
  href: string;
  category: 'core' | 'generation' | 'analysis' | 'optimization' | 'publishing';
  badge?: 'new' | 'popular' | 'premium';
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
    badge: 'popular',
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
    badge: 'popular',
  },
  {
    id: 'video',
    name: 'Video Generator',
    quantumName: 'Quantum Video',
    description: 'Create UGC-style video ads with AI avatars and dynamic scripts.',
    icon: Video,
    href: '/video',
    category: 'generation',
    badge: 'new',
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
    badge: 'popular',
  },
  {
    id: 'attention',
    name: 'Attention Analyzer',
    quantumName: 'Quantum Vision',
    description: 'Predict where eyes will look with attention heatmaps.',
    icon: Eye,
    href: '/attention',
    category: 'analysis',
    badge: 'premium',
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
    badge: 'new',
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
  { id: 'all', name: 'All Tools', icon: Layers, count: tools.length },
  { id: 'core', name: 'Core', icon: Zap, count: tools.filter(t => t.category === 'core').length },
  { id: 'generation', name: 'Generation', icon: Sparkles, count: tools.filter(t => t.category === 'generation').length },
  { id: 'analysis', name: 'Analysis', icon: BarChart3, count: tools.filter(t => t.category === 'analysis').length },
  { id: 'optimization', name: 'Optimization', icon: Target, count: tools.filter(t => t.category === 'optimization').length },
  { id: 'publishing', name: 'Publishing', icon: Download, count: tools.filter(t => t.category === 'publishing').length },
];

const badgeConfig = {
  new: { variant: 'quantum' as const, label: 'New' },
  popular: { variant: 'purple' as const, label: 'Popular' },
  premium: { variant: 'warning' as const, label: 'Premium' },
};

// Animation variants
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

function ToolCard({ tool, index }: { tool: Tool; index: number }) {
  const Icon = tool.icon;

  return (
    <motion.div
      variants={item}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Link href={tool.href}>
        <div className="group h-full p-6 bg-zinc-900/80 border border-zinc-800 rounded-xl hover:border-quantum-500/30 hover:shadow-lg hover:shadow-quantum-500/5 transition-all duration-300 cursor-pointer relative overflow-hidden">
          {/* Glow effect on hover */}
          <div className="absolute inset-0 bg-gradient-to-br from-quantum-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

          <div className="relative">
            <div className="flex items-start justify-between mb-4">
              <motion.div
                className="w-12 h-12 rounded-lg bg-quantum-500/10 border border-quantum-500/20 flex items-center justify-center group-hover:bg-quantum-500/20 group-hover:border-quantum-500/30 transition-all duration-300"
                whileHover={{ scale: 1.05 }}
              >
                <Icon className="w-6 h-6 text-quantum-400" />
              </motion.div>

              {tool.badge && (
                <Badge variant={badgeConfig[tool.badge].variant} size="sm">
                  {badgeConfig[tool.badge].label}
                </Badge>
              )}
            </div>

            <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-quantum-400 transition-colors">
              {tool.quantumName}
            </h3>
            <p className="text-xs text-zinc-500 mb-3 font-mono">{tool.name}</p>
            <p className="text-sm text-zinc-400 leading-relaxed">{tool.description}</p>

            {/* Arrow indicator */}
            <div className="mt-4 flex items-center text-quantum-500 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              <span>Open Tool</span>
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

export default function ToolsPage() {
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTools = tools.filter(tool => {
    const matchesCategory = activeCategory === 'all' || tool.category === activeCategory;
    const matchesSearch = searchQuery === '' ||
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.quantumName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-zinc-800/80 bg-[#050505]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="text-zinc-400 hover:text-white transition p-2 hover:bg-zinc-800 rounded-lg">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="flex items-center gap-3">
                <motion.div
                  className="w-10 h-10 rounded-xl bg-quantum-500/20 border border-quantum-500/30 flex items-center justify-center"
                  animate={{
                    boxShadow: ['0 0 20px rgba(34, 197, 94, 0.2)', '0 0 30px rgba(34, 197, 94, 0.3)', '0 0 20px rgba(34, 197, 94, 0.2)']
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Zap className="w-5 h-5 text-quantum-400" />
                </motion.div>
                <span className="text-xl font-bold text-white">QuantumLaunch</span>
              </div>
            </div>

            <nav className="flex items-center gap-6">
              <Link href="/studio" className="text-sm text-zinc-400 hover:text-white transition">
                Studio
              </Link>
              <Link href="/dashboard" className="text-sm text-zinc-400 hover:text-white transition">
                Dashboard
              </Link>
              <Link href="/tools" className="text-sm text-quantum-400 font-medium">
                Tools
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Hero */}
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            <span className="bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
              {tools.length} Quantum-Powered
            </span>{' '}
            <span className="bg-gradient-to-r from-quantum-400 to-quantum-500 bg-clip-text text-transparent">
              Tools
            </span>
          </h1>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
            Every tool runs automatically in the Studio. Use them individually when you need more control.
          </p>

          <div className="mt-8 flex items-center justify-center gap-4">
            <Link href="/studio">
              <motion.button
                className="px-6 py-3 bg-gradient-to-r from-quantum-500 to-quantum-600 text-black font-semibold rounded-xl flex items-center gap-2 shadow-lg shadow-quantum-500/25"
                whileHover={{ scale: 1.02, boxShadow: '0 0 30px rgba(34, 197, 94, 0.4)' }}
                whileTap={{ scale: 0.98 }}
              >
                <Zap className="w-5 h-5" />
                Launch Studio
              </motion.button>
            </Link>
          </div>
        </motion.div>

        {/* Search & Filter */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {/* Search */}
          <div className="relative mb-6 max-w-md mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder:text-zinc-500 focus:outline-none focus:border-quantum-500/50 focus:ring-2 focus:ring-quantum-500/20 transition"
            />
          </div>

          {/* Category Pills */}
          <div className="flex flex-wrap justify-center gap-2">
            {categories.map((category) => {
              const Icon = category.icon;
              const isActive = activeCategory === category.id;

              return (
                <motion.button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-quantum-500/20 text-quantum-400 border border-quantum-500/30'
                      : 'bg-zinc-900 text-zinc-400 border border-zinc-800 hover:border-zinc-700 hover:text-white'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Icon className="w-4 h-4" />
                  {category.name}
                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                    isActive ? 'bg-quantum-500/30' : 'bg-zinc-800'
                  }`}>
                    {category.count}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </motion.div>

        {/* Tools Grid */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeCategory + searchQuery}
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
            variants={container}
            initial="hidden"
            animate="show"
          >
            {filteredTools.map((tool, index) => (
              <ToolCard key={tool.id} tool={tool} index={index} />
            ))}
          </motion.div>
        </AnimatePresence>

        {/* No Results */}
        {filteredTools.length === 0 && (
          <motion.div
            className="text-center py-16"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-zinc-800 flex items-center justify-center">
              <Search className="w-8 h-8 text-zinc-500" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">No tools found</h3>
            <p className="text-zinc-400">Try a different search term or category</p>
          </motion.div>
        )}

        {/* Quick Stats */}
        <motion.div
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          {[
            { label: 'Total Tools', value: tools.length, icon: Layers },
            { label: 'AI Models', value: '4+', icon: Sparkles },
            { label: 'Ad Formats', value: '9', icon: Download },
            { label: 'Platforms', value: '6', icon: Target },
          ].map((stat, i) => (
            <div key={i} className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl text-center">
              <stat.icon className="w-6 h-6 text-quantum-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white font-mono">{stat.value}</p>
              <p className="text-xs text-zinc-500">{stat.label}</p>
            </div>
          ))}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm text-zinc-500">Powered by Quantum Multi-Model Intelligence</p>
          <p className="text-xs text-zinc-600 mt-1">QuantumLaunch - A <a href="https://www.quantumlayerplatform.com/" className="text-quantum-400 hover:text-quantum-300 transition" target="_blank" rel="noopener noreferrer">QuantumLayer Platform</a> company</p>
        </div>
      </footer>
    </div>
  );
}
