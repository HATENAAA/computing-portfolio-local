package com.hystu.springboot_.controller;

import com.hystu.springboot_.entity.Factory;
import com.hystu.springboot_.service.FactoryService;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/factories")
public class FactoryController {

  private final FactoryService service;

  public FactoryController(FactoryService s) {
    service = s;
  }

  @GetMapping
  public List<Factory> all() {
    return service.all();
  }

  @GetMapping("/{id}")
  public Factory get(@PathVariable Long id) {
    return service.byId(id);
  }

  @GetMapping("/factoryName/{name}")
  public Factory named(@PathVariable String name) {
    return service.byName(name);
  }

  @PostMapping
  public void add(@RequestBody Factory f) {
    service.add(f);
  }

  @PutMapping("/{id}")
  public void update(@PathVariable Long id, @RequestBody Factory f) {
    service.update(id, f);
  }

  @DeleteMapping("/{id}")
  public void delete(@PathVariable Long id) {
    service.delete(id);
  }
}
