'use client';

import { Suspense, useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Zap,
  Mail,
  Lock,
  ArrowRight,
  Loader2,
  Github,
  Chrome
} from 'lucide-react';

// Wrapper component to handle Suspense boundary for useSearchParams
function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') || '/campaigns';
  const error = searchParams.get('error');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(error);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setAuthError(null);

    try {
      const result = await signIn('credentials', {
        email,
        password,
        redirect: false,
        callbackUrl,
      });

      if (result?.error) {
        setAuthError('Invalid credentials. Please try again.');
      } else if (result?.ok) {
        router.push(callbackUrl);
      }
    } catch (err) {
      setAuthError('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthSignIn = (provider: string) => {
    signIn(provider, { callbackUrl });
  };

  return (
    <div className="min-h-screen bg-[#050505] flex flex-col">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-quantum-500/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px] animate-pulse delay-1000" />
      </div>

      {/* Header */}
      <header className="relative z-10 p-6">
        <Link href="/" className="flex items-center gap-2 text-white hover:text-quantum-400 transition-colors w-fit">
          <Zap className="w-8 h-8 text-quantum-500" />
          <span className="text-xl font-bold">BrandTruth AI</span>
        </Link>
      </header>

      {/* Main content */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Login card */}
          <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-8 backdrop-blur-xl">
            {/* Header */}
            <div className="text-center mb-8">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-quantum-500 to-quantum-600 flex items-center justify-center shadow-lg shadow-quantum-500/25"
              >
                <Zap className="w-8 h-8 text-white" />
              </motion.div>
              <h1 className="text-2xl font-bold text-white mb-2">Welcome back</h1>
              <p className="text-zinc-400">Sign in to your BrandTruth AI account</p>
            </div>

            {/* Error message */}
            {authError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm"
              >
                {authError}
              </motion.div>
            )}

            {/* Login form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email field */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    required
                    className="w-full pl-11 pr-4 py-3 bg-zinc-800/50 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-quantum-500 focus:ring-1 focus:ring-quantum-500 transition-colors"
                  />
                </div>
              </div>

              {/* Password field */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    className="w-full pl-11 pr-4 py-3 bg-zinc-800/50 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-quantum-500 focus:ring-1 focus:ring-quantum-500 transition-colors"
                  />
                </div>
              </div>

              {/* Submit button */}
              <motion.button
                type="submit"
                disabled={isLoading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-3 px-4 bg-gradient-to-r from-quantum-500 to-quantum-600 text-white font-semibold rounded-lg shadow-lg shadow-quantum-500/25 hover:shadow-quantum-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Sign in
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-zinc-800" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-zinc-900 text-zinc-500">or continue with</span>
              </div>
            </div>

            {/* OAuth buttons */}
            <div className="grid grid-cols-2 gap-3">
              <motion.button
                type="button"
                onClick={() => handleOAuthSignIn('google')}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="py-3 px-4 bg-zinc-800/50 border border-zinc-700 rounded-lg text-white font-medium hover:bg-zinc-800 hover:border-zinc-600 transition-colors flex items-center justify-center gap-2"
              >
                <Chrome className="w-5 h-5" />
                Google
              </motion.button>
              <motion.button
                type="button"
                onClick={() => handleOAuthSignIn('github')}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="py-3 px-4 bg-zinc-800/50 border border-zinc-700 rounded-lg text-white font-medium hover:bg-zinc-800 hover:border-zinc-600 transition-colors flex items-center justify-center gap-2"
              >
                <Github className="w-5 h-5" />
                GitHub
              </motion.button>
            </div>

            {/* Demo note */}
            <div className="mt-6 p-4 bg-quantum-500/5 border border-quantum-500/20 rounded-lg">
              <p className="text-sm text-zinc-400">
                <span className="text-quantum-400 font-medium">Demo mode:</span> Enter any email and password to create an account or sign in.
              </p>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center mt-6 text-zinc-500 text-sm">
            Don&apos;t have an account?{' '}
            <span className="text-quantum-400">Sign in to create one automatically</span>
          </p>
        </motion.div>
      </main>
    </div>
  );
}

// Loading fallback for Suspense
function LoginFallback() {
  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-quantum-500 animate-spin" />
    </div>
  );
}

// Main page component with Suspense boundary
export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginContent />
    </Suspense>
  );
}
