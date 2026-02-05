from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Union
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
    mobile: str = Field(..., min_length=10, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    bank_account_no: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=255)
    ifsc_code: Optional[str] = Field(None, max_length=20)
    tds_applicable: Union[bool, int] = Field(False)
    tds_rate: Optional[float] = Field(0.0)
    tds_nature_of_payment: Optional[str] = Field(None, max_length=255)
    remarks: Optional[str] = None

    @field_validator("tds_applicable", mode="before")
    @classmethod
    def convert_tds_applicable(cls, v):
        """Convert int (0/1) to bool for form compatibility"""
        if isinstance(v, int):
            return bool(v)
        return v

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v):
        """Validate PAN format if provided"""
        if v and v.strip():
            v = v.strip().upper()
            if len(v) != 10:
                raise ValueError("PAN must be 10 characters")
            # Basic pattern check (can be made stricter if needed)
            if not v[:5].isalpha() or not v[5:9].isdigit() or not v[9].isalpha():
                raise ValueError("Invalid PAN format (e.g., ABCDE1234F)")
        return v if v and v.strip() else None

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v):
        """Validate GSTIN format if provided"""
        if v and v.strip():
            v = v.strip().upper()
            if len(v) != 15:
                raise ValueError("GSTIN must be 15 characters")
        return v if v and v.strip() else None

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v):
        """Validate IFSC format if provided"""
        if v and v.strip():
            v = v.strip().upper()
            if len(v) != 11:
                raise ValueError("IFSC must be 11 characters")
        return v if v and v.strip() else None

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        """Validate mobile number"""
        if v:
            # Remove any spaces or special characters
            v = ''.join(filter(str.isdigit, v))
            if len(v) < 10 or len(v) > 15:
                raise ValueError("Mobile must be 10-15 digits")
        return v

    @field_validator("tds_rate")
    @classmethod
    def validate_tds_rate(cls, v, info):
        tds_applicable = info.data.get("tds_applicable")
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
