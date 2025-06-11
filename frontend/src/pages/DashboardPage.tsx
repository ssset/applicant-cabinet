import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogClose,
} from '@/components/ui/dialog';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/hooks/useAuth';
import { motion } from 'framer-motion';
import { BarChart } from '@/components/dashboard/Charts';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { useToast } from '@/hooks/use-toast';
import { FileText, School, Users, Settings, Plus, Pencil, Trash2, UserPlus } from 'lucide-react';
import { applicationAPI, messageAPI, institutionAPI, specialtyAPI, moderatorAPI, adminAPI } from '@/services/api';
import { useIsMobile } from '@/hooks/use-mobile';

interface Organization {
    id: number;
    name: string;
}

interface Building {
    id: number;
    organization: Organization;
}

interface Specialty {
    id: number;
    name: string;
}

interface BuildingSpecialty {
    id: number;
    building: Building;
    specialty: Specialty;
}

interface Application {
    id: number;
    building_specialty: BuildingSpecialty | null;
    status: 'pending' | 'accepted' | 'rejected';
    priority: number;
    course: number;
    study_form: string;
    funding_basis: string;
}

const DashboardPage = () => {
    const { user } = useAuth();
    const { toast } = useToast();
    const isMobile = useIsMobile();
    const [applications, setApplications] = useState<Application[]>([]);
    const [chats, setChats] = useState<any[]>([]);
    const [institutions, setInstitutions] = useState<any[]>([]);
    const [specialties, setSpecialties] = useState<any[]>([]);
    const [moderators, setModerators] = useState<any[]>([]);
    const [admins, setAdmins] = useState<any[]>([]);

    useEffect(() => {
        toast({
            title: "Добро пожаловать в панель управления",
            description: `Вы вошли как ${getRoleLabel(user?.role)}`,
        });

        const fetchData = async () => {
            try {
                if (user?.role === 'applicant') {
                    const apps = await applicationAPI.getApplications();
                    console.log('Applications data:', apps);
                    const chatData = await messageAPI.getChats();
                    setApplications(apps);
                    setChats(chatData);
                    const orgIds = new Set(
                        apps
                            .map((app: any) => app.building_specialty?.building?.organization?.id)
                            .filter((id: any) => id != null)
                    );
                    setInstitutions(Array.from(orgIds).map(id => ({ id })));
                } else if (user?.role === 'moderator') {
                    const apps = await applicationAPI.getModeratorApplications();
                    const specs = await specialtyAPI.getSpecialties();
                    const chatData = await messageAPI.getChats();
                    setApplications(apps);
                    setSpecialties(specs);
                    setChats(chatData);
                } else if (user?.role === 'admin_org') {
                    const apps = await applicationAPI.getModeratorApplications();
                    const specs = await specialtyAPI.getSpecialties();
                    const mods = await moderatorAPI.getModerators();
                    setApplications(apps);
                    setSpecialties(specs);
                    setModerators(mods);
                } else if (user?.role === 'admin_app') {
                    const insts = await institutionAPI.getInstitutions();
                    const adminData = await adminAPI.getAdmins();
                    setInstitutions(insts);
                    setAdmins(adminData);
                }
            } catch (error: any) {
                console.error('Error fetching dashboard data:', error);
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: error.message || "Не удалось загрузить данные дашборда",
                });
            }
        };

        fetchData();
    }, [user?.role, toast]);

    const getRoleLabel = (role?: string) => {
        switch (role) {
            case 'applicant': return 'абитуриент';
            case 'moderator': return 'модератор';
            case 'admin_org': return 'администратор учебного заведения';
            case 'admin_app': return 'администратор системы';
            default: return 'пользователь';
        }
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: { duration: 0.5 }
        }
    };

    // Компонент дашборда для абитуриента
    const ApplicantDashboard = () => {
        const statusLabels: { [key: string]: { label: string, color: string } } = {
            pending: { label: 'На рассмотрении', color: 'bg-yellow-100 text-yellow-800' },
            accepted: { label: 'Принято', color: 'bg-green-100 text-green-800' },
            rejected: { label: 'Отклонено', color: 'bg-red-100 text-red-800' },
        };

        return (
            <>
                <motion.div
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium">Мои заявления</CardTitle>
                                <FileText className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{applications.length}</div>
                                <p className="text-xs text-muted-foreground">
                                    Активных заявлений
                                </p>
                            </CardContent>
                        </Card>
                    </motion.div>

                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium">Учебные заведения</CardTitle>
                                <School className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{institutions.length}</div>
                                <p className="text-xs text-muted-foreground">
                                    В которые поданы заявки
                                </p>
                            </CardContent>
                        </Card>
                    </motion.div>

                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium">Сообщения</CardTitle>
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    className="h-4 w-4 text-muted-foreground"
                                >
                                    <rect width="20" height="14" x="2" y="5" rx="2" />
                                    <path d="m2 10 9 3 9-3" />
                                </svg>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{chats.length}</div>
                                <p className="text-xs text-muted-foreground">
                                    Активных чатов
                                </p>
                            </CardContent>
                        </Card>
                    </motion.div>
                </motion.div>

                <motion.div
                    className="grid grid-cols-1 gap-6"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader>
                                <CardTitle>Мои активные заявления</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4 max-h-96 overflow-y-auto">
                                    {applications.map((app: any) => (
                                        <div key={app.id} className="flex justify-between items-center p-3 bg-muted/40 rounded-md">
                                            <div>
                                                <p className="font-medium">
                                                    {app.building_specialty?.building?.organization?.name || 'Организация не указана'}
                                                </p>
                                                <p className="text-sm text-muted-foreground">
                                                    {app.building_specialty?.specialty?.name || 'Специальность не указана'}
                                                </p>
                                            </div>
                                            <span className={`px-2 py-1 text-xs font-medium rounded ${statusLabels[app.status]?.color || 'bg-gray-100 text-gray-800'}`}>
                                                {statusLabels[app.status]?.label || 'Статус неизвестен'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </motion.div>
            </>
        );
    };

    // Компонент дашборда для модератора
    const ModeratorDashboard = () => (
        <>
            <motion.div
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-sm font-medium">Заявки</CardTitle>
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                className="h-4 w-4 text-muted-foreground"
                            >
                                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                                <circle cx="9" cy="7" r="4" />
                                <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                            </svg>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{applications.length}</div>
                            <p className="text-xs text-muted-foreground">
                                Всего заявок
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-sm font-medium">Специальности</CardTitle>
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                className="h-4 w-4 text-muted-foreground"
                            >
                                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                            </svg>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{specialties.length}</div>
                            <p className="text-xs text-muted-foreground">
                                Доступно сейчас
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-sm font-medium">Сообщения</CardTitle>
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                className="h-4 w-4 text-muted-foreground"
                            >
                                <rect width="20" height="14" x="2" y="5" rx="2" />
                                <path d="m2 10 9 3 9-3" />
                            </svg>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{chats.length}</div>
                            <p className="text-xs text-muted-foreground">
                                Активных чатов
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>

            <motion.div
                className="grid grid-cols-1 gap-6"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader>
                            <CardTitle>Статистика заявок за текущую неделю</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[300px]">
                            <BarChart role={user?.role} />
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>
        </>
    );

    // Компонент дашборда для администратора организации
    const AdminOrgDashboard = () => (
        <>
            <motion.div
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-sm font-medium">Модераторы</CardTitle>
                            <Users className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{moderators.length}</div>
                            <p className="text-xs text-muted-foreground">
                                Активных модераторов
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-sm font-medium">Специальности</CardTitle>
                            <School className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{specialties.length}</div>
                            <p className="text-xs text-muted-foreground">
                                Активных специальностей
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-sm font-medium">Заявления</CardTitle>
                            <FileText className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{applications.length}</div>
                            <p className="text-xs text-muted-foreground">
                                Всего заявлений
                            </p>
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>

            <motion.div
                className="grid grid-cols-1 gap-6"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader>
                            <CardTitle>Статистика заявок за текущую неделю</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[300px]">
                            <BarChart role={user?.role} />
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>
        </>
    );

    // Компонент дашборда для администратора приложения
    const AdminAppDashboard = () => {
        const { toast } = useToast();

        const [orgForm, setOrgForm] = useState({ id: null as number | null, name: '', email: '', phone: '', address: '' });
        const [isOrgDialogOpen, setIsOrgDialogOpen] = useState(false);

        const [adminForm, setAdminForm] = useState({
            id: null as number | null,
            email: '',
            password: '',
            organization_id: null as number | null,
        });
        const [isAdminDialogOpen, setIsAdminDialogOpen] = useState(false);

        const handleCreateOrg = async () => {
            if (!orgForm.name || !orgForm.email || !orgForm.phone || !orgForm.address) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Все поля обязательны",
                });
                return;
            }

            try {
                const newOrg = await institutionAPI.createOrganization({
                    name: orgForm.name,
                    email: orgForm.email,
                    phone: orgForm.phone,
                    address: orgForm.address,
                });
                setInstitutions([...institutions, newOrg]);
                setIsOrgDialogOpen(false);
                setOrgForm({ id: null, name: '', email: '', phone: '', address: '' });
                toast({
                    title: "Успех",
                    description: "Организация успешно создана",
                });
            } catch (error: any) {
                console.error('Error creating organization:', error);
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: error.message || "Не удалось создать организацию",
                });
            }
        };

        const handleUpdateOrg = async () => {
            if (orgForm.id === null) return;
            try {
                const updatedOrg = await institutionAPI.updateOrganization(orgForm.id, {
                    name: orgForm.name,
                    email: orgForm.email,
                    phone: orgForm.phone,
                    address: orgForm.address,
                });
                setInstitutions(institutions.map(org => (org.id === orgForm.id ? updatedOrg : org)));
                setIsOrgDialogOpen(false);
                setOrgForm({ id: null, name: '', email: '', phone: '', address: '' });
                toast({
                    title: "Успех",
                    description: "Организация успешно обновлена",
                });
            } catch (error: any) {
                console.error('Error updating organization:', error);
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: error.message || "Не удалось обновить организацию",
                });
            }
        };

        const handleDeleteOrg = async (id: number) => {
            try {
                await institutionAPI.deleteOrganization(id);
                setInstitutions(institutions.filter(org => org.id !== id));
                toast({
                    title: "Успех",
                    description: "Организация успешно удалена",
                });
            } catch (error: any) {
                console.error('Error deleting organization:', error);
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: error.message || "Не удалось удалить организацию",
                });
            }
        };

        const handleEditOrg = (org: any) => {
            setOrgForm({ id: org.id, name: org.name, email: org.email, phone: org.phone, address: org.address });
            setIsOrgDialogOpen(true);
        };

        const handleCreateAdmin = async () => {
            if (!adminForm.email) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Email обязателен",
                });
                return;
            }
            if (!adminForm.password && !adminForm.id) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Пароль обязателен при создании администратора",
                });
                return;
            }
            if (!adminForm.organization_id) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Выберите организацию",
                });
                return;
            }

            const orgId = Number(adminForm.organization_id);
            if (isNaN(orgId) || orgId <= 0) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Выберите корректную организацию",
                });
                return;
            }

            try {
                const payload = {
                    email: adminForm.email,
                    password: adminForm.password,
                    organization_id: orgId,
                    consent_to_data_processing: true,
                };
                const newAdmin = await adminAPI.createAdmin(payload);
                setAdmins([...admins, { id: newAdmin.id || Date.now(), email: adminForm.email, organization: institutions.find(org => org.id === orgId) }]);
                setIsAdminDialogOpen(false);
                setAdminForm({ id: null, email: '', password: '', organization_id: null });
                toast({
                    title: "Успех",
                    description: "Администратор успешно создан. Проверьте email для кода верификации.",
                });
            } catch (error: any) {
                console.error('Error creating admin:', error);
                let errorMessage = "Не удалось создать администратора";
                if (error.response?.data) {
                    if (error.response.data.message) {
                        errorMessage = error.response.data.message;
                    } else if (error.response.data.email) {
                        errorMessage = `Ошибка в email: ${error.response.data.email.join(', ')}`;
                    } else if (error.response.data.password) {
                        errorMessage = `Ошибка в пароле: ${error.response.data.password.join(', ')}`;
                    } else if (error.response.data.non_field_errors) {
                        errorMessage = error.response.data.non_field_errors.join(', ');
                    }
                }
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: errorMessage,
                });
            }
        };

        const handleUpdateAdmin = async () => {
            if (adminForm.id === null) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "ID администратора не указан",
                });
                return;
            }

            if (!adminForm.email) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Email обязателен",
                });
                return;
            }

            const orgId = adminForm.organization_id ? Number(adminForm.organization_id) : null;
            if (orgId === null) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Выберите организацию",
                });
                return;
            }
            if (isNaN(orgId) || orgId <= 0) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Выберите корректную организацию",
                });
                return;
            }

            try {
                const payload = {
                    email: adminForm.email,
                    organization_id: orgId,
                    ...(adminForm.password && { password: adminForm.password }),
                };
                const updatedAdmin = await adminAPI.updateAdmin(adminForm.id, payload);
                setAdmins(admins.map(admin => (admin.id === adminForm.id ? { ...admin, ...updatedAdmin, email: adminForm.email, organization: institutions.find(org => org.id === orgId) } : admin)));
                setIsAdminDialogOpen(false);
                setAdminForm({ id: null, email: '', password: '', organization_id: null });
                toast({
                    title: "Успех",
                    description: "Администратор успешно обновлён",
                });
            } catch (error: any) {
                console.error('Error updating admin:', error);
                let errorMessage = "Не удалось обновить администратора";
                if (error.response?.data) {
                    if (error.response.data.message) {
                        errorMessage = error.response.data.message;
                    } else if (error.response.data.email) {
                        errorMessage = `Ошибка в email: ${error.response.data.email.join(', ')}`;
                    } else if (error.response.data.non_field_errors) {
                        errorMessage = error.response.data.non_field_errors.join(', ');
                    }
                }
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: errorMessage,
                });
            }
        };

        const handleDeleteAdmin = async (id: number) => {
            try {
                await adminAPI.deleteAdmin(id);
                setAdmins(admins.filter(admin => admin.id !== id));
                toast({
                    title: "Успех",
                    description: "Администратор успешно удалён",
                });
            } catch (error: any) {
                console.error('Error deleting admin:', error);
                let errorMessage = "Не удалось удалить администратора";
                if (error.response?.data?.message) {
                    errorMessage = error.response.data.message;
                }
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: errorMessage,
                });
            }
        };

        const handleEditAdmin = (admin: any) => {
            if (!admin.id) {
                console.error('No admin ID provided for editing:', admin);
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: "Не удалось открыть форму редактирования: ID администратора отсутствует",
                });
                return;
            }
            console.log('Opening edit form for admin:', admin);
            setAdminForm({
                id: admin.id,
                email: admin.email,
                password: '',
                organization_id: admin.organization?.id || null,
            });
            setIsAdminDialogOpen(true);
        };

        return (
            <>
                <motion.div
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium">Учебные заведения</CardTitle>
                                <School className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{institutions.length}</div>
                                <p className="text-xs text-muted-foreground">
                                    Всего заведений
                                </p>
                            </CardContent>
                        </Card>
                    </motion.div>

                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium">Администраторы</CardTitle>
                                <Users className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{admins.length}</div>
                                <p className="text-xs text-muted-foreground">
                                    Активных администраторов
                                </p>
                            </CardContent>
                        </Card>
                    </motion.div>

                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium">Настройки системы</CardTitle>
                                <Settings className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">0</div>
                                <p className="text-xs text-muted-foreground">
                                    Активных параметров (добавить эндпоинт)
                                </p>
                            </CardContent>
                        </Card>
                    </motion.div>
                </motion.div>

                <motion.div
                    className="grid grid-cols-1 gap-6"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.div variants={itemVariants}>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle>Администраторы</CardTitle>
                                <Dialog open={isAdminDialogOpen} onOpenChange={setIsAdminDialogOpen}>
                                    <DialogTrigger asChild>
                                        <Button variant="outline" size="sm">
                                            <UserPlus className="h-4 w-4 mr-2" />
                                            Добавить
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>{adminForm.id ? 'Редактировать администратора' : 'Создать администратора'}</DialogTitle>
                                            <DialogDescription>
                                                Заполните данные для {adminForm.id ? 'редактирования' : 'создания'} администратора.
                                            </DialogDescription>
                                        </DialogHeader>
                                        <div className="grid gap-4 py-4">
                                            <div className="grid grid-cols-4 items-center gap-4">
                                                <Label htmlFor="admin-email" className="text-right">Email</Label>
                                                <Input
                                                    id="admin-email"
                                                    value={adminForm.email}
                                                    onChange={(e) => setAdminForm({ ...adminForm, email: e.target.value })}
                                                    className="col-span-3"
                                                />
                                            </div>
                                            {!adminForm.id && (
                                                <div className="grid grid-cols-4 items-center gap-4">
                                                    <Label htmlFor="admin-password" className="text-right">Пароль</Label>
                                                    <Input
                                                        id="admin-password"
                                                        type="password"
                                                        value={adminForm.password}
                                                        onChange={(e) => setAdminForm({ ...adminForm, password: e.target.value })}
                                                        className="col-span-3"
                                                    />
                                                </div>
                                            )}
                                            <div className="grid grid-cols-4 items-center gap-4">
                                                <Label htmlFor="admin-org" className="text-right">Организация</Label>
                                                <Select
                                                    onValueChange={(value) => setAdminForm({ ...adminForm, organization_id: parseInt(value) })}
                                                    value={adminForm.organization_id?.toString() || ''}
                                                >
                                                    <SelectTrigger className="col-span-3">
                                                        <SelectValue placeholder="Выберите организацию" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {institutions.map((org) => (
                                                            <SelectItem key={org.id} value={org.id.toString()}>
                                                                {org.name}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                        <DialogFooter>
                                            <DialogClose asChild>
                                                <Button variant="outline">Отмена</Button>
                                            </DialogClose>
                                            <Button onClick={adminForm.id ? handleUpdateAdmin : handleCreateAdmin}>
                                                {adminForm.id ? 'Сохранить' : 'Создать'}
                                            </Button>
                                        </DialogFooter>
                                    </DialogContent>
                                </Dialog>
                            </CardHeader>
                            <CardContent>
                                <div className={`overflow-x-auto ${!isMobile ? 'max-h-96 overflow-y-auto' : ''}`}>
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="bg-muted/50">
                                                <TableHead className="sticky top-0 bg-muted/50 min-w-[200px]">Email</TableHead>
                                                <TableHead className="sticky top-0 bg-muted/50 min-w-[200px]">Организация</TableHead>
                                                <TableHead className="sticky top-0 bg-muted/50 text-right min-w-[120px]">Действия</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {admins.map((admin) => (
                                                <TableRow key={admin.id} className="hover:bg-muted/50 transition-colors">
                                                    <TableCell className="py-3">{admin.email}</TableCell>
                                                    <TableCell className="py-3">
                                                        {institutions.find(org => org.id === admin.organization?.id)?.name || 'Не указана'}
                                                    </TableCell>
                                                    <TableCell className="py-3 text-right">
                                                        <Button variant="ghost" size="sm" onClick={() => handleEditAdmin(admin)}>
                                                            <Pencil className="h-4 w-4" />
                                                        </Button>
                                                        <Button variant="ghost" size="sm" onClick={() => handleDeleteAdmin(admin.id)}>
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </motion.div>
            </>
        );
    };

    const renderDashboardByRole = () => {
        switch(user?.role) {
            case 'applicant':
                return <ApplicantDashboard />;
            case 'moderator':
                return <ModeratorDashboard />;
            case 'admin_org':
                return <AdminOrgDashboard />;
            case 'admin_app':
                return <AdminAppDashboard />;
            default:
                return <ApplicantDashboard />;
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 flex">
            <DashboardSidebar />
            <div
                className={`flex-1 flex flex-col ${isMobile ? 'overflow-y-auto' : ''}`}
                style={isMobile ? { height: '100vh' } : {}}
            >
                <div className="container mx-auto px-4 py-8">
                    <motion.h1
                        className="text-3xl font-bold mb-6 text-gray-800"
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ duration: 0.5 }}
                    >
                        Панель управления
                    </motion.h1>

                    <motion.p
                        className="text-lg text-gray-600 mb-8"
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ duration: 0.5, delay: 0.1 }}
                    >
                        Добро пожаловать, {getRoleLabel(user?.role)}!
                    </motion.p>

                    {renderDashboardByRole()}
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;