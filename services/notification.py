class NotificationService:
    """
    Simplified Notification Service for the NVS Vendor Portal.
    No SMTP or SMS gateway dependencies. Logs notifications to console.
    """
    
    def __init__(self):
        self.from_email = "noreply@nvstravels.com"
    
    def _log(self, channel: str, to: str, message: str):
        import logging
        logger = logging.getLogger("uvicorn")
        logger.info(f"[NOTIFICATION][{channel.upper()}] To: {to} | Message: {message}")

    async def send_email(self, to_email: str, subject: str, body_html: str) -> dict:
        self._log("email", to_email, f"Subject: {subject}")
        return {"success": True, "message": "Email logged to console"}
    
    async def send_sms(self, mobile: str, template_id: str, variables: dict) -> dict:
        self._log("sms", mobile, f"Template: {template_id}, Vars: {variables}")
        return {"success": True, "message": "SMS logged to console"}
    
    async def notify_invoice_approved(self, vendor_email: str, vendor_mobile: str, invoice_no: str, amount: str) -> dict:
        msg = f"Invoice {invoice_no} for ₹{amount} has been APPROVED."
        await self.send_email(vendor_email, f"Invoice {invoice_no} Approved", msg)
        await self.send_sms(vendor_mobile, "approved_tpl", {"invoice_no": invoice_no, "amt": amount})
        return {"success": True}
    
    async def notify_invoice_rejected(self, vendor_email: str, vendor_mobile: str, invoice_no: str, reason: str) -> dict:
        msg = f"Invoice {invoice_no} has been REJECTED. Reason: {reason}"
        await self.send_email(vendor_email, f"Invoice {invoice_no} Rejected", msg)
        await self.send_sms(vendor_mobile, "rejected_tpl", {"invoice_no": invoice_no, "reason": reason})
        return {"success": True}
    
    async def notify_info_required(self, vendor_email: str, vendor_mobile: str, invoice_no: str, info_needed: str) -> dict:
        msg = f"Additional info required for invoice {invoice_no}: {info_needed}"
        await self.send_email(vendor_email, f"Info Required: {invoice_no}", msg)
        return {"success": True}
    
    async def notify_payment_completed(self, vendor_email: str, vendor_mobile: str, invoice_no: str, amount: str, transaction_id: str) -> dict:
        msg = f"Payment for invoice {invoice_no} (₹{amount}) processed. UTR: {transaction_id}"
        await self.send_email(vendor_email, f"Payment Processed: {invoice_no}", msg)
        await self.send_sms(vendor_mobile, "payment_tpl", {"invoice_no": invoice_no, "utr": transaction_id})
        return {"success": True}

notification_service = NotificationService()
