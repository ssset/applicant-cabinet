import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search } from 'lucide-react';
import SpecialtyCard from './SpecialtyCard';

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

interface SpecialtiesPopupProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    specialties: Specialty[];
    totalPages: number;
    currentPage: number;
    onPageChange: (page: number) => void;
    searchQuery: string;
    onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onEditSpecialty: (specialty: Specialty) => void;
    onDeleteSpecialty: (id: number) => void;
    userRole: string | undefined;
    navigate: (path: string) => void;
}

const SpecialtiesPopup: React.FC<SpecialtiesPopupProps> = ({
                                                               isOpen,
                                                               onOpenChange,
                                                               specialties,
                                                               totalPages,
                                                               currentPage,
                                                               onPageChange,
                                                               searchQuery,
                                                               onSearchChange,
                                                               onEditSpecialty,
                                                               onDeleteSpecialty,
                                                               userRole,
                                                               navigate,
                                                           }) => {
    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-y-auto transition-all duration-300">
                <DialogHeader>
                    <DialogTitle>Специальности</DialogTitle>
                    <DialogDescription>
                        Список доступных специальностей для выбранного учебного заведения.
                    </DialogDescription>
                </DialogHeader>
                <div className="py-4">
                    <div className="mb-6 flex items-center gap-4">
                        <div className="relative flex-1 max-w-md">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input
                                placeholder="Поиск по названию специальности"
                                value={searchQuery}
                                onChange={onSearchChange}
                                className="pl-10"
                            />
                        </div>
                    </div>
                    {specialties && specialties.length > 0 ? (
                        <div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {specialties.map((specialty, index) => (
                                    <SpecialtyCard
                                        key={specialty.id}
                                        specialty={specialty}
                                        index={index}
                                        userRole={userRole}
                                        onEdit={onEditSpecialty}
                                        onDelete={onDeleteSpecialty}
                                        onNavigate={navigate}
                                    />
                                ))}
                            </div>
                            {totalPages > 1 && (
                                <div className="flex justify-center items-center gap-2 mt-6">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={currentPage === 1}
                                        onClick={() => onPageChange(currentPage - 1)}
                                    >
                                        Назад
                                    </Button>
                                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                                        <Button
                                            key={page}
                                            variant={currentPage === page ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => onPageChange(page)}
                                        >
                                            {page}
                                        </Button>
                                    ))}
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={currentPage === totalPages}
                                        onClick={() => onPageChange(currentPage + 1)}
                                    >
                                        Вперед
                                    </Button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-center p-8 bg-gray-50 rounded-lg">
                            <p className="text-gray-600">Нет доступных специальностей</p>
                        </div>
                    )}
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Закрыть
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default SpecialtiesPopup;