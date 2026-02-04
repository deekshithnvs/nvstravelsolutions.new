from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    PENDING_CLARIFICATION = "pending_clarification"
    HOLD = "hold"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"

class InvoiceLineItem(BaseModel):
    description: str
    qty: Decimal
    rate: Decimal
    amount: Decimal

class InvoiceBase(BaseModel):
    invoice_no: str
    invoice_date: date
    amount: Decimal
    internal_remarks: Optional[Decimal] = Field(None)
    gst_amount: Optional[Decimal] = Field(None)
    taxable_value: Optional[Decimal] = Field(0)
    non_taxable_value: Optional[Decimal] = Field(0)
    discount: Optional[Decimal] = Field(0)
    cgst: Optional[Decimal] = Field(0)
    sgst: Optional[Decimal] = Field(0)
    igst: Optional[Decimal] = Field(0)

    @field_validator("gst_amount")
    @classmethod
    def validate_gst(cls, v, info):
        amount = info.data.get("amount")
        if v is not None and amount is not None and v > amount:
            raise ValueError("GST amount cannot exceed invoice amount")
        if v is not None and v < 0:
            raise ValueError("GST amount cannot be negative")
        return v

class InvoiceCreate(InvoiceBase):
    vendor_id: int

class Invoice(InvoiceBase):
    id: int
    vendor_id: int
    status: InvoiceStatus
    file_path: Optional[str] = None # Renamed to match model 'file_path'
    created_at: datetime
    line_items: List[InvoiceLineItem] = []

    model_config = ConfigDict(from_attributes=True)

class OCRResult(BaseModel):
    invoice_id: int
    extracted_json: dict
    confidence_score: float
    processed_at: datetime
