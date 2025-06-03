from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pathlib import Path

from payment_validator import PaymentValidator, PaymentValidationRequest, ValidationResult
from data_manager import DataManager

# Initialize FastAPI app
app = FastAPI(
    title="Digital Certificate API",
    description="API for managing digital certificate applications with enhanced payment validation",
    version="2.0.0"
)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data manager and payment validator
data_manager = DataManager()
payment_validator = PaymentValidator()

# Pydantic models
class Attachment(BaseModel):
    file_name: str
    file_type: str
    url: str

class CertificateApplication(BaseModel):
    name: str
    nric: Optional[str] = None
    passport: Optional[str] = None
    dob: str  # Date of birth in YYYY-MM-DD format
    nationality: str
    email: EmailStr
    organisation: Optional[str] = None
    address: Optional[str] = None
    certificate_type: str  # "Smart Card", "USB Token", "Softcert", etc.
    payment_mode: str  # "Bank In", "Credit Card", etc.
    attachments: Optional[List[Attachment]] = []

class CertificateIssuance(BaseModel):
    application_id: str

class ApplicationHistory(BaseModel):
    step: str
    timestamp: str

class ApplicationStatus(BaseModel):
    application_id: str
    status: str
    current_step: str
    history: List[ApplicationHistory]

# Business logic for auto-processing
async def should_auto_approve_application(application_data: dict) -> bool:
    """Business logic to determine if application should be auto-approved"""
    
    trusted_domains = [
        "gov.sg", "edu.sg", "com.sg", "org.sg",  # Singapore domains
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com"  # Common email providers
    ]
    
    standard_cert_types = ["Smart Card", "USB Token", "Softcert", "Mobile Certificate"]
    
    # Check identification
    has_identification = bool(application_data.get("nric") or application_data.get("passport"))
    
    # Check email domain
    email = application_data.get("email", "")
    email_domain = email.split("@")[-1].lower() if "@" in email else ""
    trusted_email = email_domain in trusted_domains
    
    # Check certificate type
    standard_cert = application_data.get("certificate_type") in standard_cert_types
    
    # Check required fields
    required_fields = ["name", "dob", "nationality", "email", "certificate_type", "payment_mode"]
    has_required_fields = all(application_data.get(field) for field in required_fields)
    
    return has_identification and trusted_email and standard_cert and has_required_fields

async def process_application_automatically(application_id: str, application_data: dict):
    """Background task to automatically process the application"""
    
    try:
        # Wait for initial processing (simulate document verification time)
        await asyncio.sleep(2)
        
        # Check if application should be auto-approved
        # if not await should_auto_approve_application(application_data):
        #     data_manager.add_audit_log(application_id, "Application requires manual review - auto-processing skipped")
        #     return
        
        data_manager.add_audit_log(application_id, "Starting automatic processing")
        
        # Step 1: Auto-validate payment (after 5 seconds)
        await asyncio.sleep(5)
        
        # Generate payment validation request from sample payload structure
        payment_request = PaymentValidationRequest(
            application_id=application_id,
            payment_initiation_type="cardNotPresentPan",
            payment_information={
                "account_type": "default",
                "payment_type": "single",
                "transmission_date": datetime.now().strftime("%Y-%m-%d"),
                "transmission_time": datetime.now().strftime("%H:%M:%S"),
                "local_transaction_date": datetime.now().strftime("%Y-%m-%d"),
                "local_transaction_time": datetime.now().strftime("%H:%M:%S"),
                "settlement_date": datetime.now().strftime("%Y-%m-%d"),
                "retrieval_reference_number": f"00000{application_id[-6:]}",
                "system_trace_audit_number": "000000"
            },
            transaction_accept_method="electronicCommerce",
            merchant_information={
                "card_acceptor_name": "DigitalCertProvider",
                "format_card_acceptor": "32",
                "merchant_category_code": "1234"
            },
            acquiring_information={
                "merchant_id": f"ABC{application_id[-9:]}",
                "terminal_id": "00000000",
                "acquiring_institution_id": "000031",
                "forwarding_institution_id": "000031"
            },
            etp_pos_secure={
                "security_level_indicator": "unauthenticated"
            }
        )
        
        # Validate payment with 3 criteria
        validation_result = await payment_validator.validate_payment(payment_request)
        
        # Update application based on validation results
        if validation_result.overall_status == "APPROVED":
            await internal_validate_payment_success(application_id, validation_result)
            data_manager.add_audit_log(application_id, f"Payment auto-validated successfully - Score: {validation_result.overall_score}")
            
            # Step 2: Auto-issue certificate (after additional 3 seconds)
            await asyncio.sleep(3)
            
            issuance = CertificateIssuance(application_id=application_id)
            await internal_issue_certificate(issuance)
            data_manager.add_audit_log(application_id, "Certificate auto-issued successfully")
        else:
            data_manager.add_audit_log(application_id, f"Payment validation failed - Status: {validation_result.overall_status}, Score: {validation_result.overall_score}")
            # Update application status to reflect payment failure
            await internal_validate_payment_failure(application_id, validation_result)
        
    except Exception as e:
        data_manager.add_audit_log(application_id, f"Auto-processing failed: {str(e)}")

