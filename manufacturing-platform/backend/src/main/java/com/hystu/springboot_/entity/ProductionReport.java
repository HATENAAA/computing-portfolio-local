package com.hystu.springboot_.entity;

public class ProductionReport {
  private Long id;
  public Long getId(){return id;}
  public void setId(Long value){id=value;}
  private Long orderId;
  public Long getOrderId(){return orderId;}
  public void setOrderId(Long value){orderId=value;}
  private Integer goodQuantity;
  public Integer getGoodQuantity(){return goodQuantity;}
  public void setGoodQuantity(Integer value){goodQuantity=value;}
  private Integer rejectedQuantity;
  public Integer getRejectedQuantity(){return rejectedQuantity;}
  public void setRejectedQuantity(Integer value){rejectedQuantity=value;}
  private String notes;
  public String getNotes(){return notes;}
  public void setNotes(String value){notes=value;}
  private String actor;
  public String getActor(){return actor;}
  public void setActor(String value){actor=value;}
  private java.time.LocalDateTime createdAt;
  public java.time.LocalDateTime getCreatedAt(){return createdAt;}
  public void setCreatedAt(java.time.LocalDateTime value){createdAt=value;}
  private Integer version;
  public Integer getVersion(){return version;}
  public void setVersion(Integer value){version=value;}
}
