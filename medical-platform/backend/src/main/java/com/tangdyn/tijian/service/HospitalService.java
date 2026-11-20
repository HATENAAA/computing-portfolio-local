package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.Hospital;
import com.tangdyn.tijian.repository.HospitalRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

@Component
public class HospitalService {

    private final HospitalRepository hospitalRepository;

    @Autowired
    public HospitalService(HospitalRepository hospitalRepository) {
        this.hospitalRepository = hospitalRepository;
    }

    public List<Hospital> listHospitalByStatus(Integer state) {
        return hospitalRepository.findByState(state);
    }

    public Hospital getHospitalById(Integer hpId) {
        Optional<Hospital> optionalHospital = hospitalRepository.findByHpId(hpId);
        return optionalHospital.orElse(null);
    }
}
