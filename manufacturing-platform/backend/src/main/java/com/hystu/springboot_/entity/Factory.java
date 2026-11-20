package com.hystu.springboot_.entity;

public class Factory {

  private Long id;
  private String factoryName;
  private String factoryDescription;
  private String contactEmail;

  // Getters and Setters
  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
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
}
