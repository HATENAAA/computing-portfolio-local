package com.hystu.springboot_.mapper;

import com.hystu.springboot_.entity.User;
import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface UserMapper {
  @Insert(
    "INSERT INTO users(username,password,role,factoryName,factoryDescription,contactEmail,realName) VALUES(#{username},#{password},#{role},#{factoryName},#{factoryDescription},#{contactEmail},#{realName})"
  )
  @Options(useGeneratedKeys = true, keyProperty = "id")
  void insert(User user);

  @Select("SELECT * FROM users WHERE username=#{username}")
  User findByUsername(String username);

  @Select("SELECT * FROM users ORDER BY id")
  List<User> findAll();
}
