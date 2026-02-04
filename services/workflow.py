from models.invoice import InvoiceStatus

class WorkflowService:
    """
    Simplified Workflow Service.
    Handles invoice status transitions only.
    """
    
    def transition_status(self, current_status: InvoiceStatus, action: str) -> InvoiceStatus:
        """
        Calculates the next status based on admin action.
        PENDING -> APPROVED -> PAID
        """
        if action == "approve":
            return InvoiceStatus.APPROVED
        elif action == "reject":
            return InvoiceStatus.REJECTED
        elif action == "pay":
            return InvoiceStatus.PAID
        return current_status

workflow_service = WorkflowService()