# Internal functions for payment processing
async def internal_validate_payment_success(application_id: str, validation_result: ValidationResult):
    """Internal payment validation success handler"""
    applications = data_manager.load_applications()
    payments = data_manager.load_payments()
    
    # Find application
    application = None
    app_index = None
    for i, app in enumerate(applications):
        if app["application_id"] == application_id:
            application = app
            app_index = i
            break
    
    if not application:
        raise Exception("Application not found")
    
    # Create payment record
    payment_record = {
        "application_id": application_id,
        "validation_result": validation_result.dict(),
        "validation_date": datetime.now().isoformat(),
        "status": "Validated",
        "auto_processed": True,
        "functional_score": validation_result.functional_score,
        "performance_score": validation_result.performance_score,
        "security_score": validation_result.security_score,
        "overall_score": validation_result.overall_score,
        "overall_status": validation_result.overall_status
    }
    
    # Add payment record
    payments.append(payment_record)
    data_manager.save_payments(payments)
    
    # Update application status
    applications[app_index]["status"] = "Payment Validated"
    applications[app_index]["current_step"] = "Certificate Generation"
    applications[app_index]["payment_validated"] = True
    applications[app_index]["payment_date"] = datetime.now().isoformat()
    applications[app_index]["payment_validation_details"] = validation_result.dict()
    
    # Add to history
    if "history" not in applications[app_index]:
        applications[app_index]["history"] = []
    
    applications[app_index]["history"].append({
        "step": "Payment Auto-Validated",
        "timestamp": datetime.now().isoformat() + "Z",
        "details": f"Score: {validation_result.overall_score}/100"
    })
    
    data_manager.save_applications(applications)

async def internal_validate_payment_failure(application_id: str, validation_result: ValidationResult):
    """Internal payment validation failure handler"""
    applications = data_manager.load_applications()
    payments = data_manager.load_payments()
    
    # Find application
    application = None
    app_index = None
    for i, app in enumerate(applications):
        if app["application_id"] == application_id:
            application = app
            app_index = i
            break
    
    if not application:
        raise Exception("Application not found")
    
    # Create payment record for failed validation
    payment_record = {
        "application_id": application_id,
        "validation_result": validation_result.dict(),
        "validation_date": datetime.now().isoformat(),
        "status": "Failed",
        "auto_processed": True,
        "functional_score": validation_result.functional_score,
        "performance_score": validation_result.performance_score,
        "security_score": validation_result.security_score,
        "overall_score": validation_result.overall_score,
        "overall_status": validation_result.overall_status,
        "reason": validation_result.failure_reasons
    }
    
    # Add payment record
    payments.append(payment_record)
    data_manager.save_payments(payments)
    
    # Update application status
    applications[app_index]["status"] = "Payment Failed"
    applications[app_index]["current_step"] = "Payment Review Required"
    applications[app_index]["payment_validated"] = False
    applications[app_index]["payment_date"] = datetime.now().isoformat()
    applications[app_index]["payment_validation_details"] = validation_result.dict()
    
    # Add to history
    if "history" not in applications[app_index]:
        applications[app_index]["history"] = []
    
    applications[app_index]["history"].append({
        "step": "Payment Validation Failed",
        "timestamp": datetime.now().isoformat() + "Z",
        "details": f"Score: {validation_result.overall_score}/100, Reason: {', '.join(validation_result.failure_reasons)}"
    })
    
    data_manager.save_applications(applications)

