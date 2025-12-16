'use client';

import Link from 'next/link';
import { 
  Zap, 
  Globe, 
  Target, 
  TrendingUp, 
  Shield, 
  DollarSign,
  Users,
  BarChart3,
  Video,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Clock,
  ExternalLink,
} from 'lucide-react';

// Quantum Feature Card
function FeatureCard({ 
  icon: Icon, 
  title, 
  description,
  href,
}: { 
  icon: any; 
  title: string; 
  description: string;
  href?: string;
}) {
  const content = (
    <div className="group p-6 bg-dark-surface border border-dark-hover rounded-xl hover:border-quantum-500/30 hover:shadow-quantum transition-all cursor-pointer">
      <div className="w-12 h-12 rounded-lg bg-quantum-500/10 flex items-center justify-center mb-4 group-hover:bg-quantum-500/20 transition">
        <Icon className="w-6 h-6 text-quantum-400" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-zinc-400">{description}</p>
    </div>
  );
  
  if (href) {
    return <Link href={href}>{content}</Link>;
  }
  return content;
}

// Stat Item
function StatItem({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-4xl font-bold font-mono text-quantum-400">{value}</div>
      <div className="text-sm text-zinc-500 mt-1">{label}</div>
    </div>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen bg-dark-primary">
      {/* Header */}
      <header className="border-b border-dark-hover px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-quantum-500/20 border border-quantum-500/30 flex items-center justify-center">
              <Zap className="w-5 h-5 text-quantum-400" />
            </div>
            <span className="text-xl font-bold text-white">QuantumLaunch</span>
          </div>
          
          <nav className="hidden md:flex items-center gap-8">
            <Link href="/studio" className="text-sm text-zinc-400 hover:text-white transition">
              Studio
            </Link>
            <Link href="/tools" className="text-sm text-zinc-400 hover:text-white transition">
              Tools
            </Link>
            <Link href="/dashboard" className="text-sm text-zinc-400 hover:text-white transition">
              Dashboard
            </Link>
          </nav>
          
          <div className="flex items-center gap-4">
            <button className="text-sm text-zinc-400 hover:text-white transition">
              Sign In
            </button>
            <Link 
              href="/studio"
              className="px-4 py-2 bg-quantum-500 hover:bg-quantum-600 text-black font-medium rounded-lg transition"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-24">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-quantum-500/10 border border-quantum-500/30 rounded-full mb-8">
              <Sparkles className="w-4 h-4 text-quantum-400" />
              <span className="text-sm font-medium text-quantum-400">
                Quantum Multi-Model Ad Intelligence
              </span>
            </div>
            
            {/* Headline */}
            <h1 className="text-6xl font-bold leading-tight">
              Launch ads at{' '}
              <span className="bg-gradient-to-r from-quantum-400 to-quantum-500 bg-clip-text text-transparent">
                quantum speed
              </span>
            </h1>
            
            {/* Subheadline */}
            <p className="mt-6 text-xl text-zinc-400 max-w-2xl mx-auto">
              The First Autonomous Ad Engine. Transform your website into high-performing 
              ads with Quantum Intelligence — automatic extraction, compliance verification, 
              and one-click publishing.
            </p>
            
            {/* CTA */}
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link 
                href="/studio"
                className="px-8 py-4 bg-quantum-500 hover:bg-quantum-600 text-black text-lg font-semibold rounded-xl transition flex items-center gap-2"
              >
                <Zap className="w-5 h-5" />
                Launch My Ads
              </Link>
              <Link 
                href="/dashboard"
                className="px-8 py-4 border border-dark-hover hover:border-zinc-600 text-white text-lg font-medium rounded-xl transition flex items-center gap-2"
              >
                View Demo
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
            
            {/* Stats */}
            <div className="mt-16 flex justify-center gap-16">
              <StatItem value="60s" label="To Launch" />
              <StatItem value="23" label="Quantum Tools" />
              <StatItem value="2.3x" label="Avg ROAS" />
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="px-6 py-20 border-t border-dark-hover">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white">How Quantum Intelligence Works</h2>
            <p className="mt-4 text-zinc-400 max-w-2xl mx-auto">
              One input. Full campaign. You approve, we execute.
            </p>
          </div>
          
          <div className="grid md:grid-cols-4 gap-8">
            {[
              {
                step: '1',
                icon: Globe,
                title: 'Enter URL',
                description: 'Paste your website. Quantum Extractor analyzes your content.',
              },
              {
                step: '2',
                icon: Shield,
                title: 'Review Claims',
                description: 'See extracted claims with compliance verification.',
              },
              {
                step: '3',
                icon: Sparkles,
                title: 'Approve Ads',
                description: 'Quantum Score ranks each variant. Approve the best.',
              },
              {
                step: '4',
                icon: TrendingUp,
                title: 'Launch & Monitor',
                description: 'One-click publish. Quantum Sentinel monitors 24/7.',
              },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="text-6xl font-bold text-dark-hover absolute -top-4 -left-2 select-none">
                  {item.step}
                </div>
                <div className="relative z-10 pt-8">
                  <div className="w-12 h-12 rounded-lg bg-quantum-500/10 flex items-center justify-center mb-4">
                    <item.icon className="w-6 h-6 text-quantum-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                  <p className="text-sm text-zinc-400">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-20 border-t border-dark-hover">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white">23 Quantum-Powered Tools</h2>
            <p className="mt-4 text-zinc-400 max-w-2xl mx-auto">
              All running automatically behind the scenes. Access individually when you need more control.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            <FeatureCard
              icon={Globe}
              title="Quantum Extractor"
              description="Extracts brand claims, value propositions, and messaging from any website."
              href="/dashboard"
            />
            <FeatureCard
              icon={Sparkles}
              title="Quantum Hooks"
              description="Generates high-converting headlines using proven persuasion patterns."
              href="/hooks"
            />
            <FeatureCard
              icon={TrendingUp}
              title="Quantum Score"
              description="Predicts ad performance before you spend a dollar."
              href="/predict"
            />
            <FeatureCard
              icon={Shield}
              title="Quantum Sentinel"
              description="Monitors brand sentiment 24/7. Auto-pauses ads during PR crises."
              href="/sentiment"
            />
            <FeatureCard
              icon={DollarSign}
              title="Quantum Budget"
              description="Simulates budget scenarios with expected CPA and ROAS."
              href="/budget"
            />
            <FeatureCard
              icon={Users}
              title="Quantum Audience"
              description="Suggests optimal targeting based on your product and goals."
              href="/audience"
            />
            <FeatureCard
              icon={Video}
              title="Quantum Video"
              description="Generates UGC-style video ads with AI avatars."
              href="/video"
            />
            <FeatureCard
              icon={BarChart3}
              title="Quantum Radar"
              description="Analyzes competitor ads and identifies winning patterns."
              href="/intel"
            />
            <FeatureCard
              icon={Target}
              title="Quantum Platform"
              description="Recommends the best platform for your product and budget."
              href="/platforms"
            />
          </div>
          
          <div className="mt-8 text-center">
            <Link 
              href="/tools"
              className="inline-flex items-center gap-2 text-quantum-400 hover:text-quantum-300 transition"
            >
              View all 23 tools
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Why Quantum */}
      <section className="px-6 py-20 border-t border-dark-hover">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl font-bold text-white mb-6">
                Why Quantum Intelligence?
              </h2>
              <p className="text-zinc-400 mb-8">
                Not just another ad generator. Quantum Multi-Model Intelligence orchestrates 
                23 specialized tools to create, score, publish, and monitor your ads automatically.
              </p>
              
              <div className="space-y-4">
                {[
                  'Extracts claims directly from your website',
                  'Verifies legal compliance before publishing',
                  'Scores every variant with performance prediction',
                  'Publishes to Meta with one click',
                  'Monitors 24/7 with auto-pause on crisis',
                  'Suggests improvements based on real data',
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-quantum-400 flex-shrink-0" />
                    <span className="text-zinc-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="bg-dark-surface border border-dark-hover rounded-xl p-8">
              <h3 className="text-lg font-semibold text-white mb-6">Quantum vs. Alternatives</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-dark-hover">
                  <span className="text-zinc-400">ChatGPT</span>
                  <span className="text-zinc-500">Copy ideas only</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-dark-hover">
                  <span className="text-zinc-400">Jasper</span>
                  <span className="text-zinc-500">No publishing</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-dark-hover">
                  <span className="text-zinc-400">AdCreative.ai</span>
                  <span className="text-zinc-500">No monitoring</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-dark-hover">
                  <span className="text-zinc-400">Ad Agency</span>
                  <span className="text-zinc-500">$5,000+/month</span>
                </div>
                <div className="flex items-center justify-between py-3 bg-quantum-500/10 rounded-lg px-4 -mx-4">
                  <span className="text-quantum-400 font-medium">QuantumLaunch</span>
                  <span className="text-quantum-400">End-to-end automation</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 border-t border-dark-hover">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to launch at quantum speed?
          </h2>
          <p className="text-xl text-zinc-400 mb-8">
            Enter your URL. Get ads in 60 seconds. No credit card required.
          </p>
          <Link 
            href="/studio"
            className="inline-flex items-center gap-2 px-8 py-4 bg-quantum-500 hover:bg-quantum-600 text-black text-lg font-semibold rounded-xl transition"
          >
            <Zap className="w-5 h-5" />
            Start Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-hover px-6 py-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-quantum-500/20 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-quantum-400" />
                </div>
                <span className="font-bold text-white">QuantumLaunch</span>
              </div>
              <p className="text-sm text-zinc-500">
                Part of the Quantum family of products.
              </p>
            </div>
            
            <div>
              <h4 className="font-medium text-white mb-4">Product</h4>
              <div className="space-y-2">
                <Link href="/studio" className="block text-sm text-zinc-400 hover:text-white transition">
                  Studio
                </Link>
                <Link href="/tools" className="block text-sm text-zinc-400 hover:text-white transition">
                  All Tools
                </Link>
                <Link href="/dashboard" className="block text-sm text-zinc-400 hover:text-white transition">
                  Dashboard
                </Link>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-white mb-4">Quantum Family</h4>
              <div className="space-y-2">
                <a href="#" className="block text-sm text-zinc-400 hover:text-white transition">
                  QuantumLayer Platform
                </a>
                <a href="#" className="block text-sm text-zinc-400 hover:text-white transition">
                  QuantumTest
                </a>
                <a href="#" className="block text-sm text-zinc-400 hover:text-white transition">
                  QL Resilience Fabric
                </a>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-white mb-4">Resources</h4>
              <div className="space-y-2">
                <a href="#" className="block text-sm text-zinc-400 hover:text-white transition">
                  Documentation
                </a>
                <a href="#" className="block text-sm text-zinc-400 hover:text-white transition">
                  API Reference
                </a>
                <a href="#" className="block text-sm text-zinc-400 hover:text-white transition">
                  Contact
                </a>
              </div>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-dark-hover flex items-center justify-between">
            <p className="text-sm text-zinc-500">
              © 2025 QuantumLaunch. Powered by Quantum Multi-Model Intelligence.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-sm text-zinc-500 hover:text-white transition">
                Privacy
              </a>
              <a href="#" className="text-sm text-zinc-500 hover:text-white transition">
                Terms
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
