import React, { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { ArrowLeft, Building, FileText, MapPin, Mail, Phone, Globe, CheckCircle, CreditCard } from "lucide-react";
import { Link } from "react-router-dom";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "@/components/ui/select";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { institutionAPI } from "@/services/api";

const formSchema = z.object({
    institutionName: z.string().min(3, {
        message: "Название должно содержать не менее 3 символов",
    }),
    institutionType: z.enum(["university", "college", "school", "other"], {
        required_error: "Пожалуйста, выберите тип учебного заведения",
    }),
    email: z.string().email({
        message: "Введите корректный email адрес",
    }),
    phone: z.string().min(10, {
        message: "Введите корректный номер телефона",
    }),
    address: z.string().min(5, {
        message: "Адрес должен содержать не менее 5 символов",
    }),
    city: z.string().min(2, {
        message: "Город должен содержать не менее 2 символов",
    }), // Новое поле
    website: z.string().url({
        message: "Введите корректный URL сайта",
    }).optional().or(z.literal('')),
    description: z.string().min(30, {
        message: "Описание должно содержать не менее 30 символов",
    }),
    acceptTerms: z.boolean().refine(val => val === true, {
        message: "Необходимо принять условия"
    }),
});

type FormValues = z.infer<typeof formSchema>;

const InstitutionsApplyPage = () => {
    const { toast } = useToast();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showSuccessDialog, setShowSuccessDialog] = useState(false);
    const [currentStep, setCurrentStep] = useState<number>(1);
    const [isPaymentProcessing, setIsPaymentProcessing] = useState(false);

    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            institutionName: "",
            institutionType: "university",
            email: "",
            phone: "",
            address: "",
            city: "", // Новое поле
            website: "",
            description: "",
            acceptTerms: false,
        },
        mode: "onChange",
    });

    const handlePayment = async (values: FormValues) => {
        setIsPaymentProcessing(true);

        try {
            const paymentResponse = await institutionAPI.initiatePayment({
                institutionName: values.institutionName,
                email: values.email,
                phone: values.phone,
                address: values.address,
                city: values.city,
                website: values.website,
                description: values.description,
                institutionType: values.institutionType,
                return_url: 'https://applicantcabinet.ru/payment-success"', // Обновленный URL возврата
            });

            window.location.href = paymentResponse.payment_url;
        } catch (error) {
            toast({
                variant: "destructive",
                title: "Ошибка",
                description: error.message || "Произошла ошибка при инициации платежа",
            });
            setIsPaymentProcessing(false);
        }
    };

    const onSubmit = async (values: FormValues) => {
        setIsSubmitting(true);

        try {
            // Проверяем валидацию второго шага
            if (currentStep === 2) {
                setCurrentStep(3); // Переходим к шагу оплаты
            }
        } catch (error) {
            toast({
                variant: "destructive",
                title: "Ошибка",
                description: error.message || "Произошла ошибка при отправке формы",
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    const steps = [
        { number: 1, title: "Основная информация" },
        { number: 2, title: "Подробная информация" },
        { number: 3, title: "Оплата и подтверждение" },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white overflow-auto">
            <div className="container mx-auto max-w-4xl py-12 px-4">
                <Link
                    to="/"
                    className="inline-flex items-center text-appBlue hover:text-appBlue/80 mb-8 transition-colors"
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Вернуться на главную
                </Link>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="mb-8"
                >
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Регистрация учебного заведения</h1>
                    <p className="text-gray-600">
                        Заполните форму, чтобы подать заявку на добавление вашего учебного заведения в систему
                    </p>
                </motion.div>

                <div className="mb-8">
                    <div className="flex justify-between items-center">
                        {steps.map((step, index) => (
                            <React.Fragment key={step.number}>
                                <div className="flex flex-col items-center">
                                    <div
                                        className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 
                      ${currentStep >= step.number
                                            ? "bg-appBlue text-white"
                                            : "bg-gray-200 text-gray-500"}`}
                                    >
                                        {currentStep > step.number ? (
                                            <CheckCircle className="h-5 w-5" />
                                        ) : (
                                            step.number
                                        )}
                                    </div>
                                    <span className={`text-sm ${currentStep >= step.number ? "text-appBlue font-medium" : "text-gray-500"}`}>
                    {step.title}
                  </span>
                                </div>

                                {index < steps.length - 1 && (
                                    <div
                                        className={`flex-1 h-1 mx-4 ${
                                            currentStep > index + 1 ? "bg-appBlue" : "bg-gray-200"
                                        }`}
                                    />
                                )}
                            </React.Fragment>
                        ))}
                    </div>
                </div>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                        <Card className="border-0 shadow-lg">
                            <CardHeader className="bg-appBlue text-white rounded-t-lg">
                                <CardTitle className="text-2xl">
                                    {currentStep === 1 && "Основная информация об учебном заведении"}
                                    {currentStep === 2 && "Подробная информация"}
                                    {currentStep === 3 && "Оплата и подтверждение"}
                                </CardTitle>
                                <CardDescription className="text-blue-100">
                                    {currentStep === 1 && "Заполните основные данные об учебном заведении"}
                                    {currentStep === 2 && "Расскажите подробнее о вашем учебном заведении"}
                                    {currentStep === 3 && "Завершите регистрацию, оплатив услугу"}
                                </CardDescription>
                            </CardHeader>

                            <CardContent className="pt-6">
                                <ScrollArea className="h-[500px]">
                                    {currentStep === 1 && (
                                        <div className="space-y-6">
                                            <div className="flex items-center space-x-3 mb-6 text-appBlue">
                                                <Building className="h-5 w-5" />
                                                <h3 className="text-lg font-medium">Данные об учебном заведении</h3>
                                            </div>

                                            <FormField
                                                control={form.control}
                                                name="institutionName"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Название учебного заведения</FormLabel>
                                                        <FormControl>
                                                            <Input placeholder="Полное официальное название" {...field} />
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <FormField
                                                control={form.control}
                                                name="institutionType"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Тип учебного заведения</FormLabel>
                                                        <Select
                                                            onValueChange={field.onChange}
                                                            defaultValue={field.value}
                                                        >
                                                            <FormControl>
                                                                <SelectTrigger>
                                                                    <SelectValue placeholder="Выберите тип учебного заведения" />
                                                                </SelectTrigger>
                                                            </FormControl>
                                                            <SelectContent>
                                                                <SelectItem value="university">Университет</SelectItem>
                                                                <SelectItem value="college">Колледж</SelectItem>
                                                                <SelectItem value="school">Школа</SelectItem>
                                                                <SelectItem value="other">Другое</SelectItem>
                                                            </SelectContent>
                                                        </Select>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <FormField
                                                    control={form.control}
                                                    name="email"
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel>Email</FormLabel>
                                                            <FormControl>
                                                                <Input placeholder="official@example.com" {...field} type="email" />
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
                                                                <Input placeholder="+7 (XXX) XXX-XX-XX" {...field} />
                                                            </FormControl>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {currentStep === 2 && (
                                        <div className="space-y-6">
                                            <div className="flex items-center space-x-3 mb-6 text-appBlue">
                                                <MapPin className="h-5 w-5" />
                                                <h3 className="text-lg font-medium">Расположение и контакты</h3>
                                            </div>

                                            <FormField
                                                control={form.control}
                                                name="address"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Юридический адрес</FormLabel>
                                                        <FormControl>
                                                            <Input placeholder="Полный юридический адрес" {...field} />
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
                                                            <Input placeholder="Например, Москва" {...field} />
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            /> {/* Новое поле */}

                                            <FormField
                                                control={form.control}
                                                name="website"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Веб-сайт</FormLabel>
                                                        <FormControl>
                                                            <Input placeholder="https://example.com" type="url" {...field} />
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <div className="flex items-center space-x-3 mb-6 text-appBlue">
                                                <FileText className="h-5 w-5" />
                                                <h3 className="text-lg font-medium">Информация об учреждении</h3>
                                            </div>

                                            <FormField
                                                control={form.control}
                                                name="description"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Информация об учебном заведении</FormLabel>
                                                        <FormControl>
                                                            <Textarea
                                                                placeholder="Краткое описание учебного заведения, специализация, особенности"
                                                                className="min-h-[120px]"
                                                                {...field}
                                                            />
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <FormField
                                                control={form.control}
                                                name="acceptTerms"
                                                render={({ field }) => (
                                                    <FormItem className="flex flex-row items-start space-x-3 space-y-0 mt-6">
                                                        <FormControl>
                                                            <Checkbox
                                                                checked={field.value}
                                                                onCheckedChange={field.onChange}
                                                            />
                                                        </FormControl>
                                                        <div className="space-y-1 leading-none">
                                                            <FormLabel>
                                                                Я согласен с <a href="#" className="text-appBlue hover:underline">условиями использования</a> и <a href="#" className="text-appBlue hover:underline">политикой конфиденциальности</a>
                                                            </FormLabel>
                                                            <FormMessage />
                                                        </div>
                                                    </FormItem>
                                                )}
                                            />
                                        </div>
                                    )}

                                    {currentStep === 3 && (
                                        <div className="space-y-6">
                                            <div className="p-6 bg-blue-50 rounded-lg border border-blue-100 mb-6">
                                                <div className="flex items-center space-x-3 mb-4">
                                                    <CreditCard className="h-6 w-6 text-appBlue" />
                                                    <h3 className="text-lg font-medium text-gray-900">Информация об оплате</h3>
                                                </div>

                                                <p className="text-gray-700 mb-4">
                                                    Стоимость регистрации учебного заведения в системе составляет <span className="font-semibold">2000 ₽</span>.
                                                    Оплата производится единоразово и включает:
                                                </p>

                                                <ul className="space-y-2">
                                                    <li className="flex items-start">
                                                        <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                                                        <span>Доступ к системе на один календарный год</span>
                                                    </li>
                                                    <li className="flex items-start">
                                                        <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                                                        <span>Размещение информации об учебном заведении</span>
                                                    </li>
                                                    <li className="flex items-start">
                                                        <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                                                        <span>Возможность принимать и обрабатывать заявки от абитуриентов</span>
                                                    </li>
                                                    <li className="flex items-start">
                                                        <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                                                        <span>Техническая поддержка 24/7</span>
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>
                                    )}
                                </ScrollArea>
                            </CardContent>

                            <CardFooter className="flex flex-col sm:flex-row gap-4 sm:justify-between">
                                {currentStep > 1 && (
                                    <Button
                                        variant="outline"
                                        type="button"
                                        onClick={() => setCurrentStep(prev => prev - 1)}
                                    >
                                        Назад
                                    </Button>
                                )}

                                <div className="flex-1"></div>

                                {currentStep < 3 ? (
                                    <Button
                                        type="button"
                                        className="bg-appBlue hover:bg-appBlue/90"
                                        onClick={() => {
                                            if (currentStep === 1) {
                                                form.trigger(["institutionName", "institutionType", "email", "phone"]);

                                                const firstStepValid = !form.formState.errors.institutionName &&
                                                    !form.formState.errors.institutionType &&
                                                    !form.formState.errors.email &&
                                                    !form.formState.errors.phone;

                                                if (firstStepValid) {
                                                    setCurrentStep(2);
                                                }
                                            } else if (currentStep === 2) {
                                                form.handleSubmit(onSubmit)();
                                            }
                                        }}
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? "Сохранение..." : "Продолжить"}
                                    </Button>
                                ) : (
                                    <Button
                                        type="button"
                                        className="bg-appBlue hover:bg-appBlue/90 w-full sm:w-auto"
                                        onClick={() => handlePayment(form.getValues())}
                                        disabled={isPaymentProcessing}
                                    >
                                        {isPaymentProcessing ? (
                                            <>Обработка платежа...</>
                                        ) : (
                                            <>
                                                Оплатить 2000 ₽
                                                <CreditCard className="ml-2 h-4 w-4" />
                                            </>
                                        )}
                                    </Button>
                                )}
                            </CardFooter>
                        </Card>
                    </form>
                </Form>
            </div>

            <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
                <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-center">Заявка успешно отправлена</DialogTitle>
                        <DialogDescription className="text-center">
                            Ваша заявка на регистрацию учебного заведения успешно отправлена и будет рассмотрена в ближайшее время.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="flex flex-col items-center justify-center py-4">
                        <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
                            <CheckCircle className="w-8 h-8" />
                        </div>
                        <p className="text-center text-gray-700">
                            Мы отправили подтверждение на указанный вами email. Наш специалист свяжется с вами для уточнения деталей.
                        </p>
                    </div>
                    <div className="flex justify-center">
                        <Button
                            onClick={() => {
                                setShowSuccessDialog(false);
                                window.location.href = '/';
                            }}
                        >
                            Вернуться на главную
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default InstitutionsApplyPage;