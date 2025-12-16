'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { motion, useInView, useScroll, useTransform } from 'framer-motion';
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
  LucideIcon,
} from 'lucide-react';

// Animated Counter
function AnimatedCounter({ value, suffix = '', duration = 2 }: { value: number; suffix?: string; duration?: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      let start = 0;
      const end = value;
      const timer = setInterval(() => {
        start += end / (duration * 60);
        if (start >= end) {
          setCount(end);
          clearInterval(timer);
        } else {
          setCount(Math.floor(start * 10) / 10);
        }
      }, 1000 / 60);
      return () => clearInterval(timer);
    }
  }, [isInView, value, duration]);

  return (
    <span ref={ref} className="font-mono">
      {count}
      {suffix}
    </span>
  );
}

// Feature Card with animation
function FeatureCard({
  icon: Icon,
  title,
  description,
  href,
  delay = 0,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  href?: string;
  delay?: number;
}) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const content = (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      className="group h-full p-6 bg-zinc-900/80 border border-zinc-800 rounded-xl hover:border-quantum-500/30 hover:shadow-lg hover:shadow-quantum-500/10 transition-all cursor-pointer relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-quantum-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="relative">
        <div className="w-12 h-12 rounded-lg bg-quantum-500/10 border border-quantum-500/20 flex items-center justify-center mb-4 group-hover:bg-quantum-500/20 transition">
          <Icon className="w-6 h-6 text-quantum-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-quantum-400 transition-colors">
          {title}
        </h3>
        <p className="text-sm text-zinc-400">{description}</p>
      </div>
    </motion.div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }
  return content;
}

// Stat Item with animation
function StatItem({ value, label, suffix = '' }: { value: number; label: string; suffix?: string }) {
  return (
    <div className="text-center">
      <div className="text-4xl md:text-5xl font-bold text-quantum-400">
        <AnimatedCounter value={value} suffix={suffix} />
      </div>
      <div className="text-sm text-zinc-500 mt-2">{label}</div>
    </div>
  );
}

// Step Card
function StepCard({
  step,
  icon: Icon,
  title,
  description,
  delay,
}: {
  step: string;
  icon: LucideIcon;
  title: string;
  description: string;
  delay: number;
}) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay }}
      className="relative"
    >
      <div className="text-6xl font-bold text-zinc-800 absolute -top-4 -left-2 select-none">{step}</div>
      <div className="relative z-10 pt-8">
        <motion.div
          className="w-12 h-12 rounded-lg bg-quantum-500/10 border border-quantum-500/20 flex items-center justify-center mb-4"
          whileHover={{ scale: 1.1 }}
        >
          <Icon className="w-6 h-6 text-quantum-400" />
        </motion.div>
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-sm text-zinc-400">{description}</p>
      </div>
    </motion.div>
  );
}

