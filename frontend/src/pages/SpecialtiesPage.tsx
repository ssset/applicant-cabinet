import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { useToast } from '@/hooks/use-toast';
import { useNavigate } from 'react-router-dom';
import { useIsMobile } from '@/hooks/use-mobile';
import { institutionAPI, specialtyAPI, buildingAPI } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import AdminInstitutionInfo from '@/components/specialties/AdminInstitutionInfo';
import CityFilter from '@/components/specialties/CityFilter';
import InstitutionFilter from '@/components/specialties/InstitutionFilter';
import SpecialtiesPopup from '@/components/specialties/SpecialtiesPopup';
import SpecialtyFormDialog from '@/components/specialties/SpecialtyFormDialog';
import ErrorBoundary from '@/components/specialties/ErrorBoundary';
import { BookOpen } from 'lucide-react';

interface SpecialtyFormData {
    id?: number;
    name: string;
    code: string;
    description?: string;
    organization?: number;
    duration?: string;
    requirements?: string;
    building_specialties?: Array<{
        building_id: number;
        budget_places: number;
        commercial_places: number;
        commercial_price: number;
    }>;
}

interface Specialty {
    id: number;
    name: string;
    code: string;
    organization: { id: number; name: string };
    created_at: string;
    updated_at: string;
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

interface Organization {
    id: number;
    name: string;
    city: string;
}

interface Building {
    id: number;
    name: string;
    address: string;
}

const emptySpecialtyForm: SpecialtyFormData = {
    name: '',
    code: '',
    description: '',
    duration: '',
    requirements: '',
    building_specialties: [],
};

const ITEMS_PER_PAGE = 20;

const SpecialtiesPage: React.FC = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const { toast } = useToast();
    const isMobile = useIsMobile();
    const [specialtyFormData, setSpecialtyFormData] = useState<SpecialtyFormData>(emptySpecialtyForm);
    const [isEditingSpecialty, setIsEditingSpecialty] = useState(false);
    const [isSpecialtyDialogOpen, setIsSpecialtyDialogOpen] = useState(false);
    const [isSpecialtiesPopupOpen, setIsSpecialtiesPopupOpen] = useState(false);
    const [selectedInstitutionId, setSelectedInstitutionId] = useState<string | null>(null);
    const [selectedCity, setSelectedCity] = useState<string | undefined>(undefined);
    const [searchQuery, setSearchQuery] = useState('');
    const [currentPage, setCurrentPage] = useState(1);

    const { data: cities, isLoading: isCitiesLoading } = useQuery<string[]>({
        queryKey: ['availableCities'],
        queryFn: () => institutionAPI.getAvailableCities(),
        enabled: user?.role === 'applicant',
    });

    const { data: organizations, isLoading: isOrganizationsLoading } = useQuery<Organization[]>({
        queryKey: ['organizations', selectedCity],
        queryFn: () => institutionAPI.getAvailableInstitutions(selectedCity),
        enabled: user?.role === 'applicant',
    });

    const filteredOrganizations = useMemo(() => {
        if (!organizations) return [];
        if (!selectedCity) return organizations;
        return organizations.filter((org) => org.city === selectedCity);
    }, [organizations, selectedCity]);

    const { data: specialties, isLoading: isSpecialtiesLoading } = useQuery<Specialty[]>({
        queryKey: [
            'specialties',
            user?.role ?? 'unknown',
            selectedInstitutionId ?? 'none',
            selectedCity ?? 'all',
        ],
        queryFn: async () => {
            if (user?.role === 'admin_org') {
                return await specialtyAPI.getSpecialties();
            } else if (user?.role === 'applicant') {
                const organizationId = selectedInstitutionId ? parseInt(selectedInstitutionId) : undefined;
                return await specialtyAPI.getAvailableSpecialties(organizationId, selectedCity);
            }
            return [];
        },
        enabled: (user?.role === 'admin_org') || (user?.role === 'applicant' && !!selectedInstitutionId),
        staleTime: 0,
        gcTime: 0,
    });

    const { data: adminInstitution, isLoading: isInstitutionLoading } = useQuery({
        queryKey: ['adminInstitution'],
        queryFn: async () => {
            if (user?.role === 'admin_org') {
                const orgs = await institutionAPI.getInstitutions();
                return orgs[0];
            }
            return null;
        },
        enabled: user?.role === 'admin_org',
    });

