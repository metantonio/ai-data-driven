import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { DataTable } from '../components/DataTable';
import { Trash2, BarChart3, Clock, Trophy, Database } from 'lucide-react';
import { ColumnDef } from '@tanstack/react-table';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ModelRun {
    run_id: string;
    timestamp: string;
    model_type: string;
    target: string;
    metrics: Record<string, number>;
    features: string[];
    shap_importance?: Record<string, number>;
}

const ModelRegistry: React.FC = () => {
    const [runs, setRuns] = useState<ModelRun[]>([]);
    const [selectedRun, setSelectedRun] = useState<ModelRun | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchRuns = async () => {
        try {
            const resp = await axios.get('http://localhost:8000/api/models');
            setRuns(resp.data);
            if (resp.data.length > 0 && !selectedRun) {
                setSelectedRun(resp.data[0]);
            }
        } catch (err) {
            console.error("Failed to fetch models", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRuns();
    }, []);

    const deleteRun = async (run_id: string) => {
        if (!confirm(`Are you sure you want to delete run ${run_id}?`)) return;
        try {
            await axios.delete(`http://localhost:8000/api/models/${run_id}`);
            setRuns(runs.filter(r => r.run_id !== run_id));
            if (selectedRun?.run_id === run_id) setSelectedRun(null);
        } catch (err) {
            alert("Failed to delete run");
        }
    };

    const columns: ColumnDef<ModelRun>[] = [
        {
            header: 'Run ID',
            accessorKey: 'run_id',
            cell: (info) => <span className="font-mono text-xs">{info.getValue() as string}</span>
        },
        {
            header: 'Algorithm',
            accessorKey: 'model_type',
        },
        {
            header: 'Date',
            accessorKey: 'timestamp',
            cell: (info) => <span className="text-slate-500 text-xs">{info.getValue() as string}</span>
        },
        {
            header: 'Main Metric',
            id: 'metric',
            cell: (info) => {
                const run = info.row.original;
                const metricName = Object.keys(run.metrics)[0];
                const val = run.metrics[metricName];
                return (
                    <div className="flex flex-col">
                        <span className="text-[10px] uppercase text-slate-400 font-bold">{metricName}</span>
                        <span className="font-bold text-cyan-500">{typeof val === 'number' ? val.toFixed(4) : val}</span>
                    </div>
                );
            }
        },
        {
            header: 'Actions',
            id: 'actions',
            cell: (info) => (
                <div className="flex gap-2">
                    <button
                        onClick={() => setSelectedRun(info.row.original)}
                        className="p-1.5 hover:bg-cyan-500/10 text-cyan-500 rounded-lg transition-colors"
                        title="View Details"
                    >
                        <BarChart3 className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => deleteRun(info.row.original.run_id)}
                        className="p-1.5 hover:bg-red-500/10 text-red-500 rounded-lg transition-colors"
                        title="Delete Run"
                    >
                        <Trash2 className="h-4 w-4" />
                    </button>
                </div>
            )
        }
    ];

    const shapData = selectedRun?.shap_importance
        ? Object.entries(selectedRun.shap_importance)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10)
        : [];

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-8 mt-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-cyan-500/10 rounded-2xl border border-cyan-500/20">
                        <Database className="h-8 w-8 text-cyan-500" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-500 to-blue-600 dark:from-cyan-400 dark:to-blue-500">
                            Model Registry
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400">Track and compare your machine learning experiments</p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* List Table */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-800/50 p-6 rounded-3xl border border-slate-200 dark:border-slate-700/50 shadow-xl overflow-hidden self-start">
                    <div className="flex items-center gap-2 mb-6 text-slate-400 italic text-sm">
                        <Clock className="h-4 w-4" />
                        Historical Training Runs
                    </div>
                    {loading ? (
                        <div className="h-64 flex items-center justify-center text-slate-500">Loading registry...</div>
                    ) : (
                        <DataTable data={runs} columns={columns} pageSize={10} />
                    )}
                </div>

                {/* Details Side Panel */}
                <div className="space-y-6">
                    {selectedRun ? (
                        <div className="bg-white dark:bg-slate-800/50 p-8 rounded-3xl border border-slate-200 dark:border-slate-700/50 shadow-xl animate-in fade-in slide-in-from-right-4">
                            <h3 className="text-xl font-bold mb-1">{selectedRun.model_type}</h3>
                            <div className="text-xs text-slate-400 font-mono mb-6">{selectedRun.run_id}</div>

                            <div className="space-y-6">
                                <div>
                                    <div className="text-[10px] uppercase font-black text-slate-400 mb-2 tracking-widest flex items-center gap-1">
                                        <Trophy className="h-3 w-3" />
                                        Performance Metrics
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        {Object.entries(selectedRun.metrics).map(([k, v]) => (
                                            <div key={k} className="bg-slate-50 dark:bg-slate-900/50 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                                                <div className="text-[10px] text-slate-500 uppercase">{k}</div>
                                                <div className="text-lg font-bold text-cyan-500">{typeof v === 'number' ? v.toFixed(4) : v}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {shapData.length > 0 && (
                                    <div>
                                        <div className="text-[10px] uppercase font-black text-slate-400 mb-4 tracking-widest flex items-center gap-1">
                                            <BarChart3 className="h-3 w-3" />
                                            Feature Importance (SHAP)
                                        </div>
                                        <div className="h-64 -ml-4">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={shapData} layout="vertical" margin={{ left: 20 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                                                    <XAxis type="number" hide />
                                                    <YAxis
                                                        dataKey="name"
                                                        type="category"
                                                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                                                        width={80}
                                                    />
                                                    <Tooltip
                                                        cursor={{ fill: 'transparent' }}
                                                        contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', fontSize: '12px' }}
                                                    />
                                                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                                        {shapData.map((_, index) => (
                                                            <Cell key={`cell-${index}`} fill={`url(#gradient-${index})`} />
                                                        ))}
                                                    </Bar>
                                                    <defs>
                                                        {shapData.map((_, index) => (
                                                            <linearGradient key={`gradient-${index}`} id={`gradient-${index}`} x1="0" y1="0" x2="1" y2="0">
                                                                <stop offset="0%" stopColor="#0891b2" />
                                                                <stop offset="100%" stopColor="#22d3ee" />
                                                            </linearGradient>
                                                        ))}
                                                    </defs>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="bg-slate-50 dark:bg-slate-900/30 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl h-full flex flex-col items-center justify-center p-12 text-center text-slate-400">
                            <BarChart3 className="h-12 w-12 mb-4 opacity-20" />
                            <p>Select a model run to view detailed insights and feature importance.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ModelRegistry;
