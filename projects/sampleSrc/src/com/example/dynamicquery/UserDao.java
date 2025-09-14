package com.example.dynamicquery;

import org.apache.ibatis.session.SqlSession;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

/**
 * 사용자 정보에 접근하는 Data Access Object (DAO) 입니다.
 * MyBatis SqlSession을 통해 매퍼를 호출합니다.
 */
public class UserDao {

    private static final Logger logger = Logger.getLogger(UserDao.class.getName());
    private static final String DEFAULT_PROFILE_IMAGE = "/images/default_profile.png";

    private final SqlSession sqlSession;

    public UserDao(SqlSession sqlSession) {
        this.sqlSession = sqlSession;
    }

    /**
     * [Oracle Join 방식] 검색 조건에 맞는 사용자 목록을 조회합니다.
     *
     * @param searchDto 사용자 검색 조건
     * @return 조회 및 가공된 사용자 목록
     */
    public List<Map<String, Object>> findUsersByCondition(UserSearchDto searchDto) {
        logger.info("사용자 검색 시작 (Oracle Join). 검색어: " + searchDto.getSearchKeyword());
        
        // 공통 로직 호출
        validateAndSetDefaults(searchDto);

        UserMapper mapper = sqlSession.getMapper(UserMapper.class);
        List<Map<String, Object>> users = mapper.findUsers(searchDto);
        
        return processUserData(users);
    }

    /**
     * [ANSI Join 방식] 검색 조건에 맞는 사용자 목록을 조회합니다.
     *
     * @param searchDto 사용자 검색 조건
     * @return 조회 및 가공된 사용자 목록
     */
    public List<Map<String, Object>> findUsersByConditionAnsi(UserSearchDto searchDto) {
        logger.info("사용자 검색 시작 (ANSI Join). 검색어: " + searchDto.getSearchKeyword());

        // 공통 로직 호출
        validateAndSetDefaults(searchDto);

        UserMapper mapper = sqlSession.getMapper(UserMapper.class);
        List<Map<String, Object>> users = mapper.findUsersWithAnsiJoin(searchDto);

        return processUserData(users);
    }

    /**
     * 입력 파라미터를 검증하고 기본값을 설정하는 공통 메소드
     */
    private void validateAndSetDefaults(UserSearchDto searchDto) {
        if (searchDto.getSortOrder() == null ||
            (!searchDto.getSortOrder().equalsIgnoreCase("ASC") && !searchDto.getSortOrder().equalsIgnoreCase("DESC"))) {
            logger.warning("유효하지 않은 정렬 순서입니다. 기본값 'DESC'로 설정합니다.");
            searchDto.setSortOrder("DESC");
        }
    }

    /**
     * 조회된 사용자 데이터를 후처리하는 공통 메소드
     */
    private List<Map<String, Object>> processUserData(List<Map<String, Object>> users) {
        logger.info(users.size() + "명의 사용자를 조회했습니다.");

        for (Map<String, Object> user : users) {
            if (user.get("PROFILE_IMAGE_URL") == null || user.get("PROFILE_IMAGE_URL").toString().isEmpty()) {
                user.put("PROFILE_IMAGE_URL", DEFAULT_PROFILE_IMAGE);
            }

            String status = (String) user.get("STATUS");
            if ("ACTIVE".equalsIgnoreCase(status)) {
                user.put("STATUS_TEXT", "활성 사용자");
            } else if ("INACTIVE".equalsIgnoreCase(status)) {
                user.put("STATUS_TEXT", "비활성 사용자");
            } else {
                user.put("STATUS_TEXT", "상태 미정");
            }
        }

        logger.info("사용자 데이터 후처리 완료.");
        return users;
    }
}
