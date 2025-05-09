// src/pages/registerPage.tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import RegisterForm from '@/components/auth/RegisterForm';
import Navbar from '@/components/common/Navbar';
import { motion } from 'framer-motion';

const RegisterPage = () => {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // Если пользователь уже авторизован, перенаправляем на /dashboard
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    return (
        <div className="min-h-screen bg-appBackground flex flex-col">
            <Navbar />
            <motion.div
                className="flex flex-grow items-center justify-center px-4 py-12"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
            >
                <RegisterForm />
            </motion.div>
        </div>
    );
};

export default RegisterPage;