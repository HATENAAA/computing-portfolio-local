package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.CiReport;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CiReportRepository extends JpaRepository<CiReport, Integer> {
    List<CiReport> findByOrderId(Integer orderId);
}
