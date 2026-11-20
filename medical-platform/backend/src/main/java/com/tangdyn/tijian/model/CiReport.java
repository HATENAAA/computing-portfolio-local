package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "cireport")
public class CiReport {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "cirID")
    private Integer cirId; // 检查项报告主键

    @NotNull
    @Column(name = "ciID", nullable = false)
    private Integer ciId; // 检查项编号

    @NotBlank
    @Column(name = "ciname", length = 30, nullable = false)
    private String ciName; // 检查项名称

    @NotNull
    @Column(name = "orderID", nullable = false)
    private Integer orderId; // 所属预约编号
}