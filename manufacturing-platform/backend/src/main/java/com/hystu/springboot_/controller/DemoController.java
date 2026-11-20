package com.hystu.springboot_.controller;
import com.hystu.springboot_.security.DemoAccounts;
import org.springframework.web.bind.annotation.*;
@RestController
public class DemoController {
 private final DemoAccounts demo;public DemoController(DemoAccounts demo){this.demo=demo;}
 @GetMapping("/auth/demo") public Object status(){return demo.status();}
}
