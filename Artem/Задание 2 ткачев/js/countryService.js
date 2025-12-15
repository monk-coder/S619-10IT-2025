class CountryService {
    // 🎯 Кэш в памяти для быстрого доступа
    static cache = new Map();
    
    // ⭐ Популярные страны для предзагрузки
    static popularCountries = ['россия', 'сша', 'франция', 'германия', 'япония'];

    static async searchCountry(query) {
        const normalizedQuery = query.toLowerCase().trim();
        
        // 1. 🔍 ПРОВЕРЯЕМ КЭШ ПЕРВЫМ
        if (this.cache.has(normalizedQuery)) {
            console.log('✅ Данные из кэша:', normalizedQuery);
            return this.cache.get(normalizedQuery);
        }
        
        // 2. 🌐 ЕСЛИ НЕТ В КЭШЕ - ИДЕМ В API
        console.log('🌐 Запрос к API:', normalizedQuery);
        
        try {
            // Пробуем разные варианты API
            let response = await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(normalizedQuery)}`);
            
            if (!response.ok) {
                // Пробуем альтернативный эндпоинт
                response = await fetch(`https://restcountries.com/v3.1/translation/${encodeURIComponent(normalizedQuery)}`);
            }
            
            if (!response.ok) {
                throw new Error('Страна не найдена');
            }
            
            const data = await response.json();
            const countryData = this.formatCountryData(data[0]);
            
            // 3. 💾 СОХРАНЯЕМ В КЭШ
            this.cache.set(normalizedQuery, countryData);
            console.log('💾 Сохранено в кэш:', normalizedQuery);
            
            // 4. 📦 ОГРАНИЧИВАЕМ РАЗМЕР КЭША (макс. 20 стран)
            if (this.cache.size > 20) {
                const firstKey = this.cache.keys().next().value;
                this.cache.delete(firstKey);
                console.log('📦 Очищен старый кэш:', firstKey);
            }
            
            return countryData;
            
        } catch (error) {
            console.error('💥 Ошибка API:', error);
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
        if (num >= 1000000) return (num / 1000000000).toFixed(1) + ' млн';
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
        
        return facts.length > 0 
            ? `Страна ${facts.join(', ')}.` 
            : 'Удивительная страна с богатой культурой и историей.';
    }

    // 🚀 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ УЛУЧШЕНИЯ
    static preloadPopularCountries() {
        // Предзагрузка популярных стран в фоне
        this.popularCountries.forEach(country => {
            setTimeout(() => {
                this.searchCountry(country).then(data => {
                    if (data) {
                        console.log('🔮 Предзагружена популярная страна:', country);
                    }
                });
            }, 1000);
        });
    }

    static clearCache() {
        this.cache.clear();
        console.log('🗑️ Кэш полностью очищен');
    }

    static getCacheStats() {
        return {
            size: this.cache.size,
            countries: Array.from(this.cache.keys())
        };
    }
}
