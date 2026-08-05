def format_currency(amount: float, currency_code: str = "USD") -> str:
    """
    Formats a numeric amount into a standard currency string.
    """
    return f"{amount:,.2f} {currency_code}"
