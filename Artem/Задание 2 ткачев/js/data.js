// Локальный кэш стран
const countries = {};

class CountryCache {
    static set(countryName, countryData) {
        const normalizedName = countryName.toLowerCase().trim();
        countries[normalizedName] = {
            ...countryData,
            cachedAt: Date.now()
        };
        
        // Сохраняем в localStorage для persistence (максимум 50 стран)
        try {
            const cacheKey = `country_${normalizedName}`;
            localStorage.setItem(cacheKey, JSON.stringify(countries[normalizedName]));
            
            // Управляем размером кэша
            CountryCache.cleanupOldCache();
        } catch (error) {
            console.warn('Не удалось сохранить в localStorage:', error);
        }
    }
    
    static get(countryName) {
        const normalizedName = countryName.toLowerCase().trim();
        
        // Сначала проверяем memory cache
        if (countries[normalizedName]) {
            // Проверяем, не устарели ли данные (больше 24 часов)
            const cacheAge = Date.now() - countries[normalizedName].cachedAt;
            if (cacheAge < 24 * 60 * 60 * 1000) { // 24 часа
                return countries[normalizedName];
            } else {
                // Удаляем устаревшие данные
                delete countries[normalizedName];
                localStorage.removeItem(`country_${normalizedName}`);
            }
        }
        
        // Затем проверяем localStorage
        try {
            const cached = localStorage.getItem(`country_${normalizedName}`);
            if (cached) {
                const parsedData = JSON.parse(cached);
                const cacheAge = Date.now() - parsedData.cachedAt;
                
                if (cacheAge < 24 * 60 * 60 * 1000) {
                    countries[normalizedName] = parsedData;
                    return countries[normalizedName];
                } else {
                    localStorage.removeItem(`country_${normalizedName}`);
                }
            }
        } catch (error) {
            console.warn('Ошибка при чтении из localStorage:', error);
        }
        
        return null;
    }
    
    static getAllCachedCountries() {
        const cachedCountries = [];
        
        // Получаем из memory cache
        Object.keys(countries).forEach(key => {
            const cacheAge = Date.now() - countries[key].cachedAt;
            if (cacheAge < 24 * 60 * 60 * 1000) {
                cachedCountries.push(countries[key]);
            }
        });
        
        return cachedCountries;
    }
    
    static cleanupOldCache() {
        try {
            const cacheKeys = Object.keys(localStorage).filter(key => key.startsWith('country_'));
            
            // Если больше 50 записей, удаляем самые старые
            if (cacheKeys.length > 50) {
                const cacheEntries = cacheKeys.map(key => {
                    const data = JSON.parse(localStorage.getItem(key));
                    return { key, cachedAt: data.cachedAt };
                });
                
                // Сортируем по времени создания (старые сначала)
                cacheEntries.sort((a, b) => a.cachedAt - b.cachedAt);
                
                // Удаляем самые старые записи
                const toRemove = cacheEntries.slice(0, cacheEntries.length - 50);
                toRemove.forEach(entry => {
                    localStorage.removeItem(entry.key);
                    const countryName = entry.key.replace('country_', '');
                    delete countries[countryName];
                });
            }
        } catch (error) {
            console.warn('Ошибка при очистке кэша:', error);
        }
    }
    
    static clear() {
        // Очистка memory cache
        Object.keys(countries).forEach(key => delete countries[key]);
        
        // Очистка localStorage (только данные стран)
        try {
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('country_')) {
                    localStorage.removeItem(key);
                }
            });
        } catch (error) {
            console.warn('Ошибка при очистке localStorage:', error);
        }
        
        console.log('Кэш стран полностью очищен');
    }
    
    static getStats() {
        const memoryCacheCount = Object.keys(countries).length;
        let localStorageCount = 0;
        
        try {
            localStorageCount = Object.keys(localStorage).filter(key => 
                key.startsWith('country_')
            ).length;
        } catch (error) {
            console.warn('Не удалось получить статистику localStorage:', error);
        }
        
        return {
            memoryCacheCount,
            localStorageCount,
            total: memoryCacheCount + localStorageCount
        };
    }
}

// Инициализация - загрузка кэша из localStorage при запуске
document.addEventListener('DOMContentLoaded', function() {
    try {
        const cacheKeys = Object.keys(localStorage).filter(key => key.startsWith('country_'));
        
        cacheKeys.forEach(key => {
            try {
                const data = JSON.parse(localStorage.getItem(key));
                const countryName = key.replace('country_', '');
                
                // Проверяем актуальность данных
                const cacheAge = Date.now() - data.cachedAt;
                if (cacheAge < 24 * 60 * 60 * 1000) {
                    countries[countryName] = data;
                } else {
                    // Удаляем устаревшие данные
                    localStorage.removeItem(key);
                }
            } catch (error) {
                console.warn(`Ошибка при загрузке кэша для ${key}:`, error);
                localStorage.removeItem(key);
            }
        });
        
        console.log(`Загружено ${Object.keys(countries).length} стран в кэш`);
    } catch (error) {
        console.warn('Ошибка при инициализации кэша:', error);
    }
});
