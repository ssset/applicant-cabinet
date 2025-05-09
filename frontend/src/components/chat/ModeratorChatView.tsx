import React, { useState, useEffect, useRef } from 'react';
import { Send, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { messageAPI } from '@/services/api';

interface Chat {
    id: string;
    applicant: { id: string; email: string };
    applicant_email: string;
    organization: { id: string; name: string };
    organization_name: string;
    messages: Message[];
    created_at: string;
    updated_at: string;
}

interface Message {
    id: string;
    sender: { id: string; email: string; role: string };
    sender_email: string;
    sender_role: string;
    content: string;
    created_at: string;
}

export const ModeratorChatView = () => {
    const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
    const [newMessage, setNewMessage] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const scrollRef = useRef<HTMLDivElement>(null);

    const {
        data: chats = [],
        isLoading: isLoadingChats,
        error: chatsError,
    } = useQuery({
        queryKey: ['chats'],
        queryFn: messageAPI.getChats,
        refetchInterval: selectedChatId ? 2000 : 10000,
        refetchIntervalInBackground: false,
    });

    const {
        data: selectedChat,
        isLoading: isLoadingMessages,
        error: messagesError,
    } = useQuery({
        queryKey: ['chat', selectedChatId],
        queryFn: () => messageAPI.getChatDetails(selectedChatId!),
        enabled: !!selectedChatId,
        refetchInterval: 2000,
        refetchIntervalInBackground: false,
    });

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [selectedChat?.messages]);

    const sendMessageMutation = useMutation({
        mutationFn: (content: string) => messageAPI.sendMessage(selectedChatId!, content),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['chat', selectedChatId] });
            setNewMessage('');
            toast({
                title: 'Сообщение отправлено',
                description: 'Ваше сообщение успешно отправлено',
            });
        },
        onError: (error: any) => {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: error.message || 'Не удалось отправить сообщение',
            });
        },
    });

    const getUnreadCount = (chat: Chat) => {
        return chat.messages.filter(
            (msg) => msg.sender_role === 'applicant' && new Date(msg.created_at) > new Date(chat.updated_at)
        ).length;
    };

    const filteredChats = chats.filter((chat: Chat) =>
        chat.applicant_email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleSendMessage = () => {
        if (newMessage.trim() === '' || !selectedChatId) return;
        sendMessageMutation.mutate(newMessage);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleSelectChat = (chatId: string) => {
        setSelectedChatId(chatId);
    };

    useEffect(() => {
        if (chatsError) {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: 'Не удалось загрузить чаты',
            });
        }
    }, [chatsError, toast]);

    useEffect(() => {
        if (messagesError) {
            toast({
                variant: 'destructive',
                title: 'Ошибка',
                description: 'Не удалось загрузить сообщения',
            });
        }
    }, [messagesError, toast]);

    return (
        <div className="flex h-[calc(100vh-150px)] gap-4">
            {/* Список чатов */}
            <Card className="w-1/3 max-w-xs p-4 flex flex-col">
                <div className="mb-4 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                        placeholder="Поиск абитуриентов..."
                        className="pl-10"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <ScrollArea className="flex-1">
                    {isLoadingChats ? (
                        <div className="py-4 text-center text-gray-500">Загрузка...</div>
                    ) : (
                        <div className="space-y-2">
                            {filteredChats.length > 0 ? (
                                filteredChats.map((chat: Chat) => {
                                    const unreadCount = getUnreadCount(chat);
                                    return (
                                        <div
                                            key={chat.id}
                                            className={`p-3 rounded-lg cursor-pointer transition-colors ${
                                                selectedChatId === chat.id ? 'bg-blue-100' : 'hover:bg-gray-100'
                                            }`}
                                            onClick={() => handleSelectChat(chat.id)}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center">
                                                    {chat.applicant_email.charAt(0)}
                                                </div>
                                                <div className="flex-1">
                                                    <p className="font-medium">{chat.applicant_email}</p>
                                                    <p className="text-sm text-gray-500">ID: {chat.applicant.id}</p>
                                                </div>
                                            </div>
                                            {unreadCount > 0 && (
                                                <div className="mt-1 flex justify-end">
                                                    <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                                                        {unreadCount}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })
                            ) : (
                                <div className="py-4 text-center text-gray-500">Чаты не найдены</div>
                            )}
                        </div>
                    )}
                </ScrollArea>
            </Card>

            {/* Окно чата */}
            <div className="flex-1 flex flex-col h-full">
                {selectedChatId ? (
                    <>
                        <Card className="flex-1 mb-4 p-4">
                            <ScrollArea className="h-[calc(100vh-350px)] pr-4" ref={scrollRef}>
                                {isLoadingMessages ? (
                                    <div className="py-4 text-center text-gray-500">Загрузка сообщений...</div>
                                ) : selectedChat?.messages?.length > 0 ? (
                                    <div className="flex flex-col gap-4 pb-4">
                                        {selectedChat.messages.map((message: Message) => (
                                            <ChatMessage
                                                key={message.id}
                                                message={message}
                                                isCurrentUser={message.sender_role !== 'applicant'}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full py-12 text-center text-gray-500">
                                        <p className="text-lg font-medium mb-2">
                                            Начните общение с {selectedChat?.applicant_email}
                                        </p>
                                        <p className="max-w-md">
                                            Ответьте на вопросы абитуриента о поступлении или программах обучения
                                        </p>
                                    </div>
                                )}
                            </ScrollArea>
                        </Card>

                        <div className="relative">
                            <Textarea
                                placeholder="Введите сообщение..."
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                onKeyDown={handleKeyDown}
                                className="resize-none pr-12"
                                rows={3}
                            />
                            <Button
                                size="icon"
                                className="absolute right-2 bottom-2"
                                onClick={handleSendMessage}
                                disabled={newMessage.trim() === '' || sendMessageMutation.isPending}
                            >
                                <Send className="h-4 w-4" />
                            </Button>
                        </div>
                    </>
                ) : (
                    <Card className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            <p className="text-xl font-semibold mb-2">Выберите чат для начала общения</p>
                            <p className="text-muted-foreground">Список чатов отображён слева</p>
                        </div>
                    </Card>
                )}
            </div>
        </div>
    );
};