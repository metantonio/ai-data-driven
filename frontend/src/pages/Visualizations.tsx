import { useLocation, useNavigate } from 'react-router-dom';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { ChevronLeft, BarChart2 } from 'lucide-react';
import { DataTable } from '../components/DataTable';
import { ColumnDef } from '@tanstack/react-table';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export default function Visualizations() {
    const location = useLocation();
    const navigate = useNavigate();
    const { report, algorithmType } = location.state || {};

    if (!report || !report.visualization_data) {
        return (
            <div className="min-h-screen bg-slate-900 text-slate-50 flex items-center justify-center p-6">
                <div className="text-center space-y-4">
                    <h2 className="text-2xl font-bold">No Visualization Data Available</h2>
                    <p className="text-slate-400">The current model run didn't produce compatible visualization data.</p>
                    <button onClick={() => navigate(-1)} className="text-cyan-400 hover:underline">Go Back</button>
                </div>
            </div>
        );
    }

    const data = report.visualization_data;

    const renderChart = () => {
        if (algorithmType.includes('regression')) {
            return (
                <div className="h-[500px] w-full bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-xl font-semibold mb-4 text-slate-200">Actual vs Predicted</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis type="number" dataKey="Actual" name="Actual" stroke="#94a3b8" label={{ value: 'Actual', position: 'insideBottom', offset: -10 }} />
                            <YAxis type="number" dataKey="Predicted" name="Predicted" stroke="#94a3b8" label={{ value: 'Predicted', angle: -90, position: 'insideLeft' }} />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} />
                            <Legend />
                            <Scatter name="Predictions" data={data} fill="#8884d8" />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>
            );
        }

        if (algorithmType.includes('kmeans') || algorithmType.includes('clustering')) {
            const keys = Object.keys(data[0] || {}).filter(k => k !== 'cluster');
            const xKey = keys[0];
            const yKey = keys[1];

            return (
                <div className="h-[500px] w-full bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-xl font-semibold mb-4 text-slate-200">Cluster Visualization ({xKey} vs {yKey})</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis type="number" dataKey={xKey} name={xKey} stroke="#94a3b8" label={{ value: xKey, position: 'insideBottom', offset: -10 }} />
                            <YAxis type="number" dataKey={yKey} name={yKey} stroke="#94a3b8" label={{ value: yKey, angle: -90, position: 'insideLeft' }} />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} />
                            <Legend />
                            <Scatter name="Clusters" data={data} fill="#8884d8">
                                {data.map((entry: any, index: number) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[entry.cluster % COLORS.length]} />
                                ))}
                            </Scatter>
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>
            );
        }

        return (
            <div className="text-center p-12 text-slate-400 border border-dashed border-slate-700 rounded-xl">
                <BarChart2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Visualization not yet implemented for this algorithm type.</p>
                <div className="mt-4 text-left max-h-60 overflow-auto bg-slate-950 p-4 rounded text-xs font-mono">
                    {JSON.stringify(data[0], null, 2)}
                    ...
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50 p-6 md:p-12">
            <div className="max-w-6xl mx-auto space-y-8">
                <div className="flex items-center gap-4 border-b border-slate-700/50 pb-6">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                        <ChevronLeft className="h-6 w-6 text-slate-400" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold">Model Visualizations</h1>
                        <p className="text-slate-400">
                            {algorithmType ? algorithmType.replace(/_/g, ' ').toUpperCase() : 'Analysis'} Results
                        </p>
                    </div>
                </div>

                {renderChart()}

                <div className="bg-white dark:bg-slate-800/50 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg">
                    <h3 className="text-xl font-semibold mb-6 text-slate-500 dark:text-slate-200 uppercase tracking-widest text-sm font-bold">Raw Data Sample</h3>
                    <DataTable
                        data={data}
                        columns={
                            data.length > 0
                                ? Object.keys(data[0]).map(key => ({
                                    header: key,
                                    accessorKey: key,
                                    cell: (info: any) => {
                                        const val = info.getValue();
                                        return typeof val === 'number' ? val.toFixed(4) : String(val);
                                    }
                                })) as ColumnDef<any, any>[]
                                : []
                        }
                        pageSize={10}
                    />
                </div>
            </div>
        </div>
    );
}
