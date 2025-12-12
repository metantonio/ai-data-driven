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
    metrics: {
        mse: number;
        r2: number;
    };
    model_type: string;
    features: string[];
    target: string;
}

export const analyzeSchema = async (connectionString: string): Promise<SchemaAnalysis> => {
    const response = await api.post('/analyze-schema', { connection_string: connectionString });
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
