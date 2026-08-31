/**
 * Simple Auth Context - Hardcoded Credentials
 * For hackathon demo - easy judge access
 */

import { createContext, useContext, useState, ReactNode } from 'react';

interface AuthContextType {
  user: { username: string } | null;
  loading: boolean;
  signIn: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Hardcoded credentials for hackathon demo
const DEMO_CREDENTIALS = {
  username: 'Admin123',
  password: 'Hackathon123'
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<{ username: string } | null>(null);
  const [loading] = useState(false);

  const signIn = async (username: string, password: string): Promise<boolean> => {
    // Simple credential check
    if (username === DEMO_CREDENTIALS.username && password === DEMO_CREDENTIALS.password) {
      setUser({ username: DEMO_CREDENTIALS.username });
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
