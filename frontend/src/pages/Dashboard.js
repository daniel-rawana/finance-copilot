import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import PortfolioOverview from '../components/PortfolioOverview';
import InvestmentChart from '../components/InvestmentChart';
import AdvisorChat from '../components/AdvisorChat';
import HoldingsSection from '../components/HoldingsSection';
import MarketNews from '../components/MarketNews';
import { newsItems, chartDataByPeriod } from '../data/mockData';
import './Dashboard.css';

function Dashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState('1M');
  const [portfolio, setPortfolio] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch portfolio data from backend
  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch portfolio data from backend
        const response = await fetch('http://127.0.0.1:5000/api/portfolio/2');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        setPortfolio(data.portfolio);
        setHoldings(data.holdings);
        
        console.log('Portfolio data loaded:', data);
        
      } catch (err) {
        console.error('Error fetching portfolio data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        
        {/* Navigation Menu */}
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Link 
                  to="/" 
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Home
                </Link>
                <span className="text-gray-300">|</span>
                <Link 
                  to="/hello" 
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium"
                >
                  Upload New Portfolio
                </Link>
              </div>
              
              <div className="text-sm text-gray-500">
                Portfolio Dashboard
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading portfolio data...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        
        {/* Navigation Menu */}
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Link 
                  to="/" 
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Home
                </Link>
                <span className="text-gray-300">|</span>
                <Link 
                  to="/hello" 
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium"
                >
                  Upload New Portfolio
                </Link>
              </div>
              
              <div className="text-sm text-gray-500">
                Portfolio Dashboard
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
                <div className="flex items-center mb-4">
                  <svg className="w-8 h-8 text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="text-lg font-medium text-red-800">Error Loading Portfolio</h3>
                </div>
                <p className="text-red-700 mb-4">{error}</p>
                <button 
                  onClick={() => window.location.reload()} 
                  className="bg-red-500 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-600 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // No portfolio data
  if (!portfolio || !holdings.length) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        
        {/* Navigation Menu */}
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Link 
                  to="/" 
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Home
                </Link>
                <span className="text-gray-300">|</span>
                <Link 
                  to="/hello" 
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium"
                >
                  Upload New Portfolio
                </Link>
              </div>
              
              <div className="text-sm text-gray-500">
                Portfolio Dashboard
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 max-w-md">
                <div className="flex items-center mb-4">
                  <svg className="w-8 h-8 text-yellow-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <h3 className="text-lg font-medium text-yellow-800">No Portfolio Data</h3>
                </div>
                <p className="text-yellow-700 mb-4">No portfolio data found. Please upload a portfolio first.</p>
                <Link 
                  to="/hello"
                  className="inline-flex items-center bg-yellow-500 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-yellow-600 transition-colors"
                >
                  Upload Portfolio
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Transform real holdings data to match component expectations
  const transformedHoldings = holdings.map((holding, index) => ({
    id: holding.id,
    symbol: holding.ticker,
    name: holding.company_name || holding.ticker, // Use company_name if available, fallback to ticker
    shares: holding.shares,
    price: holding.purchase_price,
    change: 0, // Real-time price changes would come from a market data API
    changePercent: 0,
    value: holding.shares * holding.purchase_price,
    weight: 0 // Will be calculated based on total portfolio value
  }));

  // Calculate portfolio totals and weights
  const totalValue = transformedHoldings.reduce((sum, holding) => sum + holding.value, 0);
  const holdingsWithWeights = transformedHoldings.map(holding => ({
    ...holding,
    weight: totalValue > 0 ? (holding.value / totalValue) * 100 : 0
  }));

  // Generate chart data based on real holdings (simplified for demo)
  const generateChartData = (period) => {
    const baseValue = totalValue;
    const dataPoints = period === '1D' ? 14 : period === '1W' ? 7 : period === '1M' ? 4 : 3;
    
    return Array.from({ length: dataPoints }, (_, i) => ({
      time: period === '1D' ? `${9 + i}:30` : 
            period === '1W' ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i] :
            period === '1M' ? `Week ${i + 1}` : `Month ${i + 1}`,
      value: baseValue + (Math.random() - 0.5) * baseValue * 0.1 // Simulate some variation
    }));
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      
      {/* Navigation Menu */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                to="/" 
                className="text-sm text-gray-600 hover:text-gray-900 font-medium flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Home
              </Link>
              <span className="text-gray-300">|</span>
              <Link 
                to="/hello" 
                className="text-sm text-gray-600 hover:text-gray-900 font-medium"
              >
                Upload New Portfolio
              </Link>
            </div>
            
            <div className="text-sm text-gray-500">
              Portfolio Dashboard - {portfolio.file_name}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <PortfolioOverview
              selectedPeriod={selectedPeriod}
              onPeriodChange={setSelectedPeriod}
              portfolioData={{
                totalValue: totalValue,
                holdingsCount: holdings.length,
                uploadDate: portfolio.upload_date
              }}
            />

            <InvestmentChart data={generateChartData(selectedPeriod)} />

            <HoldingsSection holdings={holdingsWithWeights} />

            <MarketNews news={newsItems} />
          </div>

          <div className="lg:col-span-1">
            <AdvisorChat portfolioId={portfolio.id} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;

