
// src/pages/VerifyEmailPage.tsx
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { authAPI } from '@/services/api';

const VerifyEmailPage = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { toast } = useToast();
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = searchParams.get('token');
        if (!token) {
            toast({
                variant: "destructive",
                title: "Ошибка",
                description: "Токен верификации отсутствует",
            });
            setLoading(false);
            return;
        }

        const verifyEmail = async () => {
            try {
                await authAPI.verifyEmail(token);
                toast({
                    title: "Успех",
                    description: "Email успешно подтверждён! Перенаправляем на страницу входа...",
                });
                setTimeout(() => {
                    navigate('/login');
                }, 2000);
            } catch (error: any) {
                toast({
                    variant: "destructive",
                    title: "Ошибка",
                    description: error.message || "Не удалось подтвердить email",
                });
            } finally {
                setLoading(false);
            }
        };

        verifyEmail();
    }, [searchParams, navigate, toast]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle>Подтверждение email</CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <p className="text-center">Проверяем токен...</p>
                    ) : (
                        <p className="text-center">
                            Если email подтверждён, вы будете перенаправлены на страницу входа.
                        </p>
                    )}
                    <Button
                        className="mt-4 w-full"
                        onClick={() => navigate('/login')}
                        disabled={loading}
                    >
                        Перейти на страницу входа
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
};

export default VerifyEmailPage;
