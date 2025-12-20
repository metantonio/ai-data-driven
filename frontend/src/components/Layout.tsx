import React from 'react';
import { ThemeToggle } from './ThemeToggle';
import { Sparkles } from 'lucide-react';

interface LayoutProps {
    children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50 transition-colors duration-300">
            <header className="fixed top-0 left-0 right-0 h-16 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md z-50 px-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center">
                        <Sparkles className="h-5 w-5 text-white" />
                    </div>
                    <span className="font-bold text-lg tracking-tight hidden sm:block">
                        QLX <span className="text-cyan-500">AI</span>-Data
                    </span>
                </div>

                <div className="flex items-center gap-4">
                    <ThemeToggle />
                </div>
            </header>

            <main className="pt-16 min-h-screen">
                {children}
            </main>
        </div>
    );
};
