import os
import logging
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.csv_parser import parse_portfolio_csv
from utils.database import insert_portfolio, insert_holdings, get_portfolio_by_id, get_holdings_by_portfolio, get_portfolio_summary
from utils.file_utils import allowed_file

# Ensure environment variables are loaded
# Try loading from backend directory first, then project root
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
load_dotenv(os.path.join(backend_dir, '.env'))  # Try backend/.env first
load_dotenv(os.path.join(project_root, '.env'))  # Then try project root .env
from utils.advisor_prompt import generate_advisor_prompt

from utils.finance_functions import (
    get_total_unrealized_gain_loss,
    get_daily_change,
    get_portfolio_weights
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route("/hello")
def hello():
    return jsonify({"message": "Hello from Flask backend!"})

@api_bp.route("/upload", methods=['POST'])
def upload_portfolio():
    """
    Upload and process portfolio CSV file.
    Parses CSV, validates data, and saves to database.
    """
    try:
        # Validate file presence
        if 'file' not in request.files:
            logger.warning("Upload request missing file")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.warning("Upload request with empty filename")
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type uploaded: {file.filename}")
            return jsonify({"error": "Invalid file type. Only CSV files are allowed"}), 400
        
        # Get user ID from request (default to 'anonymous' if not provided)
        user_id = request.form.get('user_id', 'anonymous')
        filename = secure_filename(file.filename)
        
        logger.info(f"Processing upload for user {user_id}: {filename}")
        
        # Read file content
        try:
            csv_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            logger.error(f"Failed to decode file {filename} as UTF-8")
            return jsonify({"error": "File encoding error. Please ensure the file is UTF-8 encoded"}), 400
        
        # Parse CSV using parser
        logger.info(f"Parsing CSV content for {filename}")
        parse_result = parse_portfolio_csv(csv_content, filename)
        
        # Check for parsing errors
        if not parse_result['success']:
            logger.error(f"CSV parsing failed for {filename}: {parse_result['errors']}")
            return jsonify({
                "error": "CSV validation failed",
                "details": parse_result['errors'],
                "warnings": parse_result['warnings']
            }), 400
        
        # Analyze portfolio with finance functions
        try:
            logger.info(f"Analyzing portfolio with {len(parse_result['data'])} holdings")
            
            # Your csv_parser already returns the right format!
            portfolio = parse_result['data']
            
            # Calculate the 3 metrics
            gains = get_total_unrealized_gain_loss(portfolio)
            daily = get_daily_change(portfolio)
            weights = get_portfolio_weights(portfolio)
            
            logger.info(f"Portfolio analysis complete: Total value ${weights['total_portfolio_value']:,.2f}")
            
        except Exception as analysis_error:
            logger.error(f"Portfolio analysis failed: {str(analysis_error)}")
            # Continue with upload even if analysis fails
            gains = None
            daily = None
            weights = None
        
        # Save to database
        try:
            logger.info(f"Inserting portfolio for user {user_id}")
            portfolio_id = insert_portfolio(user_id, filename)
            
            logger.info(f"Inserting {len(parse_result['data'])} holdings for portfolio {portfolio_id}")
            holdings_count = insert_holdings(portfolio_id, parse_result['data'])
            
            logger.info(f"Successfully processed portfolio {portfolio_id} with {holdings_count} holdings")
            
            # NEW: Build response with analysis data
            response = {
                "message": "Portfolio uploaded and processed successfully",
                "portfolio_id": portfolio_id,
                "filename": filename,
                "holdings_count": holdings_count,
                "warnings": parse_result['warnings'] if parse_result['warnings'] else None
            }
            
            # Add analysis results if available
            if gains and daily and weights:
                response["analysis"] = {
                    "total_value": weights['total_portfolio_value'],
                    "total_gain_loss": gains['total_gain_loss'],
                    "return_percentage": gains['percentage_return'],
                    "daily_change_value": daily['daily_change_value'],
                    "daily_change_percentage": daily['daily_change_percentage'],
                    "holdings": weights['weights']  # Sorted by weight
                }
            
            return jsonify(response), 200
            
        except Exception as db_error:
            logger.error(f"Database error during portfolio insertion: {str(db_error)}")
            return jsonify({
                "error": "Failed to save portfolio to database",
                "details": str(db_error)
            }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


# Add endpoint to get fresh analysis for existing portfolio
@api_bp.route("/portfolio/<int:portfolio_id>/analyze", methods=['GET'])
def analyze_portfolio(portfolio_id):
    """
    Get fresh financial analysis for an existing portfolio.
    Fetches current stock prices and calculates metrics.
    """
    try:
        logger.info(f"Analyzing portfolio {portfolio_id}")
        
        # Get portfolio data
        portfolio = get_portfolio_by_id(portfolio_id)
        if not portfolio:
            logger.warning(f"Portfolio {portfolio_id} not found")
            return jsonify({"error": "Portfolio not found"}), 404
        
        # Get holdings from database
        holdings = get_holdings_by_portfolio(portfolio_id)
        
        if not holdings:
            return jsonify({"error": "No holdings found for this portfolio"}), 404
        
        # Run analysis with finance functions
        gains = get_total_unrealized_gain_loss(holdings)
        daily = get_daily_change(holdings)
        weights = get_portfolio_weights(holdings)
        
        logger.info(f"Analysis complete for portfolio {portfolio_id}")
        
        return jsonify({
            "portfolio_id": portfolio_id,
            "portfolio_info": portfolio,
            "analysis": {
                "total_value": weights['total_portfolio_value'],
                "total_gain_loss": gains['total_gain_loss'],
                "total_cost_basis": gains['total_cost_basis'],
                "return_percentage": gains['percentage_return'],
                "daily_change_value": daily['daily_change_value'],
                "daily_change_percentage": daily['daily_change_percentage']
            },
            "holdings": weights['weights'],
            "details": {
                "gains_by_stock": gains['details'],
                "daily_changes_by_stock": daily['details']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio {portfolio_id}: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@api_bp.route("/portfolio/<int:portfolio_id>", methods=['GET'])
def get_portfolio(portfolio_id):
    """
    Get portfolio data with holdings by portfolio ID.
    """
    try:
        logger.info(f"Fetching portfolio {portfolio_id}")
        
        # Get portfolio information
        portfolio = get_portfolio_by_id(portfolio_id)
        if not portfolio:
            logger.warning(f"Portfolio {portfolio_id} not found")
            return jsonify({"error": "Portfolio not found"}), 404
        
        # Get holdings for the portfolio
        holdings = get_holdings_by_portfolio(portfolio_id)
        
        # Get portfolio summary
        summary = get_portfolio_summary(portfolio_id)
        
        logger.info(f"Successfully retrieved portfolio {portfolio_id} with {len(holdings)} holdings")
        
        return jsonify({
            "portfolio": portfolio,
            "holdings": holdings,
            "summary": summary,
            "holdings_count": len(holdings)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching portfolio {portfolio_id}: {str(e)}")
        return jsonify({"error": f"Failed to fetch portfolio: {str(e)}"}), 500

@api_bp.route("/portfolios/user/<user_id>", methods=['GET'])
def get_user_portfolios(user_id):
    """
    Get all portfolios for a specific user.
    """
    try:
        logger.info(f"Fetching portfolios for user {user_id}")
        
        from utils.database import get_portfolios_by_user
        portfolios = get_portfolios_by_user(user_id)
        
        logger.info(f"Successfully retrieved {len(portfolios)} portfolios for user {user_id}")
        
        return jsonify({
            "user_id": user_id,
            "portfolios": portfolios,
            "count": len(portfolios)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching portfolios for user {user_id}: {str(e)}")
        return jsonify({"error": f"Failed to fetch portfolios: {str(e)}"}), 500

@api_bp.route("/health", methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    """
    try:
        from utils.database import get_database_stats
        stats = get_database_stats()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@api_bp.route("/advice", methods=['POST'])
def get_advice():
    """
    Generate investment advice using portfolio data and a user question.
    Expects JSON body: { "portfolio_id": int, "question": string }
    """
    logger.info("=" * 80)
    logger.info("ADVICE ENDPOINT CALLED - Starting request processing")
    logger.info("=" * 80)
    
    try:
        # Step 1: Parse request
        logger.info("STEP 1: Parsing request payload")
        payload = request.get_json(silent=True) or {}
        portfolio_id = payload.get('portfolio_id')
        question = (payload.get('question') or '').strip()
        logger.info(f"  - portfolio_id: {portfolio_id} (type: {type(portfolio_id)})")
        logger.info(f"  - question: '{question}'")

        if not portfolio_id or not isinstance(portfolio_id, int):
            logger.warning("  ❌ Invalid portfolio_id")
            return jsonify({"advice": None, "error": "Invalid or missing portfolio_id"}), 400

        if not question:
            logger.warning("  ❌ Missing question")
            return jsonify({"advice": None, "error": "Question is required"}), 400

        logger.info("  ✓ Request validation passed")

        # Step 2: Fetch portfolio data
        logger.info("STEP 2: Fetching portfolio data from database")
        portfolio = get_portfolio_by_id(portfolio_id)
        if not portfolio:
            logger.warning(f"  ❌ Portfolio {portfolio_id} not found")
            return jsonify({"advice": None, "error": "Portfolio not found"}), 404

        logger.info(f"  ✓ Portfolio found: {portfolio.get('file_name')}")

        holdings_rows = get_holdings_by_portfolio(portfolio_id)
        logger.info(f"  ✓ Retrieved {len(holdings_rows)} holdings")

        # Step 3: Prepare portfolio data
        logger.info("STEP 3: Preparing portfolio data for advisor prompt")
        holdings = []
        for h in holdings_rows:
            shares = h.get('shares') or 0
            purchase_price = h.get('purchase_price') or 0
            current_value = h.get('current_value') if 'current_value' in h else (shares * purchase_price)
            holdings.append({
                'ticker': h.get('ticker'),
                'shares': shares,
                'purchase_price': purchase_price,
                'current_value': current_value,
                'gain_loss': None,
                'sector': h.get('sector') if 'sector' in h else None,
            })

        portfolio_data = { 'holdings': holdings }
        logger.info(f"  ✓ Prepared {len(holdings)} holdings for prompt generation")

        # Step 4: Generate prompt
        logger.info("STEP 4: Generating advisor prompt")
        prompt = generate_advisor_prompt(portfolio_data, question)
        logger.info(f"  ✓ Prompt generated (length: {len(prompt)} characters)")
        logger.debug(f"  Prompt preview: {prompt[:200]}...")

        # Step 5: Check environment variables
        logger.info("STEP 5: Checking OpenAI API configuration")
        logger.info("  Checking environment variables...")
        
        # Check all possible env var sources
        api_key_env = os.getenv('OPENAI_API_KEY')
        api_key_from_environ = os.environ.get('OPENAI_API_KEY')
        
        logger.info(f"  - os.getenv('OPENAI_API_KEY'): {'SET' if api_key_env else 'NOT SET'}")
        logger.info(f"  - os.environ.get('OPENAI_API_KEY'): {'SET' if api_key_from_environ else 'NOT SET'}")
        
        # Check .env file locations
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)
        env_backend = os.path.join(backend_dir, '.env')
        env_root = os.path.join(project_root, '.env')
        
        logger.info(f"  Checking .env file locations:")
        logger.info(f"    - {env_backend}: {'EXISTS' if os.path.exists(env_backend) else 'NOT FOUND'}")
        logger.info(f"    - {env_root}: {'EXISTS' if os.path.exists(env_root) else 'NOT FOUND'}")
        
        # Get API key
        api_key = api_key_env or api_key_from_environ
        
        if api_key:
            logger.info(f"  ✓ OPENAI_API_KEY found in environment")
            logger.info(f"    - Key prefix: {api_key[:10]}...")
            logger.info(f"    - Key length: {len(api_key)} characters")
            logger.info(f"    - Key starts with 'sk-': {api_key.startswith('sk-')}")
        else:
            logger.warning("  ❌ OPENAI_API_KEY is NOT set in environment variables")
            logger.warning("  This means the API will fall back to simulated responses")
            logger.warning("  To fix: Create backend/.env file with: OPENAI_API_KEY=sk-your-key-here")

        # Step 6: Attempt OpenAI API call
        advice_text = None
        openai_error = None
        
        if api_key:
            logger.info("STEP 6: Attempting OpenAI API call")
            try:
                logger.info("  Importing OpenAI library...")
                from openai import OpenAI
                logger.info("  ✓ OpenAI library imported successfully")
                
                logger.info("  Initializing OpenAI client...")
                client = OpenAI(api_key=api_key)
                logger.info("  ✓ OpenAI client initialized")
                
                logger.info("  Preparing API request...")
                logger.info(f"    - Model: gpt-3.5-turbo")
                logger.info(f"    - Prompt length: {len(prompt)} characters")
                logger.info(f"    - Temperature: 0.3")
                logger.info(f"    - Max tokens: 500")
                
                logger.info("  Making API call to OpenAI...")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful financial investment advisor. Provide clear, concise, and prudent guidance based on the user's portfolio data."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                )
                
                logger.info("  ✓ API call successful!")
                logger.info(f"    - Response ID: {response.id}")
                logger.info(f"    - Model used: {response.model}")
                logger.info(f"    - Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
                
                advice_text = response.choices[0].message.content.strip()
                logger.info(f"  ✓ Advice extracted (length: {len(advice_text)} characters)")
                logger.info("  ✓ SUCCESS: Real OpenAI API response received")
                
            except ImportError as ie:
                openai_error = f"OpenAI library not installed: {str(ie)}"
                logger.error(f"  ❌ IMPORT ERROR: {openai_error}")
                logger.error("  To fix: Run: pip install openai")
                logger.exception("Full import error traceback:")
                
            except Exception as oe:
                openai_error = str(oe)
                logger.error(f"  ❌ API CALL FAILED: {openai_error}")
                logger.error(f"    Error type: {type(oe).__name__}")
                logger.exception("Full API error traceback:")
        else:
            openai_error = "OPENAI_API_KEY not set in environment variables"
            logger.warning(f"  ⚠️ SKIPPING OpenAI API call: {openai_error}")

        # Step 7: Handle response
        logger.info("STEP 7: Preparing final response")
        if not advice_text:
            logger.warning("  ⚠️ No advice_text from OpenAI, using simulated response")
            logger.warning(f"    Reason: {openai_error if openai_error else 'Unknown'}")
            
            advice_text = (
                "This is a simulated advisory response. "
                "Key points from your portfolio were summarized, and prudent, diversified investing, risk tolerance alignment, "
                "and periodic rebalancing are recommended. "
                f"Prompt context: {prompt[:200]}..."
            )
            
            logger.info("  Returning simulated response with error information")
            logger.info("=" * 80)
            logger.info("REQUEST COMPLETE: Returning simulated response")
            logger.info("=" * 80)
            
            return jsonify({
                "advice": advice_text, 
                "error": openai_error if openai_error else "OpenAI API not configured"
            }), 200

        logger.info("  ✓ Returning real OpenAI API response")
        logger.info("=" * 80)
        logger.info("REQUEST COMPLETE: Returning real OpenAI API response")
        logger.info("=" * 80)
        
        return jsonify({"advice": advice_text, "error": None}), 200

    except Exception as e:
        logger.error("=" * 80)
        logger.error("FATAL ERROR in advice endpoint")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.exception("Full error traceback:")
        return jsonify({"advice": None, "error": f"Advice generation failed: {str(e)}"}), 500

@api_bp.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large"}), 413
