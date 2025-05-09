
// src/components/dashboard/Charts.tsx
import { useEffect, useState } from 'react';
import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent
} from "@/components/ui/chart";
import {
    Line,
    Bar,
    Pie,
    PieChart as RechartsPieChart,
    BarChart as RechartsBarChart,
    LineChart as RechartsLineChart,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Cell
} from 'recharts';
import { statisticsAPI } from '@/services/api';

const COLORS = ['#8B5CF6', '#D946EF', '#F97316', '#0EA5E9', '#403E43'];

export const BarChart = ({ role }: { role: string }) => {
    const [data, setData] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                let response;
                if (role === 'admin_app') {
                    response = await statisticsAPI.getSystemStats();
                } else {
                    response = await statisticsAPI.getApplicationStats();
                }
                setData(response);
            } catch (error) {
                console.error('Error fetching bar chart data:', error);
            }
        };
        fetchData();
    }, [role]);

    return (
        <div className="w-full h-full">
            <ChartContainer
                config={{
                    Заявки: {
                        label: 'Заявки за этот день: ',
                        color: '#8B5CF6',
                    },
                }}
                className="w-full h-full"
            >
                <RechartsBarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <ChartLegend content={<ChartLegendContent />} />
                    <Bar dataKey="Заявки" fill="#8B5CF6" />
                </RechartsBarChart>
            </ChartContainer>
        </div>
    );
};

export const PieChart = ({ role }: { role: string }) => {
    const [data, setData] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                let response;
                if (role === 'admin_app') {
                    response = await statisticsAPI.getInstitutionStats();
                } else {
                    response = await statisticsAPI.getSpecialtyStats();
                }
                setData(response);
            } catch (error) {
                console.error('Error fetching pie chart data:', error);
            }
        };
        fetchData();
    }, [role]);

    return (
        <div className="w-full h-full">
            <ChartContainer
                config={{
                    pieData: {
                        label: 'Распределение за текущую неделю',
                    },
                }}
                className="w-full h-full"
            >
                <RechartsPieChart margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                    >
                        {data.map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <ChartLegend />
                </RechartsPieChart>
            </ChartContainer>
        </div>
    );
};

export const LineChart = ({ role }: { role: string }) => {
    const [data, setData] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                let response;
                if (role === 'admin_app') {
                    response = await statisticsAPI.getAdminActivityStats();
                } else if (role === 'admin_org') {
                    response = await statisticsAPI.getModeratorActivityStats();
                } else {
                    response = await statisticsAPI.getActivityStats();
                }
                setData(response);
            } catch (error) {
                console.error('Error fetching line chart data:', error);
            }
        };
        fetchData();
    }, [role]);

    return (
        <div className="w-full h-full">
            <ChartContainer
                config={{
                    Активность: {
                        label: 'Активность за текущую неделю',
                        color: '#0EA5E9',
                    },
                }}
                className="w-full h-full"
            >
                <RechartsLineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <ChartLegend content={<ChartLegendContent />} />
                    <Line type="monotone" dataKey="Активность" stroke="#0EA5E9" activeDot={{ r: 8 }} />
                </RechartsLineChart>
            </ChartContainer>
        </div>
    );
};
