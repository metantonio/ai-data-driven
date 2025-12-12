import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import Visualizations from './pages/Visualizations';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/results" element={<Results />} />
                <Route path="/visualizations" element={<Visualizations />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
