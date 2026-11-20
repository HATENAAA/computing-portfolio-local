package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.CiReport;
import com.tangdyn.tijian.service.CiReportService;
import com.tangdyn.tijian.service.OrdersService;
import java.security.Principal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/ciReport")
public class CiReportController {

    private final CiReportService ciReportService;

    private final OrdersService orders;

    public CiReportController(CiReportService ciReportService, OrdersService orders) {
        this.orders = orders;
        this.ciReportService = ciReportService;
    }

    @PostMapping("/listCiReport")
    public List<CiReport> listCiReport(@RequestBody CiReport ciReport, Principal patient) {
        orders.requireOwnedOrder(ciReport.getOrderId(), patient.getName());
        return ciReportService.listCiReportByOrderId(ciReport.getOrderId());
    }
}
