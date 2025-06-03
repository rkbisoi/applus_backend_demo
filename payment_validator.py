from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
import asyncio
import re
import hashlib
import time

class PaymentValidationRequest(BaseModel):
    application_id: str
    payment_initiation_type: str
    payment_information: Dict[str, Any]
    transaction_accept_method: str
    merchant_information: Dict[str, Any]
    acquiring_information: Dict[str, Any]
    etp_pos_secure: Dict[str, Any]

class ValidationResult(BaseModel):
    functional_score: int
    performance_score: int
    security_score: int
    overall_score: int
    overall_status: str  # APPROVED, DECLINED, PENDING
    functional_details: Dict[str, Any]
    performance_details: Dict[str, Any]
    security_details: Dict[str, Any]
    failure_reasons: List[str]
    validation_timestamp: str

class PaymentValidator:
    def __init__(self):
        self.min_passing_score = 60
        self.weight_functional = 0.4
        self.weight_performance = 0.3
        self.weight_security = 0.3
        
    def generate_high_score_test_data(application_id: str) -> PaymentValidationRequest:
        """Generate test data optimized for APPROVED status"""
        
        current_time = datetime.now()
        
        return PaymentValidationRequest(
            application_id=application_id,
            payment_initiation_type="cardNotPresentPan",
            payment_information={
                "account_type": "default",
                "payment_type": "single",  # Best score (not recurring)
                "transmission_date": current_time.strftime("%Y-%m-%d"),
                "transmission_time": current_time.strftime("%H:%M:%S"),
                "local_transaction_date": current_time.strftime("%Y-%m-%d"),  # Same as transmission
                "local_transaction_time": current_time.strftime("%H:%M:%S"),
                "settlement_date": current_time.strftime("%Y-%m-%d"),
                "retrieval_reference_number": f"000001{random.randint(10000, 99999)}",
                "system_trace_audit_number": f"{random.randint(100000, 999999)}"  # 6 digits
            },
            transaction_accept_method="electronicCommerce",  # Valid method
            merchant_information={
                "card_acceptor_name": "TrustedMerchant",  # Short name for performance
                "format_card_acceptor": "32",
                "merchant_category_code": "1234"  # Valid 4-digit MCC
            },
            acquiring_information={
                "merchant_id": f"ABC{random.randint(100000000, 999999999)}",  # ABC prefix = 25 points
                "terminal_id": f"{random.randint(10000001, 99999999)}",       # Not 00000000
                "acquiring_institution_id": f"000012",
                "forwarding_institution_id": f"000034"
            },
            etp_pos_secure={
                "security_level_indicator": "authenticated"  # CRITICAL: 35 points vs 15
            }
        )
        
    def generate_approved_scenario_data(application_id: str):
        """Generator optimized for APPROVED status (85+ score)"""
        current_time = datetime.now()
        
        return PaymentValidationRequest(
            application_id=application_id,
            payment_initiation_type="cardNotPresentPan",
            payment_information={
                "account_type": "default",
                "payment_type": "single",  # NOT recurring (avoids -5 risk penalty)
                "transmission_date": current_time.strftime("%Y-%m-%d"),
                "transmission_time": current_time.strftime("%H:%M:%S"),
                "local_transaction_date": current_time.strftime("%Y-%m-%d"),  # SAME date
                "local_transaction_time": current_time.strftime("%H:%M:%S"),
                "settlement_date": current_time.strftime("%Y-%m-%d"),
                "retrieval_reference_number": f"000001{random.randint(10000, 99999)}",
                "system_trace_audit_number": f"{random.randint(100000, 999999)}"
            },
            transaction_accept_method="electronicCommerce",
            merchant_information={
                "card_acceptor_name": "SecureCert",  # Short name for performance
                "format_card_acceptor": "32",
                "merchant_category_code": "1234"  # Valid 4-digit
            },
            acquiring_information={
                "merchant_id": f"ABC{random.randint(100000000, 999999999)}",  # ABC = +25 points
                "terminal_id": f"{random.randint(10000001, 99999999)}",       # NOT 00000000
                "acquiring_institution_id": "000012",
                "forwarding_institution_id": "000034"
            },
            etp_pos_secure={
                "security_level_indicator": "authenticated"  # +35 points (not +15)
            }
        )

    def generate_test_data(self, application_id: str) -> PaymentValidationRequest:
        """Generate test payment data based on sample payload structure"""
        
        # Simulate different scenarios with random variations
        scenarios = ["good", "medium", "poor"]
        scenario = random.choice(scenarios)
        
        if scenario == "good":
            # High success probability data
            payment_type = "single"
            card_acceptor_method = "notSpecified"
            security_level = "authenticated" if random.random() > 0.3 else "unauthenticated"
            merchant_id = f"ABC{random.randint(100000000, 999999999)}"
            terminal_id = f"{random.randint(10000000, 99999999)}"
        elif scenario == "medium":
            # Medium success probability data
            payment_type = random.choice(["single", "recurring"])
            card_acceptor_method = random.choice(["notSpecified", "manual"])
            security_level = "unauthenticated"
            merchant_id = f"XYZ{random.randint(100000000, 999999999)}"
            terminal_id = f"{random.randint(10000000, 99999999)}"
        else:
            # Lower success probability data
            payment_type = "recurring"
            card_acceptor_method = "manual"
            security_level = "unauthenticated"
            merchant_id = f"TEST{random.randint(100000, 999999)}"
            terminal_id = "00000000"
        
        current_time = datetime.now()
        
        return PaymentValidationRequest(
            application_id=application_id,
            payment_initiation_type="cardNotPresentPan",
            payment_information={
                "account_type": "default",
                "payment_type": payment_type,
                "transmission_date": current_time.strftime("%Y-%m-%d"),
                "transmission_time": current_time.strftime("%H:%M:%S"),
                "local_transaction_date": current_time.strftime("%Y-%m-%d"),
                "local_transaction_time": current_time.strftime("%H:%M:%S"),
                "settlement_date": current_time.strftime("%Y-%m-%d"),
                "retrieval_reference_number": f"00000{random.randint(100000, 999999)}",
                "system_trace_audit_number": f"{random.randint(100000, 999999)}"
            },
            transaction_accept_method="electronicCommerce",
            merchant_information={
                "card_acceptor_name": random.choice(["DigitalCertProvider", "SecureCertAuth", "TrustCertSvc"]),
                "format_card_acceptor": "32",
                "merchant_category_code": random.choice(["1234", "5678", "9012"])
            },
            acquiring_information={
                "merchant_id": merchant_id,
                "terminal_id": terminal_id,
                "acquiring_institution_id": f"0000{random.randint(10, 99)}",
                "forwarding_institution_id": f"0000{random.randint(10, 99)}"
            },
            etp_pos_secure={
                "security_level_indicator": security_level
            }
        )

    async def validate_functional(self, request: PaymentValidationRequest) -> Dict[str, Any]:
        """Validate functional aspects of payment request"""
        
        score = 0
        max_score = 100
        details = {}
        issues = []
        
        # Test 1: Required fields validation (30 points)
        required_fields_score = 0
        required_checks = [
            ("application_id", request.application_id),
            ("payment_initiation_type", request.payment_initiation_type),
            ("payment_information", request.payment_information),
            ("merchant_information", request.merchant_information),
            ("acquiring_information", request.acquiring_information)
        ]
        
        for field_name, field_value in required_checks:
            if field_value and str(field_value).strip():
                required_fields_score += 6
            else:
                issues.append(f"Missing or empty {field_name}")
        
        score += required_fields_score
        details["required_fields_score"] = required_fields_score
        
        # Test 2: Data format validation (25 points)
        format_score = 0
        
        # Date format validation
        payment_info = request.payment_information
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        time_pattern = r'^\d{2}:\d{2}:\d{2}$'
        
        if re.match(date_pattern, payment_info.get("transmission_date", "")):
            format_score += 5
        else:
            issues.append("Invalid transmission_date format")
        
        if re.match(time_pattern, payment_info.get("transmission_time", "")):
            format_score += 5
        else:
            issues.append("Invalid transmission_time format")
        
        if re.match(date_pattern, payment_info.get("local_transaction_date", "")):
            format_score += 5
        else:
            issues.append("Invalid local_transaction_date format")
        
        if re.match(time_pattern, payment_info.get("local_transaction_time", "")):
            format_score += 5
        else:
            issues.append("Invalid local_transaction_time format")
        
        # Merchant ID format validation
        merchant_id = request.acquiring_information.get("merchant_id", "")
        if len(merchant_id) >= 8 and merchant_id.isalnum():
            format_score += 5
        else:
            issues.append("Invalid merchant_id format")
        
        score += format_score
        details["format_score"] = format_score
        
        # Test 3: Business logic validation (25 points)
        business_logic_score = 0
        
        # Payment type validation
        valid_payment_types = ["single", "recurring", "installment"]
        if payment_info.get("payment_type") in valid_payment_types:
            business_logic_score += 8
        else:
            issues.append("Invalid payment_type")
        
        # Transaction acceptance method validation
        valid_accept_methods = ["electronicCommerce", "moto", "pos"]
        if request.transaction_accept_method in valid_accept_methods:
            business_logic_score += 8
        else:
            issues.append("Invalid transaction_accept_method")
        
        # Merchant category code validation
        mcc = request.merchant_information.get("merchant_category_code", "")
        if mcc.isdigit() and len(mcc) == 4:
            business_logic_score += 9
        else:
            issues.append("Invalid merchant_category_code")
        
        score += business_logic_score
        details["business_logic_score"] = business_logic_score
        
        # Test 4: Data consistency validation (20 points)
        consistency_score = 0
        
        # Date consistency check
        trans_date = payment_info.get("transmission_date", "")
        local_date = payment_info.get("local_transaction_date", "")
        if trans_date == local_date:
            consistency_score += 10
        else:
            issues.append("Date inconsistency between transmission and local transaction")
        
        # Terminal ID consistency
        terminal_id = request.acquiring_information.get("terminal_id", "")
        if terminal_id != "00000000" and len(terminal_id) == 8:
            consistency_score += 10
        else:
            issues.append("Invalid or placeholder terminal_id")
        
        score += consistency_score
        details["consistency_score"] = consistency_score
        
        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "details": details,
            "issues": issues
        }

    async def validate_performance(self, request: PaymentValidationRequest) -> Dict[str, Any]:
        """Validate performance aspects of payment request"""
        
        score = 0
        max_score = 100
        details = {}
        issues = []
        
        # Test 1: Response time simulation (40 points)
        start_time = time.time()
        
        # Simulate processing delay based on complexity
        complexity_factors = 0
        if request.payment_information.get("payment_type") == "recurring":
            complexity_factors += 1
        if request.etp_pos_secure.get("security_level_indicator") == "authenticated":
            complexity_factors += 1
        if len(request.merchant_information.get("card_acceptor_name", "")) > 15:
            complexity_factors += 1
        
        # Simulate processing time (0.1 to 0.5 seconds)
        processing_time = 0.1 + (complexity_factors * 0.1) + random.uniform(0, 0.2)
        await asyncio.sleep(processing_time)
        
        actual_time = time.time() - start_time
        
        if actual_time < 0.2:
            response_time_score = 40
        elif actual_time < 0.4:
            response_time_score = 30
        elif actual_time < 0.6:
            response_time_score = 20
        else:
            response_time_score = 10
            issues.append(f"Slow response time: {actual_time:.3f}s")
        
        score += response_time_score
        details["response_time_score"] = response_time_score
        details["actual_response_time"] = actual_time
        
        # Test 2: Throughput capacity (30 points)
        # Simulate concurrent processing capability
        concurrent_capacity = random.randint(50, 200)
        
        if concurrent_capacity >= 150:
            throughput_score = 30
        elif concurrent_capacity >= 100:
            throughput_score = 20
        elif concurrent_capacity >= 75:
            throughput_score = 15
        else:
            throughput_score = 10
            issues.append(f"Low throughput capacity: {concurrent_capacity}")
        
        score += throughput_score
        details["throughput_score"] = throughput_score
        details["concurrent_capacity"] = concurrent_capacity
        
        # Test 3: Memory efficiency (30 points)
        # Simulate memory usage based on payload complexity
        payload_size = len(str(request.dict()))
        memory_efficiency = max(0, 100 - (payload_size / 50))
        
        if memory_efficiency >= 80:
            memory_score = 30
        elif memory_efficiency >= 60:
            memory_score = 20
        elif memory_efficiency >= 40:
            memory_score = 15
        else:
            memory_score = 10
            issues.append(f"High memory usage indicated by payload size: {payload_size}")
        
        score += memory_score
        details["memory_score"] = memory_score
        details["payload_size"] = payload_size
        
        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "details": details,
            "issues": issues
        }

    async def validate_security(self, request: PaymentValidationRequest) -> Dict[str, Any]:
        """Validate security aspects of payment request"""
        
        score = 0
        max_score = 100
        details = {}
        issues = []
        
        # Test 1: Authentication level (35 points)
        security_level = request.etp_pos_secure.get("security_level_indicator", "")
        
        if security_level == "authenticated":
            auth_score = 35
        elif security_level == "unauthenticated":
            auth_score = 15
            issues.append("Unauthenticated transaction detected")
        else:
            auth_score = 0
            issues.append("Unknown security level indicator")
        
        score += auth_score
        details["authentication_score"] = auth_score
        
        # Test 2: Merchant validation (25 points)
        merchant_score = 0
        merchant_id = request.acquiring_information.get("merchant_id", "")
        
        # Check merchant ID patterns for security
        if merchant_id.startswith("ABC"):
            merchant_score = 25  # Trusted merchant
        elif merchant_id.startswith("XYZ"):
            merchant_score = 15  # Standard merchant
        elif merchant_id.startswith("TEST"):
            merchant_score = 5   # Test merchant
            issues.append("Test merchant detected - low security score")
        else:
            merchant_score = 10
            issues.append("Unknown merchant pattern")
        
        score += merchant_score
        details["merchant_score"] = merchant_score
        
        # Test 3: Transaction integrity (25 points)
        integrity_score = 0
        
        # Check for suspicious patterns
        terminal_id = request.acquiring_information.get("terminal_id", "")
        if terminal_id == "00000000":
            issues.append("Suspicious terminal ID pattern")
            integrity_score += 5
        else:
            integrity_score += 15
        
        # Validate trace numbers
        trace_number = request.payment_information.get("system_trace_audit_number", "")
        if trace_number and trace_number.isdigit() and len(trace_number) == 6:
            integrity_score += 10
        else:
            issues.append("Invalid system trace audit number")
        
        score += integrity_score
        details["integrity_score"] = integrity_score
        
        # Test 4: Risk assessment (15 points)
        risk_score = 15
        
        # Payment type risk assessment
        payment_type = request.payment_information.get("payment_type", "")
        if payment_type == "recurring":
            risk_score -= 5
            issues.append("Recurring payment carries additional risk")
        
        # Time-based risk assessment
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            risk_score -= 3
            issues.append("Off-hours transaction detected")
        
        score += max(0, risk_score)
        details["risk_score"] = max(0, risk_score)
        
        return {
            "score": min(score, max_score),
            "max_score": max_score,
            "details": details,
            "issues": issues
        }

    async def validate_payment(self, request: PaymentValidationRequest) -> ValidationResult:
        """Main validation method that orchestrates all validation checks"""
        
        start_time = datetime.now()
        
        # Run all validations concurrently
        functional_result, performance_result, security_result = await asyncio.gather(
            self.validate_functional(request),
            self.validate_performance(request),
            self.validate_security(request)
        )
        
        # Calculate weighted overall score
        functional_score = functional_result["score"]
        performance_score = performance_result["score"]
        security_score = security_result["score"]
        
        overall_score = int(
            (functional_score * self.weight_functional) +
            (performance_score * self.weight_performance) +
            (security_score * self.weight_security)
        )
        
        # Determine overall status
        if overall_score >= 70:
            overall_status = "APPROVED"
        elif overall_score >= self.min_passing_score:
            overall_status = "PENDING"
        else:
            overall_status = "DECLINED"
        
        # Collect all failure reasons
        failure_reasons = []
        failure_reasons.extend(functional_result["issues"])
        failure_reasons.extend(performance_result["issues"])
        failure_reasons.extend(security_result["issues"])
        
        return ValidationResult(
            functional_score=functional_score,
            performance_score=performance_score,
            security_score=security_score,
            overall_score=overall_score,
            overall_status=overall_status,
            functional_details=functional_result["details"],
            performance_details=performance_result["details"],
            security_details=security_result["details"],
            failure_reasons=failure_reasons,
            validation_timestamp=start_time.isoformat()
        )

