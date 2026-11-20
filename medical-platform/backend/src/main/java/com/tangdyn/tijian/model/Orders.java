package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

import java.util.Date;

@Entity
@Getter
@Setter
@Table(name = "orders")
public class Orders {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "orderID")
    private Integer orderId; // 订单编号

    @NotNull
    @Temporal(TemporalType.DATE)
    @Column(name = "orderdate", nullable = false)
    private Date orderDate; // 预约日期

    @NotBlank
    @Size(max = 11)
    @Column(name = "userID", length = 11, nullable = false)
    private String userId; // 客户编号

    @NotNull
    @Column(name = "hpID", nullable = false)
    private Integer hpId; // 所属医院编号

    @NotNull
    @Column(name = "smID", nullable = false)
    private Integer smId; // 所属套餐编号

    @Column(name = "state")
    private Integer state; // 订单状态（允许为空）
}
