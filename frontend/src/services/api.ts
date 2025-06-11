import axios from 'axios';

export const api = axios.create({
    baseURL: 'http://localhost:8000/api/',
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        let errorMessage = 'Произошла ошибка на сервере';

        if (error.response?.data) {
            const data = error.response.data;

            if (data.message) {
                errorMessage = data.message;
            } else if (data.errors) {
                errorMessage = Object.values(data.errors).flat().join(', ');
            } else {
                errorMessage = JSON.stringify(data);
            }

            const errorMap = {
                'You have already applied to this specialty in this building.': 'У вас уже есть заявление на выбранную специальность.',
                'You have reached the maximum number of application attempts (3) for this specialty.': 'Вы исчерпали максимальное количество попыток подачи (3) на эту специальность.',
                'Invalid credentials': 'Неверный email или пароль.',
                'Permission denied': 'У вас нет доступа к этой операции.',
                'You must fill out your applicant profile before submitting an application.': 'Вы должны заполнить профиль абитуриента перед подачей заявления.',
                'Пользователь с таким email уже существует': 'Пользователь с таким email уже существует.',
                'Organization with this email already exists.': 'Организация с таким email уже существует.',
            };
            errorMessage = errorMap[errorMessage] || errorMessage;
        } else {
            errorMessage = error.message || 'Произошла ошибка на сервере';
        }

        return Promise.reject(new Error(errorMessage));
    }
);

export const institutionAPI = {
    getInstitutions: async () => {
        const response = await api.get('/org/organizations/');
        return response.data;
    },
    applyOrganization: async (data: any) => {
        const response = await api.post('/org/apply/', data);
        return response.data;
    },
    initiatePayment: async (data: any) => {
        const response = await api.post('/org/payment/', data);
        return response.data;
    },
    createOrganization: async (data: any) => {
        const response = await api.post('/org/organizations/', data);
        return response.data;
    },
    updateOrganization: async (id: number, data: any) => {
        const response = await api.patch('/org/organizations/', { id, ...data });
        return response.data;
    },
    deleteOrganization: async (id: number) => {
        const response = await api.delete('/org/organizations/', { params: { id } });
        return response.data;
    },
    getAvailableInstitutions: async (city?: string) => {
        const response = await api.get('/applications/available-organizations/', { params: { city } });
        return response.data;
    },
    getAvailableCities: async () => {
        const response = await api.get('/applications/available-cities/');
        return response.data;
    },
};

export const authAPI = {
    register: async (email: string, password: string, password2: string, consent_to_data_processing: boolean) => {
        try {
            const response = await api.post('/auth/register/', {
                email,
                password,
                password2,
                consent_to_data_processing,
            });
            return response.data;
        } catch (error) {
            throw new Error(error.message || 'Произошла ошибка при подключении к серверу');
        }
    },
    login: async (email: string, password: string) => {
        try {
            const response = await api.post('/auth/login/', { email, password });
            return response.data;
        } catch (error) {
            throw new Error(error.message || 'Произошла ошибка при подключении к серверу');
        }
    },
    verifyEmail: async (token: string) => {
        try {
            const response = await api.get('/auth/verify/', {
                params: { token }
            });
            return response.data;
        } catch (error) {
            throw new Error(error.message || 'Произошла ошибка при подключении к серверу');
        }
    },
};

