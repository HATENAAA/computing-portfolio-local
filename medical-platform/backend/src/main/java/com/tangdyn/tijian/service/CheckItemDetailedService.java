package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.CheckItemDetailed;
import com.tangdyn.tijian.repository.CheckItemDetailedRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CheckItemDetailedService {
    @Autowired
    private CheckItemDetailedRepository checkItemDetailedRepository;

    public CheckItemDetailedService(CheckItemDetailedRepository checkItemDetailedRepository) {
        this.checkItemDetailedRepository = checkItemDetailedRepository;
    }


    public List<CheckItemDetailed> getCheckItemDetailedByCiId(Integer ciId) {
        return checkItemDetailedRepository.findByCiId(ciId);
    }
}
