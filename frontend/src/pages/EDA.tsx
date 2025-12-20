
import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import ReactMarkdown from 'react-markdown';
import Plot from 'react-plotly.js';
import { Database, Send, Loader, Sparkles, ArrowLeft, Reply, Star, Bookmark, Trash2, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Stepper } from '../components/Stepper';
import { DataTable } from '../components/DataTable';
import { ColumnDef } from '@tanstack/react-table';

interface Artifact {
    title?: string;
    render_type: 'dataframe' | 'matplotlib' | 'plotly' | 'sweetviz' | 'dtale' | 'sql_history' | 'unknown';
    data: any;
}

interface Message {
    role: 'user' | 'ai';
    content: string;
    artifacts?: Artifact[];
    context?: string; // Original user question for this response
}

const EDAPage: React.FC = () => {
    const navigate = useNavigate();
    const [messages, setMessages] = useState<Message[]>([
        { role: 'ai', content: 'Hello! I\'m your EDA Copilot. Ask me to analyze your data, visualize patterns, or generate reports.' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [connectionString, setConnectionString] = useState('sqlite:///../example.db');
    const [useSqlAgent, setUseSqlAgent] = useState(false);
    const [replyingTo, setReplyingTo] = useState<number | null>(null);
    const [showLibrary, setShowLibrary] = useState(false);
    const [favorites, setFavorites] = useState<any[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    const fetchFavorites = async () => {
        try {
            const resp = await api.get('/sql/favorites');
            setFavorites(resp.data);
        } catch (err) {
            console.error("Failed to fetch favorites", err);
        }
    };

    useEffect(() => {
        fetchFavorites();
    }, []);

    const saveFavorite = async (title: string, query: string) => {
        try {
            await api.post('/sql/favorites', {
                title,
                query,
                connection_string: connectionString
            });
            fetchFavorites();
        } catch (err) {
            alert("Failed to save to library");
        }
    };

    const deleteFavorite = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await api.delete(`/sql/favorites/${id}`);
            setFavorites(favorites.filter(f => f.id !== id));
        } catch (err) {
            alert("Failed to delete favorite");
        }
    };

    const handleReply = (messageIndex: number) => {
        const message = messages[messageIndex];
        if (message.role === 'ai' && message.context) {
            setReplyingTo(messageIndex);
            setInput('');
            scrollToBottom();
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            context: replyingTo !== null ? messages[replyingTo].context : undefined
        };
        setMessages(prev => [...prev, userMessage]);

        const currentInput = input;
        const isReply = replyingTo !== null;
        const replyContext = isReply && messages[replyingTo].context
            ? `Previous question: "${messages[replyingTo].context}"\nPrevious response: "${messages[replyingTo].content.substring(0, 300)}..."`
            : '';

        setInput('');
        setReplyingTo(null);
        setLoading(true);

        try {
            // Use different endpoint for replies
            const endpoint = isReply ? '/eda/reply' : '/eda/chat';
            const payload = isReply
                ? {
                    question: currentInput,
                    connection_string: connectionString,
                    context: replyContext
                }
                : {
                    question: currentInput,
                    connection_string: connectionString,
                    model_name: "gpt-4-turbo",
                    use_sql_agent: useSqlAgent
                };

            const response = await api.post(endpoint, payload);

            const data = response.data;
            const artifactList: Artifact[] = [];
            const rawArtifacts = data.artifacts || {};

            // Map artifacts from SimpleEDAService
            if (rawArtifacts) {
                // Dataframe artifacts
                if (rawArtifacts.describe_df) {
                    artifactList.push({ title: 'Statistical Summary', render_type: 'dataframe', data: rawArtifacts.describe_df });
                }
                if (rawArtifacts.sample_df) {
                    artifactList.push({ title: 'Data Sample', render_type: 'dataframe', data: rawArtifacts.sample_df });
                }

                // Image artifacts (matplotlib plots)
                if (rawArtifacts.bar_plot) {
                    artifactList.push({ title: 'Chart', render_type: 'matplotlib', data: rawArtifacts.bar_plot });
                }
                if (rawArtifacts.heatmap_plot) {
                    artifactList.push({ title: 'Correlation Heatmap', render_type: 'matplotlib', data: rawArtifacts.heatmap_plot });
                }
                if (rawArtifacts.distribution_plot) {
                    artifactList.push({ title: 'Distributions', render_type: 'matplotlib', data: rawArtifacts.distribution_plot });
                }
                if (rawArtifacts.outlier_plot) {
                    artifactList.push({ title: 'Outlier Detection', render_type: 'matplotlib', data: rawArtifacts.outlier_plot });
                }
                if (rawArtifacts.sql_history) {
                    artifactList.push({ title: 'SQL Agent History', render_type: 'sql_history', data: rawArtifacts.sql_history });
                }
                if (rawArtifacts.generated_plot) {
                    artifactList.push({ title: 'AI Generated Analysis', render_type: 'matplotlib', data: rawArtifacts.generated_plot });
                }
            }

            const aiMessage: Message = {
                role: 'ai',
                content: data.ai_message,
                artifacts: artifactList,
                context: currentInput // Store the original question for context
            };

            setMessages(prev => [...prev, aiMessage]);

        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'ai', content: "Error: " + (error as any).message }]);
        } finally {
            setLoading(false);
        }
    };

    const renderArtifact = (artifact: Artifact, idx: number) => {
        switch (artifact.render_type) {
            case 'dataframe': {
                const columns: ColumnDef<any, any>[] = artifact.data.length > 0
                    ? Object.keys(artifact.data[0]).map(key => ({
                        header: key,
                        accessorKey: key,
                        cell: (info: any) => String(info.getValue()),
                    }))
                    : [];

                return (
                    <div key={idx} className="my-4 p-4 rounded-xl border border-slate-700/50 bg-slate-900/50 shadow-xl">
                        <h4 className="text-sm font-bold text-cyan-400 mb-4 px-2 uppercase tracking-wider">{artifact.title}</h4>
                        <DataTable data={artifact.data} columns={columns} pageSize={5} />
                    </div>
                );
            }
            case 'matplotlib':
                return (
                    <div key={idx} className="my-4 p-4 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <h4 className="text-sm font-bold text-cyan-400 mb-3">{artifact.title}</h4>
                        <img src={`data:image/png;base64,${artifact.data}`} alt={artifact.title} className="max-w-full h-auto rounded-lg shadow-lg" />
                    </div>
                );
            case 'plotly':
                return (
                    <div key={idx} className="my-4 p-4 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <h4 className="text-sm font-bold text-cyan-400 mb-3">{artifact.title}</h4>
                        <Plot
                            data={artifact.data.data}
                            layout={{ ...artifact.data.layout, autosize: true, paper_bgcolor: 'rgba(15, 23, 42, 0.5)', plot_bgcolor: 'rgba(15, 23, 42, 0.5)', font: { color: '#cbd5e1' } }}
                            useResizeHandler={true}
                            style={{ width: "100%", height: "100%" }}
                        />
                    </div>
                );
            case 'sweetviz':
                return (
                    <div key={idx} className="my-4 p-4 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <h4 className="text-sm font-bold text-cyan-400 mb-3">{artifact.title}</h4>
                        <iframe
                            srcDoc={artifact.data.html}
                            className="w-full h-[600px] rounded-lg border border-slate-700/50"
                            title="Sweetviz"
                        />
                    </div>
                );
            case 'sql_history':
                return (
                    <div key={idx} className="my-4 p-4 rounded-xl bg-slate-900/50 border border-slate-700/50">
                        <h4 className="text-sm font-bold text-cyan-400 mb-3 flex items-center gap-2">
                            🤖 Agent Execution History
                        </h4>
                        <div className="space-y-3">
                            {artifact.data.map((attempt: any, i: number) => (
                                <div key={i} className={`p-3 rounded-lg border ${attempt.status === 'success' ? 'bg-green-900/20 border-green-700/50' : 'bg-red-900/20 border-red-700/50'}`}>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className={`text-xs font-bold uppercase ${attempt.status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                                            Attempt {attempt.attempt}: {attempt.status}
                                        </span>
                                        {attempt.status === 'success' && (
                                            <button
                                                onClick={() => saveFavorite(`Query for ${messages[messages.length - 1]?.context || 'Analysis'}`, attempt.sql)}
                                                className="p-1 hover:bg-white/10 rounded transition-colors text-yellow-500"
                                                title="Save to Library"
                                            >
                                                <Star className="h-4 w-4" />
                                            </button>
                                        )}
                                    </div>
                                    <div className="bg-slate-950/50 p-2 rounded border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto">
                                        {attempt.sql}
                                    </div>
                                    {attempt.error && (
                                        <div className="mt-2 text-xs text-red-400 font-mono">
                                            Error: {attempt.error}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                );
            default:
                return <div key={idx} className="text-red-400">Unknown artifact type: {artifact.render_type}</div>;
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col p-4 text-slate-900 dark:text-slate-50">
            {/* Stepper */}
            <div className="mt-4">
                <Stepper currentStep="explore" />
            </div>

            {/* Header */}
            <div className="mb-6 text-center relative">
                {/* Back Button */}
                <button
                    onClick={() => navigate('/')}
                    className="absolute left-0 top-0 flex items-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 rounded-lg border border-slate-700/50 transition-all"
                >
                    <ArrowLeft className="h-4 w-4" />
                    <span className="text-sm">Back</span>
                </button>

                <div className="flex items-center justify-center gap-3 mb-2">
                    <Sparkles className="h-8 w-8 text-cyan-400" />
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                        EDA Copilot
                    </h1>
                </div>
                <p className="text-slate-400 text-sm">Explore your data with AI-powered analysis</p>

                {/* Library Button */}
                <button
                    onClick={() => setShowLibrary(true)}
                    className="absolute right-0 top-0 flex items-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 rounded-lg border border-slate-700/50 transition-all font-bold"
                >
                    <Bookmark className="h-4 w-4" />
                    Library ({favorites.length})
                </button>
            </div>

            {/* Connection String Input */}
            <div className="mb-4 max-w-4xl mx-auto w-full">
                <label className="block text-sm font-medium text-slate-300 mb-2 ml-1">Database Connection</label>
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Database className="h-5 w-5 text-slate-500" />
                    </div>
                    <input
                        type="text"
                        value={connectionString}
                        onChange={e => setConnectionString(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 placeholder-slate-500 transition-all font-mono text-sm"
                        placeholder="sqlite:///../example.db"
                    />
                </div>
            </div>

            {/* SQL Agent Toggle */}
            <div className="mb-2 max-w-4xl mx-auto w-full flex justify-end">
                <label className="flex items-center gap-2 cursor-pointer bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-700/50 hover:bg-slate-700/50 transition-all">
                    <input
                        type="checkbox"
                        checked={useSqlAgent}
                        onChange={(e) => setUseSqlAgent(e.target.checked)}
                        className="form-checkbox h-4 w-4 text-cyan-500 rounded border-slate-600 bg-slate-700 focus:ring-cyan-500 focus:ring-offset-slate-900"
                    />
                    <span className="text-xs font-medium text-cyan-400">Enable Agentic SQL Mode</span>
                </label>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto mb-4 bg-slate-800/30 rounded-2xl border border-slate-700/50 p-4 space-y-4 max-w-4xl mx-auto w-full backdrop-blur-sm">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-2xl p-4 ${msg.role === 'user'
                            ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white'
                            : 'bg-slate-800/50 border border-slate-700/50 text-slate-100'
                            }`}>
                            <div className="prose prose-sm prose-invert max-w-none">
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                            {msg.artifacts && msg.artifacts.length > 0 && (
                                <div className="mt-4 space-y-4">
                                    {msg.artifacts.map((art, aIdx) => renderArtifact(art, aIdx))}
                                </div>
                            )}
                            {/* Reply Button for AI messages */}
                            {msg.role === 'ai' && msg.context && (
                                <button
                                    onClick={() => handleReply(idx)}
                                    className="mt-3 flex items-center gap-2 px-3 py-1.5 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 hover:text-cyan-400 rounded-lg text-xs transition-all border border-slate-600/50"
                                >
                                    <Reply className="h-3 w-3" />
                                    Reply
                                </button>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 flex items-center gap-2">
                            <Loader className="h-4 w-4 animate-spin text-cyan-400" />
                            <span className="text-slate-400 text-sm">Analyzing...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="max-w-4xl mx-auto w-full">
                {/* Replying Indicator */}
                {replyingTo !== null && (
                    <div className="mb-2 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg flex items-center justify-between">
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                            <Reply className="h-3 w-3" />
                            <span>Replying to: "{messages[replyingTo].context?.substring(0, 50)}..."</span>
                        </div>
                        <button
                            onClick={() => setReplyingTo(null)}
                            className="text-slate-500 hover:text-slate-300 text-xs"
                        >
                            ✕
                        </button>
                    </div>
                )}
                <div className="flex gap-2 bg-slate-800/50 p-3 rounded-2xl border border-slate-700/50 backdrop-blur-sm">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                        className="flex-1 bg-transparent border-none focus:outline-none text-slate-100 placeholder-slate-500 px-2"
                        placeholder="Ask about your data (e.g., 'Describe the dataset', 'Visualize missing data')"
                        disabled={loading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white px-6 py-2 rounded-xl font-medium flex items-center gap-2 transition-all shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5"
                    >
                        <Send className="h-4 w-4" />
                        Send
                    </button>
                </div>

                {/* EDA Options */}
                <div className="mt-4 space-y-3">
                    <p className="text-xs text-slate-400 text-center font-medium">Available Analysis Options:</p>

                    {/* Data Overview */}
                    <div className="space-y-2">
                        <p className="text-xs text-cyan-400 font-semibold ml-1">📊 Data Overview</p>
                        <div className="flex flex-wrap gap-2">
                            {[
                                'Show tables',
                                'Describe the dataset',
                                'Show column info',
                                'Show first 10 rows',
                                'Show last 10 rows',
                                'Show all data'
                            ].map((q) => (
                                <button
                                    key={q}
                                    onClick={() => setInput(q)}
                                    className="text-xs px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 rounded-lg border border-slate-700/50 transition-all"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Data Quality */}
                    <div className="space-y-2">
                        <p className="text-xs text-cyan-400 font-semibold ml-1">🔍 Data Quality</p>
                        <div className="flex flex-wrap gap-2">
                            {[
                                'Analyze missing data',
                                'Detect outliers',
                                'Show unique values'
                            ].map((q) => (
                                <button
                                    key={q}
                                    onClick={() => setInput(q)}
                                    className="text-xs px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 rounded-lg border border-slate-700/50 transition-all"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Statistical Analysis */}
                    <div className="space-y-2">
                        <p className="text-xs text-cyan-400 font-semibold ml-1">📈 Statistical Analysis</p>
                        <div className="flex flex-wrap gap-2">
                            {[
                                'Show correlations',
                                'Show distributions',
                                'Show value counts'
                            ].map((q) => (
                                <button
                                    key={q}
                                    onClick={() => setInput(q)}
                                    className="text-xs px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-cyan-400 rounded-lg border border-slate-700/50 transition-all"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* SQL Library Sidebar/Overlay */}
            {showLibrary && (
                <div className="fixed inset-0 z-50 flex justify-end animate-in fade-in duration-300">
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowLibrary(false)}></div>
                    <div className="relative w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-500 overflow-hidden">
                        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
                            <div className="flex items-center gap-3 text-cyan-400">
                                <Bookmark className="h-6 w-6" />
                                <h2 className="text-xl font-bold">SQL Library</h2>
                            </div>
                            <button onClick={() => setShowLibrary(false)} className="text-slate-500 hover:text-white transition-colors p-2 hover:bg-white/5 rounded-lg">✕</button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                            {favorites.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 space-y-4 py-20 opacity-40">
                                    <Bookmark className="h-16 w-16" />
                                    <p className="max-w-[200px]">Save your favorite AI-generated queries to find them here later.</p>
                                </div>
                            ) : (
                                favorites.map(fav => (
                                    <div key={fav.id} className="group bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 hover:border-cyan-500/30 transition-all hover:bg-slate-800">
                                        <div className="flex justify-between items-start mb-3">
                                            <h3 className="text-sm font-bold text-slate-200 line-clamp-1">{fav.title}</h3>
                                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => { setInput(fav.query); setShowLibrary(false); }}
                                                    className="p-1.5 hover:bg-cyan-500/20 text-cyan-400 rounded-lg transition-colors"
                                                    title="Use query"
                                                >
                                                    <Play className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={(e) => deleteFavorite(fav.id, e)}
                                                    className="p-1.5 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                                                    title="Delete"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </button>
                                            </div>
                                        </div>
                                        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/50 font-mono text-[10px] text-slate-400 overflow-x-auto mb-2 select-all">
                                            {fav.query}
                                        </div>
                                        <div className="text-[10px] text-slate-600 flex justify-between items-center">
                                            <span>{fav.timestamp}</span>
                                            <span className="truncate max-w-[150px]">{fav.connection_string}</span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EDAPage;
