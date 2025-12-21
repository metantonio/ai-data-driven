import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings as SettingsIcon, Save, ArrowLeft, Loader, Database, Cpu, Globe, Key, AlertCircle, CheckCircle, Power, Zap, RefreshCw } from 'lucide-react';
import { getSettings, updateSettings, shutdownApp, checkUpdates, UpdateInfo, triggerUpdate } from '../api/client';
import UpdateModal from '../components/UpdateModal';

export default function Settings() {
    const [config, setConfig] = useState({
        LLM_PROVIDER: 'ollama',
        LLM_API_URL: '',
        LLM_MODEL: '',
        LLM_API_KEY: '',
        DATABASE_URL: '',
        MAX_RETRIES: 2
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [checkingUpdates, setCheckingUpdates] = useState(false);
    const [isUpdating, setIsUpdating] = useState(false);
    const [updateResult, setUpdateResult] = useState<UpdateInfo | null>(null);
    const [showUpdateModal, setShowUpdateModal] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        fetchSettings();
        handleCheckUpdates();
    }, []);

    const handleCheckUpdates = async () => {
        setCheckingUpdates(true);
        try {
            const result = await checkUpdates();
            setUpdateResult(result);
        } catch (err) {
            console.error("Failed to check for updates:", err);
        } finally {
            setCheckingUpdates(false);
        }
    };

    const handleTriggerUpdate = async () => {
        if (!updateResult?.download_url) return;

        setIsUpdating(true);
        try {
            // Find the first .exe asset if available, otherwise use the release page URL
            // (Note: The backend trigger_update will fail if it's not a direct file link, 
            // but for this implementation we assume the user provides a valid download URL)
            const exeAsset = updateResult?.download_url; // Simplified

            const res = await triggerUpdate(exeAsset);
            setMessage({ type: 'success', text: res.message });
            // The app will shut down shortly
        } catch (err: any) {
            setMessage({ type: 'error', text: err.response?.data?.detail || "Update failed." });
            setIsUpdating(false);
        }
    };

    const fetchSettings = async () => {
        try {
            const data = await getSettings();
            setConfig(data);
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to load settings.' });
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);
        try {
            await updateSettings(config);
            setMessage({ type: 'success', text: 'Settings saved successfully! Restart the backend for all changes to take effect.' });
        } catch (err: any) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to save settings.' });
        } finally {
            setSaving(false);
        }
    };

    const handleShutdown = async () => {
        if (window.confirm('Are you sure you want to shut down the application server? You will need to restart the .exe manually.')) {
            try {
                await shutdownApp();
                setMessage({ type: 'success', text: 'Application is shutting down. You can close this window now.' });
                // We don't clear saving/loading because the app is dying
            } catch (err) {
                setMessage({ type: 'error', text: 'Failed to request shutdown.' });
            }
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <Loader className="h-8 w-8 text-cyan-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-12">
            <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
                    >
                        <ArrowLeft className="h-5 w-5" />
                        Back to Dashboard
                    </button>
                    <div className="flex items-center gap-2 px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-cyan-400 text-xs font-bold tracking-widest uppercase">
                        Configuration
                    </div>
                </div>

                <div className="space-y-2 flex justify-between items-end">
                    <div className="space-y-2">
                        <h1 className="text-4xl font-extrabold flex items-center gap-3">
                            <SettingsIcon className="h-10 w-10 text-cyan-400" />
                            System Settings
                        </h1>
                        <p className="text-slate-400">
                            Configure your AI processing engine and database connections.
                        </p>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                        <div className="flex items-center gap-2 px-3 py-1 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-[10px] font-mono">
                            v{updateResult?.current_version || "..."}
                        </div>
                        <button
                            onClick={handleCheckUpdates}
                            disabled={checkingUpdates}
                            className="flex items-center gap-2 text-xs font-bold text-cyan-400 hover:text-cyan-300 transition-colors disabled:opacity-50"
                        >
                            <RefreshCw className={`h-3 w-3 ${checkingUpdates ? 'animate-spin' : ''}`} />
                            Check Updates
                        </button>
                    </div>
                </div>

                {updateResult?.has_update && (
                    <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/50 flex items-center justify-between group animate-in slide-in-from-top-4 duration-500">
                        <div className="flex items-center gap-3">
                            <Zap className="h-5 w-5 text-indigo-400 animate-pulse" />
                            <div>
                                <p className="text-sm font-bold text-indigo-300">Update Available: v{updateResult.latest_version}</p>
                                <p className="text-[10px] text-slate-400">A new version is ready with improvements.</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setShowUpdateModal(true)}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition-all"
                        >
                            View Details
                        </button>
                    </div>
                )}

                {message && (
                    <div className={`p-4 rounded-xl flex items-center gap-3 border ${message.type === 'success'
                        ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400'
                        : 'bg-red-500/10 border-red-500/50 text-red-400'
                        }`}>
                        {message.type === 'success' ? <CheckCircle className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
                        <span className="text-sm font-medium">{message.text}</span>
                    </div>
                )}

                <form onSubmit={handleSave} className="bg-slate-800/50 border border-slate-700/50 rounded-3xl p-8 shadow-2xl backdrop-blur-md space-y-8">

                    {/* LLM Provider Section */}
                    <div className="space-y-6">
                        <h2 className="text-lg font-bold flex items-center gap-2 text-cyan-400">
                            <Cpu className="h-5 w-5" />
                            LLM Engine
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300 ml-1">AI Provider</label>
                                <select
                                    value={config.LLM_PROVIDER}
                                    onChange={(e) => setConfig({ ...config, LLM_PROVIDER: e.target.value })}
                                    className="w-full pl-4 pr-10 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 transition-all text-sm appearance-none"
                                >
                                    <option value="ollama">Ollama (Local)</option>
                                    <option value="openai">OpenAI / Compatible</option>
                                    <option value="vllm">vLLM (Local Batching)</option>
                                    <option value="mock">Mock (Development)</option>
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300 ml-1">AI Model Name</label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Cpu className="h-4 w-4 text-slate-500" />
                                    </div>
                                    <input
                                        type="text"
                                        value={config.LLM_MODEL}
                                        onChange={(e) => setConfig({ ...config, LLM_MODEL: e.target.value })}
                                        placeholder="e.g. qwen2.5-coder:7b"
                                        className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 placeholder-slate-600 transition-all font-mono text-sm"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300 ml-1">API URL</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Globe className="h-4 w-4 text-slate-500" />
                                </div>
                                <input
                                    type="text"
                                    value={config.LLM_API_URL}
                                    onChange={(e) => setConfig({ ...config, LLM_API_URL: e.target.value })}
                                    className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 placeholder-slate-600 transition-all font-mono text-sm"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300 ml-1">API Key (if required)</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Key className="h-4 w-4 text-slate-500" />
                                </div>
                                <input
                                    type="password"
                                    value={config.LLM_API_KEY}
                                    onChange={(e) => setConfig({ ...config, LLM_API_KEY: e.target.value })}
                                    className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 placeholder-slate-600 transition-all font-mono text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="h-px bg-slate-700/50" />

                    {/* Database Section */}
                    <div className="space-y-6">
                        <h2 className="text-lg font-bold flex items-center gap-2 text-cyan-400">
                            <Database className="h-5 w-5" />
                            Database Defaults
                        </h2>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300 ml-1">Default Connection String</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Database className="h-4 w-4 text-slate-500" />
                                </div>
                                <input
                                    type="text"
                                    value={config.DATABASE_URL}
                                    onChange={(e) => setConfig({ ...config, DATABASE_URL: e.target.value })}
                                    className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 placeholder-slate-600 transition-all font-mono text-sm"
                                />
                            </div>
                            <p className="text-[10px] text-slate-500 italic ml-1">
                                Used as the default starting point for new analysis pipelines.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300 ml-1">Maximum Repair Retries</label>
                            <div className="flex items-center gap-4">
                                <div className="relative flex-1">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Cpu className="h-4 w-4 text-slate-500" />
                                    </div>
                                    <input
                                        type="number"
                                        min="0"
                                        max="49"
                                        value={config.MAX_RETRIES}
                                        onChange={(e) => setConfig({ ...config, MAX_RETRIES: parseInt(e.target.value) || 0 })}
                                        className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none text-slate-100 placeholder-slate-600 transition-all font-mono text-sm"
                                    />
                                </div>
                                <div className="text-xs text-slate-400 bg-slate-700/50 px-3 py-2 rounded-lg border border-slate-600">
                                    Total attempts: <span className="text-cyan-400 font-bold">{(config.MAX_RETRIES || 0) + 1}</span>
                                </div>
                            </div>
                            <p className="text-[10px] text-slate-500 italic ml-1">
                                How many times the AI should try to fix failing code before stopping (Max: 49 retries / 50 total attempts).
                            </p>
                        </div>
                    </div>

                    <div className="pt-4 flex flex-col gap-4">
                        <button
                            type="submit"
                            disabled={saving}
                            className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg ${saving
                                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-cyan-500/20 hover:shadow-cyan-500/40 transform hover:-translate-y-0.5'
                                }`}
                        >
                            {saving ? (
                                <>
                                    <Loader className="animate-spin h-5 w-5" />
                                    Saving Config...
                                </>
                            ) : (
                                <>
                                    <Save className="h-5 w-5" />
                                    Apply Configuration
                                </>
                            )}
                        </button>

                        <button
                            type="button"
                            onClick={handleShutdown}
                            className="w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all border border-red-500/30 text-red-400 hover:bg-red-500/10 hover:border-red-500/50"
                        >
                            <Power className="h-5 w-5" />
                            Shutdown Application
                        </button>
                    </div>
                </form>
            </div>

            <UpdateModal
                isOpen={showUpdateModal}
                onClose={() => setShowUpdateModal(false)}
                onUpdate={handleTriggerUpdate}
                isUpdating={isUpdating}
                currentVersion={updateResult?.current_version || ""}
                latestVersion={updateResult?.latest_version || ""}
                releaseNotes={updateResult?.release_notes || ""}
            />
        </div>
    );
}
