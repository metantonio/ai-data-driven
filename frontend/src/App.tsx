import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import Visualizations from './pages/Visualizations';
import AdvancedAnalysis from './pages/AdvancedAnalysis';
import EDAPage from './pages/EDA';
import EDAProgress from './pages/EDAProgress';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/results" element={<Results />} />
                <Route path="/visualizations" element={<Visualizations />} />
                <Route path="/advanced-analysis" element={<AdvancedAnalysis />} />
                <Route path="/eda" element={<EDAPage />} />
                <Route path="/eda-progress" element={<EDAProgress />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
