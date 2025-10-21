class CountryService {
    static async searchCountry(query) {
        try {
            const response = await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(query)}`);
            
            if (!response.ok) throw new Error('Страна не найдена');
            
            const data = await response.json();
            return this.formatCountryData(data[0]);
            
        } catch (error) {
            console.error('Ошибка API:', error);
            throw error;
        }
    }

    static formatCountryData(countryData) {
        const currencies = countryData.currencies ? Object.values(countryData.currencies) : [];
        const currency = currencies.length > 0 ? `${currencies[0].name} (${currencies[0].symbol || ''})` : 'Не указано';
        
        const languages = countryData.languages ? Object.values(countryData.languages) : [];
        
        const nativeNameObj = countryData.name?.nativeName || {};
        const nativeNameKey = Object.keys(nativeNameObj)[0];
        const nativeName = nativeNameKey ? nativeNameObj[nativeNameKey]?.common : countryData.name?.common;
        
        return {
            name: countryData.name?.common || 'Неизвестно',
            nativeName: nativeName || countryData.name?.common || 'Неизвестно',
            capital: countryData.capital ? countryData.capital[0] : 'Не указано',
            region: countryData.region || 'Не указано',
            population: this.formatNumber(countryData.population),
            area: this.formatArea(countryData.area),
            languages: languages.length > 0 ? languages.join(', ') : 'Не указано',
            currency: currency,
            flag: countryData.flags?.png || countryData.flags?.svg,
            description: this.generateDescription(countryData)
        };
    }

    static formatNumber(num) {
        if (!num) return 'Неизвестно';
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
        if (countryData.population > 50000000) facts.push('крупная по населению');
        if (countryData.area > 1000000) facts.push('обладает большой территорией');
        
        return facts.length > 0 
            ? `Страна ${facts.join(', ')}.` 
            : 'Интересная страна для посещения.';
    }
}