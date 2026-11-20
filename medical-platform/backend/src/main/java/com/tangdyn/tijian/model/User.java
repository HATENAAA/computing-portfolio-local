package com.tangdyn.tijian.model;

import jakarta.persistence.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

import java.util.Date;

@Entity
@Getter
@Setter
@Table(name = "users")
public class User {
    @Id
    @NotBlank
    @Column(name = "userID", length = 11, nullable = false)
    private String userID; //手机号

    @NotBlank
    @Column(name = "password", nullable = false)
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String password;

    @NotBlank
    @Column(name = "realname", length = 20, nullable = false)
    private String realName;

    @NotNull
    @Column(name = "sex", length = 1, nullable = false)
    private Integer sex;

    @NotBlank
    @Column(name = "identitycard", length = 18, nullable = false)
    private String identityCard;

    @NotNull
    @Column(name = "birthday", nullable = false)
    @Temporal(TemporalType.DATE)
    private Date birthday;

    @NotNull
    @Column(name = "usertype", nullable = false)
    private Integer userType;
}
