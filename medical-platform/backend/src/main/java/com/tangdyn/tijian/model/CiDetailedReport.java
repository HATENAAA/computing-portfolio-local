package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "cidetailedreport")
public class CiDetailedReport {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "cidrID")
    private Integer cidrId; // 检查项明细报告编号

    @NotBlank
    @Column(name = "name", length = 40, nullable = false)
    private String name; // 检查项明细名称

    @Column(name = "unit", length = 20)
    private String unit; // 检查项明细单位

    @Column(name = "minrange")
    private Double minrange; // 检查项明细正常值范围中的最小值

    @Column(name = "maxrange")
    private Double maxrange; // 检查项明细正常值范围中的最大值

    @Column(name = "normalvalue", length = 20)
    private String normalValue; // 检查项明细正常值

    @Column(name = "normalvaluestring", length = 20)
    private String normalValueString; // 检查项验证范围说明文字

    @Column(name = "type", nullable = false)
    private Integer type; // 检查项明细类型

    @Column(name = "value", length = 100)
    private String value; // 检查项明细值

    @Column(name = "iserror", nullable = false)
    private Integer isError; // 此项是否异常

    @Column(name = "ciID", nullable = false)
    private Integer ciId; // 所属检查项报告编号

    @Column(name = "orderID", nullable = false)
    private Integer orderId; // 所属预约编号

}