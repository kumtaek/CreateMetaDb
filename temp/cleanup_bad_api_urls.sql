-- 잘못된 API_URL 컴포넌트들 삭제 (/:GET, /:POST, :GET, :POST 등)

BEGIN TRANSACTION;

-- 1. 관련 관계들 먼저 삭제
UPDATE relationships 
SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
WHERE (src_id IN (
    SELECT component_id 
    FROM components 
    WHERE component_type = 'API_URL' 
      AND del_yn = 'N'
      AND (
          component_name LIKE '/:%' 
          OR component_name LIKE ':%'
          OR component_name = '/'
          OR component_name = ''
      )
) OR dst_id IN (
    SELECT component_id 
    FROM components 
    WHERE component_type = 'API_URL' 
      AND del_yn = 'N'
      AND (
          component_name LIKE '/:%' 
          OR component_name LIKE ':%'
          OR component_name = '/'
          OR component_name = ''
      )
)) AND del_yn = 'N';

-- 2. 잘못된 API_URL 컴포넌트 삭제
UPDATE components 
SET del_yn = 'Y', updated_at = datetime('now', '+9 hours')
WHERE component_type = 'API_URL' 
  AND del_yn = 'N'
  AND (
      component_name LIKE '/:%' 
      OR component_name LIKE ':%'
      OR component_name = '/'
      OR component_name = ''
  );

COMMIT;

-- 정리 후 상태 확인
SELECT '=== 정리 후 API_URL 상태 ===' as status;
SELECT component_name, COUNT(*) as count
FROM components 
WHERE component_type = 'API_URL' AND del_yn = 'N'
GROUP BY component_name
ORDER BY count DESC
LIMIT 10;
