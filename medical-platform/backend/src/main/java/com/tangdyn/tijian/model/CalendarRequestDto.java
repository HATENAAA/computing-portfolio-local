package com.tangdyn.tijian.model;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class CalendarRequestDto {
    private Long hospitalId;
    private int year;
    private int month;
}
