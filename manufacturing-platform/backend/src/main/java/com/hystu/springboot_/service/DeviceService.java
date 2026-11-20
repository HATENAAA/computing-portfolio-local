package com.hystu.springboot_.service;

import com.hystu.springboot_.entity.*;
import com.hystu.springboot_.mapper.*;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class DeviceService {

  private final DeviceMapper devices;
  private final FactoryMapper factories;
  private final Access access;
  private final OperationsMapper ops;

  public DeviceService(DeviceMapper d, FactoryMapper f, Access a, OperationsMapper operations) {
    devices = d;
    factories = f;
    access = a;ops=operations;
  }

  public List<Device> list(String name) {
    access.factory(name);
    return devices.findDevicesByFactoryName(name);
  }

  public List<Device> all() {
    var u = access.role("superAdmin", "factoryAdmin");
    return u.getRole().equals("superAdmin")
      ? devices.findall()
      : devices.findDevicesByFactoryName(u.getFactoryName());
  }

  public Device add(Device d) {
    access.factory(d.getFactoryName());
    Access.label(d.getDeviceName(), 100, "Device name");
    Access.found(factories.getFactoryByFactoryName(d.getFactoryName()));
    validate(d);d.setVersion(0);
    d.setId(null);
    devices.insertDevice(d);
    devices.event(d.getId(),d.getStatus(),"设备建档",access.actor().getUsername(),0);
    return d;
  }

  public Device update(Long id, Device d) {
    var old = devices.lock(id);
    Access.found(old);
    access.factory(old.getFactoryName());
    Access.require(
      d.getFactoryName() == null ||
        d.getFactoryName().equals(old.getFactoryName()),
      "A device cannot be reassigned through this endpoint"
    );
    Access.label(d.getDeviceName(), 100, "Device name");
    d.setId(id);
    d.setFactoryName(old.getFactoryName());
    validate(d);
    if(d.getVersion()!=old.getVersion())throw new org.springframework.web.server.ResponseStatusException(org.springframework.http.HttpStatus.CONFLICT,"Device changed; refresh before retrying");
    Access.require("AVAILABLE".equals(d.getStatus()) || ops.running(id)==0,"Pause running production before taking this device out of service");
    if(devices.updateDevice(d)!=1)throw new org.springframework.web.server.ResponseStatusException(org.springframework.http.HttpStatus.CONFLICT,"Device changed; refresh before retrying");
    devices.event(id,d.getStatus(),d.getMaintenanceNote(),access.actor().getUsername(),d.getVersion()+1);
    return devices.findById(id);
  }

  private void validate(Device d){
    if(d.getStatus()==null)d.setStatus("AVAILABLE");if(d.getCategory()==null)d.setCategory("加工设备");
    Access.require(java.util.Set.of("AVAILABLE","MAINTENANCE","OFFLINE").contains(d.getStatus()),"Invalid device status");
    Access.label(d.getCategory(),100,"Category");Access.require(d.getDailyCapacityMinutes()>=30 && d.getDailyCapacityMinutes()<=1440,"Daily capacity must be 30..1440 minutes");
    Access.require(d.getLocation()==null || d.getLocation().length()<=100,"Location exceeds limit");
    Access.require(d.getDeviceDescription()==null || d.getDeviceDescription().length()<=1000,"Description exceeds limit");
    Access.require(d.getMaintenanceNote()==null || d.getMaintenanceNote().length()<=1000,"Maintenance note exceeds limit");
    if(!"AVAILABLE".equals(d.getStatus()))Access.label(d.getMaintenanceNote(),1000,"Maintenance reason");
  }
  public List<java.util.Map<String,Object>> history(Long id){var d=devices.findById(id);Access.found(d);access.factory(d.getFactoryName());return devices.events(id).stream().map(OperationsService::normalized).toList();}
  public void delete(Long id) {
    var d = devices.findById(id);
    Access.found(d);
    access.factory(d.getFactoryName());
    devices.deleteDevice(id);
  }
}
