import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface SchemaAnalysis {
    raw_schema: any;
    analysis: string;
    connection_string?: string;
}

export interface ExecutionReport {
    metrics: Record<string, any>; // Record to support dynamic keys like 'silhouette_score', 'accuracy', etc.
    model_type: string;
    features: string[];
    target: string;
    visualization_data?: any[];
}

export const analyzeSchema = async (connectionString: string, algorithmType: string) => {
    const response = await axios.post(`${API_BASE_URL}/analyze-schema`, {
        connection_string: connectionString,
        algorithm_type: algorithmType
    });
    return response.data;
};

export const adaptCode = async (schemaAnalysis: SchemaAnalysis, algorithmType: string = "linear_regression"): Promise<{ code: string }> => {
    const response = await api.post('/adapt-code', { schema_analysis: schemaAnalysis, algorithm_type: algorithmType });
    return response.data;
};

export const executeCode = async (code: string, schemaAnalysis?: SchemaAnalysis): Promise<{ stdout: string; stderr: string; report: ExecutionReport | null }> => {
    const response = await api.post('/execute-code', { code, schema_analysis: schemaAnalysis });
    return response.data;
};

export const generateInsights = async (executionReport: ExecutionReport, schemaAnalysis: SchemaAnalysis): Promise<{ insights: string }> => {
    const response = await api.post('/generate-insights', { execution_report: executionReport, schema_analysis: schemaAnalysis });
    return response.data;
};
