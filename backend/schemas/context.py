from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, List, Any


class CompanyContextBase(BaseModel):
    """Base company context schema"""

    tone: Optional[str] = None
    company_description: Optional[str] = None
    products: Optional[List[str]] = None
    policies: Optional[Dict[str, Any]] = None
    faq: Optional[List[Dict[str, str]]] = None
    roles: Optional[Dict[str, str]] = None


class CompanyContextCreate(CompanyContextBase):
    """Company context creation schema"""

    pass


class CompanyContextUpdate(CompanyContextBase):
    """Company context update schema"""

    pass


class CompanyContextResponse(CompanyContextBase):
    """Company context response schema"""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
