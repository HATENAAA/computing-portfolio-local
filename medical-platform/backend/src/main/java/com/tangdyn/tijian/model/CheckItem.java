package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "checkitem")
public class CheckItem {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "ciID")
    private Integer ciId;

    @NotBlank
    @Column(name = "ciname", length = 30, nullable = false)
    private String ciName;

    @NotBlank
    @Column(name = "cicontent", length = 200, nullable = false)
    private String ciContent;

    @Column(name = "meaning", length = 200)
    private String meaning;

    @Column(name = "remarks", length = 50)
    private String remarks;
}
