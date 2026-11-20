package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.CiDetailedReport;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CiDetailedReportRepository extends JpaRepository<CiDetailedReport, Integer> {

    List<CiDetailedReport> findByOrderId(Integer orderId);
}
