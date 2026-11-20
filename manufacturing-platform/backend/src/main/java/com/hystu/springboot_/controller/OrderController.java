package com.hystu.springboot_.controller;

import com.hystu.springboot_.entity.Order;
import com.hystu.springboot_.service.OrderService;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/orders")
public class OrderController {

  private final OrderService service;

  public OrderController(OrderService s) {
    service = s;
  }

  @GetMapping
  public List<Order> all() {
    return service.all();
  }

  @PostMapping
  public Order add(@RequestBody Order o) {
    return service.add(o);
  }

  public record Change(String status,Integer version,String note){}
  @PatchMapping("/{id}/status")
  public Order change(@PathVariable Long id,@RequestBody Change value){return service.transition(id,value.status(),value.version(),value.note());}
  @GetMapping("/{id}/history")
  public List<java.util.Map<String,Object>> history(@PathVariable Long id){return service.history(id);}

  @DeleteMapping("/{id}")
  public void delete(@PathVariable Long id) {
    service.delete(id);
  }
}
