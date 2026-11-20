package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.CiDetailedReport;
import com.tangdyn.tijian.service.CiDetailedReportService;
import com.tangdyn.tijian.service.OrdersService;
import java.security.Principal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/ciDetailedReport")
public class CiDetailedReportController {

    private final CiDetailedReportService ciDetailedReportService;

    private final OrdersService orders;

    public CiDetailedReportController(CiDetailedReportService ciDetailedReportService, OrdersService orders) {
        this.orders = orders;
        this.ciDetailedReportService = ciDetailedReportService;
    }

    @PutMapping("/updateCiDetailedReport")
    public int updateCiDetailedReport(@RequestBody List<CiDetailedReport> ciDetailedReports) {
        return ciDetailedReportService.updateCiDetailedReports(ciDetailedReports);
    }

    @PostMapping("/listCiDetailedReportByOrderId")
    public List<CiDetailedReport> listCiDetailedReportByOrderId(@RequestBody CiDetailedReport ciDetailedReport, Principal patient) {
        orders.requireOwnedOrder(ciDetailedReport.getOrderId(), patient.getName());
        return ciDetailedReportService.listCiDetailedReportByOrderId(ciDetailedReport.getOrderId());
    }
}
