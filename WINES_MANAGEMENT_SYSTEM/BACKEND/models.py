"""
Wines Management System - SQLAlchemy ORM Models
Defines tables: supplier, wine, customer, orders, order_details, inventory.
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import relationship
from database import Base

class Supplier(Base):
    __tablename__ = "supplier"

    supplier_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    wines = relationship("Wine", back_populates="supplier")


class Wine(Base):
    __tablename__ = "wine"

    wine_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wine_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=0)
    supplier_id = Column(Integer, ForeignKey("supplier.supplier_id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="wines")
    inventory = relationship("Inventory", back_populates="wine", uselist=False, cascade="all, delete-orphan")
    order_details = relationship("OrderDetail", back_populates="wine")


class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customer.customer_id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date = Column(DateTime, server_default=func.now())
    total_amount = Column(Numeric(10, 2), default=0.00)
    payment_status = Column(String(30), default="Pending")
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order", cascade="all, delete-orphan")


class OrderDetail(Base):
    __tablename__ = "order_details"

    order_detail_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    wine_id = Column(Integer, ForeignKey("wine.wine_id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="order_details")
    wine = relationship("Wine", back_populates="order_details")


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wine_id = Column(Integer, ForeignKey("wine.wine_id", ondelete="CASCADE"), nullable=False, index=True)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    wine = relationship("Wine", back_populates="inventory")
