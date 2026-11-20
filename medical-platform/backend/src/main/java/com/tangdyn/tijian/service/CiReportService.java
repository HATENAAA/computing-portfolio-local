package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.CiReport;
import com.tangdyn.tijian.repository.CiReportRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class CiReportService {

    private final CiReportRepository ciReportRepository;

    @Autowired
    public CiReportService(CiReportRepository ciReportRepository) {
        this.ciReportRepository = ciReportRepository;
    }

    public List<CiReport> listCiReportByOrderId(Integer orderId) {
        return ciReportRepository.findByOrderId(orderId);
    }

    public List<CiReport> saveCiReports(List<CiReport> ciReports) {
        return ciReportRepository.saveAll(ciReports);
    }
}
