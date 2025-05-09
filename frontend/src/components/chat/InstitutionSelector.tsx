import React, { useState } from 'react';
import { CheckCircle, Search } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface Institution {
    id: string;
    name: string;
}

interface InstitutionSelectorProps {
    institutions: Institution[];
    existingChats: string[];
    onSelect: (institutionId: string) => void;
}

export const InstitutionSelector: React.FC<InstitutionSelectorProps> = ({
                                                                            institutions,
                                                                            existingChats,
                                                                            onSelect,
                                                                        }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredInstitutions = institutions.filter((institution) =>
        institution.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="flex flex-col max-h-[450px]">
            <div className="px-4 pt-4 pb-2">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                        placeholder="Поиск по названию..."
                        className="pl-10 w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <ScrollArea className="flex-1 px-4 pb-4">
                <div className="space-y-2">
                    {institutions.length === 0 ? (
                        <div className="py-4 text-center text-gray-500">
                            У вас нет доступных организаций для общения. Подайте заявку, чтобы начать чат.
                        </div>
                    ) : filteredInstitutions.length > 0 ? (
                        filteredInstitutions.map((institution) => {
                            const hasExistingChat = existingChats.includes(institution.id);
                            return (
                                <Button
                                    key={institution.id}
                                    variant="outline"
                                    className={`w-full justify-start p-3 h-auto ${
                                        hasExistingChat ? 'border-blue-300 bg-blue-50' : ''
                                    }`}
                                    onClick={() => onSelect(institution.id)}
                                    disabled={hasExistingChat}
                                >
                                    <div className="flex items-center gap-3 w-full overflow-hidden">
                                        <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center flex-shrink-0">
                                            {institution.name.charAt(0)}
                                        </div>
                                        <div className="flex-1 text-left overflow-hidden">
                                            <div className="font-medium truncate">{institution.name}</div>
                                            <div className="text-sm text-gray-500 truncate">{institution.name.slice(0, 3).toUpperCase()}</div>
                                        </div>
                                        {hasExistingChat && (
                                            <CheckCircle className="h-5 w-5 text-blue-500 flex-shrink-0" />
                                        )}
                                    </div>
                                </Button>
                            );
                        })
                    ) : (
                        <div className="py-4 text-center text-gray-500">
                            Учебные заведения не найдены
                        </div>
                    )}
                </div>
            </ScrollArea>
        </div>
    );
};