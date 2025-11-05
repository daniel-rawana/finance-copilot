# Future Financial Analysis Features

This document outlines planned financial analysis features for Captura, including risk analysis, diversification scoring, and options hedging strategies.

---

## 1. Risk Analysis

### Overview
Calculate portfolio volatility and risk metrics to help users understand their portfolio's risk profile.

### Data Requirements

**Current Holdings Data:**
- `ticker` - Stock symbol
- `shares` - Number of shares
- `purchase_price` - Purchase price per share
- `purchase_date` - Date of purchase

**Required External Data:**
- Historical price data (daily closing prices for each ticker)
- Market data source: Alpha Vantage, Yahoo Finance, or IEX Cloud API
- Risk-free rate (10-year Treasury yield) - from Federal Reserve API
- Market benchmark data (S&P 500 daily returns) - for beta calculation

**Data Storage:**
```sql
-- New table for historical price data
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    close_price REAL NOT NULL,
    volume INTEGER,
    UNIQUE(ticker, date)
);

-- Index for performance
CREATE INDEX idx_price_history_ticker_date ON price_history(ticker, date);
```

### Formulas & Calculations

#### 1.1 Portfolio Volatility (Standard Deviation)

**Formula:**
```
Portfolio Volatility (σp) = √(Σ(wi² × σi²) + Σ(wi × wj × σi × σj × ρij))
```

Where:
- `wi` = weight of asset i in portfolio
- `σi` = standard deviation (volatility) of asset i
- `ρij` = correlation coefficient between assets i and j

**Simplified Calculation (if correlation data unavailable):**
```
Portfolio Volatility ≈ √(Σ(wi² × σi²))
```

**Implementation Steps:**
1. Calculate individual stock volatility (30-day, 90-day, 1-year)
2. Calculate portfolio weights
3. Calculate correlation matrix (if data available)
4. Compute portfolio volatility

**Code Structure:**
```python
def calculate_portfolio_volatility(holdings, historical_data, period='1Y'):
    """
    Calculate portfolio volatility.
    
    Args:
        holdings: List of portfolio holdings
        historical_data: Dict of {ticker: [prices]}
        period: '30D', '90D', '1Y'
    
    Returns:
        float: Portfolio volatility (annualized percentage)
    """
    # 1. Calculate individual stock volatilities
    stock_volatilities = {}
    for holding in holdings:
        ticker = holding['ticker']
        prices = historical_data.get(ticker, [])
        if len(prices) >= 30:
            returns = calculate_returns(prices)
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized
            stock_volatilities[ticker] = volatility
    
    # 2. Calculate portfolio weights
    total_value = sum(h['shares'] * h['current_price'] for h in holdings)
    weights = {
        h['ticker']: (h['shares'] * h['current_price']) / total_value
        for h in holdings
    }
    
    # 3. Calculate portfolio volatility
    portfolio_variance = 0
    for ticker, weight in weights.items():
        if ticker in stock_volatilities:
            portfolio_variance += (weight ** 2) * (stock_volatilities[ticker] ** 2)
    
    portfolio_volatility = np.sqrt(portfolio_variance)
    return portfolio_volatility
```

#### 1.2 Beta (Market Risk)

**Formula:**
```
β = Covariance(Stock Returns, Market Returns) / Variance(Market Returns)
```

**Implementation:**
```python
def calculate_portfolio_beta(holdings, historical_data, market_data):
    """
    Calculate portfolio beta.
    
    Returns:
        float: Portfolio beta (1.0 = market risk, >1.0 = higher risk, <1.0 = lower risk)
    """
    portfolio_returns = calculate_portfolio_returns(holdings, historical_data)
    market_returns = calculate_market_returns(market_data)
    
    covariance = np.cov(portfolio_returns, market_returns)[0][1]
    market_variance = np.var(market_returns)
    
    beta = covariance / market_variance
    return beta
```

#### 1.3 Value at Risk (VaR)

**Formula (Historical Method):**
```
VaR(95%) = Portfolio Value × (1 - Percentile of Returns at 5%)
```

