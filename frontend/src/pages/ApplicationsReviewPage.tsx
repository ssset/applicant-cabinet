import React, { useState } from 'react';
import { Search, Check, X, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    SidebarProvider,
    SidebarInset
} from "@/components/ui/sidebar";
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ApplicationsDialog } from '@/components/applications/ApplicationsDialog';
import { RejectionDialog } from '@/components/applications/RejectionDialog';
import { ApplicantDetailsDialog } from '@/components/applications/ApplicantDetailsDialog';
import { useToast } from "@/hooks/use-toast";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { applicationAPI } from '@/services/api';

// Типы для заявок
export type ApplicationStatus = 'pending' | 'accepted' | 'rejected';

export type Application = {
    id: number;
    applicant_profile: {
        first_name?: string;
        last_name?: string;
        middle_name?: string;
        date_of_birth?: string;
        citizenship?: string;
        birth_place?: string;
        passport_series?: string;
        passport_number?: string;
        passport_issued_date?: string;
        passport_issued_by?: string;
        snils?: string;
        registration_address?: string;
        actual_address?: string;
        phone?: string;
        education_type?: string;
        education_institution?: string;
        graduation_year?: number;
        document_type?: string;
        document_series?: string;
        document_number?: string;
        average_grade?: number;
        calculated_average_grade?: number;
        foreign_languages?: string[];
        attestation_photo?: string;
        additional_info?: string;
        mother_full_name?: string;
        mother_workplace?: string;
        mother_phone?: string;
        father_full_name?: string;
        father_workplace?: string;
        father_phone?: string;
        photo?: string;
    };
    building_specialty: { specialty: { name: string } };
    created_at: string;
    status: ApplicationStatus;
    reject_reason?: string;
};

