-- sql_id: SQL_1003
SELECT /* SQL_1003: product search by category and price */
       product_id,
       product_name,
       category,
       price
FROM   PRODUCTS
WHERE  category = :category
  AND  price BETWEEN :min_price AND :max_price
ORDER BY price DESC;
