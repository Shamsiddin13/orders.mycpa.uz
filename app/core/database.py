from sqlalchemy import create_engine, event, text, func
from sqlalchemy.orm import sessionmaker, Session, joinedload, object_session
from sqlalchemy.ext.declarative import declarative_base
from .config import settings
from ..models.models import Order, OrderItem, OfferData
from .logging_config import setup_logging
import json
from urllib.parse import quote_plus
import logging
from datetime import datetime, timedelta
from typing import Optional

# Set up logging
logger = logging.getLogger('app.database')

# Create declarative base
Base = declarative_base()

# PostgreSQL Connection
pg_engine = create_engine(settings.POSTGRESQL_URL)
PostgresSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

# MySQL Connection with escaped password
mysql_password = quote_plus(settings.MYSQL_PASSWORD)
mysql_url = f"mysql://{settings.MYSQL_USER}:{mysql_password}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
mysql_engine = create_engine(mysql_url)
MySQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)

def get_pg_db():
    db = PostgresSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mysql_db():
    db = MySQLSessionLocal()
    try:
        yield db
    finally:
        db.close()

def sync_order_to_mysql(order: Order, action: str, mysql_session: Optional[Session] = None) -> None:
    """Sync order to MySQL database with retries and proper action handling"""
    logger = logging.getLogger('app.core.database')
    max_retries = 5
    retry_count = 0
    
    # Create a new session if one wasn't provided
    should_close_session = mysql_session is None
    if mysql_session is None:
        mysql_session = MySQLSessionLocal()
    
    # Get a PostgreSQL session to load relationships
    pg_session = PostgresSessionLocal()
    try:
        # Load the complete order with relationships from PostgreSQL
        order_with_relations = pg_session.query(Order).options(
            joinedload(Order.items),
            joinedload(Order.offer_data)
        ).filter(Order.id == order.id).first()
        
        if not order_with_relations:
            logger.error(f"Order {order.id} not found in PostgreSQL")
            return
            
        while retry_count < max_retries:
            try:
                if action == 'deleted':
                    # Delete order items first due to foreign key constraints
                    mysql_session.execute(
                        text("DELETE FROM `order_items` WHERE order_no = :order_no"),
                        {'order_no': order_with_relations.order_no}
                    )
                    # Then delete the order
                    mysql_session.execute(
                        text("DELETE FROM `order` WHERE order_no = :order_no"),
                        {'order_no': order_with_relations.order_no}
                    )
                    
                elif action in ['created', 'updated']:
                    if action == 'updated':
                        # Delete existing items for update
                        mysql_session.execute(
                            text("DELETE FROM `order_items` WHERE order_no = :order_no"),
                            {'order_no': order_with_relations.order_no}
                        )
                        # Delete existing order for update
                        mysql_session.execute(
                            text("DELETE FROM `order` WHERE order_no = :order_no"),
                            {'order_no': order_with_relations.order_no}
                        )
                    
                    # Insert/Update order
                    insert_query = text("""
                        INSERT INTO `order` (
                            created_at, order_no, offer_id, k_id, source, name, phone,
                            region, order_method, summ, total_sum, purchase_sum, pay_web,
                            two_plus_one, add_manager, fbs, cost_ship, net_cost_ship,
                            utm_campaign, utm_medium, utm_source
                        ) VALUES (
                            :created_at, :order_no, :offer_id, :k_id, :source, :name, :phone,
                            :region, :order_method, :summ, :total_sum, :purchase_sum, :pay_web,
                            :two_plus_one, :add_manager, :fbs, :cost_ship, :net_cost_ship,
                            :utm_campaign, :utm_medium, :utm_source
                        )
                    """)
                    
                    # Get offer data values
                    offer_data = order_with_relations.offer_data
                    
                    mysql_session.execute(
                        insert_query,
                        {
                            'created_at': order_with_relations.created_at,
                            'order_no': order_with_relations.order_no,
                            'offer_id': order_with_relations.offer_id,
                            'k_id': offer_data.k_id if offer_data else None,
                            'source': offer_data.source if offer_data else 'No source',
                            'name': order_with_relations.full_name,
                            'phone': order_with_relations.phone1,
                            'region': order_with_relations.region.name if order_with_relations.region else None,
                            'order_method': order_with_relations.order_method,
                            'summ': order_with_relations.summ,
                            'total_sum': order_with_relations.total_summ,
                            'purchase_sum': order_with_relations.purchase_summ,
                            'pay_web': offer_data.pay_web if offer_data else 0,
                            'two_plus_one': 5000 if (offer_data and offer_data.two_plus_one == 'Bor') else 0,
                            'add_manager': offer_data.add_manager if offer_data else 0,
                            'fbs': 'Bor' if offer_data and offer_data.fbs else 'Yoq',
                            'cost_ship': order_with_relations.cost_ship,
                            'net_cost_ship': order_with_relations.net_cost_ship,
                            'utm_campaign': order_with_relations.utm_campaign or 'No campaign',
                            'utm_medium': order_with_relations.utm_medium or 'No medium',
                            'utm_source': order_with_relations.utm_source or 'No source'
                        }
                    )
                    
                    # Insert order items
                    if order_with_relations.items:
                        for item in order_with_relations.items:
                            insert_item_query = text("""
                                INSERT INTO `order_items` (
                                    id, order_no, store_id, store, product, article, sku,
                                    buy_price, sell_price, quantity
                                ) VALUES (
                                    :id, :order_no, :store_id, :store, :product, :article, :sku,
                                    :buy_price, :sell_price, :quantity
                                )
                            """)
                            
                            mysql_session.execute(
                                insert_item_query,
                                {
                                    'id': item.id,
                                    'order_no': order_with_relations.order_no,
                                    'store_id': item.store_id,
                                    'store': item.store,
                                    'product': item.product,
                                    'article': item.article,
                                    'sku': item.sku,
                                    'buy_price': item.buy_price,
                                    'sell_price': item.sell_price,
                                    'quantity': item.quantity
                                }
                            )
                
                mysql_session.commit()
                logger.info(f"Order {order_with_relations.id} {action} in MySQL successfully")
                if order_with_relations.items:
                    logger.info(f"OrderItems {[item.sku for item in order_with_relations.items]} {action} in MySQL successfully")
                if order_with_relations.offer_data:
                    logger.info(f"OfferData for order {order_with_relations.id} {action} in MySQL successfully")
                return
                
            except Exception as e:
                logger.error(f"Error syncing order to MySQL (attempt {retry_count + 1}/{max_retries}): {str(e)}")
                mysql_session.rollback()
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Failed to sync order {order_with_relations.id} to MySQL after {max_retries} attempts")
                    raise
                
    finally:
        if should_close_session:
            mysql_session.close()
        pg_session.close()

