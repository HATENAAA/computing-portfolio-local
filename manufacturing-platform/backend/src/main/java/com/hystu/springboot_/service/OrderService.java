package com.hystu.springboot_.service;

import com.hystu.springboot_.entity.*;
import com.hystu.springboot_.mapper.*;
import java.util.List;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class OrderService {

  private final OrderMapper orders;
  private final FactoryMapper factories;
  private final Access access;
  private final OperationsMapper ops;
  private final DeviceMapper devices;
  private final InventoryService inventory;

  public OrderService(OrderMapper o, FactoryMapper f, Access a, OperationsMapper operations, DeviceMapper d, InventoryService inventory) {
    orders = o;
    factories = f;
    access = a; ops=operations; devices=d; this.inventory=inventory;
  }

  public List<Order> all() {
    var u = access.actor();
    return switch (u.getRole()) {
      case "superAdmin" -> orders.findAll();
      case "factoryAdmin" -> orders.findByFactory(u.getFactoryName());
      default -> orders.findByOwner(u.getUsername());
    };
  }

  public Order add(Order o) {
    var u = access.role("distributor");
    Access.label(o.getProductName(), 100, "Product");
    Access.require(o.getQuantity() > 0, "Quantity must be positive");
    Access.found(factories.getFactoryByFactoryName(o.getFactoryName()));
    o.setId(null);
    o.setOwnerUsername(u.getUsername());
    o.setStatus("PENDING");
    o.setVersion(0);
    Access.require(o.getQuantity()<=1000000,"Quantity limit is 1000000");
    o.setPriority(o.getPriority()==null?"NORMAL":o.getPriority());
    Access.require(java.util.Set.of("NORMAL","HIGH","URGENT").contains(o.getPriority()),"Invalid priority");
    Access.require(o.getNotes()==null || o.getNotes().length()<=2000,"Notes exceed 2000 characters");
    Access.require(o.getDueDate()==null || !o.getDueDate().isBefore(java.time.LocalDate.now(java.time.ZoneId.of("Asia/Shanghai"))),"Due date cannot be in the past");
    o.setCompletedQuantity(0);o.setRejectedQuantity(0);o.setCreatedAt(null);o.setUpdatedAt(null);
    orders.insert(o);
    orders.event(o.getId(),null,"PENDING",u.getUsername(),0);
    return orders.findById(o.getId());
  }

  public Order readable(Long id){
    var o=orders.findById(id); Access.found(o);var u=access.actor();
    if(u.getRole().equals("superAdmin"))return o;
    if(u.getRole().equals("factoryAdmin") && java.util.Objects.equals(u.getFactoryName(),o.getFactoryName()))return o;
    if(u.getRole().equals("distributor") && u.getUsername().equals(o.getOwnerUsername()))return o;
    throw new AccessDeniedException("Order not permitted");
  }
  public List<java.util.Map<String,Object>> history(Long id){readable(id);return orders.events(id).stream().map(row->{java.util.Map<String,Object> normalized=new java.util.LinkedHashMap<>();row.forEach((key,value)->normalized.put(key.toLowerCase(java.util.Locale.ROOT),value));return normalized;}).toList();}
  public Order transition(Long id,String next,Integer version){return transition(id,next,version,null);}
  public Order transition(Long id,String next,Integer version,String note){
    Access.found(orders.lock(id));
    var o=readable(id);var u=access.actor();
    Access.require(next!=null && version!=null && version>=0,"Status and version are required");
    boolean cancel="CANCELLED".equals(next);
    if(cancel){
      if(!u.getRole().equals("distributor") && !u.getRole().equals("superAdmin"))throw new AccessDeniedException("Only the owner can cancel");
    }else if(!u.getRole().equals("factoryAdmin") && !u.getRole().equals("superAdmin"))throw new AccessDeniedException("Factory processing role required");
    if(version!=o.getVersion())throw new org.springframework.web.server.ResponseStatusException(org.springframework.http.HttpStatus.CONFLICT,"Order changed; refresh before retrying");
    var allowed=switch(o.getStatus()){case "PENDING"->java.util.Set.of("ACCEPTED");case "ACCEPTED"->java.util.Set.of("PRODUCING");case "PRODUCING"->java.util.Set.of("COMPLETED","PAUSED");case "PAUSED"->java.util.Set.of("PRODUCING");default->java.util.Set.<String>of();};
    Access.require(cancel ? "PENDING".equals(o.getStatus()) : allowed.contains(next),"Invalid order transition");
    if("PAUSED".equals(next))Access.label(note,1000,"Pause reason");
    if("PRODUCING".equals(next)){
      var plan=ops.plan(id);Access.require(plan!=null,"Schedule the order before starting production");
      var device=devices.lock(plan.getDeviceId());Access.found(device);
      Access.require("AVAILABLE".equals(device.getStatus()),"Device is unavailable");
      Access.require(ops.running(device.getId())==0,"Device already has a running order");
      Access.require(ops.blocking(id)==0,"Resolve high-severity issues before starting production");
      inventory.consumeOnStart(o);
    }
    if("COMPLETED".equals(next)){
      Access.require(o.getCompletedQuantity()==o.getQuantity(),"Good output must meet the ordered quantity before completion");
      Access.require(ops.blocking(id)==0,"Resolve high-severity issues before completion");
    }
    if(orders.transition(id,version,o.getStatus(),next)!=1)throw new org.springframework.web.server.ResponseStatusException(org.springframework.http.HttpStatus.CONFLICT,"Order changed; refresh before retrying");
    orders.event(id,o.getStatus(),next,u.getUsername(),version+1);
    // Pause reasons are stored on the same versioned transition event.
    if(note!=null && !note.isBlank())opsNote(id,version+1,note);
    return orders.findById(id);
  }
  private void opsNote(Long id,int version,String note){Access.require(note.length()<=1000,"Note exceeds 1000 characters");orders.note(id,version,note);}
  // Keep the old endpoint as a non-destructive cancellation operation.
  public void delete(Long id){var o=readable(id);transition(id,"CANCELLED",o.getVersion());}
}
