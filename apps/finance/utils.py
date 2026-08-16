"""Finance Engine utilities."""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Tuple

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify


def get_financial_year_for_date(date: timezone.datetime) -> Optional[Any]:
    """
    Get the financial year for a given date.

    Args:
        date: The date to check.

    Returns:
        FinancialYear: The financial year containing the date, or None if not found.
    """
    FinancialYear = django_apps.get_model("finance", "FinancialYear")
    
    try:
        return FinancialYear.objects.get(
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        )
    except FinancialYear.DoesNotExist:
        return None


def format_currency(amount: Decimal, currency_code: str = "USD") -> str:
    """
    Format a decimal amount as currency.

    Args:
        amount: The amount to format.
        currency_code: The currency code (default: USD).

    Returns:
        str: The formatted currency string.
    """
    # Get currency symbol from settings or use default
    currency_symbols = getattr(settings, 'CURRENCY_SYMBOLS', {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'UGX': 'USH',
        'KES': 'KSh',
        'TZS': 'TSh',
    })
    
    symbol = currency_symbols.get(currency_code, currency_code)
    
    # Format with 2 decimal places
    formatted_amount = f"{amount:,.2f}"
    
    # Return formatted string
    return f"{symbol}{formatted_amount}"


def parse_currency_string(currency_string: str) -> Tuple[Decimal, str]:
    """
    Parse a currency string into amount and currency code.

    Args:
        currency_string: The currency string to parse (e.g., "$1,234.56" or "USD 1,234.56").

    Returns:
        Tuple of (Decimal amount, str currency_code).
    """
    # Remove whitespace
    currency_string = currency_string.strip()
    
    # Common currency symbols
    currency_symbols = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        'USH': 'UGX',
        'KSh': 'KES',
        'TSh': 'TZS',
    }
    
    # Try to match currency symbol at the beginning
    amount_str = currency_string
    currency_code = None
    
    for symbol, code in currency_symbols.items():
        if currency_string.startswith(symbol):
            amount_str = currency_string[len(symbol):].strip()
            currency_code = code
            break
    
    # If no symbol matched, try to match currency code at the beginning
    if currency_code is None:
        # Match patterns like "USD 1,234.56" or "EUR 1,234.56"
        match = re.match(r'^([A-Z]{3})\s+(.+)$', currency_string)
        if match:
            currency_code = match.group(1)
            amount_str = match.group(2).strip()
        else:
            # Default to USD if no currency specified
            currency_code = 'USD'
            amount_str = currency_string
    
    # Remove commas and convert to Decimal
    amount_str = amount_str.replace(',', '')
    try:
        amount = Decimal(amount_str)
    except Exception:
        raise ValidationError(f"Invalid currency amount: {currency_string}")
        
    return amount, currency_code


def generate_financial_reference(prefix: str, year: Optional[int] = None) -> str:
    """
    Generate a financial reference number.

    Args:
        prefix: The prefix for the reference (e.g., "FIN", "INV", "REC").
        year: The year to use (default: current year).

    Returns:
        str: The generated reference number.
    """
    if year is None:
        year = timezone.now().year
        
    # Get the next sequence number
    # In a real implementation, this would use a proper sequence service
    # For now, we'll use a simple approach based on existing references
    ReferenceEntry = django_apps.get_model("references", "ReferenceEntry")
    
    # Find the latest reference with this prefix for the given year
    latest_reference = ReferenceEntry.objects.filter(
        reference__startswith=f"{prefix}/{year}/"
    ).order_by('-reference').first()
    
    if latest_reference:
        # Extract the sequence number and increment it
        try:
            # Format is usually PREFIX/YEAR/SEQUENCE
            parts = latest_reference.reference.split('/')
            if len(parts) >= 3:
                sequence = int(parts[2]) + 1
            else:
                sequence = 1
        except (ValueError, IndexError):
            sequence = 1
    else:
        sequence = 1
        
    # Format the reference with zero-padded sequence number
    return f"{prefix}/{year}/{sequence:06d}"


def validate_financial_amount(amount: Any) -> Decimal:
    """
    Validate and convert a value to a Decimal financial amount.

    Args:
        amount: The value to validate.

    Returns:
        Decimal: The validated amount.

    Raises:
        ValidationError: If the amount is invalid.
    """
    try:
        if isinstance(amount, str):
            # Remove any currency symbols or commas
            amount = re.sub(r'[^\d.-]', '', amount)
        amount_decimal = Decimal(str(amount))
        
        if amount_decimal < 0:
            raise ValidationError("Financial amount cannot be negative.")
            
        return amount_decimal
    except Exception as e:
        raise ValidationError(f"Invalid financial amount: {amount}. Error: {str(e)}")


