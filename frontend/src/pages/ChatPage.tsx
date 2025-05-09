import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import {
    SidebarProvider,
    SidebarInset
} from "@/components/ui/sidebar";
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { ModeratorChatView } from '@/components/chat/ModeratorChatView';
import { ApplicantChatView } from '@/components/chat/ApplicantChatView';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { useNavigate } from 'react-router-dom';

// Функция для получения читаемого названия роли
const getRoleLabel = (role: string) => {
    switch (role) {
        case 'applicant':
            return 'Абитуриент';
        case 'moderator':
            return 'Модератор';
        case 'admin_org':
            return 'Администратор организации';
        default:
            return role;
    }
};

const ChatPage = () => {
    const { user, isLoading: isAuthLoading, error: authError } = useAuth();
    const { toast } = useToast();
    const navigate = useNavigate();

    // Обработка ошибок авторизации
    React.useEffect(() => {
        if (authError) {
            toast({
                variant: 'destructive',
                title: 'Ошибка авторизации',
                description: 'Не удалось загрузить данные пользователя. Пожалуйста, войдите снова.',
            });
            navigate('/login');
        }
    }, [authError, toast, navigate]);

    // Пока данные пользователя загружаются, показываем индикатор загрузки
    if (isAuthLoading) {
        return (
            <SidebarProvider defaultOpen>
                <div className="min-h-screen flex w-full bg-gray-50">
                    <DashboardSidebar />
                    <SidebarInset className="p-4 md:p-6 w-full">
                        <h1 className="text-2xl font-bold mb-6">Сообщения</h1>
                        <Card className="flex-1 flex items-center justify-center">
                            <div className="text-center text-gray-500">Загрузка...</div>
                        </Card>
                    </SidebarInset>
                </div>
            </SidebarProvider>
        );
    }

    // Если пользователь не авторизован, перенаправляем на страницу логина
    if (!user) {
        toast({
            variant: 'destructive',
            title: 'Ошибка',
            description: 'Пожалуйста, войдите в систему, чтобы получить доступ к чатам.',
        });
        navigate('/login');
        return null;
    }

    // Проверка поддерживаемых ролей
    const supportedRoles = ['moderator', 'admin_org', 'applicant']; // Убрали 'admin', так как используется 'admin_org'
    if (!supportedRoles.includes(user.role)) {
        return (
            <SidebarProvider defaultOpen>
                <div className="min-h-screen flex w-full bg-gray-50">
                    <DashboardSidebar />
                    <SidebarInset className="p-4 md:p-6 w-full">
                        <h1 className="text-2xl font-bold mb-6">Сообщения</h1>
                        <Card className="flex-1 flex items-center justify-center">
                            <div className="text-center text-gray-500">
                                <p className="text-xl font-semibold mb-2">Доступ запрещён</p>
                                <p>Ваша роль ({getRoleLabel(user.role)}) не поддерживает доступ к чатам.</p>
                            </div>
                        </Card>
                    </SidebarInset>
                </div>
            </SidebarProvider>
        );
    }

    return (
        <SidebarProvider defaultOpen>
            <div className="min-h-screen flex w-full bg-gray-50">
                <DashboardSidebar />
                <SidebarInset className="p-4 md:p-6 w-full">
                    <h1 className="text-2xl font-bold mb-6">Сообщения ({getRoleLabel(user.role)})</h1>
                    {['moderator', 'admin_org'].includes(user.role) ? (
                        <ModeratorChatView />
                    ) : (
                        <ApplicantChatView />
                    )}
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
};

export default ChatPage;