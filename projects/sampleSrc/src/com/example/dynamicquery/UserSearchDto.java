package com.example.dynamicquery;

/**
 * 사용자 검색 조건을 담는 Data Transfer Object (DTO) 입니다.
 */
public class UserSearchDto {

    private String searchKeyword; // 검색어 (이름 또는 이메일)
    private String userStatus;    // 사용자 상태 (e.g., "ACTIVE", "INACTIVE")
    private String deptName;      // 부서명 검색 조건
    private String sortOrder;     // 정렬 순서 (e.g., "ASC", "DESC")

    // Getters and Setters
    public String getSearchKeyword() {
        return searchKeyword;
    }

    public void setSearchKeyword(String searchKeyword) {
        this.searchKeyword = searchKeyword;
    }

    public String getUserStatus() {
        return userStatus;
    }

    public void setUserStatus(String userStatus) {
        this.userStatus = userStatus;
    }

    public String getDeptName() {
        return deptName;
    }

    public void setDeptName(String deptName) {
        this.deptName = deptName;
    }

    public String getSortOrder() {
        return sortOrder;
    }

    public void setSortOrder(String sortOrder) {
        this.sortOrder = sortOrder;
    }
}
