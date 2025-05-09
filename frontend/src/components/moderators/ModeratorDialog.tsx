import React, { useState, useEffect } from 'react'; // Добавляем useEffect
import { Moderator } from '@/pages/ModeratorsPage';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface ModeratorDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    moderator: Moderator | null;
    onSave: (moderator: Moderator & { password?: string }) => void;
}

const formSchema = z.object({
    id: z.string().optional(),
    email: z.string().email({
        message: "Введите корректный email",
    }),
    password: z.string().min(8, {
        message: "Пароль должен содержать минимум 8 символов",
    }).optional(),
    role: z.literal('moderator'),
});

export const ModeratorDialog: React.FC<ModeratorDialogProps> = ({
                                                                    open,
                                                                    onOpenChange,
                                                                    moderator,
                                                                    onSave,
                                                                }) => {
    const [isSuccess, setIsSuccess] = useState(false);
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            id: moderator?.id || undefined,
            email: moderator?.email || '',
            password: '',
            role: 'moderator',
        },
    });

    // Добавляем/удаляем класс modal-open на body
    useEffect(() => {
        if (open) {
            document.body.classList.add('modal-open');
        } else {
            document.body.classList.remove('modal-open');
        }

        // Очистка при размонтировании компонента
        return () => {
            document.body.classList.remove('modal-open');
        };
    }, [open]);

    React.useEffect(() => {
        if (open) {
            form.reset({
                id: moderator?.id || undefined,
                email: moderator?.email || '',
                password: '',
                role: 'moderator',
            });
            setIsSuccess(false);
        }
    }, [form, moderator, open]);

    const onSubmit = async (values: z.infer<typeof formSchema>) => {
        try {
            await onSave({
                id: values.id,
                email: values.email,
                role: values.role,
                ...(values.password && { password: values.password }),
            } as Moderator & { password?: string });
            setIsSuccess(true);
        } catch (error) {
            // Ошибка обрабатывается в родительском компоненте через toast
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>
                        {moderator ? 'Редактировать модератора' : 'Добавить модератора'}
                    </DialogTitle>
                    <DialogDescription>
                        {moderator
                            ? 'Измените email модератора и нажмите Сохранить'
                            : isSuccess
                                ? 'Модератор будет добавлен после подтверждения email!'
                                : 'Введите email и пароль для добавления нового модератора'}
                    </DialogDescription>
                </DialogHeader>

                {!isSuccess ? (
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-2">
                            <FormField
                                control={form.control}
                                name="email"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Email</FormLabel>
                                        <FormControl>
                                            <Input placeholder="ivan@example.com" type="email" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="password"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Пароль</FormLabel>
                                        <FormControl>
                                            <Input placeholder="Введите пароль" type="password" {...field} disabled={!!moderator} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <div className="flex justify-end space-x-2 pt-4">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => onOpenChange(false)}
                                >
                                    Отмена
                                </Button>
                                <Button type="submit">Сохранить</Button>
                            </div>
                        </form>
                    </Form>
                ) : (
                    <div className="pt-4 text-center">
                        <p className="text-green-600">Модератор будет добавлен после подтверждения email!</p>
                        <Button
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            className="mt-4"
                        >
                            Закрыть
                        </Button>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
};