import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog';
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface Application {
    id: number;
    applicant_profile: { first_name: string; last_name: string; patronymic: string };
    building_specialty: { specialty: { name: string } };
    status: 'pending' | 'accepted' | 'rejected';
    reject_reason?: string;
}

interface RejectionDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (reason: string) => void;
    application: Application | null;
}

const rejectionSchema = z.object({
    reason: z.string().min(3, {
        message: 'Необходимо указать причину отклонения (минимум 3 символа)',
    }),
});

type RejectionFormValues = z.infer<typeof rejectionSchema>;

export function RejectionDialog({
                                    open,
                                    onOpenChange,
                                    onSubmit,
                                    application,
                                }: RejectionDialogProps) {
    const form = useForm<RejectionFormValues>({
        resolver: zodResolver(rejectionSchema),
        defaultValues: {
            reason: '',
        },
    });

    // Добавляем/убираем класс modal-open на body
    useEffect(() => {
        if (open) {
            document.body.classList.add('modal-open');
        } else {
            document.body.classList.remove('modal-open');
        }

        // Убираем класс при размонтировании компонента
        return () => {
            document.body.classList.remove('modal-open');
        };
    }, [open]);

    const handleSubmit = (values: RejectionFormValues) => {
        onSubmit(values.reason);
        form.reset();
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Укажите причину отклонения</DialogTitle>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                        {application && (
                            <div className="bg-gray-50 p-3 rounded">
                                <p className="text-sm font-medium">
                                    Заявка: {`${application.applicant_profile.last_name} ${application.applicant_profile.first_name} ${application.applicant_profile.patronymic || ''}`}
                                </p>
                                <p className="text-sm text-gray-500">Специальность: {application.building_specialty.specialty.name}</p>
                            </div>
                        )}

                        <FormField
                            control={form.control}
                            name="reason"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Причина отклонения</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            placeholder="Укажите причину отклонения заявки..."
                                            className="resize-none"
                                            rows={4}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                                Отмена
                            </Button>
                            <Button type="submit">Отклонить заявку</Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}