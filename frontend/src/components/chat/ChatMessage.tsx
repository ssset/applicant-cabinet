import React from 'react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

interface ChatMessageProps {
    message: {
        id: string;
        content: string;
        sender: { id: string; email: string; role: string };
        sender_email: string;
        sender_role: string;
        created_at: string;
    };
    isCurrentUser: boolean;
}

// Функция для преобразования роли в читаемый вид
const getRoleLabel = (role: string) => {
    switch (role) {
        case 'applicant':
            return 'Абитуриент';
        case 'moderator':
            return 'Модератор';
        case 'admin_org':
            return 'Администратор';
        default:
            return role;
    }
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isCurrentUser }) => {
    const formattedTime = format(new Date(message.created_at), 'HH:mm', { locale: ru });

    return (
        <div className={`flex ${isCurrentUser ? 'justify-end' : 'justify-start'} mb-4`}>
            <div
                className={`max-w-[80%] rounded-lg p-3 shadow-sm ${
                    isCurrentUser ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'
                }`}
            >
                <div className="flex justify-between items-start mb-1">
                    <div className="text-sm font-medium">
                        {message.sender_email} ({getRoleLabel(message.sender_role)})
                    </div>
                </div>
                <div className="break-words">{message.content}</div>
                <div
                    className={`text-xs mt-1 text-right ${
                        isCurrentUser ? 'text-blue-100' : 'text-gray-500'
                    }`}
                >
                    {formattedTime}
                </div>
            </div>
        </div>
    );
};