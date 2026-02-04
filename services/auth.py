import hashlib
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta

class AuthService:
    def __init__(self):
        from passlib.context import CryptContext
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if not hashed_password: 
            return False
            
        # Standard Bcrypt Verify
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Fallback for simple hex-hashes during dev/test if needed
            return plain_password == hashed_password
    
    def authenticate(self, email: str, password: str) -> Optional[dict]:
        """Verify credentials against DB and create persistent session."""
        from models.database import SessionLocal
        from models.user import User
        from models.session import Session as UserSession
        
        email = email.lower().strip()
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user or not self.verify_password(password, user.password_hash):
                return None
            
            if not user.is_active:
                from core.error_handler import AuthenticationError
                raise AuthenticationError("Account is pending admin approval")
            
            # Create session token
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            from core.config import settings
            
            vendor_id = user.vendor_id if user.role == "vendor" else None

            # Store session in database (persistent)
            expires_at = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            session_record = UserSession(
                token=token_hash,
                user_id=user.id,
                vendor_id=vendor_id,
                expires_at=expires_at
            )
            db.add(session_record)
            db.commit()
            
            return {"token": raw_token, "id": user.id, "name": user.name, "role": user.role, "vendor_id": vendor_id}
        finally:
            db.close()

    def register_vendor(self, data: dict) -> dict:
        """Register a new vendor and associated user."""
        from models.database import SessionLocal
        from models.user import User
        from models.vendor import Vendor
        
        # Password validation: 6-72 characters, alphanumeric suggestion
        password = data.get('password', '')
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if len(password) > 72:
            raise ValueError("Password cannot be longer than 72 characters")
        
        # Suggested complexity: At least one letter and one number
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise ValueError("Password should contain both letters and numbers for better security")

        db = SessionLocal()
        try:
            # Check if email exists
            existing_user = db.query(User).filter(User.email == data['email']).first()
            if existing_user:
                raise ValueError("Email already registered")
                
            # Create Vendor
            new_vendor = Vendor(
                company_name=data['company_name'],
                contact_person=data['contact_person'],
                email=data['email'],
                mobile=data.get('mobile'),
                status="pending"
            )
            db.add(new_vendor)
            db.flush() # Get ID
            
            # Create User
            pwd_hash = self._hash_password(data['password'])
            new_user = User(
                email=data['email'],
                name=data['contact_person'],
                password_hash=pwd_hash,
                role="vendor",
                vendor_id=new_vendor.id,
                is_active=True # Allow login but vendor status is pending
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Auto-login (create session)
            return self.authenticate(data['email'], data['password'])
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def validate_session(self, token: str) -> Optional[dict]:
        """Check if session token is valid in database."""
        from models.database import SessionLocal
        from models.session import Session as UserSession
        from models.user import User
        
        # Hash the incoming token to lookup
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        db = SessionLocal()
        try:
            session_record = db.query(UserSession).filter(UserSession.token == token_hash).first()
            if not session_record or datetime.now() > session_record.expires_at:
                return None
            
            user = db.query(User).filter(User.id == session_record.user_id).first()
            if not user:
                return None
            
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "vendor_id": session_record.vendor_id
            }
        finally:
            db.close()

    def logout(self, token: str) -> bool:
        """Invalidate session by deleting from database."""
        from models.database import SessionLocal
        from models.session import Session as UserSession
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        db = SessionLocal()
        try:
            session_record = db.query(UserSession).filter(UserSession.token == token_hash).first()
            if session_record:
                db.delete(session_record)
                db.commit()
                return True
            return False
        finally:
            db.close()

auth_service = AuthService()
