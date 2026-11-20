package com.hystu.springboot_.entity;

public class Device {
  private Long id;
  public Long getId(){return id;}
  public void setId(Long value){id=value;}
  private String deviceName;
  public String getDeviceName(){return deviceName;}
  public void setDeviceName(String value){deviceName=value;}
  private String deviceDescription;
  public String getDeviceDescription(){return deviceDescription;}
  public void setDeviceDescription(String value){deviceDescription=value;}
  private String factoryName;
  public String getFactoryName(){return factoryName;}
  public void setFactoryName(String value){factoryName=value;}
  private String status;
  public String getStatus(){return status;}
  public void setStatus(String value){status=value;}
  private String category;
  public String getCategory(){return category;}
  public void setCategory(String value){category=value;}
  private String location;
  public String getLocation(){return location;}
  public void setLocation(String value){location=value;}
  private int dailyCapacityMinutes = 480;
  public int getDailyCapacityMinutes(){return dailyCapacityMinutes;}
  public void setDailyCapacityMinutes(int value){dailyCapacityMinutes=value;}
  private java.time.LocalDate serviceDueDate;
  public java.time.LocalDate getServiceDueDate(){return serviceDueDate;}
  public void setServiceDueDate(java.time.LocalDate value){serviceDueDate=value;}
  private String maintenanceNote;
  public String getMaintenanceNote(){return maintenanceNote;}
  public void setMaintenanceNote(String value){maintenanceNote=value;}
  private int version;
  public int getVersion(){return version;}
  public void setVersion(int value){version=value;}
}
