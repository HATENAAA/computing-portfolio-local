package com.hystu.springboot_.controller;

import com.hystu.springboot_.entity.Device;
import com.hystu.springboot_.service.DeviceService;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/devices")
public class DeviceController {

  private final DeviceService service;

  public DeviceController(DeviceService s) {
    service = s;
  }

  @GetMapping({ "/factory/{name}", "/factoryName/{name}" })
  public List<Device> list(@PathVariable String name) {
    return service.list(name);
  }

  @GetMapping("/allDevices")
  public List<Device> all() {
    return service.all();
  }

  @PostMapping
  public Device add(@RequestBody Device d) {
    return service.add(d);
  }

  @PutMapping("/{id}")
  public Device update(@PathVariable Long id, @RequestBody Device d) {
    return service.update(id, d);
  }

  @GetMapping("/{id}/history")
  public Object history(@PathVariable Long id){return service.history(id);}
  @DeleteMapping("/{id}")
  public void delete(@PathVariable Long id) {
    service.delete(id);
  }
}
