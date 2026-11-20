package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.*;
import com.tangdyn.tijian.service.*;
import com.tangdyn.tijian.repository.OrdersRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import com.tangdyn.tijian.util.JwtTokenUtil;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.server.ResponseStatusException;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/doctor")
public class DoctorController {

    record PublishedReport(OverallResult summary, List<CiDetailedReport> readings) {}

    private final DoctorService doctorService;
    private final OrdersRepository orders;
    private final CiDetailedReportService detailedReports;
    private final JwtTokenUtil tokens;
    private final ReportPublication publication;
    private final OrdersService ordersService;
    private final SetmealService setmealService;
    private final CiReportService ciReportService;
    private final CheckItemService checkItemService;
    private final OverallResultService overallResultService;
    private final CheckItemDetailedService checkItemDetailedService;

    @Autowired
    public DoctorController(DoctorService doctorService, OrdersService ordersService, SetmealService setmealService, CiReportService ciReportService, CheckItemService checkItemService, OverallResultService overallResultService, CheckItemDetailedService checkItemDetailedService, JwtTokenUtil tokens, ReportPublication publication,
                            OrdersRepository orders, CiDetailedReportService detailedReports) {
        this.orders = orders;
        this.detailedReports = detailedReports;
        this.tokens = tokens;
        this.publication = publication;
        this.doctorService = doctorService;
        this.ordersService = ordersService;
        this.setmealService = setmealService;
        this.ciReportService = ciReportService;
        this.checkItemService = checkItemService;
        this.overallResultService = overallResultService;
        this.checkItemDetailedService = checkItemDetailedService;
    }


    @PostMapping("/getDoctorByCodeByPass")
    public ResponseEntity<?> getDoctorByCodeByPass(@RequestBody Doctor doctor) {
        if (doctor.getDocCode() == null || doctor.getPassword() == null) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid request");
        }
        Doctor found = doctorService.getDoctorByCodeByPass(doctor.getDocCode(), doctor.getPassword());
        if (found == null) return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("登录信息有误。");
        return ResponseEntity.ok(Map.of("token", tokens.generateToken("doctor:" + found.getDocCode()), "name", found.getRealName()));
    }

    @GetMapping("/orders/{id}/items")
    public List<CheckItemDetailed> reportItems(@PathVariable Integer id) {
        Orders order = ordersService.getOrdersById(id);
        if (order == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        return publication.itemsFor(order);
    }

    @PostMapping("/reports")
    public ResponseEntity<Void> publish(@RequestBody ReportPublication.Publication request) {
        publication.publish(request);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/appointments")
    public List<OrdersRepository.AppointmentRow> appointments() {
        return orders.listForDoctor();
    }

    @GetMapping("/reports/{id}")
    public PublishedReport publishedReport(@PathVariable Integer id) {
        Orders order = ordersService.getOrdersById(id);
        if (order == null || !Integer.valueOf(2).equals(order.getState())) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "没有已归档的报告。");
        }
        OverallResult summary = overallResultService.listOverallResultByOrderId(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "没有已归档的报告。"));
        return new PublishedReport(summary, detailedReports.listCiDetailedReportByOrderId(id));
    }

    @PostMapping("/getOrdersByState")
    public ResponseEntity<?> getOrdersByState(@RequestBody Orders order) {
        return ResponseEntity.ok(ordersService.listOrdersByState(order.getState()));
    }

    @PostMapping("/getOrdersById")
    public ResponseEntity<?> getOrdersById(@RequestBody Orders order) {
        return ResponseEntity.ok(ordersService.getOrdersById(order.getOrderId()));
    }

    @PostMapping("/listSetmeal")
    public ResponseEntity<?> listSetmeal() {
        return ResponseEntity.ok(setmealService.listSetmeal());
    }

    @PostMapping("/getSetmealBySmId")
    public ResponseEntity<?> getSetmealBySmId(@RequestBody Setmeal setmeal) {
        return ResponseEntity.ok(setmealService.getSetmealBySmId(setmeal.getSmId()));
    }

    @PostMapping("/getOverallResult")
    public ResponseEntity<?> getOverallResult(@RequestBody OverallResult overallResult) {
        Optional<OverallResult> overallResultT = overallResultService.listOverallResultByOrderId(overallResult.getOrderId());
        if (overallResultT.isPresent()){
            return ResponseEntity.ok(overallResultT.get());
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body("No overall result found");
    }
    @PostMapping("/SaveOverallResult")
    public ResponseEntity<?> SaveOverallResult(@RequestBody OverallResult overallResult) {
        return ResponseEntity.ok(overallResultService.saveOverallResult(overallResult));
    }

    @PostMapping("/getCheckItemByCiId")
    public ResponseEntity<?> getCheckitemByCiId(@RequestBody CheckItem checkItem) {
        return ResponseEntity.ok(checkItemService.getCheckItemByCiId(checkItem.getCiId()));
    }
    @PostMapping("/listCiReport")
    public List<CiReport> listCiReport(@RequestBody CiReport ciReport) {
        return ciReportService.listCiReportByOrderId(ciReport.getOrderId());
    }
    @PostMapping("/SaveCiReportsForOrder")
    public ResponseEntity<?> SaveCiReportsForOrder(@RequestBody List<CiReport> ciReports) {
        return ResponseEntity.ok(ciReportService.saveCiReports(ciReports));
    }

    @PostMapping("/listCheckItemDetailed")
    public ResponseEntity<?> listCheckItemDetailed(@RequestBody CheckItemDetailed checkItemDetailed) {
        return ResponseEntity.ok(checkItemDetailedService.getCheckItemDetailedByCiId(checkItemDetailed.getCiId()));
    }
}