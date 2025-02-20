from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    article: Optional[str]
    sku: str
    ikpu: Optional[str]
    categories_name: Optional[str]
    categories_id: Optional[int]
    store_name: Optional[str]
    store_id: Optional[int]
    min_price: Optional[Decimal]
    max_price: Optional[Decimal]
    img: Optional[str]

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class ProductOfferBase(BaseModel):
    product_id: int
    name: str
    sku: str
    buy_price: Decimal
    sell_price: Decimal
    weight: Optional[Decimal]
    img: Optional[str]
    is_available: str = 'stock'

class ProductOfferCreate(ProductOfferBase):
    pass

class ProductOfferResponse(ProductOfferBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class OrderItemCreate(BaseModel):
    sku: str
    store_id: int
    store: str
    product: str
    article: str
    buy_price: str
    sell_price: str
    quantity: int
    img: Optional[str] = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        # Convert string values to appropriate types
        data['buy_price'] = Decimal(str(data['buy_price']))
        data['sell_price'] = Decimal(str(data['sell_price']))
        return data

class OrderItemResponse(BaseModel):
    id: int
    orderId: str
    store_id: int
    store: str
    product: str
    article: str
    sku: str
    quantity: int
    buy_price: Decimal
    sell_price: Decimal
    img: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class OfferDataCreate(BaseModel):
    source: str
    stream: str
    two_plus_one: str
    pay_web: str
    add_manager: str
    free2: str
    free1: str
    pick_up: Optional[str] = None
    fbs: Optional[str] = None
    k_id: int
    offer_id: int

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        # Convert string values to appropriate types
        data['two_plus_one'] = data['two_plus_one'] == 'Bor'
        data['free2'] = data['free2'] == 'Bor'
        data['free1'] = data['free1'] == 'Bor'
        data['pick_up'] = data.get('pick_up', 'Yoq') == 'Bor'
        data['fbs'] = data.get('fbs', 'Yoq') == 'Bor'
        data['pay_web'] = int(float(data['pay_web']))
        data['add_manager'] = int(float(data['add_manager']))
        return data

class RegionResponse(BaseModel):
    id: int
    name: str
    name_ru: Optional[str]
    country_id: int
    is_active: bool

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    phone: str
    order_method: str
    full_name: str
    offer_id: int
    region: Optional[str] = None
    shipping_method_id: int
    group_id: int
    cost_ship: float = Field(default=0, description="Shipping cost")
    sub_status_id: int = Field(default=1, description="Order sub status ID")
    offer_data: OfferDataCreate
    items: List[OrderItemCreate]

    @validator('cost_ship')
    def validate_cost_ship(cls, v):
        if v < 0:
            raise ValueError("Shipping cost cannot be negative")
        return float(v)

    @validator('sub_status_id')
    def validate_sub_status(cls, v):
        if v < 1:
            raise ValueError("Sub status ID must be at least 1")
        return int(v)

class CreateOrderRequest(BaseModel):
    order: OrderCreate
    api_key: str

class OfferDataResponse(BaseModel):
    id: int
    source: str
    stream: str
    two_plus_one: bool
    pay_web: int
    add_manager: int
    free2: bool
    free1: bool
    pick_up: bool
    fbs: bool
    k_id: int
    offer_id: int
    orderId: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    orderId: str
    order_no: str
    phone1: str
    phone2: Optional[str]
    order_method: str
    full_name: str
    offer_id: int
    region: Optional[RegionResponse] = None
    country_id: Optional[int]
    shipping_method_id: Optional[int]
    group_id: Optional[int]
    sub_status_id: int
    summ: Decimal
    purchase_summ: Decimal
    cost_ship: Optional[int]
    discount_amount: Optional[Decimal]
    total_summ: Decimal
    gender: Optional[str]
    city_id: Optional[int]
    pick_up_point_id: Optional[int]
    address: Optional[str]
    address_comment: Optional[str]
    status_comment: Optional[str]
    net_cost_ship: Optional[Decimal]
    tariff_id: Optional[int]
    tariff_code: Optional[str]
    utm_campaign: Optional[str]
    utm_medium: Optional[str]
    utm_source: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    items: List[OrderItemResponse]
    offer_data: Optional[OfferDataResponse]

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None
