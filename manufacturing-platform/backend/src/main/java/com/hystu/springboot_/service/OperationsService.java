package com.hystu.springboot_.service;
import com.hystu.springboot_.entity.*;
import com.hystu.springboot_.mapper.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import java.util.*;
@Service @Transactional public class OperationsService {
  private final OperationsMapper ops; private final OrderMapper orders; private final OrderService service; private final DeviceMapper devices; private final Access access;
  public OperationsService(OperationsMapper p,OrderMapper o,OrderService s,DeviceMapper d,Access a){ops=p;orders=o;service=s;devices=d;access=a;}
  public static Map<String,Object> normalized(Map<String,Object> row){Map<String,Object> value=new LinkedHashMap<>();row.forEach((k,v)->value.put(k.toLowerCase(Locale.ROOT),v));return value;}
  public List<Map<String,Object>> plans(){var u=access.actor();return ops.plans(u.getRole(),u.getFactoryName(),u.getUsername()).stream().map(OperationsService::normalized).toList();}
  public List<Map<String,Object>> issues(){var u=access.actor();return ops.allIssues(u.getRole(),u.getFactoryName(),u.getUsername()).stream().map(OperationsService::normalized).toList();}
  public Map<String,Object> detail(Long id){var o=service.readable(id);Map<String,Object> result=new LinkedHashMap<>();result.put("order",o);result.put("plan",ops.plan(id));result.put("reports",ops.reports(id));result.put("issues",ops.issues(id));result.put("history",service.history(id));return result;}
  private Order working(Long id,Integer version){
    access.role("superAdmin","factoryAdmin");Access.found(orders.lock(id));var o=service.readable(id);
    Access.require(version!=null && version>=0,"Version is required");
    if(version!=o.getVersion())throw new ResponseStatusException(HttpStatus.CONFLICT,"Order changed; refresh before retrying");return o;
  }
  private void log(Order o,String type,String note){var u=access.actor();if(orders.touch(o.getId(),o.getVersion())!=1)throw new ResponseStatusException(HttpStatus.CONFLICT,"Order changed; refresh before retrying");orders.log(o.getId(),o.getStatus(),u.getUsername(),o.getVersion()+1,type,note);}
  public Map<String,Object> schedule(Long id,ProductionPlan p){
    var o=working(id,p.getVersion());Access.require("ACCEPTED".equals(o.getStatus()),"Only accepted orders can be scheduled");
    Access.require(p.getDeviceId()!=null && p.getPlannedStart()!=null && p.getPlannedEnd()!=null,"Device, start and end are required");
    Access.require(p.getPlannedEnd().isAfter(p.getPlannedStart()) && java.time.Duration.between(p.getPlannedStart(),p.getPlannedEnd()).compareTo(java.time.Duration.ofDays(30))<=0,"Schedule must have positive duration and span at most 30 days");
    Access.require(p.getNotes()==null || p.getNotes().length()<=1000,"Schedule notes exceed 1000 characters");
    // Serialize reservations on the target device, including plans for different orders.
    var d=devices.lock(p.getDeviceId());Access.found(d);
    Access.require(o.getFactoryName().equals(d.getFactoryName()),"Device must belong to the order factory");
    Access.require("AVAILABLE".equals(d.getStatus()),"Device is unavailable");
    if(ops.overlaps(d.getId(),id,p.getPlannedStart(),p.getPlannedEnd())>0)throw new ResponseStatusException(HttpStatus.CONFLICT,"Device schedule overlaps another active order");
    p.setOrderId(id);ops.deletePlan(id);ops.insertPlan(p);log(o,"SCHEDULE","设备 #"+d.getId()+" · "+p.getPlannedStart()+" → "+p.getPlannedEnd());return detail(id);
  }
  public Map<String,Object> report(Long id,ProductionReport r){
    var o=working(id,r.getVersion());Access.require("PRODUCING".equals(o.getStatus()),"Only running orders accept production reports");
    Access.require(r.getGoodQuantity()!=null && r.getRejectedQuantity()!=null,"Good and rejected quantities are required");
    int good=r.getGoodQuantity(),bad=r.getRejectedQuantity();
    Access.require(good>=0 && bad>=0 && (long)good+bad>0 && (long)good+bad<=1000000,"Report quantities must be positive in total and at most 1000000");
    Access.require((long)o.getCompletedQuantity()+good<=o.getQuantity(),"Good output exceeds the ordered quantity");
    Access.require((long)o.getRejectedQuantity()+bad<=Integer.MAX_VALUE,"Rejected total exceeds limit");
    Access.require(r.getNotes()==null || r.getNotes().length()<=1000,"Report notes exceed 1000 characters");
    r.setId(null);r.setOrderId(id);r.setActor(access.actor().getUsername());ops.report(r);
    if(orders.progress(id,o.getVersion(),good,bad)!=1)throw new ResponseStatusException(HttpStatus.CONFLICT,"Order changed; refresh before retrying");
    orders.log(id,o.getStatus(),access.actor().getUsername(),o.getVersion()+1,"REPORT","合格 "+good+" 件 · 不良 "+bad+" 件"+(r.getNotes()==null?"":" · "+r.getNotes()));return detail(id);
  }
  public Map<String,Object> issue(Long id,Issue i){
    var o=working(id,i.getVersion());Access.require(!Set.of("COMPLETED","CANCELLED").contains(o.getStatus()),"Closed orders cannot receive new issues");
    Access.require(i.getType()!=null && Set.of("QUALITY","EQUIPMENT","MATERIAL","PROCESS").contains(i.getType()),"Invalid issue type");
    Access.require(i.getSeverity()!=null && Set.of("LOW","MEDIUM","HIGH").contains(i.getSeverity()),"Invalid issue severity");Access.label(i.getDescription(),2000,"Issue description");
    i.setId(null);i.setOrderId(id);i.setActor(access.actor().getUsername());ops.issue(i);log(o,"ISSUE",i.getType()+" · "+i.getSeverity()+" · "+i.getDescription());return detail(id);
  }
  public Map<String,Object> resolve(Long issueId,Integer version,Integer orderVersion,String resolution){
    var i=ops.issueById(issueId);Access.found(i);var o=working(i.getOrderId(),orderVersion);Access.label(resolution,2000,"Resolution");
    Access.require(version!=null && version>=0,"Issue version is required");
    if(ops.resolve(issueId,version,resolution,access.actor().getUsername())!=1)throw new ResponseStatusException(HttpStatus.CONFLICT,"Issue changed; refresh before retrying");
    log(o,"RESOLVE","异常 #"+issueId+" · "+resolution);return detail(o.getId());
  }
}
