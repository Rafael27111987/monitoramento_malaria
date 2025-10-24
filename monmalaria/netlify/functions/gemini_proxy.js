// Arquivo: netlify/functions/gemini_proxy.js

// Usa o 'fetch' nativo do Node.js/Netlify Functions
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GEMINI_MODEL = 'gemini-2.5-flash';

// Cabeçalhos para tratamento de CORS (MANTIDO)
const HEADERS = {
    'Access-Control-Allow-Origin': '*', 
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
};

/**
 * Função utilitária para retornar um erro de forma consistente.
 * @param {number} statusCode - Código HTTP do erro.
 * @param {string} message - Mensagem de erro amigável para o cliente.
 * @param {any} details - Detalhes internos (para console.error).
 */
const handleError = (statusCode, message, details) => {
    // Loga o erro no console do Netlify para depuração
    console.error(`ERRO [Status ${statusCode}]: ${message}`, details); 
    
    return {
        statusCode: statusCode,
        headers: HEADERS,
        body: JSON.stringify({ 
            error: message,
            // Apenas inclua detalhes de forma segura, se necessário
            details: (statusCode >= 500 && details) ? details.toString() : undefined
        }),
    };
};

exports.handler = async (event, context) => {
    
    // --- 1. TRATAMENTO DE PRÉ-VOO OPTIONS (CORS) ---
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200, 
            headers: HEADERS,
            body: JSON.stringify({ message: "CORS OK" }),
        };
    }

    // --- 2. VERIFICAÇÃO DE MÉTODO e Chave ---
    if (event.httpMethod !== 'POST') {
        // Usa a função utilitária
        return handleError(405, 'Método não permitido. Use POST.', null);
    }

    if (!GEMINI_API_KEY) {
        // Usa a função utilitária
        return handleError(500, 'Chave de API do Gemini não configurada no servidor.', "GEMINI_API_KEY Missing");
    }

    // --- 3. EXTRAÇÃO E VALIDAÇÃO DO PROMPT ---
    let prompt;
    try {
        const body = JSON.parse(event.body);
        prompt = body?.prompt?.trim(); // Usa optional chaining para mais segurança e trim()
    } catch (e) {
        return handleError(400, 'Corpo da requisição inválido (JSON mal-formado).', e);
    }

    if (!prompt) {
        return handleError(400, 'O campo "prompt" é obrigatório e não pode ser vazio.', null);
    }

    // --- 4. CHAMADA À API GEMINI ---
    try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_API_KEY}`;
        
        const apiBody = JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
            // Recomenda-se adicionar um 'systemInstruction' para guiar a IA,
            // ou configurações de segurança (safetySettings)
        });

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: apiBody,
        });
        
        // Tenta ler a resposta da API (JSON)
        const data = await response.json(); 

        // --- 5. TRATAMENTO DE ERROS DA API GEMINI ---
        if (!response.ok) {
            // Retorna o status code do Gemini (ex: 400, 403, 429)
            // Loga o objeto 'data' completo retornado pela API para inspeção
            return handleError(
                response.status || 502, // 502 Bad Gateway é um bom fallback para erro na API externa
                `Erro ao comunicar com a API Gemini (Status: ${response.status}).`,
                data 
            );
        }
        
        // Verifica se a resposta tem conteúdo válido
        const aiText = data?.candidates?.[0]?.content?.parts?.[0]?.text;

        if (!aiText) {
             // Tratamento robusto para respostas bloqueadas ou vazias
             return handleError(
                500, 
                'A IA não retornou um texto válido. Conteúdo pode ter sido bloqueado ou a resposta é vazia.', 
                data
            );
        }

        // --- 6. SUCESSO ---
        return {
            statusCode: 200,
            headers: HEADERS,
            body: JSON.stringify({ 
                text: aiText
            }),
        };
        
    } catch (error) {
        // Erro fatal (ex: falha de rede, erro no parse do JSON da API, etc.)
        return handleError(
            500, 
            'Erro interno do servidor ao processar a requisição da IA.', 
            error
        );
    }
};