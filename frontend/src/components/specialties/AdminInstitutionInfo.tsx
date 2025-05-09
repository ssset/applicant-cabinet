import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Building, Plus, BookOpen } from 'lucide-react';

interface AdminInstitutionInfoProps {
    institution: {
        name: string;
        address: string;
        phone: string;
        email: string;
    };
    onAddSpecialty: () => void;
    onViewSpecialties: () => void;
}

const AdminInstitutionInfo: React.FC<AdminInstitutionInfoProps> = ({
                                                                       institution,
                                                                       onAddSpecialty,
                                                                       onViewSpecialties,
                                                                   }) => {
    return (
        <>
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
                <div>
                    <p className="text-gray-500">{institution.name}</p>
                </div>
                <div className="flex gap-4 mt-4 md:mt-0">
                    <Button onClick={onAddSpecialty}>
                        <Plus className="h-4 w-4 mr-2" /> Добавить специальность
                    </Button>
                    <Button
                        onClick={onViewSpecialties}
                        className="bg-blue-600 hover:bg-blue-700"
                    >
                        <BookOpen className="h-4 w-4 mr-2" /> Посмотреть специальности
                    </Button>
                </div>
            </div>
            <Card className="mb-8">
                <CardHeader>
                    <CardTitle className="flex items-center">
                        <Building className="h-5 w-5 mr-2" /> Информация об учебном заведении
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        <p><strong>Название:</strong> {institution.name}</p>
                        <p><strong>Адрес:</strong> {institution.address}</p>
                        <p><strong>Телефон:</strong> {institution.phone}</p>
                        <p><strong>Email:</strong> {institution.email}</p>
                    </div>
                </CardContent>
            </Card>
        </>
    );
};

export default AdminInstitutionInfo;