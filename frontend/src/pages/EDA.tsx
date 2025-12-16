
import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import ReactMarkdown from 'react-markdown';
import Plot from 'react-plotly.js';
import { Database, Send, Loader, Sparkles } from 'lucide-react';

interface Artifact {
    title?: string;
    render_type: 'dataframe' | 'matplotlib' | 'plotly' | 'sweetviz' | 'dtale' | 'unknown';
    data: any;
}

interface Message {
    role: 'user' | 'ai';
    content: string;
    artifacts?: Artifact[];
}

const EDAPage: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'ai', content: 'Hello! I\'m your EDA Copilot. Ask me to analyze your data, visualize patterns, or generate reports.' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [connectionString, setConnectionString] = useState('sqlite:///../example.db');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await api.post('/eda/chat', {
                question: input,
                connection_string: connectionString,
                model_name: "gpt-4-turbo"
            });

            const data = response.data;
            const artifactList: Artifact[] = [];
            const toolCalls = data.tool_calls || [];
            const rawArtifacts = data.artifacts || {};
            const lastTool = toolCalls.length > 0 ? toolCalls[toolCalls.length - 1] : null;

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
                    artifactList.push({ title: 'Missing Values', render_type: 'matplotlib', data: rawArtifacts.bar_plot });
                }
                if (rawArtifacts.heatmap_plot) {
                    artifactList.push({ title: 'Correlation Heatmap', render_type: 'matplotlib', data: rawArtifacts.heatmap_plot });
                }
                if (rawArtifacts.distribution_plot) {
                    artifactList.push({ title: 'Distributions', render_type: 'matplotlib', data: rawArtifacts.distribution_plot });
                }
            }

            const aiMessage: Message = {
                role: 'ai',
                content: data.ai_message,
                artifacts: artifactList
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
            case 'dataframe':
                return (
                    <div key={idx} className="overflow-x-auto my-4 rounded-xl border border-slate-700/50 bg-slate-900/50">
                        <table className="min-w-full divide-y divide-slate-700">
                            <thead className="bg-slate-800/50">
                                <tr>
                                    {artifact.data.length > 0 && Object.keys(artifact.data[0]).map(key => (
                                        <th key={key} className="px-4 py-3 text-left text-xs font-semibold text-cyan-400 uppercase tracking-wider">{key}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {artifact.data.map((row: any, rIdx: number) => (
                                    <tr key={rIdx} className="hover:bg-slate-800/30 transition-colors">
                                        {Object.values(row).map((val: any, cIdx: number) => (
                                            <td key={cIdx} className="px-4 py-3 whitespace-nowrap text-sm text-slate-300">{String(val)}</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                );
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
            default:
                return <div key={idx} className="text-red-400">Unknown artifact type: {artifact.render_type}</div>;
        }
    };

    return (
        <div className="min-h-screen bg-slate-900 flex flex-col p-4">
            {/* Header */}
            <div className="mb-6 text-center">
                <div className="flex items-center justify-center gap-3 mb-2">
                    <Sparkles className="h-8 w-8 text-cyan-400" />
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                        EDA Copilot
                    </h1>
                </div>
                <p className="text-slate-400 text-sm">Explore your data with AI-powered analysis</p>
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

                {/* Example Questions */}
                <div className="mt-3 flex flex-wrap gap-2 justify-center">
                    {['Describe the dataset', 'Analyze missing data', 'Show correlations', 'Show first 10 rows'].map((q) => (
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
    );
};

export default EDAPage;
