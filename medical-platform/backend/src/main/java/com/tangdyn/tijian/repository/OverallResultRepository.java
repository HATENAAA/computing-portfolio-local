package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.OverallResult;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface OverallResultRepository extends JpaRepository<OverallResult, Integer> {
    Optional<OverallResult> findByOrderId(Integer orderId);
}
