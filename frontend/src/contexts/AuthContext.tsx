// src/contexts/AuthContext.tsx
import React, { createContext, useState, useEffect, useContext } from 'react'; // Добавляем useContext
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
      try {
        const token = localStorage.getItem('access_token');
        const storedEmail = localStorage.getItem('user_email'); // Новое: читаем email
        const role = localStorage.getItem('user_role');

        if (token) {
          // Запрашиваем полные данные пользователя через /users/me/
          const userData = await userAPI.getCurrentUser();
          console.log('Fetched user data:', userData); // Отладка
          setUser({
            id: userData.id,
            email: userData.email,
            role: userData.role,
          });
          // Сохраняем email в localStorage
          localStorage.setItem('user_email', userData.email);
        } else if (storedEmail && role) {
          // Если токена нет, но есть email и role, используем их
          setUser({
            email: storedEmail,
            role: role as 'applicant' | 'moderator' | 'admin_app' | 'admin_org',
          });
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_email');
        setUser(null);
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
      localStorage.setItem('user_email', email); // Сохраняем email из формы логина

      // Запрашиваем полные данные пользователя
      const userData = await userAPI.getCurrentUser();
      console.log('Fetched user data after login:', userData);
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
    localStorage.removeItem('user_email'); // Удаляем email
    setUser(null);
    toast({
      title: 'Выход из системы',
      description: 'Вы успешно вышли из системы',
    });
  };

  return (
      <AuthContext.Provider value={{ user, loading, signIn, signOut, isAuthenticated: !!user }}>
        {loading ? <div className="flex justify-center items-center h-screen">Загрузка...</div> : children}
      </AuthContext.Provider>
  );
};

// Добавляем хук useAuth
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};