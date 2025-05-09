
// src/components/auth/RegisterForm.tsx
import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { useNavigate, Link } from 'react-router-dom';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { motion } from 'framer-motion';
import { AlertCircle, Mail } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { authAPI } from '@/services/api';

type RegisterFormData = {
    email: string;
    password: string;
    password2: string;
    consent_to_data_processing: boolean;
};

const RegisterForm = () => {
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const navigate = useNavigate();
    const { toast } = useToast();

    const {
        register,
        handleSubmit,
        watch,
        control,
        formState: { errors },
    } = useForm<RegisterFormData>({
        defaultValues: {
            email: '',
            password: '',
            password2: '',
            consent_to_data_processing: false,
        },
    });

    const password = watch('password');
    const email = watch('email');

    const onSubmit = async (data: RegisterFormData) => {
        try {
            setIsSubmitting(true);
            setError(null);

            // Логируем данные перед отправкой
            console.log('Form data:', data);

            // Отправляем запрос на регистрацию
            await authAPI.register(
                data.email,
                data.password,
                data.password2,
                data.consent_to_data_processing
            );

            setIsDialogOpen(true); // Открываем попап после успешной регистрации
        } catch (err: any) {
            const errorMessage =
                err.message ||
                (typeof err.response?.data === 'object'
                    ? Object.values(err.response.data).join(', ')
                    : 'Произошла ошибка при регистрации');
            setError(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDialogClose = () => {
        setIsDialogOpen(false);
        navigate('/login'); // Перенаправляем на страницу логина после закрытия попапа
    };

    return (
        <>
            <motion.div
                className="login-card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
            >
                <div className="text-center mb-6">
                    <h2 className="text-3xl font-bold text-gray-800">Регистрация</h2>
                    <p className="text-gray-600 mt-2">Создайте новую учетную запись</p>
                </div>

                {error && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        transition={{ duration: 0.3 }}
                        className="mb-6"
                    >
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>Ошибка</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    </motion.div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="your@email.com"
                            {...register('email', {
                                required: 'Email обязателен',
                                pattern: {
                                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                    message: 'Неверный формат email',
                                },
                            })}
                            className={errors.email ? 'border-red-500' : ''}
                        />
                        {errors.email && (
                            <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="password">Пароль</Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder="••••••••"
                            {...register('password', {
                                required: 'Пароль обязателен',
                                minLength: {
                                    value: 6,
                                    message: 'Пароль должен содержать минимум 6 символов',
                                },
                            })}
                            className={errors.password ? 'border-red-500' : ''}
                        />
                        {errors.password && (
                            <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="password2">Повторите пароль</Label>
                        <Input
                            id="password2"
                            type="password"
                            placeholder="••••••••"
                            {...register('password2', {
                                required: 'Повторите пароль',
                                validate: (value) =>
                                    value === password || 'Пароли не совпадают',
                            })}
                            className={errors.password2 ? 'border-red-500' : ''}
                        />
                        {errors.password2 && (
                            <p className="text-red-500 text-sm mt-1">{errors.password2.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                            <Controller
                                name="consent_to_data_processing"
                                control={control}
                                rules={{ required: 'Необходимо дать согласие на обработку данных' }}
                                render={({ field }) => (
                                    <Checkbox
                                        id="consent_to_data_processing"
                                        checked={field.value}
                                        onCheckedChange={field.onChange}
                                    />
                                )}
                            />
                            <Label htmlFor="consent_to_data_processing">
                                Согласие на обработку персональных данных
                            </Label>
                        </div>
                        {errors.consent_to_data_processing && (
                            <p className="text-red-500 text-sm mt-1">
                                {errors.consent_to_data_processing.message}
                            </p>
                        )}
                    </div>

                    <motion.div
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="pt-2"
                    >
                        <Button
                            type="submit"
                            className="w-full bg-appBlue hover:bg-blue-700 transition-colors"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? (
                                <>
                                    <svg
                                        className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        ></circle>
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                        ></path>
                                    </svg>
                                    Регистрация...
                                </>
                            ) : (
                                'Зарегистрироваться'
                            )}
                        </Button>
                    </motion.div>
                </form>

                <div className="mt-6 text-center text-sm">
                    <span className="text-gray-600">Уже есть учетная запись? </span>
                    <Link to="/login" className="text-appBlue hover:underline font-medium">
                        Войти
                    </Link>
                </div>
            </motion.div>

            {/* Попап с сообщением */}
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Mail className="h-5 w-5 text-green-500" />
                            Регистрация успешно завершена!
                        </DialogTitle>
                        <DialogDescription>
                            Мы отправили вам письмо на <span className="font-medium">{email}</span>. 
                            Пожалуйста, откройте письмо и перейдите по ссылке, чтобы подтвердить ваш email. 
                            После подтверждения вы сможете войти в систему.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button onClick={handleDialogClose} className="w-full">
                            Перейти к входу
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default RegisterForm;
