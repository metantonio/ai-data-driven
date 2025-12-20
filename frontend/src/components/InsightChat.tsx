import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, User, Bot, Sparkles } from 'lucide-react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

interface Message {
    role: 'user' | 'ai';
    content: string;
}

interface InsightChatProps {
    executionReport: any;
    algorithmType: string;
    initialInsight?: string;
}

const InsightChat: React.FC<InsightChatProps> = ({ executionReport, algorithmType, initialInsight }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (initialInsight && messages.length === 0) {
            setMessages([{ role: 'ai', content: initialInsight }]);
        }
    }, [initialInsight]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const resp = await axios.post('/api/chat-insights', {
                query: input,
                history: messages,
                execution_report: executionReport,
                algorithm_type: algorithmType
            });

            const aiMsg: Message = { role: 'ai', content: resp.data.response };
            setMessages(prev => [...prev, aiMsg]);
        } catch (error) {
            console.error("Chat failed", error);
            setMessages(prev => [...prev, { role: 'ai', content: "Sorry, I encountered an error processing your request." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[600px] bg-slate-900/50 border border-slate-700/50 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
            {/* Header */}
            <div className="p-4 border-b border-white/5 bg-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-yellow-400" />
                    <h3 className="font-bold text-white text-sm">Insight Chatbot</h3>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Active session</span>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                            <div className={`shrink-0 h-8 w-8 rounded-lg flex items-center justify-center ${msg.role === 'user' ? 'bg-indigo-600' : 'bg-slate-800 border border-white/10'}`}>
                                {msg.role === 'user' ? <User className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-cyan-400" />}
                            </div>
                            <div className={`p-4 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                                ? 'bg-indigo-600 text-white shadow-lg'
                                : 'bg-slate-800/80 border border-white/5 text-slate-200'}`}>
                                <div className="prose prose-invert prose-sm max-w-none">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="flex gap-3">
                            <div className="shrink-0 h-8 w-8 rounded-lg bg-slate-800 border border-white/10 flex items-center justify-center">
                                <Bot className="h-4 w-4 text-cyan-400 animate-pulse" />
                            </div>
                            <div className="p-4 rounded-2xl bg-slate-800/80 border border-white/5 flex items-center gap-3">
                                <Loader className="h-3 w-3 animate-spin text-cyan-400" />
                                <span className="text-xs text-slate-400">Processing insights...</span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 bg-white/5 border-t border-white/5">
                <div className="flex gap-2 bg-slate-950 p-2 rounded-xl border border-white/10 focus-within:border-cyan-500/50 transition-all">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask about the results..."
                        className="flex-1 bg-transparent border-none text-white text-sm focus:outline-none px-2"
                        disabled={loading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className="p-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-all disabled:opacity-50"
                    >
                        <Send className="h-4 w-4" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default InsightChat;
