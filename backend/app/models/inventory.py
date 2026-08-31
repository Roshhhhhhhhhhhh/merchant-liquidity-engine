import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String(50), primary_key=True, index=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False, unique=True, index=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id"), nullable=False, index=True)
    available_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    days_in_stock = Column(Integer, default=0, nullable=False)
    batch_number = Column(String(50), nullable=True)
    location = Column(String(100), default="Main Warehouse - Pune", nullable=False)
    status = Column(String(20), default="Healthy", nullable=False)  # Healthy, Watch, Aging, Critical
    demand_trend = Column(String(20), default="Stable", nullable=False)  # Increasing, Stable, Softening, Declining
    last_restocked_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="inventory_items")
