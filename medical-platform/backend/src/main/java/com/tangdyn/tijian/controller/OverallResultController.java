package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.OverallResult;
import com.tangdyn.tijian.service.OverallResultService;
import com.tangdyn.tijian.service.OrdersService;
import java.security.Principal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/overallResult")
public class OverallResultController {

    private final OverallResultService overallResultService;

    private final OrdersService orders;

    public OverallResultController(OverallResultService overallResultService, OrdersService orders) {
        this.orders = orders;
        this.overallResultService = overallResultService;
    }

    @PostMapping("/listOverallResultByOrderId")
    public Optional<OverallResult> listOverallResultByOrderId(@RequestBody OverallResult overallResult, Principal patient) {
        orders.requireOwnedOrder(overallResult.getOrderId(), patient.getName());
        return overallResultService.listOverallResultByOrderId(overallResult.getOrderId());
    }
}
