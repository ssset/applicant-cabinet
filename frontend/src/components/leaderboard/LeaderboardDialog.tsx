import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users } from 'lucide-react';
import Leaderboard from './Leaderboard';
import { specialtyAPI } from '@/services/api';

interface SpecialtyCardProps {
    id: number;
    buildingSpecialtyId: number;
    name: string;
    code: string;
    description?: string;
}

const SpecialtyCard: React.FC<SpecialtyCardProps> = ({ id, buildingSpecialtyId, name, code, description }) => {
    const [showLeaderboard, setShowLeaderboard] = useState(false);
    const [students, setStudents] = useState<any[]>([]);

    const handleOpenLeaderboard = async () => {
        try {
            const response = await specialtyAPI.getLeaderboard(buildingSpecialtyId);
            setStudents(response.leaderboard);
            setShowLeaderboard(true);
        } catch (error) {
            console.error('Failed to fetch leaderboard:', error);
        }
    };

    return (
        <>
            <Card className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-lg font-semibold mb-2">{name}</h3>
                            <p className="text-sm text-muted-foreground mb-4">Код: {code}</p>
                            {description && (
                                <p className="text-sm text-muted-foreground mb-4">{description}</p>
                            )}
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleOpenLeaderboard}
                            className="flex items-center gap-2"
                        >
                            <Users className="w-4 h-4" />
                            <span>Рейтинг</span>
                        </Button>
                    </div>
                </CardContent>
            </Card>

            <Leaderboard
                students={students}
                specialtyName={name}
                open={showLeaderboard}
                onClose={() => setShowLeaderboard(false)}
            />
        </>
    );
};

export default SpecialtyCard;