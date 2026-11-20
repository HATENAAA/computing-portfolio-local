package com.tangdyn.tijian.dto;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;


@Data
@Getter
@Setter
public class CalendarResponseDto {
    private String ymd;
    private int total;
    private int existing;
    private int remainder;
}
