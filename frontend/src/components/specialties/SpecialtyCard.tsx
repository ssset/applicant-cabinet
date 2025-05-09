import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { GraduationCap, Clock, Info, MapPin, School, Wallet, Pencil, Trash2 } from 'lucide-react';

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

interface SpecialtyCardProps {
    specialty: Specialty;
    index: number;
    userRole: string | undefined;
    onEdit: (specialty: Specialty) => void;
    onDelete: (id: number) => void;
    onNavigate: (path: string) => void;
}

const SpecialtyCard: React.FC<SpecialtyCardProps> = ({ specialty, index, userRole, onEdit, onDelete, onNavigate }) => {
    return (
        <div className={index % 2 === 0 ? 'flex flex-col md:flex-row' : 'flex flex-col md:flex-row-reverse'}>
            <Card className="w-full mb-4 md:mb-0 transition-all hover:shadow-lg">
                <CardHeader>
                    <CardTitle className="flex items-center">
                        <GraduationCap className="w-5 h-5 text-blue-500 mr-2" />
                        {specialty.name}
                    </CardTitle>
                    <CardDescription>
                        Код: {specialty.code}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Accordion type="single" collapsible>
                        <AccordionItem value="details">
                            <AccordionTrigger>Подробная информация</AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-3 text-sm">
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-gray-500" />
                                        <span>
                                            <b>Срок обучения:</b> {specialty.duration || 'Не указано'}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Info className="h-4 w-4 text-gray-500" />
                                        <span>
                                            <b>Вступительные экзамены:</b> {specialty.requirements || 'Не указано'}
                                        </span>
                                    </div>
                                    {specialty.building_specialties.length > 0 ? (
                                        specialty.building_specialties.map((bs) => (
                                            <div key={bs.id}>
                                                <div className="flex items-center gap-2">
                                                    <MapPin className="h-4 w-4 text-gray-500" />
                                                    <span>
                                                        <b>Расположение:</b> {bs.building.address}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <School className="h-4 w-4 text-gray-500" />
                                                    <span>
                                                        <b>Бюджетные места:</b> {bs.budget_places}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Wallet className="h-4 w-4 text-gray-500" />
                                                    <span>
                                                        <b>Коммерческие места:</b> {bs.commercial_places}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Wallet className="h-4 w-4 text-gray-500" />
                                                    <span>
                                                        <b>Стоимость (коммерция):</b> {bs.commercial_price} руб.
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="flex items-center gap-2">
                                            <MapPin className="h-4 w-4 text-gray-500" />
                                            <span>
                                                <b>Расположение:</b> Не указано
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </AccordionContent>
                        </AccordionItem>
                    </Accordion>
                </CardContent>
                <CardFooter>
                    {userRole === 'applicant' ? (
                        <Button
                            className="w-full"
                            onClick={() => onNavigate(`/application/${specialty.id}/${specialty.organization.id}`)}
                        >
                            Подать заявку
                        </Button>
                    ) : (
                        <div className="flex justify-between w-full">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => onEdit(specialty)}
                            >
                                <Pencil className="h-4 w-4 mr-1" /> Изменить
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                className="text-red-600"
                                onClick={() => onDelete(specialty.id)}
                            >
                                <Trash2 className="h-4 w-4 mr-1" /> Удалить
                            </Button>
                        </div>
                    )}
                </CardFooter>
            </Card>
        </div>
    );
};

export default SpecialtyCard;