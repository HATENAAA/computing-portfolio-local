package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "checkitemdetailed")
public class CheckItemDetailed {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "cdID")
    private Integer cdId;

    @NotBlank
    @Column(name = "name", length = 40, nullable = false)
    private String name;

    @Column(name = "unit", length = 20)
    private String unit;

    @Column(name = "minrange")
    private Double minrange;

    @Column(name = "maxrange")
    private Double maxrange;

    @Column(name = "normalvalue", length = 20)
    private String normalValue;

    @Column(name = "normalvaluestring", length = 20)
    private String normalValueString;

    @NotNull
    @Column(name = "type", nullable = false)
    private Integer type;

    @Column(name = "ciID")
    private Integer ciId;

    @Column(name = "remarks", length = 100)
    private String remarks;
}