export const userAPI = {
    getCurrentUser: async () => {
        const response = await api.get('/users/me/');
        return response.data;
    },
    getApplicantProfile: async () => {
        const response = await api.get('/users/profile/');
        return response.data;
    },
    createApplicantProfile: async (data: FormData) => {
        const response = await api.post('/users/profile/', data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
    updateApplicantProfile: async (data: FormData) => {
        const response = await api.patch('/users/profile/', data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
    updateCurrentUser: async (data: any) => {
        const response = await api.patch('/users/me/', data);
        return response.data;
    },
    updatePassword: async (data: { old_password: string; new_password: string }) => {
        const response = await api.put('/users/me/password/', data);
        return response.data;
    },
    getTaskStatus: async (taskId: string) => {
        const response = await api.get('/users/task-status/', {
            params: { task_id: taskId },
        });
        return response.data;
    },
};

export const applicationAPI = {
    getApplications: async () => {
        const response = await api.get('/applications/applications/');
        return response.data;
    },
    getModeratorApplications: async () => {
        const response = await api.get('/applications/moderator/applications/');
        return response.data;
    },
    getApplicationAttempts: async (buildingSpecialtyId: number) => {
        const response = await api.get('/applications/application-attempts/', {
            params: { building_specialty_id: buildingSpecialtyId }
        });
        return response.data;
    },
    createApplication: async (data: {
        building_specialty_id: number;
        priority: number;
        course: number;
        study_form: string;
        funding_basis: string;
        dormitory_needed: boolean;
        first_time_education: boolean;
        info_source: string;
    }) => {
        const response = await api.post('/applications/applications/', data);
        return response.data;
    },
    updateApplicationStatus: async (applicationId: number, action: 'accept' | 'reject', rejectReason?: string) => {
        const response = await api.patch('/applications/moderator/application-detail/', {
            id: applicationId,
            action,
            reject_reason: rejectReason,
        });
        return response.data;
    },
};

export const messageAPI = {
    getChats: async () => {
        const response = await api.get('/message/chats/');
        return response.data;
    },
    getAvailableOrganizations: async () => {
        const response = await api.get('/message/available-organizations/');
        return response.data;
    },
    createChat: async (organizationId: string) => {
        const response = await api.post('/message/chats/', { organization_id: organizationId });
        return response.data;
    },
    getChatDetails: async (chatId: string) => {
        const response = await api.get('/message/chat-detail/', { params: { id: chatId } });
        return response.data;
    },
    sendMessage: async (chatId: string, content: string) => {
        const response = await api.post('/message/chat-detail/', { chat_id: chatId, content });
        return response.data;
    },
};

export const buildingAPI = {
    getBuildings: async () => {
        const response = await api.get('/org/buildings/');
        return response.data;
    },
    createBuilding: async (data: {
        name: string;
        address: string;
        phone: string;
        email: string;
        organization: number;
    }) => {
        console.log('Creating building with data:', data);
        const response = await api.post('/org/buildings/', data);
        return response.data;
    },
};

export const specialtyAPI = {
    getAvailableSpecialties: async (organizationId?: number, city?: string) => {
        const response = await api.get('/applications/available-specialties/', {
            params: { organization_id: organizationId, city },
        });
        return response.data;
    },
    getSpecialties: async () => {
        const response = await api.get('/org/specialties/');
        return response.data;
    },
    createSpecialty: async (data: any) => {
        const response = await api.post('/org/specialties/', data);
        return response.data;
    },
    updateSpecialty: async (id: number, data: any) => {
        const response = await api.patch('/org/specialties/', { id, ...data });
        return response.data;
    },
    deleteSpecialty: async (id: number) => {
        const response = await api.delete('/org/specialties/', { params: { id } });
        return response.data;
    },
    getLeaderboard: async (buildingSpecialtyId: number) => {
        const response = await api.get('/applications/leaderboard/', {
            params: { building_specialty_id: buildingSpecialtyId }
        });
        return response.data;
    },
};

export const buildingSpecialtyAPI = {
    getBuildingSpecialties: async () => {
        const response = await api.get('/org/building-specialties/');
        return response.data;
    },
    createBuildingSpecialty: async (data: any) => {
        const response = await api.post('/org/building-specialties/', data);
        return response.data;
    },
};

export const moderatorAPI = {
    getModerators: async () => {
        const response = await api.get('/users/moderators/');
        return response.data;
    },
    createModerator: async (data: {
        email: string;
        password: string;
        consent_to_data_processing?: boolean;
    }) => {
        const response = await api.post('/users/moderators/', data);
        return response.data;
    },
    updateModerator: async (id: number, data: { email?: string; password?: string }) => {
        const response = await api.patch('/users/moderators/', { id, ...data });
        return response.data;
    },
    deleteModerator: async (id: number) => {
        const response = await api.delete('/users/moderators/', { params: { id } });
        return response.data;
    },
};

export const adminAPI = {
    getAdmins: async () => {
        try {
            const response = await api.get('/users/admin-org/');
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error) && error.response) {
                throw new Error(error.response.data.message || 'Ошибка при получении администраторов');
            }
            throw new Error('Произошла ошибка при подключении к серверу');
        }
    },
    createAdmin: async (data: {
        email: string;
        password: string;
        organization_id: number;
        consent_to_data_processing?: boolean;
    }) => {
        try {
            const response = await api.post('/users/admin-org/', data);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error) && error.response) {
                throw new Error(
                    error.response.data.message ||
                    error.response.data.email?.join(', ') ||
                    error.response.data.password?.join(', ') ||
                    error.response.data.non_field_errors?.join(', ') ||
                    'Ошибка при создании администратора'
                );
            }
            throw new Error('Произошла ошибка при подключении к серверу');
        }
    },
    updateAdmin: async (id: number, data: {
        email?: string;
        password?: string;
        organization_id?: number;
    }) => {
        try {
            const response = await api.patch(`/users/admin-org/${id}/`, data);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error) && error.response) {
                throw new Error(
                    error.response.data.message ||
                    error.response.data.email?.join(', ') ||
                    error.response.data.password?.join(', ') ||
                    error.response.data.non_field_errors?.join(', ') ||
                    'Ошибка при обновлении администратора'
                );
            }
            throw new Error('Произошла ошибка при подключении к серверу');
        }
    },
    deleteAdmin: async (id: number) => {
        try {
            const response = await api.delete(`/users/admin-org/${id}/`);
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error) && error.response) {
                throw new Error(error.response.data.message || 'Ошибка при удалении администратора');
            }
            throw new Error('Произошла ошибка при подключении к серверу');
        }
    },
};

export const statisticsAPI = {
    getApplicationStats: async () => {
        const response = await api.get('/statistics/applications/');
        return response.data;
    },
    getSpecialtyStats: async () => {
        const response = await api.get('/statistics/specialties/');
        return response.data;
    },
    getActivityStats: async () => {
        const response = await api.get('/statistics/activity/');
        return response.data;
    },
    getModeratorActivityStats: async () => {
        const response = await api.get('/statistics/moderator-activity/');
        return response.data;
    },
    getSystemStats: async () => {
        const response = await api.get('/statistics/system/');
        return response.data;
    },
    getInstitutionStats: async () => {
        const response = await api.get('/statistics/institutions/');
        return response.data;
    },
    getAdminActivityStats: async () => {
        const response = await api.get('/statistics/admin-activity/');
        return response.data;
    },
};

export default api;