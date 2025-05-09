import React, { useState, useEffect } from 'react';
import { Search, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';

interface Application {
    id: number;
    applicant_profile: { first_name: string; last_name: string; patronymic: string };
    building_specialty: { specialty: { name: string } };
    status: 'pending' | 'accepted' | 'rejected';
    reject_reason?: string;
}

interface ApplicationsDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    applications: Application[];
    title: string;
    onApprove: (application: Application) => void;
    onReject: (application: Application) => void;
}

export function ApplicationsDialog({
                                       open,
                                       onOpenChange,
                                       applications,
                                       title,
                                       onApprove,
                                       onReject,
                                   }: ApplicationsDialogProps) {
    const [searchTerm, setSearchTerm] = useState('');

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

    const filteredApplications = applications.filter(
        (app) =>
            `${app.applicant_profile.first_name} ${app.applicant_profile.last_name}`
                .toLowerCase()
                .includes(searchTerm.toLowerCase()) ||
            app.building_specialty.specialty.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[800px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                </DialogHeader>

                <div className="relative w-full mb-4">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Поиск..."
                        className="pl-8"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>ID</TableHead>
                            <TableHead>ФИО</TableHead>
                            <TableHead>Специальность</TableHead>
                            <TableHead>Статус</TableHead>
                            <TableHead>Действия</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filteredApplications.length > 0 ? (
                            filteredApplications.map((app) => (
                                <TableRow key={app.id}>
                                    <TableCell>{app.id}</TableCell>
                                    <TableCell className="font-medium">
                                        {`${app.applicant_profile.last_name} ${app.applicant_profile.first_name} ${app.applicant_profile.patronymic || ''}`}
                                    </TableCell>
                                    <TableCell className="max-w-[200px] truncate">
                                        {app.building_specialty.specialty.name}
                                    </TableCell>
                                    <TableCell>
                    <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                            app.status === 'pending'
                                ? 'bg-yellow-100 text-yellow-800'
                                : app.status === 'accepted'
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-red-100 text-red-800'
                        }`}
                    >
                      {app.status === 'pending'
                          ? 'Ожидает'
                          : app.status === 'accepted'
                              ? 'Одобрена'
                              : 'Отклонена'}
                    </span>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            {app.status === 'pending' && (
                                                <>
                                                    <Button
                                                        size="sm"
                                                        className="bg-green-500 hover:bg-green-600"
                                                        onClick={() => onApprove(app)}
                                                    >
                                                        <Check className="w-4 h-4" />
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="destructive"
                                                        onClick={() => onReject(app)}
                                                    >
                                                        <X className="w-4 h-4" />
                                                    </Button>
                                                </>
                                            )}
                                            {app.status === 'rejected' && app.reject_reason && (
                                                <div className="text-xs text-gray-500 mt-1">
                                                    Причина: {app.reject_reason}
                                                </div>
                                            )}
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={5} className="text-center py-4">
                                    Заявки не найдены
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </DialogContent>
        </Dialog>
    );
}