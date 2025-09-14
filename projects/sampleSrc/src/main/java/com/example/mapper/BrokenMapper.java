package com.example.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Update;
import org.apache.ibatis.annotations.Delete;
import com.example.model.Product;
import java.util.List;

// 정상적인 MyBatis 매퍼 - 오류 수정됨
@Mapper
public interface BrokenMapper {
    
    // 정상적인 SQL 쿼리
    @Select("SELECT id, name, price, description, create_date FROM products WHERE id = #{id}")
    Product selectById(Long id);
    
    // 정상적인 SQL 쿼리
    @Select("SELECT id, name, price, description, create_date FROM products")
    List<Product> selectAll();
    
    // 정상적인 SQL 쿼리
    @Select("SELECT id, name, price, description, create_date FROM products WHERE name LIKE CONCAT('%', #{name}, '%')")
    List<Product> selectByName(String name);
    
    // 정상적인 SQL 쿼리
    @Select("SELECT id, name, price, description, create_date FROM products WHERE price BETWEEN #{minPrice} AND #{maxPrice}")
    List<Product> selectByPriceRange(Double minPrice, Double maxPrice);
    
    // 정상적인 SQL 쿼리
    @Insert("INSERT INTO products (name, price, description, create_date) VALUES (#{name}, #{price}, #{description}, #{createDate})")
    int insert(Product product);
    
    // 정상적인 SQL 쿼리
    @Update("UPDATE products SET name = #{name}, price = #{price}, description = #{description} WHERE id = #{id}")
    int update(Product product);
    
    // 정상적인 SQL 쿼리
    @Delete("DELETE FROM products WHERE id = #{id}")
    int delete(Long id);
    
    // 정상적인 SQL 쿼리
    @Select("SELECT COUNT(*) FROM products")
    int countProducts();
    
    // 정상적인 SQL 쿼리
    @Select("SELECT id, name, price, description, create_date FROM products ORDER BY create_date DESC LIMIT #{limit}")
    List<Product> selectRecentProducts(int limit);
}
