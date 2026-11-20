package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "doctor")
public class Doctor {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "docID")
    private Integer docId; // 医生编号

    @NotBlank
    @Column(name = "doccode", length = 20, nullable = false, unique = true)
    private String docCode; // 医生编码（登录用）

    @NotBlank
    @Column(name = "realname", length = 20, nullable = false)
    private String realName; // 医生真实姓名

    @NotBlank
    @Column(name = "password", length = 72, nullable = false)
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String password; // 医生登录密码

    @Column(name = "sex")
    private Integer sex; // 医生性别

    @Column(name = "deptno")
    private Integer deptno; // 医生所属部门编号
}
