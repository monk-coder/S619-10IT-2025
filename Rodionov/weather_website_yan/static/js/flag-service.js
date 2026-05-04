// static/js/flag-service.js
// Универсальный сервис для загрузки флагов всех стран

class FlagService {
    constructor() {
        // Список CDN ресурсов для загрузки флагов (резервные варианты)
        this.cdnList = [
            {
                name: 'FlagCDN',
                getUrl: (isoCode) => `https://flagcdn.com/w320/${isoCode.toLowerCase()}.png`
            },
            {
                name: 'Flagpedia',
                getUrl: (isoCode) => `https://flagpedia.net/data/flags/h120/${isoCode.toLowerCase()}.png`
            },
            {
                name: 'Country Flags API',
                getUrl: (isoCode) => `https://countryflagsapi.com/png/${isoCode.toLowerCase()}`
            },
            {
                name: 'OpenMoji Flags',
                getUrl: (isoCode) => `https://cdn.jsdelivr.net/npm/openmoji@14.1.0/color/svg/${isoCode.toUpperCase()}.svg`
            }
        ];

        this.cache = new Map(); // Кэшируем загруженные флаги
    }

    // Загрузка флага с попыткой использовать несколько CDN
    async loadFlag(isoCode, countryName) {
        const normalizedCode = isoCode.toLowerCase();

        // Проверяем кэш
        if (this.cache.has(normalizedCode)) {
            return this.cache.get(normalizedCode);
        }

        // Пробуем загрузить с разных CDN
        for (let i = 0; i < this.cdnList.length; i++) {
            try {
                const url = this.cdnList[i].getUrl(normalizedCode);
                const isValid = await this.testImage(url);

                if (isValid) {
                    this.cache.set(normalizedCode, url);
                    console.log(`✓ Флаг загружен с ${this.cdnList[i].name}: ${normalizedCode}`);
                    return url;
                }
            } catch (error) {
                console.log(`✗ Не удалось загрузить с ${this.cdnList[i].name}`);
            }
        }

        // Если ни один CDN не сработал, возвращаем null
        console.warn(`⚠️ Не удалось загрузить флаг для ${countryName} (${normalizedCode})`);
        return null;
    }

    // Тестирование загрузки изображения
    testImage(url) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            img.src = url;
            setTimeout(() => resolve(false), 3000);
        });
    }

    // Быстрое получение URL (без проверки)
    getFlagUrl(isoCode) {
        return this.cdnList[0].getUrl(isoCode.toLowerCase());
    }
}

// Создаем глобальный экземпляр
const flagService = new FlagService();