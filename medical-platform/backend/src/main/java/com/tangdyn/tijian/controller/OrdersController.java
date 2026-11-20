package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.Orders;
import com.tangdyn.tijian.service.OrdersService;
import org.springframework.web.bind.annotation.*;
import java.security.Principal;
import java.util.List;

@RestController
@RequestMapping("/orders")
public class OrdersController {
    private final OrdersService orders;

    public OrdersController(OrdersService orders) { this.orders = orders; }

    @PostMapping("/getOrdersByUserId")
    public int count(Principal patient) { return orders.getOrdersByUserId(patient.getName()); }

    @PostMapping("/saveOrders")
    public Orders book(@RequestBody Orders requested, Principal patient) {
        return orders.book(requested, patient.getName());
    }

    @PostMapping("/listOrdersByUserId")
    public List<Orders> list(@RequestBody Orders filter, Principal patient) {
        return orders.listOrdersByUserId(patient.getName(), filter.getState());
    }

    @PostMapping("/removeOrders")
    public void cancel(@RequestBody Orders item, Principal patient) {
        orders.cancel(item.getOrderId(), patient.getName());
    }

    @PostMapping("/getOrdersByOrderId")
    public Orders detail(@RequestBody Orders item, Principal patient) {
        return orders.requireOwnedOrder(item.getOrderId(), patient.getName());
    }
}
