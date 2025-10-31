"use client";

/**
 * User Onboarding Page - Redesigned with Landing + Dashboard Theme
 * Handles wallet connection, registration, and initial setup
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion'; // Only motion is used
import { Check, Wallet, User, Settings, Sparkles, ShieldCheck, ArrowRight, AlertCircle } from 'lucide-react';
import { useMetaMask } from '@/lib/hooks/use-metamask';
import { authService } from '@/lib/services/auth-service';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardBackground } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { BackgroundGrid } from '@/components/visual/background-grid';

// Step indicator component with icons
function StepIndicator({ currentStep }: { currentStep: 'connect' | 'register' | 'complete' }) {
  const steps = [
    { id: 'connect', label: 'Connect Wallet', icon: Wallet },
    { id: 'register', label: 'Create Profile', icon: User },
    { id: 'complete', label: 'Setup Preferences', icon: Settings },
  ];

  const currentIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="mb-12">
      <div className="flex items-center justify-between max-w-2xl mx-auto">
        {steps.map((step, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index === currentIndex;
          const Icon = step.icon;
          
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-3 flex-1">
                <motion.div
                  initial={false}
                  animate={{
                    scale: isCurrent ? 1.1 : 1,
                  }}
                  className={`relative flex items-center justify-center w-14 h-14 rounded-full border-2 transition-all ${
                    isComplete
                      ? 'bg-success/20 border-success text-success'
                      : isCurrent
                      ? 'bg-accent/20 border-accent text-accent shadow-accent-ring'
                      : 'bg-white/5 border-white/10 text-muted'
                  }`}
                >
                  {isComplete ? (
                    <Check className="w-6 h-6" />
                  ) : (
                    <Icon className="w-6 h-6" />
                  )}
                </motion.div>
                <div className="text-center">
                  <p className={`text-sm font-medium ${isCurrent ? 'text-foreground' : 'text-muted'}`}>
                    {step.label}
                  </p>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-4 mb-8">
                  <div
                    className={`h-full transition-all duration-500 ${
                      isComplete ? 'bg-success' : 'bg-white/10'
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  const router = useRouter();
  const { address, isConnecting, connect, signMessage, isMetaMaskInstalled, error: walletError } = useMetaMask();

  const [step, setStep] = useState<'connect' | 'register' | 'complete'>('connect');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [preferredNetwork, setPreferredNetwork] = useState('sepolia');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Check if user is already authenticated
  useEffect(() => {
    if (authService.isAuthenticated()) {
      const user = authService.getUser();
      if (user?.onboarding_complete) {
        router.push('/dashboard');
      } else {
        setStep('complete');
      }
    }
  }, [router]);

  // Handle wallet connection
  const handleConnectWallet = async () => {
    setError(null);
    const connectedAddress = await connect();
    if (connectedAddress) {
      // Try login, if user not found, switch to registration
      try {
        await handleLogin(connectedAddress);
      } catch (err) {
        const error = err as Error;
        if (error.message.includes('User not found')) {
          setStep('register');
          setError(null);
        } else if (error.message.includes('Nonce expired')) {
          setError('Session expired. Please reconnect your wallet.');
        } else if (error.message.includes('No nonce found')) {
          setError('Session expired. Please reconnect your wallet.');
        } else if (error.message.includes('Invalid signature')) {
          setError('Signature verification failed. Please try again.');
        } else if (error.message.includes('Account is disabled')) {
          setError('Your account is disabled. Contact support.');
        } else {
          setError(error.message || 'Login failed');
        }
      }
    }
  };

  // Handle login
  const handleLogin = async (walletAddress: string) => {
    setLoading(true);
    setError(null);
    try {
      // Get nonce
      const { message } = await authService.getNonce(walletAddress);
      // Sign message - pass address directly to avoid race condition
      const signature = await signMessage(message, walletAddress);
      if (!signature) {
        throw new Error('Failed to sign message');
      }
      // Login
      const response = await authService.login(walletAddress, signature);
      if (response.success) {
        if (response.onboarding_complete) {
          router.push('/dashboard');
        } else {
          setStep('complete');
        }
      } else {
        throw new Error(response.message || 'Login failed');
      }
    } catch (err) {
      const error = err as Error;
      // If user not found, propagate error to handleConnectWallet
      if (error.message.includes('User not found')) {
        throw error;
      }
      if (error.message.includes('Nonce expired')) {
        setError('Session expired. Please reconnect your wallet.');
      } else if (error.message.includes('No nonce found')) {
        setError('Session expired. Please reconnect your wallet.');
      } else if (error.message.includes('Invalid signature')) {
        setError('Signature verification failed. Please try again.');
      } else if (error.message.includes('Account is disabled')) {
        setError('Your account is disabled. Contact support.');
      } else {
        setError(error.message || 'Login failed');
      }
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle registration
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!address) {
      setError('Please connect your wallet first');
      return;
    }

    if (!username.trim()) {
      setError('Username is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Get nonce
      const { message } = await authService.getNonce(address);

      // Sign message - pass address directly to avoid race condition
      const signature = await signMessage(message, address);
      if (!signature) {
        throw new Error('Failed to sign message');
      }

      // Register
      const response = await authService.register(
        address,
        username.trim(),
        signature,
        email.trim() || undefined,
        bio.trim() || undefined
      );

      if (response.success) {
        setStep('complete');
      }
    } catch (err: unknown) {
      console.error('Registration error:', err);
      setError((err as Error).message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  // Handle onboarding completion
  const handleCompleteOnboarding = async () => {
    if (!acceptedTerms) {
      setError('You must accept the terms of service to continue');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await authService.completeOnboarding(acceptedTerms, preferredNetwork, true);

      router.push('/dashboard');
    } catch (err: unknown) {
      console.error('Complete onboarding error:', err);
      setError((err as Error).message || 'Failed to complete onboarding');
    } finally {
      setLoading(false);
    }
  };

  // Render MetaMask installation prompt
  if (!isMounted) return null;
  if (!isMetaMaskInstalled) {
    return (
      <div className="relative min-h-screen overflow-hidden">
        <BackgroundGrid />
        <div className="relative min-h-screen flex items-center justify-center px-4 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-lg w-full"
          >
            <Card>
              <CardBackground className="bg-gold/20" />
              <CardContent className="p-12 text-center">
                <div className="mb-8 flex justify-center">
                  <div className="w-20 h-20 rounded-full bg-gold/20 flex items-center justify-center">
                    <Wallet className="w-10 h-10 text-gold" />
                  </div>
                </div>
                <Badge variant="gold" className="mb-6">
                  MetaMask Required
                </Badge>
                <h2 className="text-3xl font-bold mb-4">Install MetaMask</h2>
                <p className="text-muted mb-8 text-lg">
                  WalletMind requires MetaMask to manage your Web3 wallet and sign transactions securely.
                </p>
                <Button
                  asChild
                  className="w-full bg-gold text-black hover:bg-gold/90"
                >
                  <a
                    href="https://metamask.io/download/"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Install MetaMask
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    );
  }

  // Render wallet connection step
  if (step === 'connect') {
    return (
      <div className="relative min-h-screen overflow-hidden">
        <BackgroundGrid />
        <div className="relative min-h-screen flex items-center justify-center px-4 py-12">
          <div className="max-w-4xl w-full">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center mb-12"
            >
              <Badge variant="gold" className="mb-6 text-sm">
                <Sparkles className="w-3 h-3" />
                Autonomous Wallet Intelligence
              </Badge>
              <h1 className="text-5xl font-bold mb-4">
                Welcome to <span className="text-gradient">WalletMind</span>
              </h1>
              <p className="text-xl text-muted max-w-2xl mx-auto">
                Connect your wallet to unlock AI-powered autonomous agents that think, negotiate, and execute transactions on your behalf.
              </p>
            </motion.div>

            <StepIndicator currentStep="connect" />

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              <Card className="max-w-2xl mx-auto">
                <CardBackground className="bg-accent/10" />
                <CardContent className="p-12">
                  {(error || walletError) && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      whileTap={{ scale: 0.98 }}
                      className="mb-6 p-4 bg-red-600/15 border border-red-500/40 rounded-lg flex items-start gap-3 shadow-lg"
                      role="alert"
                      aria-live="assertive"
                    >
                      <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" aria-hidden="true" />
                      <p className="text-sm text-red-100 font-semibold">{error || walletError}</p>
                    </motion.div>
                  )}

                  <div className="text-center mb-8">
                    <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4">
                      <Wallet className="w-8 h-8 text-accent" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Connect Your Wallet</h2>
                    <p className="text-muted">
                      Sign in securely with your MetaMask wallet to get started
                    </p>
                  </div>

                  <Button
                    onClick={handleConnectWallet}
                    disabled={isConnecting || loading}
                    aria-label="Connect MetaMask Wallet"
                    className="w-full h-14 text-lg bg-accent hover:bg-accent/90 text-black font-semibold focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {isConnecting || loading ? (
                      <>
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full mr-3"
                          aria-hidden="true"
                        />
                        <span className="sr-only">Connecting...</span>
                        Connecting...
                      </>
                    ) : (
                      <>
                        <Wallet className="w-5 h-5 mr-3" aria-hidden="true" />
                        Connect MetaMask
                      </>
                    )}
                  </Button>

                  <div className="mt-8 pt-6 border-t border-white/5 text-center text-sm text-muted">
                    <p className="mb-2">By connecting, you agree to our</p>
                    <div className="flex items-center justify-center gap-2">
                      <a href="/terms" className="text-accent hover:underline">Terms of Service</a>
                      <span>·</span>
                      <a href="/privacy" className="text-accent hover:underline">Privacy Policy</a>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="mt-12 max-w-2xl mx-auto grid grid-cols-3 gap-6">
                {[
                  { icon: ShieldCheck, label: 'Secure & Verified' },
                  { icon: Sparkles, label: 'AI-Powered Agents' },
                  { icon: Wallet, label: 'Self-Custodial' },
                ].map((feature, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + i * 0.1 }}
                    className="flex flex-col items-center text-center gap-2"
                  >
                    <feature.icon className="w-6 h-6 text-accent" />
                    <p className="text-sm text-muted">{feature.label}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  // Render registration step
  if (step === 'register') {
    return (
      <div className="relative min-h-screen overflow-hidden">
        <BackgroundGrid />
        <div className="relative min-h-screen flex items-center justify-center px-4 py-12">
          <div className="max-w-4xl w-full">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <StepIndicator currentStep="register" />

              <Card className="max-w-2xl mx-auto">
                <CardBackground className="bg-accent/10" />
                <CardHeader className="pb-6">
                  <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mb-4">
                    <User className="w-8 h-8 text-accent" />
                  </div>
                  <CardTitle className="text-3xl">Create Your Profile</CardTitle>
                  <CardDescription className="text-lg">
                    Tell us a bit about yourself to personalize your experience
                  </CardDescription>
                </CardHeader>

                <CardContent className="pb-12">
                  {address && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="mb-6 p-4 bg-success/10 border border-success/20 rounded-lg"
                    >
                      <p className="text-sm text-success flex items-center gap-2">
                        <Check className="w-4 h-4" />
                        Wallet connected: {address.slice(0, 6)}...{address.slice(-4)}
                      </p>
                    </motion.div>
                  )}

                  {error && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3"
                    >
                      <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                      <p className="text-sm text-red-200">{error}</p>
                    </motion.div>
                  )}

                  <form onSubmit={handleRegister} className="space-y-6">
                    <div>
                      <label htmlFor="username" className="block text-sm font-medium mb-2">
                        Username <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
                        placeholder="your_username"
                        required
                        minLength={3}
                        maxLength={50}
                      />
                    </div>

                    <div>
                      <label htmlFor="email" className="block text-sm font-medium mb-2">
                        Email <span className="text-muted text-xs">(optional)</span>
                      </label>
                      <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
                        placeholder="your@email.com"
                      />
                    </div>

                    <div>
                      <label htmlFor="bio" className="block text-sm font-medium mb-2">
                        Bio <span className="text-muted text-xs">(optional)</span>
                      </label>
                      <textarea
                        id="bio"
                        value={bio}
                        onChange={(e) => setBio(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all resize-none"
                        placeholder="Tell us about yourself..."
                        rows={3}
                        maxLength={500}
                      />
                      <p className="text-xs text-muted mt-1">{bio.length}/500 characters</p>
                    </div>

                    <Button
                      type="submit"
                      disabled={loading}
                      aria-label="Create Profile"
                      className="w-full h-14 text-lg bg-accent hover:bg-accent/90 text-black font-semibold focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full mr-3"
                            aria-hidden="true"
                          />
                          <span className="sr-only">Creating Profile...</span>
                          Creating Profile...
                        </>
                      ) : (
                        <>
                          Continue
                          <ArrowRight className="ml-2 w-5 h-5" aria-hidden="true" />
                        </>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  // Render onboarding completion step
  if (step === 'complete') {
    return (
      <div className="relative min-h-screen overflow-hidden">
        <BackgroundGrid />
        <div className="relative min-h-screen flex items-center justify-center px-4 py-12">
          <div className="max-w-4xl w-full">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <StepIndicator currentStep="complete" />

              <Card className="max-w-2xl mx-auto">
                <CardBackground className="bg-gold/10" />
                <CardHeader className="pb-6">
                  <div className="w-16 h-16 rounded-full bg-gold/20 flex items-center justify-center mb-4">
                    <Settings className="w-8 h-8 text-gold" />
                  </div>
                  <CardTitle className="text-3xl">Setup Preferences</CardTitle>
                  <CardDescription className="text-lg">
                    Configure your default settings to get started
                  </CardDescription>
                </CardHeader>

                <CardContent className="pb-12">
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3"
                    >
                      <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                      <p className="text-sm text-red-200">{error}</p>
                    </motion.div>
                  )}

                  <div className="space-y-8">
                    <div>
                      <label htmlFor="network" className="block text-sm font-medium mb-3">
                        Preferred Network
                      </label>
                      <select
                        id="network"
                        value={preferredNetwork}
                        onChange={(e) => setPreferredNetwork(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-all"
                      >
                        <option value="sepolia">Sepolia Testnet (Recommended)</option>
                        <option value="polygon-amoy">Polygon Amoy Testnet</option>
                        <option value="base-sepolia">Base Sepolia Testnet</option>
                        <option value="arbitrum-sepolia">Arbitrum Sepolia Testnet</option>
                      </select>
                      <p className="text-xs text-muted mt-2">
                        Start with a testnet to explore WalletMind risk-free
                      </p>
                    </div>

                    <div className="p-6 bg-white/5 border border-white/10 rounded-lg space-y-4">
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          id="terms"
                          checked={acceptedTerms}
                          onChange={(e) => setAcceptedTerms(e.target.checked)}
                          className="mt-1 w-4 h-4 rounded border-white/10 bg-white/5 text-accent focus:ring-accent focus:ring-offset-0"
                        />
                        <label htmlFor="terms" className="text-sm flex-1">
                          I agree to the{' '}
                          <a href="/terms" target="_blank" className="text-accent hover:underline">
                            Terms of Service
                          </a>{' '}
                          and{' '}
                          <a href="/privacy" target="_blank" className="text-accent hover:underline">
                            Privacy Policy
                          </a>
                          . I understand that WalletMind agents will execute transactions on my behalf based on
                          the configured rules and spending limits.
                        </label>
                      </div>
                    </div>

                    <Button
                      onClick={handleCompleteOnboarding}
                      disabled={loading || !acceptedTerms}
                      aria-label="Complete Onboarding"
                      className="w-full h-14 text-lg bg-gold hover:bg-gold/90 text-black font-semibold focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full mr-3"
                            aria-hidden="true"
                          />
                          <span className="sr-only">Finalizing...</span>
                          Finalizing...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-5 h-5 mr-3" aria-hidden="true" />
                          Launch Dashboard
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
