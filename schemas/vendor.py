from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class VendorStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class VendorBase(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    entity_type: Optional[str] = Field("Company", max_length=50)
    contact_person: Optional[str] = Field(None, max_length=255)
    email: EmailStr
    mobile: str = Field(..., pattern=r"^[0-9]{10,12}$")
    pan: Optional[str] = Field(None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
    gstin: Optional[str] = Field(None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
    bank_account_no: Optional[str] = Field(None, min_length=9, max_length=18)
    bank_name: Optional[str] = Field(None, max_length=255)
    ifsc_code: Optional[str] = Field(None, pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    tds_applicable: bool = Field(False)
    tds_rate: Optional[float] = Field(0.0)
    tds_nature_of_payment: Optional[str] = Field(None, max_length=255)
    remarks: Optional[str] = None

    @field_validator("tds_rate")
    @classmethod
    def validate_tds_rate(cls, v, info):
        tds_applicable = info.data.get("tds_applicable")
        if not tds_applicable and v > 0:
            raise ValueError("TDS rate provided but TDS not applicable")
        if v is not None and (v < 0 or v > 100):
            raise ValueError("TDS rate must be between 0 and 100")
        return v

    # Document Path fields for onboarding
    pan_doc_path: Optional[str] = None
    gst_doc_path: Optional[str] = None
    msme_doc_path: Optional[str] = None
    coi_doc_path: Optional[str] = None
    cheque_doc_path: Optional[str] = None

class VendorCreate(VendorBase):
    pass

class Vendor(VendorBase):
    id: int
    status: VendorStatus
    kyc_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
