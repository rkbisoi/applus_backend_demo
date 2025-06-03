"""
Payment Validation Test Payloads
These payloads demonstrate different scenarios that will pass or fail validation
based on the functional, performance, and security criteria in the system.
"""

from datetime import datetime
import json

# ============================================================================
# PASSING PAYLOADS (Expected to get APPROVED status - Score >= 85)
# ============================================================================

# 1. HIGH SCORE PAYLOAD - Perfect scenario (Expected: 90+ score)
high_score_payload = {
    "application_id": "APP_001_PERFECT",
    "payment_initiation_type": "cardNotPresentPan",
    "payment_information": {
        "account_type": "default",
        "payment_type": "single",  # Good: Single payment (no risk penalty)
        "transmission_date": "2025-06-03",  # Good: Valid date format
        "transmission_time": "14:30:45",  # Good: Valid time format
        "local_transaction_date": "2025-06-03",  # Good: Consistent with transmission date
        "local_transaction_time": "14:30:45",  # Good: Valid time format
        "settlement_date": "2025-06-03",
        "retrieval_reference_number": "000001234567",  # Good: Valid format
        "system_trace_audit_number": "123456"  # Good: Valid 6-digit number
    },
    "transaction_accept_method": "electronicCommerce",  # Good: Valid method
    "merchant_information": {
        "card_acceptor_name": "TrustedMerchant",  # Good: Standard length
        "format_card_acceptor": "32",
        "merchant_category_code": "1234"  # Good: Valid 4-digit MCC
    },
    "acquiring_information": {
        "merchant_id": "ABC123456789",  # Good: Trusted merchant (ABC prefix)
        "terminal_id": "12345678",  # Good: Valid 8-digit terminal ID (not 00000000)
        "acquiring_institution_id": "000031",
        "forwarding_institution_id": "000031"
    },
    "etp_pos_secure": {
        "security_level_indicator": "authenticated"  # Good: High security level
    }
}

# 2. GOOD SCORE PAYLOAD - Standard approval scenario (Expected: 85-89 score)
good_score_payload = {
    "application_id": "APP_002_GOOD",
    "payment_initiation_type": "cardNotPresentPan",
    "payment_information": {
        "account_type": "default",
        "payment_type": "single",
        "transmission_date": "2025-06-03",
        "transmission_time": "10:15:30",
        "local_transaction_date": "2025-06-03",
        "local_transaction_time": "10:15:30",
        "settlement_date": "2025-06-03",
        "retrieval_reference_number": "000009876543",
        "system_trace_audit_number": "987654"
    },
    "transaction_accept_method": "electronicCommerce",
    "merchant_information": {
        "card_acceptor_name": "StandardStore",
        "format_card_acceptor": "32",
        "merchant_category_code": "5678"
    },
    "acquiring_information": {
        "merchant_id": "ABC987654321",  # Good: Trusted merchant
        "terminal_id": "87654321",  # Good: Valid terminal ID
        "acquiring_institution_id": "000045",
        "forwarding_institution_id": "000045"
    },
    "etp_pos_secure": {
        "security_level_indicator": "unauthenticated"  # Medium: Lower security but still acceptable
    }
}

# ============================================================================
# MEDIUM SCORE PAYLOADS (Expected to get PENDING status - Score 60-84)
# ============================================================================

# 3. MEDIUM SCORE PAYLOAD - Some issues but acceptable (Expected: 70-80 score)
medium_score_payload = {
    "application_id": "APP_003_MEDIUM",
    "payment_initiation_type": "cardNotPresentPan",
    "payment_information": {
        "account_type": "default",
        "payment_type": "recurring",  # Medium: Recurring has risk penalty
        "transmission_date": "2025-06-03",
        "transmission_time": "16:45:20",
        "local_transaction_date": "2025-06-03",
        "local_transaction_time": "16:45:20",
        "settlement_date": "2025-06-03",
        "retrieval_reference_number": "000005555555",
        "system_trace_audit_number": "555555"
    },
    "transaction_accept_method": "electronicCommerce",
    "merchant_information": {
        "card_acceptor_name": "RegularMerchant",
        "format_card_acceptor": "32",
        "merchant_category_code": "9012"
    },
    "acquiring_information": {
        "merchant_id": "XYZ456789012",  # Medium: Standard merchant (XYZ prefix)
        "terminal_id": "45678901",
        "acquiring_institution_id": "000067",
        "forwarding_institution_id": "000067"
    },
    "etp_pos_secure": {
        "security_level_indicator": "unauthenticated"
    }
}

