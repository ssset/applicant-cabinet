import React, { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Application } from '@/pages/ApplicationsReviewPage';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { motion } from 'framer-motion';
import { ImagePreviewDialog } from '@/components/applications/ImagePreviewDialog'

// Базовый URL бэкенда
export const BASE_URL = 'https://applicantcabinet.ru/'

interface ApplicantDetailsDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    application: Application | null;
}

export const ApplicantDetailsDialog: React.FC<ApplicantDetailsDialogProps> = ({
                                                                                  open,
                                                                                  onOpenChange,
                                                                                  application,
                                                                              }) => {
    const [isImagePreviewOpen, setIsImagePreviewOpen] = useState(false);
    const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(null);
    const [selectedImageTitle, setSelectedImageTitle] = useState<string>('');

    if (!application || !application.applicant_profile) {
        return null;
    }

    const { applicant_profile: profile } = application;

    // Функция для отображения даты в формате ДД.ММ.ГГГГ
    const formatDate = (date?: string) => {
        return date ? new Date(date).toLocaleDateString('ru-RU') : 'Не указана';
    };

    // Функция для отображения списка языков
    const formatLanguages = (languages?: string[]) => {
        return languages && languages.length > 0 ? languages.join(', ') : 'Не указаны';
    };

    // Функция для отображения типа образования
    const formatEducationType = (type?: string) => {
        const types: { [key: string]: string } = {
            'school': 'Школа',
            'npo': 'НПО',
            'other': 'Другое',
        };
        return type ? types[type] || type : 'Не указан';
    };

    // Функция для отображения типа документа
    const formatDocumentType = (type?: string) => {
        const types: { [key: string]: string } = {
            'certificate': 'Аттестат',
            'diploma': 'Диплом',
        };
        return type ? types[type] || type : 'Не указан';
    };

    // Функция для формирования полного URL
    const getFullImageUrl = (path?: string) => {
        if (!path) return null;
        return path.startsWith('http') ? path : `${BASE_URL}${path}`;
    };

    // Обработчик клика по изображению
    const handleImageClick = (imageUrl: string | null, title: string) => {
        if (imageUrl) {
            setSelectedImageUrl(imageUrl);
            setSelectedImageTitle(title);
            setIsImagePreviewOpen(true);
        }
    };

    // Компонент для отображения пары "метка-значение"
    const InfoRow = ({ label, value }: { label: string; value: string }) => (
        <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right font-semibold text-gray-700">{label}:</Label>
            <div className="col-span-3 text-gray-600">{value}</div>
        </div>
    );

    const studentPhotoUrl = getFullImageUrl(profile.photo);
    const attestationPhotoUrl = getFullImageUrl(profile.attestation_photo);

    return (
        <>
            <Dialog open={open} onOpenChange={onOpenChange}>
                <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="text-2xl font-bold text-gray-800">
                            Информация об абитуриенте
                        </DialogTitle>
                        <DialogDescription className="text-gray-600">
                            Подробные данные профиля абитуриента
                        </DialogDescription>
                    </DialogHeader>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className="space-y-6"
                    >
                        {/* Личные данные */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg font-semibold text-gray-800">
                                    Личные данные
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <InfoRow
                                    label="ФИО"
                                    value={`${profile.last_name || ''} ${profile.first_name || ''} ${profile.middle_name || ''}`}
                                />
                                <InfoRow label="Дата рождения" value={formatDate(profile.date_of_birth)} />
                                <InfoRow label="Гражданство" value={profile.citizenship || 'Не указано'} />
                                <InfoRow label="Место рождения" value={profile.birth_place || 'Не указано'} />
                                <InfoRow label="Телефон" value={profile.phone || 'Не указан'} />
                            </CardContent>
                        </Card>

                        {/* Документы */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg font-semibold text-gray-800">
                                    Документы
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <InfoRow label="Серия паспорта" value={profile.passport_series || 'Не указана'} />
                                <InfoRow label="Номер паспорта" value={profile.passport_number || 'Не указан'} />
                                <InfoRow label="Дата выдачи" value={formatDate(profile.passport_issued_date)} />
                                <InfoRow label="Кем выдан" value={profile.passport_issued_by || 'Не указано'} />
                                <InfoRow label="СНИЛС" value={profile.snils || 'Не указан'} />
                            </CardContent>
                        </Card>

                        {/* Адреса */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg font-semibold text-gray-800">
                                    Адреса
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <InfoRow label="Адрес регистрации" value={profile.registration_address || 'Не указан'} />
                                <InfoRow label="Фактический адрес" value={profile.actual_address || 'Не указан'} />
                            </CardContent>
                        </Card>

                        {/* Образование */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg font-semibold text-gray-800">
                                    Образование
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <InfoRow label="Тип образования" value={formatEducationType(profile.education_type)} />
                                <InfoRow label="Учебное заведение" value={profile.education_institution || 'Не указано'} />
                                <InfoRow label="Год окончания" value={profile.graduation_year?.toString() || 'Не указан'} />
                                <InfoRow label="Тип документа" value={formatDocumentType(profile.document_type)} />
                                <InfoRow label="Серия документа" value={profile.document_series || 'Не указана'} />
                                <InfoRow label="Номер документа" value={profile.document_number || 'Не указан'} />
                                <InfoRow label="Средний балл (введённый)" value={profile.average_grade?.toString() || 'Не указан'} />
                                <InfoRow label="Средний балл (рассчитанный)" value={profile.calculated_average_grade?.toString() || 'Не рассчитан'} />
                            </CardContent>
                        </Card>

                        {/* Дополнительная информация */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg font-semibold text-gray-800">
                                    Дополнительная информация
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <InfoRow label="Иностранные языки" value={formatLanguages(profile.foreign_languages)} />
                                <InfoRow label="Дополнительно" value={profile.additional_info || 'Не указано'} />
                            </CardContent>
                        </Card>

                        {/* Родители */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg font-semibold text-gray-800">
                                    Родители
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <div className="space-y-2">
                                    <h4 className="font-semibold text-gray-700">Мать</h4>
                                    <InfoRow label="ФИО" value={profile.mother_full_name || 'Не указано'} />
                                    <InfoRow label="Место работы" value={profile.mother_workplace || 'Не указано'} />
                                    <InfoRow label="Телефон" value={profile.mother_phone || 'Не указан'} />
                                </div>
                                <div className="space-y-2">
                                    <h4 className="font-semibold text-gray-700">Отец</h4>
                                    <InfoRow label="ФИО" value={profile.father_full_name || 'Не указано'} />
                                    <InfoRow label="Место работы" value={profile.father_workplace || 'Не указано'} />
                                    <InfoRow label="Телефон" value={profile.father_phone || 'Не указан'} />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Фото */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg font-semibold text-gray-800">
                                    Фото
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <div className="flex gap-4">
                                    <div className="flex-1">
                                        <Label className="font-semibold text-gray-700">Фото студента</Label>
                                        <div className="mt-2">
                                            {studentPhotoUrl ? (
                                                <img
                                                    src={studentPhotoUrl}
                                                    alt="Фото студента"
                                                    className="max-w-[150px] h-auto rounded-md border border-gray-200 cursor-pointer hover:opacity-80 transition-opacity"
                                                    onClick={() => handleImageClick(studentPhotoUrl, 'Фото студента')}
                                                    onError={(e) => {
                                                        e.currentTarget.src = '/placeholder-user.jpg';
                                                        e.currentTarget.onerror = null;
                                                    }}
                                                />
                                            ) : (
                                                <span className="text-gray-600">Не загружено</span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <Label className="font-semibold text-gray-700">Аттестат</Label>
                                        <div className="mt-2">
                                            {attestationPhotoUrl ? (
                                                <img
                                                    src={attestationPhotoUrl}
                                                    alt="Аттестат"
                                                    className="max-w-[150px] h-auto rounded-md border border-gray-200 cursor-pointer hover:opacity-80 transition-opacity"
                                                    onClick={() => handleImageClick(attestationPhotoUrl, 'Аттестат')}
                                                    onError={(e) => {
                                                        e.currentTarget.src = '/placeholder-attestation.jpg';
                                                        e.currentTarget.onerror = null;
                                                    }}
                                                />
                                            ) : (
                                                <span className="text-gray-600">Не загружен</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </DialogContent>
            </Dialog>

            {/* Диалог для просмотра изображения в высоком разрешении */}
            <ImagePreviewDialog
                open={isImagePreviewOpen}
                onOpenChange={setIsImagePreviewOpen}
                imageUrl={selectedImageUrl}
                title={selectedImageTitle}
            />
        </>
    );
};