**Implementation:**
```python
def calculate_var(holdings, historical_data, confidence_level=0.95):
    """
    Calculate Value at Risk.
    
    Args:
        confidence_level: 0.95 for 95% VaR, 0.99 for 99% VaR
    
    Returns:
        dict: VaR in dollars and percentage
    """
    portfolio_returns = calculate_portfolio_returns(holdings, historical_data)
    portfolio_value = sum(h['shares'] * h['current_price'] for h in holdings)
    
    percentile = (1 - confidence_level) * 100
    var_return = np.percentile(portfolio_returns, percentile)
    var_dollar = portfolio_value * abs(var_return)
    
    return {
        'var_dollar': var_dollar,
        'var_percentage': abs(var_return) * 100,
        'confidence_level': confidence_level
    }
```

#### 1.4 Sharpe Ratio

**Formula:**
```
Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
```

**Implementation:**
```python
def calculate_sharpe_ratio(holdings, historical_data, risk_free_rate):
    """
    Calculate Sharpe ratio.
    
    Returns:
        float: Sharpe ratio (higher is better, >1 is good, >2 is excellent)
    """
    portfolio_return = calculate_portfolio_return(holdings, historical_data)
    portfolio_volatility = calculate_portfolio_volatility(holdings, historical_data)
    
    sharpe = (portfolio_return - risk_free_rate) / (portfolio_volatility / 100)
    return sharpe
```

### API Endpoints

#### GET /api/portfolio/{portfolio_id}/risk-analysis
```json
{
  "portfolio_id": 1,
  "risk_metrics": {
    "volatility": {
      "30_day": 18.5,
      "90_day": 22.3,
      "1_year": 25.7,
      "unit": "annualized_percentage"
    },
    "beta": {
      "value": 1.15,
      "interpretation": "15% more volatile than market"
    },
    "var": {
      "95_percent": {
        "dollar": 3500.00,
        "percentage": 10.2
      },
      "99_percent": {
        "dollar": 5200.00,
        "percentage": 15.1
      }
    },
    "sharpe_ratio": {
      "value": 1.45,
      "interpretation": "Good risk-adjusted returns"
    },
    "max_drawdown": {
      "value": 15.3,
      "period": "1_year"
    }
  },
  "calculation_date": "2024-01-15",
  "period": "1_year"
}
```

#### POST /api/portfolio/{portfolio_id}/risk-analysis
```json
{
  "period": "1Y",  // "30D", "90D", "1Y", "3Y", "5Y"
  "confidence_level": 0.95  // For VaR calculation
}
```

---

## 2. Diversification Score

### Overview
Measure portfolio diversification across sectors, asset classes, and geographic regions on a 0-100 scale.

### Data Requirements

**Current Holdings Data:**
- `ticker` - Stock symbol
- `shares` - Number of shares
- `current_price` - Current market price

**Required External Data:**
- Sector classification for each ticker
- Industry classification
- Asset class (stocks, bonds, commodities, etc.)
- Geographic exposure (if international stocks)

**Data Storage:**
```sql
-- Enhanced holdings table
ALTER TABLE holdings ADD COLUMN sector TEXT;
ALTER TABLE holdings ADD COLUMN industry TEXT;
ALTER TABLE holdings ADD COLUMN asset_class TEXT DEFAULT 'stock';

-- New table for sector/industry mappings
CREATE TABLE ticker_metadata (
    ticker TEXT PRIMARY KEY,
    sector TEXT,
    industry TEXT,
    asset_class TEXT,
    market_cap TEXT,  -- 'large', 'mid', 'small'
    country TEXT DEFAULT 'US'
);
```

### Formulas & Calculations

#### 2.1 Sector Diversification Score

**Formula:**
```
Sector Diversification = 100 × (1 - Herfindahl Index)

Where:
Herfindahl Index = Σ(wi²)
wi = weight of sector i in portfolio
```

