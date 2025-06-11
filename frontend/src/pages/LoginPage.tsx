import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import LoginForm from '@/components/auth/LoginForm';
import Navbar from '@/components/common/Navbar';
import { motion } from 'framer-motion';
import LoadingSpinner from '@/components/common/LoadingSpinner'; // Добавьте компонент спиннера

const LoginPage = () => {
    const { isAuthenticated, loading } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        // Перенаправляем только после завершения загрузки
        if (!loading && isAuthenticated) {
            // Проверяем текущий путь, чтобы избежать лишних перенаправлений
            if (location.pathname === '/login') {
                navigate('/dashboard', { replace: true });
            }
        }
    }, [isAuthenticated, loading, navigate, location]);

    // Показываем лоадер во время проверки аутентификации
    if (loading) {
        return (
            <div className="min-h-screen bg-appBackground flex flex-col">
                <Navbar />
                <div className="flex-grow flex items-center justify-center">
                    <LoadingSpinner />
                </div>
            </div>
        );
    }

    // Если пользователь уже аутентифицирован, ничего не показываем
    // (useEffect уже выполнит перенаправление)
    if (isAuthenticated) {
        return null;
    }

    return (
        <div className="min-h-screen bg-appBackground flex flex-col">
            <Navbar />
            <motion.div
                className="flex flex-grow items-center justify-center px-4 py-12"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
            >
                <LoginForm />
            </motion.div>
        </div>
    );
};

export default LoginPage;