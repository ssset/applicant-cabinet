import React from 'react';
import { DashboardSidebar } from './DashboardSidebar';

interface DashboardLayoutProps {
    children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
    return (
        <div className="flex min-h-screen bg-gray-50">
            <DashboardSidebar />
            <div className="flex-1 ml-0 md:ml-64">
                <main className="bg-gray-50 min-h-screen">
                    {children}
                </main>
            </div>
        </div>
    );
};