# ============================================================================
# FAILING PAYLOADS (Expected to get DECLINED status - Score < 60)
# ============================================================================

# 4. LOW SCORE PAYLOAD - Multiple validation failures (Expected: 40-55 score)
low_score_payload = {
    "application_id": "APP_004_LOW",
    "payment_initiation_type": "cardNotPresentPan",
    "payment_information": {
        "account_type": "default",
        "payment_type": "recurring",  # Bad: Risk penalty
        "transmission_date": "2025-6-3",  # Bad: Invalid date format (missing leading zeros)
        "transmission_time": "25:70:90",  # Bad: Invalid time format
        "local_transaction_date": "2025-06-04",  # Bad: Inconsistent with transmission date
        "local_transaction_time": "16:45:20",
        "settlement_date": "2025-06-03",
        "retrieval_reference_number": "000003333333",
        "system_trace_audit_number": "33333"  # Bad: Invalid length (5 digits instead of 6)
    },
    "transaction_accept_method": "invalidMethod",  # Bad: Invalid transaction method
    "merchant_information": {
        "card_acceptor_name": "TestMerchantWithVeryLongNameThatExceedsNormalLimits",  # Bad: Very long name
        "format_card_acceptor": "32",
        "merchant_category_code": "12345"  # Bad: Invalid length (5 digits instead of 4)
    },
    "acquiring_information": {
        "merchant_id": "TEST123456",  # Bad: Test merchant (TEST prefix)
        "terminal_id": "00000000",  # Bad: Suspicious terminal ID pattern
        "acquiring_institution_id": "000089",
        "forwarding_institution_id": "000089"
    },
    "etp_pos_secure": {
        "security_level_indicator": "unauthenticated"
    }
}

# 5. CRITICAL FAILURE PAYLOAD - Missing required fields (Expected: 20-35 score)
critical_failure_payload = {
    "application_id": "",  # Bad: Empty application ID
    "payment_initiation_type": "",  # Bad: Empty payment initiation type
    "payment_information": {
        "account_type": "",  # Bad: Empty account type
        "payment_type": "invalidType",  # Bad: Invalid payment type
        "transmission_date": "invalid-date",  # Bad: Invalid date format
        "transmission_time": "invalid-time",  # Bad: Invalid time format
        "local_transaction_date": "2025-13-45",  # Bad: Invalid date (month 13, day 45)
        "local_transaction_time": "25:99:99",  # Bad: Invalid time
        "settlement_date": "",  # Bad: Empty settlement date
        "retrieval_reference_number": "",  # Bad: Empty reference number
        "system_trace_audit_number": ""  # Bad: Empty trace number
    },
    "transaction_accept_method": "",  # Bad: Empty transaction method
    "merchant_information": {
        "card_acceptor_name": "",  # Bad: Empty merchant name
        "format_card_acceptor": "",
        "merchant_category_code": ""  # Bad: Empty MCC
    },
    "acquiring_information": {
        "merchant_id": "XY",  # Bad: Too short merchant ID
        "terminal_id": "00000000",  # Bad: Suspicious pattern
        "acquiring_institution_id": "",
        "forwarding_institution_id": ""
    },
    "etp_pos_secure": {
        "security_level_indicator": "unknown"  # Bad: Unknown security level
    }
}

