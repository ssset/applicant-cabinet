// src/contexts/AuthContext.tsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import { authAPI, userAPI } from '../services/api';
import { useToast } from '@/components/ui/use-toast';

interface User {
  id?: number;
  email?: string;
  role: 'applicant' | 'moderator' | 'admin_app' | 'admin_org' | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        // Запрашиваем полные данные пользователя
        const userData = await userAPI.getCurrentUser();
        setUser({
          id: userData.id,
          email: userData.email,
          role: userData.role,
        });
        localStorage.setItem('user_email', userData.email);
      } catch (error) {
        console.error('Error checking authentication:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_email');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      setLoading(true);
      const data = await authAPI.login(email, password);

      localStorage.setItem('access_token', data.access);
      localStorage.setItem('user_role', data.role);
      localStorage.setItem('user_email', email);

      // Получаем актуальные данные пользователя
      const userData = await userAPI.getCurrentUser();
      setUser({
        id: userData.id,
        email: userData.email,
        role: userData.role,
      });

      toast({
        title: 'Успешная авторизация',
        description: 'Добро пожаловать в Applicant Portal',
      });
    } catch (error) {
      console.error('Login error:', error);
      toast({
        variant: 'destructive',
        title: 'Ошибка входа',
        description: error instanceof Error ? error.message : 'Произошла неизвестная ошибка',
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signOut = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_email');
    setUser(null);
    toast({
      title: 'Выход из системы',
      description: 'Вы успешно вышли из системы',
    });
  };

  return (
      <AuthContext.Provider value={{
        user,
        loading,
        signIn,
        signOut,
        isAuthenticated: !!user
      }}>
        {children}
      </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};