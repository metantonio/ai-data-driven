import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import Visualizations from './pages/Visualizations';
import AdvancedAnalysis from './pages/AdvancedAnalysis';
import EDAPage from './pages/EDA';
import EDAProgress from './pages/EDAProgress';
import Settings from './pages/Settings';
import ModelRegistry from './pages/ModelRegistry';
import PredictionSandbox from './pages/PredictionSandbox';
import { Layout } from './components/Layout';

function App() {
    return (
        <BrowserRouter>
            <Layout>
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/results" element={<Results />} />
                    <Route path="/visualizations" element={<Visualizations />} />
                    <Route path="/advanced-analysis" element={<AdvancedAnalysis />} />
                    <Route path="/eda" element={<EDAPage />} />
                    <Route path="/eda-progress" element={<EDAProgress />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/registry" element={<ModelRegistry />} />
                    <Route path="/sandbox" element={<PredictionSandbox />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Layout>
        </BrowserRouter>
    );
}

export default App;