# 6. EDGE CASE PAYLOAD - Mixed good and bad elements (Expected: 45-60 score)
edge_case_payload = {
    "application_id": "APP_006_EDGE",
    "payment_initiation_type": "cardNotPresentPan",
    "payment_information": {
        "account_type": "default",
        "payment_type": "installment",  # Good: Valid but less common type
        "transmission_date": "2025-06-03",  # Good: Valid format
        "transmission_time": "23:45:30",  # Medium: Late hour transaction
        "local_transaction_date": "2025-06-02",  # Bad: Date inconsistency
        "local_transaction_time": "23:45:30",
        "settlement_date": "2025-06-03",
        "retrieval_reference_number": "000007777777",
        "system_trace_audit_number": "777777"  # Good: Valid format
    },
    "transaction_accept_method": "moto",  # Good: Valid but different method
    "merchant_information": {
        "card_acceptor_name": "EdgeCaseMerchant",
        "format_card_acceptor": "32",
        "merchant_category_code": "ABCD"  # Bad: Non-numeric MCC
    },
    "acquiring_information": {
        "merchant_id": "UNKNOWN123456789",  # Bad: Unknown merchant pattern
        "terminal_id": "11111111",  # Medium: Valid but suspicious pattern
        "acquiring_institution_id": "000078",
        "forwarding_institution_id": "000078"
    },
    "etp_pos_secure": {
        "security_level_indicator": "unauthenticated"
    }
}

# ============================================================================
# UTILITY FUNCTIONS FOR TESTING
# ============================================================================

def print_payload_summary():
    """Print a summary of all test payloads"""
    payloads = [
        ("High Score (Perfect)", high_score_payload, "APPROVED", "90+"),
        ("Good Score (Standard)", good_score_payload, "APPROVED", "85-89"),
        ("Medium Score (Issues)", medium_score_payload, "PENDING", "70-80"),
        ("Low Score (Multiple Failures)", low_score_payload, "DECLINED", "40-55"),
        ("Critical Failure (Missing Fields)", critical_failure_payload, "DECLINED", "20-35"),
        ("Edge Case (Mixed)", edge_case_payload, "DECLINED/PENDING", "45-60")
    ]
    
    print("=" * 80)
    print("PAYMENT VALIDATION TEST PAYLOADS SUMMARY")
    print("=" * 80)
    
    for name, payload, expected_status, expected_score in payloads:
        print(f"\n{name}:")
        print(f"  Application ID: {payload['application_id']}")
        print(f"  Expected Status: {expected_status}")
        print(f"  Expected Score: {expected_score}")
        print(f"  Key Characteristics:")
        
        # Analyze key characteristics
        payment_type = payload['payment_information'].get('payment_type', 'N/A')
        merchant_id = payload['acquiring_information'].get('merchant_id', 'N/A')
        security_level = payload['etp_pos_secure'].get('security_level_indicator', 'N/A')
        terminal_id = payload['acquiring_information'].get('terminal_id', 'N/A')
        
        print(f"    - Payment Type: {payment_type}")
        print(f"    - Merchant ID: {merchant_id}")
        print(f"    - Security Level: {security_level}")
        print(f"    - Terminal ID: {terminal_id}")

def get_payload_by_name(name):
    """Get a specific payload by name"""
    payloads = {
        "high_score": high_score_payload,
        "good_score": good_score_payload,
        "medium_score": medium_score_payload,
        "low_score": low_score_payload,
        "critical_failure": critical_failure_payload,
        "edge_case": edge_case_payload
    }
    return payloads.get(name.lower())

def get_all_payloads():
    """Get all test payloads as a list"""
    return [
        high_score_payload,
        good_score_payload,
        medium_score_payload,
        low_score_payload,
        critical_failure_payload,
        edge_case_payload
    ]

# Example usage
if __name__ == "__main__":
    print_payload_summary()
    
    print("\n" + "=" * 80)
    print("SAMPLE JSON PAYLOAD (High Score):")
    print("=" * 80)
    print(json.dumps(high_score_payload, indent=2))
    
    print("\n" + "=" * 80)
    print("SAMPLE JSON PAYLOAD (Critical Failure):")
    print("=" * 80)
    print(json.dumps(critical_failure_payload, indent=2))