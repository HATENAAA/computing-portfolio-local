package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "setmealdetailed")
public class SetmealDetailed {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "sdID")
    private Integer sdId;

    @NotNull
    @Column(name = "smID", nullable = false)
    private Integer smId;

    @NotNull
    @Column(name = "ciID", nullable = false)
    private Integer ciId;
}
