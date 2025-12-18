import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, ArrowRight, Loader, Settings, HelpCircle, Copy, Check, ExternalLink } from 'lucide-react';
import { analyzeSchema, getSchema } from '../api/client';

function ConnectionGuide({ onSelect }: { onSelect: (val: string) => void }) {
    const [copied, setCopied] = useState<string | null>(null);

    const examples = [
        { label: 'SQLite (Default)', value: 'sqlite:///../example.db', desc: 'Relative path to root project directory.' },
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
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 text-left space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="flex items-center gap-2 text-cyan-400 mb-2">
                <HelpCircle className="h-5 w-5" />
                <h3 className="font-bold text-lg">Connection Guide</h3>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed">
                Connect your database using SQLAlchemy compatible strings. Here are some examples from the documentation:
            </p>
            <div className="space-y-3">
                {examples.map((ex) => (
                    <div key={ex.value} className="group relative bg-slate-900/50 border border-slate-700/50 rounded-xl p-3 hover:border-cyan-500/50 transition-all">
                        <div className="flex justify-between items-start mb-1">
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{ex.label}</span>
                            <div className="flex gap-1">
                                <button
                                    onClick={() => copyToClipboard(ex.value)}
                                    className="p-1 hover:bg-slate-700 rounded transition-colors"
                                    title="Copy to clipboard"
                                >
                                    {copied === ex.value ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-slate-400" />}
                                </button>
                                <button
                                    onClick={() => onSelect(ex.value)}
                                    className="p-1 hover:bg-slate-700 rounded transition-colors"
                                    title="Use this example"
                                >
                                    <ExternalLink className="h-3.5 w-3.5 text-cyan-400" />
                                </button>
                            </div>
                        </div>
                        <div className="font-mono text-xs text-slate-300 break-all mb-1">{ex.value}</div>
                        <div className="text-[10px] text-slate-500 italic">{ex.desc}</div>
                    </div>
                ))}
            </div>
            <div className="pt-2 border-t border-slate-700/50">
                <p className="text-[10px] text-slate-500">
                    Note: For SQLite, if you enter a filename like <code className="text-slate-400">example.db</code>,
                    the system will automatically prepend <code className="text-slate-400">sqlite:///</code>.
                </p>
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
        <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6 space-y-12">
            <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-5 gap-12 items-center text-left">

                {/* Left Side: Hero & Form */}
                <div className="lg:col-span-3 space-y-8 animate-in fade-in slide-in-from-left-8 duration-700">
                    <div className="space-y-4">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-cyan-400 text-xs font-bold tracking-widest uppercase">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                            </span>
                            QLX AI-Powered Data Science
                        </div>
                        <h1 className="text-5xl font-extrabold text-white tracking-tight leading-tight">
                            Build ML Pipelines <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                                Directly from your DB
                            </span>
                        </h1>
                        <p className="text-slate-400 text-xl max-w-xl">
                            Connect your PostgreSQL, SQLite, or SAP HANA database and let our AI agents handle the rest.
                        </p>
                    </div>

                    <div className="bg-slate-800/80 p-8 rounded-3xl shadow-2xl border border-slate-700/50 backdrop-blur-md relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4">
                            <button
                                onClick={() => setShowGuide(!showGuide)}
                                className={`p-2 rounded-xl transition-all ${showGuide ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/20' : 'bg-slate-900/50 text-slate-400 hover:text-white hover:bg-slate-700'}`}
                                title="Connection Guide"
                            >
                                <HelpCircle className="h-6 w-6" />
                            </button>
                        </div>

                        <div className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300 ml-1">Analysis Type</label>
                                <select
                                    value={algorithmType}
                                    onChange={(e) => setAlgorithmType(e.target.value)}
                                    className="w-full pl-4 pr-10 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 transition-all text-sm appearance-none"
                                >
                                    <option value="linear_regression">Linear Regression</option>
                                    <option value="logistic_regression">Logistic Regression (Classification)</option>
                                    <option value="kmeans">K-Means Clustering</option>
                                    <option value="hierarchical">Hierarchical Clustering</option>
                                    <option value="time_series">Time Series Forecasting</option>
                                    <option value="association_rules">Association Rules (Market Basket)</option>
                                    <option value="reinforcement_learning">Reinforcement Learning</option>
                                    <option value="linear_programming">Linear Programming (Optimization)</option>
                                    <option value="mixed_integer_programming">Mixed Integer Programming</option>
                                    <option value="random_forest">Random Forest</option>
                                    <option value="decision_tree">Decision Tree</option>
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300 ml-1">Database Connection String</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Database className="h-5 w-5 text-slate-500" />
                                    </div>
                                    <input
                                        type="text"
                                        value={connectionString}
                                        onChange={(e) => setConnectionString(e.target.value)}
                                        placeholder="sqlite:///database.db or postgresql://..."
                                        className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 placeholder-slate-600 transition-all font-mono text-sm"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-3 bg-slate-900/30 p-3 rounded-xl border border-slate-700/50">
                                <div className="relative flex items-center">
                                    <input
                                        type="checkbox"
                                        id="advancedAnalysis"
                                        checked={advancedAnalysis}
                                        onChange={(e) => setAdvancedAnalysis(e.target.checked)}
                                        className="peer h-5 w-5 cursor-pointer appearance-none rounded-md border border-slate-600 bg-slate-900/50 transition-all checked:border-cyan-500 checked:bg-cyan-500 hover:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20"
                                    />
                                    <div className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-0 peer-checked:opacity-100">
                                        <ArrowRight className="h-3 w-3 text-white" />
                                    </div>
                                </div>
                                <label htmlFor="advancedAnalysis" className="flex-1 cursor-pointer select-none">
                                    <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                                        <Settings className="h-4 w-4 text-cyan-400" />
                                        Advanced Analysis
                                    </div>
                                    <p className="text-xs text-slate-500 mt-0.5">
                                        Manually annotation columns to improve AI Context
                                    </p>
                                </label>
                            </div>

                            {error && (
                                <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg text-red-200 text-sm text-left">
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleAnalyze}
                                disabled={loading || !connectionString}
                                className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg ${loading || !connectionString
                                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                    : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-cyan-500/20 hover:shadow-cyan-500/40 transform hover:-translate-y-0.5'
                                    }`}
                            >
                                {loading ? (
                                    <>
                                        <Loader className="animate-spin h-5 w-5" />
                                        Analyzing Schema...
                                    </>
                                ) : (
                                    <>
                                        Analyze Database
                                        <ArrowRight className="h-5 w-5" />
                                    </>
                                )}
                            </button>

                            <p className="text-xs text-slate-500 text-center">
                                Supports PostgreSQL, SQLite, MySQL, and more via SQLAlchemy.
                            </p>

                            <div className="pt-4 border-t border-slate-700/50 text-center">
                                <button
                                    onClick={() => navigate('/eda')}
                                    className="text-cyan-400 hover:text-cyan-300 text-sm font-medium flex items-center justify-center gap-2 mx-auto transition-colors"
                                >
                                    <Database className="h-4 w-4" />
                                    Try the New EDA Copilot
                                    <ArrowRight className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side: Connection Guide (Conditional) */}
                <div className={`lg:col-span-2 transition-all duration-500 ${showGuide ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-12 pointer-events-none lg:block lg:opacity-30'}`}>
                    {showGuide ? (
                        <ConnectionGuide onSelect={(val) => {
                            setConnectionString(val);
                        }} />
                    ) : (
                        <div className="hidden lg:flex flex-col items-center justify-center h-full text-slate-600 border-2 border-dashed border-slate-800 rounded-3xl p-12 text-center space-y-4">
                            <div className="p-4 bg-slate-800/30 rounded-full">
                                <HelpCircle className="h-12 w-12" />
                            </div>
                            <p className="text-sm font-medium">Need help with connection strings?</p>
                            <button
                                onClick={() => setShowGuide(true)}
                                className="px-6 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 transition-all text-sm"
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
