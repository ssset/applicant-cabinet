import React from "react";
import { Link, Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { ArrowRight, LogIn, UserPlus, School } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const LandingPage: React.FC = () => {
    const { user, loading } = useAuth();

    if (!loading && user) {
        return <Navigate to="/dashboard" replace />;
    }

    if (loading) {
        return <div className="p-6 text-center">Загрузка...</div>;
    }

    return (
        <div className="landing-page-wrapper" style={{ minHeight: '100vh', overflowY: 'auto' }}>
            <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex flex-col">
                {/* Navbar */}
                <header className="bg-white/80 backdrop-blur-sm shadow-sm py-4 sticky top-0 z-10">
                    <div className="container mx-auto px-4 flex justify-between items-center">
                        <div className="text-2xl font-bold text-blue-600">Applicant Portal</div>
                        <div className="flex gap-2">
                            <Button
                                asChild
                                variant="ghost"
                                size="sm"
                                className="text-blue-600 hover:text-blue-600/80"
                            >
                                <Link to="/login">
                                    <LogIn className="w-4 h-4 mr-2" />
                                    Войти
                                </Link>
                            </Button>
                            <Button
                                asChild
                                variant="outline"
                                size="sm"
                                className="text-blue-600 border-blue-600 hover:bg-blue-600/10"
                            >
                                <Link to="/register">
                                    <UserPlus className="w-4 h-4 mr-2" />
                                    Регистрация
                                </Link>
                            </Button>
                        </div>
                    </div>
                </header>

                {/* Hero Section */}
                <motion.section
                    className="container mx-auto px-4 py-16 flex flex-col lg:flex-row items-center gap-12"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                >
                    <div className="lg:w-1/2 space-y-6">
                        <motion.h1
                            className="text-4xl md:text-5xl font-bold text-gray-800 leading-tight"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.2, duration: 0.8 }}
                        >
                            Современная платформа для подачи заявлений в учебные заведения
                        </motion.h1>

                        <motion.p
                            className="text-lg text-gray-600"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.4, duration: 0.8 }}
                        >
                            Упростите процесс подачи и управления заявлениями абитуриентов с помощью нашей цифровой
                            платформы
                        </motion.p>

                        <motion.div
                            className="pt-4 flex flex-col sm:flex-row gap-4"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.6, duration: 0.8 }}
                        >
                            <Button
                                asChild
                                size="lg"
                                className="bg-blue-600 hover:bg-blue-600/90 text-white"
                            >
                                <Link to="/register">
                                    Начать как абитуриент
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Link>
                            </Button>
                            <Button
                                asChild
                                variant="outline"
                                size="lg"
                                className="border-2 border-blue-600 text-blue-600 hover:bg-blue-600/10"
                            >
                                <Link to="/institutions-apply">
                                    <School className="mr-2 h-5 w-5" />
                                    Подать заявку от учебного заведения
                                </Link>
                            </Button>
                        </motion.div>
                    </div>

                    <motion.div
                        className="lg:w-1/2"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4, duration: 0.8 }}
                    >
                        <div className="rounded-xl bg-white shadow-xl p-4 border border-gray-100 overflow-hidden">
                            <img
                                src="https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                                alt="Студент работает с заявлением онлайн"
                                className="w-full h-[300px] object-cover rounded shadow-lg"
                            />
                            <div className="bg-gradient-to-r from-blue-600/20 to-purple-100 mt-6 p-4 rounded-lg">
                                <h3 className="font-semibold text-gray-800">Современный подход к поступлению</h3>
                                <p className="text-sm text-gray-600 mt-1">
                                    Подайте заявление онлайн, следите за статусом и общайтесь с приемной комиссией в
                                    одном месте
                                </p>
                            </div>
                        </div>
                    </motion.div>
                </motion.section>

                {/* Features */}
                <section className="bg-gray-50 py-16">
                    <div className="container mx-auto px-4">
                        <h2 className="text-3xl font-bold text-center mb-12">Наши преимущества</h2>

                        <div className="grid md:grid-cols-3 gap-8">
                            <FeatureCard
                                title="Для абитуриентов"
                                description="Подача заявлений онлайн в любое учебное заведение на платформе. Отслеживание статуса заявок в реальном времени."
                                icon="📝"
                                delay={0.2}
                            />
                            <FeatureCard
                                title="Для учебных заведений"
                                description="Удобный интерфейс управления заявлениями. Эффективная коммуникация с абитуриентами."
                                icon="🏫"
                                delay={0.4}
                            />
                            <FeatureCard
                                title="Безопасность и надежность"
                                description="Защита персональных данных и документов. Надежное хранение всей информации."
                                icon="🔐"
                                delay={0.6}
                            />
                        </div>
                    </div>
                </section>

                {/* Institution Application CTA */}
                <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-16">
                    <div className="container mx-auto px-4 text-center">
                        <h2 className="text-3xl font-bold mb-4">Для учебных заведений</h2>
                        <p className="max-w-2xl mx-auto mb-8 text-white/90">
                            Хотите упростить процесс приема абитуриентов? Присоединяйтесь к нашей платформе и получите
                            доступ к современным инструментам управления заявлениями.
                        </p>
                        <Button
                            asChild
                            size="lg"
                            variant="secondary"
                            className="bg-white text-blue-600 hover:bg-gray-100"
                        >
                            <Link to="/institutions-apply">
                                <School className="mr-2 h-5 w-5" />
                                Подать заявку на регистрацию учебного заведения
                            </Link>
                        </Button>
                    </div>
                </section>

                {/* Footer */}
                <footer className="bg-gray-800 text-white py-12">
                    <div className="container mx-auto px-4">
                        <div className="flex flex-col md:flex-row justify-between">
                            <div className="mb-8 md:mb-0">
                                <h3 className="text-xl font-bold mb-4">Applicant Portal</h3>
                                <p className="text-gray-400 max-w-md">
                                    Современная платформа для цифровизации процесса поступления в учебные заведения.
                                </p>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
                                <div>
                                    <h4 className="text-lg font-semibold mb-4">Ресурсы</h4>
                                    <ul className="space-y-2">
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                Документация
                                            </Link>
                                        </li>
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                FAQ
                                            </Link>
                                        </li>
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                Поддержка
                                            </Link>
                                        </li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="text-lg font-semibold mb-4">Компания</h4>
                                    <ul className="space-y-2">
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                О нас
                                            </Link>
                                        </li>
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                Контакты
                                            </Link>
                                        </li>
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                Карьера
                                            </Link>
                                        </li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="text-lg font-semibold mb-4">Правовая информация</h4>
                                    <ul className="space-y-2">
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                Условия использования
                                            </Link>
                                        </li>
                                        <li>
                                            <Link to="#" className="text-gray-400 hover:text-white transition-colors">
                                                Политика конфиденциальности
                                            </Link>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
                            <p>© {new Date().getFullYear()} Applicant Portal. Все права защищены.</p>
                        </div>
                    </div>
                </footer>
            </div>
        </div>
    );
};

// Feature Card Component
const FeatureCard: React.FC<{
    title: string;
    description: string;
    icon: string;
    delay?: number;
}> = ({ title, description, icon, delay = 0 }) => {
    return (
        <motion.div
            className="bg-white rounded-xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-shadow"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.5 }}
            viewport={{ once: true }}
        >
            <div className="text-3xl mb-4">{icon}</div>
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-gray-600">{description}</p>
        </motion.div>
    );
};

export default LandingPage;