import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { BrainCircuit, Play, Loader, TrendingUp, AlertCircle, ChevronLeft, Database, Sliders, Calculator } from 'lucide-react';
import { predict } from '../api/client';

interface ModelRun {
    run_id: string;
    timestamp: string;
    model_type: string;
    target: string;
    metrics: Record<string, number>;
    features: string[];
    shap_importance?: Record<string, number>;
}

const PredictionSandbox: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [runs, setRuns] = useState<ModelRun[]>([]);
    const [selectedRun, setSelectedRun] = useState<ModelRun | null>(null);
    const [loading, setLoading] = useState(true);
    const [formData, setFormData] = useState<Record<string, string>>({});
    const [prediction, setPrediction] = useState<any>(null);
    const [predicting, setPredicting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchRuns = async () => {
        try {
            const resp = await axios.get('http://localhost:8000/api/models');
            setRuns(resp.data);

            // Check if there's a run_id in the location state (from Registry)
            const preselectedRunId = location.state?.run_id;
            if (preselectedRunId) {
                const found = resp.data.find((r: ModelRun) => r.run_id === preselectedRunId);
                if (found) setSelectedRun(found);
            } else if (resp.data.length > 0) {
                setSelectedRun(resp.data[0]);
            }
        } catch (err) {
            console.error("Failed to fetch models", err);
            setError("Could not load model registry.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRuns();
    }, []);

    useEffect(() => {
        if (selectedRun) {
            const initial: Record<string, string> = {};
            selectedRun.features.forEach(f => initial[f] = "");
            setFormData(initial);
            setPrediction(null);
        }
    }, [selectedRun]);

    const handlePredict = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedRun) return;

        setPredicting(true);
        setError(null);
        try {
            const formatted: any = {};
            for (const key of selectedRun.features) {
                const val = formData[key];
                formatted[key] = isNaN(Number(val)) || val === "" ? val : Number(val);
            }

            const modelPath = `models/${selectedRun.run_id}/model.joblib`;
            const res = await predict(modelPath, formatted);
            setPrediction(res.prediction);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Prediction failed.");
        } finally {
            setPredicting(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-8 mt-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/registry')}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all text-slate-400 hover:text-cyan-500 border border-transparent hover:border-slate-200 dark:hover:border-slate-700"
                        title="Back to Registry"
                    >
                        <ChevronLeft className="h-6 w-6" />
                    </button>
                    <div className="p-3 bg-purple-500/10 rounded-2xl border border-purple-500/20">
                        <BrainCircuit className="h-8 w-8 text-purple-500" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-indigo-600 dark:from-purple-400 dark:to-indigo-500">
                            Prediction Sandbox
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400">Validate your models with interactive manual testing</p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Model Selection Column */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white dark:bg-slate-800/50 p-6 rounded-3xl border border-slate-200 dark:border-slate-700/50 shadow-xl self-start">
                        <div className="flex items-center gap-2 mb-4 text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                            <Database className="h-3 w-3" />
                            Select Model
                        </div>
                        {loading ? (
                            <div className="py-8 flex justify-center"><Loader className="animate-spin h-5 w-5 text-purple-500" /></div>
                        ) : (
                            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                                {runs.map(run => (
                                    <button
                                        key={run.run_id}
                                        onClick={() => setSelectedRun(run)}
                                        className={`w-full text-left p-3 rounded-xl border transition-all ${selectedRun?.run_id === run.run_id
                                            ? 'bg-purple-500/10 border-purple-500 text-purple-600 dark:text-purple-400'
                                            : 'bg-slate-50 dark:bg-slate-900/50 border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-purple-500/30'
                                            }`}
                                    >
                                        <div className="font-bold text-sm truncate">{run.model_type}</div>
                                        <div className="text-[10px] opacity-60 font-mono">{run.run_id}</div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {selectedRun && (
                        <div className="bg-slate-900 text-white p-6 rounded-3xl shadow-xl space-y-4">
                            <div className="flex items-center gap-2 text-purple-400 text-[10px] uppercase font-bold tracking-widest">
                                <TrendingUp className="h-3 w-3" />
                                Model Info
                            </div>
                            <div>
                                <div className="text-sm font-bold text-slate-400">Target Feature</div>
                                <div className="text-lg font-black text-white">{selectedRun.target}</div>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                {Object.entries(selectedRun.metrics).map(([k, v]) => (
                                    <div key={k} className="bg-white/5 p-2 rounded-lg border border-white/10">
                                        <div className="text-[8px] text-slate-500 uppercase">{k}</div>
                                        <div className="text-sm font-bold text-purple-400">{typeof v === 'number' ? v.toFixed(3) : v}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Input Controls Column */}
                <div className="lg:col-span-2 space-y-6">
                    {selectedRun ? (
                        <div className="bg-white dark:bg-slate-800/50 p-8 rounded-3xl border border-slate-200 dark:border-slate-700/50 shadow-xl h-full">
                            <div className="flex items-center gap-2 mb-8 text-slate-400 font-bold uppercase text-[10px] tracking-widest border-b border-slate-100 dark:border-slate-700/50 pb-4">
                                <Sliders className="h-3 w-3" />
                                Feature Inputs
                            </div>
                            <form onSubmit={handlePredict} className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {selectedRun.features.map(feature => (
                                        <div key={feature} className="space-y-2">
                                            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">{feature.replace(/_/g, ' ')}</label>
                                            <input
                                                type="text"
                                                value={formData[feature] || ""}
                                                onChange={(e) => setFormData({ ...formData, [feature]: e.target.value })}
                                                placeholder={`Value for ${feature}`}
                                                className="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all font-mono text-sm"
                                                required
                                            />
                                        </div>
                                    ))}
                                </div>
                                <button
                                    type="submit"
                                    disabled={predicting}
                                    className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-4 rounded-2xl shadow-xl transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 flex items-center justify-center gap-3"
                                >
                                    {predicting ? <Loader className="animate-spin h-5 w-5" /> : <Play className="h-5 w-5 fill-current" />}
                                    <span>Run Prediction</span>
                                </button>
                            </form>
                        </div>
                    ) : (
                        <div className="bg-slate-50 dark:bg-slate-900/30 border-2 border-dashed border-slate-100 dark:border-slate-800 rounded-3xl h-full flex items-center justify-center p-12 text-center text-slate-400 font-medium">
                            <p>Select a model from the registry to start testing inputs.</p>
                        </div>
                    )}
                </div>

                {/* Result Column */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-gradient-to-br from-slate-900 to-indigo-950 p-8 rounded-3xl shadow-2xl h-full relative overflow-hidden group">
                        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl group-hover:bg-purple-500/20 transition-all duration-1000"></div>

                        <div className="relative z-10 flex flex-col h-full">
                            <div className="flex items-center gap-2 mb-8 text-purple-400 font-bold uppercase text-[10px] tracking-widest border-b border-white/5 pb-4">
                                <Calculator className="h-3 w-3" />
                                Prediction Result
                            </div>

                            <div className="flex-1 flex flex-col items-center justify-center text-center space-y-6">
                                {prediction !== null ? (
                                    <div className="animate-in zoom-in-90 duration-500">
                                        <div className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-2">Estimated Value</div>
                                        <div className="text-6xl font-black text-white tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
                                            {typeof prediction === 'number' ?
                                                (prediction < 1 ? prediction.toFixed(4) : prediction.toLocaleString(undefined, { maximumFractionDigits: 2 }))
                                                : prediction}
                                        </div>
                                        <div className="mt-8 inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/20 rounded-full border border-emerald-500/30 text-emerald-400 text-xs font-bold animate-pulse">
                                            <AlertCircle className="h-3.5 w-3.5" />
                                            Live Inference Ready
                                        </div>
                                    </div>
                                ) : (
                                    <div className="opacity-20 flex flex-col items-center gap-4">
                                        <Calculator className="h-20 w-20 text-white" />
                                        <p className="text-sm font-medium text-slate-400 max-w-[150px]">Fill the features and click run to see results</p>
                                    </div>
                                )}
                            </div>

                            {error && (
                                <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-2xl text-red-400 text-xs font-medium flex items-start gap-2">
                                    <AlertCircle className="h-4 w-4 shrink-0" />
                                    <span>{error}</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PredictionSandbox;