async def internal_issue_certificate(issuance: CertificateIssuance):
    """Internal certificate issuance without HTTP overhead"""
    applications = data_manager.load_applications()
    certificates = data_manager.load_certificates()
    
    # Find application
    application = None
    app_index = None
    for i, app in enumerate(applications):
        if app["application_id"] == issuance.application_id:
            application = app
            app_index = i
            break
    
    if not application:
        raise Exception("Application not found")
    
    if not application.get("payment_validated", False):
        raise Exception("Payment must be validated before certificate issuance")
    
    # Generate certificate ID
    certificate_id = data_manager.generate_certificate_id()
    
    # Create certificate record
    certificate_record = {
        "certificate_id": certificate_id,
        "application_id": issuance.application_id,
        "name": application["name"],
        "status": "Valid",
        "issue_date": datetime.now().isoformat(),
        "validity": {
            "start": datetime.now().strftime("%Y-%m-%d"),
            "end": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        },
        "delivery_medium": application["certificate_type"],
        "revoked": False,
        "nric": application.get("nric"),
        "passport": application.get("passport"),
        "email": application["email"],
        "organisation": application.get("organisation"),
        "nationality": application["nationality"],
        "auto_issued": True
    }
    
    # Add certificate record
    certificates.append(certificate_record)
    data_manager.save_certificates(certificates)
    
    # Update application status
    applications[app_index]["status"] = "Issued"
    applications[app_index]["current_step"] = "Completed"
    applications[app_index]["certificate_id"] = certificate_id
    applications[app_index]["issue_date"] = datetime.now().isoformat()
    
    # Add to history
    applications[app_index]["history"].append({
        "step": "Certificate Auto-Issued",
        "timestamp": datetime.now().isoformat() + "Z"
    })
    
    data_manager.save_applications(applications)

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Digital Certificate API with Enhanced Payment Validation", "version": "2.0.0"}

