import { useEffect } from 'react';
import { Toaster } from '@/components/ui/toaster';
import { Toaster as Sonner } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import VerifyEmailPage from '@/pages/VerifyEmailPage';
import DashboardPage from '@/pages/DashboardPage';
import ApplicationsPage from '@/pages/ApplicationsPage';
import SpecialtiesPage from '@/pages/SpecialtiesPage';
import ProfileSettingsPage from '@/pages/ProfileSettingsPage';
import NotFound from '@/pages/NotFound';
import ApplicationSubmissionPage from '@/pages/ApplicationSubmissionPage';
import ApplicationsReviewPage from '@/pages/ApplicationsReviewPage';
import ChatPage from '@/pages/ChatPage';
import ModeratorsPage from '@/pages/ModeratorsPage';
import InstitutionsPage from '@/pages/InstitutionsPage';
import LandingPage from '@/pages/LandingPage';
import InstitutionsApplyPage from "@/pages/InstitutionsApplyPage";
import LeaderboardPage from "@/pages/LeaderboardPage";

// Тип для ролей
type UserRole = 'applicant' | 'moderator' | 'admin_app' | 'admin_org' | null;

// Protected route component с проверкой ролей
const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode; allowedRoles: UserRole[] }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="p-6 text-center">Загрузка...</div>;
    }

    const token = localStorage.getItem('access_token');
    if (!token || !user) {
        return <Navigate to="/login" replace />;
    }

    const userRole = user.role;
    if (!allowedRoles.includes(userRole)) {
        return <Navigate to="/404" replace />;
    }

    return <>{children}</>;
};

// Компонент для управления классами скролла
const ScrollManager = ({ children }: { children: React.ReactNode }) => {
    const location = useLocation();

    useEffect(() => {
        const root = document.getElementById('root');
        if (!root) return;

        // Страницы, которые должны быть прокручиваемыми
        const scrollableRoutes = ['/', '/institutions-apply'];

        if (scrollableRoutes.includes(location.pathname)) {
            root.classList.remove('no-scroll');
            root.classList.add('scrollable');
            root.style.overflowY = 'auto'; // Явно включаем скролл
        } else {
            root.classList.remove('scrollable');
            root.classList.add('no-scroll');
            root.style.overflowY = 'hidden'; // Явно отключаем скролл
        }
    }, [location.pathname]);

    return <>{children}</>;
};

const queryClient = new QueryClient();

const App = () => {
    useEffect(() => {
        const calculateScrollbarWidth = () => {
            const outer = document.createElement('div');
            outer.style.visibility = 'hidden';
            outer.style.overflow = 'scroll';
            document.body.appendChild(outer);

            const inner = document.createElement('div');
            outer.appendChild(inner);

            const scrollbarWidth = outer.offsetWidth - inner.offsetWidth;

            outer.remove();
            return scrollbarWidth;
        };

        const scrollbarWidth = calculateScrollbarWidth();
        document.documentElement.style.setProperty('--scrollbar-width', `${scrollbarWidth}px`);
    }, []);

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <TooltipProvider>
                    <Toaster />
                    <Sonner />
                    <BrowserRouter>
                        <ScrollManager>
                            <Routes>
                                <Route path="/" element={<LandingPage />} />
                                <Route path="/login" element={<LoginPage />} />
                                <Route path="/register" element={<RegisterPage />} />
                                <Route path="/verify-email" element={<VerifyEmailPage />} />
                                <Route path="/institutions-apply" element={<InstitutionsApplyPage />} />
                                <Route
                                    path="/messages"
                                    element={
                                        <ProtectedRoute allowedRoles={['applicant', 'moderator', 'admin_org']}>
                                            <ChatPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/applications-manage"
                                    element={
                                        <ProtectedRoute allowedRoles={['moderator', 'admin_org']}>
                                            <ApplicationsReviewPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/moderators"
                                    element={
                                        <ProtectedRoute allowedRoles={['admin_org']}>
                                            <ModeratorsPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/institutions"
                                    element={
                                        <ProtectedRoute allowedRoles={['admin_app']}>
                                            <InstitutionsPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/specialties"
                                    element={
                                        <ProtectedRoute allowedRoles={['applicant', 'admin_org']}>
                                            <SpecialtiesPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/leaderboard"
                                    element={
                                        <ProtectedRoute allowedRoles={['applicant', 'admin_org', 'moderator']}>
                                            <LeaderboardPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/settings"
                                    element={
                                        <ProtectedRoute allowedRoles={['applicant', 'moderator', 'admin_org', 'admin_app']}>
                                            <ProfileSettingsPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/dashboard"
                                    element={
                                        <ProtectedRoute allowedRoles={['applicant', 'moderator', 'admin_org', 'admin_app']}>
                                            <DashboardPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/applications"
                                    element={
                                        <ProtectedRoute allowedRoles={['applicant']}>
                                            <ApplicationsPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route
                                    path="/application/:specialtyId/:organizationId"
                                    element={
                                        <ProtectedRoute allowedRoles={['applicant']}>
                                            <ApplicationSubmissionPage />
                                        </ProtectedRoute>
                                    }
                                />
                                <Route path="/404" element={<NotFound />} />
                                <Route path="*" element={<Navigate to="/404" replace />} />
                            </Routes>
                        </ScrollManager>
                    </BrowserRouter>
                </TooltipProvider>
            </AuthProvider>
        </QueryClientProvider>
    );
};

export default App;