import { X, Download, Zap, Info, Loader } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface UpdateModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUpdate: () => void;
    isUpdating: boolean;
    currentVersion: string;
    latestVersion: string;
    releaseNotes: string;
}

export default function UpdateModal({
    isOpen,
    onClose,
    onUpdate,
    isUpdating,
    currentVersion,
    latestVersion,
    releaseNotes,
}: UpdateModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-300">
                {/* Header */}
                <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-gradient-to-r from-indigo-600/10 to-transparent">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-500/20 rounded-2xl border border-indigo-500/30">
                            <Zap className="h-6 w-6 text-indigo-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white">New Update Available!</h2>
                            <p className="text-slate-400 text-sm">
                                Upgrade from <span className="font-mono text-slate-300">v{currentVersion}</span> to <span className="font-mono text-indigo-400 font-bold">v{latestVersion}</span>
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-800 rounded-xl text-slate-400 hover:text-white transition-all"
                    >
                        <X className="h-6 w-6" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-8 overflow-y-auto space-y-6">
                    <div className="flex items-start gap-4 p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-2xl">
                        <Info className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                        <p className="text-sm text-indigo-300 leading-relaxed">
                            A new version of QLX AI Data Science is available with improvements and new features. We recommend updating to the latest version for the best experience.
                        </p>
                    </div>

                    <div className="space-y-4">
                        <h3 className="text-sm font-bold uppercase tracking-widest text-slate-500 ml-1">Release Notes</h3>
                        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 markdown-content max-w-none">
                            <ReactMarkdown>{releaseNotes || "No release notes provided."}</ReactMarkdown>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex flex-col sm:flex-row gap-4">
                    <button
                        onClick={onUpdate}
                        disabled={isUpdating}
                        className="flex-1 px-8 py-4 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 text-white rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-xl shadow-indigo-500/20 group disabled:opacity-50"
                    >
                        {isUpdating ? (
                            <>
                                <Loader className="h-5 w-5 animate-spin" />
                                Updating...
                            </>
                        ) : (
                            <>
                                <Download className="h-5 w-5 group-hover:scale-110 transition-transform" />
                                Update and Restart
                            </>
                        )}
                    </button>
                    <button
                        onClick={onClose}
                        disabled={isUpdating}
                        className="px-8 py-4 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-2xl font-bold transition-all border border-slate-700"
                    >
                        Maybe Later
                    </button>
                </div>
            </div>
        </div>
    );
}
