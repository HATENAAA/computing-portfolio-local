package com.hystu.springboot_.entity;

import java.time.LocalDateTime;
import org.springframework.cglib.core.Local;

public class User {

  private Long id;
  private String username;
  private String password;
  private String role;
  private String factoryName;
  private String factoryDescription;
  private String contactEmail;
  private String realName;
  private LocalDateTime createdAt;

  // Getter 和 Setter 方法

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }

  public void setCreatedAt(LocalDateTime createdAt) {
    this.createdAt = createdAt;
  }

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  @com.fasterxml.jackson.annotation.JsonProperty(
    access = com.fasterxml.jackson.annotation.JsonProperty.Access.WRITE_ONLY
  )
  public String getPassword() {
    return password;
  }

  public void setPassword(String password) {
    this.password = password;
  }

  public String getRole() {
    return role;
  }

  public void setRole(String role) {
    this.role = role;
  }

  public String getFactoryName() {
    return factoryName;
  }

  public void setFactoryName(String factoryName) {
    this.factoryName = factoryName;
  }

  public String getFactoryDescription() {
    return factoryDescription;
  }

  public void setFactoryDescription(String factoryDescription) {
    this.factoryDescription = factoryDescription;
  }

  public String getContactEmail() {
    return contactEmail;
  }

  public void setContactEmail(String contactEmail) {
    this.contactEmail = contactEmail;
  }

  public String getRealName() {
    return realName;
  }

  public void setRealName(String realName) {
    this.realName = realName;
  }
}
