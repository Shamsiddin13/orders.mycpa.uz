from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text, BigInteger, Boolean, func, text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, index=True, server_default=text("nextval('products_id_seq'::regclass)"))
    name = Column(String(255), nullable=False)
    article = Column(String(255), nullable=True)
    sku = Column(String(255), nullable=False)
    ikpu = Column(String(255), nullable=True)
    categories_name = Column(String(255), nullable=True)
    categories_id = Column(BigInteger, nullable=True)
    store_name = Column(String(255), nullable=True)
    store_id = Column(BigInteger, nullable=True)
    min_price = Column(Numeric(10,2), nullable=True)
    max_price = Column(Numeric(10,2), nullable=True)
    img = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Relationship with ProductOffer
    offers = relationship("ProductOffer", back_populates="product")

class ProductOffer(Base):
    __tablename__ = "product_offers"

    id = Column(BigInteger, primary_key=True, index=True, server_default=text("nextval('product_offers_id_seq'::regclass)"))
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    name = Column(String(255), nullable=False)
    sku = Column(String(255), nullable=False)
    buy_price = Column(Numeric(10,2), nullable=False)
    sell_price = Column(Numeric(10,2), nullable=False)
    weight = Column(Numeric(10,2), nullable=True)
    img = Column(String(255), nullable=True)
    is_available = Column(String(24), nullable=False, server_default=text("'stock'::character varying"))
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Relationship with Product
    product = relationship("Product", back_populates="offers")

class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, index=True, server_default=text("nextval('orders_id_seq'::regclass)"))
    order_no = Column(String(24), nullable=False)
    orderId = Column(String(24), nullable=False, server_default=text("nextval('order_id_seq'::regclass)"))
    group_id = Column(BigInteger, nullable=True)
    manager_id = Column(BigInteger, nullable=True)
    order_method = Column(String(36), nullable=False)
    full_name = Column(String(64), nullable=False)
    phone1 = Column(String(20), nullable=False)
    phone2 = Column(String(20), nullable=True)
    gender = Column(String(255), nullable=True)
    country_id = Column(BigInteger, nullable=True)
    region_id = Column(BigInteger, ForeignKey('regions.id'), nullable=True)
    city_id = Column(BigInteger, nullable=True)
    pick_up_point_id = Column(BigInteger, nullable=True)
    address = Column(String(64), nullable=True)
    sub_status_id = Column(BigInteger, nullable=False)
    address_comment = Column(Text, nullable=True)
    summ = Column(Numeric(10,2), nullable=False, server_default=text("'0'::numeric"))
    discount_amount = Column(Numeric(10,2), nullable=False, server_default=text("'0'::numeric"))
    total_summ = Column(Numeric(10,2), nullable=False, server_default=text("'0'::numeric"))
    purchase_summ = Column(Numeric(10,2), nullable=False, server_default=text("'0'::numeric"))
    cost_ship = Column(Numeric(10,2), nullable=False, server_default=text("'0'::numeric"))
    net_cost_ship = Column(Numeric(10,2), nullable=False, server_default=text("'0'::numeric"))
    shipping_method_id = Column(BigInteger, nullable=True)
    tariff_id = Column(BigInteger, nullable=True)
    tariff_code = Column(String(24), nullable=True)
    offer_id = Column(Integer, nullable=True)
    utm_campaign = Column(String(56), nullable=True)
    utm_medium = Column(String(56), nullable=True)
    utm_source = Column(String(56), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    status_comment = Column(Text, nullable=True)

    # Relationships
    region = relationship("Region")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    offer_data = relationship("OfferData", back_populates="order", uselist=False, cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, index=True, server_default=text("nextval('order_items_id_seq'::regclass)"))
    orderId = Column(String(24), ForeignKey("orders.orderId"), nullable=False)
    store_id = Column(Integer, nullable=False)
    store = Column(String(255), nullable=False)
    product = Column(String(255), nullable=False)
    article = Column(String(255), nullable=False)
    sku = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    buy_price = Column(Numeric(10,2), nullable=False)
    sell_price = Column(Numeric(10,2), nullable=False)
    img = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="items")

class OfferData(Base):
    __tablename__ = "offer_data"

    id = Column(BigInteger, primary_key=True, index=True, server_default=text("nextval('offer_data_id_seq'::regclass)"))
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    offer_id = Column(Integer, nullable=False)
    k_id = Column(Integer, nullable=False)
    source = Column(String(255), nullable=False)
    stream = Column(String(255), nullable=False)
    pay_web = Column(Integer, nullable=False)
    add_manager = Column(Integer, nullable=False)
    two_plus_one = Column(Boolean, nullable=False, default=False)
    free2 = Column(Boolean, nullable=False, default=False)
    free1 = Column(Boolean, nullable=False, default=False)
    pick_up = Column(Boolean, nullable=False, default=False)
    fbs = Column(Boolean, nullable=False, default=False)
    orderId = Column(String(24), ForeignKey("orders.orderId"), nullable=True)
    order = relationship("Order", back_populates="offer_data")

class Region(Base):
    __tablename__ = "regions"

    id = Column(BigInteger, primary_key=True, index=True, server_default=text("nextval('regions_id_seq'::regclass)"))
    name = Column(String(48), nullable=False)
    name_ru = Column(String(48), nullable=True)
    country_id = Column(BigInteger, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default='true')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
