import React, { useState, useEffect } from 'react';
import { Building, Plus, Search, MapPin, Mail, Phone, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { useToast } from '@/hooks/use-toast';
import { institutionAPI, buildingAPI, api } from '@/services/api';

// Схема валидации
const organizationSchema = z.object({
    name: z.string().min(2, 'Название должно содержать минимум 2 символа').max(100, 'Название не должно превышать 100 символов'),
    email: z.string().email('Введите корректный email'),
    phone: z.string().min(5, 'Введите корректный номер телефона').max(20, 'Номер телефона не должен превышать 20 символов'),
    address: z.string().min(5, 'Адрес должен содержать минимум 5 символов'),
    city: z.string().min(2, 'Город должен содержать минимум 2 символа').max(100, 'Город не должен превышать 100 символов'),
    buildings: z
        .array(
            z.object({
                id: z.number().optional(),
                name: z.string().min(2, 'Название корпуса должно содержать минимум 2 символа').max(100, 'Название корпуса не должен превышать 100 символов'),
                address: z.string().min(5, 'Адрес корпуса должен содержать минимум 5 символов').max(200, 'Адрес корпуса не должен превышать 200 символов'),
                phone: z.string().min(5, 'Введите корректный номер телефона корпуса').max(20, 'Номер телефона корпуса не должен превышать 20 символов'),
                email: z.string().email('Введите корректный email корпуса'),
            })
        )
        .min(1, 'Необходимо добавить хотя бы один корпус'),
});

type OrganizationForm = z.infer<typeof organizationSchema>;

interface Building {
    id: number;
    name: string;
    address: string;
    phone: string;
    email: string;
    organization: number;
}

interface Organization {
    id: number;
    name: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    buildings: Building[];
}

const ITEMS_PER_PAGE = 20;

const InstitutionsPage = () => {
    const { toast } = useToast();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
    const [currentPage, setCurrentPage] = useState(1);

    const form = useForm<OrganizationForm>({
        resolver: zodResolver(organizationSchema),
        defaultValues: {
            name: '',
            email: '',
            phone: '',
            address: '',
            city: '',
            buildings: [{ name: '', address: '', phone: '', email: '' }],
        },
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const orgResponse = await institutionAPI.getInstitutions();
                setOrganizations(orgResponse);
            } catch (error) {
                toast({
                    title: 'Ошибка',
                    description: 'Не удалось загрузить данные',
                    variant: 'destructive',
                });
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const onSubmit = async (data: OrganizationForm) => {
        try {
            if (editingOrg) {
                console.log('Editing organization with ID:', editingOrg.id);
                const updatedOrg = await institutionAPI.updateOrganization(editingOrg.id, {
                    name: data.name,
                    email: data.email,
                    phone: data.phone,
                    address: data.address,
                    city: data.city,
                });

                const updatedBuildings: Building[] = [];
                for (const building of data.buildings) {
                    if (building.id) {
                        const buildingResponse = await api.patch('/org/buildings/', {
                            id: building.id,
                            name: building.name,
                            address: building.address,
                            phone: building.phone,
                            email: building.email,
                        });
                        updatedBuildings.push(buildingResponse.data);
                    } else {
                        if (!editingOrg.id) {
                            throw new Error('ID организации отсутствует');
                        }
                        const buildingResponse = await buildingAPI.createBuilding({
                            name: building.name,
                            address: building.address,
                            phone: building.phone,
                            email: building.email,
                            organization: editingOrg.id,
                        });
                        updatedBuildings.push(buildingResponse);
                    }
                }

                setOrganizations((prev) =>
                    prev.map((org) =>
                        org.id === editingOrg.id ? { ...org, ...data, buildings: updatedBuildings } : org
                    )
                );
                toast({
                    title: 'Успех',
                    description: `${data.name} успешно обновлено`,
                });
            } else {
                const orgResponse = await institutionAPI.createOrganization({
                    name: data.name,
                    email: data.email,
                    phone: data.phone,
                    address: data.address,
                    city: data.city,
                });

                const newBuildings: Building[] = [];
                for (const building of data.buildings) {
                    const buildingResponse = await buildingAPI.createBuilding({
                        name: building.name,
                        address: building.address,
                        phone: building.phone,
                        email: building.email,
                        organization: orgResponse.id,
                    });
                    newBuildings.push(buildingResponse);
                }

                setOrganizations((prev) => [
                    ...prev,
                    { ...orgResponse, buildings: newBuildings },
                ]);
                toast({
                    title: 'Успех',
                    description: `${data.name} успешно создано с корпусами`,
                });
            }
            setIsDialogOpen(false);
            setEditingOrg(null);
            form.reset();
        } catch (error) {
            console.error('Ошибка при создании/обновлении:', error);
            toast({
                title: 'Ошибка',
                description: 'Не удалось создать/обновить организацию или корпуса',
                variant: 'destructive',
            });
        }
    };

    const addBuilding = () => {
        const currentBuildings = form.getValues('buildings');
        form.setValue('buildings', [
            ...currentBuildings,
            { name: '', address: '', phone: '', email: '' },
        ]);
    };

    const removeBuilding = (index: number) => {
        const currentBuildings = form.getValues('buildings');
        form.setValue('buildings', currentBuildings.filter((_, i) => i !== index));
    };

    const handleEdit = (org: Organization) => {
        setEditingOrg(org);
        form.reset({
            name: org.name,
            email: org.email,
            phone: org.phone,
            address: org.address,
            city: org.city,
            buildings: org.buildings.length > 0
                ? org.buildings.map((b) => ({
                    id: b.id,
                    name: b.name,
                    address: b.address,
                    phone: b.phone,
                    email: b.email,
                }))
                : [{ name: '', address: '', phone: '', email: '' }],
        });
        setIsDialogOpen(true);
    };

    const handleDelete = async (orgId: number) => {
        if (window.confirm('Вы уверены, что хотите удалить эту организацию?')) {
            try {
                await institutionAPI.deleteOrganization(orgId);
                setOrganizations((prev) => prev.filter((org) => org.id !== orgId));
                toast({
                    title: 'Успех',
                    description: 'Организация удалена',
                });
                const filtered = organizations.filter(
                    (org) =>
                        org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        org.email.toLowerCase().includes(searchQuery.toLowerCase())
                );
                const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
                if (currentPage > totalPages && currentPage > 1) {
                    setCurrentPage(currentPage - 1);
                }
            } catch (error) {
                toast({
                    title: 'Ошибка',
                    description: 'Не удалось удалить организацию',
                    variant: 'destructive',
                });
            }
        }
    };

    const filteredOrganizations = organizations.filter(
        (org) =>
            org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            org.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const totalPages = Math.ceil(filteredOrganizations.length / ITEMS_PER_PAGE);
    const paginatedOrganizations = filteredOrganizations.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    const handlePageChange = (page: number) => {
        setCurrentPage(page);
        const scrollContainer = document.getElementById('organizations-scroll-container');
        if (scrollContainer) {
            scrollContainer.scrollTop = 0;
        }
    };

    return (
        <SidebarProvider defaultOpen>
            <div className="min-h-screen flex w-full bg-gray-50">
                <DashboardSidebar />
                <SidebarInset className="p-4 md:p-6 w-full">
                    <div className="mb-6 space-y-4">
                        <h1 className="text-2xl font-bold">Управление организациями</h1>
                        <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                            <div className="relative w-full sm:w-96">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Поиск организаций..."
                                    className="pl-8"
                                    value={searchQuery}
                                    onChange={(e) => {
                                        setSearchQuery(e.target.value);
                                        setCurrentPage(1);
                                    }}
                                />
                            </div>
                            <Dialog open={isDialogOpen} onOpenChange={(open) => {
                                setIsDialogOpen(open);
                                if (!open) {
                                    setEditingOrg(null);
                                    form.reset();
                                }
                            }}>
                                <DialogTrigger asChild>
                                    <Button className="w-full sm:w-auto">
                                        <Plus className="mr-2 h-4 w-4" />
                                        Добавить организацию
                                    </Button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                                    <DialogHeader>
                                        <DialogTitle>{editingOrg ? 'Редактировать организацию' : 'Добавить организацию'}</DialogTitle>
                                        <DialogDescription>
                                            {editingOrg ? 'Измените информацию об организации и её корпусах' : 'Заполните данные и добавьте корпуса'}
                                        </DialogDescription>
                                    </DialogHeader>
                                    <Form {...form}>
                                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                                            <FormField
                                                control={form.control}
                                                name="name"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Название организации</FormLabel>
                                                        <FormControl>
                                                            <Input placeholder="Название организации" {...field} />
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <FormField
                                                    control={form.control}
                                                    name="address"
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel>Адрес</FormLabel>
                                                            <FormControl>
                                                                <Input placeholder="ул. Примерная, д. 1" {...field} />
                                                            </FormControl>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                                <FormField
                                                    control={form.control}
                                                    name="city"
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel>Город</FormLabel>
                                                            <FormControl>
                                                                <Input placeholder="Москва" {...field} />
                                                            </FormControl>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                                <FormField
                                                    control={form.control}
                                                    name="email"
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel>Email</FormLabel>
                                                            <FormControl>
                                                                <Input type="email" placeholder="contact@organization.ru" {...field} />
                                                            </FormControl>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                                <FormField
                                                    control={form.control}
                                                    name="phone"
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel>Телефон</FormLabel>
                                                            <FormControl>
                                                                <Input placeholder="+7 (999) 123-45-67" {...field} />
                                                            </FormControl>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                            </div>
                                            <div className="space-y-4">
                                                <div className="flex justify-between items-center">
                                                    <h3 className="text-lg font-semibold">Корпуса</h3>
                                                    <Button type="button" variant="outline" onClick={addBuilding}>
                                                        <Plus className="h-4 w-4 mr-2" />
                                                        Добавить корпус
                                                    </Button>
                                                </div>
                                                <FormField
                                                    control={form.control}
                                                    name="buildings"
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormMessage />
                                                            {form.watch('buildings').map((building, index) => (
                                                                <div key={index} className="border p-4 rounded-md space-y-4 mt-4">
                                                                    <div className="flex justify-between items-center">
                                                                        <h4 className="font-medium">Корпус {index + 1}</h4>
                                                                        <Button
                                                                            type="button"
                                                                            variant="destructive"
                                                                            size="sm"
                                                                            onClick={() => removeBuilding(index)}
                                                                            disabled={form.watch('buildings').length === 1}
                                                                        >
                                                                            Удалить
                                                                        </Button>
                                                                    </div>
                                                                    <FormField
                                                                        control={form.control}
                                                                        name={`buildings.${index}.name`}
                                                                        render={({ field }) => (
                                                                            <FormItem>
                                                                                <FormLabel>Название корпуса</FormLabel>
                                                                                <FormControl>
                                                                                    <Input placeholder="Корпус 1" {...field} />
                                                                                </FormControl>
                                                                                <FormMessage />
                                                                            </FormItem>
                                                                        )}
                                                                    />
                                                                    <FormField
                                                                        control={form.control}
                                                                        name={`buildings.${index}.address`}
                                                                        render={({ field }) => (
                                                                            <FormItem>
                                                                                <FormLabel>Адрес корпуса</FormLabel>
                                                                                <FormControl>
                                                                                    <Input placeholder="ул. Корпусная, д. 2" {...field} />
                                                                                </FormControl>
                                                                                <FormMessage />
                                                                            </FormItem>
                                                                        )}
                                                                    />
                                                                    <FormField
                                                                        control={form.control}
                                                                        name={`buildings.${index}.email`}
                                                                        render={({ field }) => (
                                                                            <FormItem>
                                                                                <FormLabel>Email корпуса</FormLabel>
                                                                                <FormControl>
                                                                                    <Input type="email" placeholder="building@organization.ru" {...field} />
                                                                                </FormControl>
                                                                                <FormMessage />
                                                                            </FormItem>
                                                                        )}
                                                                    />
                                                                    <FormField
                                                                        control={form.control}
                                                                        name={`buildings.${index}.phone`}
                                                                        render={({ field }) => (
                                                                            <FormItem>
                                                                                <FormLabel>Телефон корпуса</FormLabel>
                                                                                <FormControl>
                                                                                    <Input placeholder="+7 (999) 987-65-43" {...field} />
                                                                                </FormControl>
                                                                                <FormMessage />
                                                                            </FormItem>
                                                                        )}
                                                                    />
                                                                </div>
                                                            ))}
                                                        </FormItem>
                                                    )}
                                                />
                                            </div>
                                            <DialogFooter className="mt-6">
                                                <Button type="submit">{editingOrg ? 'Сохранить изменения' : 'Создать организацию'}</Button>
                                            </DialogFooter>
                                        </form>
                                    </Form>
                                </DialogContent>
                            </Dialog>
                        </div>
                    </div>
                    {loading ? (
                        <div className="text-center text-muted-foreground">Загрузка...</div>
                    ) : (
                        <div className="flex flex-col space-y-4">
                            {/* Скроллируемый блок с карточками */}
                            <div
                                id="organizations-scroll-container"
                                className="max-h-[70vh] overflow-y-auto bg-white shadow-sm rounded-lg border border-gray-200 p-6"
                            >
                                {paginatedOrganizations.length > 0 ? (
                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        {paginatedOrganizations.map((org) => (
                                            <Card key={org.id} className="shadow-md hover:shadow-lg transition-shadow duration-200">
                                                <CardHeader>
                                                    <div className="flex justify-between items-start">
                                                        <div className="space-y-1">
                                                            <CardTitle className="text-xl font-bold">{org.name}</CardTitle>
                                                            <p className="text-sm text-muted-foreground">{org.city}</p>
                                                        </div>
                                                        <Building className="h-6 w-6 text-blue-500 flex-shrink-0" />
                                                    </div>
                                                </CardHeader>
                                                <CardContent className="space-y-4">
                                                    <div className="space-y-3">
                                                        {org.buildings.length > 0 ? (
                                                            org.buildings.map((building) => (
                                                                <div key={building.id} className="flex items-center text-sm text-muted-foreground">
                                                                    <MapPin className="h-4 w-4 mr-2" />
                                                                    <span>{building.address}</span>
                                                                </div>
                                                            ))
                                                        ) : (
                                                            <div className="text-sm text-muted-foreground">Корпуса отсутствуют</div>
                                                        )}
                                                        <div className="flex items-center text-sm text-muted-foreground">
                                                            <Mail className="h-4 w-4 mr-2" />
                                                            <span>{org.email}</span>
                                                        </div>
                                                        <div className="flex items-center text-sm text-muted-foreground">
                                                            <Phone className="h-4 w-4 mr-2" />
                                                            <span>{org.phone}</span>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                                <div className="flex justify-end gap-2 p-4">
                                                    <Button variant="outline" onClick={() => handleEdit(org)}>
                                                        Редактировать
                                                    </Button>
                                                    <Button variant="destructive" onClick={() => handleDelete(org.id)}>
                                                        <Trash2 className="h-4 w-4 mr-2" />
                                                        Удалить
                                                    </Button>
                                                </div>
                                            </Card>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center text-muted-foreground">
                                        Организации не найдены
                                    </div>
                                )}
                            </div>

                            {/* Пагинация */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-center space-x-2 mt-4">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handlePageChange(currentPage - 1)}
                                        disabled={currentPage === 1}
                                        className="text-gray-600 hover:text-gray-800"
                                    >
                                        <ChevronLeft className="h-4 w-4" />
                                    </Button>
                                    {Array.from({ length: totalPages }, (_, index) => index + 1).map((page) => (
                                        <Button
                                            key={page}
                                            variant={currentPage === page ? 'default' : 'outline'}
                                            size="sm"
                                            onClick={() => handlePageChange(page)}
                                            className={
                                                currentPage === page
                                                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                                                    : 'text-gray-600 hover:text-gray-800'
                                            }
                                        >
                                            {page}
                                        </Button>
                                    ))}
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handlePageChange(currentPage + 1)}
                                        disabled={currentPage === totalPages}
                                        className="text-gray-600 hover:text-gray-800"
                                    >
                                        <ChevronRight className="h-4 w-4" />
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
};

export default InstitutionsPage;