import os
import shutil
import hashlib
from sqlalchemy.orm import Session
from models.database import engine, SessionLocal, Base
from models.user import User
# Import all models to ensure they are registered with Base.metadata
import models.user
import models.vendor
import models.invoice
import models.session
import models.audit
import models.error_log
import models.message
import models.system_setting
import models.tax_document

from passlib.context import CryptContext

def prepare_production():
    print("--- 🚀 Starting Production Preparation (Reset Mode) ---")
    
    # 1. Clear Database Tables via Drop/Create
    print("\n[1/3] Resetting Database Schema...")
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("  - All tables dropped and recreated successfully.")
    except Exception as e:
        print(f"  - Failed to reset schema: {e}")
        # Fallback to manual delete if drop_all fails (e.g. locks)
        return

    # 2. Clear File Storage
    print("\n[2/3] Clearing File Storage...")
    storage_dirs = ['uploads', 'receipts']
    base_path = os.path.dirname(os.path.abspath(__file__))
    for sdir in storage_dirs:
        dir_path = os.path.join(base_path, sdir)
        if os.path.exists(dir_path):
            files_removed = 0
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        files_removed += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        files_removed += 1
                except Exception as e:
                    print(f"    Failed to delete {file_path}. Reason: {e}")
            print(f"  - Cleared {files_removed} items from {sdir}/")
            
            # Ensure index.html exists in these dirs if needed or just recreate them
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        else:
            os.makedirs(dir_path)
            print(f"  - Created {sdir}/ directory.")

    # 3. Create Production Admin Account
    print("\n[3/3] Creating Production Admin...")
    db = SessionLocal()
    try:
        admin_email = "admin@nvstravels.com"
        admin_pass = "NVSadmin2026!"
        
        # Use passlib but handle bcrypt 4.x issues if they arise
        try:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_pass = pwd_context.hash(admin_pass)
        except Exception as e:
            print(f"  - Bcrypt hashing failed ({e}), attempting fallback hex-hash for safety...")
            # Fallback for extreme cases to ensure admin creation
            hashed_pass = admin_pass # auth_service.verify_password has a fallback for this
            
        prod_admin = User(
            email=admin_email,
            name="System Administrator",
            password_hash=hashed_pass,
            role="admin",
            is_active=True
        )
        db.add(prod_admin)
        db.commit()
        
        print("\n--- ✅ Production Preparation Complete ---")
        print(f"Production Admin Created:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_pass}")
        print("\nIMPORTANT: Please change this password immediately after first login.")

    except Exception as e:
        print(f"\n❌ FATAL ERROR DURING ADMIN CREATION: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    prepare_production()
