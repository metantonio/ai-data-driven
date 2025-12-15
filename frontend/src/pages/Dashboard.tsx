import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, ArrowRight, Loader, Settings } from 'lucide-react';
import { analyzeSchema, getSchema } from '../api/client';

export default function Dashboard() {
    const [connectionString, setConnectionString] = useState('');
    const [algorithmType, setAlgorithmType] = useState('linear_regression');
    const [advancedAnalysis, setAdvancedAnalysis] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleAnalyze = async () => {
        setLoading(true);
        setError(null);
        try {
            let dbString = connectionString.trim();
            // Automatically add sqlite protocol if user just enters a filename like 'example.db'
            if (!dbString.includes('://') && (dbString.endsWith('.db') || dbString.endsWith('.sqlite'))) {
                // Assume it's a relative path to the backend, so we might need ../ prefix if running from nested dir
                // But for simplicity in UI, we just prepend sqlite:///. 
                // The user might need to adjust relative paths.
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
        <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-2xl text-center space-y-8">
                <div className="space-y-2">
                    <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                        QLX AI Powered ML System
                    </h1>
                    <p className="text-slate-400 text-lg">
                        Connect your database and let AI build your ML pipeline.
                    </p>
                </div>

                <div className="bg-slate-800 p-8 rounded-2xl shadow-xl border border-slate-700/50 backdrop-blur-sm">
                    <div className="space-y-6">
                        <div className="text-left space-y-2">
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
                            </select>
                        </div>

                        <div className="text-left space-y-2">
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

                        <p className="text-xs text-slate-500">
                            Supports PostgreSQL, SQLite, MySQL, and more via SQLAlchemy.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
