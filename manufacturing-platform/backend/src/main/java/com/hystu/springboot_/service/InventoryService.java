package com.hystu.springboot_.service;

import com.hystu.springboot_.entity.Order;
import com.hystu.springboot_.mapper.OrderMapper;
import java.util.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

@Service
@Transactional
public class InventoryService {
  private final JdbcTemplate db; private final Access access; private final OrderMapper orders;
  public InventoryService(JdbcTemplate db, Access access, OrderMapper orders){this.db=db;this.access=access;this.orders=orders;}
  public record MaterialInput(String factoryName,String sku,String name,String unit){}
  public record Line(long materialId,long units){}
  public record BomInput(String factoryName,String productName,int version,List<Line> lines){}
  public record Receipt(long quantity,String requestId){}
  private static Map<String,Object> norm(Map<String,Object> row){var out=new LinkedHashMap<String,Object>();row.forEach((k,v)->out.put(k.toLowerCase(Locale.ROOT),v));return out;}
  private List<Map<String,Object>> rows(String sql,Object...args){return db.queryForList(sql,args).stream().map(InventoryService::norm).toList();}
  private Map<String,Object> one(String sql,Object...args){var list=rows(sql,args);return list.isEmpty()?null:list.get(0);}
  private long num(Map<String,Object> row,String key){return ((Number)row.get(key)).longValue();}
  private void conflict(String message){throw new ResponseStatusException(HttpStatus.CONFLICT,message);}
  private String factory(String requested){var u=access.role("factoryAdmin","superAdmin");if(requested!=null&&!requested.isBlank())access.factory(requested);String name=u.getRole().equals("factoryAdmin")?u.getFactoryName():requested;Access.label(name,100,"Factory");access.factory(name);Access.found(one("SELECT * FROM factories WHERE factoryName=?",name));return name;}
  public Map<String,Object> workspace(String requested){String f=factory(requested);return Map.of("factoryName",f,"materials",rows("SELECT *,onHand-reserved AS available FROM materials WHERE factoryName=? ORDER BY sku",f),"boms",rows("SELECT * FROM bom_headers WHERE factoryName=? ORDER BY productName",f),"ledger",rows("SELECT l.*,m.sku,m.name FROM material_ledger l JOIN materials m ON m.id=l.materialId WHERE m.factoryName=? ORDER BY l.id DESC LIMIT 100",f));}
  @Transactional(readOnly=true,isolation=org.springframework.transaction.annotation.Isolation.REPEATABLE_READ)
  public Map<String,Object> reconcile(String requested){
    String f=factory(requested);
    // Every query shares one repeatable-read snapshot; no repair writes are performed.
    var movements=rows("SELECT l.materialId, SUM(CASE WHEN l.kind='RECEIPT' THEN l.quantity WHEN l.kind='ISSUE' THEN -l.quantity ELSE 0 END) AS expectedStock, SUM(CASE WHEN l.kind='RESERVE' THEN l.quantity WHEN l.kind IN ('RELEASE','ISSUE') THEN -l.quantity ELSE 0 END) AS expectedReserved FROM material_ledger l JOIN materials m ON m.id=l.materialId WHERE m.factoryName=? GROUP BY l.materialId",f);
    var live=rows("SELECT l.materialId,SUM(l.quantity) AS activeReserved FROM reservation_lines l JOIN material_reservations r ON r.orderId=l.orderId JOIN materials m ON m.id=l.materialId WHERE m.factoryName=? AND r.status='RESERVED' GROUP BY l.materialId",f);
    var ledgerById=new HashMap<Long,Map<String,Object>>();for(var r:movements)ledgerById.put(num(r,"materialid"),r);
    var liveById=new HashMap<Long,Long>();for(var r:live)liveById.put(num(r,"materialid"),num(r,"activereserved"));
    var results=new ArrayList<Map<String,Object>>();int failures=0;
    for(var m:rows("SELECT * FROM materials WHERE factoryName=? ORDER BY sku",f)){
      long id=num(m,"id"),stock=num(m,"onhand"),reserved=num(m,"reserved");var l=ledgerById.get(id);
      long expectedStock=l==null?0:num(l,"expectedstock"),expectedReserved=l==null?0:num(l,"expectedreserved"),active=liveById.getOrDefault(id,0L);
      var codes=new ArrayList<String>();
      if(stock<0||reserved<0||reserved>stock)codes.add("STOCK_BOUNDS");
      if(stock!=expectedStock)codes.add("STOCK_LEDGER_MISMATCH");
      if(reserved!=expectedReserved)codes.add("RESERVATION_LEDGER_MISMATCH");
      if(reserved!=active)codes.add("ACTIVE_RESERVATION_MISMATCH");
      if(!codes.isEmpty())failures++;
      results.add(Map.of("materialId",id,"sku",m.get("sku"),"onHand",stock,"reserved",reserved,"ledgerStock",expectedStock,"ledgerReserved",expectedReserved,"activeReserved",active,"issues",codes));
    }
    return Map.of("factoryName",f,"consistent",failures==0,"checkedMaterials",results.size(),"inconsistentMaterials",failures,"materials",results,"scope","Read-only ledger and active-reservation reconciliation; no automatic correction");
  }
  public Map<String,Object> create(MaterialInput in){String f=factory(in.factoryName());Access.label(in.sku(),64,"SKU");Access.label(in.name(),100,"Material");Access.label(in.unit(),16,"Unit");
    db.queryForList("SELECT id FROM factories WHERE factoryName=? FOR UPDATE",f);
    if(one("SELECT id FROM materials WHERE factoryName=? AND sku=?",f,in.sku())!=null)conflict("SKU already exists");
    db.update("INSERT INTO materials(factoryName,sku,name,unit) VALUES(?,?,?,?)",f,in.sku(),in.name(),in.unit());return one("SELECT *,onHand-reserved AS available FROM materials WHERE factoryName=? AND sku=?",f,in.sku());}
  public Map<String,Object> receive(long id,Receipt in){Access.require(in.quantity()>0&&in.quantity()<=1000000000L,"Receipt quantity must be 1..1000000000");
    Access.require(in.requestId()!=null&&in.requestId().matches("[a-zA-Z0-9_-]{16,64}"),"A 16..64 character request ID is required");
    var m=one("SELECT * FROM materials WHERE id=? FOR UPDATE",id);Access.found(m);factory((String)m.get("factoryname"));
    var old=one("SELECT * FROM material_ledger WHERE materialId=? AND requestId=?",id,in.requestId());
    if(old!=null){if(num(old,"quantity")!=in.quantity())conflict("Request ID was already used with a different quantity");return old;}
    Access.require(num(m,"onhand")+in.quantity()<=1000000000000L,"Stock limit exceeded");
    db.update("UPDATE materials SET onHand=onHand+?,version=version+1 WHERE id=?",in.quantity(),id);
    ledger(id,null,"RECEIPT",in.quantity(),in.requestId());return one("SELECT * FROM material_ledger WHERE materialId=? AND requestId=?",id,in.requestId());}
  public Map<String,Object> saveBom(BomInput in){String f=factory(in.factoryName());Access.label(in.productName(),100,"Product");Access.require(in.lines()!=null&&!in.lines().isEmpty()&&in.lines().size()<=100,"BOM needs 1..100 material lines");
    db.queryForList("SELECT id FROM factories WHERE factoryName=? FOR UPDATE",f);
    var header=one("SELECT * FROM bom_headers WHERE factoryName=? AND productName=? FOR UPDATE",f,in.productName());
    if(header==null){if(in.version()!=0)conflict("BOM version changed");db.update("INSERT INTO bom_headers(factoryName,productName) VALUES(?,?)",f,in.productName());header=one("SELECT * FROM bom_headers WHERE factoryName=? AND productName=?",f,in.productName());}
    else if(num(header,"version")!=in.version())conflict("BOM changed; reload before saving");
    var ids=new HashSet<Long>();for(var line:in.lines()){Access.require(line.units()>0&&line.units()<=1000000L&&ids.add(line.materialId()),"BOM units must be 1..1000000 and materials must be unique");var m=one("SELECT * FROM materials WHERE id=?",line.materialId());Access.found(m);Access.require(f.equals(m.get("factoryname")),"Material belongs to a different factory");}
    long id=num(header,"id");db.update("DELETE FROM bom_lines WHERE bomId=?",id);for(var line:in.lines())db.update("INSERT INTO bom_lines(bomId,materialId,units) VALUES(?,?,?)",id,line.materialId(),line.units());db.update("UPDATE bom_headers SET version=version+1 WHERE id=?",id);return bom(id);}
  public Map<String,Object> bom(long id){var h=one("SELECT * FROM bom_headers WHERE id=?",id);Access.found(h);factory((String)h.get("factoryname"));var out=new LinkedHashMap<>(h);out.put("lines",rows("SELECT b.*,m.sku,m.name,m.unit FROM bom_lines b JOIN materials m ON m.id=b.materialId WHERE bomId=? ORDER BY materialId",id));return out;}
  private Order working(long id,Integer version){var o=orders.lock(id);Access.found(o);factory(o.getFactoryName());if(version==null||o.getVersion()!=version)conflict("Order changed; refresh before retrying");Access.require("ACCEPTED".equals(o.getStatus()),"Materials can only be reserved or released before production");return o;}
  public Map<String,Object> orderMaterials(long id){var o=orders.findById(id);Access.found(o);factory(o.getFactoryName());var header=one("SELECT * FROM bom_headers WHERE factoryName=? AND productName=?",o.getFactoryName(),o.getProductName());var reservation=one("SELECT * FROM material_reservations WHERE orderId=?",id);List<Map<String,Object>> lines;
    if(reservation!=null)lines=rows("SELECT r.materialId,r.quantity,m.sku,m.name,m.unit,m.onHand,m.reserved,m.onHand-m.reserved AS available FROM reservation_lines r JOIN materials m ON m.id=r.materialId WHERE orderId=? ORDER BY materialId",id);
    else lines=header==null?List.of():rows("SELECT b.materialId,b.units*CAST(? AS BIGINT) AS quantity,m.sku,m.name,m.unit,m.onHand,m.reserved,m.onHand-m.reserved AS available FROM bom_lines b JOIN materials m ON m.id=b.materialId WHERE bomId=? ORDER BY materialId",o.getQuantity(),num(header,"id"));
    return Map.of("status",reservation==null?(header==null?"NO_BOM":"UNRESERVED"):reservation.get("status"),"bomVersion",reservation==null?(header==null?0:num(header,"version")):num(reservation,"bomversion"),"lines",lines);}
  public Map<String,Object> reserve(long id,Integer version){var o=working(id,version);var old=one("SELECT * FROM material_reservations WHERE orderId=?",id);if(old!=null&&"RESERVED".equals(old.get("status")))return orderMaterials(id);
    Access.require(old==null||"RELEASED".equals(old.get("status")),"Materials already consumed");
    var h=one("SELECT * FROM bom_headers WHERE factoryName=? AND productName=? FOR UPDATE",o.getFactoryName(),o.getProductName());Access.require(h!=null,"Configure a BOM for this product first");
    var lines=rows("SELECT * FROM bom_lines WHERE bomId=? ORDER BY materialId",num(h,"id"));Access.require(!lines.isEmpty(),"BOM is empty");
    if(old!=null)db.update("DELETE FROM material_reservations WHERE orderId=?",id);
    db.update("INSERT INTO material_reservations(orderId,bomVersion,status) VALUES(?,?,'RESERVED')",id,num(h,"version"));
    for(var line:lines){long mid=num(line,"materialid"),q=Math.multiplyExact(num(line,"units"),(long)o.getQuantity());var m=one("SELECT * FROM materials WHERE id=? FOR UPDATE",mid);if(num(m,"onhand")-num(m,"reserved")<q)conflict("Insufficient stock for "+m.get("sku"));db.update("UPDATE materials SET reserved=reserved+?,version=version+1 WHERE id=?",q,mid);db.update("INSERT INTO reservation_lines(orderId,materialId,quantity) VALUES(?,?,?)",id,mid,q);ledger(mid,id,"RESERVE",q,null);}
    audit(o,"RESERVE","Materials reserved using BOM revision "+num(h,"version"));return orderMaterials(id);}
  public Map<String,Object> release(long id,Integer version){var o=working(id,version);var h=one("SELECT * FROM material_reservations WHERE orderId=?",id);Access.require(h!=null&&"RESERVED".equals(h.get("status")),"No active material reservation");
    for(var l:rows("SELECT * FROM reservation_lines WHERE orderId=? ORDER BY materialId",id)){long mid=num(l,"materialid"),q=num(l,"quantity");db.queryForList("SELECT id FROM materials WHERE id=? FOR UPDATE",mid);db.update("UPDATE materials SET reserved=reserved-?,version=version+1 WHERE id=?",q,mid);ledger(mid,id,"RELEASE",q,null);}db.update("UPDATE material_reservations SET status='RELEASED' WHERE orderId=?",id);audit(o,"RELEASE","Material reservation released");return orderMaterials(id);}
  // Called by OrderService inside the SAME transaction, after its order/device locks.
  public void consumeOnStart(Order o){var reservation=one("SELECT * FROM material_reservations WHERE orderId=?",o.getId());
    var bom=one("SELECT * FROM bom_headers WHERE factoryName=? AND productName=? FOR UPDATE",o.getFactoryName(),o.getProductName());
    if(reservation==null&&bom==null)return; // Historical products without a BOM remain compatible.
    if(reservation!=null&&"CONSUMED".equals(reservation.get("status")))return; // Resume never issues twice.
    Access.require(reservation!=null&&"RESERVED".equals(reservation.get("status")),"Reserve materials before starting production");
    for(var l:rows("SELECT * FROM reservation_lines WHERE orderId=? ORDER BY materialId",o.getId())){long mid=num(l,"materialid"),q=num(l,"quantity");db.queryForList("SELECT id FROM materials WHERE id=? FOR UPDATE",mid);db.update("UPDATE materials SET onHand=onHand-?,reserved=reserved-?,version=version+1 WHERE id=?",q,q,mid);ledger(mid,o.getId(),"ISSUE",q,null);}db.update("UPDATE material_reservations SET status='CONSUMED' WHERE orderId=?",o.getId());}
  private void ledger(long mid,Long oid,String kind,long quantity,String request){db.update("INSERT INTO material_ledger(materialId,orderId,kind,quantity,actor,requestId) VALUES(?,?,?,?,?,?)",mid,oid,kind,quantity,access.actor().getUsername(),request);}
  private void audit(Order o,String type,String note){if(orders.touch(o.getId(),o.getVersion())!=1)conflict("Order changed");orders.log(o.getId(),o.getStatus(),access.actor().getUsername(),o.getVersion()+1,type,note);}
}
