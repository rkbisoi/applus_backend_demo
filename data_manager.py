import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from pathlib import Path

class DataManager:
    """
    Data Manager class for handling JSON file operations
    Manages applications, certificates, payments, and audit logs
    """
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize DataManager with data directory
        
        Args:
            data_directory: Directory to store JSON files
        """
        self.data_dir = Path(data_directory)
        self.data_dir.mkdir(exist_ok=True)
        
        # Define file paths
        self.applications_file = self.data_dir / "applications.json"
        self.certificates_file = self.data_dir / "certificates.json"
        self.payments_file = self.data_dir / "payments.json"
        self.audit_logs_file = self.data_dir / "audit_logs.json"
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize JSON files with empty arrays if they don't exist"""
        files_to_init = [
            self.applications_file,
            self.certificates_file,
            self.payments_file,
            self.audit_logs_file
        ]
        
        for file_path in files_to_init:
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
    
    def _read_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Read and parse JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of dictionaries from JSON file
        """
        try:
            if not file_path.exists():
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def _write_json_file(self, file_path: Path, data: List[Dict[str, Any]]):
        """
        Write data to JSON file
        
        Args:
            file_path: Path to JSON file
            data: List of dictionaries to write
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
            raise
    
    # Application Management Methods
    def load_applications(self) -> List[Dict[str, Any]]:
        """Load all applications from JSON file"""
        return self._read_json_file(self.applications_file)
    
    def save_applications(self, applications: List[Dict[str, Any]]):
        """Save applications to JSON file"""
        self._write_json_file(self.applications_file, applications)
    
    def get_application_by_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get specific application by ID"""
        applications = self.load_applications()
        for app in applications:
            if app.get("application_id") == application_id:
                return app
        return None
    
    def update_application(self, application_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific application
        
        Args:
            application_id: ID of application to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully, False if application not found
        """
        applications = self.load_applications()
        
        for i, app in enumerate(applications):
            if app.get("application_id") == application_id:
                applications[i].update(updates)
                applications[i]["last_updated"] = datetime.now().isoformat()
                self.save_applications(applications)
                return True
        
        return False
    
    def generate_application_id(self) -> str:
        """Generate unique application ID"""
        applications = self.load_applications()
        
        # Generate ID with format: APP_YYYYMMDD_HHMMSS_XXXX
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        counter = len(applications) + 1
        
        return f"APP_{timestamp}_{counter:04d}"
    
    # Certificate Management Methods
    def load_certificates(self) -> List[Dict[str, Any]]:
        """Load all certificates from JSON file"""
        return self._read_json_file(self.certificates_file)
    
    def save_certificates(self, certificates: List[Dict[str, Any]]):
        """Save certificates to JSON file"""
        self._write_json_file(self.certificates_file, certificates)
    
    def get_certificate_by_id(self, certificate_id: str) -> Optional[Dict[str, Any]]:
        """Get specific certificate by ID"""
        certificates = self.load_certificates()
        for cert in certificates:
            if cert.get("certificate_id") == certificate_id:
                return cert
        return None
    
    def get_certificate_by_application_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get certificate by application ID"""
        certificates = self.load_certificates()
        for cert in certificates:
            if cert.get("application_id") == application_id:
                return cert
        return None
    
    def update_certificate(self, certificate_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific certificate
        
        Args:
            certificate_id: ID of certificate to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully, False if certificate not found
        """
        certificates = self.load_certificates()
        
        for i, cert in enumerate(certificates):
            if cert.get("certificate_id") == certificate_id:
                certificates[i].update(updates)
                certificates[i]["last_updated"] = datetime.now().isoformat()
                self.save_certificates(certificates)
                return True
        
        return False
    
    def generate_certificate_id(self) -> str:
        """Generate unique certificate ID"""
        certificates = self.load_certificates()
        
        # Generate ID with format: CERT_YYYYMMDD_HHMMSS_XXXX
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        counter = len(certificates) + 1
        
        return f"CERT_{timestamp}_{counter:04d}"
    
    # Payment Management Methods
    def load_payments(self) -> List[Dict[str, Any]]:
        """Load all payment records from JSON file"""
        return self._read_json_file(self.payments_file)
    
    def save_payments(self, payments: List[Dict[str, Any]]):
        """Save payment records to JSON file"""
        self._write_json_file(self.payments_file, payments)
    
    def get_payments_by_application_id(self, application_id: str) -> List[Dict[str, Any]]:
        """Get all payment records for specific application"""
        payments = self.load_payments()
        return [payment for payment in payments if payment.get("application_id") == application_id]
    
    def add_payment_record(self, payment_record: Dict[str, Any]):
        """Add new payment record"""
        payments = self.load_payments()
        payment_record["created_at"] = datetime.now().isoformat()
        payments.append(payment_record)
        self.save_payments(payments)
    
    # Audit Log Management Methods
    def load_audit_logs(self) -> List[Dict[str, Any]]:
        """Load all audit logs from JSON file"""
        return self._read_json_file(self.audit_logs_file)
    
    def save_audit_logs(self, audit_logs: List[Dict[str, Any]]):
        """Save audit logs to JSON file"""
        self._write_json_file(self.audit_logs_file, audit_logs)
    
    def add_audit_log(self, application_id: str, action: str, details: Optional[Dict[str, Any]] = None):
        """
        Add new audit log entry
        
        Args:
            application_id: ID of related application
            action: Description of action performed
            details: Optional additional details
        """
        audit_logs = self.load_audit_logs()
        
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "application_id": application_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        audit_logs.append(log_entry)
        self.save_audit_logs(audit_logs)
    
    def get_audit_trail(self, application_id: str) -> Dict[str, Any]:
        """
        Get audit trail for specific application
        
        Args:
            application_id: ID of application
            
        Returns:
            Dictionary containing audit trail information
        """
        audit_logs = self.load_audit_logs()
        
        # Filter logs for this application
        app_logs = [log for log in audit_logs if log.get("application_id") == application_id]
        
        # Sort by timestamp
        app_logs.sort(key=lambda x: x.get("timestamp", ""))
        
        return {
            "application_id": application_id,
            "total_entries": len(app_logs),
            "audit_trail": app_logs,
            "first_entry": app_logs[0]["timestamp"] if app_logs else None,
            "last_entry": app_logs[-1]["timestamp"] if app_logs else None
        }
    
    # Utility Methods
    def backup_data(self, backup_suffix: Optional[str] = None) -> Dict[str, str]:
        """
        Create backup of all JSON files
        
        Args:
            backup_suffix: Optional suffix for backup files
            
        Returns:
            Dictionary mapping original files to backup file paths
        """
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_paths = {}
        files_to_backup = {
            "applications": self.applications_file,
            "certificates": self.certificates_file,
            "payments": self.payments_file,
            "audit_logs": self.audit_logs_file
        }
        
        for file_type, file_path in files_to_backup.items():
            if file_path.exists():
                backup_path = self.data_dir / f"{file_type}_backup_{backup_suffix}.json"
                
                # Copy file content
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                
                backup_paths[str(file_path)] = str(backup_path)
        
        return backup_paths
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        applications = self.load_applications()
        certificates = self.load_certificates()
        payments = self.load_payments()
        audit_logs = self.load_audit_logs()
        
        # Application statistics
        app_statuses = {}
        for app in applications:
            status = app.get("status", "Unknown")
            app_statuses[status] = app_statuses.get(status, 0) + 1
        
        # Certificate statistics
        cert_statuses = {}
        for cert in certificates:
            status = cert.get("status", "Unknown")
            cert_statuses[status] = cert_statuses.get(status, 0) + 1
        
        # Payment statistics
        payment_statuses = {}
        for payment in payments:
            status = payment.get("status", "Unknown")
            payment_statuses[status] = payment_statuses.get(status, 0) + 1
        
        return {
            "applications": {
                "total": len(applications),
                "by_status": app_statuses
            },
            "certificates": {
                "total": len(certificates),
                "by_status": cert_statuses
            },
            "payments": {
                "total": len(payments),
                "by_status": payment_statuses
            },
            "audit_logs": {
                "total": len(audit_logs)
            },
            "data_directory": str(self.data_dir),
            "last_updated": datetime.now().isoformat()
        }
    
    def clear_all_data(self, confirm: bool = False):
        """
        Clear all data (use with caution!)
        
        Args:
            confirm: Must be True to actually clear data
        """
        if not confirm:
            raise ValueError("Must set confirm=True to clear all data")
        
        # Create backup first
        backup_paths = self.backup_data("before_clear")
        
        # Clear all files
        for file_path in [self.applications_file, self.certificates_file, 
                         self.payments_file, self.audit_logs_file]:
            self._write_json_file(file_path, [])
        
        return {
            "message": "All data cleared successfully",
            "backup_created": backup_paths
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize data manager
    dm = DataManager()
    
    print("=== Data Manager Test ===")
    
    # Test application management
    print("\n1. Testing Application Management:")
    
    # Create sample application
    sample_app = {
        "application_id": dm.generate_application_id(),
        "name": "John Doe",
        "email": "john.doe@example.com",
        "status": "Pending",
        "certificate_type": "Smart Card",
        "submission_date": datetime.now().isoformat()
    }
    
    # Save application
    apps = dm.load_applications()
    apps.append(sample_app)
    dm.save_applications(apps)
    print(f"Created application: {sample_app['application_id']}")
    
    # Add audit log
    dm.add_audit_log(sample_app['application_id'], "Application submitted")
    print("Added audit log entry")
    
    # Test certificate management
    print("\n2. Testing Certificate Management:")
    
    sample_cert = {
        "certificate_id": dm.generate_certificate_id(),
        "application_id": sample_app['application_id'],
        "name": sample_app['name'],
        "status": "Valid",
        "issue_date": datetime.now().isoformat()
    }
    
    certs = dm.load_certificates()
    certs.append(sample_cert)
    dm.save_certificates(certs)
    print(f"Created certificate: {sample_cert['certificate_id']}")
    
    # Test statistics
    print("\n3. Data Statistics:")
    stats = dm.get_statistics()
    print(f"Applications: {stats['applications']['total']}")
    print(f"Certificates: {stats['certificates']['total']}")
    print(f"Audit Logs: {stats['audit_logs']['total']}")
    
    # Test audit trail
    print("\n4. Audit Trail:")
    audit_trail = dm.get_audit_trail(sample_app['application_id'])
    print(f"Audit entries for {sample_app['application_id']}: {audit_trail['total_entries']}")
    
    print("\n=== Test Completed Successfully ===")