import React, { useEffect, useState } from 'react';
import { FileText, School, BookOpen, Clock, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { applicationAPI } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { Link } from 'react-router-dom';

const ApplicationsPage = () => {
    const { toast } = useToast();
    const [applications, setApplications] = useState<any[]>([]);

    useEffect(() => {
        const fetchApplications = async () => {
            try {
                const apps = await applicationAPI.getApplications();
                setApplications(apps);
            } catch (error: any) {
                console.error('Error fetching applications:', error);
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: error.message || "Не удалось загрузить заявки",
                });
            }
        };

        fetchApplications();
    }, [toast]);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'pending':
                return <Badge className="bg-amber-500">На рассмотрении</Badge>;
            case 'accepted':
                return <Badge className="bg-green-500">Принято</Badge>;
            case 'rejected':
                return <Badge className="bg-red-500">Отклонено</Badge>;
            default:
                return <Badge>Неизвестно</Badge>;
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'pending':
                return <Clock className="w-5 h-5 text-amber-500" />;
            case 'accepted':
                return <CheckCircle2 className="w-5 h-5 text-green-500" />;
            case 'rejected':
                return <AlertCircle className="w-5 h-5 text-red-500" />;
            default:
                return null;
        }
    };

    return (
        <SidebarProvider defaultOpen>
            <div className="min-h-screen flex w-full bg-gray-50">
                <DashboardSidebar />

                <SidebarInset className="p-4 md:p-6 w-full">
                    <h1 className="text-2xl font-bold mb-6">Мои заявления</h1>

                    {/* Верхняя сетка - теперь на всю ширину */}
                    <div className="grid grid-cols-1 gap-6 mb-8">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <BookOpen className="w-5 h-5 text-blue-500" />
                                    Специальности
                                </CardTitle>
                                <CardDescription>Просмотр доступных специальностей</CardDescription>
                            </CardHeader>
                            <CardFooter>
                                <Button asChild variant="outline" className="w-full">
                                    <Link to="/specialties">Просмотреть</Link>
                                </Button>
                            </CardFooter>
                        </Card>
                    </div>

                    <h2 className="text-xl font-semibold mb-4">Мои заявления</h2>
                    <Card className="bg-white shadow-md rounded-lg">
                        <CardContent className="p-4">
                            <div className="space-y-4 h-[calc(100vh-400px)] overflow-y-auto">
                                {applications.length === 0 ? (
                                    <p className="text-gray-500">У вас пока нет заявлений.</p>
                                ) : (
                                    applications.map((app) => (
                                        <Card key={app.id} className="w-full">
                                            <CardHeader>
                                                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                                                    <div>
                                                        <CardTitle className="flex items-center gap-2">
                                                            {getStatusIcon(app.status)}
                                                            {app.building_specialty?.building?.organization?.name || 'Организация не указана'}
                                                        </CardTitle>
                                                        <CardDescription>
                                                            {app.building_specialty?.specialty?.name || 'Специальность не указана'}
                                                        </CardDescription>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {getStatusBadge(app.status)}
                                                    </div>
                                                </div>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="space-y-3">
                                                    <div className="flex justify-between">
                                                        <span className="text-sm text-gray-500">
                                                            Дата подачи: {new Date(app.created_at).toLocaleDateString('ru-RU')}
                                                        </span>
                                                    </div>
                                                    {app.status === 'rejected' && app.reject_reason && (
                                                        <p className="text-sm text-red-500 mt-2">
                                                            Причина отклонения: {app.reject_reason}
                                                        </p>
                                                    )}
                                                </div>
                                            </CardContent>
                                            <CardFooter className="flex justify-end">
                                                {app.status === 'rejected' && (
                                                    <Button
                                                        asChild
                                                        variant="outline"
                                                        className="text-blue-600 border-blue-600 hover:bg-blue-50"
                                                    >
                                                        <Link to={`/application/${app.building_specialty.specialty.id}/${app.building_specialty.building.organization.id}`}>
                                                            <RefreshCw className="h-4 w-4 mr-2" />
                                                            Переподать
                                                        </Link>
                                                    </Button>
                                                )}
                                            </CardFooter>
                                        </Card>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
};

export default ApplicationsPage;