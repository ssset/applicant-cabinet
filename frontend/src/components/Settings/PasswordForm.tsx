// src/components/settings/PasswordForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation } from '@tanstack/react-query';
import { Lock } from 'lucide-react';

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
import { useToast } from '@/components/ui/use-toast';
import { userAPI } from '@/services/api';

const passwordSchema = z
    .object({
        old_password: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
        new_password: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
        confirm_password: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
    })
    .refine((data) => data.new_password === data.confirm_password, {
        message: 'Пароли не совпадают',
        path: ['confirm_password'],
    });

type PasswordFormValues = z.infer<typeof passwordSchema>;

export const PasswordForm: React.FC = () => {
    const { toast } = useToast();

    const form = useForm<PasswordFormValues>({
        resolver: zodResolver(passwordSchema),
        defaultValues: {
            old_password: '',
            new_password: '',
            confirm_password: '',
        },
    });

    const updatePasswordMutation = useMutation({
        mutationFn: (data: { old_password: string; new_password: string }) =>
            userAPI.updatePassword(data),
        onSuccess: () => {
            toast({
                title: 'Пароль обновлён',
                description: 'Ваш пароль успешно изменён.',
            });
            form.reset();
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.response?.data?.error || 'Не удалось обновить пароль.',
            });
        },
    });

    const onSubmit = (data: PasswordFormValues) => {
        updatePasswordMutation.mutate({
            old_password: data.old_password,
            new_password: data.new_password,
        });
    };

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                    control={form.control}
                    name="old_password"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Текущий пароль *</FormLabel>
                            <FormControl>
                                <div className="flex items-center">
                                    <Lock className="mr-2 h-4 w-4 opacity-70" />
                                    <Input placeholder="••••••••" type="password" {...field} />
                                </div>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="new_password"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Новый пароль *</FormLabel>
                            <FormControl>
                                <div className="flex items-center">
                                    <Lock className="mr-2 h-4 w-4 opacity-70" />
                                    <Input placeholder="••••••••" type="password" {...field} />
                                </div>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="confirm_password"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Подтвердите новый пароль *</FormLabel>
                            <FormControl>
                                <div className="flex items-center">
                                    <Lock className="mr-2 h-4 w-4 opacity-70" />
                                    <Input placeholder="••••••••" type="password" {...field} />
                                </div>
                            </FormControl>
                            <FormMessage />
                        </FormItem>
                    )}
                />
                <div className="flex justify-end">
                    <Button type="submit">Обновить пароль</Button>
                </div>
            </form>
        </Form>
    );
};

export default PasswordForm;