@app.post("/apply", status_code=201)
async def submit_application(application: CertificateApplication, background_tasks: BackgroundTasks):
    """🔐 Submit a new certificate application with auto-processing"""
    try:
        # Load existing applications
        applications = data_manager.load_applications()
        
        # Generate unique application ID
        application_id = data_manager.generate_application_id()
        
        # Create application record
        app_record = {
            "application_id": application_id,
            "status": "Pending",
            "current_step": "Document Verification",
            "submission_date": datetime.now().isoformat(),
            "name": application.name,
            "nric": application.nric,
            "passport": application.passport,
            "dob": application.dob,
            "nationality": application.nationality,
            "email": application.email,
            "organisation": application.organisation,
            "address": application.address,
            "certificate_type": application.certificate_type,
            "payment_mode": application.payment_mode,
            "attachments": [att.dict() for att in application.attachments] if application.attachments else [],
            "auto_processing": True,
            "history": [
                {
                    "step": "Submitted",
                    "timestamp": datetime.now().isoformat() + "Z"
                },
                {
                    "step": "Documents Received",
                    "timestamp": (datetime.now() + timedelta(minutes=1)).isoformat() + "Z"
                }
            ]
        }
        
        # Add to applications list
        applications.append(app_record)
        
        # Save to JSON
        data_manager.save_applications(applications)
        
        # Add audit log
        data_manager.add_audit_log(application_id, "Application submitted - auto-processing initiated")
        
        # Start background auto-processing
        background_tasks.add_task(process_application_automatically, application_id, app_record)
        
        return {
            "application_id": application_id,
            "status": "Pending",
            "auto_processing": True,
            "estimated_completion": "8-12 seconds",
            "message": "Application submitted successfully. Enhanced payment validation initiated."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing application: {str(e)}")

@app.get("/application/{application_id}")
async def get_application_status(application_id: str):
    """🧾 Check status of an application"""
    try:
        applications = data_manager.load_applications()
        
        # Find application
        application = None
        for app in applications:
            if app["application_id"] == application_id:
                application = app
                break
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "application_id": application_id,
            "status": application["status"],
            "current_step": application["current_step"],
            "auto_processing": application.get("auto_processing", False),
            "certificate_id": application.get("certificate_id"),
            "payment_validation_details": application.get("payment_validation_details"),
            "history": application.get("history", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving application: {str(e)}")

@app.post("/validate-payment-manual")
async def validate_payment_manual(payment_request: PaymentValidationRequest):
    """💳 Manual payment validation with 3-criteria assessment"""
    try:
        # Validate payment with 3 criteria
        validation_result = await payment_validator.validate_payment(payment_request)
        
        # Update application based on validation results
        if validation_result.overall_status == "APPROVED":
            await internal_validate_payment_success(payment_request.application_id, validation_result)
            data_manager.add_audit_log(
                payment_request.application_id, 
                f"Payment manually validated - Score: {validation_result.overall_score}/100"
            )
        else:
            await internal_validate_payment_failure(payment_request.application_id, validation_result)
            data_manager.add_audit_log(
                payment_request.application_id, 
                f"Payment manual validation failed - Score: {validation_result.overall_score}/100"
            )
        
        return {
            "application_id": payment_request.application_id,
            "validation_result": validation_result.dict(),
            "method": "Manual"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating payment: {str(e)}")

@app.post("/issue-certificate")
async def issue_certificate(issuance: CertificateIssuance):
    """📜 Simulate issuance of the digital certificate (Manual override)"""
    try:
        await internal_issue_certificate(issuance)
        
        # Get the issued certificate details
        certificates = data_manager.load_certificates()
        certificate = None
        for cert in certificates:
            if cert.get("application_id") == issuance.application_id:
                certificate = cert
                break
        
        data_manager.add_audit_log(issuance.application_id, f"Certificate manually issued: {certificate['certificate_id']}")
        
        return {
            "application_id": issuance.application_id,
            "certificate_id": certificate["certificate_id"],
            "status": "Issued",
            "validity": f"{certificate['validity']['start']} to {certificate['validity']['end']}",
            "delivery_medium": certificate["delivery_medium"],
            "download_url": f"https://example.com/certificates/{certificate['certificate_id']}.pem",
            "method": "Manual"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error issuing certificate: {str(e)}")

@app.get("/certificate/{identifier}")
async def get_certificate_info(identifier: str):
    """🧪 View certificate info & validity - accepts certificate ID or application ID"""
    try:
        certificates = data_manager.load_certificates()
        
        # Find certificate by certificate_id first
        certificate = None
        for cert in certificates:
            if cert["certificate_id"] == identifier:
                certificate = cert
                break
        
        # If not found by certificate_id, try by application_id
        if not certificate:
            for cert in certificates:
                if cert.get("application_id") == identifier:
                    certificate = cert
                    break
        
        if not certificate:
            # Check if it's an application that hasn't been issued yet
            applications = data_manager.load_applications()
            for app in applications:
                if app["application_id"] == identifier:
                    return {
                        "error": "Certificate not yet issued",
                        "application_id": identifier,
                        "current_status": app["status"],
                        "current_step": app["current_step"],
                        "auto_processing": app.get("auto_processing", False),
                        "payment_validation_details": app.get("payment_validation_details"),
                        "message": "Processing in progress" if app.get("auto_processing") else "Complete payment validation and certificate issuance first"
                    }
            
            raise HTTPException(status_code=404, detail="Certificate or application not found")
        
        return {
            "certificate_id": certificate["certificate_id"],
            "application_id": certificate.get("application_id"),
            "name": certificate["name"],
            "status": certificate["status"],
            "validity": certificate["validity"],
            "revoked": certificate["revoked"],
            "issue_date": certificate.get("issue_date"),
            "delivery_medium": certificate.get("delivery_medium"),
            "organisation": certificate.get("organisation"),
            "email": certificate.get("email"),
            "auto_issued": certificate.get("auto_issued", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving certificate: {str(e)}")

@app.get("/audit-trail")
async def get_audit_trail(application_id: str):
    """🧾 Return application trace logs"""
    try:
        return data_manager.get_audit_trail(application_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit trail: {str(e)}")

@app.get("/applications")
async def list_all_applications():
    """List all applications (for admin use)"""
    try:
        applications = data_manager.load_applications()
        return {
            "total_applications": len(applications),
            "applications": applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving applications: {str(e)}")

@app.get("/certificates")
async def list_all_certificates():
    """List all certificates (for admin use)"""
    try:
        certificates = data_manager.load_certificates()
        return {
            "total_certificates": len(certificates),
            "certificates": certificates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving certificates: {str(e)}")

@app.get("/payments")
async def list_all_payments():
    """List all payment validation records (for admin use)"""
    try:
        payments = data_manager.load_payments()
        return {
            "total_payments": len(payments),
            "payments": payments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving payments: {str(e)}")

@app.post("/certificate/{certificate_id}/revoke")
async def revoke_certificate(certificate_id: str):
    """Revoke a certificate"""
    try:
        certificates = data_manager.load_certificates()
        
        # Find and update certificate
        cert_index = None
        for i, cert in enumerate(certificates):
            if cert["certificate_id"] == certificate_id:
                cert_index = i
                break
        
        if cert_index is None:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        certificates[cert_index]["status"] = "Revoked"
        certificates[cert_index]["revoked"] = True
        certificates[cert_index]["revocation_date"] = datetime.now().isoformat()
        
        data_manager.save_certificates(certificates)
        
        return {
            "certificate_id": certificate_id,
            "status": "Revoked",
            "revocation_date": certificates[cert_index]["revocation_date"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking certificate: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)