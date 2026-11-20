package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.dto.CalendarRequestDto;
import com.tangdyn.tijian.dto.CalendarResponseDto;
import com.tangdyn.tijian.service.CalendarService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.text.ParseException;
import java.util.List;

@RestController
@RequestMapping("/calendar")
public class CalendarController {

    private final CalendarService calendarService;

    @Autowired
    public CalendarController(CalendarService calendarService) {
        this.calendarService = calendarService;
    }

    @PostMapping("/listAppointmentCalendar")
    public List<CalendarResponseDto> listAppointmentCalendar(@RequestBody CalendarRequestDto request) throws ParseException {
        return calendarService.listAppointmentCalendar(request);
    }
}
