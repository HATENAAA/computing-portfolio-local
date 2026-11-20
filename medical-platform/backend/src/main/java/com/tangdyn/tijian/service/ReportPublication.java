package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.*;
import com.tangdyn.tijian.repository.*;
import jakarta.transaction.Transactional;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;

@Service
public class ReportPublication {
    public record Reading(Integer itemId, String value, boolean flagged) {}
    public record Publication(Integer orderId, String title, String content, List<Reading> readings) {}

    private final OrdersRepository orders;
    private final CheckItemDetailedRepository details;
    private final SetmealDetailedRepository packages;
    private final CiDetailedReportRepository measurements;
    private final OverallResultRepository summaries;

    public ReportPublication(OrdersRepository orders, CheckItemDetailedRepository details,
                             SetmealDetailedRepository packages, CiDetailedReportRepository measurements,
                             OverallResultRepository summaries) {
        this.orders = orders;
        this.details = details;
        this.packages = packages;
        this.measurements = measurements;
        this.summaries = summaries;
    }

    public List<CheckItemDetailed> itemsFor(Orders order) {
        return packages.findBySmId(order.getSmId()).stream()
                .flatMap(item -> details.findByCiId(item.getCiId()).stream()).toList();
    }

    @Transactional
    public void publish(Publication request) {
        if (request.orderId() == null || request.title() == null || request.title().isBlank()
                || request.title().length() > 40 || request.content() == null || request.content().isBlank()
                || request.content().length() > 400 || request.readings() == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "请填写总检标题、结论和检查结果。");
        }
        Orders order = orders.lockById(request.orderId()).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        if (order.getState() != 1) throw new ResponseStatusException(HttpStatus.CONFLICT, "该报告已出。");
        List<CheckItemDetailed> items = itemsFor(order);
        if (items.isEmpty() || items.size() != request.readings().size()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "请录入套餐的全部检查项。");
        }
        for (CheckItemDetailed item : items) {
            Reading reading = request.readings().stream().filter(entry -> entry != null && item.getCdId().equals(entry.itemId()))
                    .findFirst().orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "检查项不匹配。"));
            if (reading.value() == null || reading.value().isBlank() || reading.value().length() > 100) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "每项结果均须填写。");
            }
            CiDetailedReport row = new CiDetailedReport();
            row.setName(item.getName());
            row.setUnit(item.getUnit());
            row.setType(item.getType());
            row.setOrderId(order.getOrderId());
            row.setCiId(item.getCiId());
            row.setValue(reading.value().strip());
            row.setIsError(reading.flagged() ? 1 : 0);
            measurements.save(row);
        }
        OverallResult summary = new OverallResult();
        summary.setOrderId(order.getOrderId());
        summary.setTitle(request.title().strip());
        summary.setContent(request.content().strip());
        summaries.save(summary);
        order.setState(2);
    }
}
