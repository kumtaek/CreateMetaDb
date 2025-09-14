package com.example.dynamicquery;

import java.util.List;
import java.util.Map;

/**
 * 사용자 정보 조회를 위한 MyBatis 매퍼 인터페이스입니다.
 */
public interface UserMapper {

    /**
     * 동적 검색 조건에 따라 사용자 목록을 조회합니다. (Oracle Implicit Join 방식)
     *
     * @param searchDto 검색 조건 DTO
     * @return 사용자 정보 리스트
     */
    List<Map<String, Object>> findUsers(UserSearchDto searchDto);

    /**
     * 동적 검색 조건에 따라 사용자 목록을 조회합니다. (ANSI Join 방식)
     *
     * @param searchDto 검색 조건 DTO
     * @return 사용자 정보 리스트
     */
    List<Map<String, Object>> findUsersWithAnsiJoin(UserSearchDto searchDto);
}
