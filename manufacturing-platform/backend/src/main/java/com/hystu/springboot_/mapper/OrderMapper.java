package com.hystu.springboot_.mapper;

import com.hystu.springboot_.entity.Order;
import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface OrderMapper {
  @Insert(
    "INSERT INTO orders(productName,quantity,factoryName,ownerUsername,status,version,priority,dueDate,notes) VALUES(#{productName},#{quantity},#{factoryName},#{ownerUsername},#{status},#{version},#{priority},#{dueDate},#{notes})"
  )
  @Options(useGeneratedKeys = true, keyProperty = "id")
  void insert(Order order);

  @Select("SELECT * FROM orders WHERE id=#{id}")
  Order findById(Long id);

  @Select("SELECT * FROM orders ORDER BY id")
  List<Order> findAll();

  @Select("SELECT * FROM orders WHERE ownerUsername=#{owner} ORDER BY id")
  List<Order> findByOwner(String owner);

  @Select("SELECT * FROM orders WHERE factoryName=#{factory} ORDER BY id")
  List<Order> findByFactory(String factory);

  @Update("UPDATE orders SET status=#{next},version=version+1,updatedAt=CURRENT_TIMESTAMP WHERE id=#{id} AND version=#{version} AND status=#{previous}")
  int transition(@Param("id") Long id,@Param("version") int version,@Param("previous") String previous,@Param("next") String next);
  @Insert("INSERT INTO order_events(orderId,fromStatus,toStatus,actor,orderVersion) VALUES(#{id},#{previous},#{next},#{actor},#{version})")
  void event(@Param("id") Long id,@Param("previous") String previous,@Param("next") String next,@Param("actor") String actor,@Param("version") int version);
  @Select("SELECT id,fromStatus,toStatus,actor,orderVersion,createdAt,eventType,note FROM order_events WHERE orderId=#{id} ORDER BY orderVersion")
  List<java.util.Map<String,Object>> events(Long id);

  @Select("SELECT * FROM orders WHERE id=#{id} FOR UPDATE")
  Order lock(Long id);
  @Update("UPDATE orders SET version=version+1,updatedAt=CURRENT_TIMESTAMP WHERE id=#{id} AND version=#{version}")
  int touch(@Param("id") Long id,@Param("version") int version);
  @Update("UPDATE orders SET completedQuantity=completedQuantity+#{good},rejectedQuantity=rejectedQuantity+#{rejected},version=version+1,updatedAt=CURRENT_TIMESTAMP WHERE id=#{id} AND version=#{version}")
  int progress(@Param("id") Long id,@Param("version") int version,@Param("good") int good,@Param("rejected") int rejected);
  @Insert("INSERT INTO order_events(orderId,fromStatus,toStatus,actor,orderVersion,eventType,note) VALUES(#{id},#{status},#{status},#{actor},#{version},#{type},#{note})")
  void log(@Param("id") Long id,@Param("status") String status,@Param("actor") String actor,@Param("version") int version,@Param("type") String type,@Param("note") String note);
  @Update("UPDATE order_events SET note=#{note} WHERE orderId=#{id} AND orderVersion=#{version}")
  void note(@Param("id") Long id,@Param("version") int version,@Param("note") String note);
  @Delete("DELETE FROM orders WHERE id=#{id}")
  void delete(Long id);
}
