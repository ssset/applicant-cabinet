import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { User, Lock } from 'lucide-react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { ProfileForm } from '@/components/Settings/ProfileForm';
import { PasswordForm } from '@/components/Settings/PasswordForm';
import { useAuth } from '@/hooks/useAuth';
import { userAPI } from '@/services/api';
import { useQuery } from '@tanstack/react-query';

const ProfileSettingsPage = () => {
    const { user, isLoading: isAuthLoading } = useAuth();
    const [activeTab, setActiveTab] = useState('password');

    // Запрос для получения профиля абитуриента
    const { data: profile } = useQuery({
        queryKey: ['applicantProfile'],
        queryFn: () => userAPI.getApplicantProfile(),
        enabled: user?.role === 'applicant',
        retry: false, // Не повторять запрос при ошибке 404
    });

    // Устанавливаем активную вкладку в зависимости от роли
    useEffect(() => {
        if (!isAuthLoading && user) {
            setActiveTab(user.role === 'applicant' ? 'profile' : 'password');
        }
    }, [isAuthLoading, user]);

    // Если данные пользователя еще загружаются
    if (isAuthLoading) {
        return (
            <div className="flex h-screen overflow-hidden">
                <DashboardSidebar />
                <div className="flex-1 container mx-auto py-10 px-4">
                    <h1 className="text-2xl font-bold mb-8">Настройки профиля</h1>
                    <div className="text-center text-gray-500">Загрузка данных...</div>
                </div>
            </div>
        );
    }

    // Если пользователь не авторизован
    if (!user) {
        return (
            <div className="flex h-screen overflow-hidden">
                <DashboardSidebar />
                <div className="flex-1 container mx-auto py-10 px-4">
                    <h1 className="text-2xl font-bold mb-8">Настройки профиля</h1>
                    <div className="text-center text-red-500">Ошибка: пользователь не авторизован</div>
                </div>
            </div>
        );
    }

    const isApplicant = user.role === 'applicant';

    return (
        <div className="flex h-screen overflow-hidden">
            <DashboardSidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="container mx-auto py-10 px-4 flex flex-col h-full">
                    <div className="flex justify-between items-center mb-8">
                        <h1 className="text-2xl font-bold">Настройки профиля</h1>
                    </div>

                    <div className="mb-8">
                        <p className="text-muted-foreground">
                            Управляйте настройками {isApplicant ? 'вашего профиля и паролем' : 'вашего пароля'}.
                        </p>
                    </div>

                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full flex-1 flex flex-col overflow-hidden">
                        <TabsList className={`grid ${isApplicant ? 'grid-cols-2' : 'grid-cols-1'} w-full md:w-[400px]`}>
                            {isApplicant && (
                                <TabsTrigger value="profile" className="flex items-center">
                                    <User className="w-4 h-4 mr-2" />
                                    <span>Профиль</span>
                                </TabsTrigger>
                            )}
                            <TabsTrigger value="password" className="flex items-center">
                                <Lock className="w-4 h-4 mr-2" />
                                <span>Пароль</span>
                            </TabsTrigger>
                        </TabsList>

                        <div className="mt-6 flex-1 overflow-hidden">
                            <Card className="h-full flex flex-col">
                                <CardContent className="pt-6 flex-1 overflow-y-auto">
                                    {isApplicant && (
                                        <TabsContent value="profile" className="m-0">
                                            <ProfileForm profile={profile} />
                                        </TabsContent>
                                    )}
                                    <TabsContent value="password" className="m-0">
                                        <PasswordForm />
                                    </TabsContent>
                                </CardContent>
                            </Card>
                        </div>
                    </Tabs>
                </div>
            </div>
        </div>
    );
};

export default ProfileSettingsPage;