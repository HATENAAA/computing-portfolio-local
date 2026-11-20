package com.hystu.springboot_.entity;

public class Issue {
  private Long id;
  public Long getId(){return id;}
  public void setId(Long value){id=value;}
  private Long orderId;
  public Long getOrderId(){return orderId;}
  public void setOrderId(Long value){orderId=value;}
  private String type;
  public String getType(){return type;}
  public void setType(String value){type=value;}
  private String severity;
  public String getSeverity(){return severity;}
  public void setSeverity(String value){severity=value;}
  private String description;
  public String getDescription(){return description;}
  public void setDescription(String value){description=value;}
  private String status;
  public String getStatus(){return status;}
  public void setStatus(String value){status=value;}
  private String resolution;
  public String getResolution(){return resolution;}
  public void setResolution(String value){resolution=value;}
  private String actor;
  public String getActor(){return actor;}
  public void setActor(String value){actor=value;}
  private String resolvedBy;
  public String getResolvedBy(){return resolvedBy;}
  public void setResolvedBy(String value){resolvedBy=value;}
  private java.time.LocalDateTime createdAt;
  public java.time.LocalDateTime getCreatedAt(){return createdAt;}
  public void setCreatedAt(java.time.LocalDateTime value){createdAt=value;}
  private java.time.LocalDateTime resolvedAt;
  public java.time.LocalDateTime getResolvedAt(){return resolvedAt;}
  public void setResolvedAt(java.time.LocalDateTime value){resolvedAt=value;}
  private Integer version;
  public Integer getVersion(){return version;}
  public void setVersion(Integer value){version=value;}
}
