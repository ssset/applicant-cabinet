import React, { useState } from 'react';
import { Moderator } from '@/pages/ModeratorsPage';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MoreHorizontal, Search, Edit, Trash2 } from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ModeratorsListProps {
    moderators: Moderator[];
    onEdit: (moderator: Moderator) => void;
    onDelete: (moderatorId: string) => void;
}

export const ModeratorsList: React.FC<ModeratorsListProps> = ({
                                                                  moderators,
                                                                  onEdit,
                                                                  onDelete,
                                                              }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredModerators = moderators.filter(
        (moderator) =>
            moderator.email?.toLowerCase().includes(searchTerm.toLowerCase()) || false
    );

    return (
        <div className="space-y-4">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                    placeholder="Поиск модераторов..."
                    className="pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            <div className="bg-white rounded-md border overflow-y-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
                {filteredModerators.length > 0 ? (
                    filteredModerators.map((moderator) => (
                        <div
                            key={moderator.id || `temp-${moderator.email}`}
                            className="flex items-center justify-between p-4 border-b last:border-b-0 hover:bg-gray-50 transition-colors"
                        >
                            <div className="flex items-center space-x-4">
                                <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                                    <span className="text-gray-500">{moderator.email.charAt(0).toUpperCase()}</span>
                                </div>
                                <span className="font-medium">{moderator.email}</span>
                            </div>
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                        <MoreHorizontal className="h-4 w-4" />
                                        <span className="sr-only">Открыть меню</span>
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={() => onEdit(moderator)}>
                                        <Edit className="mr-2 h-4 w-4" />
                                        <span>Редактировать</span>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                        className="text-red-600 focus:text-red-600"
                                        onClick={() => onDelete(moderator.id)}
                                    >
                                        <Trash2 className="mr-2 h-4 w-4" />
                                        <span>Удалить</span>
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    ))
                ) : (
                    <div className="p-4 text-center text-gray-500">Модераторы не найдены</div>
                )}
            </div>
        </div>
    );
};