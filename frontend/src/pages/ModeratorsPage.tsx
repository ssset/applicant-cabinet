import React, { useState, useEffect } from 'react';
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { ModeratorsList } from '@/components/moderators/ModeratorsList';
import { ModeratorDialog } from '@/components/moderators/ModeratorDialog';
import { useToast } from "@/hooks/use-toast";
import { PlusCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { moderatorAPI } from '@/services/api';

// Тип для модератора, адаптированный под данные с бэкенда
export type Moderator = {
    id: string;
    email: string;
    role: 'moderator';
};

const ModeratorsPage: React.FC = () => {
    const [moderators, setModerators] = useState<Moderator[]>([]);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [currentModerator, setCurrentModerator] = useState<Moderator | null>(null);
    const { toast } = useToast();
    const [isLoading, setIsLoading] = useState(true);

    // Загрузка списка модераторов
    useEffect(() => {
        const fetchModerators = async () => {
            try {
                setIsLoading(true);
                const data = await moderatorAPI.getModerators();
                console.log('Response from getModerators:', data);

                // Проверяем, что data — массив
                if (!Array.isArray(data)) {
                    throw new Error("Ответ от сервера не является массивом");
                }

                const formattedModerators: Moderator[] = data.map((mod: any, index: number) => {
                    if (!mod.id || !mod.email || !mod.role) {
                        console.warn('Некорректный формат модератора:', mod);
                        throw new Error("Некорректный формат данных модератора");
                    }
                    return {
                        id: mod.id.toString(),
                        email: mod.email,
                        role: mod.role,
                    };
                });
                setModerators(formattedModerators);
            } catch (error: any) {
                console.error('Error fetching moderators:', error);
                toast({
                    title: "Ошибка",
                    description: error.message || "Не удалось загрузить список модераторов",
                    variant: "destructive",
                });
            } finally {
                setIsLoading(false);
            }
        };

        fetchModerators();
    }, [toast]);

    const handleOpenCreate = () => {
        setCurrentModerator(null);
        setIsDialogOpen(true);
    };

    const handleEdit = (moderator: Moderator) => {
        setCurrentModerator(moderator);
        setIsDialogOpen(true);
    };

    const handleDelete = async (moderatorId: string) => {
        try {
            // Пропускаем удаление, если id временный
            if (moderatorId.startsWith('temp-')) {
                setModerators(moderators.filter(mod => mod.id !== moderatorId));
                toast({
                    title: "Модератор удалён",
                    description: "Модератор был удалён локально",
                });
                return;
            }

            await moderatorAPI.deleteModerator(parseInt(moderatorId));
            setModerators(moderators.filter(mod => mod.id !== moderatorId));
            toast({
                title: "Модератор удалён",
                description: "Модератор был успешно удалён из системы",
            });
        } catch (error) {
            toast({
                title: "Ошибка",
                description: "Не удалось удалить модератора",
                variant: "destructive",
            });
        }
    };

    const handleSave = async (moderator: Moderator & { password?: string }) => {
        try {
            if (moderator.id && !moderator.id.startsWith('temp-')) {
                // Обновление модератора
                await moderatorAPI.updateModerator(parseInt(moderator.id), { email: moderator.email });
                setModerators(moderators.map(mod =>
                    mod.id === moderator.id ? moderator : mod
                ));
                toast({
                    title: "Модератор обновлён",
                    description: "Данные модератора были успешно обновлены",
                });
            } else {
                // Создание нового модератора
                if (!moderator.password) {
                    throw new Error("Пароль обязателен для создания нового модератора");
                }
                const response = await moderatorAPI.createModerator({
                    email: moderator.email,
                    password: moderator.password,
                    consent_to_data_processing: true,
                });
                console.log('New moderator data:', response);

                // Перезагружаем список модераторов с сервера
                const updatedModerators = await moderatorAPI.getModerators();
                const formattedModerators: Moderator[] = updatedModerators.map((mod: any) => ({
                    id: String(mod.id),
                    email: mod.email,
                    role: mod.role,
                }));
                setModerators(formattedModerators);

                toast({
                    title: "Модератор добавлен",
                    description: "Новый модератор добавлен. Он появится в списке после подтверждения email.",
                });
            }
            setIsDialogOpen(false);
        } catch (error: any) {
            toast({
                title: "Ошибка",
                description: error.message || "Не удалось сохранить модератора",
                variant: "destructive",
            });
        }
    };

    return (
        <SidebarProvider defaultOpen>
            <div className="min-h-screen flex w-full bg-gray-50">
                <DashboardSidebar />

                <SidebarInset className="p-4 md:p-6 flex-1 overflow-x-hidden">
                    <div className="flex justify-between items-center mb-6">
                        <h1 className="text-2xl font-bold">Управление модераторами</h1>
                        <Button
                            onClick={handleOpenCreate}
                            className="flex items-center gap-2"
                            disabled={isLoading}
                        >
                            <PlusCircle className="h-5 w-5" />
                            Добавить модератора
                        </Button>
                    </div>

                    {isLoading ? (
                        <p>Загрузка...</p>
                    ) : (
                        <ModeratorsList
                            moderators={moderators}
                            onEdit={handleEdit}
                            onDelete={handleDelete}
                        />
                    )}

                    <ModeratorDialog
                        open={isDialogOpen}
                        onOpenChange={setIsDialogOpen}
                        moderator={currentModerator}
                        onSave={handleSave}
                    />
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
};

export default ModeratorsPage;