def calculate_exchange_rate(from_currency: str, to_currency: str, amount: Decimal) -> Decimal:
    """
    Calculate exchange rate between two currencies.

    Args:
        from_currency: The source currency code.
        to_currency: The target currency code.
        amount: The amount in source currency.

    Returns:
        Decimal: The exchange rate (to_currency per unit of from_currency).
    """
    # In a real implementation, this would call an external exchange rate service
    # For now, we'll use fixed rates or 1:1 for same currency
    
    if from_currency == to_currency:
        return Decimal('1.0')
        
    # Fixed exchange rates (these would normally come from a service)
    exchange_rates = {
        ('USD', 'EUR'): Decimal('0.85'),
        ('EUR', 'USD'): Decimal('1.18'),
        ('USD', 'GBP'): Decimal('0.73'),
        ('GBP', 'USD'): Decimal('1.37'),
        ('USD', 'UGX'): Decimal('3700.0'),
        ('UGX', 'USD'): Decimal('0.00027'),
        ('USD', 'KES'): Decimal('110.0'),
        ('KES', 'USD'): Decimal('0.0091'),
        ('USD', 'TZS'): Decimal('2300.0'),
        ('TZS', 'USD'): Decimal('0.00043'),
    }
    
    rate_key = (from_currency, to_currency)
    if rate_key in exchange_rates:
        return exchange_rates[rate_key]
    else:
        # Default to 1:1 if rate not found (not ideal but prevents errors)
        return Decimal('1.0')


def convert_currency(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """
    Convert an amount from one currency to another.

    Args:
        amount: The amount to convert.
        from_currency: The source currency code.
        to_currency: The target currency code.

    Returns:
        Decimal: The converted amount.
    """
    if from_currency == to_currency:
        return amount
        
    exchange_rate = calculate_exchange_rate(from_currency, to_currency, amount)
    return amount * exchange_rate


def is_financial_period_open(date: timezone.datetime) -> bool:
    """
    Check if a financial period is open for posting.

    Args:
        date: The date to check.

    Returns:
        bool: True if the financial period is open, False otherwise.
    """
    FinancialYear = django_apps.get_model("finance", "FinancialYear")
    
    try:
        financial_year = FinancialYear.objects.get(
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        )
        return financial_year.is_open_for_posting
    except FinancialYear.DoesNotExist:
        return False


def get_default_currency() -> str:
    """
    Get the default currency for the system.

    Returns:
        str: The default currency code.
    """
    return getattr(settings, 'DEFAULT_CURRENCY', 'USD')


def get_supported_currencies() -> List[str]:
    """
    Get the list of supported currencies.

    Returns:
        List[str]: List of supported currency codes.
    """
    return getattr(settings, 'SUPPORTED_CURRENCIES', ['USD', 'EUR', 'GBP', 'UGX', 'KES', 'TZS'])


def validate_account_code(account_code: str) -> bool:
    """
    Validate an account code format.

    Args:
        account_code: The account code to validate.

    Returns:
        bool: True if the account code is valid, False otherwise.
    """
    # Account codes are typically numeric and follow a chart of accounts structure
    # For example: 1000-1999 for Assets, 2000-2999 for Liabilities, etc.
    if not account_code:
        return False
        
    # Remove any hyphens or spaces for validation
    clean_code = account_code.replace('-', '').replace(' ', '')
    
    # Should be numeric
    if not clean_code.isdigit():
        return False
        
    # Should be a reasonable length (typically 4-6 digits)
    if len(clean_code) < 3 or len(clean_code) > 8:
        return False
        
    return True


def get_account_type_from_code(account_code: str) -> Optional[str]:
    """
    Determine account type from account code.

    Args:
        account_code: The account code.

    Returns:
        str: The account type (asset, liability, equity, income, expense), or None if invalid.
    """
    if not validate_account_code(account_code):
        return None
        
    # Get the first digit to determine account type
    clean_code = account_code.replace('-', '').replace(' ', '')
    first_digit = int(clean_code[0])
    
    # Standard chart of accounts numbering:
    # 1xxx = Assets
    # 2xxx = Liabilities
    # 3xxx = Equity/Fund Balance
    # 4xxx = Income/Revenue
    # 5xxx = Expenses/Expenditures
    
    if first_digit == 1:
        return 'asset'
    elif first_digit == 2:
        return 'liability'
    elif first_digit == 3:
        return 'equity'
    elif first_digit == 4:
        return 'income'
    elif first_digit == 5:
        return 'expense'
    else:
        return None