export default function HomePage() {
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0]);
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 100]);

  return (
    <div className="min-h-screen bg-[#050505] overflow-hidden">
      {/* Background gradient mesh */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-quantum-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-[128px]" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-zinc-800/80 bg-[#050505]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <motion.div
                className="w-10 h-10 rounded-xl bg-quantum-500/20 border border-quantum-500/30 flex items-center justify-center"
                animate={{
                  boxShadow: [
                    '0 0 20px rgba(34, 197, 94, 0.2)',
                    '0 0 30px rgba(34, 197, 94, 0.3)',
                    '0 0 20px rgba(34, 197, 94, 0.2)',
                  ],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Zap className="w-5 h-5 text-quantum-400" />
              </motion.div>
              <span className="text-xl font-bold text-white">BrandTruth AI</span>
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
              <button className="hidden md:block text-sm text-zinc-400 hover:text-white transition">Sign In</button>
              <Link href="/studio">
                <motion.button
                  className="px-4 py-2 bg-quantum-500 hover:bg-quantum-600 text-black font-medium rounded-lg transition"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Get Started
                </motion.button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section ref={heroRef} className="relative px-6 py-24 md:py-32">
        <motion.div style={{ opacity: heroOpacity, y: heroY }} className="max-w-7xl mx-auto">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-quantum-500/10 border border-quantum-500/30 rounded-full mb-8"
            >
              <motion.div
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
              >
                <Sparkles className="w-4 h-4 text-quantum-400" />
              </motion.div>
              <span className="text-sm font-medium text-quantum-400">Quantum Multi-Model Ad Intelligence</span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-5xl md:text-7xl font-bold leading-tight"
            >
              Launch ads at{' '}
              <span className="bg-gradient-to-r from-quantum-400 via-quantum-500 to-green-400 bg-clip-text text-transparent">
                quantum speed
              </span>
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mt-6 text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto"
            >
              The First Autonomous Ad Engine. Transform your website into high-performing ads with Quantum Intelligence
              — automatic extraction, compliance verification, and one-click publishing.
            </motion.p>

            {/* CTA */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <Link href="/studio">
                <motion.button
                  className="px-8 py-4 bg-gradient-to-r from-quantum-500 to-quantum-600 text-black text-lg font-semibold rounded-xl flex items-center gap-2 shadow-lg shadow-quantum-500/25"
                  whileHover={{ scale: 1.02, boxShadow: '0 0 40px rgba(34, 197, 94, 0.4)' }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Zap className="w-5 h-5" />
                  Launch My Ads
                </motion.button>
              </Link>
              <Link href="/dashboard">
                <motion.button
                  className="px-8 py-4 border border-zinc-700 hover:border-zinc-500 text-white text-lg font-medium rounded-xl flex items-center gap-2"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  View Demo
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
            </motion.div>

            {/* Stats */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-16 flex justify-center gap-8 md:gap-16"
            >
              <StatItem value={60} suffix="s" label="To Launch" />
              <StatItem value={23} label="Quantum Tools" />
              <StatItem value={2.3} suffix="x" label="Avg ROAS" />
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* How It Works */}
      <section className="relative px-6 py-20 border-t border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white">How Quantum Intelligence Works</h2>
            <p className="mt-4 text-zinc-400 max-w-2xl mx-auto">One input. Full campaign. You approve, we execute.</p>
          </motion.div>

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
            ].map((item, i) => (
              <StepCard key={item.step} {...item} delay={i * 0.1} />
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative px-6 py-20 border-t border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white">23 Quantum-Powered Tools</h2>
            <p className="mt-4 text-zinc-400 max-w-2xl mx-auto">
              All running automatically behind the scenes. Access individually when you need more control.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Globe,
                title: 'Quantum Extractor',
                description: 'Extracts brand claims, value propositions, and messaging from any website.',
                href: '/dashboard',
              },
              {
                icon: Sparkles,
                title: 'Quantum Hooks',
                description: 'Generates high-converting headlines using proven persuasion patterns.',
                href: '/hooks',
              },
              {
                icon: TrendingUp,
                title: 'Quantum Score',
                description: 'Predicts ad performance before you spend a dollar.',
                href: '/predict',
              },
              {
                icon: Shield,
                title: 'Quantum Sentinel',
                description: 'Monitors brand sentiment 24/7. Auto-pauses ads during PR crises.',
                href: '/sentiment',
              },
              {
                icon: DollarSign,
                title: 'Quantum Budget',
                description: 'Simulates budget scenarios with expected CPA and ROAS.',
                href: '/budget',
              },
              {
                icon: Users,
                title: 'Quantum Audience',
                description: 'Suggests optimal targeting based on your product and goals.',
                href: '/audience',
              },
              {
                icon: Video,
                title: 'Quantum Video',
                description: 'Generates UGC-style video ads with AI avatars.',
                href: '/video',
              },
              {
                icon: BarChart3,
                title: 'Quantum Radar',
                description: 'Analyzes competitor ads and identifies winning patterns.',
                href: '/intel',
              },
              {
                icon: Target,
                title: 'Quantum Platform',
                description: 'Recommends the best platform for your product and budget.',
                href: '/platforms',
              },
            ].map((feature, i) => (
              <FeatureCard key={feature.title} {...feature} delay={i * 0.05} />
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mt-8 text-center"
          >
            <Link
              href="/tools"
              className="inline-flex items-center gap-2 text-quantum-400 hover:text-quantum-300 transition group"
            >
              View all 23 tools
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Why Quantum */}
      <section className="relative px-6 py-20 border-t border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Why Quantum Intelligence?</h2>
              <p className="text-zinc-400 mb-8">
                Not just another ad generator. Quantum Multi-Model Intelligence orchestrates 23 specialized tools to
                create, score, publish, and monitor your ads automatically.
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
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.3, delay: i * 0.1 }}
                    className="flex items-center gap-3"
                  >
                    <CheckCircle className="w-5 h-5 text-quantum-400 flex-shrink-0" />
                    <span className="text-zinc-300">{item}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-8"
            >
              <h3 className="text-lg font-semibold text-white mb-6">Quantum vs. Alternatives</h3>

              <div className="space-y-4">
                {[
                  { name: 'ChatGPT', note: 'Copy ideas only' },
                  { name: 'Jasper', note: 'No publishing' },
                  { name: 'AdCreative.ai', note: 'No monitoring' },
                  { name: 'Ad Agency', note: '$5,000+/month' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between py-3 border-b border-zinc-800">
                    <span className="text-zinc-400">{item.name}</span>
                    <span className="text-zinc-500">{item.note}</span>
                  </div>
                ))}
                <motion.div
                  className="flex items-center justify-between py-3 bg-quantum-500/10 rounded-lg px-4 -mx-4"
                  animate={{
                    boxShadow: [
                      '0 0 0 rgba(34, 197, 94, 0)',
                      '0 0 20px rgba(34, 197, 94, 0.1)',
                      '0 0 0 rgba(34, 197, 94, 0)',
                    ],
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <span className="text-quantum-400 font-medium">BrandTruth AI</span>
                  <span className="text-quantum-400">End-to-end automation</span>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative px-6 py-24 border-t border-zinc-800">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl mx-auto text-center"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Ready to launch at quantum speed?</h2>
          <p className="text-xl text-zinc-400 mb-8">Enter your URL. Get ads in 60 seconds. No credit card required.</p>
          <Link href="/studio">
            <motion.button
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-quantum-500 to-quantum-600 text-black text-lg font-semibold rounded-xl shadow-lg shadow-quantum-500/25"
              whileHover={{ scale: 1.02, boxShadow: '0 0 40px rgba(34, 197, 94, 0.4)' }}
              whileTap={{ scale: 0.98 }}
            >
              <Zap className="w-5 h-5" />
              Start Free
            </motion.button>
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 px-6 py-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-quantum-500/20 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-quantum-400" />
                </div>
                <span className="font-bold text-white">BrandTruth AI</span>
              </div>
              <p className="text-sm text-zinc-500">Part of the QuantumLaunch family.</p>
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

          <div className="mt-12 pt-8 border-t border-zinc-800 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-zinc-500">BrandTruth AI by QuantumLaunch</p>
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
