# models.py
# SQLAlchemy ORM models based on the domain model specifications

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, BigInteger, JSON, Enum as SQLEnum, Date, Time, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from .DomainModel import Base
from ..orchestrator.fsm_spec import State, Event


# Enum definitions based on domain model
class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    """non termianl"""
    AWAITING = "AWAITING"
    """Payment status enumeration"""
    SUCCESS = "SUCCESS"
    DECLINED = "DECLINED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


# PaymentMethodCode enum removed - using String instead for flexibility


class DeviceType(str, Enum):
    """Device type enumeration"""
    KIOSK = "KIOSK"
    POS_TERMINAL = "POS_TERMINAL"
    FISCAL_PRINTER = "FISCAL_PRINTER"
    KKT = "KKT"


class AuthMethod(str, Enum):
    """Customer authentication method enumeration"""
    PSW = "PSW"
    SMS = "SMS"
    QR = "QR"
    NFC_DEVICE = "NFCDevice"
    OAUTH2 = "Oauth2"


class ActorType(str, Enum):
    """Actor types for FSM transitions"""
    CUSTOMER = "CUSTOMER"
    POS_TERMINAL = "POS_TERMINAL"
    FISCAL_DEVICE = "FISCAL_DEVICE"
    PRINTER = "PRINTER"
    KITCHEN = "KITCHEN"
    SYSTEM = "SYSTEM"


# Core domain models
class Role(Base):
    """User access control role"""
    __tablename__ = "roles"
    
    # Primary key
    name = Column(String(100), primary_key=True, unique=True)
    permissions = Column(JSONB, nullable=True)  # JSON permissions structure
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="role")


