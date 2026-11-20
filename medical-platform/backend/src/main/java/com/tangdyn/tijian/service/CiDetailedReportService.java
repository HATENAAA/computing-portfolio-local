package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.CiDetailedReport;
import com.tangdyn.tijian.repository.CiDetailedReportRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CiDetailedReportService {

    private final CiDetailedReportRepository ciDetailedReportRepository;

    @Autowired
    public CiDetailedReportService(CiDetailedReportRepository ciDetailedReportRepository) {
        this.ciDetailedReportRepository = ciDetailedReportRepository;
    }

    public int updateCiDetailedReports(List<CiDetailedReport> ciDetailedReports) {
        ciDetailedReportRepository.saveAll(ciDetailedReports);
        return ciDetailedReports.size();
    }

    public List<CiDetailedReport> listCiDetailedReportByOrderId(Integer orderId) {
        return ciDetailedReportRepository.findByOrderId(orderId);
    }
}
