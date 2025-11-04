# test_currency_conversion.py
# Comprehensive test suite for kopeck-ruble currency conversion and validation

import pytest
from decimal import Decimal

from app.utils.currency_utils import (
    rubles_to_kopecks,
    kopecks_to_rubles,
    kopecks_to_rubles_display,
    validate_kopecks_amount,
    calculate_vat_kopecks,
    calculate_gross_kopecks
)


class TestRublesToKopecks:
    """Test ruble to kopeck conversion"""
    
    def test_basic_conversion(self):
        """Test basic ruble to kopeck conversion"""
        assert rubles_to_kopecks(1.50) == 150
        assert rubles_to_kopecks(100.00) == 10000
        assert rubles_to_kopecks(0.01) == 1
        assert rubles_to_kopecks(0) == 0
    
    def test_decimal_input(self):
        """Test conversion with Decimal input"""
        assert rubles_to_kopecks(Decimal('150.50')) == 15050
        assert rubles_to_kopecks(Decimal('99.99')) == 9999
        assert rubles_to_kopecks(Decimal('0.01')) == 1
    
    def test_integer_input(self):
        """Test conversion with integer input"""
        assert rubles_to_kopecks(150) == 15000
        assert rubles_to_kopecks(1) == 100
        assert rubles_to_kopecks(0) == 0
    
    def test_rounding(self):
        """Test proper rounding behavior"""
        assert rubles_to_kopecks(1.505) == 151  # Round half up
        assert rubles_to_kopecks(1.504) == 150  # Round down
        assert rubles_to_kopecks(1.506) == 151  # Round up
    
    def test_none_input(self):
        """Test None input handling"""
        assert rubles_to_kopecks(None) == 0


class TestKopecksToRubles:
    """Test kopeck to ruble conversion"""
    
    def test_basic_conversion(self):
        """Test basic kopeck to ruble conversion"""
        assert kopecks_to_rubles(150) == Decimal('1.50')
        assert kopecks_to_rubles(10000) == Decimal('100.00')
        assert kopecks_to_rubles(1) == Decimal('0.01')
        assert kopecks_to_rubles(0) == Decimal('0.00')
    
    def test_large_amounts(self):
        """Test large kopeck amounts"""
        assert kopecks_to_rubles(15050) == Decimal('150.50')
        assert kopecks_to_rubles(9999) == Decimal('99.99')
        assert kopecks_to_rubles(100000000) == Decimal('1000000.00')
    
    def test_none_input(self):
        """Test None input handling"""
        assert kopecks_to_rubles(None) == Decimal('0.00')


class TestKopecksToRublesDisplay:
    """Test kopeck to ruble display formatting"""
    
    def test_display_formatting(self):
        """Test display string formatting"""
        assert kopecks_to_rubles_display(15050) == "150.50 ₽"
        assert kopecks_to_rubles_display(9999) == "99.99 ₽"
        assert kopecks_to_rubles_display(10000) == "100.00 ₽"
        assert kopecks_to_rubles_display(1) == "0.01 ₽"
        assert kopecks_to_rubles_display(0) == "0.00 ₽"


class TestValidateKopecksAmount:
    """Test kopeck amount validation"""
    
    def test_valid_amounts(self):
        """Test valid kopeck amounts"""
        assert validate_kopecks_amount(0) == True
        assert validate_kopecks_amount(1) == True
        assert validate_kopecks_amount(15050) == True
        assert validate_kopecks_amount(99999999) == True  # Under max
    
    def test_invalid_amounts(self):
        """Test invalid kopeck amounts"""
        assert validate_kopecks_amount(-1) == False  # Negative
        assert validate_kopecks_amount(100000001) == False  # Over max
        assert validate_kopecks_amount("150") == False  # Wrong type
        assert validate_kopecks_amount(1.5) == False  # Float
    
    def test_boundary_values(self):
        """Test boundary values"""
        assert validate_kopecks_amount(100000000) == True  # Exactly max
        assert validate_kopecks_amount(100000001) == False  # Over max


class TestCalculateVatKopecks:
    """Test VAT calculation in kopecks"""
    
    def test_standard_vat_rates(self):
        """Test standard VAT rate calculations"""
        # 20% VAT on 100.00₽ (10000 kopecks) = 20.00₽ (2000 kopecks)
        assert calculate_vat_kopecks(10000, Decimal('20.00')) == 2000
        
        # 10% VAT on 150.00₽ (15000 kopecks) = 15.00₽ (1500 kopecks)
        assert calculate_vat_kopecks(15000, Decimal('10.00')) == 1500
        
        # 0% VAT
        assert calculate_vat_kopecks(10000, Decimal('0.00')) == 0
    
    def test_edge_cases(self):
        """Test edge cases for VAT calculation"""
        assert calculate_vat_kopecks(0, Decimal('20.00')) == 0  # Zero amount
        assert calculate_vat_kopecks(10000, Decimal('0')) == 0  # Zero VAT
        assert calculate_vat_kopecks(-100, Decimal('20.00')) == 0  # Negative amount
    
    def test_fractional_results(self):
        """Test VAT calculations that result in fractions"""
        # 20% VAT on 1.00₽ (100 kopecks) = 0.20₽ (20 kopecks)
        assert calculate_vat_kopecks(100, Decimal('20.00')) == 20
        
        # 10% VAT on 1.01₽ (101 kopecks) = 0.101₽ → 10 kopecks (rounded)
        assert calculate_vat_kopecks(101, Decimal('10.00')) == 10