def sync_after_commit(session, order_id):
    """Sync order after transaction is committed"""
    try:
        # Get a new session for PostgreSQL
        pg_session = PostgresSessionLocal()
        
        # Load the complete order with relationships using a fresh query
        order_with_relations = (
            pg_session.query(Order)
            .options(
                joinedload(Order.items),
                joinedload(Order.offer_data)
            )
            .filter(Order.id == order_id)
            .first()
        )
        
        if order_with_relations:
            sync_order_to_mysql(order_with_relations, 'created')
        else:
            logger.error(f"Order {order_id} not found in PostgreSQL")
            
    except Exception as e:
        logger.error(f"Error in sync_after_commit: {str(e)}")
    finally:
        pg_session.close()

# Event listener for order creation
@event.listens_for(Order, 'after_insert')
def after_order_insert(mapper, connection, target):
    try:
        session = object_session(target)
        if session:
            @event.listens_for(session, 'after_commit', once=True)
            def do_after_commit(session):
                sync_after_commit(session, target.id)
    except Exception as e:
        logger.error(f"Error in after_order_insert event: {str(e)}")

# Event listener for order update
@event.listens_for(Order, 'after_update')
def after_order_update(mapper, connection, target):
    try:
        sync_order_to_mysql(target, 'updated')
    except Exception as e:
        logger.error(f"Error in after_order_update event: {str(e)}")

# Event listener for order delete
@event.listens_for(Order, 'after_delete')
def after_order_delete(mapper, connection, target):
    try:
        sync_order_to_mysql(target, 'deleted')
    except Exception as e:
        logger.error(f"Error in after_order_delete event: {str(e)}")

logger.info("Database event listeners registered successfully")