**Implementation:**
```python
def calculate_sector_diversification(holdings):
    """
    Calculate sector diversification score (0-100).
    
    Returns:
        dict: Diversification metrics
    """
    # 1. Calculate sector weights
    total_value = sum(h['shares'] * h['current_price'] for h in holdings)
    sector_weights = {}
    
    for holding in holdings:
        sector = holding.get('sector', 'Unknown')
        value = holding['shares'] * holding['current_price']
        sector_weights[sector] = sector_weights.get(sector, 0) + value
    
    # Normalize to percentages
    sector_weights = {k: v / total_value for k, v in sector_weights.items()}
    
    # 2. Calculate Herfindahl Index
    herfindahl_index = sum(weight ** 2 for weight in sector_weights.values())
    
    # 3. Calculate diversification score
    diversification_score = 100 * (1 - herfindahl_index)
    
    # 4. Calculate number of sectors
    num_sectors = len(sector_weights)
    
    # 5. Calculate concentration (max sector weight)
    max_sector_weight = max(sector_weights.values()) if sector_weights else 0
    
    return {
        'score': round(diversification_score, 2),
        'herfindahl_index': round(herfindahl_index, 4),
        'num_sectors': num_sectors,
        'sector_weights': {k: round(v * 100, 2) for k, v in sector_weights.items()},
        'max_sector_concentration': round(max_sector_weight * 100, 2),
        'interpretation': get_diversification_interpretation(diversification_score)
    }

def get_diversification_interpretation(score):
    """Interpret diversification score."""
    if score >= 80:
        return "Excellent diversification"
    elif score >= 60:
        return "Good diversification"
    elif score >= 40:
        return "Moderate diversification"
    elif score >= 20:
        return "Low diversification"
    else:
        return "Poor diversification - highly concentrated"
```

#### 2.2 Asset Class Diversification

**Implementation:**
```python
def calculate_asset_class_diversification(holdings):
    """
    Calculate diversification across asset classes.
    
    Returns:
        dict: Asset class diversification metrics
    """
    total_value = sum(h['shares'] * h['current_price'] for h in holdings)
    asset_class_weights = {}
    
    for holding in holdings:
        asset_class = holding.get('asset_class', 'stock')
        value = holding['shares'] * holding['current_price']
        asset_class_weights[asset_class] = asset_class_weights.get(asset_class, 0) + value
    
    # Normalize
    asset_class_weights = {k: v / total_value for k, v in asset_class_weights.items()}
    
    # Calculate diversification
    herfindahl = sum(weight ** 2 for weight in asset_class_weights.values())
    diversification = 100 * (1 - herfindahl)
    
    return {
        'score': round(diversification, 2),
        'asset_class_weights': {k: round(v * 100, 2) for k, v in asset_class_weights.items()},
        'num_asset_classes': len(asset_class_weights)
    }
```

#### 2.3 Overall Diversification Score

**Formula:**
```
Overall Score = (Sector Score × 0.5) + (Asset Class Score × 0.3) + (Holding Count Score × 0.2)

Where:
Holding Count Score = min(100, (num_holdings / 20) × 100)
```

**Implementation:**
```python
def calculate_overall_diversification_score(holdings):
    """
    Calculate overall diversification score (0-100).
    
    Returns:
        dict: Comprehensive diversification analysis
    """
    sector_div = calculate_sector_diversification(holdings)
    asset_class_div = calculate_asset_class_diversification(holdings)
    
    # Holding count score
    num_holdings = len(holdings)
    holding_count_score = min(100, (num_holdings / 20) * 100)
    
    # Weighted overall score
    overall_score = (
        sector_div['score'] * 0.5 +
        asset_class_div['score'] * 0.3 +
        holding_count_score * 0.2
    )
    
    return {
        'overall_score': round(overall_score, 2),
        'sector_diversification': sector_div,
        'asset_class_diversification': asset_class_div,
        'holding_count_score': round(holding_count_score, 2),
        'num_holdings': num_holdings,
        'recommendations': generate_diversification_recommendations(
            overall_score, sector_div, asset_class_div
        )
    }

def generate_diversification_recommendations(overall_score, sector_div, asset_class_div):
    """Generate recommendations for improving diversification."""
    recommendations = []
    
    if overall_score < 50:
        recommendations.append("Consider adding holdings from different sectors")
    
    if sector_div['max_sector_concentration'] > 40:
        recommendations.append(f"Portfolio is heavily concentrated in one sector ({sector_div['max_sector_concentration']:.1f}%)")
    
    if sector_div['num_sectors'] < 5:
        recommendations.append("Add holdings from more sectors for better diversification")
    
    if asset_class_div['num_asset_classes'] == 1:
        recommendations.append("Consider adding bonds or other asset classes")
    
    return recommendations
```

### API Endpoints

