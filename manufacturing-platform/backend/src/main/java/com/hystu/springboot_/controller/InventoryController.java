package com.hystu.springboot_.controller;
import com.hystu.springboot_.service.InventoryService;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
@RestController
@RequestMapping("/inventory")
public class InventoryController {
 private final InventoryService s; public InventoryController(InventoryService s){this.s=s;}
 public record Version(Integer version){}
 @GetMapping public Object workspace(@RequestParam(required=false) String factoryName){return s.workspace(factoryName);}
 @GetMapping("/reconciliation") public Object reconciliation(@RequestParam(required=false) String factoryName){return s.reconcile(factoryName);}
 @PostMapping("/materials") public Object create(@RequestBody InventoryService.MaterialInput in){return s.create(in);}
 @PostMapping("/materials/{id}/receipts") public Object receive(@PathVariable long id,@RequestBody InventoryService.Receipt in){return s.receive(id,in);}
 @PostMapping("/boms") public Object bom(@RequestBody InventoryService.BomInput in){return s.saveBom(in);}
 @GetMapping("/boms/{id}") public Object bom(@PathVariable long id){return s.bom(id);}
 @GetMapping("/orders/{id}") public Object order(@PathVariable long id){return s.orderMaterials(id);}
 @PostMapping("/orders/{id}/reserve") public Object reserve(@PathVariable long id,@RequestBody Version v){return s.reserve(id,v.version());}
 @PostMapping("/orders/{id}/release") public Object release(@PathVariable long id,@RequestBody Version v){return s.release(id,v.version());}
}
