package com.hystu.springboot_.entity;

public class ProductionPlan {
  private Long orderId;
  public Long getOrderId(){return orderId;}
  public void setOrderId(Long value){orderId=value;}
  private Long deviceId;
  public Long getDeviceId(){return deviceId;}
  public void setDeviceId(Long value){deviceId=value;}
  private java.time.LocalDateTime plannedStart;
  public java.time.LocalDateTime getPlannedStart(){return plannedStart;}
  public void setPlannedStart(java.time.LocalDateTime value){plannedStart=value;}
  private java.time.LocalDateTime plannedEnd;
  public java.time.LocalDateTime getPlannedEnd(){return plannedEnd;}
  public void setPlannedEnd(java.time.LocalDateTime value){plannedEnd=value;}
  private String notes;
  public String getNotes(){return notes;}
  public void setNotes(String value){notes=value;}
  private Integer version;
  public Integer getVersion(){return version;}
  public void setVersion(Integer value){version=value;}
}
