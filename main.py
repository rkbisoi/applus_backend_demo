from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os
import uuid
import csv
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="Digital Certificate API",
    description="API for managing digital certificate applications",
    version="1.0.0"
)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

APPLICATIONS_FILE = DATA_DIR / "applications.json"
CERTIFICATES_FILE = DATA_DIR / "certificates.json"
AUDIT_LOGS_FILE = DATA_DIR / "audit_logs.json"
PAYMENTS_FILE = DATA_DIR / "payments.json"

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

class PaymentValidation(BaseModel):
    application_id: str
    payment_type: str
    bank_name: Optional[str] = None
    amount: float
    reference_no: str
    proof_url: Optional[str] = None

class CertificateIssuance(BaseModel):
    application_id: str

class AuditLogEntry(BaseModel):
    timestamp: str
    message: str

class ApplicationHistory(BaseModel):
    step: str
    timestamp: str

class ApplicationStatus(BaseModel):
    application_id: str
    status: str
    current_step: str
    history: List[ApplicationHistory]

# Utility functions for JSON file operations
def load_json_data(file_path: Path) -> List[Dict]:
    """Load data from JSON file"""
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_json_data(file_path: Path, data: List[Dict]):
    """Save data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def save_to_csv(file_path: Path, data: List[Dict], fieldnames: List[str]):
    """Save data to CSV file"""
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def generate_application_id() -> str:
    """Generate unique application ID"""
    return f"APP{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"

def generate_certificate_id() -> str:
    """Generate unique certificate ID"""
    return f"CERT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

def add_audit_log(application_id: str, message: str):
    """Add entry to audit log"""
    logs = load_json_data(AUDIT_LOGS_FILE)
    
    # Find existing application logs or create new entry
    app_logs = None
    for log_entry in logs:
        if log_entry.get("application_id") == application_id:
            app_logs = log_entry
            break
    
    if not app_logs:
        app_logs = {
            "application_id": application_id,
            "logs": []
        }
        logs.append(app_logs)
    
    # Add new log entry
    app_logs["logs"].append({
        "timestamp": datetime.now().isoformat() + "Z",
        "message": message
    })
    
    save_json_data(AUDIT_LOGS_FILE, logs)

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Digital Certificate API", "version": "1.0.0"}

@app.post("/apply", status_code=201)
async def submit_application(application: CertificateApplication):
    """🔐 Submit a new certificate application"""
    try:
        # Load existing applications
        applications = load_json_data(APPLICATIONS_FILE)
        
        # Generate unique application ID
        application_id = generate_application_id()
        
        # Create application record
        app_record = {
            "application_id": application_id,
            "status": "Pending Verification",
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
            "history": [
                {
                    "step": "Submitted",
                    "timestamp": datetime.now().isoformat() + "Z"
                },
                {
                    "step": "Documents Received",
                    "timestamp": (datetime.now() + timedelta(minutes=30)).isoformat() + "Z"
                }
            ]
        }
        
        # Add to applications list
        applications.append(app_record)
        
        # Save to JSON
        save_json_data(APPLICATIONS_FILE, applications)
        
        # Save to CSV for backup
        if applications:
            fieldnames = list(applications[0].keys())
            save_to_csv(DATA_DIR / "applications.csv", applications, fieldnames)
        
        # Add audit log
        add_audit_log(application_id, "Application submitted")
        
        return {
            "application_id": application_id,
            "status": "Pending Verification"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing application: {str(e)}")

@app.get("/application/{application_id}")
async def get_application_status(application_id: str):
    """🧾 Check status of an application"""
    try:
        applications = load_json_data(APPLICATIONS_FILE)
        
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
            "history": application.get("history", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving application: {str(e)}")

@app.post("/validate-payment")
async def validate_payment(payment: PaymentValidation):
    """💳 Validate payment method and simulate receipt"""
    try:
        applications = load_json_data(APPLICATIONS_FILE)
        payments = load_json_data(PAYMENTS_FILE)
        
        # Find application
        application = None
        app_index = None
        for i, app in enumerate(applications):
            if app["application_id"] == payment.application_id:
                application = app
                app_index = i
                break
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Create payment record
        payment_record = {
            "application_id": payment.application_id,
            "payment_type": payment.payment_type,
            "bank_name": payment.bank_name,
            "amount": payment.amount,
            "reference_no": payment.reference_no,
            "proof_url": payment.proof_url,
            "validation_date": datetime.now().isoformat(),
            "status": "Validated"
        }
        
        # Add payment record
        payments.append(payment_record)
        save_json_data(PAYMENTS_FILE, payments)
        
        # Update application status
        applications[app_index]["status"] = "Payment Validated"
        applications[app_index]["current_step"] = "Certificate Generation"
        applications[app_index]["payment_validated"] = True
        applications[app_index]["payment_date"] = datetime.now().isoformat()
        
        # Add to history
        if "history" not in applications[app_index]:
            applications[app_index]["history"] = []
        
        applications[app_index]["history"].append({
            "step": "Payment Validated",
            "timestamp": datetime.now().isoformat() + "Z"
        })
        
        save_json_data(APPLICATIONS_FILE, applications)
        
        # Add audit log
        add_audit_log(
            payment.application_id, 
            f"Payment validated with {payment.bank_name} REF: {payment.reference_no}"
        )
        
        return {
            "application_id": payment.application_id,
            "payment_status": "Validated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating payment: {str(e)}")

@app.post("/issue-certificate")
async def issue_certificate(issuance: CertificateIssuance):
    """📜 Simulate issuance of the digital certificate"""
    try:
        applications = load_json_data(APPLICATIONS_FILE)
        certificates = load_json_data(CERTIFICATES_FILE)
        
        # Find application
        application = None
        app_index = None
        for i, app in enumerate(applications):
            if app["application_id"] == issuance.application_id:
                application = app
                app_index = i
                break
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Check if payment is validated
        if not application.get("payment_validated", False):
            raise HTTPException(status_code=400, detail="Payment must be validated before certificate issuance")
        
        # Generate certificate ID
        certificate_id = generate_certificate_id()
        
        # Create certificate record
        certificate_record = {
            "certificate_id": certificate_id,
            "application_id": issuance.application_id,
            "name": application["name"],
            "status": "Valid",
            "issue_date": datetime.now().isoformat(),
            "validity": {
                "start": datetime.now().strftime("%Y-%m-%d"),
                "end": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")  # 1 year validity
            },
            "delivery_medium": application["certificate_type"],
            "revoked": False,
            "nric": application.get("nric"),
            "passport": application.get("passport"),
            "email": application["email"],
            "organisation": application.get("organisation"),
            "nationality": application["nationality"]
        }
        
        # Add certificate record
        certificates.append(certificate_record)
        save_json_data(CERTIFICATES_FILE, certificates)
        
        # Update application status
        applications[app_index]["status"] = "Issued"
        applications[app_index]["current_step"] = "Completed"
        applications[app_index]["certificate_id"] = certificate_id
        applications[app_index]["issue_date"] = datetime.now().isoformat()
        
        # Add to history
        applications[app_index]["history"].append({
            "step": "Certificate Issued",
            "timestamp": datetime.now().isoformat() + "Z"
        })
        
        save_json_data(APPLICATIONS_FILE, applications)
        
        # Add audit log
        add_audit_log(issuance.application_id, f"Certificate issued: {certificate_id}")
        
        return {
            "application_id": issuance.application_id,
            "certificate_id": certificate_id,
            "status": "Issued",
            "validity": f"{certificate_record['validity']['start']} to {certificate_record['validity']['end']}",
            "delivery_medium": certificate_record["delivery_medium"],
            "download_url": f"https://example.com/certificates/{certificate_id}.pem"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error issuing certificate: {str(e)}")

# @app.get("/certificate/{certificate_id}")
# async def get_certificate_info(certificate_id: str):
#     """🧪 View certificate info & validity"""
#     try:
#         certificates = load_json_data(CERTIFICATES_FILE)
        
#         # Find certificate
#         certificate = None
#         for cert in certificates:
#             if cert["certificate_id"] == certificate_id:
#                 certificate = cert
#                 break
        
#         if not certificate:
#             raise HTTPException(status_code=404, detail="Certificate not found")
        
#         return {
#             "certificate_id": certificate_id,
#             "name": certificate["name"],
#             "status": certificate["status"],
#             "validity": certificate["validity"],
#             "revoked": certificate["revoked"],
#             "issue_date": certificate.get("issue_date"),
#             "delivery_medium": certificate.get("delivery_medium"),
#             "organisation": certificate.get("organisation"),
#             "email": certificate.get("email")
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving certificate: {str(e)}")

@app.get("/certificate/{identifier}")
async def get_certificate_info(identifier: str):
    """🧪 View certificate info & validity - accepts certificate ID or application ID"""
    try:
        certificates = load_json_data(CERTIFICATES_FILE)
        
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
            applications = load_json_data(APPLICATIONS_FILE)
            for app in applications:
                if app["application_id"] == identifier:
                    return {
                        "error": "Certificate not yet issued",
                        "application_id": identifier,
                        "current_status": app["status"],
                        "current_step": app["current_step"],
                        "message": "Complete payment validation and certificate issuance first"
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
            "email": certificate.get("email")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving certificate: {str(e)}")

@app.get("/audit-trail")
async def get_audit_trail(application_id: str):
    """🧾 Return application trace logs"""
    try:
        logs = load_json_data(AUDIT_LOGS_FILE)
        
        # Find application logs
        app_logs = None
        for log_entry in logs:
            if log_entry.get("application_id") == application_id:
                app_logs = log_entry
                break
        
        if not app_logs:
            return {
                "application_id": application_id,
                "logs": []
            }
        
        return {
            "application_id": application_id,
            "logs": app_logs["logs"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit trail: {str(e)}")

# Additional helper endpoints

@app.get("/applications")
async def list_all_applications():
    """List all applications (for admin use)"""
    try:
        applications = load_json_data(APPLICATIONS_FILE)
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
        certificates = load_json_data(CERTIFICATES_FILE)
        return {
            "total_certificates": len(certificates),
            "certificates": certificates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving certificates: {str(e)}")

@app.post("/certificate/{certificate_id}/revoke")
async def revoke_certificate(certificate_id: str):
    """Revoke a certificate"""
    try:
        certificates = load_json_data(CERTIFICATES_FILE)
        
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
        
        save_json_data(CERTIFICATES_FILE, certificates)
        
        return {
            "certificate_id": certificate_id,
            "status": "Revoked",
            "revocation_date": certificates[cert_index]["revocation_date"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking certificate: {str(e)}")

@app.get("/export/applications")
async def export_applications_csv():
    """Export applications to CSV"""
    try:
        applications = load_json_data(APPLICATIONS_FILE)
        if not applications:
            raise HTTPException(status_code=404, detail="No applications found")
        
        csv_file = DATA_DIR / "applications_export.csv"
        fieldnames = list(applications[0].keys())
        save_to_csv(csv_file, applications, fieldnames)
        
        return FileResponse(
            path=csv_file,
            filename="applications_export.csv",
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting applications: {str(e)}")

@app.get("/export/certificates")
async def export_certificates_csv():
    """Export certificates to CSV"""
    try:
        certificates = load_json_data(CERTIFICATES_FILE)
        if not certificates:
            raise HTTPException(status_code=404, detail="No certificates found")
        
        csv_file = DATA_DIR / "certificates_export.csv"
        fieldnames = list(certificates[0].keys())
        save_to_csv(csv_file, certificates, fieldnames)
        
        return FileResponse(
            path=csv_file,
            filename="certificates_export.csv",
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting certificates: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)