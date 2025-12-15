class CountrySearch {
    static async search(query) {
        const normalizedQuery = query.toLowerCase().trim();
        
        CountrySearch.showLoading();
        try {
            const country = await CountryService.searchCountry(normalizedQuery);
            CountrySearch.hideLoading();
            
            if (country) {
                CountrySearch.renderCountry(country);
            } else {
                CountrySearch.showError();
            }
        } catch (error) {
            CountrySearch.hideLoading();
            CountrySearch.showError();
        }
    }
    
    static renderCountry(countryData) {
        const html = this.createCountryHTML(countryData);
        document.getElementById('results').innerHTML = html;
        document.getElementById('errorMessage').style.display = 'none';
    }
    
    static createCountryHTML(countryData) {
        return `
            <div class="country-card">
                <img src="${countryData.flag}" alt="Флаг ${countryData.name}" class="country-flag">
                <div class="country-info">
                    <h2 class="country-name">
                        <i class="fas fa-flag"></i> ${countryData.name}
                        <small>(${countryData.nativeName})</small>
                    </h2>
                    
                    <div class="country-detail">
                        <i class="fas fa-landmark"></i>
                        <strong>Столица:</strong> ${countryData.capital}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-globe-europe"></i>
                        <strong>Регион:</strong> ${countryData.region}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-users"></i>
                        <strong>Население:</strong> ${countryData.population}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-ruler-combined"></i>
                        <strong>Площадь:</strong> ${countryData.area}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-money-bill-wave"></i>
                        <strong>Валюта:</strong> ${countryData.currency}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-language"></i>
                        <strong>Языки:</strong> ${countryData.languages}
                    </div>
                    
                    <div style="margin-top: 1.5rem; padding: 1.5rem; background: #f8f9fa; border-radius: 12px;">
                        <p>${countryData.description}</p>
                    </div>
                    
                    <button class="add-to-wishlist" onclick="Wishlist.add('${countryData.name}')" style="margin-top: 2rem; background: var(--gradient); padding: 14px 28px; font-size: 1.1rem;">
                        <i class="fas fa-heart"></i> Добавить в вишлист
                    </button>
                </div>
            </div>
        `;
    }
    
    static showError() {
        document.getElementById('results').innerHTML = '';
        document.getElementById('errorMessage').style.display = 'block';
    }
    
    static showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('errorMessage').style.display = 'none';
    }
    
    static hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }
}
