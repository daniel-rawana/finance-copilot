# Captura Data Flow Documentation

This document illustrates the complete data flow for portfolio CSV upload and management in the Captura application.

## CSV Upload and Portfolio Management Flow

```mermaid
graph TD
    A[User] -->|1. Upload CSV File| B[Frontend Upload Page]
    B -->|2. FormData with CSV| C[POST /api/upload]
    C -->|3. File Processing| D[Backend Flask Route]
    D -->|4. Read CSV Content| E[CSV Parser]
    E -->|5. Validate Headers| F{Headers Valid?}
    F -->|No| G[Return Error Response]
    F -->|Yes| H[Parse Each Row]
    H -->|6. Validate Data Types| I{Data Valid?}
    I -->|No| J[Collect Validation Errors]
    I -->|Yes| K[Create Holdings List]
    J --> L[Return Error Response]
    K -->|7. Insert Portfolio| M[Database Manager]
    M -->|8. Create Portfolio Record| N[SQLite: portfolios table]
    N -->|9. Get Portfolio ID| O[Insert Holdings]
    O -->|10. Bulk Insert Holdings| P[SQLite: holdings table]
    P -->|11. Success Response| Q[Return JSON Success]
    Q -->|12. Display Success| R[Frontend Upload Page]
    R -->|13. Navigate to Dashboard| S[Dashboard Page]
    S -->|14. Fetch Portfolio Data| T[GET /api/portfolio/:id]
    T -->|15. Query Database| U[Database Manager]
    U -->|16. Get Portfolio + Holdings| V[SQLite Query]
    V -->|17. Return Portfolio Data| W[Frontend Dashboard]
    W -->|18. Display Portfolio| X[Portfolio Overview]
    W -->|19. Display Holdings| Y[Holdings Table]
    W -->|20. Display Chart| Z[Investment Chart]
    W -->|21. AI Chat Ready| AA[Advisor Chat]

    %% Error Handling
    G -->|Error Display| R
    L -->|Error Display| R

    %% Styling
    classDef userAction fill:#e1f5fe
    classDef frontend fill:#f3e5f5
    classDef backend fill:#e8f5e8
    classDef database fill:#fff3e0
    classDef error fill:#ffebee
    classDef success fill:#e8f5e8

    class A userAction
    class B,R,S,W,X,Y,Z,AA frontend
    class C,D,E,M,T,U backend
    class N,P,V database
    class G,L error
    class Q success
```

## Detailed Component Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant P as CSV Parser
    participant D as Database
    participant DB as SQLite

    U->>F: 1. Upload CSV file
    F->>B: 2. POST /api/upload (FormData)
    
    B->>P: 3. Parse CSV content
    P->>P: 4. Validate headers
    P->>P: 5. Validate each row
    P-->>B: 6. Return parsed data + errors
    
    alt Validation Success
        B->>D: 7. insert_portfolio(user_id, filename)
        D->>DB: 8. INSERT INTO portfolios
        DB-->>D: 9. Return portfolio_id
        D->>D: 10. insert_holdings(portfolio_id, holdings)
        D->>DB: 11. INSERT INTO holdings (bulk)
        DB-->>D: 12. Return success
        D-->>B: 13. Return success
        B-->>F: 14. Return JSON success response
        F->>F: 15. Display success message
        F->>F: 16. Navigate to dashboard
        F->>B: 17. GET /api/portfolio/:id
        B->>D: 18. get_portfolio_by_id()
        D->>DB: 19. SELECT portfolio + holdings
        DB-->>D: 20. Return portfolio data
        D-->>B: 21. Return portfolio data
        B-->>F: 22. Return portfolio JSON
        F->>F: 23. Display portfolio dashboard
    else Validation Error
        P-->>B: Return validation errors
        B-->>F: Return error response
        F->>F: Display error message
    end
```

## Database Schema Integration

```mermaid
erDiagram
    PORTFOLIOS {
        int id PK
        string user_id
        datetime upload_date
        string file_name
    }
    
    HOLDINGS {
        int id PK
        int portfolio_id FK
        string ticker
        real shares
        real purchase_price
        date purchase_date
        datetime timestamp
    }
    
    PORTFOLIOS ||--o{ HOLDINGS : "has many"
```

## API Endpoints Flow

```mermaid
graph LR
    A[Frontend] -->|POST /api/upload| B[Upload Endpoint]
    A -->|GET /api/portfolio/:id| C[Portfolio Endpoint]
    A -->|GET /api/portfolios/user/:id| D[User Portfolios Endpoint]
    
    B --> E[CSV Parser]
    B --> F[Database Manager]
    
    C --> F
    D --> F
    
    F --> G[SQLite Database]
    
    E --> H[Validation Results]
    F --> I[Database Results]
    
    H --> J[JSON Response]
    I --> J
```

## Error Handling Flow

```mermaid
graph TD
    A[CSV Upload] --> B{File Valid?}
    B -->|No| C[File Error]
    B -->|Yes| D{Headers Valid?}
    D -->|No| E[Header Error]
    D -->|Yes| F{Data Valid?}
    F -->|No| G[Data Validation Error]
    F -->|Yes| H{Database Insert?}
    H -->|No| I[Database Error]
    H -->|Yes| J[Success]
    
    C --> K[Return Error Response]
    E --> K
    G --> K
    I --> K
    J --> L[Return Success Response]
    
    K --> M[Display Error in Frontend]
    L --> N[Display Success + Navigate]
```

## File Structure Integration

```
backend/
├── app.py                 # Flask application
├── routes/
│   └── api_routes.py     # API endpoints
├── utils/
│   ├── csv_parser.py     # CSV parsing & validation
│   ├── database.py       # Database operations
│   └── file_utils.py     # File handling utilities
├── database_schema.sql   # Database schema
├── captura.db           # SQLite database (auto-created)
└── DATA_FLOW.md         # This documentation

frontend/
├── src/
│   ├── pages/
│   │   ├── HelloPage.js  # Upload page
│   │   └── Dashboard.js  # Portfolio dashboard
│   └── components/       # Dashboard components
```

## Key Data Transformations

1. **CSV File** → **Parsed Holdings List**
   - Raw CSV content → Validated dictionary objects
   - Type conversion (strings → numbers, dates)
   - Business rule validation

2. **Holdings List** → **Database Records**
   - Portfolio metadata creation
   - Bulk holdings insertion
   - Foreign key relationships

3. **Database Records** → **Dashboard Display**
   - Aggregated portfolio statistics
   - Holdings table data
   - Chart data preparation

## Performance Considerations

- **Bulk Insert**: Holdings are inserted in a single transaction
- **Indexing**: Database indexes on frequently queried fields
- **Connection Management**: Context managers for safe database connections
- **Error Recovery**: Graceful handling of partial failures
- **Validation**: Early validation to prevent unnecessary database operations
