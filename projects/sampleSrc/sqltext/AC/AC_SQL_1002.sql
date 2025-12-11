-- sql_id: SQL_1002
UPDATE ORDERS
   SET status = :status,
       updated_at = CURRENT_TIMESTAMP
 WHERE order_id = :order_id;
