import React, { createContext, useContext, useState, useEffect } from 'react';

export type UserRole = 'viewer' | 'operator' | 'admin' | 'carrier';

export interface User {
  email: string;
  role: UserRole;
  name: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  hasRole: (role: UserRole | UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('truthforge_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('truthforge_user');
      }
    }
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    // Mock authentication - in production, this would call the backend API
    const mockUsers: Record<string, { password: string; role: UserRole; name: string }> = {
      'viewer@truthforge.io': { password: 'viewer123', role: 'viewer', name: 'View User' },
      'operator@truthforge.io': { password: 'operator123', role: 'operator', name: 'Operator User' },
      'admin@truthforge.io': { password: 'admin123', role: 'admin', name: 'Admin User' },
      'carrier@truthforge.io': { password: 'carrier123', role: 'carrier', name: 'Carrier User' },
    };

    const mockUser = mockUsers[email];
    if (mockUser && mockUser.password === password) {
      const authenticatedUser: User = {
        email,
        role: mockUser.role,
        name: mockUser.name,
      };
      setUser(authenticatedUser);
      localStorage.setItem('truthforge_user', JSON.stringify(authenticatedUser));
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('truthforge_user');
    localStorage.removeItem('truthforge_wallet');
  };

  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    const roles = Array.isArray(role) ? role : [role];
    return roles.includes(user.role);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
