import React, { createContext, useContext, useState, useEffect } from 'react';

export interface UserProfile {
  name: string;
  email: string;
  location?: string;
  primaryCrop?: string;
  farmType?: string;
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (email: string, name?: string) => void;
  signup: (profile: UserProfile) => void;
  logout: () => void;
  updateProfile: (profile: Partial<UserProfile>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_STORAGE_KEY = 'agrinexus_user_session';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const saved = localStorage.getItem(AUTH_STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }, [user]);

  const login = (email: string, name?: string) => {
    const newUser: UserProfile = {
      name: name || email.split('@')[0],
      email,
      primaryCrop: 'Rice',
      farmType: 'Commercial Agronomy'
    };
    setUser(newUser);
  };

  const signup = (profile: UserProfile) => {
    setUser(profile);
  };

  const logout = () => {
    setUser(null);
  };

  const updateProfile = (updated: Partial<UserProfile>) => {
    if (user) {
      setUser({ ...user, ...updated });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        updateProfile
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
