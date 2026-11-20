package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "hospital")
public class Hospital {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "hpID")
    private Integer hpId; // 医院编号

    @NotBlank
    @Column(name = "name", length = 30, nullable = false)
    private String name; // 医院名称

    @NotBlank
    @Column(name = "picture", columnDefinition = "MEDIUMTEXT", nullable = false)
    private String picture;

    @NotBlank
    @Column(name = "telephone", length = 20, nullable = false)
    private String telephone; // 医院电话

    @NotBlank
    @Column(name = "address", length = 100, nullable = false)
    private String address; // 医院地址

    @NotBlank
    @Column(name = "businesshours", length = 100, nullable = false)
    private String businessHours; // 营业时间

    @NotBlank
    @Column(name = "deadline", length = 30, nullable = false)
    private String deadline; // 截止时间

    @NotBlank
    @Column(name = "rule", length = 30, nullable = false)
    private String rule; // 规则

    @NotNull
    @Column(name = "state", nullable = false)
    private Integer state; // 状态
}
