class CountryService {
    static async searchCountry(query) {
        try {
            console.log("🔍 Ищем страну через API:", query);
            
            // Пробуем разные варианты API
            let response = await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                // Пробуем альтернативный эндпоинт
                response = await fetch(`https://restcountries.com/v3.1/translation/${encodeURIComponent(query)}`);
            }
            
            if (!response.ok) {
                throw new Error('Страна не найдена');
            }
            
            const data = await response.json();
            const countryData = data[0];
            
            return this.formatCountryData(countryData);
            
        } catch (error) {
            console.error("💥 Ошибка API:", error);
            return null;
        }
    }

    static formatCountryData(countryData) {
        const currencies = countryData.currencies ? Object.values(countryData.currencies) : [];
        const languages = countryData.languages ? Object.values(countryData.languages) : [];
        
        return {
            name: countryData.name?.common || 'Неизвестно',
            nativeName: Object.values(countryData.name?.nativeName || {})[0]?.common || countryData.name?.common || 'Неизвестно',
            capital: countryData.capital ? countryData.capital[0] : 'Не указано',
            region: countryData.region || 'Не указано',
            population: this.formatNumber(countryData.population),
            area: this.formatArea(countryData.area),
            languages: languages.length > 0 ? languages.join(', ') : 'Не указано',
            currency: currencies.length > 0 ? currencies[0].name : 'Не указано',
            flag: countryData.flags?.png || countryData.flags?.svg,
            description: this.generateDescription(countryData)
        };
    }

    static formatNumber(num) {
        if (num >= 1000000000) return (num / 1000000000).toFixed(1) + ' млрд';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + ' млн';
        if (num >= 1000) return (num / 1000).toFixed(1) + ' тыс';
        return num.toLocaleString();
    }

    static formatArea(area) {
        if (!area) return 'Неизвестно';
        if (area >= 1000000) return (area / 1000000).toFixed(1) + ' млн км²';
        return area.toLocaleString() + ' км²';
    }

    static generateDescription(countryData) {
        const facts = [];
        if (countryData.capital) facts.push(`столица - ${countryData.capital[0]}`);
        if (countryData.region) facts.push(`расположена в ${countryData.region}`);
        if (countryData.population > 100000000) facts.push('одна из самых населенных стран');
        if (countryData.area > 1000000) facts.push('обладает огромной территорией');
        if (countryData.subregion) facts.push(`в регионе ${countryData.subregion}`);
        
        return facts.length > 0 
            ? `Страна ${facts.join(', ')}.` 
            : 'Удивительная страна с богатой культурой и историей.';
    }
}