// src/components/auth/VerifyEmailForm.tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useNavigate, useLocation, Link } from 'react-router-dom'; // Добавляем импорт Link
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { motion } from 'framer-motion';
import { AlertCircle } from 'lucide-react';
import api from '@/services/api';
import { useToast } from '@/components/ui/use-toast';

type VerifyEmailFormData = {
    email: string;
    verification_code: string;
};

const VerifyEmailForm = () => {
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const { toast } = useToast();

    const emailFromState = location.state?.email || '';

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<VerifyEmailFormData>({
        defaultValues: {
            email: emailFromState,
            verification_code: '',
        },
    });

    const onSubmit = async (data: VerifyEmailFormData) => {
        try {
            setIsSubmitting(true);
            setError(null);

            // Отправляем запрос на верификацию
            const response = await api.post('/auth/verify/', {
                email: data.email,
                verification_code: data.verification_code,
            });

            // Сохраняем токены
            localStorage.setItem('access_token', response.data.access);
            localStorage.setItem('user_role', response.data.role);

            toast({
                title: 'Email успешно подтверждён',
                description: 'Теперь вы можете войти в систему.',
            });

            // Перенаправляем на страницу логина
            navigate('/login');
        } catch (err: any) {
            const errorMessage =
                err.response?.data?.message ||
                (typeof err.response?.data === 'object'
                    ? Object.values(err.response.data).join(', ')
                    : 'Произошла ошибка при верификации');
            setError(errorMessage);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <motion.div
            className="login-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
        >
            <div className="text-center mb-6">
                <h2 className="text-3xl font-bold text-gray-800">Подтверждение Email</h2>
                <p className="text-gray-600 mt-2">Введите код, отправленный на ваш email</p>
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
                        disabled={!!emailFromState} // Отключаем поле, если email передан через state
                    />
                    {errors.email && (
                        <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
                    )}
                </div>

                <div className="space-y-2">
                    <Label htmlFor="verification_code">Код верификации</Label>
                    <Input
                        id="verification_code"
                        type="text"
                        placeholder="Введите код"
                        {...register('verification_code', {
                            required: 'Код верификации обязателен',
                            minLength: {
                                value: 8,
                                message: 'Код должен содержать 8 символов',
                            },
                            maxLength: {
                                value: 8,
                                message: 'Код должен содержать 8 символов',
                            },
                        })}
                        className={errors.verification_code ? 'border-red-500' : ''}
                    />
                    {errors.verification_code && (
                        <p className="text-red-500 text-sm mt-1">{errors.verification_code.message}</p>
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
                                Подтверждение...
                            </>
                        ) : (
                            'Подтвердить'
                        )}
                    </Button>
                </motion.div>
            </form>

            <div className="mt-6 text-center text-sm">
                <span className="text-gray-600">Уже подтвердили email? </span>
                <Link to="/login" className="text-appBlue hover:underline font-medium">
                    Войти
                </Link>
            </div>
        </motion.div>
    );
};

export default VerifyEmailForm;