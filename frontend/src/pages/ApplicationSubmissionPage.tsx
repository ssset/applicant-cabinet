import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { GraduationCap, Send, MapPin, Clock, Info, AlertCircle, Wallet, School } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { specialtyAPI, institutionAPI, applicationAPI, userAPI } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { Link } from 'react-router-dom';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Specialty {
    id: number;
    name: string;
    code: string;
    organization: { id: number; name: string; address: string; phone: string; email: string };
    duration: string | null;
    requirements: string | null;
    building_specialties: Array<{
        id: number;
        building: { id: number; name: string; address: string };
        budget_places: number;
        commercial_places: number;
        commercial_price: number;
    }>;
}

interface ApplicationFormData {
    building_specialty_id: number;
    priority: number;
    course: number;
    study_form: 'full_time' | 'part_time';
    funding_basis: 'budget' | 'commercial';
    dormitory_needed: boolean;
    first_time_education: boolean;
    info_source: string;
}

const ApplicationSubmissionPage: React.FC = () => {
    const { specialtyId, organizationId } = useParams<{ specialtyId: string; organizationId: string }>();
    const { user } = useAuth();
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [fundingBasis, setFundingBasis] = useState<'budget' | 'commercial'>('budget');

    // Загрузка данных о специальности
    const { data: specialty, isLoading: isSpecialtyLoading } = useQuery<Specialty>({
        queryKey: ['specialty', specialtyId, organizationId],
        queryFn: async () => {
            const response = await specialtyAPI.getAvailableSpecialties(
                organizationId ? parseInt(organizationId) : undefined
            );
            const foundSpecialty = response.find((s: Specialty) => s.id.toString() === specialtyId);
            if (!foundSpecialty) {
                throw new Error('Специальность не найдена');
            }
            return foundSpecialty;
        },
        enabled: !!specialtyId && !!organizationId && user?.role === 'applicant',
    });

    // Загрузка данных об организации
    const { data: organization, isLoading: isOrganizationLoading } = useQuery({
        queryKey: ['organization', organizationId],
        queryFn: async () => {
            const response = await institutionAPI.getAvailableInstitutions();
            const foundOrg = response.find((org: any) => org.id.toString() === organizationId);
            if (!foundOrg) {
                throw new Error('Организация не найдена');
            }
            return foundOrg;
        },
        enabled: !!organizationId && user?.role === 'applicant',
    });

    // Загрузка профиля абитуриента
    const { data: profile, isLoading: isProfileLoading, error: profileError } = useQuery({
        queryKey: ['applicantProfile'],
        queryFn: userAPI.getApplicantProfile,
        enabled: user?.role === 'applicant',
    });

    // Загрузка количества попыток подачи заявления
    const buildingSpecialtyId = specialty?.building_specialties[0]?.id;
    const { data: attemptsData, isLoading: isAttemptsLoading } = useQuery({
        queryKey: ['applicationAttempts', buildingSpecialtyId],
        queryFn: () => applicationAPI.getApplicationAttempts(buildingSpecialtyId!),
        enabled: !!buildingSpecialtyId && user?.role === 'applicant',
    });

    // Мутация для подачи заявления
    const submitApplicationMutation = useMutation({
        mutationFn: (data: ApplicationFormData) => applicationAPI.createApplication(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['applications'] });
            queryClient.invalidateQueries({ queryKey: ['applicationAttempts'] });
            toast({
                title: 'Заявление успешно отправлено!',
                description: 'Мы свяжемся с вами для дальнейших действий.',
            });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || 'Пожалуйста, попробуйте снова позже.',
            });
        },
        onSettled: () => {
            setIsSubmitting(false);
        },
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!specialty || !specialty.building_specialties[0]) {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: 'Данные о специальности недоступны.',
            });
            return;
        }

        // Проверка доступности мест
        const buildingSpecialty = specialty.building_specialties[0];
        if (fundingBasis === 'budget' && buildingSpecialty.budget_places <= 0) {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: 'Нет доступных бюджетных мест для этой специальности.',
            });
            return;
        }
        if (fundingBasis === 'commercial' && buildingSpecialty.commercial_places <= 0) {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: 'Нет доступных коммерческих мест для этой специальности.',
            });
            return;
        }

        setIsSubmitting(true);
        const applicationData: ApplicationFormData = {
            building_specialty_id: specialty.building_specialties[0].id,
            priority: 1,
            course: 1,
            study_form: 'full_time',
            funding_basis: fundingBasis,
            dormitory_needed: false,
            first_time_education: true,
            info_source: 'Сайт организации',
        };

        submitApplicationMutation.mutate(applicationData);
    };

    if (isSpecialtyLoading || isOrganizationLoading || isProfileLoading || isAttemptsLoading) {
        return (
            <DashboardLayout>
                <div className="p-6">Загрузка...</div>
            </DashboardLayout>
        );
    }

    if (!specialty || !organization) {
        return (
            <DashboardLayout>
                <div className="p-6">Специальность или организация не найдены.</div>
            </DashboardLayout>
        );
    }

    const hasProfile = !profileError || (profileError.response?.status !== 404);
    const buildingSpecialty = specialty.building_specialties[0] || {};
    const remainingAttempts = attemptsData?.remaining ?? 3;
    const canSubmit = remainingAttempts > 0;

    return (
        <DashboardLayout>
            <div className="p-6">
                <h1 className="text-2xl font-bold mb-6">Подача заявления в {organization.name}</h1>

                <Card className="mb-8 max-w-3xl mx-auto">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <GraduationCap className="h-6 w-6 text-blue-500" />
                            {specialty.name} ({specialty.code})
                        </CardTitle>
                        <CardDescription>Информация о выбранной специальности</CardDescription>
                    </CardHeader>

                    <CardContent>
                        <div className="space-y-6">
                            <div className="bg-blue-50 p-4 rounded-md">
                                <h3 className="text-lg font-semibold flex items-center gap-2 mb-2">
                                    <GraduationCap className="h-5 w-5" />
                                    О специальности
                                </h3>
                                <p className="text-sm mb-4">{specialty.description || 'Описание отсутствует'}</p>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <h4 className="font-medium text-gray-700">Детали обучения</h4>
                                        <div className="space-y-2 mt-2 text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <MapPin className="h-4 w-4" />
                                                <span>
                                                    <strong>Расположение:</strong>{' '}
                                                    {buildingSpecialty.building?.address || 'Не указано'}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Clock className="h-4 w-4" />
                                                <span>
                                                    <strong>Срок обучения:</strong> {specialty.duration || 'Не указано'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-gray-700">Требования и места</h4>
                                        <div className="space-y-2 mt-2 text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <School className="h-4 w-4" />
                                                <span>
                                                    <strong>Бюджетные места:</strong>{' '}
                                                    {buildingSpecialty.budget_places || 0}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Wallet className="h-4 w-4" />
                                                <span>
                                                    <strong>Коммерческие места:</strong>{' '}
                                                    {buildingSpecialty.commercial_places || 0}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Info className="h-4 w-4" />
                                                <span>
                                                    <strong>Требования:</strong> {specialty.requirements || 'Не указано'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {!hasProfile && (
                                <div className="bg-red-50 p-4 rounded-md flex items-start gap-3">
                                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                                    <div>
                                        <h3 className="text-lg font-semibold text-red-700">Профиль не заполнен</h3>
                                        <p className="text-sm text-red-600">
                                            Чтобы подать заявление, вам нужно заполнить профиль абитуриента.
                                            Перейдите в{' '}
                                            <Link to="/settings" className="underline hover:text-red-800">
                                                настройки профиля
                                            </Link>{' '}
                                            и заполните все необходимые поля.
                                        </p>
                                    </div>
                                </div>
                            )}

                            {hasProfile && (
                                <div className="bg-yellow-50 p-4 rounded-md flex items-start gap-3">
                                    <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                                    <div>
                                        <h3 className="text-lg font-semibold text-yellow-700">Оставшиеся попытки</h3>
                                        <p className="text-sm text-yellow-600">
                                            У вас осталось {remainingAttempts} из 3 попыток подачи заявления на эту специальность.
                                            {remainingAttempts === 0 && (
                                                <span className="block mt-1">
                                                    Вы исчерпали все попытки. Пожалуйста, выберите другую специальность.
                                                </span>
                                            )}
                                        </p>
                                    </div>
                                </div>
                            )}

                            <form onSubmit={handleSubmit}>
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Основа обучения
                                    </label>
                                    <Select
                                        value={fundingBasis}
                                        onValueChange={(value: 'budget' | 'commercial') => setFundingBasis(value)}
                                    >
                                        <SelectTrigger className="w-full md:w-[200px]">
                                            <SelectValue placeholder="Выберите основу обучения" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="budget">Бюджет</SelectItem>
                                            <SelectItem value="commercial">Коммерция</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                {fundingBasis === 'commercial' && (
                                    <div className="mb-4 text-sm text-gray-600">
                                        <strong>Стоимость обучения:</strong> {buildingSpecialty.commercial_price} руб.
                                    </div>
                                )}

                                <div className="pt-4 flex justify-end">
                                    <Button
                                        type="submit"
                                        disabled={isSubmitting || !hasProfile || !canSubmit}
                                        className="w-full sm:w-auto"
                                    >
                                        {isSubmitting ? (
                                            <>Отправка...</>
                                        ) : (
                                            <>
                                                <Send className="h-4 w-4 mr-2" />
                                                Отправить заявление
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </form>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
};

export default ApplicationSubmissionPage;