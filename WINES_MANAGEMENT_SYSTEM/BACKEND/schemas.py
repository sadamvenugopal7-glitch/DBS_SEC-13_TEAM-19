"""
Wines Management System - Pydantic Schemas
Defines request validation and response serializations for all API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator


# =====================================================================
# SUPPLIER SCHEMAS
# =====================================================================
class SupplierBase(BaseModel):
    supplier_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)

    @field_validator("supplier_name")
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Supplier name cannot be empty.")
        return v.strip()


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)


class SupplierOut(SupplierBase):
    supplier_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================================
# WINE SCHEMAS
# =====================================================================
class WineBase(BaseModel):
    wine_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0, description="Wine price must be greater than zero")
    quantity: int = Field(0, ge=0, description="Quantity cannot be negative")
    supplier_id: Optional[int] = None

    @field_validator("wine_name", "category")
    def validate_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip()


class WineCreate(WineBase):
    pass


class WineUpdate(BaseModel):
    wine_name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    supplier_id: Optional[int] = None


class WineOut(WineBase):
    wine_id: int
    supplier_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================================
# CUSTOMER SCHEMAS
# =====================================================================
class CustomerBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)

    @field_validator("customer_name")
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Customer name cannot be empty.")
        return v.strip()


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)


class CustomerOut(CustomerBase):
    customer_id: int
    total_orders: Optional[int] = 0
    total_spent: Optional[float] = 0.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================================
# INVENTORY SCHEMAS
# =====================================================================
class InventoryBase(BaseModel):
    wine_id: int
    stock_quantity: int = Field(0, ge=0, description="Stock cannot be negative")
    reorder_level: int = Field(10, ge=0, description="Reorder level cannot be negative")


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    stock_quantity: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)


class InventoryOut(InventoryBase):
    inventory_id: int
    wine_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = "AVAILABLE"
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================================
# ORDER & ORDER DETAILS SCHEMAS
# =====================================================================
class OrderItemCreate(BaseModel):
    wine_id: int
    quantity: int = Field(..., gt=0, description="Quantity must be at least 1")


class OrderCreate(BaseModel):
    customer_id: int
    payment_status: Optional[str] = "Paid"
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order must contain at least one item")


class OrderDetailOut(BaseModel):
    order_detail_id: int
    order_id: int
    wine_id: int
    wine_name: Optional[str] = None
    category: Optional[str] = None
    quantity: int
    unit_price: float
    line_total: Optional[float] = None

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    order_id: int
    customer_id: int
    customer_name: Optional[str] = None
    order_date: Optional[datetime] = None
    total_amount: float
    payment_status: str
    items_count: Optional[int] = 0
    items: Optional[List[OrderDetailOut]] = []

    class Config:
        from_attributes = True


# =====================================================================
# DASHBOARD & REPORTS SCHEMAS
# =====================================================================
class DashboardStatsOut(BaseModel):
    total_wines: int
    total_customers: int
    total_suppliers: int
    total_orders: int
    total_stock: int
    total_sales: float
    low_stock_count: int


class CategorySalesOut(BaseModel):
    category: str
    wine_count: int
    bottles_sold: int
    total_revenue: float


class MonthlySalesOut(BaseModel):
    month: str
    order_count: int
    revenue: float


# =====================================================================
# CSV IMPORT RESPONSE SCHEMA
# =====================================================================
class CSVImportResponse(BaseModel):
    success: bool
    inserted: int
    failed: int
    errors: List[str] = []