#### GET /api/portfolio/{portfolio_id}/diversification
```json
{
  "portfolio_id": 1,
  "diversification": {
    "overall_score": 72.5,
    "interpretation": "Good diversification",
    "sector_diversification": {
      "score": 75.3,
      "num_sectors": 6,
      "sector_weights": {
        "Technology": 35.2,
        "Healthcare": 20.1,
        "Financial Services": 15.8,
        "Consumer Cyclical": 12.5,
        "Energy": 10.2,
        "Industrials": 6.2
      },
      "max_sector_concentration": 35.2
    },
    "asset_class_diversification": {
      "score": 30.0,
      "asset_class_weights": {
        "stock": 100.0
      },
      "num_asset_classes": 1
    },
    "holding_count_score": 85.0,
    "num_holdings": 17,
    "recommendations": [
      "Consider adding bonds or other asset classes",
      "Portfolio is heavily concentrated in Technology sector (35.2%)"
    ]
  },
  "calculation_date": "2024-01-15"
}
```

---

## 3. Options Hedging Strategies

### Overview
Framework for suggesting protective put or covered call strategies to hedge portfolio risk.

### Data Requirements

**Current Holdings Data:**
- `ticker` - Stock symbol
- `shares` - Number of shares
- `purchase_price` - Purchase price per share
- `current_price` - Current market price

**Required External Data:**
- Options chain data (strikes, expiration dates, premiums)
- Implied volatility for each option
- Greeks (Delta, Gamma, Theta, Vega)
- Options data source: CBOE, IEX Cloud, or Alpha Vantage

**Data Storage:**
```sql
-- Options data table
CREATE TABLE options_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    option_type TEXT NOT NULL,  -- 'call' or 'put'
    strike_price REAL NOT NULL,
    expiration_date DATE NOT NULL,
    bid_price REAL,
    ask_price REAL,
    last_price REAL,
    volume INTEGER,
    open_interest INTEGER,
    implied_volatility REAL,
    delta REAL,
    gamma REAL,
    theta REAL,
    vega REAL,
    data_date DATE NOT NULL,
    UNIQUE(ticker, option_type, strike_price, expiration_date, data_date)
);

-- User hedging strategies
CREATE TABLE hedging_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    holding_id INTEGER NOT NULL,
    strategy_type TEXT NOT NULL,  -- 'protective_put', 'covered_call'
    option_ticker TEXT NOT NULL,
    strike_price REAL NOT NULL,
    expiration_date DATE NOT NULL,
    premium_paid REAL,
    premium_received REAL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
    FOREIGN KEY (holding_id) REFERENCES holdings(id)
);
```

### Formulas & Calculations

#### 3.1 Protective Put Strategy

**Strategy Overview:**
Buy put options to protect against downside risk while maintaining upside potential.

**Formula:**
```
Protection Level = Strike Price / Current Stock Price
Cost of Protection = Put Premium / Stock Price
Breakeven = Current Stock Price - Put Premium
Max Loss = (Current Stock Price - Strike Price) + Put Premium
Max Gain = Unlimited (reduced by put premium)
```

**Implementation:**
```python
def suggest_protective_put(holding, options_data, target_protection=0.95):
    """
    Suggest protective put strategy.
    
    Args:
        holding: Holding dict with ticker, shares, current_price
        options_data: List of available put options
        target_protection: Desired protection level (0.95 = 95% of current price)
    
    Returns:
        dict: Recommended protective put strategy
    """
    ticker = holding['ticker']
    current_price = holding['current_price']
    shares = holding['shares']
    target_strike = current_price * target_protection
    
    # Find closest put option
    available_puts = [o for o in options_data if o['ticker'] == ticker and o['option_type'] == 'put']
    
    if not available_puts:
        return None
    
    # Find put with strike closest to target
    best_put = min(available_puts, key=lambda x: abs(x['strike_price'] - target_strike))
    
    strike = best_put['strike_price']
    premium = best_put['ask_price']  # Use ask price for buying
    expiration = best_put['expiration_date']
    
    # Calculate strategy metrics
    protection_level = strike / current_price
    cost_per_share = premium
    total_cost = premium * shares * 100  # Options are per 100 shares
    breakeven = current_price - premium
    max_loss = (current_price - strike) + premium
    
    # Calculate protection effectiveness
    protection_amount = (current_price - strike) * shares
    cost_percentage = (premium / current_price) * 100
    
    return {
        'strategy_type': 'protective_put',
        'ticker': ticker,
        'shares_protected': shares,
        'put_option': {
            'strike_price': strike,
            'premium': premium,
            'expiration_date': expiration,
            'contracts_needed': shares / 100  # 1 contract = 100 shares
        },
        'cost': {
            'per_share': premium,
            'total_cost': total_cost,
            'cost_percentage': round(cost_percentage, 2)
        },
        'protection': {
            'protection_level': round(protection_level * 100, 2),
            'protection_amount': protection_amount,
            'breakeven_price': round(breakeven, 2),
            'max_loss': round(max_loss, 2)
        },
        'risk_reward': {
            'downside_protected': True,
            'upside_maintained': True,
            'cost_impact': f"{cost_percentage:.2f}% of stock value"
        }
    }
```