const ApplicationsReviewPage = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [isNewApplicationsDialogOpen, setIsNewApplicationsDialogOpen] = useState(false);
    const [isProcessedApplicationsDialogOpen, setIsProcessedApplicationsDialogOpen] = useState(false);
    const [isRejectionDialogOpen, setIsRejectionDialogOpen] = useState(false);
    const [isDetailsDialogOpen, setIsDetailsDialogOpen] = useState(false);
    const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
    const { toast } = useToast();
    const queryClient = useQueryClient();

    // Загрузка заявок с бэкенда
    const { data: applications = [], isLoading, error } = useQuery({
        queryKey: ['moderatorApplications'],
        queryFn: applicationAPI.getModeratorApplications,
    });

    const pendingApplications = applications.filter((app: Application) => app.status === 'pending');
    const processedApplications = applications.filter((app: Application) => app.status !== 'pending');

    const filteredApplications = applications.filter((app: Application) =>
        `${app.applicant_profile.first_name || ''} ${app.applicant_profile.last_name || ''}`
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
        app.building_specialty.specialty.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Мутация для обновления статуса заявки
    const updateApplicationMutation = useMutation({
        mutationFn: ({ applicationId, action, rejectReason }: { applicationId: number; action: 'accept' | 'reject'; rejectReason?: string }) =>
            applicationAPI.updateApplicationStatus(applicationId, action, rejectReason),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['moderatorApplications'] });
            toast({
                title: 'Статус заявки обновлён',
                description: 'Статус заявки успешно изменён.',
            });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || 'Не удалось обновить статус заявки',
            });
        },
    });

    const handleApprove = (application: Application) => {
        updateApplicationMutation.mutate({ applicationId: application.id, action: 'accept' });
    };

    const openRejectionDialog = (application: Application) => {
        setSelectedApplication(application);
        setIsRejectionDialogOpen(true);
    };

    const openDetailsDialog = (application: Application) => {
        setSelectedApplication(application);
        setIsDetailsDialogOpen(true);
    };

    const handleReject = (reason: string) => {
        if (selectedApplication) {
            updateApplicationMutation.mutate({
                applicationId: selectedApplication.id,
                action: 'reject',
                rejectReason: reason,
            });
            setIsRejectionDialogOpen(false);
            setSelectedApplication(null);
        }
    };

    if (isLoading) {
        return <div className="p-6 text-center">Загрузка...</div>;
    }

    if (error) {
        return <div className="p-6 text-center text-red-500">Ошибка загрузки заявок: {error.message}</div>;
    }

    return (
        <SidebarProvider defaultOpen>
            <div className="min-h-screen flex w-full bg-gray-50">
                <DashboardSidebar />

                <SidebarInset className="p-4 md:p-6 w-full box-border">
                    <h1 className="text-2xl font-bold mb-6">Обработка заявок</h1>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Новые заявки</CardTitle>
                                <CardDescription>{pendingApplications.length} заявок ожидают обработки</CardDescription>
                            </CardHeader>
                            <CardFooter>
                                <Button
                                    variant="outline"
                                    className="w-full"
                                    onClick={() => setIsNewApplicationsDialogOpen(true)}
                                >
                                    Просмотреть
                                </Button>
                            </CardFooter>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Обработанные заявки</CardTitle>
                                <CardDescription>{processedApplications.length} обработанных заявок</CardDescription>
                            </CardHeader>
                            <CardFooter>
                                <Button
                                    variant="outline"
                                    className="w-full"
                                    onClick={() => setIsProcessedApplicationsDialogOpen(true)}
                                >
                                    Просмотреть
                                </Button>
                            </CardFooter>
                        </Card>
                    </div>

                    <div className="bg-white p-6 rounded-lg shadow-sm">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-semibold">Список всех заявок</h2>
                            <div className="relative w-64">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Поиск..."
                                    className="pl-8"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="max-h-[calc(100vh-300px)] overflow-y-auto">
                            <Table>
                                <TableCaption>Список всех заявок абитуриентов</TableCaption>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>ID</TableHead>
                                        <TableHead>ФИО</TableHead>
                                        <TableHead>Дата подачи</TableHead>
                                        <TableHead>Специальность</TableHead>
                                        <TableHead>Статус</TableHead>
                                        <TableHead>Действия</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredApplications.map((app: Application) => (
                                        <TableRow key={app.id}>
                                            <TableCell>{app.id}</TableCell>
                                            <TableCell className="font-medium">
                                                {`${app.applicant_profile.last_name || ''} ${app.applicant_profile.first_name || ''} ${app.applicant_profile.middle_name || ''}`}
                                            </TableCell>
                                            <TableCell>{new Date(app.created_at).toLocaleDateString('ru-RU')}</TableCell>
                                            <TableCell>{app.building_specialty.specialty.name}</TableCell>
                                            <TableCell>
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                    app.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                                        app.status === 'accepted' ? 'bg-green-100 text-green-800' :
                                                            'bg-red-100 text-red-800'
                                                }`}>
                                                    {app.status === 'pending' ? 'Ожидает' :
                                                        app.status === 'accepted' ? 'Одобрена' :
                                                            'Отклонена'}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex gap-2">
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => openDetailsDialog(app)}
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                    {app.status === 'pending' && (
                                                        <>
                                                            <Button
                                                                size="sm"
                                                                className="bg-green-500 hover:bg-green-600"
                                                                onClick={() => handleApprove(app)}
                                                            >
                                                                <Check className="w-4 h-4" />
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="destructive"
                                                                onClick={() => openRejectionDialog(app)}
                                                            >
                                                                <X className="w-4 h-4" />
                                                            </Button>
                                                        </>
                                                    )}
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </SidebarInset>
            </div>

            {/* Диалог для новых заявок */}
            <ApplicationsDialog
                open={isNewApplicationsDialogOpen}
                onOpenChange={setIsNewApplicationsDialogOpen}
                applications={pendingApplications}
                title="Новые заявки"
                onApprove={handleApprove}
                onReject={openRejectionDialog}
            />

            {/* Диалог для обработанных заявок */}
            <ApplicationsDialog
                open={isProcessedApplicationsDialogOpen}
                onOpenChange={setIsProcessedApplicationsDialogOpen}
                applications={processedApplications}
                title="Обработанные заявки"
                onApprove={handleApprove}
                onReject={openRejectionDialog}
            />

            {/* Диалог для указания причины отклонения */}
            <RejectionDialog
                open={isRejectionDialogOpen}
                onOpenChange={setIsRejectionDialogOpen}
                onSubmit={handleReject}
                application={selectedApplication}
            />

            {/* Диалог с деталями абитуриента */}
            <ApplicantDetailsDialog
                open={isDetailsDialogOpen}
                onOpenChange={setIsDetailsDialogOpen}
                application={selectedApplication}
            />
        </SidebarProvider>
    );
};

export default ApplicationsReviewPage;