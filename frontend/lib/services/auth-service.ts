/**
 * Authentication Service
 * Handles user registration, login, and session management
 */

import { API_BASE_URL } from '@/lib/env';

export interface AuthUser {
  id: string;
  username: string;
  wallet_address: string;
  email?: string;
  bio?: string;
  profile_picture?: string;
  role: string;
  onboarding_complete: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  access_token?: string;
  refresh_token?: string;
  user?: AuthUser;
  onboarding_complete?: boolean;
}

export interface NonceResponse {
  nonce: string;
  message: string;
}

class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private currentUser: AuthUser | null = null;

  constructor() {
    // Load tokens from localStorage on init
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
      const userJson = localStorage.getItem('user');
      if (userJson) {
        try {
          this.currentUser = JSON.parse(userJson);
        } catch (e) {
          console.error('Failed to parse user from localStorage', e);
        }
      }
    }
  }

  /**
   * Request a nonce for wallet authentication
   */
  async getNonce(walletAddress: string): Promise<NonceResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/nonce`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        wallet_address: walletAddress,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get nonce');
    }

    return await response.json();
  }

  /**
   * Register a new user
   */
  async register(
    walletAddress: string,
    username: string,
    signature: string,
    email?: string,
    bio?: string,
    profilePicture?: string
  ): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        wallet_address: walletAddress,
        username,
        signature,
        email,
        bio,
        profile_picture: profilePicture,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data: AuthResponse = await response.json();

    if (data.success && data.access_token && data.user) {
      this.setSession(data.access_token, data.refresh_token || null, data.user);
    }

    return data;
  }

  /**
   * Login with wallet
   */
  async login(walletAddress: string, signature: string): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        wallet_address: walletAddress,
        signature,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data: AuthResponse = await response.json();

    if (data.success && data.access_token && data.user) {
      this.setSession(data.access_token, data.refresh_token || null, data.user);
    }

    return data;
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<AuthUser> {
    if (!this.accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.clearSession();
        throw new Error('Session expired');
      }
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get user');
    }

    const user: AuthUser = await response.json();
    this.currentUser = user;
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(user));
    }

    return user;
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: {
    username?: string;
    email?: string;
    bio?: string;
    profile_picture?: string;
  }): Promise<AuthUser> {
    if (!this.accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update profile');
    }

    const user: AuthUser = await response.json();
    this.currentUser = user;
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(user));
    }

    return user;
  }

  /**
   * Complete onboarding
   */
  async completeOnboarding(
    acceptedTerms: boolean,
    preferredNetwork: string = 'sepolia',
    enableNotifications: boolean = true
  ): Promise<AuthResponse> {
    if (!this.accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/onboarding/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify({
        accepted_terms: acceptedTerms,
        preferred_network: preferredNetwork,
        enable_notifications: enableNotifications,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to complete onboarding');
    }

    const data: AuthResponse = await response.json();

    if (data.user) {
      this.currentUser = data.user;
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(data.user));
      }
    }

    return data;
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    if (this.accessToken) {
      try {
        await fetch(`${API_BASE_URL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${this.accessToken}`,
          },
        });
      } catch (e) {
        console.error('Logout request failed', e);
      }
    }

    this.clearSession();
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.accessToken !== null && this.currentUser !== null;
  }

  /**
   * Get current user (from cache)
   */
  getUser(): AuthUser | null {
    return this.currentUser;
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Set session data
   */
  private setSession(accessToken: string, refreshToken: string | null, user: AuthUser): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.currentUser = user;

    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', accessToken);
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
      }
      localStorage.setItem('user', JSON.stringify(user));
    }
  }

  /**
   * Clear session data
   */
  private clearSession(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.currentUser = null;

    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
