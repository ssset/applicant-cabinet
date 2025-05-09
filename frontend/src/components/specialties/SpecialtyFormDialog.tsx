import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

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

interface Building {
    id: number;
    name: string;
    address: string;
}

interface SpecialtyFormDialogProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    isEditing: boolean;
    formData: SpecialtyFormData;
    buildings: Building[] | undefined;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    onBuildingSpecialtyChange: (
        index: number,
        field: 'building_id' | 'budget_places' | 'commercial_places' | 'commercial_price',
        value: string | number
    ) => void;
    onAddBuildingSpecialty: () => void;
    onRemoveBuildingSpecialty: (index: number) => void;
    onSubmit: () => void;
}

const SpecialtyFormDialog: React.FC<SpecialtyFormDialogProps> = ({
                                                                     isOpen,
                                                                     onOpenChange,
                                                                     isEditing,
                                                                     formData,
                                                                     buildings,
                                                                     onInputChange,
                                                                     onBuildingSpecialtyChange,
                                                                     onAddBuildingSpecialty,
                                                                     onRemoveBuildingSpecialty,
                                                                     onSubmit,
                                                                 }) => {
    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{isEditing ? 'Редактировать специальность' : 'Добавить новую специальность'}</DialogTitle>
                    <DialogDescription>
                        Заполните информацию о специальности. Поля, отмеченные звездочкой (*), обязательны для заполнения.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <Label htmlFor="name">Название специальности *</Label>
                            <Input
                                id="name"
                                name="name"
                                value={formData.name}
                                onChange={onInputChange}
                                className="mt-1"
                            />
                        </div>
                        <div>
                            <Label htmlFor="code">Код специальности *</Label>
                            <Input
                                id="code"
                                name="code"
                                value={formData.code}
                                onChange={onInputChange}
                                className="mt-1"
                                placeholder="XX.XX.XX"
                            />
                        </div>
                    </div>
                    <div>
                        <Label htmlFor="description">Описание специальности</Label>
                        <Textarea
                            id="description"
                            name="description"
                            value={formData.description || ''}
                            onChange={onInputChange}
                            className="mt-1"
                            rows={3}
                        />
                    </div>
                    <div>
                        <Label htmlFor="duration">Срок обучения</Label>
                        <Input
                            id="duration"
                            name="duration"
                            value={formData.duration || ''}
                            onChange={onInputChange}
                            className="mt-1"
                            placeholder="Например, 2 года 10 месяцев"
                        />
                    </div>
                    <div>
                        <Label htmlFor="requirements">Вступительные экзамены</Label>
                        <Textarea
                            id="requirements"
                            name="requirements"
                            value={formData.requirements || ''}
                            onChange={onInputChange}
                            className="mt-1"
                            rows={3}
                            placeholder="Укажите необходимые экзамены или требования"
                        />
                    </div>
                    <div>
                        <Label>Привязка к корпусам</Label>
                        <div className="space-y-4 mt-2">
                            {formData.building_specialties?.map((bs, index) => (
                                <div key={index} className="border p-4 rounded-md">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <Label htmlFor={`building-${index}`}>Корпус *</Label>
                                            <Select
                                                value={bs.building_id?.toString() || ''}
                                                onValueChange={(value) =>
                                                    onBuildingSpecialtyChange(index, 'building_id', value)
                                                }
                                            >
                                                <SelectTrigger id={`building-${index}`}>
                                                    <SelectValue placeholder="Выберите корпус" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {buildings?.map((building) => (
                                                        <SelectItem key={building.id} value={building.id.toString()}>
                                                            {building.name} ({building.address})
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div>
                                            <Label htmlFor={`budget_places-${index}`}>Бюджетные места *</Label>
                                            <Input
                                                id={`budget_places-${index}`}
                                                type="number"
                                                value={bs.budget_places || 0}
                                                onChange={(e) =>
                                                    onBuildingSpecialtyChange(index, 'budget_places', e.target.value)
                                                }
                                                min="0"
                                                className="mt-1"
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor={`commercial_places-${index}`}>Коммерческие места *</Label>
                                            <Input
                                                id={`commercial_places-${index}`}
                                                type="number"
                                                value={bs.commercial_places || 0}
                                                onChange={(e) =>
                                                    onBuildingSpecialtyChange(index, 'commercial_places', e.target.value)
                                                }
                                                min="0"
                                                className="mt-1"
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor={`commercial_price-${index}`}>Цена (коммерция) *</Label>
                                            <Input
                                                id={`commercial_price-${index}`}
                                                type="number"
                                                value={bs.commercial_price || 0}
                                                onChange={(e) =>
                                                    onBuildingSpecialtyChange(index, 'commercial_price', e.target.value)
                                                }
                                                min="0"
                                                step="0.01"
                                                className="mt-1"
                                            />
                                        </div>
                                    </div>
                                    <Button
                                        variant="destructive"
                                        size="sm"
                                        className="mt-4"
                                        onClick={() => onRemoveBuildingSpecialty(index)}
                                    >
                                        Удалить корпус
                                    </Button>
                                </div>
                            ))}
                            <Button variant="outline" onClick={onAddBuildingSpecialty}>
                                <Plus className="h-4 w-4 mr-2" /> Добавить корпус
                            </Button>
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Отмена
                    </Button>
                    <Button onClick={onSubmit}>{isEditing ? 'Сохранить' : 'Добавить'}</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default SpecialtyFormDialog;