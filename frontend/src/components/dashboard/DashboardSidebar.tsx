import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { motion } from 'framer-motion';
import {
    LayoutDashboard,
    FileText,
    GraduationCap,
    MessageCircle,
    Settings,
    User,
    LogOut,
    Building,
    Users,
    School,
} from 'lucide-react';
import { useIsMobile } from '@/hooks/use-mobile';
import { Crown, Medal, Award } from "lucide-react";
import { useState, useEffect } from 'react';

export const DashboardSidebar = () => {
    const { user, signOut } = useAuth();
    const navigate = useNavigate();
    const isMobile = useIsMobile();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    useEffect(() => {
        if (isMobile) {
            setIsSidebarOpen(false);
        } else {
            setIsSidebarOpen(true);
        }
    }, [isMobile]);

    // Общие элементы меню для всех ролей
    const commonItems = [
        {
            icon: LayoutDashboard,
            text: 'Дашборд',
            path: '/dashboard',
            roles: ['applicant', 'moderator', 'admin_app', 'admin_org']
        },
        {
            icon: MessageCircle,
            text: 'Сообщения',
            path: '/messages',
            roles: ['applicant', 'moderator', 'admin_org']
        },
        {
            icon: Settings,
            text: 'Настройки',
            path: '/settings',
            roles: ['applicant', 'moderator', 'admin_app', 'admin_org']
        }
    ];

    // Элементы меню для абитуриента
    const applicantItems = [
        {
            icon: FileText,
            text: 'Мои заявки',
            path: '/applications',
            roles: ['applicant']
        },
        {
            icon: GraduationCap,
            text: 'Специальности',
            path: '/specialties',
            roles: ['applicant']
        },
        {
            icon: Crown,
            text: 'Лидерборд',
            path: '/leaderboard',
            roles: ['applicant']
        }
    ];

    // Элементы меню для модератора
    const moderatorItems = [
        {
            icon: FileText,
            text: 'Заявки',
            path: '/applications-manage',
            roles: ['moderator', 'admin_org']
        },
        {
            icon: Crown,
            text: 'Лидерборд',
            path: '/leaderboard',
            roles: ['applicant']
        }
    ];

    const adminOrgItems = [
        {
            icon: Users,
            text: 'Модераторы',
            path: '/moderators',
            roles: ['admin_org']
        },
        {
            icon: GraduationCap,
            text: 'Специальности',
            path: '/specialties',
            roles: ['admin_org']
        },
        {
            icon: Crown,
            text: 'Лидерборд',
            path: '/leaderboard',
            roles: ['admin_org']
        }
    ];

    const adminAppItems = [
        {
            icon: School,
            text: 'Учебные заведения',
            path: '/institutions',
            roles: ['admin_app']
        },
    ];

    // Объединяем все элементы меню в зависимости от роли
    const getSidebarItems = () => {
        let items = [...commonItems];

        if (user?.role === 'applicant') {
            items = [...items, ...applicantItems];
        } else if (user?.role === 'moderator') {
            items = [...items, ...moderatorItems];
        } else if (user?.role === 'admin_org') {
            items = [...items, ...moderatorItems, ...adminOrgItems];
        } else if (user?.role === 'admin_app') {
            items = [...items, ...adminAppItems];
        }

        return items.filter(item => item.roles.includes(user?.role || ''));
    };

    const sidebarItems = getSidebarItems();

    const sidebarVariants = {
        hidden: { x: -250 },
        visible: {
            x: 0,
            transition: {
                type: "spring",
                stiffness: 100,
                duration: 0.5
            }
        }
    };

    const listVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
                delayChildren: 0.3
            }
        }
    };

    const itemVariants = {
        hidden: { x: -20, opacity: 0 },
        visible: {
            x: 0,
            opacity: 1,
            transition: { duration: 0.3 }
        }
    };

    // Функция определения текста и роли для отображения
    const getRoleInfo = () => {
        switch(user?.role) {
            case 'applicant':
                return { text: 'Абитуриент', shortText: 'A' };
            case 'moderator':
                return { text: 'Модератор', shortText: 'M' };
            case 'admin_org':
                return { text: 'Администратор организации', shortText: 'A' };
            case 'admin_app':
                return { text: 'Администратор приложения', shortText: 'S' };
            default:
                return { text: 'Пользователь', shortText: 'П' };
        }
    };

    const roleInfo = getRoleInfo();

    // Обработчик выхода с перенаправлением
    const handleSignOut = () => {
        signOut();
        navigate('/login');
    };

    return (
        <>
            {/* Сайдбар с поддержкой свайпа только на мобильных */}
            <motion.div
                className="w-64 bg-white shadow-md h-screen flex flex-col fixed md:static z-40"
                variants={sidebarVariants}
                initial="hidden"
                animate={isSidebarOpen || !isMobile ? "visible" : "hidden"}
                drag={isMobile ? "x" : false} // Свайп только на мобильных
                dragConstraints={isMobile ? { left: 0, right: 0 } : false}
                dragElastic={isMobile ? 0.2 : 0}
                onDragEnd={isMobile ? (event, info) => {
                    if (info.offset.x > 100) {
                        setIsSidebarOpen(true); // Открываем при свайпе вправо
                    } else if (info.offset.x < -100) {
                        setIsSidebarOpen(false); // Закрываем при свайпе влево
                    }
                } : undefined}
            >
                <div className="p-4 border-b">
                    <h2 className="text-2xl font-bold text-appBlue">Кабинет абитуриента</h2>
                </div>

                <motion.div
                    className="p-4 border-b"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                >
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-full bg-appBlue text-white flex items-center justify-center">
                            {roleInfo.shortText}
                        </div>
                        <div>
                            <p className="font-semibold">{roleInfo.text}</p>
                            <p className="text-xs text-gray-500">{user?.email || 'Загрузка...'}</p>
                        </div>
                    </div>
                </motion.div>

                <motion.nav
                    className="flex-1 overflow-y-auto py-4"
                    variants={listVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <ul className="space-y-2 px-2">
                        {sidebarItems.map((item, index) => (
                            <motion.li key={index} variants={itemVariants}>
                                <Link
                                    to={item.path}
                                    onClick={() => isMobile && setIsSidebarOpen(false)} // Закрываем при клике на ссылку
                                    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-blue-50 transition-colors"
                                >
                                    <item.icon className="w-5 h-5 text-blue-500" />
                                    <span>{item.text}</span>
                                </Link>
                            </motion.li>
                        ))}
                    </ul>
                </motion.nav>

                <div className="p-4 border-t">
                    <button
                        onClick={handleSignOut}
                        className="flex items-center space-x-3 w-full p-3 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors"
                    >
                        <LogOut className="w-5 h-5" />
                        <span>Выйти</span>
                    </button>
                </div>
            </motion.div>

            {/* Оверлей для закрытия сайдбара на мобильных устройствах */}
            {isMobile && isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-30"
                    onClick={() => setIsSidebarOpen(false)} // Закрываем при клике на оверлей
                />
            )}
        </>
    );
};