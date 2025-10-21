class AIService {
    static async getCountryGuide(countryName, countryData) {
        const apiKey = this.getApiKey();
        
        if (!apiKey) throw new Error('API ключ не найден. Пожалуйста, добавьте ваш OpenRouter API ключ в настройках.');

        const prompt = this.generatePrompt(countryName, countryData);
        
        try {
            const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`,
                    'HTTP-Referer': window.location.origin,
                    'X-Title': 'Путешествия по миру'
                },
                body: JSON.stringify({
                    model: "meta-llama/llama-3.1-8b-instruct:free",
                    messages: [{ role: "user", content: prompt }],
                    max_tokens: 800,
                    temperature: 0.7
                })
            });

            if (!response.ok) throw new Error(`Ошибка API: ${response.status}`);

            const data = await response.json();
            
            if (!data.choices || !data.choices[0]) throw new Error('Неверный формат ответа от API');
            
            return data.choices[0].message.content;
            
        } catch (error) {
            console.error('Ошибка AI сервиса:', error);
            throw error;
        }
    }

    static generatePrompt(countryName, countryData) {
        return `Создай краткий и интересный туристический гид по стране ${countryName}. 
        
Основная информация:
- Столица: ${countryData.capital}
- Регион: ${countryData.region} 
- Население: ${countryData.population}
- Языки: ${countryData.languages}
- Валюта: ${countryData.currency}

Структурируй ответ так:
1. Краткое описание страны
2. Главные достопримечательности
3. Советы для туристов
4. Интересный факт

Будь информативным и дружелюбным! Отвечай на русском языке.`;
    }

    static getApiKey() { return localStorage.getItem('openrouter_api_key'); }

    static saveApiKey(apiKey) {
        if (apiKey && apiKey.trim()) {
            localStorage.setItem('openrouter_api_key', apiKey.trim());
            return true;
        }
        return false;
    }

    static clearApiKey() { localStorage.removeItem('openrouter_api_key'); }

    static hasApiKey() { return !!this.getApiKey(); }

    static testApiKey() {
        const apiKey = this.getApiKey();
        if (!apiKey) return { valid: false, message: 'API ключ не найден' };
        return { valid: true, message: 'API ключ сохранен' };
    }
}