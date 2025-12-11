import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { adaptCode, executeCode, generateInsights, SchemaAnalysis, ExecutionReport } from '../api/client';
import { Code, Play, FileText, CheckCircle, AlertTriangle, Loader, ChevronLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css'; // Import highlight.js styles

export default function Results() {
    const { state } = useLocation();
    const navigate = useNavigate();
    const schemaAnalysis = state?.schemaAnalysis as SchemaAnalysis;

    // State
    const [stage, setStage] = useState<'adapt' | 'execute' | 'insight' | 'done'>('adapt');
    const [adaptedCode, setAdaptedCode] = useState<string>('');
    const [executionResult, setExecutionResult] = useState<{ stdout: string; stderr: string; report: ExecutionReport | null } | null>(null);
    const [insights, setInsights] = useState<string>('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!schemaAnalysis) {
            navigate('/');
            return;
        }
        runPipeline();
    }, [schemaAnalysis]);

    const runPipeline = async () => {
        try {
            // 1. Adapt Code
            setStage('adapt');
            const adaptRes = await adaptCode(schemaAnalysis);
            setAdaptedCode(adaptRes.code);

            // 2. Execute Code
            setStage('execute');
            const execRes = await executeCode(adaptRes.code);
            setExecutionResult(execRes);

            if (execRes.report) {
                // 3. Generate Insights
                setStage('insight');
                const insightRes = await generateInsights(execRes.report, schemaAnalysis);
                setInsights(insightRes.insights);
                setStage('done');
            } else {
                setError('Execution failed to produce a structured report. Check stderr.');
                setStage('done'); // Stop here but marked as done with error
            }

        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Pipeline failed');
        }
    };

    if (!schemaAnalysis) return null;

    return (
        <div className="min-h-screen bg-slate-900 text-slate-50 p-6 md:p-12">
            <div className="max-w-6xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex items-center gap-4 border-b border-slate-700/50 pb-6">
                    <button onClick={() => navigate('/')} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                        <ChevronLeft className="h-6 w-6 text-slate-400" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold">Pipeline Results</h1>
                        <p className="text-slate-400 flex items-center gap-2">
                            {stage === 'done' ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Loader className="h-4 w-4 animate-spin text-cyan-500" />}
                            {stage === 'adapt' && 'Adapting code template...'}
                            {stage === 'execute' && 'Executing ML pipeline...'}
                            {stage === 'insight' && 'Generating AI insights...'}
                            {stage === 'done' && 'Pipeline execution complete'}
                        </p>
                    </div>
                </div>

                {error && (
                    <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-xl flex items-start gap-3">
                        <AlertTriangle className="h-6 w-6 text-red-400 mt-0.5" />
                        <div>
                            <h3 className="font-bold text-red-200">Processing Error</h3>
                            <p className="text-red-300/80 text-sm mt-1">{error}</p>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                    {/* Left Column: Code & Execution Logs */}
                    <div className="space-y-8">
                        {/* Code Block */}
                        <div className={`space-y-4 transition-all duration-500 ${adaptedCode ? 'opacity-100 translate-y-0' : 'opacity-50 translate-y-4'}`}>
                            <div className="flex items-center gap-2 text-cyan-400">
                                <Code className="h-5 w-5" />
                                <h2 className="font-semibold text-lg">Adapted ML Code</h2>
                            </div>
                            <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-xs md:text-sm text-slate-300 overflow-x-auto h-96 custom-scrollbar">
                                <pre>{adaptedCode || 'Waiting for adaptation...'}</pre>
                            </div>
                        </div>

                        {/* Execution Logs */}
                        <div className={`space-y-4 transition-all duration-500 delay-100 ${executionResult ? 'opacity-100 translate-y-0' : 'opacity-50 translate-y-4'}`}>
                            <div className="flex items-center gap-2 text-purple-400">
                                <Play className="h-5 w-5" />
                                <h2 className="font-semibold text-lg">Execution Output</h2>
                            </div>
                            <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-xs md:text-sm text-slate-300 overflow-x-auto h-48 custom-scrollbar">
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

                    {/* Right Column: Insights & Metrics */}
                    <div className="space-y-8">
                        {/* Metrics Card */}
                        {executionResult?.report && (
                            <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 p-6 rounded-2xl shadow-lg space-y-6">
                                <h2 className="text-lg font-semibold text-slate-200 border-b border-slate-700/50 pb-2">Model Metrics</h2>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                                        <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">MSE</div>
                                        <div className="text-2xl font-bold text-white">{executionResult.report.metrics.mse.toFixed(4)}</div>
                                    </div>
                                    <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                                        <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">R2 Score</div>
                                        <div className="text-2xl font-bold text-emerald-400">{executionResult.report.metrics.r2.toFixed(4)}</div>
                                    </div>
                                </div>
                                <div className="text-sm text-slate-400 flex flex-wrap gap-2">
                                    <span className="bg-slate-950 px-2 py-1 rounded text-slate-300">Target: {executionResult.report.target}</span>
                                    <span className="bg-slate-950 px-2 py-1 rounded text-slate-300">Features: {executionResult.report.features.length}</span>
                                </div>
                            </div>
                        )}

                        {/* Insights Panel */}
                        <div className={`space-y-4 transition-all duration-500 delay-200 ${insights ? 'opacity-100 translate-y-0' : 'opacity-50 translate-y-4'}`}>
                            <div className="flex items-center gap-2 text-yellow-400">
                                <FileText className="h-5 w-5" />
                                <h2 className="font-semibold text-lg">AI-Generated Insights</h2>
                            </div>
                            <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6 text-slate-200 leading-relaxed shadow-lg">
                                <div className="prose prose-invert max-w-none">
                                    {insights ? (
                                        <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                                            {insights}
                                        </ReactMarkdown>
                                    ) : (
                                        <div className="flex items-center gap-2 text-slate-500 italic">
                                            {stage === 'insight' ? <Loader className="animate-spin h-4 w-4" /> : null}
                                            Waiting for report generation...
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

            </div>
        </div>
    );
}
