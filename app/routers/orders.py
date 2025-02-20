from queue import Empty
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import Optional, Tuple, Dict, List
from ..core.database import get_pg_db
from ..models.models import Order, OrderItem, OfferData, Region
from ..schemas.orders import CreateOrderRequest, OrderResponse, APIResponse, OrderItemCreate
from datetime import datetime, timedelta
import logging
from decimal import Decimal
from pydantic import ValidationError

router = APIRouter(
    prefix="/api/v1",
    tags=["orders"],
    responses={404: {"description": "Not found"}}
)
logger = logging.getLogger('app.routers.orders')

API_KEY = "oNUfKo0VRzsPWa9SnhHjvWnLadJ6NVrV"

def verify_api_key(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def calculate_totals(items: List[OrderItemCreate], cost_ship: float) -> Dict[str, float]:
    """
    Calculate order totals from items
    """
    buy_sum = 0.0
    sell_sum = 0.0

    for item in items:
        quantity = int(item.quantity)
        buy_sum += float(item.buy_price) * quantity
        sell_sum += float(item.sell_price) * quantity

    return {
        'buy_sum': buy_sum,
        'sell_sum': sell_sum,
        'total': sell_sum + cost_ship
    }

def get_region_info(db: Session, region_name: str) -> Dict[str, Optional[int]]:
    """
    Get region ID and country ID by name_ru or name
    Returns dictionary with region_id and country_id
    """
    try:
        if not region_name:
            logger.info("No region name provided")
            return {"region_id": None, "country_id": None}
            
        region = db.query(Region).filter(
            (Region.name_ru == region_name) | (Region.name == region_name),
            Region.is_active == True
        ).first()
        
        if region:
            logger.info(f"Found region: id={region.id}, country_id={region.country_id}")
            return {"region_id": region.id, "country_id": region.country_id}
            
        logger.info(f"Region not found for name: {region_name}")
        return {"region_id": None, "country_id": None}
        
    except Exception as e:
        logger.error(f"Error getting region info for {region_name}: {str(e)}")
        return {"region_id": None, "country_id": None}

def get_next_order_id(db: Session) -> int:
    """
    Get next value from order_id_seq sequence
    """
    result = db.execute(text("SELECT nextval('order_id_seq') as id"))
    return result.scalar()

@router.post("/orders/", response_model=APIResponse)
async def create_order(request: CreateOrderRequest, db: Session = Depends(get_pg_db)):
    logger = logging.getLogger('app.routers.orders')
    
    try:
        logger.info(f"Creating order: {request.order}")
        verify_api_key(request.api_key)
        order_data = request.order
        
        try:
            # Get region and country info
            region_info = get_region_info(db, order_data.region)
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'args') and e.args:
                error_msg = e.args[0]
            logger.error(f"Error getting region info: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Invalid region: {error_msg}")
        
        try:
            # Calculate totals
            total_summ = calculate_totals(order_data.items, order_data.cost_ship)
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'args') and e.args:
                error_msg = e.args[0]
            logger.error(f"Error calculating totals: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Error calculating totals: {error_msg}")

        try:
            order_id = str(get_next_order_id(db))
            # Create new order
            new_order = Order(
                order_no=order_id,
                orderId=order_id,
                phone1=order_data.phone,
                order_method=order_data.order_method,
                full_name=order_data.full_name,
                offer_id=order_data.offer_id,
                region_id=region_info["region_id"],
                country_id=region_info["country_id"],
                shipping_method_id=order_data.shipping_method_id,
                group_id=order_data.group_id,
                sub_status_id=order_data.sub_status_id,
                summ=Decimal(str(total_summ["sell_sum"])),
                purchase_summ=Decimal(str(total_summ["buy_sum"])),
                cost_ship=Decimal(str(order_data.cost_ship)),
                discount_amount=Decimal('0'),
                total_summ=Decimal(str(total_summ["total"])),
                created_at=datetime.utcnow() + timedelta(hours=5),
                updated_at=datetime.utcnow() + timedelta(hours=5)
            )
            db.add(new_order)
            db.flush()  # Get the order ID without committing
            logger.info(f"Created order with ID: {new_order.id}, OrderID: {new_order.orderId}")
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'args') and e.args:
                error_msg = e.args[0]
            logger.error(f"Error creating order record: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Error creating order: {error_msg}")

        try:
            # Create order items
            for idx, item in enumerate(order_data.items):
                try:
                    item_dict = item.dict()
                    order_item = OrderItem(
                        orderId=new_order.orderId,
                        store_id=item_dict["store_id"],
                        store=item_dict["store"],
                        product=item_dict["product"],
                        article=item_dict["article"],
                        sku=item_dict["sku"],
                        buy_price=Decimal(str(item_dict["buy_price"])),
                        sell_price=Decimal(str(item_dict["sell_price"])),
                        quantity=item_dict["quantity"],
                        img=item_dict.get("img"),
                        created_at=datetime.utcnow() + timedelta(hours=5),
                        updated_at=datetime.utcnow() + timedelta(hours=5)
                    )
                    db.add(order_item)
                    logger.info(f"Added order item {idx+1}: SKU={item_dict['sku']}, Product={item_dict['product']}")
                except Exception as e:
                    error_msg = str(e)
                    if hasattr(e, 'args') and e.args:
                        error_msg = e.args[0]
                    logger.error(f"Error creating order item {idx+1} (SKU={item_dict.get('sku')}): {error_msg}")
                    raise
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'args') and e.args:
                error_msg = e.args[0]
            logger.error(f"Error creating order items: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Error creating order items: {error_msg}")

        try:
            # Create offer data
            offer_data_dict = order_data.offer_data.dict()
            offer_data = OfferData(
                orderId=new_order.orderId,
                created_at=datetime.utcnow() + timedelta(hours=5),
                updated_at=datetime.utcnow() + timedelta(hours=5),
                **offer_data_dict
            )
            db.add(offer_data)
            logger.info(f"Added offer data for order {new_order.id}")
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'args') and e.args:
                error_msg = e.args[0]
            logger.error(f"Error creating offer data: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Error creating offer data: {error_msg}")
        
        try:
            db.commit()
            logger.info(f"Order {new_order.id} committed successfully")
            db.refresh(new_order)
            
            try:
                # Validate and create response
                validated_order = OrderResponse.model_validate(new_order)
                logger.info(f"Order response validated successfully")
                return APIResponse(
                    status="success",
                    message="Order created successfully",
                    data={"order": validated_order.model_dump()}
                )
            except ValidationError as ve:
                error_msg = str(ve)
                if hasattr(ve, 'errors') and ve.errors():
                    error_msg = '; '.join(str(err) for err in ve.errors())
                logger.error(f"Validation error: {error_msg}")
                raise HTTPException(status_code=422, detail=error_msg)
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, 'args') and e.args:
                    error_msg = e.args[0]
                logger.error(f"Error creating response: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Error creating response: {error_msg}")
                
        except Exception as e:
            db.rollback()
            error_msg = str(e)
            if hasattr(e, 'args') and e.args:
                error_msg = e.args[0]
            logger.error(f"Database commit error: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Database commit error: {error_msg}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        if hasattr(e, 'args') and e.args:
            error_msg = e.args[0]
        logger.error(f"Unhandled error in create_order: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Unhandled error: {error_msg}"
        )

@router.get("/orders/{order_id}", response_model=APIResponse)
async def get_order(order_id: str, api_key: str, db: Session = Depends(get_pg_db)):
    """Get order by orderId with its relationships"""
    try:
        # Verify API key first
        verify_api_key(api_key)
        
        logger.info(f"Fetching order with ID: {order_id}")
        
        # Query order with relationships
        order = db.query(Order).options(
            joinedload(Order.items),
            joinedload(Order.offer_data)
        ).filter(Order.orderId == order_id).first()
        
        # Check if order exists
        if not order:
            logger.error(f"Order with ID {order_id} not found")
            raise HTTPException(
                status_code=404, 
                detail=f"Order with ID {order_id} not found"
            )
        
        try:
            # Validate and create response
            validated_order = OrderResponse.model_validate(order)
            logger.info(f"Order {order_id} retrieved successfully")
            
            return APIResponse(
                status="success",
                message="Order retrieved successfully",
                data={"order": validated_order.model_dump()}
            )
            
        except ValidationError as ve:
            logger.error(f"Validation error for order {order_id}: {str(ve)}")
            raise HTTPException(status_code=422, detail=str(ve))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error retrieving order: {str(e)}",
                "type": type(e).__name__
            }
        )

