import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
    User,
    Mail,
    Phone,
    MapPin,
    Calendar,
    Building,
    Book,
    Award,
    FileText,
    Home,
    TrendingUp,
} from 'lucide-react';

import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { useToast } from '@/components/ui/use-toast';
import { userAPI } from '@/services/api';

// Базовый URL бэкенда
const BASE_URL = 'http://localhost:8000';

interface ApplicantProfileData {
    first_name: string;
    last_name: string;
    middle_name?: string;
    date_of_birth?: string;
    citizenship: string;
    birth_place: string;
    passport_series: string;
    passport_number: string;
    passport_issued_date?: string;
    passport_issued_by: string;
    snils: string;
    registration_address: string;
    actual_address: string;
    phone: string;
    education_type: string;
    education_institution: string;
    graduation_year?: number;
    document_type: string;
    document_series: string;
    document_number: string;
    average_grade?: number;
    calculated_average_grade?: number;
    foreign_languages?: string[];
    additional_info?: string;
    mother_full_name: string;
    mother_workplace: string;
    mother_phone: string;
    father_full_name: string;
    father_workplace: string;
    father_phone: string;
    photo?: string;
    attestation_photo?: string;
}

const profileSchema = z.object({
    email: z.string().email('Введите корректный email'),
    first_name: z.string().min(2, 'Имя должно содержать минимум 2 символа'),
    last_name: z.string().min(2, 'Фамилия должна содержать минимум 2 символа'),
    middle_name: z.string().optional(),
    date_of_birth: z.date({ required_error: 'Пожалуйста, выберите дату рождения' }),
    citizenship: z.string().min(2, 'Гражданство обязательно'),
    birth_place: z.string().min(2, 'Место рождения обязательно'),
    passport_series: z.string().min(2, 'Серия паспорта обязательна'),
    passport_number: z.string().min(2, 'Номер паспорта обязателен'),
    passport_issued_date: z.date({ required_error: 'Пожалуйста, выберите дату выдачи паспорта' }),
    passport_issued_by: z.string().min(2, 'Укажите, кем выдан паспорт'),
    snils: z.string().min(2, 'СНИЛС обязателен'),
    registration_address: z.string().min(5, 'Адрес регистрации должен содержать минимум 5 символов'),
    actual_address: z.string().min(5, 'Фактический адрес должен содержать минимум 5 символов'),
    phone: z.string().min(10, 'Введите корректный номер телефона'),
    education_type: z.string().min(2, 'Тип образования обязателен'),
    education_institution: z.string().min(2, 'Укажите учебное заведение'),
    graduation_year: z.string().regex(/^\d{4}$/, 'Введите корректный год выпуска'),
    document_type: z.string().min(2, 'Тип документа обязателен'),
    document_series: z.string().min(2, 'Серия документа обязательна'),
    document_number: z.string().min(2, 'Номер документа обязателен'),
    average_grade: z
        .union([
            z.string().regex(/^\d*\.?\d*$/, 'Введите корректное число'),
            z.number(),
        ])
        .transform((val) => (typeof val === 'string' ? parseFloat(val) : val))
        .refine((val) => val >= 0 && val <= 5.0, 'Средний балл должен быть от 0 до 5.0')
        .optional(),
    calculated_average_grade: z
        .union([
            z.number(),
            z.string().transform((val) => {
                const normalized = val.replace(',', '.');
                return parseFloat(normalized);
            }),
        ])
        .optional()
        .refine(
            (val) => val === undefined || (typeof val === 'number' && !isNaN(val)),
            { message: 'Посчитанный средний балл должен быть числом' }
        ),
    foreign_languages: z.string().optional(),
    additional_info: z.string().optional(),
    mother_full_name: z.string().min(2, 'ФИО матери обязательно'),
    mother_workplace: z.string().min(2, 'Место работы матери обязательно'),
    mother_phone: z.string().min(10, 'Введите корректный номер телефона матери'),
    father_full_name: z.string().min(2, 'ФИО отца обязательно'),
    father_workplace: z.string().min(2, 'Место работы отца обязательно'),
    father_phone: z.string().min(10, 'Введите корректный номер телефона отца'),
    photo: z.any().optional(),
    attestation_photo: z.any().optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export const ProfileForm: React.FC<{ profile?: ApplicantProfileData }> = ({ profile }) => {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    const { data: userData, isLoading: isUserLoading } = useQuery({
        queryKey: ['currentUser'],
        queryFn: userAPI.getCurrentUser,
    });

    const form = useForm<ProfileFormValues>({
        resolver: zodResolver(profileSchema),
        defaultValues: {
            email: userData?.email || '',
            first_name: profile?.first_name || '',
            last_name: profile?.last_name || '',
            middle_name: profile?.middle_name || '',
            date_of_birth: profile?.date_of_birth ? new Date(profile.date_of_birth) : undefined,
            citizenship: profile?.citizenship || '',
            birth_place: profile?.birth_place || '',
            passport_series: profile?.passport_series || '',
            passport_number: profile?.passport_number || '',
            passport_issued_date: profile?.passport_issued_date ? new Date(profile.passport_issued_date) : undefined,
            passport_issued_by: profile?.passport_issued_by || '',
            snils: profile?.snils || '',
            registration_address: profile?.registration_address || '',
            actual_address: profile?.actual_address || '',
            phone: profile?.phone || '',
            education_type: profile?.education_type || '',
            education_institution: profile?.education_institution || '',
            graduation_year: profile?.graduation_year ? profile.graduation_year.toString() : '',
            document_type: profile?.document_type || '',
            document_series: profile?.document_series || '',
            document_number: profile?.document_number || '',
            average_grade: profile?.average_grade ?? undefined,
            calculated_average_grade: profile?.calculated_average_grade ?? undefined,
            foreign_languages: profile?.foreign_languages ? profile.foreign_languages.join(', ') : '',
            additional_info: profile?.additional_info || '',
            mother_full_name: profile?.mother_full_name || '',
            mother_workplace: profile?.mother_workplace || '',
            mother_phone: profile?.mother_phone || '',
            father_full_name: profile?.father_full_name || '',
            father_workplace: profile?.father_workplace || '',
            father_phone: profile?.father_phone || '',
            photo: null,
            attestation_photo: null,
        },
    });

    useEffect(() => {
        if (userData) {
            form.setValue('email', userData.email || '');
        }
    }, [userData, form]);

    const updateEmailMutation = useMutation({
        mutationFn: (data: { email: string }) => userAPI.updateCurrentUser(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['currentUser'] });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || error.response?.data?.error || 'Не удалось обновить email.',
            });
        },
    });

    const createProfileMutation = useMutation({
        mutationFn: (data: FormData) => userAPI.createApplicantProfile(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['applicantProfile'] });
            form.setValue('photo', null);
            form.setValue('attestation_photo', null);
            toast({
                title: 'Профиль создан',
                description: 'Ваши данные успешно сохранены.',
            });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || error.response?.data?.error || 'Не удалось создать профиль.',
            });
        },
    });

    const updateProfileMutation = useMutation({
        mutationFn: (data: FormData) => userAPI.updateApplicantProfile(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['applicantProfile'] });
            form.setValue('photo', null);
            form.setValue('attestation_photo', null);
            toast({
                title: 'Профиль обновлён',
                description: 'Ваши данные успешно сохранены.',
            });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || error.response?.data?.error || 'Не удалось обновить профиль.',
            });
        },
    });

    const onSubmit = (data: ProfileFormValues) => {
        updateEmailMutation.mutate({ email: data.email });

        const formDataToSend = new FormData();
        formDataToSend.append('first_name', data.first_name);
        formDataToSend.append('last_name', data.last_name);
        if (data.middle_name) formDataToSend.append('middle_name', data.middle_name);
        formDataToSend.append('date_of_birth', data.date_of_birth.toISOString().split('T')[0]);
        formDataToSend.append('citizenship', data.citizenship);
        formDataToSend.append('birth_place', data.birth_place);
        formDataToSend.append('passport_series', data.passport_series);
        formDataToSend.append('passport_number', data.passport_number);
        formDataToSend.append('passport_issued_date', data.passport_issued_date.toISOString().split('T')[0]);
        formDataToSend.append('passport_issued_by', data.passport_issued_by);
        formDataToSend.append('snils', data.snils);
        formDataToSend.append('registration_address', data.registration_address);
        formDataToSend.append('actual_address', data.actual_address);
        formDataToSend.append('phone', data.phone);
        formDataToSend.append('education_type', data.education_type);
        formDataToSend.append('education_institution', data.education_institution);
        formDataToSend.append('graduation_year', data.graduation_year);
        formDataToSend.append('document_type', data.document_type);
        formDataToSend.append('document_series', data.document_series);
        formDataToSend.append('document_number', data.document_number);
        if (data.average_grade !== undefined) formDataToSend.append('average_grade', data.average_grade.toString());
        if (data.foreign_languages) {
            const languages = data.foreign_languages.split(',').map((lang) => lang.trim());
            formDataToSend.append('foreign_languages', JSON.stringify(languages));
        }
        if (data.additional_info) formDataToSend.append('additional_info', data.additional_info);
        formDataToSend.append('mother_full_name', data.mother_full_name);
        formDataToSend.append('mother_workplace', data.mother_workplace);
        formDataToSend.append('mother_phone', data.mother_phone);
        formDataToSend.append('father_full_name', data.father_full_name);
        formDataToSend.append('father_workplace', data.father_workplace);
        formDataToSend.append('father_phone', data.father_phone);

        if (data.photo) formDataToSend.append('photo', data.photo);
        if (data.attestation_photo) formDataToSend.append('attestation_photo', data.attestation_photo);

        if (profile) {
            updateProfileMutation.mutate(formDataToSend);
        } else {
            createProfileMutation.mutate(formDataToSend);
        }
    };

    const getFullImageUrl = (path?: string) => {
        if (!path) return null;
        return path.startsWith('http') ? path : `${BASE_URL}${path}`;
    };

    if (isUserLoading) {
        return <div>Загрузка...</div>;
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                {/* Контактные данные */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Контактные данные</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="email"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Email *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Mail className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="email@example.com" type="email" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="phone"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Телефон *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Phone className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="+7 (XXX) XXX-XX-XX" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                </div>

                {/* Персональные данные */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Персональные данные</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="last_name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Фамилия *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <User className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Фамилия" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="first_name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Имя *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <User className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Имя" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="middle_name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Отчество (если есть)</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <User className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Отчество" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="date_of_birth"
                            render={({ field }) => (
                                <FormItem className="flex flex-col">
                                    <FormLabel>Дата рождения *</FormLabel>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <FormControl>
                                                <Button
                                                    variant="outline"
                                                    className={`w-full pl-3 text-left font-normal ${
                                                        !field.value ? 'text-muted-foreground' : ''
                                                    }`}
                                                >
                                                    <Calendar className="mr-2 h-4 w-4 opacity-70" />
                                                    {field.value ? (
                                                        format(field.value, 'PPP', { locale: ru })
                                                    ) : (
                                                        <span>Выберите дату</span>
                                                    )}
                                                </Button>
                                            </FormControl>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-auto p-0" align="start">
                                            <CalendarComponent
                                                mode="single"
                                                selected={field.value}
                                                onSelect={field.onChange}
                                                disabled={(date) => date > new Date() || date < new Date('1900-01-01')}
                                                initialFocus
                                            />
                                        </PopoverContent>
                                    </Popover>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="citizenship"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Гражданство *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <User className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Гражданство" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="birth_place"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Место рождения *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <MapPin className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Место рождения" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                </div>

                {/* Фотографии */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Фотографии</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="photo"
                            render={({ field: { onChange, value, ...field } }) => (
                                <FormItem>
                                    <FormLabel>Фото профиля</FormLabel>
                                    {profile?.photo && !value ? (
                                        <div className="mt-2">
                                            <img
                                                src={getFullImageUrl(profile.photo)}
                                                alt="Фото профиля"
                                                className="w-48 h-48 object-cover rounded-md border border-gray-200"
                                                onError={(e) => {
                                                    e.currentTarget.src = '/placeholder-user.jpg';
                                                    e.currentTarget.onerror = null;
                                                }}
                                            />
                                        </div>
                                    ) : value ? (
                                        <div className="mt-2 text-gray-600">
                                            Файл выбран: {value.name}
                                        </div>
                                    ) : (
                                        <div className="mt-2 text-gray-600">Не загружено</div>
                                    )}
                                    <FormControl>
                                        <Input
                                            type="file"
                                            accept="image/*"
                                            {...field}
                                            onChange={(e) => {
                                                const file = e.target.files?.[0];
                                                onChange(file);
                                            }}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="attestation_photo"
                            render={({ field: { onChange, value, ...field } }) => (
                                <FormItem>
                                    <FormLabel>Фото аттестата</FormLabel>
                                    {profile?.attestation_photo && !value ? (
                                        <div className="mt-2">
                                            <img
                                                src={getFullImageUrl(profile.attestation_photo)}
                                                alt="Фото аттестата"
                                                className="w-48 h-48 object-cover rounded-md border border-gray-200"
                                                onError={(e) => {
                                                    e.currentTarget.src = '/placeholder-attestation.jpg';
                                                    e.currentTarget.onerror = null;
                                                }}
                                            />
                                        </div>
                                    ) : value ? (
                                        <div className="mt-2 text-gray-600">
                                            Файл выбран: {value.name}
                                        </div>
                                    ) : (
                                        <div className="mt-2 text-gray-600">Не загружено</div>
                                    )}
                                    <FormControl>
                                        <Input
                                            type="file"
                                            accept="image/*"
                                            {...field}
                                            onChange={(e) => {
                                                const file = e.target.files?.[0];
                                                onChange(file);
                                            }}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                </div>

                {/* Паспортные данные */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Паспортные данные</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="passport_series"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Серия паспорта *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Серия паспорта" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="passport_number"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Номер паспорта *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Номер паспорта" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="passport_issued_date"
                            render={({ field }) => (
                                <FormItem className="flex flex-col">
                                    <FormLabel>Дата выдачи *</FormLabel>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <FormControl>
                                                <Button
                                                    variant="outline"
                                                    className={`w-full pl-3 text-left font-normal ${
                                                        !field.value ? 'text-muted-foreground' : ''
                                                    }`}
                                                >
                                                    <Calendar className="mr-2 h-4 w-4 opacity-70" />
                                                    {field.value ? (
                                                        format(field.value, 'PPP', { locale: ru })
                                                    ) : (
                                                        <span>Выберите дату</span>
                                                    )}
                                                </Button>
                                            </FormControl>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-auto p-0" align="start">
                                            <CalendarComponent
                                                mode="single"
                                                selected={field.value}
                                                onSelect={field.onChange}
                                                disabled={(date) => date > new Date() || date < new Date('1900-01-01')}
                                                initialFocus
                                            />
                                        </PopoverContent>
                                    </Popover>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="passport_issued_by"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Кем выдан *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Кем выдан" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="snils"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>СНИЛС *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="СНИЛС" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                </div>

                {/* Адреса */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Адреса</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="registration_address"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Адрес регистрации *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Home className="mr-2 h-4 w-4 opacity-70" />
                                            <Textarea placeholder="Адрес регистрации" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="actual_address"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Фактический адрес *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Home className="mr-2 h-4 w-4 opacity-70" />
                                            <Textarea placeholder="Фактический адрес" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                </div>

                {/* Образование */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Образование</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="education_type"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Тип образования *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Book className="mr-2 h-4 w-4 opacity-70" />
                                            <Select onValueChange={field.onChange} value={field.value}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Выберите тип образования" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="school">Школа</SelectItem>
                                                    <SelectItem value="npo">НПО</SelectItem>
                                                    <SelectItem value="other">Другое</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="education_institution"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Учебное заведение *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Building className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Название учебного заведения" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="graduation_year"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Год окончания *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Award className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="ГГГГ" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="document_type"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Тип документа *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Select onValueChange={field.onChange} value={field.value}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Выберите тип документа" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="certificate">Аттестат</SelectItem>
                                                    <SelectItem value="diploma">Диплом</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="document_series"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Серия документа *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Серия документа" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="document_number"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Номер документа *</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Номер документа" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="average_grade"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Средний балл</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <TrendingUp className="mr-2 h-4 w-4 opacity-70" />
                                            <Input
                                                type="number"
                                                step="0.1"
                                                min="0"
                                                max="5"
                                                placeholder="Например: 4.5"
                                                {...field}
                                                onChange={(e) => field.onChange(parseFloat(e.target.value))}
                                            />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="calculated_average_grade"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Посчитанный средний балл (из аттестата)</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <TrendingUp className="mr-2 h-4 w-4 opacity-70" />
                                            <Input
                                                type="number"
                                                step="0.1"
                                                value={field.value ?? ''}
                                                disabled
                                                placeholder="Будет посчитано автоматически"
                                            />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                </div>

                {/* Дополнительная информация */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Дополнительная информация</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="foreign_languages"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Иностранные языки</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <Book className="mr-2 h-4 w-4 opacity-70" />
                                            <Input placeholder="Например: английский, немецкий" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="additional_info"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Дополнительная информация</FormLabel>
                                    <FormControl>
                                        <div className="flex items-center">
                                            <FileText className="mr-2 h-4 w-4 opacity-70" />
                                            <Textarea placeholder="Дополнительная информация" {...field} />
                                        </div>
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>
                </div>

                {/* Данные родителей */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold">Данные родителей</h2>
                    <div className="space-y-4">
                        <h3 className="text-md font-medium">Мать</h3>
                        <div className="grid md:grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="mother_full_name"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>ФИО матери *</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center">
                                                <User className="mr-2 h-4 w-4 opacity-70" />
                                                <Input placeholder="ФИО матери" {...field} />
                                            </div>
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="mother_workplace"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Место работы матери *</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center">
                                                <Building className="mr-2 h-4 w-4 opacity-70" />
                                                <Input placeholder="Место работы" {...field} />
                                            </div>
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="mother_phone"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Телефон матери *</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center">
                                                <Phone className="mr-2 h-4 w-4 opacity-70" />
                                                <Input placeholder="+7 (XXX) XXX-XX-XX" {...field} />
                                            </div>
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>
                        <h3 className="text-md font-medium">Отец</h3>
                        <div className="grid md:grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="father_full_name"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>ФИО отца *</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center">
                                                <User className="mr-2 h-4 w-4 opacity-70" />
                                                <Input placeholder="ФИО отца" {...field} />
                                            </div>
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="father_workplace"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Место работы отца *</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center">
                                                <Building className="mr-2 h-4 w-4 opacity-70" />
                                                <Input placeholder="Место работы" {...field} />
                                            </div>
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="father_phone"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Телефон отца *</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center">
                                                <Phone className="mr-2 h-4 w-4 opacity-70" />
                                                <Input placeholder="+7 (XXX) XXX-XX-XX" {...field} />
                                            </div>
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>
                    </div>
                </div>

                {/* Кнопка отправки */}
                <div className="flex justify-end">
                    <Button type="submit">Сохранить изменения</Button>
                </div>
            </form>
        </Form>
    );
};

export default ProfileForm;