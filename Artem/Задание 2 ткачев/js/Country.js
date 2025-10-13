class Country {
    constructor(data) {
        this.data = data;
    }
    
    render() {
        return `
            <div class="country-card">
                <img src="${this.data.flag}" alt="Флаг ${this.data.name}" class="country-flag">
                <div class="country-info">
                    <h2 class="country-name">
                        <i class="fas fa-flag"></i>${this.data.name}
                        <small>(${this.data.nativeName})</small>
                    </h2>
                    
                    <div class="country-detail">
                        <i class="fas fa-landmark"></i>
                        <strong>Столица:</strong> ${this.data.capital}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-globe-europe"></i>
                        <strong>Регион:</strong> ${this.data.region}
                    </div>
                    
                    <div class="country-stats">
                        <div class="stat-item">
                            <i class="fas fa-users"></i>
                            <h4>Население</h4>
                            <span>${this.data.population}</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-money-bill-wave"></i>
                            <h4>Валюта</h4>
                            <span>${this.data.currency}</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-language"></i>
                            <h4>Язык</h4>
                            <span>${this.data.languages}</span>
                        </div>
                    </div>
                    
                    <div class="country-description">
                        <p>${this.data.description}</p>
                    </div>
                    
                    <button class="add-to-wishlist" onclick="Wishlist.add('${this.data.name}')">
                        <i class="fas fa-heart"></i> Добавить в вишлист
                    </button>
                </div>
            </div>
        `;
    }
}