class User(Base):
    """Registered user of the system (admin, superadmin, staff)"""
    __tablename__ = "users"
    
    # Primary key
    user_id = Column(Integer, primary_key=True, index=True)
    
    # User identification
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for external auth
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    
    # Role relationship
    role_name = Column(String(100), ForeignKey("roles.name"), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    created_items = relationship("ItemLive", back_populates="creator", foreign_keys="ItemLive.created_by")
    # Removed stock_changes relationship since ItemLiveStockReplenishment.changed_by is now a string, not FK
    sessions = relationship("Session", back_populates="user")


class KnownCustomer(Base):
    """Identified customer using the kiosk"""
    __tablename__ = "known_customers"
    
    # Primary key
    customer_id = Column(BigInteger, primary_key=True, index=True)
    
    # Customer information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True, index=True)
    
    # Loyalty and authentication
    loyalty_card_code = Column(String(100), nullable=True, unique=True)
    auth_method = Column(SQLEnum(AuthMethod), nullable=True)
    
    # Customer lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    is_anonymous_link = Column(Boolean, default=False, nullable=True)
    
    # Relationships
    orders = relationship("Order", back_populates="customer")
    sessions = relationship("Session", back_populates="customer")


class Session(Base):
    """Active user or kiosk session"""
    __tablename__ = "sessions"
    
    # Primary key
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Session participants (nullable for anonymous sessions)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=True)
    customer_id = Column(BigInteger, ForeignKey("known_customers.customer_id"), nullable=True)
    
    # Session lifecycle
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    expired_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session token
    session_token = Column(String(500), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")
    customer = relationship("KnownCustomer", back_populates="sessions")
    orders = relationship("Order", back_populates="session")


class UnitOfMeasure(Base):
    """Register of measurement units"""
    __tablename__ = "units_of_measure"
    
    # Primary key
    name_eng = Column(String(100), primary_key=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    items = relationship("ItemLive", back_populates="unit_measure")


class FoodCategory(Base):
    """Food item categories (Drinks, Meals, Sauces, etc.)
    
    Additional labels reserved for future use (not used by current logic):
    - ru_label: Optional Russian UI label (String(200))
    - en_label: Optional English UI label (String(200))
    """
    __tablename__ = "food_categories"
    
    # Primary key
    name = Column(String(100), primary_key=True, unique=True)
    
    # Optional localized labels (reserved for future UI; nullable, no defaults)
    ru_label = Column(String(200), nullable=True)
    en_label = Column(String(200), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    items = relationship("ItemLive", back_populates="food_category")
    menu_categories = relationship("MenuCategory", back_populates="food_category")
    menu_items = relationship("MenuItem", back_populates="food_category")



class PromotedLabel(Base):
    """Promoted label configuration (single-record table).

    NOTE:
    - This is NOT a category. It is only for displaying the name of promoted items.
    - Business logic enforces that only one record should exist.
    - Example primary key value: "promoted"
    """
    __tablename__ = "promoted_label"

    # Primary key: human-readable name (e.g., "promoted")
    name = Column(String(100), primary_key=True, unique=True)

    # Optional localized labels for UI
    ru_label = Column(String(200), nullable=True)
    en_label = Column(String(200), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class ItemLive(Base):
    """Active menu items available for ordering"""
    __tablename__ = "items_live"
    
    # Primary key
    item_id = Column(BigInteger, primary_key=True, index=True)
    
    # Item names and descriptions
    name_ru= Column(String(200), nullable=False)
    name_eng = Column(String(200), nullable=True)
    description_ru = Column(Text, nullable=False)
    description_eng = Column(Text, nullable=True)
    
    # Item status
    is_active = Column(Boolean, default=True, nullable=False)
    promoted = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Unit of measure relationships
    unit_measure_name_eng = Column(String(100), ForeignKey("units_of_measure.name_eng"), nullable=False)
    
    # Pricing - all amounts in kopecks (integers)
    price_net_kopecks = Column(Integer, nullable=False, comment="Price net in kopecks")
    vat_rate = Column(Numeric(5, 2), nullable=True, comment="VAT rate as percentage")
    vat_amount_kopecks = Column(Integer, nullable=False, comment="VAT amount in kopecks")
    price_gross_kopecks = Column(Integer, nullable=False, comment="Price gross in kopecks")
    
    # Categories
    food_category_name = Column(String(100), ForeignKey("food_categories.name"), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="created_items", foreign_keys=[created_by])
    unit_measure = relationship("UnitOfMeasure", back_populates="items")
    food_category = relationship("FoodCategory", back_populates="items")
    availability = relationship("ItemLiveAvailable", back_populates="item", uselist=False)
    stock_changes = relationship("ItemLiveStockReplenishment", back_populates="item")


class Menu(Base):
    """Menu configuration - defines which categories and items are available"""
    __tablename__ = "menus"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Menu identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Menu activation status
    is_active = Column(Boolean, default=False, nullable=False)

    # Relationships
    menu_categories = relationship("MenuCategory", back_populates="menu", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="menu", cascade="all, delete-orphan")


class MenuCategory(Base):
    """Categories included in a specific menu with display ordering"""
    __tablename__ = "menu_categories"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True)
    food_category_name = Column(String(100), ForeignKey("food_categories.name", ondelete="RESTRICT"), nullable=False)
    
    # Display configuration
    display_order = Column(Integer, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=False)
    
   
    
    # Constraints
    __table_args__ = (
        # Ensure unique category per menu
        # Ensure unique display order per menu
        # Note: These constraints will be added in the migration
    )
    
    # Relationships
    menu = relationship("Menu", back_populates="menu_categories")
    food_category = relationship("FoodCategory")


class MenuItem(Base):
    """Items included in a specific menu with display ordering and category override"""
    __tablename__ = "menu_items"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(BigInteger, ForeignKey("items_live.item_id", ondelete="RESTRICT"), nullable=False)
    food_category_name = Column(String(100), ForeignKey("food_categories.name", ondelete="RESTRICT"), nullable=False)

    # Display configuration
    display_order = Column(Integer, nullable=False)

    # Time-based visibility control
    start_at = Column(Time, nullable=True, comment="Time when this item should start displaying")
    end_at = Column(Time, nullable=True, comment="Time when this item should stop displaying")

    # Relationships
    menu = relationship("Menu", back_populates="menu_items")
    item = relationship("ItemLive")
    food_category = relationship("FoodCategory")


class ItemLiveAvailable(Base):
    """Current stock availability for active items"""
    __tablename__ = "items_live_available"
    
    # Primary key (also foreign key to ItemLive)
    item_id = Column(BigInteger, ForeignKey("items_live.item_id", ondelete="CASCADE"), 
                     primary_key=True, index=True)
    
    # Stock quantities
    stock_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    
    # Unit snapshots from ItemLive
    unit_name_ru = Column(String(100), nullable=False)
    unit_name_eng = Column(String(100), nullable=True)
    
    # Relationships
    item = relationship("ItemLive", back_populates="availability")


class ItemLiveStockReplenishment(Base):
    """Stock replenishment history for items"""
    __tablename__ = "items_live_stock_replenishment"
    
    # Primary key
    operation_id = Column(BigInteger, primary_key=True, index=True)
    
    # Item reference
    item_id = Column(BigInteger, ForeignKey("items_live.item_id", ondelete="CASCADE"),
                     nullable=False, index=True)
    
    # Item snapshots at time of operation
    name_ru = Column(String(200), nullable=False)
    description_ru = Column(Text, nullable=False)
    unit_name_ru = Column(String(100), nullable=False)
    unit_name_eng = Column(String(100), nullable=True)
    
    # Stock change
    change_quantity = Column(Integer, nullable=False)
    
    # Audit fields
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(String(100), nullable=False)  # Changed from user_id FK to username string
    
    # Relationships
    item = relationship("ItemLive", back_populates="stock_changes")
    # Removed user relationship since changed_by is now a string, not FK


class Device(Base):
    """Registered hardware devices (kiosk, POS, fiscal printer, etc.)"""
    __tablename__ = "devices"
    
    # Primary key
    device_id = Column(Integer, primary_key=True, index=True)
    
    # Device identification
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    device_code = Column(String(50), nullable=False, unique=True, index=True)
    device_name = Column(String(200), nullable=False)
    
    # Location
    branch_name = Column(String(200), ForeignKey("branches.name"), nullable=True)
    
    # Network information
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    mac_address = Column(String(17), nullable=True)
    
    # Hardware information
    serial_number = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    device_os = Column(String(50), nullable=True)
    
    # Device status
    is_managed = Column(Boolean, default=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    branch = relationship("Branch", back_populates="devices")
    sessions = relationship("Session", back_populates="device")
    pos_terminal = relationship("POSTerminal", back_populates="device", uselist=False)
    fiscal_device = relationship("FiscalDevice", back_populates="device", uselist=False)


class Branch(Base):
    """Restaurant branch/location settings"""
    __tablename__ = "branches"
    
    # Primary key
    name = Column(String(200), primary_key=True)
    address = Column(JSONB, nullable=False)  # Structured address data
    work_hours = Column(JSONB, nullable=False)  # Operating hours structure
    legal_entity = Column(JSONB, nullable=False)  # Legal and tax information
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    devices = relationship("Device", back_populates="branch")


class Order(Base):
    """Customer orders/transactions"""
    __tablename__ = "orders"
    
    # Primary key
    order_id = Column(BigInteger, primary_key=True, index=True)
    order_date = Column(Date, nullable=False, index=True)
    
    # Order status and timing
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    order_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # Financial information - all amounts in kopecks (integers)
    currency = Column(String(3), nullable=False, default="643")  # ISO 4217 numeric code for RU
    total_amount_net_kopecks = Column(Integer, nullable=False, comment="Total net amount in kopecks")
    total_amount_vat_kopecks = Column(Integer, nullable=False, comment="Total VAT amount in kopecks")
    total_amount_gross_kopecks = Column(Integer, nullable=False, comment="Total gross amount in kopecks")
    
    # Customer and session
    customer_id = Column(BigInteger, ForeignKey("known_customers.customer_id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id"), nullable=True)
    
    # Pickup information
    pickup_number = Column(String(20), nullable=False, index=True)
    pin_code = Column(String(10), nullable=False)
    
    # Device snapshots (from session time)
    kiosk_id = Column(Integer, nullable=True)
    kiosk_ip = Column(String(45), nullable=True)
    kiosk_port = Column(String(10), nullable=True)
    pos_terminal_id = Column(Integer, nullable=True)
    pos_terminal_ip = Column(String(45), nullable=True)
    pos_terminal_port = Column(String(10), nullable=True)
    fiscal_machine_id = Column(Integer, nullable=True)
    fiscal_machine_ip = Column(String(45), nullable=True)
    fiscal_machine_port = Column(String(10), nullable=True)
    fiscal_printer_id = Column(Integer, nullable=True)
    fiscal_printer_ip = Column(String(45), nullable=True)
    fiscal_printer_port = Column(String(10), nullable=True)
    
    # Relationships
    customer = relationship("KnownCustomer", back_populates="orders")
    session = relationship("Session", back_populates="orders")
    payments = relationship("Payment", back_populates="order")
    order_items = relationship("OrderItem", back_populates="order")
    fsm_runtime = relationship("OrderFSMKioskRuntime", back_populates="order", uselist=False)
    lifecycle_logs = relationship("OrderLifecycleLog", back_populates="order")


class Payment(Base):
    """Payment details for orders"""
    __tablename__ = "payments"
    
    # Primary key
    payment_id = Column(BigInteger, primary_key=True, index=True)
    
    # Order reference
    order_id = Column(BigInteger, ForeignKey("orders.order_id"), nullable=False, index=True)
    
    # Payment timing
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Financial details - all amounts in kopecks (integers)
    currency = Column(String(3), nullable=True, default="RUB")
    total_amount_net_kopecks = Column(Integer, nullable=False, comment="Total net amount in kopecks")
    vat_rate = Column(Numeric(5, 2), nullable=False, comment="VAT rate as percentage")
    total_amount_vat_kopecks = Column(Integer, nullable=False, comment="Total VAT amount in kopecks")
    total_amount_gross_kopecks = Column(Integer, nullable=False, comment="Total gross amount in kopecks")
    
    # Payment method and status
    method_code = Column(String(50), ForeignKey("payment_methods.code"), nullable=True)
    status = Column(SQLEnum(PaymentStatus), nullable=True, default=PaymentStatus.AWAITING)
    
    # Transaction details
    transaction_id = Column(String(100), nullable=True, index=True)
    payment_details = Column(Text, nullable=True)
    pos_terminal_id = Column(Integer, nullable=True)
    
    # Response information
    response_code = Column(String(10), nullable=True)
    response_message = Column(String(500), nullable=True)
    
    # Receipt information from DC_INPAS
    response_raw_xml = Column(Text, nullable=True)  # Raw response from DC_INPAS
    customer_receipt = Column(Text, nullable=True)  # Customer receipt from DC response
    merchant_receipt = Column(Text, nullable=True)  # Merchant receipt from DC response
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    method = relationship("PaymentMethod", back_populates="payments")


class PaymentMethod(Base):
    """Available payment methods"""
    __tablename__ = "payment_methods"
    
    # Primary key
    code = Column(String(50), primary_key=True, unique=True)
    description_ru = Column(String(200), nullable=False)
    description_en = Column(String(200), nullable=False)
    
    # Method status
    is_active = Column(Boolean, default=True, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    payments = relationship("Payment", back_populates="method")


class POSTerminal(Base):
    """POS terminal specific configuration"""
    __tablename__ = "pos_terminals"
    
    # Primary key (also foreign key to Device)
    terminal_id = Column(Integer, ForeignKey("devices.device_id"), primary_key=True)
    
    # Banking details
    bank_terminal_id = Column(String(50), nullable=False)
    merchant_id = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    
    # Terminal configuration - amounts in kopecks (integers)
    supported_card_types = Column(JSONB, nullable=True)  # List of supported card types
    min_amount_kopecks = Column(Integer, nullable=True, comment="Minimum amount in kopecks")
    max_amount_kopecks = Column(Integer, nullable=True, comment="Maximum amount in kopecks")
    commission_rate = Column(Numeric(5, 2), nullable=True, comment="Commission rate as percentage")
    
    # Relationships
    device = relationship("Device", back_populates="pos_terminal")


class FiscalDevice(Base):
    """Fiscal printer/KKT configuration"""
    __tablename__ = "fiscal_devices"
    
    # Primary key (also foreign key to Device)
    fiscal_id = Column(Integer, ForeignKey("devices.device_id"), primary_key=True)
    
    # Fiscal details
    fiscal_number = Column(String(50), nullable=False)
    inn = Column(String(12), nullable=False)  # Russian tax ID
    fiscal_mode = Column(String(20), nullable=True)  # OSN, USN, ENVD
    
    # OFD integration
    ofd_provider = Column(String(100), nullable=True)
    certificate_expiry = Column(Date, nullable=True)
    last_fiscal_report = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="fiscal_device")


class OrderItem(Base):
    """Line within an order representing a selected item"""
    __tablename__ = "order_items"
    
    # Primary key
    item_in_order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Order reference
    order_id = Column(BigInteger, ForeignKey("orders.order_id"), nullable=False, index=True)
    
    # Item reference and snapshots
    item_id = Column(BigInteger, nullable=False)  # Snapshot of ItemLive.item_id
    name_ru = Column(String(200), nullable=False)  # Snapshot of ItemLive.name_ru
    name_eng = Column(String(200), nullable=True)  # Snapshot of ItemLive.name_eng
    description_ru = Column(Text, nullable=False)  # Snapshot of ItemLive.description_ru
    description_eng = Column(Text, nullable=True)  # Snapshot of ItemLive.description_eng
    
    # Unit of measure snapshots
    unit_of_measure_ru = Column(String(100), nullable=False)  # Snapshot of ItemLive.unit_measure
    unit_of_measure_eng = Column(String(100), nullable=True)  # Snapshot of ItemLive.unit_measure
    
    # Pricing snapshots - all amounts in kopecks (integers)
    item_price_net_kopecks = Column(Integer, nullable=False, comment="Item net price in kopecks (snapshot)")
    item_vat_rate = Column(Numeric(5, 2), nullable=False, comment="Item VAT rate as percentage (snapshot)")
    item_vat_amount_kopecks = Column(Integer, nullable=False, comment="Item VAT amount in kopecks (snapshot)")
    item_price_gross_kopecks = Column(Integer, nullable=False, comment="Item gross price in kopecks (snapshot)")
    
    # Order line details - all amounts in kopecks (integers)
    quantity = Column(Integer, nullable=False)
    total_price_net_kopecks = Column(Integer, nullable=False, comment="Total net price in kopecks")
    applied_vat_rate = Column(Numeric(5, 2), nullable=False, comment="Applied VAT rate as percentage")
    total_vat_amount_kopecks = Column(Integer, nullable=False, comment="Total VAT amount in kopecks")
    total_price_gross_kopecks = Column(Integer, nullable=False, comment="Total gross price in kopecks")
    
    # Customer preferences
    wishes = Column(String(500), nullable=True)  # Customer-specific wishes/options
    
    # Relationships
    order = relationship("Order", back_populates="order_items")


class OrderFSMKioskRuntime(Base):
    """FSM Kiosk runtime for order - reflects real order's way from payment to being picked-up"""
    __tablename__ = "order_fsm_kiosk_runtime"
    
    # Primary key
    order_fsm_kiosk_runtime_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Order reference
    order_id = Column(BigInteger, ForeignKey("orders.order_id"), nullable=False, unique=True, index=True)
    
    # Current FSM state - using State enum from fsm_spec
    fsm_kiosk_state = Column(SQLEnum(State), nullable=False, default=State.INIT)
    
    # Payment session context
    payment_session_id = Column(String(100), nullable=True)
    pos_terminal_id = Column(Integer, ForeignKey("devices.device_id"), nullable=True)
    payment_attempt_started_at = Column(DateTime(timezone=True), nullable=True)
    payment_attempt_response_at = Column(DateTime(timezone=True), nullable=True)
    payment_attempt_result_code = Column(String(50), nullable=True)
    payment_attempt_result_description = Column(JSONB, nullable=True)
    payment_id_transaction = Column(String(100), nullable=True)
    payment_slip_number_id = Column(String(100), nullable=True)
    
    # Fiscal session context
    fiscal_session_id = Column(String(100), nullable=True)
    fiscal_device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=True)
    fiscal_attempt_started_at = Column(DateTime(timezone=True), nullable=True)
    fiscal_attempt_response_at = Column(DateTime(timezone=True), nullable=True)
    fiscal_attempt_result_code = Column(String(50), nullable=True)
    fiscal_attempt_result_description = Column(JSONB, nullable=True)
    fiscal_id_transaction = Column(String(100), nullable=True)
    fiscalisation_number_id = Column(String(100), nullable=True)
    
    # Printing session context
    printing_session_id = Column(String(100), nullable=True)
    printing_device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=True)
    printing_attempt_started_at = Column(DateTime(timezone=True), nullable=True)
    printing_attempt_response_at = Column(DateTime(timezone=True), nullable=True)
    printing_attempt_result_code = Column(String(50), nullable=True)
    printing_attempt_result_description = Column(JSONB, nullable=True)
    
    # Pickup information
    pickup_code = Column(String(20), nullable=True)
    pin_code = Column(String(10), nullable=True)
    qr_code = Column(String(500), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="fsm_runtime")
    pos_terminal = relationship("Device", foreign_keys=[pos_terminal_id])
    fiscal_device = relationship("Device", foreign_keys=[fiscal_device_id])
    printing_device = relationship("Device", foreign_keys=[printing_device_id])


class OrderLifecycleLog(Base):
    """FSM Kiosk audit log for orders - logs every state transition during the lifetime of an order"""
    __tablename__ = "order_lifecycle_log"
    
    # Primary key
    order_lifecycle_log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Order reference
    order_id = Column(BigInteger, ForeignKey("orders.order_id"), nullable=False, index=True)
    
    # FSM Runtime reference
    order_fsm_kiosk_runtime_id = Column(UUID(as_uuid=True), 
                                       ForeignKey("order_fsm_kiosk_runtime.order_fsm_kiosk_runtime_id"), 
                                       nullable=True)
    
    # State transition details - using enums from fsm_spec
    from_state = Column(SQLEnum(State), nullable=True)
    to_state = Column(SQLEnum(State), nullable=False)
    trigger_event = Column(SQLEnum(Event), nullable=True)  # Nullable for initial state transitions
    
    # Actor information
    actor_type = Column(SQLEnum(ActorType), nullable=True)
    actor_id = Column(String(100), nullable=True)
    
    # Additional context
    comment = Column(Text, nullable=True)
    
    # Audit fields
    event_created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="lifecycle_logs")
    fsm_runtime = relationship("OrderFSMKioskRuntime")


class SlipReceipt(Base):
    """Slip receipts (e.g., printed or generated by POS terminal)"""
    __tablename__ = "slip_receipts"
    
    # Primary key
    slip_receipt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Order reference
    order_id = Column(BigInteger, ForeignKey("orders.order_id"), nullable=True, index=True)
    
    # Receipt details
    receipt_pos_terminal_returned_id = Column(String(100), nullable=True)
    receipt_body = Column(JSONB, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    order = relationship("Order")


class FiscalReceipt(Base):
    """Fiscal receipts (e.g., receipts printed by fiscal printer)"""
    __tablename__ = "fiscal_receipts"
    
    # Primary key
    fiscal_receipt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Order reference
    order_id = Column(BigInteger, ForeignKey("orders.order_id"), nullable=True, index=True)
    
    # Receipt details
    receipt_fiscal_machine_returned_id = Column(String(100), nullable=True)
    receipt_body = Column(JSONB, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    order = relationship("Order")


class SummaryReceipt(Base):
    """Summary check - a logical combination of slip and fiscal receipts with pickup info"""
    __tablename__ = "summary_receipts"
    
    # Primary key
    summary_receipt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Order reference
    order_id = Column(BigInteger, ForeignKey("orders.order_id"), nullable=True, index=True)
    
    # Receipt references
    slip_receipt_id = Column(UUID(as_uuid=True), ForeignKey("slip_receipts.slip_receipt_id"), nullable=True)
    fiscal_receipt_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_receipts.fiscal_receipt_id"), nullable=True)
    
    # Pickup information
    pickup_code = Column(String(20), nullable=True)
    pin_code = Column(String(10), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    order = relationship("Order")
    slip_receipt = relationship("SlipReceipt")
    fiscal_receipt = relationship("FiscalReceipt")


class KioskServiceMode(Base):
    """Service mode status for kiosk users - controls when kiosks should display service mode screen"""
    __tablename__ = "kiosk_service_mode"
    
    # Primary key
    service_mode_id = Column(Integer, primary_key=True, index=True)
    
    # Kiosk reference
    kiosk_username = Column(String(100), ForeignKey("users.username", ondelete="CASCADE"),
                           nullable=False, unique=True, index=True)
    
    # Service mode status
    is_service_mode = Column(Boolean, nullable=False, default=False)
    
    # Service picture configuration
    service_picture_name = Column(String(100), nullable=True)
    
    # Relationships
    kiosk_user = relationship("User")