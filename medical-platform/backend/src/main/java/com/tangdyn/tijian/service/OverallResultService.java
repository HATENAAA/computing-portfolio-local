package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.OverallResult;
import com.tangdyn.tijian.repository.OverallResultRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

@Component
public class OverallResultService {

    private final OverallResultRepository overallResultRepository;

    @Autowired
    public OverallResultService(OverallResultRepository overallResultRepository) {
        this.overallResultRepository = overallResultRepository;
    }

    public Optional<OverallResult> listOverallResultByOrderId(Integer orderId) {
        return overallResultRepository.findByOrderId(orderId);
    }

    public OverallResult saveOverallResult(OverallResult overallResult) {
        return overallResultRepository.save(overallResult);
    }
}