    const { data: buildings, isLoading: isBuildingsLoading } = useQuery<Building[]>({
        queryKey: ['buildings'],
        queryFn: async () => {
            if (user?.role === 'admin_org') {
                return await buildingAPI.getBuildings();
            }
            return [];
        },
        enabled: user?.role === 'admin_org',
    });

    useEffect(() => {
        queryClient.invalidateQueries({ queryKey: ['specialties'] });
    }, [selectedInstitutionId, selectedCity, queryClient]);

    const specialtyMutation = useMutation({
        mutationFn: (data: SpecialtyFormData) => {
            if (!adminInstitution?.id) {
                throw new Error('Организация не определена. Пожалуйста, перезагрузите страницу или войдите снова.');
            }
            const payload = {
                ...data,
                organization: adminInstitution.id,
                building_specialties: data.building_specialties?.map((bs) => ({
                    building_id: bs.building_id,
                    budget_places: bs.budget_places,
                    commercial_places: bs.commercial_places,
                    commercial_price: bs.commercial_price,
                })),
            };
            return data.id
                ? specialtyAPI.updateSpecialty(data.id, payload)
                : specialtyAPI.createSpecialty(payload);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['specialties'] });
            setIsSpecialtyDialogOpen(false);
            setSpecialtyFormData(emptySpecialtyForm);
            setIsEditingSpecialty(false);
            toast({
                title: isEditingSpecialty ? 'Специальность обновлена' : 'Специальность добавлена',
                description: `${specialtyFormData.name} (${specialtyFormData.code}) успешно ${isEditingSpecialty ? 'обновлена' : 'добавлена'}`,
            });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || 'Не удалось сохранить специальность',
            });
        },
    });

    const deleteSpecialtyMutation = useMutation({
        mutationFn: (id: number) => specialtyAPI.deleteSpecialty(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['specialties'] });
            toast({
                title: 'Специальность удалена',
                description: 'Специальность успешно удалена',
            });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || 'Не удалось удалить специальность',
            });
        },
    });

    const handleSpecialtyInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setSpecialtyFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleBuildingSpecialtyChange = (
        index: number,
        field: 'building_id' | 'budget_places' | 'commercial_places' | 'commercial_price',
        value: string | number
    ) => {
        setSpecialtyFormData((prev) => {
            const newBuildingSpecialties = [...(prev.building_specialties || [])];
            newBuildingSpecialties[index] = {
                ...newBuildingSpecialties[index],
                [field]: field === 'building_id' ? parseInt(value as string) : parseFloat(value as string),
            };
            return { ...prev, building_specialties: newBuildingSpecialties };
        });
    };

    const addBuildingSpecialty = () => {
        setSpecialtyFormData((prev) => ({
            ...prev,
            building_specialties: [
                ...(prev.building_specialties || []),
                { building_id: 0, budget_places: 0, commercial_places: 0, commercial_price: 0 },
            ],
        }));
    };

    const removeBuildingSpecialty = (index: number) => {
        setSpecialtyFormData((prev) => ({
            ...prev,
            building_specialties: (prev.building_specialties || []).filter((_, i) => i !== index),
        }));
    };

    const handleSpecialtySubmit = () => {
        if (!specialtyFormData.name || !specialtyFormData.code) {
            toast({
                variant: 'destructive',
                title: 'Ошибка валидации',
                description: 'Пожалуйста, заполните все обязательные поля',
            });
            return;
        }
        if (
            specialtyFormData.building_specialties?.some(
                (bs) =>
                    bs.building_id === 0 ||
                    bs.budget_places < 0 ||
                    bs.commercial_places < 0 ||
                    bs.commercial_price < 0
            )
        ) {
            toast({
                variant: 'destructive',
                title: 'Ошибка валидации',
                description: 'Пожалуйста, выберите корпус и укажите корректные значения для мест и цены',
            });
            return;
        }
        specialtyMutation.mutate(specialtyFormData);
    };

    const handleEditSpecialty = (specialty: Specialty) => {
        setSpecialtyFormData({
            id: specialty.id,
            name: specialty.name,
            code: specialty.code,
            description: specialty.description || '',
            duration: specialty.duration || '',
            requirements: specialty.requirements || '',
            building_specialties: specialty.building_specialties.map((bs) => ({
                building_id: bs.building.id,
                budget_places: bs.budget_places,
                commercial_places: bs.commercial_places,
                commercial_price: bs.commercial_price,
            })),
        });
        setIsEditingSpecialty(true);
        setIsSpecialtyDialogOpen(true);
    };

    const handleDeleteSpecialty = (id: number) => {
        if (confirm('Вы уверены, что хотите удалить эту специальность?')) {
            deleteSpecialtyMutation.mutate(id);
        }
    };

    const handleInstitutionChange = (value: string) => {
        setSelectedInstitutionId(value);
    };

    const handleCityChange = (value: string) => {
        setSelectedCity(value === 'all' ? undefined : value);
        setSelectedInstitutionId(null);
        setCurrentPage(1);
    };

    const filteredSpecialties = useMemo(() => {
        if (!specialties) return [];
        return specialties.filter((specialty) =>
            specialty.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [specialties, searchQuery]);

    const totalPages = Math.ceil(filteredSpecialties.length / ITEMS_PER_PAGE);
    const paginatedSpecialties = filteredSpecialties.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    const handlePageChange = (page: number) => {
        setCurrentPage(page);
    };

    const openSpecialtiesPopup = () => {
        if (user?.role === 'applicant' && selectedInstitutionId && selectedCity) {
            setIsSpecialtiesPopupOpen(true);
        }
    };

    if (isSpecialtiesLoading || isInstitutionLoading || isOrganizationsLoading || isBuildingsLoading || isCitiesLoading) {
        return <DashboardLayout><div>Загрузка...</div></DashboardLayout>;
    }

    return (
        <ErrorBoundary>
            <DashboardLayout>
                <div className="p-6">
                    <h1 className="text-2xl font-bold mb-6">
                        {user?.role === 'admin_org' ? 'Управление специальностями' : 'Доступные специальности'}
                    </h1>

                    {user?.role === 'admin_org' && adminInstitution && (
                        <AdminInstitutionInfo
                            institution={adminInstitution}
                            onAddSpecialty={() => {
                                setSpecialtyFormData(emptySpecialtyForm);
                                setIsEditingSpecialty(false);
                                setIsSpecialtyDialogOpen(true);
                            }}
                            onViewSpecialties={() => setIsSpecialtiesPopupOpen(true)}
                        />
                    )}

                    {user?.role === 'applicant' && (
                        <div className="mb-8 space-y-4">
                            <CityFilter
                                cities={cities || []}
                                selectedCity={selectedCity}
                                onCityChange={handleCityChange}
                            />
                            <InstitutionFilter
                                organizations={filteredOrganizations}
                                selectedInstitutionId={selectedInstitutionId}
                                onInstitutionChange={handleInstitutionChange}
                                disabled={!selectedCity}
                            />
                            <button
                                onClick={openSpecialtiesPopup}
                                disabled={!selectedInstitutionId || !selectedCity}
                                className="w-full md:w-auto inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
                            >
                                <BookOpen className="h-4 w-4 mr-2" /> Просмотреть специальности
                            </button>
                        </div>
                    )}

                    <SpecialtiesPopup
                        isOpen={isSpecialtiesPopupOpen}
                        onOpenChange={setIsSpecialtiesPopupOpen}
                        specialties={paginatedSpecialties}
                        totalPages={totalPages}
                        currentPage={currentPage}
                        onPageChange={handlePageChange}
                        searchQuery={searchQuery}
                        onSearchChange={(e) => {
                            setSearchQuery(e.target.value);
                            setCurrentPage(1);
                        }}
                        onEditSpecialty={handleEditSpecialty}
                        onDeleteSpecialty={handleDeleteSpecialty}
                        userRole={user?.role}
                        navigate={navigate}
                    />

                    {user?.role === 'admin_org' && (
                        <SpecialtyFormDialog
                            isOpen={isSpecialtyDialogOpen}
                            onOpenChange={setIsSpecialtyDialogOpen}
                            isEditing={isEditingSpecialty}
                            formData={specialtyFormData}
                            buildings={buildings}
                            onInputChange={handleSpecialtyInputChange}
                            onBuildingSpecialtyChange={handleBuildingSpecialtyChange}
                            onAddBuildingSpecialty={addBuildingSpecialty}
                            onRemoveBuildingSpecialty={removeBuildingSpecialty}
                            onSubmit={handleSpecialtySubmit}
                        />
                    )}
                </div>
            </DashboardLayout>
        </ErrorBoundary>
    );
};

export default SpecialtiesPage;