package com.hystu.springboot_.mapper;

import com.hystu.springboot_.entity.Factory;
import java.util.List;
import org.apache.ibatis.annotations.*;

/**
 * @author HATENA
 */
@Mapper
public interface FactoryMapper {
  @Select("SELECT * FROM factories")
  List<Factory> findAllFactories();

  @Select("SELECT * FROM factories WHERE id = #{id}")
  Factory findFactoryById(@Param("id") Long id);

  @Insert(
    "INSERT INTO factories(factoryName, factoryDescription, contactEmail) VALUES(#{factoryName}, #{factoryDescription}, #{contactEmail})"
  )
  void insertFactory(Factory factory);

  @Update(
    "UPDATE factories SET factoryName = #{factoryName}, factoryDescription = #{factoryDescription}, contactEmail = #{contactEmail} WHERE id = #{id}"
  )
  void updateFactory(Factory factory);

  @Delete("DELETE FROM factories WHERE id = #{id}")
  void deleteFactory(@Param("id") Long id);

  @Select("SELECT * FROM factories WHERE factoryName = #{factoryName}")
  Factory getFactoryByFactoryName(@Param("factoryName") String factoryName);
}
