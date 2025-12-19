import { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { runAutomaticEDAStream } from '../api/client';
import { Loader, MessageSquare, Lightbulb, CheckCircle, ArrowRight, Brain, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface EDAUpdate {
    status: 'info' | 'step' | 'thought' | 'success' | 'error';
    message: string;
    data: any;
}

export default function EDAProgress() {
    const location = useLocation();
    const navigate = useNavigate();
    const { connectionString, userComments, algorithmType, schemaAnalysis, mlObjective } = location.state || {};

    const [updates, setUpdates] = useState<EDAUpdate[]>([]);
    const [currentStep, setCurrentStep] = useState<string>('');
    const [suggestions, setSuggestions] = useState<any[]>([]);
    const [isComplete, setIsComplete] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>(algorithmType);
    const [edaSummary, setEdaSummary] = useState<string>('');
    const abortControllerRef = useRef<AbortController | null>(null);

    useEffect(() => {
        if (!connectionString) {
            navigate('/');
            return;
        }

        startEDA();

        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    const startEDA = async () => {
        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            await runAutomaticEDAStream(
                connectionString,
                userComments,
                algorithmType,
                (update: EDAUpdate) => {
                    if (update.status === 'step') {
                        setCurrentStep(update.message);
                    }
                    if (update.status === 'thought') {
                        setUpdates(prev => [...prev, update]);
                    }
                    if (update.status === 'success') {
                        setIsComplete(true);
                        setSuggestions(update.data.suggestions || []);
                        setEdaSummary(update.data.eda_summary || '');
                    }
                    if (update.status === 'error') {
                        setError(update.message);
                    }
                },
                controller.signal,
                mlObjective
            );
        } catch (err: any) {
            if (err.name !== 'AbortError') {
                setError(err.message || 'EDA failed');
            }
        }
    };

    const handleProceed = () => {
        navigate('/results', {
            state: {
                schemaAnalysis,
                connectionString,
                algorithmType: selectedAlgorithm,
                edaSummary,
                mlObjective
            }
        });
    };

    return (
        <div className="min-h-screen bg-slate-900 text-white p-6 md:p-12 flex flex-col items-center">
            <div className="w-full max-w-4xl space-y-8">

                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-500/20 rounded-2xl border border-indigo-500/30">
                            <Brain className="h-8 w-8 text-indigo-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                                AI Agent EDA Progress
                            </h1>
                            <p className="text-slate-400">
                                The AI is exploring your data to find patterns and suggest optimizations.
                            </p>
                        </div>
                    </div>
                    {isComplete ? (
                        <div className="flex items-center gap-2 text-emerald-400 font-medium">
                            <CheckCircle className="h-5 w-5" />
                            Complete
                        </div>
                    ) : (
                        <div className="flex items-center gap-3 text-cyan-400 font-medium bg-cyan-500/10 px-4 py-2 rounded-full border border-cyan-500/20">
                            <Loader className="h-4 w-4 animate-spin" />
                            {currentStep || 'Initializing...'}
                        </div>
                    )}
                </div>

                {/* Main Progress Area */}
                <div className="space-y-6">
                    {updates.map((update, idx) => (
                        <div key={idx} className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden backdrop-blur-sm shadow-xl">
                                <div className="bg-slate-800/80 px-6 py-3 border-b border-slate-700/50 flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-indigo-300 font-medium">
                                        <MessageSquare className="h-4 w-4" />
                                        AI Self-Questioning
                                    </div>
                                    <span className="text-xs text-slate-500 font-mono italic">#{idx + 1}</span>
                                </div>
                                <div className="p-6 space-y-6">
                                    {/* AI Thoughts/Questions */}
                                    <div className="space-y-3">
                                        {update.data.thought.map((q: string, i: number) => (
                                            <div key={i} className="flex gap-4 items-start group">
                                                <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-500 group-hover:scale-150 transition-transform" />
                                                <p className="text-slate-200 text-lg italic leading-relaxed font-light">
                                                    "{q}"
                                                </p>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Findings Context */}
                                    {update.data.results && (
                                        <div className="flex gap-4 items-start mt-4 pt-4 border-t border-slate-700/50">
                                            <div className="p-2 bg-emerald-500/10 rounded-lg shrink-0">
                                                <Lightbulb className="h-5 w-5 text-emerald-400" />
                                            </div>
                                            <div className="prose prose-invert prose-sm max-w-none">
                                                <ReactMarkdown>{update.data.results}</ReactMarkdown>
                                            </div>
                                        </div>
                                    )}

                                    {/* Visualizations */}
                                    {update.data.visualization && (
                                        <div className="mt-6 rounded-xl overflow-hidden border border-slate-700/50 bg-slate-900/50 p-2">
                                            <img
                                                src={`data:image/png;base64,${update.data.visualization}`}
                                                alt="EDA Visualization"
                                                className="w-full h-auto rounded-lg"
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Suggestions Block */}
                {isComplete && suggestions.length > 0 && (
                    <div className="animate-in zoom-in-95 duration-700 delay-300">
                        <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-8 space-y-6">
                            <div className="flex items-center gap-3">
                                <Lightbulb className="h-6 w-6 text-emerald-400" />
                                <h2 className="text-xl font-bold text-white">Suggested Alternative Models</h2>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {suggestions.map((s, i) => (
                                    <div
                                        key={i}
                                        onClick={() => setSelectedAlgorithm(s.name)}
                                        className={`p-5 rounded-xl transition-all cursor-pointer group border-2 ${selectedAlgorithm === s.name
                                            ? 'bg-emerald-500/20 border-emerald-500 shadow-lg shadow-emerald-500/10'
                                            : 'bg-slate-900/50 border-slate-700 hover:border-emerald-500/50'
                                            }`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="font-bold text-emerald-400 group-hover:translate-x-1 transition-transform">
                                                {s.display_name || s.name}
                                            </h3>
                                            {selectedAlgorithm === s.name && (
                                                <CheckCircle className="h-5 w-5 text-emerald-400 animate-in zoom-in duration-300" />
                                            )}
                                        </div>
                                        <p className="text-sm text-slate-400 leading-relaxed">{s.reason}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="p-6 bg-red-900/20 border border-red-500/50 rounded-2xl flex items-center gap-4 text-red-200">
                        <AlertCircle className="h-6 w-6 shrink-0" />
                        <div>
                            <h3 className="font-bold">Analysis Partial Failure</h3>
                            <p className="text-sm opacity-80">{error}</p>
                        </div>
                    </div>
                )}

                {/* Footer Actions */}
                <div className="flex justify-end pt-8 border-t border-slate-800">
                    <button
                        onClick={handleProceed}
                        className={`px-10 py-4 rounded-2xl font-bold flex items-center gap-3 transition-all shadow-xl group ${isComplete
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-emerald-500/20'
                            : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                            }`}
                        disabled={!isComplete}
                    >
                        {isComplete ? `Run ${selectedAlgorithm.replace('_', ' ')}` : 'Analyzing Data...'}
                        <ArrowRight className={`h-5 w-5 transition-transform ${isComplete ? 'group-hover:translate-x-1' : ''}`} />
                    </button>
                </div>
            </div>
        </div>
    );
}