class TestCalculateGrossKopecks:
    """Test gross amount calculation in kopecks"""
    
    def test_basic_calculation(self):
        """Test basic gross calculation"""
        assert calculate_gross_kopecks(10000, 2000) == 12000  # 100₽ + 20₽ = 120₽
        assert calculate_gross_kopecks(15000, 1500) == 16500  # 150₽ + 15₽ = 165₽
        assert calculate_gross_kopecks(5000, 0) == 5000  # 50₽ + 0₽ = 50₽
    
    def test_zero_values(self):
        """Test with zero values"""
        assert calculate_gross_kopecks(0, 0) == 0
        assert calculate_gross_kopecks(1000, 0) == 1000
        assert calculate_gross_kopecks(0, 200) == 200


class TestRoundTripConversion:
    """Test round-trip conversion accuracy"""
    
    def test_round_trip_accuracy(self):
        """Test that ruble→kopeck→ruble conversion is accurate"""
        test_amounts = [
            Decimal('1.50'),
            Decimal('100.00'),
            Decimal('150.50'),
            Decimal('99.99'),
            Decimal('0.01'),
            Decimal('1000.00')
        ]
        
        for original_rubles in test_amounts:
            kopecks = rubles_to_kopecks(original_rubles)
            converted_rubles = kopecks_to_rubles(kopecks)
            assert converted_rubles == original_rubles, f"Round-trip failed for {original_rubles}"
    
    def test_precision_limits(self):
        """Test precision limits of conversion"""
        # Test that we don't lose precision within kopeck boundaries
        assert rubles_to_kopecks(Decimal('0.001')) == 0  # Sub-kopeck rounds to 0
        assert rubles_to_kopecks(Decimal('0.005')) == 1  # Half-kopeck rounds up
        assert rubles_to_kopecks(Decimal('0.009')) == 1  # Near-kopeck rounds up


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def test_menu_item_pricing(self):
        """Test typical menu item pricing scenarios"""
        # Burger: 250.00₽
        burger_rubles = Decimal('250.00')
        burger_kopecks = rubles_to_kopecks(burger_rubles)
        assert burger_kopecks == 25000
        assert kopecks_to_rubles(burger_kopecks) == burger_rubles
        
        # Coffee: 89.50₽
        coffee_rubles = Decimal('89.50')
        coffee_kopecks = rubles_to_kopecks(coffee_rubles)
        assert coffee_kopecks == 8950
        assert kopecks_to_rubles(coffee_kopecks) == coffee_rubles
    
    def test_order_total_calculation(self):
        """Test order total calculation in kopecks"""
        # Order: 2x Burger (250₽) + 1x Coffee (89.50₽) = 589.50₽
        burger_kopecks = 25000
        coffee_kopecks = 8950
        
        order_total_kopecks = (burger_kopecks * 2) + (coffee_kopecks * 1)
        assert order_total_kopecks == 58950
        
        order_total_rubles = kopecks_to_rubles(order_total_kopecks)
        assert order_total_rubles == Decimal('589.50')
    
    def test_vat_calculation_scenario(self):
        """Test VAT calculation for real menu items"""
        # Item: 150.00₽ net, 20% VAT
        net_kopecks = 15000
        vat_kopecks = calculate_vat_kopecks(net_kopecks, Decimal('20.00'))
        gross_kopecks = calculate_gross_kopecks(net_kopecks, vat_kopecks)
        
        assert vat_kopecks == 3000  # 30.00₽ VAT
        assert gross_kopecks == 18000  # 180.00₽ gross
        
        # Verify display
        assert kopecks_to_rubles_display(gross_kopecks) == "180.00 ₽"


class TestPaymentGatewayCompatibility:
    """Test compatibility with payment gateway expectations"""
    
    def test_payment_gateway_amounts(self):
        """Test that amounts are correctly formatted for payment gateway"""
        # Order total: 589.50₽ should be sent as 58950 kopecks to payment gateway
        order_total_rubles = Decimal('589.50')
        order_total_kopecks = rubles_to_kopecks(order_total_rubles)
        
        # This is what should be sent to payment gateway
        assert order_total_kopecks == 58950
        assert isinstance(order_total_kopecks, int)
        
        # Verify it's valid
        assert validate_kopecks_amount(order_total_kopecks) == True
    
    def test_fiscal_gateway_amounts(self):
        """Test that amounts are correctly formatted for fiscal gateway"""
        # Individual item: 150.50₽ should be sent as 15050 kopecks
        item_price_rubles = Decimal('150.50')
        item_price_kopecks = rubles_to_kopecks(item_price_rubles)
        
        assert item_price_kopecks == 15050
        assert isinstance(item_price_kopecks, int)
        assert validate_kopecks_amount(item_price_kopecks) == True


if __name__ == "__main__":
    pytest.main([__file__])