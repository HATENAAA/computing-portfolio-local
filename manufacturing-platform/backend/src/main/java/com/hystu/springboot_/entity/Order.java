package com.hystu.springboot_.entity;

public class Order {
  private Long id;
  public Long getId(){return id;}
  public void setId(Long value){id=value;}
  private String productName;
  public String getProductName(){return productName;}
  public void setProductName(String value){productName=value;}
  private int quantity;
  public int getQuantity(){return quantity;}
  public void setQuantity(int value){quantity=value;}
  private String factoryName;
  public String getFactoryName(){return factoryName;}
  public void setFactoryName(String value){factoryName=value;}
  private String ownerUsername;
  public String getOwnerUsername(){return ownerUsername;}
  public void setOwnerUsername(String value){ownerUsername=value;}
  private String status;
  public String getStatus(){return status;}
  public void setStatus(String value){status=value;}
  private int version;
  public int getVersion(){return version;}
  public void setVersion(int value){version=value;}
  private String priority;
  public String getPriority(){return priority;}
  public void setPriority(String value){priority=value;}
  private java.time.LocalDate dueDate;
  public java.time.LocalDate getDueDate(){return dueDate;}
  public void setDueDate(java.time.LocalDate value){dueDate=value;}
  private String notes;
  public String getNotes(){return notes;}
  public void setNotes(String value){notes=value;}
  private int completedQuantity;
  public int getCompletedQuantity(){return completedQuantity;}
  public void setCompletedQuantity(int value){completedQuantity=value;}
  private int rejectedQuantity;
  public int getRejectedQuantity(){return rejectedQuantity;}
  public void setRejectedQuantity(int value){rejectedQuantity=value;}
  private java.time.LocalDateTime createdAt;
  public java.time.LocalDateTime getCreatedAt(){return createdAt;}
  public void setCreatedAt(java.time.LocalDateTime value){createdAt=value;}
  private java.time.LocalDateTime updatedAt;
  public java.time.LocalDateTime getUpdatedAt(){return updatedAt;}
  public void setUpdatedAt(java.time.LocalDateTime value){updatedAt=value;}
}
