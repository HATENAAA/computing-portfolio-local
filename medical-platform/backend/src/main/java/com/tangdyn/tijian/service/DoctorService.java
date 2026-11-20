package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.Doctor;
import com.tangdyn.tijian.repository.DoctorRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class DoctorService {
    private final DoctorRepository doctors;
    private final PasswordEncoder passwords;

    public DoctorService(DoctorRepository doctors, PasswordEncoder passwords) {
        this.doctors = doctors;
        this.passwords = passwords;
    }

    public Doctor getDoctorByCodeByPass(String code, String password) {
        return doctors.findByDocCode(code).filter(doctor -> passwords.matches(password, doctor.getPassword())).orElse(null);
    }
}
