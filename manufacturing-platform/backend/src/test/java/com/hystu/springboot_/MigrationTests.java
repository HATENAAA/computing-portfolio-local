package com.hystu.springboot_;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.sql.DriverManager;
import org.springframework.jdbc.datasource.init.ScriptUtils;
import org.springframework.core.io.ClassPathResource;
class MigrationTests {
 @Test void populatedLegacyDatabaseRetainsRecordsAndMigrationIsRepeatable() throws Exception {
  try(var c=DriverManager.getConnection("jdbc:h2:mem:legacy_migration;MODE=MySQL","sa","");var s=c.createStatement()){
   ScriptUtils.executeSqlScript(c,new ClassPathResource("legacy-schema.sql"));
   s.executeUpdate("INSERT INTO factories(id,factoryName) VALUES(1,'Legacy Factory')");
   s.executeUpdate("INSERT INTO users(id,username,password,role) VALUES(1,'legacy-dealer','retained-hash','distributor')");
   s.executeUpdate("INSERT INTO devices(id,deviceName,factoryName) VALUES(1,'Legacy Lathe','Legacy Factory')");
   s.executeUpdate("INSERT INTO orders(id,productName,quantity,status,version,factoryName,ownerUsername) VALUES(1,'Legacy Part',25,'ACCEPTED',7,'Legacy Factory','legacy-dealer')");
   for(int pass=0;pass<2;pass++){
    ScriptUtils.executeSqlScript(c,new ClassPathResource("schema.sql"));
    try(var r=s.executeQuery("SELECT o.*,d.status AS deviceStatus,d.dailyCapacityMinutes,u.password FROM orders o JOIN devices d ON d.id=1 JOIN users u ON u.username=o.ownerUsername WHERE o.id=1")){
     assertTrue(r.next());assertEquals("Legacy Part",r.getString("productName"));assertEquals(25,r.getInt("quantity"));assertEquals("ACCEPTED",r.getString("status"));assertEquals(7,r.getInt("version"));assertEquals("legacy-dealer",r.getString("ownerUsername"));assertEquals("retained-hash",r.getString("password"));assertEquals("NORMAL",r.getString("priority"));assertEquals(0,r.getInt("completedQuantity"));assertEquals("AVAILABLE",r.getString("deviceStatus"));assertEquals(480,r.getInt("dailyCapacityMinutes"));assertFalse(r.next());
    }
    for(String table:new String[]{"users","factories","devices","orders"})try(var r=s.executeQuery("SELECT COUNT(*) FROM "+table)){assertTrue(r.next());assertEquals(1,r.getInt(1));}
   }
  }
 }
}
