"""
CSV Parser for Portfolio Data
Handles parsing and validation of uploaded portfolio CSV files.
"""

import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioCSVParser:
    """
    Parser for portfolio CSV files with validation and error handling.
    """
    
    # Required columns for portfolio CSV
    REQUIRED_COLUMNS = ['ticker', 'shares', 'purchase_price', 'purchase_date']
    
    # Optional columns that can be included
    OPTIONAL_COLUMNS = ['company_name', 'sector', 'notes']
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def parse_csv(self, csv_content: str, filename: str = None) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        """
        Parse CSV content and return validated portfolio data.
        
        Args:
            csv_content (str): Raw CSV content as string
            filename (str): Original filename for logging purposes
            
        Returns:
            Tuple[List[Dict], List[str], List[str]]: (parsed_data, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        try:
            # Read CSV content
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            # Validate headers
            if not self._validate_headers(csv_reader.fieldnames):
                return [], self.errors, self.warnings
            
            # Parse and validate each row
            parsed_data = []
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                try:
                    validated_row = self._validate_and_parse_row(row, row_num)
                    if validated_row:
                        parsed_data.append(validated_row)
                except Exception as e:
                    error_msg = f"Error processing row {row_num}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.error(f"CSV parsing error in {filename}: {error_msg}")
            
            # Log summary
            logger.info(f"Successfully parsed {len(parsed_data)} holdings from {filename}")
            
            return parsed_data, self.errors, self.warnings
            
        except Exception as e:
            error_msg = f"Failed to parse CSV file: {str(e)}"
            self.errors.append(error_msg)
            logger.error(f"CSV parsing error in {filename}: {error_msg}")
            return [], self.errors, self.warnings
    
    def _validate_headers(self, headers: List[str]) -> bool:
        """
        Validate that CSV has all required columns.
        
        Args:
            headers (List[str]): List of column headers from CSV
            
        Returns:
            bool: True if headers are valid, False otherwise
        """
        if not headers:
            self.errors.append("CSV file appears to be empty or has no headers")
            return False
        
        # Normalize headers (lowercase, strip whitespace)
        normalized_headers = [h.lower().strip() for h in headers]
        
        # Check for required columns
        missing_columns = []
        for required_col in self.REQUIRED_COLUMNS:
            if required_col not in normalized_headers:
                missing_columns.append(required_col)
        
        if missing_columns:
            self.errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            self.errors.append(f"Required columns are: {', '.join(self.REQUIRED_COLUMNS)}")
            return False
        
        # Check for unexpected columns
        all_valid_columns = self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
        unexpected_columns = []
        for header in normalized_headers:
            if header not in all_valid_columns:
                unexpected_columns.append(header)
        
        if unexpected_columns:
            warning_msg = f"Unexpected columns found (will be ignored): {', '.join(unexpected_columns)}"
            self.warnings.append(warning_msg)
            logger.warning(warning_msg)
        
        return True
    
    def _validate_and_parse_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """
        Validate and parse a single row of CSV data.
        
        Args:
            row (Dict[str, str]): Raw row data from CSV
            row_num (int): Row number for error reporting
            
        Returns:
            Dict[str, Any]: Validated and parsed row data
        """
        validated_row = {}
        
        # Validate ticker
        ticker = row.get('ticker', '').strip().upper()
        if not ticker:
            raise ValueError("Ticker symbol is required and cannot be empty")
        if len(ticker) > 10:  # Reasonable limit for ticker symbols
            raise ValueError("Ticker symbol is too long (max 10 characters)")
        validated_row['ticker'] = ticker
        
        # Validate shares
        try:
            shares_str = row.get('shares', '').strip()
            if not shares_str:
                raise ValueError("Shares is required and cannot be empty")
            shares = float(shares_str)
            if shares <= 0:
                raise ValueError("Shares must be greater than 0")
            validated_row['shares'] = shares
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(f"Invalid shares value: '{shares_str}' - must be a number")
            raise e
        
        # Validate purchase_price
        try:
            price_str = row.get('purchase_price', '').strip()
            if not price_str:
                raise ValueError("Purchase price is required and cannot be empty")
            # Remove currency symbols and commas
            price_str = price_str.replace('$', '').replace(',', '').strip()
            purchase_price = float(price_str)
            if purchase_price <= 0:
                raise ValueError("Purchase price must be greater than 0")
            validated_row['purchase_price'] = purchase_price
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(f"Invalid purchase price: '{price_str}' - must be a number")
            raise e
        
        # Validate purchase_date
        try:
            date_str = row.get('purchase_date', '').strip()
            if not date_str:
                raise ValueError("Purchase date is required and cannot be empty")
            
            # Try multiple date formats
            date_formats = [
                '%Y-%m-%d',      # 2024-01-15
                '%m/%d/%Y',      # 01/15/2024
                '%m-%d-%Y',      # 01-15-2024
                '%d/%m/%Y',      # 15/01/2024
                '%d-%m-%Y',      # 15-01-2024
                '%Y/%m/%d',      # 2024/01/15
            ]
            
            purchase_date = None
            for date_format in date_formats:
                try:
                    purchase_date = datetime.strptime(date_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if purchase_date is None:
                raise ValueError(f"Invalid date format: '{date_str}' - supported formats: YYYY-MM-DD, MM/DD/YYYY, etc.")
            
            # Check if date is not in the future
            if purchase_date > datetime.now().date():
                self.warnings.append(f"Row {row_num}: Purchase date is in the future: {date_str}")
            
            validated_row['purchase_date'] = purchase_date.isoformat()
            
        except ValueError as e:
            raise e
        
        # Handle optional columns
        if 'company_name' in row and row['company_name'].strip():
            validated_row['company_name'] = row['company_name'].strip()
        
        if 'sector' in row and row['sector'].strip():
            validated_row['sector'] = row['sector'].strip()
        
        if 'notes' in row and row['notes'].strip():
            validated_row['notes'] = row['notes'].strip()
        
        return validated_row
    
    def validate_csv_file(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a CSV file from file path.
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, errors, warnings)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_content = file.read()
            
            parsed_data, errors, warnings = self.parse_csv(csv_content, file_path)
            return len(errors) == 0, errors, warnings
            
        except Exception as e:
            error_msg = f"Failed to read file {file_path}: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg], []


def parse_portfolio_csv(csv_content: str, filename: str = None) -> Dict[str, Any]:
    """
    Convenience function to parse portfolio CSV content.
    
    Args:
        csv_content (str): Raw CSV content as string
        filename (str): Original filename for logging purposes
        
    Returns:
        Dict[str, Any]: Parsing results with data, errors, and warnings
    """
    parser = PortfolioCSVParser()
    parsed_data, errors, warnings = parser.parse_csv(csv_content, filename)
    
    return {
        'data': parsed_data,
        'errors': errors,
        'warnings': warnings,
        'success': len(errors) == 0,
        'count': len(parsed_data)
    }


# Example usage and testing
if __name__ == "__main__":
    # Sample CSV content for testing
    sample_csv = """ticker,shares,purchase_price,purchase_date,company_name
AAPL,50,175.43,2024-01-15,Apple Inc.
MSFT,30,378.85,2024-01-20,Microsoft Corporation
GOOGL,20,142.56,2024-02-01,Alphabet Inc.
TSLA,15,248.50,2024-02-10,Tesla Inc.
AMZN,25,155.30,2024-02-15,Amazon.com Inc.
NVDA,10,875.20,2024-02-20,NVIDIA Corporation"""
    
    # Test the parser
    result = parse_portfolio_csv(sample_csv, "test_portfolio.csv")
    
    print("Parsing Results:")
    print(f"Success: {result['success']}")
    print(f"Count: {result['count']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
    
    if result['success']:
        print("\nParsed Data:")
        for i, holding in enumerate(result['data'], 1):
            print(f"{i}. {holding}")
