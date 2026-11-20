package com.hystu.springboot_.mapper;
import com.hystu.springboot_.entity.*;
import org.apache.ibatis.annotations.*;
import java.util.*;
@Mapper public interface OperationsMapper {
  String SCOPE=" (#{role}='superAdmin' OR (#{role}='factoryAdmin' AND o.factoryName=#{factory}) OR (#{role}='distributor' AND o.ownerUsername=#{owner})) ";
  @Select("SELECT p.*,d.deviceName,o.productName,o.factoryName,o.status,o.quantity FROM production_plans p JOIN orders o ON o.id=p.orderId JOIN devices d ON d.id=p.deviceId WHERE"+SCOPE+"ORDER BY p.plannedStart")
  List<Map<String,Object>> plans(@Param("role") String role,@Param("factory") String factory,@Param("owner") String owner);
  @Select("SELECT * FROM production_plans WHERE orderId=#{id}") ProductionPlan plan(Long id);
  @Delete("DELETE FROM production_plans WHERE orderId=#{id}") void deletePlan(Long id);
  @Insert("INSERT INTO production_plans(orderId,deviceId,plannedStart,plannedEnd,notes) VALUES(#{orderId},#{deviceId},#{plannedStart},#{plannedEnd},#{notes})") void insertPlan(ProductionPlan p);
  @Select("SELECT COUNT(*) FROM production_plans p JOIN orders o ON o.id=p.orderId WHERE p.deviceId=#{device} AND p.orderId<>#{order} AND o.status NOT IN ('COMPLETED','CANCELLED') AND p.plannedStart<#{end} AND p.plannedEnd>#{start}")
  int overlaps(@Param("device") Long device,@Param("order") Long order,@Param("start") java.time.LocalDateTime start,@Param("end") java.time.LocalDateTime end);
  @Select("SELECT COUNT(*) FROM production_plans p JOIN orders o ON o.id=p.orderId WHERE p.deviceId=#{id} AND o.status='PRODUCING'") int running(Long id);
  @Insert("INSERT INTO production_reports(orderId,goodQuantity,rejectedQuantity,notes,actor) VALUES(#{orderId},#{goodQuantity},#{rejectedQuantity},#{notes},#{actor})")
  @Options(useGeneratedKeys=true,keyProperty="id") void report(ProductionReport r);
  @Select("SELECT * FROM production_reports WHERE orderId=#{id} ORDER BY id DESC") List<ProductionReport> reports(Long id);
  @Insert("INSERT INTO production_issues(orderId,type,severity,description,status,actor,version) VALUES(#{orderId},#{type},#{severity},#{description},'OPEN',#{actor},0)")
  @Options(useGeneratedKeys=true,keyProperty="id") void issue(Issue i);
  @Select("SELECT * FROM production_issues WHERE id=#{id}") Issue issueById(Long id);
  @Select("SELECT * FROM production_issues WHERE orderId=#{id} ORDER BY id DESC") List<Issue> issues(Long id);
  @Select("SELECT i.*,o.productName,o.factoryName FROM production_issues i JOIN orders o ON o.id=i.orderId WHERE"+SCOPE+"ORDER BY i.id DESC")
  List<Map<String,Object>> allIssues(@Param("role") String role,@Param("factory") String factory,@Param("owner") String owner);
  @Select("SELECT COUNT(*) FROM production_issues WHERE orderId=#{id} AND status='OPEN' AND severity='HIGH'") int blocking(Long id);
  @Update("UPDATE production_issues SET status='RESOLVED',resolution=#{resolution},resolvedBy=#{actor},resolvedAt=CURRENT_TIMESTAMP,version=version+1 WHERE id=#{id} AND status='OPEN' AND version=#{version}")
  int resolve(@Param("id") Long id,@Param("version") int version,@Param("resolution") String resolution,@Param("actor") String actor);
}
