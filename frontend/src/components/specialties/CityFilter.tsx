import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface CityFilterProps {
    cities: string[] | undefined;
    selectedCity: string | undefined;
    onCityChange: (value: string) => void;
}

const CityFilter: React.FC<CityFilterProps> = ({ cities, selectedCity, onCityChange }) => {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Фильтр по городу</CardTitle>
                <CardDescription>
                    Выберите город, чтобы увидеть доступные учебные заведения
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Select onValueChange={onCityChange} value={selectedCity || 'all'}>
                    <SelectTrigger className="w-full md:w-[350px]">
                        <SelectValue placeholder="Выберите город" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">Все города</SelectItem>
                        {cities?.map((city) => (
                            <SelectItem key={city} value={city}>
                                {city}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </CardContent>
        </Card>
    );
};

export default CityFilter;