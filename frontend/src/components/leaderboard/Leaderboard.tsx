import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Crown, Medal, Award } from "lucide-react";

interface LeaderboardStudent {
    id: number;
    applicant_email: string;
    applicant_profile: {
        first_name: string;
        last_name: string;
        middle_name: string;
        average_grade: number;
    };
    created_at: string;
    status: string;
    rank: number;
}

interface LeaderboardProps {
    students: LeaderboardStudent[];
    specialtyName: string;
    open: boolean;
    onClose: () => void;
}

const Leaderboard = ({ students, specialtyName, open, onClose }: LeaderboardProps) => {
    const sortedStudents = [...students];

    const topStudents = sortedStudents.slice(0, 3);
    const otherStudents = sortedStudents.slice(3);

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'accepted':
                return { label: 'Принят', className: 'bg-green-50 text-green-700 ring-green-600/20' };
            case 'rejected':
                return { label: 'Отклонён', className: 'bg-red-50 text-red-700 ring-red-600/20' };
            default:
                return { label: 'На рассмотрении', className: 'bg-yellow-50 text-yellow-700 ring-yellow-600/20' };
        }
    };

    return (
        <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="text-2xl font-bold text-center">
                        Рейтинг абитуриентов: {specialtyName}
                    </DialogTitle>
                </DialogHeader>

                {sortedStudents.length === 0 ? (
                    <div className="flex items-center justify-center h-64 text-muted-foreground">
                        <p>
                            На эту специальность пока никто не подал заявление. Станьте первым!
                        </p>
                    </div>
                ) : (
                    <>
                        {topStudents.length > 0 && (
                            <div className="mb-6">
                                <h3 className="text-lg font-medium mb-4 text-center">Топ абитуриенты</h3>
                                <div className="flex justify-center gap-4 flex-wrap">
                                    {topStudents.map((student, index) => {
                                        const position = index + 1;
                                        let bgColor = "bg-white";
                                        let icon = <Award className="w-6 h-6 text-blue-500" />;

                                        if (position === 1) {
                                            bgColor = "bg-gradient-to-b from-yellow-100 to-yellow-50";
                                            icon = <Crown className="w-6 h-6 text-yellow-500" />;
                                        } else if (position === 2) {
                                            bgColor = "bg-gradient-to-b from-slate-100 to-slate-50";
                                            icon = <Medal className="w-6 h-6 text-slate-400" />;
                                        } else if (position === 3) {
                                            bgColor = "bg-gradient-to-b from-amber-100 to-amber-50";
                                            icon = <Medal className="w-6 h-6 text-amber-700" />;
                                        }

                                        const profile = student.applicant_profile;
                                        const name = `${profile.last_name} ${profile.first_name} ${profile.middle_name || ''}`.trim();

                                        return (
                                            <div
                                                key={student.id}
                                                className={`${bgColor} rounded-lg p-4 shadow-md flex flex-col items-center justify-center w-[220px] border border-gray-100`}
                                            >
                                                <div className="mb-2">{icon}</div>
                                                <div className="font-semibold text-center">{name}</div>
                                                <div className="text-2xl font-bold text-primary mt-1">{profile.average_grade}</div>
                                                <div className="text-xs text-gray-500 mt-1">Средний балл</div>
                                                <div className="text-xs text-gray-500 mt-2">
                                                    Дата подачи: {new Date(student.created_at).toLocaleDateString('ru-RU')}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        <ScrollArea className="flex-1 rounded border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-12 text-center">№</TableHead>
                                        <TableHead>ФИО</TableHead>
                                        <TableHead className="text-right">Средний балл</TableHead>
                                        <TableHead className="text-right">Дата подачи</TableHead>
                                        <TableHead className="text-right">Статус</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {sortedStudents.map((student, index) => {
                                        const profile = student.applicant_profile;
                                        const name = `${profile.last_name} ${profile.first_name} ${profile.middle_name || ''}`.trim();
                                        const statusInfo = getStatusLabel(student.status);

                                        return (
                                            <TableRow key={student.id} className={index < 3 ? "bg-muted/30" : ""}>
                                                <TableCell className="text-center font-medium">{student.rank}</TableCell>
                                                <TableCell>{name}</TableCell>
                                                <TableCell className="text-right font-semibold">
                                                    {profile.average_grade}
                                                </TableCell>
                                                <TableCell className="text-right text-muted-foreground">
                                                    {new Date(student.created_at).toLocaleDateString('ru-RU')}
                                                </TableCell>
                                                <TableCell className="text-right">
                          <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset ${statusInfo.className}`}>
                            {statusInfo.label}
                          </span>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        </ScrollArea>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
};

export default Leaderboard;