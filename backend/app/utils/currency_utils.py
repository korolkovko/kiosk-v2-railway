# currency_utils.py
# Utility functions for kopeck-ruble conversions and validation

from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional


def rubles_to_kopecks(rubles: Union[Decimal, float, int]) -> int:
    """
    Convert rubles (decimal) to kopecks (integer).
    
    Args:
        rubles: Amount in rubles (can be Decimal, float, or int)
        
    Returns:
        int: Amount in kopecks
        
    Examples:
        rubles_to_kopecks(150.50) -> 15050
        rubles_to_kopecks(Decimal('99.99')) -> 9999
        rubles_to_kopecks(100) -> 10000
    """
    if rubles is None:
        return 0
    
    # Convert to Decimal for precise arithmetic
    if isinstance(rubles, (int, float)):
        rubles_decimal = Decimal(str(rubles))
    else:
        rubles_decimal = rubles
    
    # Multiply by 100 and round to nearest integer
    kopecks_decimal = rubles_decimal * 100
    kopecks_rounded = kopecks_decimal.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    
    return int(kopecks_rounded)


def kopecks_to_rubles(kopecks: int) -> Decimal:
    """
    Convert kopecks (integer) to rubles (Decimal).
    
    Args:
        kopecks: Amount in kopecks
        
    Returns:
        Decimal: Amount in rubles with 2 decimal places
        
    Examples:
        kopecks_to_rubles(15050) -> Decimal('150.50')
        kopecks_to_rubles(9999) -> Decimal('99.99')
        kopecks_to_rubles(10000) -> Decimal('100.00')
    """
    if kopecks is None:
        return Decimal('0.00')
    
    rubles = Decimal(kopecks) / 100
    return rubles.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def kopecks_to_rubles_display(kopecks: int) -> str:
    """
    Convert kopecks to rubles formatted for display.
    
    Args:
        kopecks: Amount in kopecks
        
    Returns:
        str: Formatted amount for display (e.g., "150.50 ₽")
        
    Examples:
        kopecks_to_rubles_display(15050) -> "150.50 ₽"
        kopecks_to_rubles_display(9999) -> "99.99 ₽"
        kopecks_to_rubles_display(10000) -> "100.00 ₽"
    """
    rubles = kopecks_to_rubles(kopecks)
    return f"{rubles} ₽"


def validate_kopecks_amount(kopecks: int) -> bool:
    """
    Validate that kopecks amount is reasonable for business logic.
    
    Args:
        kopecks: Amount in kopecks to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Business rules:
        - Must be non-negative
        - Must be less than 1,000,000 rubles (100,000,000 kopecks)
    """
    if not isinstance(kopecks, int):
        return False
    
    if kopecks < 0:
        return False
    
    # Maximum 1,000,000 rubles = 100,000,000 kopecks
    if kopecks > 100_000_000:
        return False
    
    return True


def calculate_vat_kopecks(net_kopecks: int, vat_rate_percent: Decimal) -> int:
    """
    Calculate VAT amount in kopecks from net amount and VAT rate.
    
    Args:
        net_kopecks: Net amount in kopecks
        vat_rate_percent: VAT rate as percentage (e.g., Decimal('20.00') for 20%)
        
    Returns:
        int: VAT amount in kopecks
        
    Examples:
        calculate_vat_kopecks(10000, Decimal('20.00')) -> 2000  # 20% of 100.00₽
        calculate_vat_kopecks(15000, Decimal('10.00')) -> 1500  # 10% of 150.00₽
    """
    if net_kopecks <= 0 or vat_rate_percent <= 0:
        return 0
    
    # Convert kopecks to rubles for calculation
    net_rubles = kopecks_to_rubles(net_kopecks)
    
    # Calculate VAT in rubles
    vat_rubles = net_rubles * (vat_rate_percent / 100)
    
    # Convert back to kopecks
    return rubles_to_kopecks(vat_rubles)


def calculate_gross_kopecks(net_kopecks: int, vat_kopecks: int) -> int:
    """
    Calculate gross amount in kopecks from net and VAT amounts.
    
    Args:
        net_kopecks: Net amount in kopecks
        vat_kopecks: VAT amount in kopecks
        
    Returns:
        int: Gross amount in kopecks
        
    Examples:
        calculate_gross_kopecks(10000, 2000) -> 12000
        calculate_gross_kopecks(15000, 1500) -> 16500
    """
    return net_kopecks + vat_kopecks


# Validation constants
MIN_KOPECKS = 0
MAX_KOPECKS = 100_000_000  # 1,000,000 rubles