@router.put("/orders/{order_id}", response_model=APIResponse)
async def update_order(order_id: int, request: CreateOrderRequest, db: Session = Depends(get_pg_db)):
    try:
        verify_api_key(request.api_key)
        
        order_data = request.order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Calculate totals
        totals = calculate_totals(order_data.items, order_data.cost_ship)
        cost_ship = float(order_data.cost_ship)
        total_summ = totals['total']

        # Get region info
        region_info = get_region_info(db, order_data.region)

        # Update order
        order.phone1 = order_data.phone
        order.order_method = order_data.order_method
        order.full_name = order_data.full_name
        order.offer_id = order_data.offer_id
        order.region_id = region_info["region_id"]
        order.country_id = region_info["country_id"]
        order.shipping_method_id = order_data.shipping_method_id
        order.group_id = order_data.group_id
        order.sub_status_id = order_data.sub_status_id
        order.summ = totals['sell_sum']
        order.purchase_summ = totals['buy_sum']
        order.cost_ship = cost_ship
        order.total_summ = total_summ
        order.updated_at = datetime.utcnow()

        # Delete existing items
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

        # Create new items
        for item in order_data.items:
            item_dict = item.dict()
            order_item = OrderItem(
                order_id=order.id,
                store_id=item_dict["store_id"],
                store=item_dict["store"],
                product=item_dict["product"],
                article=item_dict["article"],
                sku=item_dict["sku"],
                buy_price=item_dict["buy_price"],
                sell_price=item_dict["sell_price"],
                quantity=item_dict["quantity"],
                img=item_dict.get("img")
            )
            db.add(order_item)

        # Update offer data
        offer_data = db.query(OfferData).filter(OfferData.orderId == order_id).first()
        if offer_data:
            for key, value in order_data.offer_data.dict().items():
                setattr(offer_data, key, value)
        else:
            offer_data = OfferData(
                orderId=offer_data.orderId,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                **order_data.offer_data.dict()
            )
            db.add(offer_data)

        try:
            db.commit()
            db.refresh(order)
            
            try:
                # First validate the model
                validated_order = OrderResponse.model_validate(order)
                # Then create response
                return APIResponse(
                    status="success",
                    message="Order updated successfully",
                    data={"order": validated_order.model_dump()}
                )
            except Exception as ve:
                error_str = str(ve)
                if isinstance(ve, tuple):
                    error_str = str(ve[0]) if ve else "Validation error"
                logger.error(f"Validation error: {error_str}")
                raise HTTPException(status_code=422, detail=error_str)
                
        except Exception as e:
            db.rollback()
            error_str = str(e)
            if isinstance(e, tuple):
                error_str = str(e[0]) if e else "Database error"
            logger.error(f"Database error: {error_str}")
            if not error_str:
                error_str = "Internal server error occurred"
            raise HTTPException(
                status_code=500,
                detail={
                    "message": error_str,
                    "type": type(e).__name__
                }
            )

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        error_str = str(e)
        if isinstance(e, tuple):
            error_str = str(e[0]) if e else "Unknown error"
        logger.error(f"Update order error: {error_str}")
        if not error_str:
            error_str = "Internal server error occurred"
        raise HTTPException(
            status_code=500,
            detail={
                "message": error_str,
                "type": type(e).__name__
            }
        )

@router.delete("/orders/{order_id}", response_model=APIResponse)
async def delete_order(order_id: int, api_key: str, db: Session = Depends(get_pg_db)):
    try:
        verify_api_key(api_key)
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        db.delete(order)
        db.commit()

        return APIResponse(
            status="success",
            message="Order deleted successfully",
            data={"order_id": order_id}
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        error_str = str(e)
        if isinstance(e, tuple):
            error_str = str(e[0]) if e else "Unknown error"
        logger.error(f"Delete order error: {error_str}")
        if not error_str:
            error_str = "Internal server error occurred"
        raise HTTPException(
            status_code=500,
            detail={
                "message": error_str,
                "type": type(e).__name__
            }
        )