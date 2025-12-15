import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import Visualizations from './pages/Visualizations';
import AdvancedAnalysis from './pages/AdvancedAnalysis';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/results" element={<Results />} />
                <Route path="/visualizations" element={<Visualizations />} />
                <Route path="/advanced-analysis" element={<AdvancedAnalysis />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
