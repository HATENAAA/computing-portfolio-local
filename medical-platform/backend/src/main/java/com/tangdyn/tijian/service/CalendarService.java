package com.tangdyn.tijian.service;

import com.tangdyn.tijian.dto.CalendarRequestDto;
import com.tangdyn.tijian.dto.CalendarResponseDto;
import com.tangdyn.tijian.model.Hospital;
import com.tangdyn.tijian.repository.HospitalRepository;
import com.tangdyn.tijian.repository.OrdersRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

@Service
public class CalendarService {

    private final HospitalRepository hospitalRepository;
    private final OrdersRepository ordersRepository;

    @Autowired
    public CalendarService(HospitalRepository hospitalRepository, OrdersRepository ordersRepository) {
        this.hospitalRepository = hospitalRepository;
        this.ordersRepository = ordersRepository;
    }

    public List<CalendarResponseDto> listAppointmentCalendar(CalendarRequestDto request) throws ParseException {
        Integer hospitalId = request.getHpId();
        int year = request.getYear();
        int month = request.getMonth();

        // 获取医院信息
        Optional<Hospital> hospitalOpt = hospitalRepository.findById(hospitalId);
        if (hospitalOpt.isEmpty()) {
            throw new RuntimeException("医院未找到");
        }

        Hospital hospital = hospitalOpt.get();
        String[] rules = hospital.getRule().split(",");

        // 获取该月份的所有日期
        List<Date> dates = getDatesOfMonth(year, month);

        // 获取该月份每天的预约情况
        List<CalendarResponseDto> calendar = new ArrayList<>();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");

        for (Date date : dates) {
            Calendar calendarDate = Calendar.getInstance();
            calendarDate.setTime(date);
            int dayOfWeek = calendarDate.get(Calendar.DAY_OF_WEEK); // 星期天为1，星期一为2，依此类推
            int index = (dayOfWeek - 1) % 7; // 将星期日映射为0，星期六映射为6
            int totalAppointments = Integer.parseInt(rules[index]);
            int bookedAppointments = ordersRepository.countByHospitalIdAndOrderDate(hospitalId, new java.sql.Date(date.getTime()));
            int remainingAppointments = totalAppointments - bookedAppointments;

            CalendarResponseDto dto = new CalendarResponseDto();
            dto.setYmd(sdf.format(date)); // 只设置日期部分
            dto.setTotal(totalAppointments);
            dto.setExisting(bookedAppointments);
            dto.setRemainder(remainingAppointments);

            calendar.add(dto);
        }

        return calendar;
    }

    private List<Date> getDatesOfMonth(int year, int month) throws ParseException {
        List<Date> dates = new ArrayList<>();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");

        Calendar calendar = Calendar.getInstance();
        calendar.set(year, month - 1, 1);

        int maxDay = calendar.getActualMaximum(Calendar.DAY_OF_MONTH);

        for (int i = 1; i <= maxDay; i++) {
            dates.add(sdf.parse(sdf.format(calendar.getTime())));
            calendar.add(Calendar.DAY_OF_MONTH, 1);
        }

        return dates;
    }
}
