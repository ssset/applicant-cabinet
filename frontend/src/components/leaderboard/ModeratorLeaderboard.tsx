import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Crown, Medal, Award, Search, SortDesc, SortAsc } from "lucide-react";
import { specialtyAPI } from '@/services/api';

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

export const ModeratorLeaderboard = () => {
    const [selectedBuildingSpecialty, setSelectedBuildingSpecialty] = useState<string>("");
    const [students, setStudents] = useState<LeaderboardStudent[]>([]);
    const [searchQuery, setSearchQuery] = useState<string>("");
    const [sortDirection] = useState<'asc' | 'desc'>('desc'); // Сортировка уже выполнена на бэкенде
    const [specialties, setSpecialties] = useState<any[]>([]);

    useEffect(() => {
        const fetchSpecialties = async () => {
            try {
                const response = await specialtyAPI.getSpecialties();
                setSpecialties(response);
            } catch (error) {
                console.error('Failed to fetch specialties:', error);
            }
        };
        fetchSpecialties();
    }, []);

    useEffect(() => {
        if (selectedBuildingSpecialty) {
            const fetchLeaderboard = async () => {
                try {
                    const response = await specialtyAPI.getLeaderboard(parseInt(selectedBuildingSpecialty));
                    setStudents(response.leaderboard);
                } catch (error) {
                    console.error('Failed to fetch leaderboard:', error);
                }
            };
            fetchLeaderboard();
        } else {
            setStudents([]);
        }
    }, [selectedBuildingSpecialty]);

    const filteredStudents = students.filter(student =>
        searchQuery === "" ||
        `${student.applicant_profile.last_name} ${student.applicant_profile.first_name} ${student.applicant_profile.middle_name || ''}`
            .toLowerCase()
            .includes(searchQuery.toLowerCase())
    );

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

    const selectedSpecialtyName = selectedBuildingSpecialty
        ? specialties.find(s =>
        s.building_specialties.some((bs: any) => bs.id === parseInt(selectedBuildingSpecialty))
    )?.name || ""
        : "";

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className="w-full sm:w-80">
                    <Select value={selectedBuildingSpecialty} onValueChange={setSelectedBuildingSpecialty}>
                        <SelectTrigger>
                            <SelectValue placeholder="Выберите специальность" />
                        </SelectTrigger>
                        <SelectContent>
                            {specialties.map(specialty => (
                                specialty.building_specialties.map((bs: any) => (
                                    <SelectItem key={bs.id} value={bs.id.toString()}>
                                        {specialty.name} ({specialty.code})
                                    </SelectItem>
                                ))
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="flex gap-2 w-full sm:w-auto">
                    <div className="relative flex-1">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Поиск абитуриента..."
                            className="pl-8"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {selectedBuildingSpecialty ? (
                <Card>
                    <CardHeader className="pb-0">
                        <CardTitle className="text-xl">
                            Рейтинг абитуриентов: {selectedSpecialtyName}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[500px] rounded-md">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-12">Место</TableHead>
                                        <TableHead>ФИО абитуриента</TableHead>
                                        <TableHead className="text-right">Средний балл</TableHead>
                                        <TableHead className="text-right">Дата подачи</TableHead>
                                        <TableHead className="text-right">Статус</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredStudents.length > 0 ? (
                                        filteredStudents.map((student, index) => {
                                            const position = student.rank;
                                            let icon = null;

                                            if (position === 1) {
                                                icon = <Crown className="w-4 h-4 text-yellow-500 ml-1" />;
                                            } else if (position === 2) {
                                                icon = <Medal className="w-4 h-4 text-slate-400 ml-1" />;
                                            } else if (position === 3) {
                                                icon = <Medal className="w-4 h-4 text-amber-700 ml-1" />;
                                            }

                                            const profile = student.applicant_profile;
                                            const name = `${profile.last_name} ${profile.first_name} ${profile.middle_name || ''}`.trim();
                                            const statusInfo = getStatusLabel(student.status);

                                            return (
                                                <TableRow key={student.id} className={index < 3 ? "bg-muted/30" : ""}>
                                                    <TableCell className="font-medium">
                                                        <div className="flex items-center">
                                                            {position}
                                                            {icon}
                                                        </div>
                                                    </TableCell>
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
                                        })
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
                                                {searchQuery ? "Абитуриенты не найдены" : "Нет данных для отображения"}
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </ScrollArea>
                    </CardContent>
                </Card>
            ) : (
                <div className="flex items-center justify-center p-10 rounded-md border border-dashed">
                    <p className="text-muted-foreground">Выберите специальность для просмотра рейтинга абитуриентов</p>
                </div>
            )}
        </div>
    );
};