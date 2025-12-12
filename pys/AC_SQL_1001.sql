-- sql_id: SQL_1001
SELECT /* SQL_1001: active users by role */
       user_id,
       user_name,
       status,
       role
FROM   USERS
WHERE  status = 'ACTIVE'
  AND  role = :role
ORDER BY user_name;
