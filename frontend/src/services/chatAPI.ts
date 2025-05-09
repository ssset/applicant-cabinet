import { api } from './api';

export const chatAPI = {
    // Получение списка чатов
    getChats: async () => {
        const response = await api.get('message/chats/');
        return response.data;
    },

    // Получение деталей чата (включая сообщения)
    getChatDetails: async (chatId: string) => {
        const response = await api.get('message/chat-detail/', {
            params: { id: chatId },
        });
        return response.data;
    },


    sendMessage: async (chatId: string, content: string) => {
        const response = await api.post('message/chat-detail/', {
            chat_id: chatId,
            content,
        });
        return response.data;
    },


    getAvailableOrganizations: async () => {
        const response = await api.get('message/available-organizations/');
        return response.data;
    },

    // Создание нового чата
    createChat: async (organizationId: string) => {
        const response = await api.post('message/chats/', {
            organization_id: organizationId,
        });
        return response.data;
    },
};