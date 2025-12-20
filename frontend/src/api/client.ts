import axios from 'axios';

const API_BASE_URL = '/api';

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
    metrics: Record<string, any>;
    model_type: string;
    features: string[];
    target: string;
    model_path?: string;
    visualization_data?: any[];
    shap_importance?: Record<string, number>;
}

export const analyzeSchema = async (connectionString: string, algorithmType: string) => {
    const response = await api.post('/analyze-schema', {
        connection_string: connectionString,
        algorithm_type: algorithmType
    });
    return response.data;
};

export const getSchema = async (connectionString: string) => {
    const response = await api.post('/get-schema', { connection_string: connectionString });
    return response.data;
};

export const analyzeSchemaWithComments = async (connectionString: string, userComments: Record<string, any>, algorithmType: string, selectedTables: string[] = [], mlObjective?: string) => {
    const response = await api.post('/analyze-schema-with-comments', {
        connection_string: connectionString,
        user_comments: userComments,
        algorithm_type: algorithmType,
        selected_tables: selectedTables,
        ml_objective: mlObjective
    });
    return response.data;
};

export const adaptCode = async (schemaAnalysis: SchemaAnalysis, algorithmType: string = "linear_regression", edaSummary?: string, mlObjective?: string): Promise<{ code: string }> => {
    const response = await api.post('/adapt-code', {
        schema_analysis: schemaAnalysis,
        algorithm_type: algorithmType,
        eda_summary: edaSummary,
        ml_objective: mlObjective
    });
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

export const generateInsights = async (executionReport: ExecutionReport, schemaAnalysis: SchemaAnalysis, algorithmType: string, mlObjective?: string): Promise<{ insights: string }> => {
    const response = await api.post('/generate-insights', {
        execution_report: executionReport,
        schema_analysis: schemaAnalysis,
        algorithm_type: algorithmType,
        ml_objective: mlObjective
    });
    return response.data;
};

export const predict = async (modelPath: string, features: any) => {
    const response = await api.post('/predict', { model_path: modelPath, features });
    return response.data;
};

export const runAutomaticEDAStream = async (
    connectionString: string,
    userComments: Record<string, any>,
    algorithmType: string,
    onUpdate: (data: any) => void,
    signal?: AbortSignal,
    mlObjective?: string
) => {
    const response = await fetch(`${API_BASE_URL}/automatic-eda`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            connection_string: connectionString,
            user_comments: userComments,
            algorithm_type: algorithmType,
            ml_objective: mlObjective
        }),
        signal
    });

    if (!response.ok) {
        throw new Error(`EDA failed with status: ${response.status} ${response.statusText}`);
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
        buffer = lines[lines.length - 1];
    }
};
export const getSettings = async () => {
    const response = await api.get('/settings');
    return response.data;
};

export const updateSettings = async (settings: any) => {
    const response = await api.post('/settings', settings);
    return response.data;
};

export const shutdownApp = async () => {
    const response = await api.post('/settings/shutdown');
    return response.data;
};
