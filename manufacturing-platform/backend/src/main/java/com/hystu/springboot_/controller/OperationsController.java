package com.hystu.springboot_.controller;
import com.hystu.springboot_.entity.*;
import com.hystu.springboot_.service.OperationsService;
import org.springframework.web.bind.annotation.*;
@RestController public class OperationsController {
 private final OperationsService service; public OperationsController(OperationsService s){service=s;}
 @GetMapping("/operations/plans") public Object plans(){return service.plans();}
 @GetMapping("/operations/issues") public Object issues(){return service.issues();}
 @GetMapping("/orders/{id}") public Object detail(@PathVariable Long id){return service.detail(id);}
 @PutMapping("/orders/{id}/plan") public Object schedule(@PathVariable Long id,@RequestBody ProductionPlan p){return service.schedule(id,p);}
 @PostMapping("/orders/{id}/reports") public Object report(@PathVariable Long id,@RequestBody ProductionReport r){return service.report(id,r);}
 @PostMapping("/orders/{id}/issues") public Object issue(@PathVariable Long id,@RequestBody Issue i){return service.issue(id,i);}
 public record Resolution(Integer version,Integer orderVersion,String resolution){}
 @PatchMapping("/operations/issues/{id}") public Object resolve(@PathVariable Long id,@RequestBody Resolution r){return service.resolve(id,r.version(),r.orderVersion(),r.resolution());}
}
