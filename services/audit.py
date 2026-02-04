from sqlalchemy.orm import Session
from models.audit import AuditLog, AuditAction

import logging

class AuditService:
    def log_action(self, db: Session, actor_id: int, action: str, invoice_id: int = None, comment: str = None):
        """
        Logs an action to the audit trail.
        """
        from models.user import User
        
        try:
            # Fetch User details to snapshot
            actor = db.query(User).filter(User.id == actor_id).first()
            actor_name = actor.name if actor else "System"
            actor_role = actor.role if actor else "System"

            log_entry = AuditLog(
                action=action,
                invoice_id=invoice_id,
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role,
                comment=comment
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        except Exception as e:
            # We don't want audit failure to break the main transaction usually, 
            # but for strict compliance maybe we do. 
            logging.error(f"FAILED TO AUDIT LOG: {e}")
            # raise e # Suppress for now to keep flow running

audit_service = AuditService()
