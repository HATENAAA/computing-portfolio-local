package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.Hospital;
import com.tangdyn.tijian.service.HospitalService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/hospital")
public class HospitalController {

    private final HospitalService hospitalService;

    @Autowired
    public HospitalController(HospitalService hospitalService) {
        this.hospitalService = hospitalService;
    }

    @PostMapping("/listHospital")
    public List<Hospital> listHospital(@RequestBody Hospital hospital) {
        return hospitalService.listHospitalByStatus(hospital.getState());
    }

    @PostMapping("/getHospitalById")
    public Hospital getHospitalById(@RequestBody Hospital hospital) {
        return hospitalService.getHospitalById(hospital.getHpId());
    }
}
