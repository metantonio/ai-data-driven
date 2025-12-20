import React, { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { adaptCode, executeCodeStream, generateInsights, ExecutionReport, predict } from '../api/client';
import { ChevronLeft, CheckCircle, Loader, AlertTriangle, Code, Download, Play, BarChart2, FileText, Calculator, Copy, Check } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { Stepper } from '../components/Stepper';

function PredictionForm({ modelPath, features }: { modelPath: string, features: string[] }) {
    const [formData, setFormData] = useState<Record<string, string>>({});
    const [prediction, setPrediction] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setPrediction(null);

        try {
            const formattedData: any = {};
            for (const key of features) {
                const val = formData[key];
                if (!isNaN(Number(val)) && val !== '') {
                    formattedData[key] = Number(val);
                } else {
                    formattedData[key] = val;
                }
            }

            const res = await predict(modelPath, formattedData);
            setPrediction(res.prediction);
        } catch (err: any) {
            setError(err.message || 'Prediction failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative group overflow-hidden bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-700/50 rounded-2xl p-8 shadow-2xl mt-8">
            {/* Ambient Background Effect */}
            <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl group-hover:bg-purple-500/20 transition-all duration-1000"></div>

            <div className="relative z-10">
                <div className="flex items-center gap-3 mb-8 border-b border-slate-800 pb-4">
                    <div className="p-2.5 bg-purple-500/10 rounded-xl border border-purple-500/20">
                        <Calculator className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-white tracking-tight">Interactive Prediction</h3>
                        <p className="text-slate-400 text-sm">Test the model with custom inputs</p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {features.map((feature) => (
                            <div key={feature} className="space-y-2">
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider ml-1">
                                    {feature.replace(/_/g, ' ')}
                                </label>
                                <input
                                    type="text"
                                    className="w-full bg-slate-950/50 border border-slate-700/50 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all font-mono text-sm"
                                    placeholder={`Enter ${feature}...`}
                                    value={formData[feature] || ''}
                                    onChange={(e) => setFormData({ ...formData, [feature]: e.target.value })}
                                    required
                                />
                            </div>
                        ))}
                    </div>

                    <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col md:flex-row items-center gap-6">
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full md:w-auto bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:from-slate-700 disabled:to-slate-800 text-white px-8 py-3.5 rounded-xl font-semibold shadow-lg shadow-purple-900/20 transition-all transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2 min-w-[160px]"
                        >
                            {loading ? (
                                <>
                                    <Loader className="w-4 h-4 animate-spin" />
                                    <span>Calculating...</span>
                                </>
                            ) : (
                                <>
                                    <Play className="w-4 h-4 fill-current" />
                                    <span>Generate Prediction</span>
                                </>
                            )}
                        </button>

                        {prediction !== null && (
                            <div className="flex-1 w-full flex items-center justify-center md:justify-end">
                                <div className="flex items-center gap-4 bg-emerald-500/10 border border-emerald-500/20 px-6 py-3 rounded-xl animate-in fade-in slide-in-from-left-4 duration-500">
                                    <span className="text-emerald-400 font-medium text-sm uppercase tracking-wider">Result:</span>
                                    <span className="text-2xl font-bold text-white font-mono tracking-tight">
                                        {typeof prediction === 'number' ? prediction.toLocaleString(undefined, { maximumFractionDigits: 4 }) : prediction}
                                    </span>
                                </div>
                            </div>
                        )}

                        {error && (
                            <div className="flex-1 w-full text-center md:text-right text-red-400 text-sm animate-in fade-in">
                                Error: {error}
                            </div>
                        )}
                    </div>
                </form>
            </div>
        </div>
    );
}

function CopyButton({ text, label }: { text: string, label?: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    };

    return (
        <button
            onClick={handleCopy}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all text-xs font-semibold border ${copied
                ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-700 hover:text-white'
                } `}
        >
            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            {label && <span>{copied ? 'Copied!' : label}</span>}
        </button>
    );
}

export default function Results() {
    const location = useLocation();
    const navigate = useNavigate();
    const { schemaAnalysis, algorithmType, edaSummary, mlObjective } = location.state || {};

    // State
    const [stage, setStage] = useState<'adapt' | 'execute' | 'insight' | 'done'>('adapt');
    const [streamStatus, setStreamStatus] = useState<string>('');
    const [adaptedCode, setAdaptedCode] = useState<string>('');
    const [executionResult, setExecutionResult] = useState<{ stdout: string; stderr: string; report: ExecutionReport | null } | null>(null);
    const [insights, setInsights] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [aiErrorSummary, setAiErrorSummary] = useState<string | null>(null);
    const [latestCode, setLatestCode] = useState<string>('');

    // Ref for abort controller
    const abortControllerRef = useRef<AbortController | null>(null);

    useEffect(() => {
        if (!schemaAnalysis) {
            navigate('/');
            return;
        }

        const cachedResult = location.state?.executionResult;
        const cachedInsights = location.state?.insights;

        if (cachedResult) {
            setExecutionResult(cachedResult);
            if (cachedInsights) setInsights(cachedInsights);
            setStage('done');
            return;
        }

        runPipeline();

        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [schemaAnalysis, algorithmType]);

    const runPipeline = async (codeToRun?: string) => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            let code = codeToRun;

            if (!code) {
                setStage('adapt');
                const adaptRes = await adaptCode(schemaAnalysis, algorithmType, edaSummary, mlObjective);
                if (controller.signal.aborted) return;
                code = adaptRes.code;
            }

            setAdaptedCode(code!);
            setLatestCode(code!);
            setExecutionResult(null);
            setError(null);
            setAiErrorSummary(null);

            setStage('execute');

            let finalStateReached = false;

            await executeCodeStream(code!, schemaAnalysis, (update) => {
                if (controller.signal.aborted) return;

                if (update.status === 'info' || update.status === 'fixing') {
                    setStreamStatus(update.message);
                    if (update.data && update.data.code) {
                        setLatestCode(update.data.code);
                    }
                } else if (update.status === 'error') {
                    setStreamStatus(update.message);
                    if (update.data?.is_ai_summary) {
                        setAiErrorSummary(update.message);
                    }
                    if (update.data?.stderr) {
                        setExecutionResult(prev => ({
                            stdout: prev?.stdout || '',
                            stderr: update.data.stderr,
                            report: null
                        }));
                    }
                } else if (update.status === 'success') {
                    finalStateReached = true;
                    setAiErrorSummary(null); // Clear any intermediate error summary on success
                    setExecutionResult(update.data);
                    generateInsightsWrapper(update.data, schemaAnalysis);
                } else if (update.status === 'final_error') {
                    finalStateReached = true;
                    setError(update.message);
                    if (update.data?.error_summary) {
                        setAiErrorSummary(update.data.error_summary);
                    }
                    if (update.data && update.data.code) {
                        setLatestCode(update.data.code);
                    }
                    if (update.data && (update.data.stdout || update.data.stderr)) {
                        setExecutionResult({
                            stdout: update.data.stdout || '',
                            stderr: update.data.stderr || '',
                            report: null
                        });
                    }
                    setStage('done');
                }
            }, controller.signal);

            if (controller.signal.aborted) return;

            if (!finalStateReached) {
                setStage('done');
                if (!error) setError("Execution stream ended unexpectedly.");
            }

        } catch (err: any) {
            if (err.name === 'AbortError') return;
            setError(err.response?.data?.detail || err.message || 'Pipeline failed');
            setStage('done');
        } finally {
            if (abortControllerRef.current === controller) {
                abortControllerRef.current = null;
            }
        }
    };

    const handleRetry = () => {
        const codeToRetry = latestCode || adaptedCode;
        if (codeToRetry) {
            runPipeline(codeToRetry);
        } else {
            console.error("No code available to retry");
        }
    };

    const generateInsightsWrapper = async (execResult: any, analysis: any) => {
        if (execResult.report) {
            setStage('insight');
            const insightRes = await generateInsights(execResult.report, analysis, algorithmType, mlObjective);
            setInsights(insightRes.insights);
            setStage('done');

            navigate('.', {
                state: {
                    ...location.state,
                    executionResult: execResult,
                    insights: insightRes.insights
                },
                replace: true
            });
        } else {
            // Execution successful but no JSON report
            setStage('done');
        }
    };

    if (!schemaAnalysis) return null;

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50 p-6 md:p-12">
            <div className="max-w-6xl mx-auto mb-10">
                <Stepper currentStep="results" />
            </div>
            <div className="mx-auto space-y-8">

                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-700/50 pb-6 mb-8">
                    <div className="flex items-center gap-4">
                        <button onClick={() => navigate('/')} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                            <ChevronLeft className="h-6 w-6 text-slate-400" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-bold">Pipeline Results</h1>
                            <p className="text-slate-400 flex items-center gap-2">
                                {stage === 'done' ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Loader className="h-4 w-4 animate-spin text-cyan-500" />}
                                {stage === 'adapt' && 'Adapting code template...'}
                                {stage === 'execute' && (streamStatus || 'Executing ML pipeline...')}
                                {stage === 'insight' && 'Generating AI insights...'}
                                {stage === 'done' && 'Pipeline execution complete'}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="px-5 py-2 bg-slate-800/80 border border-slate-700/50 rounded-2xl flex flex-col items-end">
                            <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Target Algorithm</span>
                            <span className="text-sm font-bold text-cyan-400">{algorithmType?.replace('_', ' ').toUpperCase()}</span>
                        </div>
                    </div>
                </div>

                {(error || aiErrorSummary || (stage === 'done' && !executionResult?.report)) && (
                    <div className="p-6 bg-red-900/20 border border-red-500/50 rounded-2xl flex flex-col gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-red-500/20 rounded-xl">
                                <AlertTriangle className="h-6 w-6 text-red-400" />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-xl font-bold text-red-200">
                                    {!executionResult?.report && stage === 'done' && !error && !aiErrorSummary
                                        ? 'No valid execution report found'
                                        : error === 'Max retries reached. Execution failed.'
                                            ? 'Automated Fixing Failed'
                                            : 'Pipeline Execution Error'}
                                </h3>
                                <div className="mt-3 text-red-300/90 leading-relaxed bg-red-950/30 p-4 rounded-xl border border-red-500/10">
                                    {aiErrorSummary || error || 'The pipeline finished but did not produce a results report. Check the execution logs for details.'}
                                </div>

                                {error && aiErrorSummary && error !== aiErrorSummary && (
                                    <p className="text-red-400/60 text-xs mt-3 italic">
                                        System Status: {error}
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* Retry Button */}
                        {(stage === 'done' || error || aiErrorSummary) && !executionResult?.report && (
                            <div className="flex justify-end mt-2 pt-4 border-t border-red-500/10">
                                <button
                                    onClick={handleRetry}
                                    className="bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white px-8 py-4 rounded-xl font-bold shadow-lg shadow-red-900/40 transition-all transform hover:scale-[1.02] active:scale-[0.98] flex flex-col items-center gap-1"
                                >
                                    <div className="flex items-center gap-2">
                                        <Play className="h-4 w-4 fill-current" />
                                        <span>{stage === 'done' ? 'Manual Retry with AI Fix' : 'Stop & Force Manual Retry'}</span>
                                    </div>
                                    <span className="text-[10px] opacity-70 font-normal">
                                        {stage === 'done' ? 'Forces 3 additional automated fixing attempts' : 'Stops current attempt and starts fresh with 3 new fixes'}
                                    </span>
                                </button>
                            </div>
                        )}
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-7 gap-5 items-start">

                    {/* Left Column (1/4): Code & Execution Logs */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Code Block */}
                        <div className={`space-y-4 transition-all duration-500 ${latestCode ? 'opacity-100 translate-y-0' : 'opacity-50 translate-y-4'} `}>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-cyan-400">
                                    <Code className="h-5 w-5" />
                                    <h2 className="font-semibold text-lg">Adapted ML Code</h2>
                                </div>
                                <div className="flex items-center gap-2">
                                    <CopyButton text={latestCode} label="Copy" />
                                    <button
                                        onClick={() => {
                                            const blob = new Blob([latestCode], { type: 'text/plain' });
                                            const url = URL.createObjectURL(blob);
                                            const a = document.createElement('a');
                                            a.href = url;
                                            a.download = 'pipeline.py';
                                            a.click();
                                            URL.revokeObjectURL(url);
                                        }}
                                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700 text-slate-400 hover:bg-slate-700 hover:text-white text-xs font-semibold transition-all"
                                        title="Download .py file"
                                    >
                                        <Download className="w-3.5 h-3.5" />
                                        <span>Download</span>
                                    </button>
                                </div>
                            </div>
                            <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-xs md:text-sm text-slate-300 overflow-x-auto h-96 custom-scrollbar">
                                <pre>{latestCode || 'Waiting for adaptation...'}</pre>
                            </div>
                        </div>

                        {/* Execution Logs */}
                        <div className={`space-y-4 transition-all duration-500 delay-100 ${executionResult ? 'opacity-100 translate-y-0' : 'opacity-50 translate-y-4'} `}>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-purple-400">
                                    <Play className="h-5 w-5" />
                                    <h2 className="font-semibold text-lg">Execution Output</h2>
                                </div>
                                {executionResult && (
                                    <CopyButton
                                        text={`STDOUT:\n${executionResult.stdout}\n\nSTDERR:\n${executionResult.stderr}`}
                                        label="Copy Logs"
                                    />
                                )}
                            </div>
                            <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-xs md:text-sm text-slate-300 overflow-x-auto max-h-[280px] custom-scrollbar">
                                {executionResult ? (
                                    <>
                                        <div className="text-slate-500 mb-2">$ python pipeline.py</div>
                                        {executionResult.stdout && <div>{executionResult.stdout}</div>}
                                        {executionResult.stderr && <div className="text-red-400 mt-2">{executionResult.stderr}</div>}
                                    </>
                                ) : 'Waiting for execution...'}
                            </div>
                        </div>
                    </div>

                    {/* Middle Column (1/4): Metrics & Interactive Elements */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Metrics Card */}
                        {executionResult?.report && (
                            <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 p-6 rounded-2xl shadow-lg space-y-6">
                                <div className="flex items-center justify-between border-b border-slate-700/50 pb-2">
                                    <h2 className="text-lg font-semibold text-slate-200">Execution Report</h2>
                                    <div className="px-2 py-0.5 bg-indigo-500/20 text-indigo-300 text-[10px] font-bold uppercase rounded border border-indigo-500/30">
                                        {executionResult.report.model_type || 'Custom Model'}
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 gap-4">
                                    {executionResult.report.metrics && Object.entries(executionResult.report.metrics).map(([key, value]) => (
                                        <div key={key} className="bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                                            <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">{key.replace(/_/g, ' ')}</div>
                                            <div className="text-2xl font-bold text-white">
                                                {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : String(value)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="text-sm text-slate-400 flex flex-wrap gap-2 pt-2 border-t border-slate-800">
                                    <span className="bg-slate-950 px-2 py-1 rounded text-slate-300 border border-white/5">Target: {executionResult.report.target || 'N/A'}</span>
                                    <span className="bg-slate-950 px-2 py-1 rounded text-slate-300 border border-white/5">Features: {executionResult.report.features?.length || 0}</span>
                                </div>
                            </div>
                        )}

                        {/* Visualization Link */}
                        {executionResult?.report?.visualization_data && (
                            <button
                                onClick={() => navigate('/visualizations', { state: { report: executionResult.report, algorithmType } })}
                                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-4 rounded-xl shadow-lg transition-all"
                            >
                                <BarChart2 className="h-5 w-5" />
                                View Interactive Visualizations & Data
                            </button>
                        )}

                        {/* SHAP Importance Card */}
                        {executionResult?.report?.shap_importance && (
                            <div className="bg-white dark:bg-slate-800/80 p-6 rounded-3xl border border-slate-200 dark:border-slate-700/50 shadow-xl space-y-4">
                                <div className="flex items-center gap-2 text-cyan-500 mb-2">
                                    <BarChart2 className="h-5 w-5" />
                                    <h3 className="font-bold text-lg">Feature Importance (SHAP)</h3>
                                </div>
                                <div className="h-64 -ml-4">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart
                                            data={Object.entries(executionResult.report.shap_importance)
                                                .map(([name, value]) => ({ name, value }))
                                                .sort((a, b) => b.value - a.value)
                                                .slice(0, 10)}
                                            layout="vertical"
                                            margin={{ left: 20 }}
                                        >
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
                                            <Bar dataKey="value" radius={[0, 4, 4, 0]} fill="#06b6d4" />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                                <p className="text-[10px] text-slate-500 italic">This chart shows which features had the most impact on the model's predictions.</p>
                            </div>
                        )}

                        {/* Interactive Prediction Form */}
                        {executionResult?.report?.model_path && executionResult?.report?.features && (
                            <PredictionForm
                                modelPath={executionResult.report.model_path}
                                features={executionResult.report.features}
                            />
                        )}
                    </div>

                    {/* Right Column (2/4 = 1/2): Insights */}
                    <div className={`lg:col-span-3 transition-all duration-500 delay-200 ${insights ? 'opacity-100 translate-y-0' : 'opacity-50 translate-y-4'} `}>
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2 text-yellow-400">
                                <FileText className="h-6 w-6" />
                                <h2 className="font-semibold text-2xl">AI-Generated Insights</h2>
                            </div>
                            {insights && <CopyButton text={insights} label="Copy Report" />}
                        </div>
                        <div className="bg-slate-800/50 rounded-2xl border border-slate-700 p-8 text-slate-200 leading-relaxed shadow-xl backdrop-blur-sm max-h-[750px]" style={{ overflowY: 'auto' }}>
                            <div className="prose prose-invert prose-lg max-w-none">
                                {insights ? (
                                    <ReactMarkdown
                                        rehypePlugins={[rehypeHighlight]}
                                        components={{
                                            p: ({ node, ...props }) => <p className="mb-4 whitespace-pre-wrap" {...props} />
                                        }}
                                    >
                                        {insights}
                                    </ReactMarkdown>
                                ) : (
                                    <div className="flex flex-col items-center justify-center gap-4 py-8 text-slate-500 italic">
                                        {stage === 'insight' ? (
                                            <>
                                                <Loader className="animate-spin h-8 w-8 text-yellow-500" />
                                                <span>Analyzing results and generating insights...</span>
                                            </>
                                        ) : (
                                            <span>Waiting for report generation...</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div >
    );
}