#### 3.2 Covered Call Strategy

**Strategy Overview:**
Sell call options against existing stock holdings to generate income while limiting upside potential.

**Formula:**
```
Income Generated = Call Premium × Number of Contracts × 100
Breakeven = Purchase Price - Call Premium
Max Profit = (Strike Price - Purchase Price) + Call Premium
Max Loss = Purchase Price - Call Premium (if stock falls to zero)
Upside Cap = Strike Price
```

**Implementation:**
```python
def suggest_covered_call(holding, options_data, target_premium=0.02):
    """
    Suggest covered call strategy.
    
    Args:
        holding: Holding dict with ticker, shares, purchase_price, current_price
        options_data: List of available call options
        target_premium: Minimum premium as percentage of stock price (0.02 = 2%)
    
    Returns:
        dict: Recommended covered call strategy
    """
    ticker = holding['ticker']
    current_price = holding['current_price']
    purchase_price = holding['purchase_price']
    shares = holding['shares']
    
    # Find suitable call options
    available_calls = [
        o for o in options_data 
        if o['ticker'] == ticker and o['option_type'] == 'call'
        and o['strike_price'] >= current_price  # Out-of-the-money calls
    ]
    
    if not available_calls:
        return None
    
    # Filter by minimum premium requirement
    min_premium = current_price * target_premium
    suitable_calls = [o for o in available_calls if o['bid_price'] >= min_premium]
    
    if not suitable_calls:
        return None
    
    # Find best call (highest premium relative to strike)
    best_call = max(suitable_calls, key=lambda x: x['bid_price'] / x['strike_price'])
    
    strike = best_call['strike_price']
    premium = best_call['bid_price']  # Use bid price for selling
    expiration = best_call['expiration_date']
    
    # Calculate strategy metrics
    contracts = shares / 100
    total_premium = premium * contracts * 100
    income_percentage = (premium / current_price) * 100
    breakeven = purchase_price - premium
    max_profit = (strike - purchase_price) + premium
    max_loss = purchase_price - premium
    upside_cap = strike
    
    # Calculate ROI
    annualized_return = (premium / current_price) * (365 / days_to_expiration) * 100
    
    return {
        'strategy_type': 'covered_call',
        'ticker': ticker,
        'shares_covered': shares,
        'call_option': {
            'strike_price': strike,
            'premium': premium,
            'expiration_date': expiration,
            'contracts_to_sell': contracts
        },
        'income': {
            'premium_per_share': premium,
            'total_premium': total_premium,
            'income_percentage': round(income_percentage, 2),
            'annualized_yield': round(annualized_return, 2)
        },
        'risk_reward': {
            'breakeven_price': round(breakeven, 2),
            'max_profit': round(max_profit, 2),
            'max_loss': round(max_loss, 2),
            'upside_cap': strike,
            'upside_cap_percentage': round((strike / current_price - 1) * 100, 2)
        },
        'considerations': [
            f"Stock will be called away if price exceeds ${strike}",
            f"Generates {income_percentage:.2f}% income on current position"
        ]
    }
```

#### 3.3 Strategy Comparison

**Implementation:**
```python
def compare_hedging_strategies(holding, options_data):
    """
    Compare protective put vs covered call strategies.
    
    Returns:
        dict: Comparison of both strategies
    """
    protective_put = suggest_protective_put(holding, options_data)
    covered_call = suggest_covered_call(holding, options_data)
    
    return {
        'ticker': holding['ticker'],
        'current_price': holding['current_price'],
        'strategies': {
            'protective_put': protective_put,
            'covered_call': covered_call
        },
        'recommendation': get_strategy_recommendation(holding, protective_put, covered_call)
    }

def get_strategy_recommendation(holding, protective_put, covered_call):
    """Recommend best strategy based on portfolio goals."""
    current_price = holding['current_price']
    purchase_price = holding['purchase_price']
    
    # If stock is at a loss, protective put makes more sense
    if current_price < purchase_price:
        return {
            'recommended': 'protective_put',
            'reason': 'Stock is below purchase price - protect downside'
        }
    
    # If stock has significant gains, covered call for income
    if current_price > purchase_price * 1.2:
        return {
            'recommended': 'covered_call',
            'reason': 'Stock has significant gains - generate income while protecting gains'
        }
    
    # Default recommendation
    return {
        'recommended': 'protective_put',
        'reason': 'General protection recommended for risk management'
    }
```

