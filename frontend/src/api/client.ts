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
    model_path?: string; // Added for interactive prediction
    visualization_data?: any[];
}

export const analyzeSchema = async (connectionString: string, algorithmType: string) => {
    const response = await axios.post(`${API_BASE_URL}/analyze-schema`, {
        connection_string: connectionString,
        algorithm_type: algorithmType
    });
    return response.data;
};

export const getSchema = async (connectionString: string) => {
    const response = await api.post('/get-schema', { connection_string: connectionString });
    return response.data;
};

export const analyzeSchemaWithComments = async (connectionString: string, userComments: Record<string, any>, algorithmType: string) => {
    const response = await api.post('/analyze-schema-with-comments', {
        connection_string: connectionString,
        user_comments: userComments,
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

export const executeCodeStream = async (code: string, schemaAnalysis: any, onUpdate: (data: any) => void, signal?: AbortSignal) => {
    const response = await fetch(`${API_BASE_URL}/execute-code`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, schema_analysis: schemaAnalysis }),
        signal
    });

    if (!response.ok) {
        throw new Error(`Execution failed with status: ${response.status} ${response.statusText}`);
    }

    if (!response.body) return;

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Process all complete lines
        for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim();
            if (line) {
                try {
                    const data = JSON.parse(line);
                    onUpdate(data);
                } catch (e) {
                    console.error("Error parsing stream line:", line, e);
                }
            }
        }

        // Keep the last partial line in buffer
        buffer = lines[lines.length - 1];
    }
};

export const generateInsights = async (executionReport: ExecutionReport, schemaAnalysis: SchemaAnalysis): Promise<{ insights: string }> => {
    const response = await api.post('/generate-insights', { execution_report: executionReport, schema_analysis: schemaAnalysis });
    return response.data;
};

export const predict = async (modelPath: string, features: any) => {
    const response = await api.post('/predict', { model_path: modelPath, features });
    return response.data;
};
