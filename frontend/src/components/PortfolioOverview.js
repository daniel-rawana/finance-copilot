import React from 'react';

function PortfolioOverview({ selectedPeriod, onPeriodChange, portfolioData }) {
  const periods = ['1D', '1W', '1M', '3M', '1Y'];
  
  // Use real portfolio data if provided, otherwise use defaults
  const data = portfolioData || {
    totalValue: 0,
    holdingsCount: 0,
    uploadDate: null
  };
  
  // Calculate mock daily change for demo (in real app, this would come from market data)
  const dayChange = data.totalValue * 0.02; // 2% change for demo
  const dayChangePercent = 2.0;
  const isPositive = true;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Portfolio Overview</h2>
        
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {periods.map((period) => (
            <button
              key={period}
              onClick={() => onPeriodChange(period)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                selectedPeriod === period
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <div className="text-sm text-gray-500 mb-1">Total Value</div>
          <div className="text-3xl font-bold text-gray-900">
            ${data.totalValue.toLocaleString()}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {data.holdingsCount} holdings
          </div>
        </div>
        
        <div>
          <div className="text-sm text-gray-500 mb-1">Today's Change</div>
          <div className={`text-2xl font-semibold ${
            isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            {isPositive ? '+' : ''}${dayChange.toLocaleString()}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Demo data
          </div>
        </div>
        
        <div>
          <div className="text-sm text-gray-500 mb-1">Change %</div>
          <div className={`text-2xl font-semibold ${
            isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            {isPositive ? '+' : ''}{dayChangePercent}%
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Uploaded: {data.uploadDate ? new Date(data.uploadDate).toLocaleDateString() : 'Unknown'}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PortfolioOverview;
