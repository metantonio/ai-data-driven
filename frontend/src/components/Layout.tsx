import React from 'react';
import { Link } from 'react-router-dom';
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
                    <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                        <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center">
                            <Sparkles className="h-5 w-5 text-white" />
                        </div>
                        <span className="font-bold text-lg tracking-tight hidden sm:block">
                            QLX <span className="text-cyan-500">AI</span>-Data
                        </span>
                    </Link>

                    <nav className="ml-8 hidden md:flex items-center gap-6">
                        <Link to="/eda" className="text-sm font-medium text-slate-500 hover:text-cyan-500 transition-colors flex items-center gap-1.5 px-3 py-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">
                            <Sparkles className="h-4 w-4 text-cyan-500" />
                            EDA Copilot
                        </Link>
                    </nav>
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
