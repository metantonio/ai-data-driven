import React from 'react';
import { Database, Search, Settings, PlayCircle } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export type Step = 'connect' | 'explore' | 'configure' | 'results';

interface StepperProps {
    currentStep: Step;
    onStepClick?: (step: Step) => void;
}

const steps: { key: Step; label: string; icon: React.ReactNode }[] = [
    { key: 'connect', label: 'Connect', icon: <Database className="w-4 h-4" /> },
    { key: 'explore', label: 'Explore', icon: <Search className="w-4 h-4" /> },
    { key: 'configure', label: 'Configure', icon: <Settings className="w-4 h-4" /> },
    { key: 'results', label: 'Analyze', icon: <PlayCircle className="w-4 h-4" /> },
];

export const Stepper: React.FC<StepperProps> = ({ currentStep, onStepClick }) => {
    const currentIndex = steps.findIndex(s => s.key === currentStep);

    return (
        <div className="flex items-center justify-center w-full max-w-2xl mx-auto mb-8">
            {steps.map((step, index) => (
                <React.Fragment key={step.key}>
                    <div
                        className={cn(
                            "flex flex-col items-center group relative cursor-pointer",
                            onStepClick ? "pointer-events-auto" : "pointer-events-none"
                        )}
                        onClick={() => onStepClick?.(step.key)}
                    >
                        <div className={cn(
                            "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 border-2 shadow-lg",
                            index <= currentIndex
                                ? "bg-cyan-500 border-cyan-400 text-white shadow-cyan-500/20"
                                : "bg-slate-800 border-slate-700 text-slate-500"
                        )}>
                            {step.icon}
                        </div>
                        <span className={cn(
                            "absolute -bottom-6 text-[10px] font-bold uppercase tracking-widest whitespace-nowrap transition-colors",
                            index <= currentIndex ? "text-cyan-400" : "text-slate-500"
                        )}>
                            {step.label}
                        </span>
                    </div>

                    {index < steps.length - 1 && (
                        <div className="flex-1 h-0.5 mx-4 bg-slate-800 relative overflow-hidden">
                            <div
                                className={cn(
                                    "absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500",
                                    index < currentIndex ? "translate-x-0" : "-translate-x-full"
                                )}
                            />
                        </div>
                    )}
                </React.Fragment>
            ))}
        </div>
    );
};
