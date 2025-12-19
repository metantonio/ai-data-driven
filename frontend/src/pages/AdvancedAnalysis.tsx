import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Save, Database, Table, MessageSquare, Loader, Brain } from 'lucide-react';
import { analyzeSchemaWithComments } from '../api/client';

export default function AdvancedAnalysis() {
    const location = useLocation();
    const navigate = useNavigate();
    const { connectionString, algorithmType, schema } = location.state || {};

    // State for user comments: table -> column -> comment
    const [comments, setComments] = useState<Record<string, Record<string, string>>>({});
    const [selectedTables, setSelectedTables] = useState<string[]>(
        Object.keys(schema?.tables || {})
    );
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [mlObjective, setMlObjective] = useState('');

    if (!location.state) {
        return <div className="text-white p-10">Invalid State. Please return to Dashboard.</div>;
    }

    const handleCommentChange = (table: string, column: string, value: string) => {
        setComments(prev => ({
            ...prev,
            [table]: {
                ...prev[table],
                [column]: value
            }
        }));
    };

    const handleTableToggle = (tableName: string) => {
        setSelectedTables(prev =>
            prev.includes(tableName)
                ? prev.filter(t => t !== tableName)
                : [...prev, tableName]
        );
    };

    const handleAnalyze = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await analyzeSchemaWithComments(connectionString, comments, algorithmType, selectedTables, mlObjective);
            navigate('/eda-progress', {
                state: {
                    schemaAnalysis: data,
                    connectionString,
                    algorithmType,
                    userComments: comments,
                    mlObjective
                }
            });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to analyze schema');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-900 p-6 flex flex-col items-center">
            <div className="w-full max-w-6xl space-y-6">

                {/* Header */}
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Dashboard
                    </button>
                    <h1 className="text-2xl font-bold text-white">Advanced Analysis Configuration</h1>
                </div>

                {/* ML Objective Section */}
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-xl">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="p-3 bg-indigo-500/10 rounded-lg">
                            <Brain className="h-6 w-6 text-indigo-400" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Project Objective</h2>
                            <p className="text-slate-400 text-sm">Describe what you want to achieve. The AI will adapt the SQL and code to fit this goal.</p>
                        </div>
                    </div>
                    <div className="relative">
                        <MessageSquare className="absolute top-4 left-4 h-5 w-5 text-slate-500" />
                        <textarea
                            placeholder="e.g. 'Predict customer churn using transaction history and demographics', 'Identify high-value players in the last 30 days'..."
                            className="w-full bg-slate-900 border border-slate-700 rounded-xl py-3 pl-12 pr-4 text-slate-200 placeholder-slate-600 focus:ring-2 focus:ring-indigo-500 outline-none transition-all min-h-[100px]"
                            value={mlObjective}
                            onChange={(e) => setMlObjective(e.target.value)}
                        />
                    </div>
                </div>

                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-xl">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="p-3 bg-cyan-500/10 rounded-lg">
                            <Database className="h-6 w-6 text-cyan-400" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">Schema Annotation</h2>
                            <p className="text-slate-400 text-sm">Add context to your data to help the AI understand your schema better.</p>
                        </div>
                    </div>

                    <div className="space-y-8">
                        {Object.entries(schema?.tables || {}).map(([tableName, tableData]: [string, any]) => (
                            <div key={tableName} className={`bg-slate-900/50 rounded-lg overflow-hidden border border-slate-700/50 transition-all ${!selectedTables.includes(tableName) ? 'opacity-50 grayscale' : ''}`}>
                                <div className="bg-slate-800/80 px-4 py-3 border-b border-slate-700/50 flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={selectedTables.includes(tableName)}
                                        onChange={() => handleTableToggle(tableName)}
                                        className="h-4 w-4 rounded border-slate-600 bg-slate-700 text-cyan-500 focus:ring-cyan-500/20"
                                    />
                                    <Table className="h-4 w-4 text-cyan-400" />
                                    <h3 className="font-mono text-cyan-100 font-medium">{tableName}</h3>
                                </div>
                                <div className="p-4">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                                                    <th className="py-2 px-3 font-medium w-1/4">Column</th>
                                                    <th className="py-2 px-3 font-medium w-1/6">Type</th>
                                                    <th className="py-2 px-3 font-medium">User Comments (Context for AI)</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-800">
                                                {tableData.columns.map((col: any) => (
                                                    <tr key={col.name} className="hover:bg-slate-800/30 transition-colors">
                                                        <td className="py-3 px-3 font-mono text-sm text-slate-300">
                                                            {col.name}
                                                            {col.primary_key && <span className="ml-2 text-[10px] bg-yellow-500/20 text-yellow-400 px-1 py-0.5 rounded">PK</span>}
                                                        </td>
                                                        <td className="py-3 px-3 text-sm text-slate-500 font-mono">{col.type}</td>
                                                        <td className="py-3 px-3">
                                                            <div className="relative">
                                                                <MessageSquare className="absolute top-3 left-3 h-4 w-4 text-slate-600" />
                                                                <input
                                                                    type="text"
                                                                    placeholder="e.g. 'Target variable', 'User age in years', 'Key identifier'"
                                                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg py-2 pl-9 pr-3 text-sm text-slate-200 placeholder-slate-600 focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition-all"
                                                                    value={comments[tableName]?.[col.name] || ''}
                                                                    onChange={(e) => handleCommentChange(tableName, col.name, e.target.value)}
                                                                />
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {error && (
                    <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg text-red-200 text-sm">
                        {error}
                    </div>
                )}

                <div className="flex justify-end">
                    <button
                        onClick={handleAnalyze}
                        disabled={loading}
                        className={`px-8 py-4 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg ${loading
                            ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                            : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-emerald-500/20 hover:shadow-emerald-500/40 transform hover:-translate-y-0.5'
                            }`}
                    >
                        {loading ? (
                            <>
                                <Loader className="animate-spin h-5 w-5" />
                                Analyzing with Context...
                            </>
                        ) : (
                            <>
                                <Save className="h-5 w-5" />
                                Save Comments & Analyze
                                <ArrowRight className="h-5 w-5" />
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
