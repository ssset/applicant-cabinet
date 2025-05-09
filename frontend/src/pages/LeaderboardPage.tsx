import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { useAuth } from '@/hooks/useAuth';
import { ModeratorLeaderboard } from '@/components/leaderboard/ModeratorLeaderboard';
import SpecialtyCard from '@/components/leaderboard/LeaderboardDialog';
import { specialtyAPI, institutionAPI } from '@/services/api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const LeaderboardPage = () => {
    const { user } = useAuth();
    const userRole = user?.role;
    const isApplicant = userRole === 'applicant';
    const isModeratorOrAdminOrg = userRole === 'moderator' || userRole === 'admin_org';

    const [organizations, setOrganizations] = useState<any[]>([]);
    const [selectedOrganization, setSelectedOrganization] = useState<string>("");
    const [specialties, setSpecialties] = useState<any[]>([]);

    // Загружаем доступные организации для абитуриента
    useEffect(() => {
        if (isApplicant) {
            const fetchOrganizations = async () => {
                try {
                    const response = await institutionAPI.getAvailableInstitutions();
                    setOrganizations(response);
                } catch (error) {
                    console.error('Failed to fetch organizations:', error);
                }
            };
            fetchOrganizations();
        }
    }, [isApplicant]);


    useEffect(() => {
        const fetchSpecialties = async () => {
            try {
                let response;
                if (isApplicant && selectedOrganization) {
                    response = await specialtyAPI.getAvailableSpecialties(parseInt(selectedOrganization));
                } else if (isModeratorOrAdminOrg) {
                    response = await specialtyAPI.getSpecialties();
                } else {
                    response = [];
                }
                setSpecialties(response);
            } catch (error) {
                console.error('Failed to fetch specialties:', error);
            }
        };
        fetchSpecialties();
    }, [isApplicant, isModeratorOrAdminOrg, selectedOrganization]);

    return (
        <SidebarProvider defaultOpen>
            <div className="min-h-screen flex w-full bg-gray-50">
                <DashboardSidebar />

                <SidebarInset className="p-4 md:p-6 w-full overflow-hidden">
                    <h1 className="text-2xl font-bold mb-6">Рейтинг абитуриентов</h1>

                    {isApplicant && (
                        <div className="space-y-6 h-[calc(100vh-120px)] flex flex-col">
                            <div className="flex flex-col gap-4">
                                <p className="text-muted-foreground">
                                    Выберите образовательное учреждение для просмотра рейтинга.
                                </p>
                                <div className="w-full sm:w-80">
                                    <Select value={selectedOrganization} onValueChange={setSelectedOrganization}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Выберите образовательное учреждение" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {organizations.map(org => (
                                                <SelectItem key={org.id} value={org.id.toString()}>
                                                    {org.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            {selectedOrganization ? (
                                <div className="flex-1">
                                    {specialties.length > 0 ? (
                                        <div className="h-[640px] border rounded-md p-4">
                                            <SpecialtyList specialties={specialties} />
                                        </div>
                                    ) : (
                                        <div className="flex items-center justify-center h-64 border rounded-md">
                                            <p className="text-muted-foreground">
                                                Нет доступных специальностей для выбранного учреждения.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="flex items-center justify-center h-64 border rounded-md">
                                    <p className="text-muted-foreground">
                                        Выберите образовательное учреждение для просмотра специальностей.
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {isModeratorOrAdminOrg && (
                        <div className="h-[calc(100vh-120px)] flex flex-col">
                            <ModeratorLeaderboard />
                        </div>
                    )}

                    {!isApplicant && !isModeratorOrAdminOrg && (
                        <div className="flex items-center justify-center h-64 border rounded-md">
                            <p className="text-muted-foreground">
                                Доступ к рейтингу есть только у абитуриентов, модераторов и администраторов организаций
                            </p>
                        </div>
                    )}
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
};


const SpecialtyList = ({ specialties }: { specialties: any[] }) => {
    const [searchQuery, setSearchQuery] = useState<string>("");

    const filteredSpecialties = specialties.filter(specialty =>
        searchQuery === "" ||
        specialty.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        specialty.code.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="flex flex-col h-full">
            <div className="mb-4">
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Поиск специальностей..."
                        className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <svg
                        className="absolute left-3 top-2.5 h-5 w-5 text-muted-foreground"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 1116.65 16.65z"
                        />
                    </svg>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2">
                <div className="space-y-4">
                    {filteredSpecialties.map((specialty: any) =>
                        specialty.building_specialties.map((bs: any) => (
                            <SpecialtyCard
                                key={bs.id}
                                id={specialty.id}
                                buildingSpecialtyId={bs.id}
                                name={specialty.name}
                                code={specialty.code}
                                description={specialty.requirements}
                            />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default LeaderboardPage;