### API Endpoints

#### GET /api/portfolio/{portfolio_id}/hedging-strategies
```json
{
  "portfolio_id": 1,
  "strategies": [
    {
      "ticker": "AAPL",
      "shares": 50,
      "current_price": 175.50,
      "protective_put": {
        "strategy_type": "protective_put",
        "put_option": {
          "strike_price": 165.00,
          "premium": 2.50,
          "expiration_date": "2024-02-16",
          "contracts_needed": 0.5
        },
        "cost": {
          "total_cost": 125.00,
          "cost_percentage": 1.42
        },
        "protection": {
          "protection_level": 94.02,
          "protection_amount": 525.00,
          "max_loss": 13.00
        }
      },
      "covered_call": {
        "strategy_type": "covered_call",
        "call_option": {
          "strike_price": 180.00,
          "premium": 3.20,
          "expiration_date": "2024-02-16",
          "contracts_to_sell": 0.5
        },
        "income": {
          "total_premium": 160.00,
          "income_percentage": 1.82,
          "annualized_yield": 12.5
        },
        "risk_reward": {
          "max_profit": 760.00,
          "upside_cap": 180.00
        }
      },
      "recommendation": {
        "recommended": "protective_put",
        "reason": "General protection recommended for risk management"
      }
    }
  ]
}
```

#### POST /api/portfolio/{portfolio_id}/hedging-strategies
```json
{
  "holding_id": 1,
  "strategy_type": "protective_put",
  "target_protection": 0.95
}
```

#### POST /api/portfolio/{portfolio_id}/hedging-strategies/apply
```json
{
  "holding_id": 1,
  "strategy_type": "protective_put",
  "option_ticker": "AAPL240216P00165000",
  "strike_price": 165.00,
  "expiration_date": "2024-02-16",
  "premium_paid": 2.50
}
```

---

## Implementation Priority

### Phase 1: Risk Analysis (High Priority)
- Portfolio volatility calculation
- Beta calculation
- Basic VaR calculation
- **Timeline**: 2-3 weeks
- **Dependencies**: Historical price data API integration

### Phase 2: Diversification Score (Medium Priority)
- Sector diversification scoring
- Asset class diversification
- Overall diversification score
- **Timeline**: 1-2 weeks
- **Dependencies**: Sector/industry classification data

### Phase 3: Options Hedging (Lower Priority)
- Protective put suggestions
- Covered call suggestions
- Strategy comparison
- **Timeline**: 3-4 weeks
- **Dependencies**: Options data API integration, options pricing models

---

## External API Requirements

### Historical Price Data
- **Alpha Vantage**: Free tier available, 5 calls/minute
- **Yahoo Finance**: Free but rate-limited
- **IEX Cloud**: Paid service, more reliable

### Options Data
- **CBOE**: Official options data (paid)
- **IEX Cloud**: Options chains available
- **Alpha Vantage**: Limited options data

### Market Data
- **Federal Reserve API**: Risk-free rate (10-year Treasury)
- **Alpha Vantage**: Market indices (S&P 500)

---

## Database Schema Updates

See individual sections above for table structures. Key additions:
- `price_history` table for historical stock prices
- `ticker_metadata` table for sector/industry classifications
- `options_data` table for options chain data
- `hedging_strategies` table for user hedging positions

---

## Testing Considerations

1. **Risk Analysis**: Test with various portfolio sizes and compositions
2. **Diversification**: Test edge cases (single stock, all same sector, etc.)
3. **Options Hedging**: Validate options pricing calculations against market data
4. **Performance**: Historical data calculations may be computationally intensive
5. **Data Freshness**: Ensure real-time data updates for accurate calculations

---

## Notes

- All calculations should be clearly documented with source formulas
- Consider caching for expensive calculations (volatility, correlations)
- Provide user-friendly explanations of all metrics
- Include disclaimers that these are educational tools, not financial advice
