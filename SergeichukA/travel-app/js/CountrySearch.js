class CountrySearch {
    static async search(query) {
        const normalizedQuery = query.trim();
        
        try {
            CountrySearch.showLoading();
            const countryData = await CountryService.searchCountry(normalizedQuery);
            CountrySearch.hideLoading();
            
            return countryData;
            
        } catch (error) {
            console.error('Ошибка поиска:', error);
            CountrySearch.hideLoading();
            return null;
        }
    }
    
    static renderCountry(countryData) {
        const country = new Country(countryData);
        document.getElementById('results').innerHTML = country.render();
        document.getElementById('errorMessage').style.display = 'none';
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