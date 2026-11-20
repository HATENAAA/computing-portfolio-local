package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "overallresult")
public class OverallResult {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "orID")
    private Integer orId;

    @NotNull
    @Size(max = 40)
    @Column(name = "title", length = 40, nullable = false)
    private String title;

    @Size(max = 400)
    @Column(name = "content", length = 400)
    private String content;

    @NotNull
    @Column(name = "orderID", nullable = false)
    private Integer orderId;
}
