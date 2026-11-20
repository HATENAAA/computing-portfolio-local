package com.tangdyn.tijian.config;

import com.tangdyn.tijian.model.*;
import com.tangdyn.tijian.repository.*;
import com.tangdyn.tijian.service.ReportPublication;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Date;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;

@Component
public class DemoData implements ApplicationRunner {
    private final UserRepository users;
    private final DoctorRepository doctors;
    private final HospitalRepository hospitals;
    private final SetmealRepository packages;
    private final SetmealDetailedRepository mappings;
    private final CheckItemRepository checks;
    private final CheckItemDetailedRepository readings;
    private final OrdersRepository orders;
    private final ReportPublication reports;
    private final PasswordEncoder passwords;

    public DemoData(UserRepository users, DoctorRepository doctors, HospitalRepository hospitals,
                    SetmealRepository packages, SetmealDetailedRepository mappings, CheckItemRepository checks,
                    CheckItemDetailedRepository readings, OrdersRepository orders, ReportPublication reports,
                    PasswordEncoder passwords) {
        this.users = users;
        this.doctors = doctors;
        this.hospitals = hospitals;
        this.packages = packages;
        this.mappings = mappings;
        this.checks = checks;
        this.readings = readings;
        this.orders = orders;
        this.reports = reports;
        this.passwords = passwords;
    }

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        if (hospitals.count() != 0) return;
        User user = new User();
        user.setUserID("00000000001");
        user.setRealName("示例用户");
        user.setIdentityCard("000000000000000001");
        user.setBirthday(Date.valueOf("2000-01-01"));
        user.setSex(1);
        user.setUserType(1);
        user.setPassword(passwords.encode("Patient-demo"));
        users.save(user);

        Doctor doctor = new Doctor();
        doctor.setDocCode("DEMO-01");
        doctor.setRealName("演示医生");
        doctor.setPassword(passwords.encode("Doctor-demo"));
        doctors.save(doctor);

        Hospital clinic = clinic("海港体检中心", "海港路 100 号（示例）");
        clinic("滨河体检中心", "滨河路 50 号（示例）");
        int routine = check("一般检查", "记录基础体检项目");
        int labs = check("检验结果", "记录套餐对应的检验项目");
        Setmeal basic = plan("基础体检", 1, 199, routine);
        plan("综合体检", 1, 399, routine, labs);
        plan("基础体检", 0, 199, routine);
        plan("综合体检", 0, 399, routine, labs);
        plan("基础体检", 2, 199, routine);
        plan("综合体检", 2, 399, routine, labs);

        Orders prior = new Orders();
        prior.setUserId(user.getUserID());
        prior.setOrderDate(Date.valueOf(LocalDate.now(ZoneId.of("Asia/Shanghai")).minusDays(3)));
        prior.setHpId(clinic.getHpId());
        prior.setSmId(basic.getSmId());
        prior.setState(1);
        orders.saveAndFlush(prior);
        var sampleReadings = reports.itemsFor(prior).stream()
                .map(item -> new ReportPublication.Reading(item.getCdId(), "示例记录", false)).toList();
        reports.publish(new ReportPublication.Publication(prior.getOrderId(), "示例总检报告",
                "此记录用于演示报告生成与查询。", sampleReadings));
    }

    private Hospital clinic(String name, String address) {
        Hospital clinic = new Hospital();
        clinic.setName(name);
        clinic.setAddress(address);
        clinic.setTelephone("000-0000000");
        clinic.setPicture("/clinic.png");
        clinic.setBusinessHours("08:00–16:00");
        clinic.setDeadline("当天 ");
        clinic.setState(1);
        clinic.setRule("0,12,12,12,12,12,6");
        return hospitals.save(clinic);
    }

    private int check(String title, String description) {
        CheckItem group = new CheckItem();
        group.setCiName(title);
        group.setCiContent(description);
        checks.save(group);
        CheckItemDetailed item = new CheckItemDetailed();
        item.setName(title + "结果");
        item.setCiId(group.getCiId());
        item.setType(1);
        readings.save(item);
        return group.getCiId();
    }

    private Setmeal plan(String name, int type, int price, int... checkIds) {
        Setmeal plan = new Setmeal();
        plan.setName(name);
        plan.setType(type);
        plan.setPrice(price);
        packages.save(plan);
        for (int id : checkIds) {
            SetmealDetailed row = new SetmealDetailed();
            row.setSmId(plan.getSmId());
            row.setCiId(id);
            mappings.save(row);
        }
        return plan;
    }
}
