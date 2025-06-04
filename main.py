from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import random
from datetime import datetime, timedelta
import time
import json
import os
from pathlib import Path

app = FastAPI(title="Certificate Management API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Machine Pool Configuration
MACHINE_POOLS = {
    "USB Crypto Token": [
        {"id": "USB-001", "name": "USB Token Machine Alpha", "config": {"encryption": "AES-256", "driver": "PKCS#11"}},
        {"id": "USB-002", "name": "USB Token Machine Beta", "config": {"encryption": "RSA-2048", "driver": "PKCS#11"}},
        {"id": "USB-003", "name": "USB Token Machine Gamma", "config": {"encryption": "ECC-P256", "driver": "PKCS#11"}},
    ],
    "Smart Card": [
        {"id": "SC-001", "name": "Smart Card Reader Alpha", "config": {"protocol": "T=1", "voltage": "3V"}},
        {"id": "SC-002", "name": "Smart Card Reader Beta", "config": {"protocol": "T=0", "voltage": "5V"}},
        {"id": "SC-003", "name": "Smart Card Reader Gamma", "config": {"protocol": "T=1", "voltage": "1.8V"}},
    ],
    "Softcert": [
        {"id": "SOFT-001", "name": "Software Certificate Engine Alpha", "config": {"keystore": "PKCS#12", "algorithm": "RSA"}},
        {"id": "SOFT-002", "name": "Software Certificate Engine Beta", "config": {"keystore": "JKS", "algorithm": "ECDSA"}},
        {"id": "SOFT-003", "name": "Software Certificate Engine Gamma", "config": {"keystore": "PKCS#12", "algorithm": "EdDSA"}},
    ]
}

# JSON Database Configuration
DB_DIR = Path("json_db")
DB_DIR.mkdir(exist_ok=True)

APPLICATIONS_DB_FILE = DB_DIR / "applications.json"
CERTIFICATES_DB_FILE = DB_DIR / "certificates.json"
AUDIT_LOG_FILE = DB_DIR / "audit_log.json"

# Database Helper Functions
def load_json_db(file_path: Path, default_value=None):
    """Load data from JSON file"""
    if default_value is None:
        default_value = {}
    
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default_value
    return default_value

def save_json_db(file_path: Path, data):
    """Save data to JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_applications_db():
    """Get applications database"""
    return load_json_db(APPLICATIONS_DB_FILE, {})

def save_applications_db(data):
    """Save applications database"""
    save_json_db(APPLICATIONS_DB_FILE, data)

def get_certificates_db():
    """Get certificates database"""
    return load_json_db(CERTIFICATES_DB_FILE, {})

def save_certificates_db(data):
    """Save certificates database"""
    save_json_db(CERTIFICATES_DB_FILE, data)

def get_audit_log():
    """Get audit log"""
    return load_json_db(AUDIT_LOG_FILE, [])

def save_audit_log(data):
    """Save audit log"""
    save_json_db(AUDIT_LOG_FILE, data)

# Pydantic Models
class ApplicationRequest(BaseModel):
    name: str
    nric: Optional[str] = None
    passport: Optional[str] = None
    dob: str
    nationality: str
    email: str
    organisation: Optional[str] = None
    address: Optional[str] = None
    certificate_type: str  # USB Crypto Token, Smart Card, Softcert
    payment_mode: str = "Bank In"
    attachments: List[str] = []
    auto_processing: bool = False

class PaymentValidationRequest(BaseModel):
    application_id: str
    payment_type: str
    bank_name: str
    amount: float
    reference_no: str
    # machine_id: str
    proof_url: Optional[str] = None

class CertificateIssueRequest(BaseModel):
    application_id: str

# Utility Functions
def generate_application_id() -> str:
    """Generate unique application ID"""
    return f"APP{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"

def generate_certificate_id() -> str:
    """Generate unique certificate ID"""
    return f"CERT{datetime.now().strftime('%Y%m%d')}{random.randint(10000, 99999)}"

def assign_machine(certificate_type: str) -> Dict[str, Any]:
    """Randomly assign a machine from the pool based on certificate type"""
    if certificate_type not in MACHINE_POOLS:
        raise HTTPException(status_code=400, detail=f"Invalid certificate type: {certificate_type}")
    
    machines = MACHINE_POOLS[certificate_type]
    selected_machine = random.choice(machines)
    
    return {
        "machine_id": selected_machine["id"],
        "machine_name": selected_machine["name"],
        "machine_config": selected_machine["config"],
        "assigned_at": datetime.now().isoformat()
    }

def add_audit_log(application_id: str, action: str, details: str, status: str = "SUCCESS"):
    """Add entry to audit log"""
    audit_log = get_audit_log()
    audit_log.append({
        "application_id": application_id,
        "action": action,
        "details": details,
        "status": status,
        "timestamp": datetime.now().isoformat()
    })
    save_audit_log(audit_log)

def validate_payment_simple(payment_data: PaymentValidationRequest) -> Dict[str, Any]:
    """Simple payment validation with basic checks"""
    
    applications_db = get_applications_db()
    
    # Basic validation rules
    validation_results = {
        "amount_valid": payment_data.amount >= 100.0,  # Minimum amount
        "reference_valid": len(payment_data.reference_no) >= 6,  # Minimum reference length
        "bank_valid": payment_data.bank_name.strip() != "",
        "payment_type_valid": payment_data.payment_type in ["Bank In", "Online Transfer", "Credit Card"]
    }
    
    # Security checks (simplified)
    security_checks = {
        "duplicate_reference": payment_data.reference_no not in [
            app.get("payment_reference") for app in applications_db.values()
        ],
        "amount_range": 100.0 <= payment_data.amount <= 10000.0,
        "valid_format": payment_data.reference_no.isalnum()
    }
    
    all_valid = all(validation_results.values()) and all(security_checks.values())
    
    return {
        "valid": all_valid,
        "validation_results": validation_results,
        "security_checks": security_checks,
        "validated_at": datetime.now().isoformat()
    }

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Certificate Management API", "version": "1.0.0"}

@app.post("/apply")
async def submit_application(application: ApplicationRequest):
    """Submit certificate application"""
    
    applications_db = get_applications_db()
    
    try:
        # Generate application ID
        app_id = generate_application_id()
        
        # Assign machine from pool
        machine_info = assign_machine(application.certificate_type)
        
        # Create application record
        application_data = {
            "application_id": app_id,
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
            "attachments": application.attachments,
            "assigned_machine": machine_info,
            "status": "PENDING",
            "submission_date": datetime.now().isoformat(),
            "payment_validated": False,
            "certificate_issued": False
        }
        
        applications_db[app_id] = application_data
        save_applications_db(applications_db)
        
        add_audit_log(app_id, "APPLICATION_SUBMITTED", f"Application submitted for {application.name}")
        add_audit_log(app_id, "MACHINE_ASSIGNED", f"Machine {machine_info['machine_id']} assigned")
        
        response = {
            "application_id": app_id,
            "status": "PENDING",
            "assigned_machine": machine_info,
            "message": "Application submitted successfully"
        }
        
        # Auto processing if requested
        if application.auto_processing:
            
            # Simulate payment validation
            time.sleep(1)  # Simulate processing time
            fake_payment = PaymentValidationRequest(
                application_id=app_id,
                payment_type=application.payment_mode,
                bank_name="Auto Bank",
                amount=250.0,
                # machine_id=machine_info["machine_id"],
                reference_no=f"AUTO{random.randint(100000, 999999)}"
            )
            
            print("fake",fake_payment)
            
            payment_result = validate_payment_simple(fake_payment)
            
            if payment_result["valid"]:
                applications_db = get_applications_db()  # Reload to get latest data
                applications_db[app_id]["payment_validated"] = True
                applications_db[app_id]["payment_reference"] = fake_payment.reference_no
                applications_db[app_id]["status"] = "CERTIFICATE_ISSUED"
                save_applications_db(applications_db)
                
                add_audit_log(app_id, "CERTIFICATE_ISSUED", "Auto payment validation successful")
                
                # Issue certificate
                time.sleep(1)  # Simulate processing time
                cert_id = generate_certificate_id()
                
                certificate_data = {
                    "certificate_id": cert_id,
                    "application_id": app_id,
                    "holder_name": application.name,
                    "certificate_type": application.certificate_type,
                    "issued_date": datetime.now().isoformat(),
                    "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
                    "status": "ACTIVE",
                    "serial_number": f"SN{random.randint(1000000, 9999999)}",
                    "machine_used": machine_info["machine_id"]
                }
                
                certificates_db = get_certificates_db()
                certificates_db[cert_id] = certificate_data
                save_certificates_db(certificates_db)
                
                applications_db = get_applications_db()  # Reload again
                applications_db[app_id]["certificate_id"] = cert_id
                applications_db[app_id]["certificate_issued"] = True
                applications_db[app_id]["status"] = "CERTIFICATE_ISSUED"
                save_applications_db(applications_db)
                
                add_audit_log(app_id, "CERTIFICATE_ISSUED", f"Certificate {cert_id} issued successfully")
                
                response.update({
                    "certificate_id": cert_id,
                    "status": "CERTIFICATE_ISSUED",
                    "payment_validated": True,
                    "auto_processing_completed": True
                })
        
        return response
        
    except Exception as e:
        add_audit_log(app_id if 'app_id' in locals() else "UNKNOWN", "ERROR", str(e), "FAILED")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate-payment")
async def validate_payment(payment_data: PaymentValidationRequest):
    """Validate payment for an application"""
    
    applications_db = get_applications_db()
    
    if payment_data.application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application = applications_db[payment_data.application_id]

    # Check if provided machine_id matches assigned one
    # assigned_machine_id = application.get("assigned_machine", {}).get("machine_id")
    # if assigned_machine_id != payment_data.machine_id:
    #     add_audit_log(payment_data.application_id, "PAYMENT_VALIDATION_FAILED",
    #                   f"Machine mismatch: expected {assigned_machine_id}, got {payment_data.machine_id}",
    #                   status="FAILED")
    #     raise HTTPException(status_code=400, detail=f"Machine ID mismatch. Expected {assigned_machine_id}")
    
    try:
        validation_result = validate_payment_simple(payment_data)
        
        if validation_result["valid"]:
            application["payment_validated"] = True
            application["payment_reference"] = payment_data.reference_no
            application["status"] = "CERTIFICATE_ISSUED"
            application["payment_details"] = payment_data.dict()
            save_applications_db(applications_db)
            
            add_audit_log(payment_data.application_id, "CERTIFICATE_ISSUED", 
                          f"Payment validated with reference {payment_data.reference_no} on machine {payment_data.application_id}")
        else:
            add_audit_log(payment_data.application_id, "PAYMENT_VALIDATION_FAILED", 
                          f"Validation checks failed on machine {payment_data.application_id}", "FAILED")
        
        return {
            "application_id": payment_data.application_id,
            "validation_result": validation_result,
            "status": "CERTIFICATE_ISSUED" if validation_result["valid"] else "PAYMENT_FAILED"
        }
        
    except Exception as e:
        add_audit_log(payment_data.application_id, "PAYMENT_ERROR", str(e), "FAILED")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/issue-certificate")
async def issue_certificate(request: CertificateIssueRequest):
    """Issue certificate for validated application"""
    
    applications_db = get_applications_db()
    
    if request.application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application = applications_db[request.application_id]
    
    if not application["payment_validated"]:
        raise HTTPException(status_code=400, detail="Payment not validated")
    
    if application["certificate_issued"]:
        raise HTTPException(status_code=400, detail="Certificate already issued")
    
    try:
        cert_id = generate_certificate_id()
        
        certificate_data = {
            "certificate_id": cert_id,
            "application_id": request.application_id,
            "holder_name": application["name"],
            "certificate_type": application["certificate_type"],
            "issued_date": datetime.now().isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "status": "ACTIVE",
            "serial_number": f"SN{random.randint(1000000, 9999999)}",
            "machine_used": application["assigned_machine"]["machine_id"]
        }
        
        certificates_db = get_certificates_db()
        certificates_db[cert_id] = certificate_data
        save_certificates_db(certificates_db)
        
        applications_db[request.application_id]["certificate_id"] = cert_id
        applications_db[request.application_id]["certificate_issued"] = True
        applications_db[request.application_id]["status"] = "CERTIFICATE_ISSUED"
        save_applications_db(applications_db)
        
        add_audit_log(request.application_id, "CERTIFICATE_ISSUED", 
                     f"Certificate {cert_id} issued successfully")
        
        return {
            "certificate_id": cert_id,
            "application_id": request.application_id,
            "status": "CERTIFICATE_ISSUED",
            "certificate_details": certificate_data
        }
        
    except Exception as e:
        add_audit_log(request.application_id, "CERTIFICATE_ISSUE_ERROR", str(e), "FAILED")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/application/{application_id}")
async def get_application_status(application_id: str):
    """Get application status and details"""
    
    applications_db = get_applications_db()
    
    if application_id not in applications_db:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return applications_db[application_id]

@app.get("/certificate/{application_id}")
async def get_certificate_info(application_id: str):
    """Get certificate information"""
    
    certificates = get_certificates_db()
    for cert in certificates.values():
        if cert["application_id"] == application_id:
            return cert
    raise HTTPException(status_code=404, detail="Certificate with given application ID not found")

@app.get("/applications")
async def get_all_applications():
    """Get all applications"""
    applications_db = get_applications_db()
    return {
        "applications": list(applications_db.values()),
        "total_count": len(applications_db)
    }

@app.get("/certificates")
async def get_all_certificates():
    """Get all certificates"""
    certificates_db = get_certificates_db()
    return {
        "certificates": list(certificates_db.values()),
        "total_count": len(certificates_db)
    }

@app.get("/audit-trail")
async def get_audit_trail(application_id: Optional[str] = None):
    """Get audit trail"""
    
    audit_log = get_audit_log()
    
    if application_id:
        filtered_logs = [log for log in audit_log if log["application_id"] == application_id]
        return {"audit_trail": filtered_logs}
    
    return {"audit_trail": audit_log}

@app.post("/certificate/{certificate_id}/revoke")
async def revoke_certificate(certificate_id: str):
    """Revoke a certificate"""
    
    certificates_db = get_certificates_db()
    
    if certificate_id not in certificates_db:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    certificates_db[certificate_id]["status"] = "REVOKED"
    certificates_db[certificate_id]["revoked_date"] = datetime.now().isoformat()
    
    applications_db = get_applications_db()
    
    # Find and update application
    for app in applications_db.values():
        if app.get("certificate_id") == certificate_id:
            app["status"] = "CERTIFICATE_REVOKED"
            add_audit_log(app["application_id"], "CERTIFICATE_REVOKED", 
                         f"Certificate {certificate_id} revoked")
            break
    
    return {
        "certificate_id": certificate_id,
        "status": "REVOKED",
        "message": "Certificate revoked successfully"
    }

@app.get("/machine-pools")
async def get_machine_pools():
    """Get machine pool information"""
    return {
        "machine_pools": MACHINE_POOLS,
        "total_machines": sum(len(machines) for machines in MACHINE_POOLS.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)