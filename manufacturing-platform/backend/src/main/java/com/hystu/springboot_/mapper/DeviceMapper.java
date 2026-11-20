package com.hystu.springboot_.mapper;

import com.hystu.springboot_.entity.Device;
import java.util.List;
import org.apache.ibatis.annotations.*;

@Mapper
public interface DeviceMapper {
  @Insert(
    "INSERT INTO devices(deviceName,deviceDescription,factoryName,status,category,location,dailyCapacityMinutes,serviceDueDate,maintenanceNote,version) VALUES(#{deviceName},#{deviceDescription},#{factoryName},#{status},#{category},#{location},#{dailyCapacityMinutes},#{serviceDueDate},#{maintenanceNote},#{version})"
  )
  @Options(useGeneratedKeys = true, keyProperty = "id")
  void insertDevice(Device device);

  @Update(
    "UPDATE devices SET deviceName=#{deviceName},deviceDescription=#{deviceDescription},status=#{status},category=#{category},location=#{location},dailyCapacityMinutes=#{dailyCapacityMinutes},serviceDueDate=#{serviceDueDate},maintenanceNote=#{maintenanceNote},version=version+1 WHERE id=#{id} AND version=#{version}"
  )
  int updateDevice(Device device);

  @Select("SELECT * FROM devices WHERE id=#{id} FOR UPDATE")
  Device lock(Long id);
  @Insert("INSERT INTO device_events(deviceId,status,note,actor,deviceVersion) VALUES(#{id},#{status},#{note},#{actor},#{version})")
  void event(@Param("id") Long id,@Param("status") String status,@Param("note") String note,@Param("actor") String actor,@Param("version") int version);
  @Select("SELECT status,note,actor,deviceVersion,createdAt FROM device_events WHERE deviceId=#{id} ORDER BY id DESC")
  List<java.util.Map<String,Object>> events(Long id);
  @Delete("DELETE FROM devices WHERE id=#{id}")
  void deleteDevice(Long id);

  @Select("SELECT * FROM devices WHERE factoryName=#{name} ORDER BY id")
  List<Device> findDevicesByFactoryName(String name);

  @Select("SELECT * FROM devices WHERE id=#{id}")
  Device findById(Long id);

  @Select("SELECT * FROM devices ORDER BY id")
  List<Device> findall();
}
