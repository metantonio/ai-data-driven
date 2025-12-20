import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, ArrowRight, Loader, Settings, HelpCircle, Copy, Check, ExternalLink, Sparkles, ChevronRight } from 'lucide-react';
import { analyzeSchema, getSchema } from '../api/client';
import { Stepper } from '../components/Stepper';

function ConnectionGuide({ onSelect }: { onSelect: (val: string) => void }) {
    const [copied, setCopied] = useState<string | null>(null);

    const examples = [
        { label: 'SQLite (example)', value: 'sqlite:///../example.db', desc: 'Relative path to root project directory.' },
        { label: 'SQLite (example)', value: 'C:/Repositories/ai-data-driven/example.db', desc: 'Absolute path to root project directory.' },
        { label: 'SQLite Casino', value: 'sqlite:///../example_casino.db', desc: 'Sample casino dataset.' },
        { label: 'SAP HANA', value: 'hana://user:password@host:port', desc: 'Port is usually 3xx15 (xx=instance).' },
        { label: 'PostgreSQL', value: 'postgresql://user:password@host:port/dbname', desc: 'Standard PostgreSQL connection.' },
        { label: 'MySQL / MariaDB', value: 'mysql+pymysql://user:password@host:3306/dbname', desc: 'Uses pymysql driver (standard port 3306).' },
        { label: 'AWS RDS (Postgres)', value: 'postgresql://user:password@mydb.cabc123.us-east-1.rds.amazonaws.com:5432/dbname', desc: 'AWS RDS endpoint with standard port 5432.' },
        { label: 'AWS RDS (MySQL)', value: 'mysql+pymysql://user:password@mydb.cabc123.us-east-1.rds.amazonaws.com:3306/dbname', desc: 'AWS RDS endpoint with standard port 3306.' },
    ];

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(text);
        setTimeout(() => setCopied(null), 2000);
    };

    return (
        <div className="bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/50 rounded-2xl p-6 text-left space-y-4 animate-in fade-in slide-in-from-right-4 duration-300 shadow-xl">
            <div className="flex items-center gap-2 text-cyan-500 mb-2">
                <HelpCircle className="h-5 w-5" />
                <h3 className="font-bold text-lg">Connection Guide</h3>
            </div>
            <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
                Connect your database using SQLAlchemy compatible strings. Here are some examples:
            </p>
            <div className="space-y-3">
                {examples.map((ex) => (
                    <div key={ex.value} className="group relative bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700/50 rounded-xl p-3 hover:border-cyan-500/50 transition-all">
                        <div className="flex justify-between items-start mb-1">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{ex.label}</span>
                            <div className="flex gap-1">
                                <button
                                    onClick={() => copyToClipboard(ex.value)}
                                    className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors"
                                    title="Copy to clipboard"
                                >
                                    {copied === ex.value ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5 text-slate-400" />}
                                </button>
                                <button
                                    onClick={() => onSelect(ex.value)}
                                    className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors"
                                    title="Use this example"
                                >
                                    <ExternalLink className="h-3.5 w-3.5 text-cyan-500" />
                                </button>
                            </div>
                        </div>
                        <div className="font-mono text-xs text-slate-600 dark:text-slate-300 break-all mb-1">{ex.value}</div>
                        <div className="text-[10px] text-slate-400 italic">{ex.desc}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default function Dashboard() {
    const [connectionString, setConnectionString] = useState('');
    const [algorithmType, setAlgorithmType] = useState('linear_regression');
    const [advancedAnalysis, setAdvancedAnalysis] = useState(false);
    const [showGuide, setShowGuide] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleAnalyze = async () => {
        setLoading(true);
        setError(null);
        try {
            let dbString = connectionString.trim();
            if (!dbString.includes('://') && (dbString.endsWith('.db') || dbString.endsWith('.sqlite'))) {
                dbString = `sqlite:///${dbString}`;
            }

            if (advancedAnalysis) {
                const schema = await getSchema(dbString);
                navigate('/advanced-analysis', { state: { schema, connectionString: dbString, algorithmType } });
            } else {
                const data = await analyzeSchema(dbString, algorithmType);
                navigate('/results', { state: { schemaAnalysis: data, connectionString: dbString, algorithmType } });
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to analyze schema');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center p-6 space-y-6 text-slate-900 dark:text-slate-50">
            <Stepper currentStep="connect" />

            <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-5 gap-12 items-center text-left">

                <div className="lg:col-span-3 space-y-8">
                    <div className="space-y-4">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-600 dark:text-cyan-400 text-xs font-bold uppercase tracking-widest">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                            </span>
                            QLX AI-Powered Data Science
                        </div>
                        <h1 className="text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
                            Build ML Pipelines <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-blue-600 dark:from-cyan-400 dark:to-blue-500">
                                Directly from your DB
                            </span>
                        </h1>
                        <p className="text-lg text-slate-500 dark:text-slate-400 max-w-xl leading-relaxed">
                            Connect your PostgreSQL, SQLite, or SAP HANA database and let our AI agents handle the rest.
                        </p>
                    </div>

                    <div className="bg-white dark:bg-slate-800/80 p-8 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-700/50 backdrop-blur-md relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 flex gap-2">
                            <button
                                onClick={() => setShowGuide(!showGuide)}
                                className={`p-2 rounded-xl transition-all ${showGuide ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/20' : 'bg-slate-100 dark:bg-slate-900/50 text-slate-400 hover:text-cyan-500 dark:hover:text-white hover:bg-white dark:hover:bg-slate-700'}`}
                                title="Connection Guide"
                            >
                                <HelpCircle className="h-6 w-6" />
                            </button>
                            <button
                                onClick={() => navigate('/settings')}
                                className="p-2 bg-slate-100 dark:bg-slate-900/50 text-slate-400 hover:text-cyan-500 dark:hover:text-white hover:bg-white dark:hover:bg-slate-700 rounded-xl transition-all"
                                title="System Settings"
                            >
                                <Settings className="h-6 w-6" />
                            </button>
                            <button
                                onClick={() => navigate('/registry')}
                                className="p-2 bg-slate-100 dark:bg-slate-900/50 text-slate-400 hover:text-cyan-500 dark:hover:text-white hover:bg-white dark:hover:bg-slate-700 rounded-xl transition-all"
                                title="Model Registry"
                            >
                                <Database className="h-6 w-6" />
                            </button>
                        </div>

                        <div className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] uppercase font-black text-slate-400 tracking-widest ml-1">Analysis Type</label>
                                <div className="relative">
                                    <select
                                        value={algorithmType}
                                        onChange={(e) => setAlgorithmType(e.target.value)}
                                        className="w-full pl-4 pr-10 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-900 dark:text-slate-100 transition-all text-sm appearance-none"
                                    >
                                        <option value="linear_regression">Linear Regression</option>
                                        <option value="logistic_regression">Logistic Regression (Classification)</option>
                                        <option value="random_forest">Random Forest Classifier</option>
                                        <option value="decision_tree">Decision Tree</option>
                                        <option value="clustering_kmeans">K-Means Clustering</option>
                                        <option value="time_series">Time Series Forecasting</option>
                                        <option value="auto_ml">AutoML Pilot (Multi-algorithm Search)</option>
                                    </select>
                                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                                        <ChevronRight className="h-4 w-4 rotate-90" />
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] uppercase font-black text-slate-400 tracking-widest ml-1">Database Connection String</label>
                                <div className="relative group/input">
                                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within/input:text-cyan-500 transition-colors">
                                        <Database className="h-5 w-5" />
                                    </div>
                                    <input
                                        type="text"
                                        value={connectionString}
                                        onChange={(e) => setConnectionString(e.target.value)}
                                        placeholder="sqlite:///database.db or postgresql://..."
                                        className="w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-600 transition-all font-mono text-sm"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-3 p-4 bg-cyan-500/5 dark:bg-cyan-500/10 rounded-2xl border border-cyan-500/20">
                                <input
                                    type="checkbox"
                                    id="advanced"
                                    checked={advancedAnalysis}
                                    onChange={(e) => setAdvancedAnalysis(e.target.checked)}
                                    className="w-5 h-5 rounded-lg border-slate-300 text-cyan-500 focus:ring-cyan-500 transition-all"
                                />
                                <label htmlFor="advanced" className="text-sm font-medium cursor-pointer">
                                    <div className="font-bold flex items-center gap-1">
                                        <Sparkles className="h-3.5 w-3.5 text-cyan-500" />
                                        Advanced Analysis
                                    </div>
                                    <div className="text-[10px] text-slate-500 dark:text-slate-400">Manually annotate columns to improve AI Context</div>
                                </label>
                            </div>

                            {error && (
                                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500 text-xs font-medium animate-in zoom-in-95">
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleAnalyze}
                                disabled={loading || !connectionString}
                                className="w-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold py-4 rounded-2xl shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-3 group"
                            >
                                {loading ? (
                                    <>
                                        <Loader className="animate-spin h-5 w-5" />
                                        <span>Analyzing Data...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Analyze Database</span>
                                        <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                    <div className="text-center">
                        <p className="text-[10px] text-slate-400 font-medium uppercase tracking-widest">
                            Supports PostgreSQL, SQLite, MySQL, and more via SQLAlchemy.
                        </p>
                    </div>
                </div>

                <div className="lg:col-span-2">
                    {showGuide ? (
                        <ConnectionGuide onSelect={(val) => setConnectionString(val)} />
                    ) : (
                        <div className="bg-slate-50 dark:bg-slate-900/30 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl p-12 flex flex-col items-center justify-center text-center space-y-4 group hover:border-cyan-500/50 transition-colors duration-500">
                            <div className="w-20 h-20 bg-white dark:bg-slate-800 rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-500">
                                <HelpCircle className="h-10 w-10 text-slate-300 group-hover:text-cyan-500 transition-colors" />
                            </div>
                            <div className="space-y-2">
                                <h3 className="font-bold text-slate-400 group-hover:text-slate-300">Need help with connection strings?</h3>
                                <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
                                    Click the help icon or button to see common examples for different databases.
                                </p>
                            </div>
                            <button
                                onClick={() => setShowGuide(true)}
                                className="px-6 py-2 bg-white dark:bg-slate-800 text-slate-400 dark:text-slate-300 text-xs font-bold rounded-full border border-slate-200 dark:border-slate-700 hover:border-cyan-500/50 hover:text-cyan-500 transition-all shadow-md"
                            >
                                Open Connection Guide
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