# Example usage and testing
async def main():
    """Example usage of the PaymentValidator"""
    
    validator = PaymentValidator()
    
    print("=== Payment Validation System Demo ===\n")
    
    # Test with multiple scenarios
    for i in range(3):
        print(f"--- Test Case {i+1} ---")
        
        # Generate test data
        test_request = validator.generate_approved_scenario_data(f"APP_{i+1:03d}")
        
        print(f"Application ID: {test_request.application_id}")
        print(f"Payment Type: {test_request.payment_information['payment_type']}")
        print(f"Merchant ID: {test_request.acquiring_information['merchant_id']}")
        print(f"Security Level: {test_request.etp_pos_secure['security_level_indicator']}")
        
        # Run validation
        result = await validator.validate_payment(test_request)
        
        print(f"\n--- Validation Results ---")
        print(f"Functional Score: {result.functional_score}/100")
        print(f"Performance Score: {result.performance_score}/100")
        print(f"Security Score: {result.security_score}/100")
        print(f"Overall Score: {result.overall_score}/100")
        print(f"Status: {result.overall_status}")
        
        if result.failure_reasons:
            print(f"\nIssues Found:")
            for reason in result.failure_reasons[:5]:  # Show first 5 issues
                print(f"  - {reason}")
            if len(result.failure_reasons) > 5:
                print(f"  ... and {len(result.failure_reasons) - 5} more issues")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())