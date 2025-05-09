import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface Organization {
    id: number;
    name: string;
    city: string;
}

interface InstitutionFilterProps {
    organizations: Organization[];
    selectedInstitutionId: string | null;
    onInstitutionChange: (value: string) => void;
    disabled: boolean;
}

const InstitutionFilter: React.FC<InstitutionFilterProps> = ({
                                                                 organizations,
                                                                 selectedInstitutionId,
                                                                 onInstitutionChange,
                                                                 disabled,
                                                             }) => {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Выберите учебное заведение</CardTitle>
                <CardDescription>
                    После выбора города выберите учебное заведение, чтобы увидеть специальности
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Select
                    onValueChange={onInstitutionChange}
                    value={selectedInstitutionId || ''}
                    disabled={disabled}
                >
                    <SelectTrigger className="w-full md:w-[350px]">
                        <SelectValue placeholder="Выберите учебное заведение" />
                    </SelectTrigger>
                    <SelectContent>
                        {organizations.map((organization) => (
                            <SelectItem key={organization.id} value={organization.id.toString()}>
                                {organization.name}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </CardContent>
        </Card>
    );
};

export default InstitutionFilter;