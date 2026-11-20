package com.hystu.springboot_;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.*;
import com.hystu.springboot_.entity.User;
import com.hystu.springboot_.mapper.UserMapper;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.*;

@SpringBootTest(
  properties = {
    "spring.datasource.url=jdbc:h2:mem:workflow;MODE=MySQL;DB_CLOSE_DELAY=-1",
    "app.admin-password=", "app.demo-enabled=false",
  }
)
@AutoConfigureMockMvc
class WorkflowTests {

  @Autowired
  MockMvc mvc;

  @Autowired
  JdbcTemplate db;

  @Autowired
  UserMapper users;

  @Autowired
  PasswordEncoder passwords;

  @Autowired
  ObjectMapper json;

  @BeforeEach
  void seed() {
    db.update("DELETE FROM orders");
    db.update("DELETE FROM devices");
    db.update("DELETE FROM users");
    db.update("DELETE FROM factories");
    db.update(
      "INSERT INTO factories(factoryName) VALUES ('Factory A'),('Factory B')"
    );
    seedUser("admin", "superAdmin", null);
    seedUser("alice", "factoryAdmin", "Factory A");
    seedUser("bob", "factoryAdmin", "Factory B");
    seedUser("dealer1", "distributor", null);
    seedUser("dealer2", "distributor", null);
  }

  void seedUser(String name, String role, String factory) {
    var u = new User();
    u.setUsername(name);
    u.setRole(role);
    u.setFactoryName(factory);
    u.setPassword(passwords.encode("test-password-123"));
    users.insert(u);
  }

  ResultActions postAs(String path, String body, String name) throws Exception {
    return mvc.perform(
      post(path)
        .with(user(name))
        .with(csrf())
        .contentType("application/json")
        .content(body)
    );
  }

  long device(String name, String factory) throws Exception {
    return json
      .readTree(
        postAs(
          "/devices",
          "{\"deviceName\":\"Lathe\",\"factoryName\":\"" + factory + "\"}",
          name
        )
          .andExpect(status().isOk())
          .andReturn()
          .getResponse()
          .getContentAsString()
      )
      .get("id")
      .asLong();
  }

  long order(String dealer, String owner) throws Exception {
    return json
      .readTree(
        postAs(
          "/orders",
          "{\"productName\":\"Part\",\"quantity\":2,\"factoryName\":\"Factory A\",\"ownerUsername\":\"" +
            owner +
            "\"}",
          dealer
        )
          .andExpect(status().isOk())
          .andReturn()
          .getResponse()
          .getContentAsString()
      )
      .get("id")
      .asLong();
  }

  @Test
  void anonymousRequestsRequireAuthentication() throws Exception {
    mvc.perform(get("/users/allUsers")).andExpect(status().isUnauthorized());
  }

  @Test
  void publicRegistrationCannotCreateSuperAdmin() throws Exception {
    postAs(
      "/users/registerUser",
      "{\"username\":\"attacker\",\"password\":\"test-password-123\",\"role\":\"superAdmin\"}",
      "dealer1"
    ).andExpect(status().isBadRequest());
    assertNull(users.findByUsername("attacker"));
  }

  @Test
  void passwordsAreHashedAndNeverReturned() throws Exception {
    postAs(
      "/users/registerUser",
      "{\"username\":\"newdealer\",\"password\":\"test-password-123\",\"role\":\"distributor\"}",
      "dealer1"
    )
      .andExpect(status().isOk())
      .andExpect(jsonPath("$.password").doesNotExist());
    assertNotEquals(
      "test-password-123",
      users.findByUsername("newdealer").getPassword()
    );
    assertTrue(
      passwords.matches(
        "test-password-123",
        users.findByUsername("newdealer").getPassword()
      )
    );
    mvc
      .perform(get("/users/allUsers").with(user("admin")))
      .andExpect(status().isOk())
      .andExpect(jsonPath("$[0].password").doesNotExist());
  }

  @Test
  void duplicateUserRollsBackNewFactory() throws Exception {
    postAs(
      "/users/registerUser",
      "{\"username\":\"alice\",\"password\":\"test-password-123\",\"role\":\"factoryAdmin\",\"factoryName\":\"Orphan\",\"factoryDescription\":\"demo\"}",
      "dealer1"
    ).andExpect(status().isConflict());
    assertEquals(
      0,
      db.queryForObject(
        "SELECT COUNT(*) FROM factories WHERE factoryName='Orphan'",
        Integer.class
      )
    );
  }

  @Test
  void duplicateFactoryIsRejectedWithoutCreatingUser() throws Exception {
    postAs(
      "/users/registerUser",
      "{\"username\":\"newowner\",\"password\":\"test-password-123\",\"role\":\"factoryAdmin\",\"factoryName\":\"Factory A\",\"factoryDescription\":\"demo\"}",
      "dealer1"
    ).andExpect(status().isConflict());
    assertNull(users.findByUsername("newowner"));
  }

  @Test
  void deviceCrudIsRestrictedToOwningFactory() throws Exception {
    long id = device("alice", "Factory A");
    mvc
      .perform(
        put("/devices/" + id)
          .with(user("bob"))
          .with(csrf())
          .contentType("application/json")
          .content("{\"deviceName\":\"Hijacked\"}")
      )
      .andExpect(status().isForbidden());
    mvc
      .perform(
        delete("/devices/" + id)
          .with(user("bob"))
          .with(csrf())
      )
      .andExpect(status().isForbidden());
    mvc
      .perform(
        put("/devices/" + id)
          .with(user("alice"))
          .with(csrf())
          .contentType("application/json")
          .content("{\"deviceName\":\"Updated\"}")
      )
      .andExpect(status().isOk());
    mvc
      .perform(
        delete("/devices/" + id)
          .with(user("alice"))
          .with(csrf())
      )
      .andExpect(status().isOk());
    assertEquals(
      0,
      db.queryForObject("SELECT COUNT(*) FROM devices", Integer.class)
    );
  }

  @Test
  void requestCannotForgeFactoryOrMoveDevice() throws Exception {
    postAs(
      "/devices",
      "{\"deviceName\":\"Fake\",\"factoryName\":\"Factory B\"}",
      "alice"
    ).andExpect(status().isForbidden());
    long id = device("alice", "Factory A");
    mvc
      .perform(
        put("/devices/" + id)
          .with(user("alice"))
          .with(csrf())
          .contentType("application/json")
          .content("{\"deviceName\":\"Moved\",\"factoryName\":\"Factory B\"}")
      )
      .andExpect(status().isBadRequest());
  }

  @Test
  void listEndpointsCannotExposeAnotherFactoryDevices() throws Exception {
    device("alice", "Factory A");
    device("bob", "Factory B");
    mvc
      .perform(get("/devices/allDevices").with(user("alice")))
      .andExpect(jsonPath("$.length()").value(1))
      .andExpect(jsonPath("$[0].factoryName").value("Factory A"));
    mvc
      .perform(get("/devices/factory/Factory B").with(user("alice")))
      .andExpect(status().isForbidden());
    mvc
      .perform(get("/devices/allDevices").with(user("dealer1")))
      .andExpect(status().isForbidden());
  }

  @Test
  void orderOwnershipComesFromLoginAndProtectsDeletion() throws Exception {
    long id = order("dealer1", "dealer2");
    assertEquals(
      "dealer1",
      db.queryForObject(
        "SELECT ownerUsername FROM orders WHERE id=?",
        String.class,
        id
      )
    );
    mvc
      .perform(get("/orders").with(user("dealer2")))
      .andExpect(jsonPath("$.length()").value(0));
    mvc
      .perform(
        delete("/orders/" + id)
          .with(user("dealer2"))
          .with(csrf())
      )
      .andExpect(status().isForbidden());
    mvc
      .perform(get("/orders").with(user("alice")))
      .andExpect(jsonPath("$.length()").value(1));
    mvc
      .perform(get("/orders").with(user("bob")))
      .andExpect(jsonPath("$.length()").value(0));
    mvc
      .perform(
        delete("/orders/" + id)
          .with(user("dealer1"))
          .with(csrf())
      )
      .andExpect(status().isOk());
  }

  @Test
  void quantityFactoryAndRoleAreValidated() throws Exception {
    postAs(
      "/orders",
      "{\"productName\":\"Part\",\"quantity\":0,\"factoryName\":\"Factory A\"}",
      "dealer1"
    ).andExpect(status().isBadRequest());
    postAs(
      "/orders",
      "{\"productName\":\"Part\",\"quantity\":1,\"factoryName\":\"Missing\"}",
      "dealer1"
    ).andExpect(status().isNotFound());
    postAs(
      "/orders",
      "{\"productName\":\"Part\",\"quantity\":1,\"factoryName\":\"Factory A\"}",
      "alice"
    ).andExpect(status().isForbidden());
  }

  @Test
  void csrfIsRequiredEvenForAnAuthenticatedMutation() throws Exception {
    mvc
      .perform(
        post("/devices")
          .with(user("alice"))
          .contentType("application/json")
          .content("{}")
      )
      .andExpect(status().isForbidden());
  }

  @Test
  void factoryLookupRoutesAreUnambiguousAndDeletionRespectsReferences()
    throws Exception {
    var id = db.queryForObject(
      "SELECT id FROM factories WHERE factoryName='Factory A'",
      Long.class
    );
    mvc
      .perform(get("/factories/" + id).with(user("dealer1")))
      .andExpect(status().isOk())
      .andExpect(jsonPath("$.factoryName").value("Factory A"));
    mvc
      .perform(get("/factories/factoryName/Factory A").with(user("dealer1")))
      .andExpect(status().isOk());
    mvc
      .perform(
        delete("/factories/" + id)
          .with(user("admin"))
          .with(csrf())
      )
      .andExpect(status().isConflict());
  }

  @Test
  void realPasswordLoginRestoresSessionAndLogoutInvalidatesIt()
    throws Exception {
    mvc
      .perform(
        post("/users/login")
          .with(csrf())
          .param("username", "alice")
          .param("password", "wrong")
      )
      .andExpect(status().isUnauthorized());
    var result = mvc
      .perform(
        post("/users/login")
          .with(csrf())
          .param("username", "alice")
          .param("password", "test-password-123")
      )
      .andExpect(status().isOk())
      .andExpect(jsonPath("$.password").doesNotExist())
      .andReturn();
    var session = (MockHttpSession) result.getRequest().getSession(false);
    assertNotNull(session);
    mvc
      .perform(get("/users/me").session(session))
      .andExpect(status().isOk())
      .andExpect(jsonPath("$.username").value("alice"));
    mvc
      .perform(post("/users/logout").session(session).with(csrf()))
      .andExpect(status().isNoContent());
    assertTrue(session.isInvalid());
  }

  @Test
  void usersCannotReadOtherUsersAndMissingRecordsReturn404() throws Exception {
    mvc
      .perform(get("/users/username/bob").with(user("alice")))
      .andExpect(status().isForbidden());
    mvc
      .perform(get("/users/allUsers").with(user("dealer1")))
      .andExpect(status().isForbidden());
    mvc
      .perform(delete("/devices/99999").with(user("alice")).with(csrf()))
      .andExpect(status().isNotFound());
  }

  ResultActions change(long id,String next,int version,String who) throws Exception {
    return mvc.perform(patch("/orders/"+id+"/status").with(user(who)).with(csrf()).contentType("application/json").content("{\"status\":\""+next+"\",\"version\":"+version+"}"));
  }
  @Test void factoryCanCompleteAnOrderWithAuditTrail() throws Exception {
    long id=order("dealer1","ignored");
    change(id,"ACCEPTED",0,"alice").andExpect(status().isOk()).andExpect(jsonPath("$.version").value(1));
    long d=device("alice","Factory A");
    plan(id,d,1,"2026-12-01T08:00:00","2026-12-01T10:00:00","alice").andExpect(status().isOk());
    change(id,"PRODUCING",2,"alice").andExpect(status().isOk());
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":2,\"rejectedQuantity\":1,\"version\":3}","alice").andExpect(status().isOk());
    change(id,"COMPLETED",4,"alice").andExpect(status().isOk());
    mvc.perform(get("/orders/"+id+"/history").with(user("dealer1"))).andExpect(status().isOk()).andExpect(jsonPath("$.length()").value(6)).andExpect(jsonPath("$[5].actor").value("alice")).andExpect(jsonPath("$[5].tostatus").value("COMPLETED"));
  }
  @Test void wrongFactoryCannotChangeOrReadOrderHistory() throws Exception {
    long id=order("dealer1","ignored");
    change(id,"ACCEPTED",0,"bob").andExpect(status().isForbidden());
    mvc.perform(get("/orders/"+id+"/history").with(user("dealer2"))).andExpect(status().isForbidden());
    assertEquals(0,db.queryForObject("SELECT version FROM orders WHERE id=?",Integer.class,id));
  }
  @Test void staleUpdateDoesNotDuplicateAudit() throws Exception {
    long id=order("dealer1","ignored");
    change(id,"ACCEPTED",0,"alice").andExpect(status().isOk());
    change(id,"ACCEPTED",0,"alice").andExpect(status().isConflict());
    assertEquals(2,db.queryForObject("SELECT COUNT(*) FROM order_events WHERE orderId=?",Integer.class,id));
  }
  @Test void dealerCanOnlyCancelPendingOrder() throws Exception {
    long id=order("dealer1","ignored");
    change(id,"ACCEPTED",0,"dealer1").andExpect(status().isForbidden());
    change(id,"CANCELLED",0,"dealer1").andExpect(status().isOk());
    change(id,"ACCEPTED",1,"alice").andExpect(status().isBadRequest());
    long second=order("dealer1","ignored");change(second,"ACCEPTED",0,"alice").andExpect(status().isOk());
    change(second,"CANCELLED",1,"dealer1").andExpect(status().isBadRequest());
  }
  @Test void statusCannotBeForgedAtCreationOrSkipped() throws Exception {
    long id=json.readTree(postAs("/orders","{\"productName\":\"Part\",\"quantity\":1,\"factoryName\":\"Factory A\",\"status\":\"COMPLETED\",\"version\":99}","dealer1").andExpect(status().isOk()).andExpect(jsonPath("$.status").value("PENDING")).andExpect(jsonPath("$.version").value(0)).andReturn().getResponse().getContentAsString()).get("id").asLong();
    change(id,"COMPLETED",0,"alice").andExpect(status().isBadRequest());
  }
  @Test void auditFailureRollsBackStatusUpdate() throws Exception {
    long id=order("dealer1","ignored");
    db.update("INSERT INTO order_events(orderId,toStatus,actor,orderVersion) VALUES(?,?,?,?)",id,"ACCEPTED","test-conflict",1);
    change(id,"ACCEPTED",0,"alice").andExpect(status().isConflict());
    assertEquals("PENDING",db.queryForObject("SELECT status FROM orders WHERE id=?",String.class,id));
    assertEquals(0,db.queryForObject("SELECT version FROM orders WHERE id=?",Integer.class,id));
  }

  ResultActions plan(long id,long device,int version,String start,String end,String who) throws Exception {
    return mvc.perform(put("/orders/"+id+"/plan").with(user(who)).with(csrf()).contentType("application/json").content(json.writeValueAsString(java.util.Map.of("deviceId",device,"version",version,"plannedStart",start,"plannedEnd",end))));
  }
  long runningOrder() throws Exception {
    long id=order("dealer1","ignored"),d=device("alice","Factory A");
    change(id,"ACCEPTED",0,"alice").andExpect(status().isOk());
    plan(id,d,1,"2026-12-01T08:00:00","2026-12-01T10:00:00","alice").andExpect(status().isOk());
    change(id,"PRODUCING",2,"alice").andExpect(status().isOk());return id;
  }
  @Test void scheduleRequiresOwnerAvailableDeviceAndAcceptedState() throws Exception {
    long id=order("dealer1","ignored"),a=device("alice","Factory A"),b=device("bob","Factory B");
    plan(id,a,0,"2026-12-01T08:00:00","2026-12-01T10:00:00","alice").andExpect(status().isBadRequest());
    change(id,"ACCEPTED",0,"alice").andExpect(status().isOk());
    plan(id,a,1,"2026-12-01T08:00:00","2026-12-01T10:00:00","dealer1").andExpect(status().isForbidden());
    plan(id,b,1,"2026-12-01T08:00:00","2026-12-01T10:00:00","alice").andExpect(status().isBadRequest());
    db.update("UPDATE devices SET status='MAINTENANCE' WHERE id=?",a);
    plan(id,a,1,"2026-12-01T08:00:00","2026-12-01T10:00:00","alice").andExpect(status().isBadRequest());
    change(id,"PRODUCING",1,"alice").andExpect(status().isBadRequest());
    assertEquals(0,db.queryForObject("SELECT COUNT(*) FROM production_plans",Integer.class));
  }
  @Test void overlapRejectedButAdjacentReservationsAllowedAndAudited() throws Exception {
    long a=order("dealer1","ignored"),b=order("dealer2","ignored"),d=device("alice","Factory A");
    change(a,"ACCEPTED",0,"alice");change(b,"ACCEPTED",0,"alice");
    plan(a,d,1,"2026-12-01T08:00:00","2026-12-01T10:00:00","alice").andExpect(status().isOk());
    plan(b,d,1,"2026-12-01T09:00:00","2026-12-01T11:00:00","alice").andExpect(status().isConflict());
    plan(b,d,1,"2026-12-01T10:00:00","2026-12-01T11:00:00","alice").andExpect(status().isOk());
    plan(a,d,1,"2026-12-02T08:00:00","2026-12-02T10:00:00","alice").andExpect(status().isConflict());
    assertEquals(2,db.queryForObject("SELECT COUNT(*) FROM production_plans",Integer.class));
    assertEquals(2,db.queryForObject("SELECT version FROM orders WHERE id=?",Integer.class,a));
    assertEquals(1,db.queryForObject("SELECT COUNT(*) FROM order_events WHERE orderId=? AND eventType='SCHEDULE'",Integer.class,a));
  }
  @Test void outputBoundsVersionAndCompletionAreEnforced() throws Exception {
    long id=runningOrder();
    change(id,"COMPLETED",3,"alice").andExpect(status().isBadRequest());
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":3,\"rejectedQuantity\":0,\"version\":3}","alice").andExpect(status().isBadRequest());
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":0,\"rejectedQuantity\":0,\"version\":3}","alice").andExpect(status().isBadRequest());
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":1,\"rejectedQuantity\":1,\"version\":3}","alice").andExpect(status().isOk()).andExpect(jsonPath("$.order.completedQuantity").value(1));
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":1,\"rejectedQuantity\":0,\"version\":3}","alice").andExpect(status().isConflict());
    change(id,"COMPLETED",4,"alice").andExpect(status().isBadRequest());
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":1,\"rejectedQuantity\":0,\"version\":4}","alice").andExpect(status().isOk());
    change(id,"COMPLETED",5,"alice").andExpect(status().isOk());
    assertEquals(2,db.queryForObject("SELECT COUNT(*) FROM production_reports WHERE orderId=?",Integer.class,id));
  }
  @Test void highIssueBlocksCompletionAndResolutionIsVersioned() throws Exception {
    long id=runningOrder();
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":2,\"rejectedQuantity\":0,\"version\":3}","alice").andExpect(status().isOk());
    var result=postAs("/orders/"+id+"/issues","{\"type\":\"QUALITY\",\"severity\":\"HIGH\",\"description\":\"Final inspection required\",\"version\":4}","alice").andExpect(status().isOk()).andReturn();
    long issue=json.readTree(result.getResponse().getContentAsString()).get("issues").get(0).get("id").asLong();
    change(id,"COMPLETED",5,"alice").andExpect(status().isBadRequest());
    mvc.perform(patch("/operations/issues/"+issue).with(user("bob")).with(csrf()).contentType("application/json").content("{\"version\":0,\"orderVersion\":5,\"resolution\":\"checked\"}")).andExpect(status().isForbidden());
    mvc.perform(patch("/operations/issues/"+issue).with(user("alice")).with(csrf()).contentType("application/json").content("{\"version\":0,\"orderVersion\":5,\"resolution\":\"checked\"}")).andExpect(status().isOk());
    change(id,"COMPLETED",6,"alice").andExpect(status().isOk());
    assertEquals("RESOLVED",db.queryForObject("SELECT status FROM production_issues WHERE id=?",String.class,issue));
  }
  @Test void pauseRequiresReasonAndDeviceMaintenancePreventsResume() throws Exception {
    long id=runningOrder();long d=db.queryForObject("SELECT deviceId FROM production_plans WHERE orderId=?",Long.class,id);
    String body="{\"deviceName\":\"Lathe\",\"status\":\"MAINTENANCE\",\"maintenanceNote\":\"inspection\",\"version\":0}";
    mvc.perform(put("/devices/"+d).with(user("alice")).with(csrf()).contentType("application/json").content(body)).andExpect(status().isBadRequest());
    change(id,"PAUSED",3,"alice").andExpect(status().isBadRequest());
    mvc.perform(patch("/orders/"+id+"/status").with(user("alice")).with(csrf()).contentType("application/json").content("{\"status\":\"PAUSED\",\"version\":3,\"note\":\"Device inspection\"}")).andExpect(status().isOk());
    mvc.perform(put("/devices/"+d).with(user("alice")).with(csrf()).contentType("application/json").content(body)).andExpect(status().isOk());
    change(id,"PRODUCING",4,"alice").andExpect(status().isBadRequest());
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":1,\"rejectedQuantity\":0,\"version\":4}","alice").andExpect(status().isBadRequest());
    assertEquals("Device inspection",db.queryForObject("SELECT note FROM order_events WHERE orderId=? AND orderVersion=4",String.class,id));
  }
  @Test void operationListsAndDetailRespectRoleScope() throws Exception {
    long id=runningOrder();postAs("/orders/"+id+"/issues","{\"type\":\"MATERIAL\",\"severity\":\"LOW\",\"description\":\"Waiting for parts\",\"version\":3}","alice").andExpect(status().isOk());
    for(String path:new String[]{"/operations/plans","/operations/issues"}){
      mvc.perform(get(path).with(user("bob"))).andExpect(jsonPath("$.length()").value(0));
      mvc.perform(get(path).with(user("dealer2"))).andExpect(jsonPath("$.length()").value(0));
      mvc.perform(get(path).with(user("dealer1"))).andExpect(jsonPath("$.length()").value(1));
    }
    mvc.perform(get("/orders/"+id).with(user("dealer2"))).andExpect(status().isForbidden());
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":1,\"rejectedQuantity\":0,\"version\":4}","dealer1").andExpect(status().isForbidden());
  }
  @Test void metadataAndDeviceVersionsCannotBeForged() throws Exception {
    postAs("/orders","{\"productName\":\"Part\",\"quantity\":2,\"factoryName\":\"Factory A\",\"priority\":\"URGENT\",\"completedQuantity\":999,\"rejectedQuantity\":999}","dealer1").andExpect(status().isOk()).andExpect(jsonPath("$.completedQuantity").value(0)).andExpect(jsonPath("$.rejectedQuantity").value(0));
    long d=device("alice","Factory A");
    for(int expected:new int[]{200,409})mvc.perform(put("/devices/"+d).with(user("alice")).with(csrf()).contentType("application/json").content("{\"deviceName\":\"Updated\",\"version\":0}")).andExpect(status().is(expected));
    mvc.perform(get("/devices/"+d+"/history").with(user("bob"))).andExpect(status().isForbidden());
  }
  @Test void productionAuditFailureRollsBackReportAndTotals() throws Exception {
    long id=runningOrder();db.update("INSERT INTO order_events(orderId,toStatus,actor,orderVersion) VALUES(?,?,?,?)",id,"PRODUCING","conflict",4);
    postAs("/orders/"+id+"/reports","{\"goodQuantity\":1,\"rejectedQuantity\":1,\"version\":3}","alice").andExpect(status().isConflict());
    assertEquals(0,db.queryForObject("SELECT COUNT(*) FROM production_reports WHERE orderId=?",Integer.class,id));
    assertEquals(0,db.queryForObject("SELECT completedQuantity FROM orders WHERE id=?",Integer.class,id));
    assertEquals(3,db.queryForObject("SELECT version FROM orders WHERE id=?",Integer.class,id));
  }
  @Test void simultaneousReservationsCannotDoubleBookDevice() throws Exception {
    long first=order("dealer1","ignored"),second=order("dealer2","ignored"),d=device("alice","Factory A");
    change(first,"ACCEPTED",0,"alice").andExpect(status().isOk());
    change(second,"ACCEPTED",0,"alice").andExpect(status().isOk());
    var start=new java.util.concurrent.CountDownLatch(1);
    var pool=java.util.concurrent.Executors.newFixedThreadPool(2);
    try {
      java.util.List<java.util.concurrent.Future<Integer>> results=new java.util.ArrayList<>();
      for(long id:new long[]{first,second})results.add(pool.submit(()->{start.await();return plan(id,d,1,"2026-12-01T08:00:00","2026-12-01T10:00:00","alice").andReturn().getResponse().getStatus();}));
      start.countDown();var statuses=new java.util.ArrayList<Integer>();
      for(var result:results)statuses.add(result.get(10,java.util.concurrent.TimeUnit.SECONDS));
      java.util.Collections.sort(statuses);assertEquals(java.util.List.of(200,409),statuses);
      assertEquals(1,db.queryForObject("SELECT COUNT(*) FROM production_plans",Integer.class));
    } finally {pool.shutdownNow();}
  }

  @Test void factoryProfileUpdatesRemainScopedAndNameImmutable() throws Exception {
    long id=db.queryForObject("SELECT id FROM factories WHERE factoryName='Factory A'",Long.class);
    String body="{\"factoryName\":\"Factory A\",\"factoryDescription\":\"Updated profile\",\"contactEmail\":\"factory@example.com\"}";
    mvc.perform(put("/factories/"+id).with(user("alice")).with(csrf()).contentType("application/json").content(body)).andExpect(status().isOk());
    mvc.perform(put("/factories/"+id).with(user("bob")).with(csrf()).contentType("application/json").content(body)).andExpect(status().isForbidden());
    mvc.perform(put("/factories/"+id).with(user("dealer1")).with(csrf()).contentType("application/json").content(body)).andExpect(status().isForbidden());
    mvc.perform(put("/factories/"+id).with(user("alice")).with(csrf()).contentType("application/json").content(body.replace("Factory A","Renamed"))).andExpect(status().isBadRequest());
  }
  @Test void scheduleDatesAndReportInputsAreValidatedWithoutPartialWrites() throws Exception {
    long id=order("dealer1","ignored"),d=device("alice","Factory A");
    change(id,"ACCEPTED",0,"alice").andExpect(status().isOk());
    plan(id,d,1,"2026-12-01T10:00:00","2026-12-01T08:00:00","alice").andExpect(status().isBadRequest());
    plan(id,d,1,"2026-12-01T08:00:00","2027-01-01T08:00:00","alice").andExpect(status().isBadRequest());
    assertEquals(0,db.queryForObject("SELECT COUNT(*) FROM production_plans",Integer.class));
    postAs("/orders","{\"productName\":\"Invalid\",\"quantity\":2,\"priority\":\"UNKNOWN\",\"factoryName\":\"Factory A\"}","dealer1").andExpect(status().isBadRequest());
    mvc.perform(put("/devices/"+d).with(user("alice")).with(csrf()).contentType("application/json").content("{\"deviceName\":\"Lathe\",\"dailyCapacityMinutes\":1441}")).andExpect(status().isBadRequest());
  }

  @Autowired com.hystu.springboot_.service.InventoryService inventory;
  long material(String sku,long stock){db.update("INSERT INTO materials(factoryName,sku,name,unit,onHand) VALUES('Factory A',?,?,'件',?)",sku,sku,stock);return db.queryForObject("SELECT id FROM materials WHERE sku=?",Long.class,sku);}
  void bom(long...ids){db.update("INSERT INTO bom_headers(factoryName,productName,version) VALUES('Factory A','Part',1)");long bid=db.queryForObject("SELECT id FROM bom_headers WHERE productName='Part'",Long.class);for(long id:ids)db.update("INSERT INTO bom_lines(bomId,materialId,units) VALUES(?,?,1)",bid,id);}
  long accepted()throws Exception{long id=order("dealer1","dealer1");patchAs("/orders/"+id+"/status","{\"status\":\"ACCEPTED\",\"version\":0}","alice").andExpect(status().isOk());return id;}
  @Test void receiptIsIdempotentAndRejectsChangedPayload()throws Exception{
    long m=material("M1",0);String path="/inventory/materials/"+m+"/receipts";
    String body="{\"quantity\":10,\"requestId\":\"receipt-command-001\"}";
    postAs(path,body,"alice").andExpect(status().isOk());postAs(path,body,"alice").andExpect(status().isOk());
    postAs(path,body.replace(":10",":11"),"alice").andExpect(status().isConflict());
    assertEquals(10L,db.queryForObject("SELECT onHand FROM materials WHERE id=?",Long.class,m));
    postAs(path,"{\"quantity\":1,\"requestId\":\"receipt-command-002\"}","bob").andExpect(status().isForbidden());
  }
  @Test void shortageRollsBackEarlierLinesAndAudit()throws Exception{
    long a=material("M1",10),b=material("M2",1);bom(a,b);long id=accepted();
    postAs("/inventory/orders/"+id+"/reserve","{\"version\":1}","alice").andExpect(status().isConflict());
    assertEquals(0L,db.queryForObject("SELECT reserved FROM materials WHERE id=?",Long.class,a));
    assertEquals(0,db.queryForObject("SELECT COUNT(*) FROM material_reservations",Integer.class));
    assertEquals(0,db.queryForObject("SELECT COUNT(*) FROM material_ledger",Integer.class));
    assertEquals(1,db.queryForObject("SELECT version FROM orders WHERE id=?",Integer.class,id));
  }
  @Test void reservationSnapshotSurvivesBomEditAndRelease()throws Exception{
    long m=material("M1",10);bom(m);long id=accepted();
    postAs("/inventory/orders/"+id+"/reserve","{\"version\":1}","alice").andExpect(status().isOk()).andExpect(jsonPath("$.lines[0].quantity").value(2));
    db.update("UPDATE bom_lines SET units=3");
    mvc.perform(get("/inventory/orders/"+id).with(user("alice"))).andExpect(jsonPath("$.lines[0].quantity").value(2));
    postAs("/inventory/orders/"+id+"/release","{\"version\":1}","alice").andExpect(status().isConflict());
    postAs("/inventory/orders/"+id+"/release","{\"version\":2}","alice").andExpect(status().isOk());
    assertEquals(0L,db.queryForObject("SELECT reserved FROM materials WHERE id=?",Long.class,m));
    postAs("/inventory/orders/"+id+"/reserve","{\"version\":3}","alice").andExpect(jsonPath("$.lines[0].quantity").value(6));
  }
  @Test void bomRejectsCrossFactoryAndStaleRevision()throws Exception{
    long m=material("M1",10);bom(m);String body="{\"factoryName\":\"Factory A\",\"productName\":\"Part\",\"version\":0,\"lines\":[{\"materialId\":"+m+",\"units\":1}]}";
    postAs("/inventory/boms",body,"alice").andExpect(status().isConflict());
    postAs("/inventory/boms",body.replace("version\":0","version\":1"),"bob").andExpect(status().isForbidden());
    mvc.perform(get("/inventory").with(user("dealer1"))).andExpect(status().isForbidden());
  }
  @Test void concurrentReservationsCannotOversell()throws Exception{
    long m=material("M1",2);bom(m);long a=accepted(),b=accepted();
    var pool=java.util.concurrent.Executors.newFixedThreadPool(2);var gate=new java.util.concurrent.CountDownLatch(1);
    java.util.concurrent.Callable<Boolean> first=()->reserveConcurrent(a,gate),second=()->reserveConcurrent(b,gate);
    var x=pool.submit(first);var y=pool.submit(second);gate.countDown();
    try{int wins=(x.get(10,java.util.concurrent.TimeUnit.SECONDS)?1:0)+(y.get(10,java.util.concurrent.TimeUnit.SECONDS)?1:0);assertEquals(1,wins);}finally{pool.shutdownNow();}
    assertEquals(2L,db.queryForObject("SELECT reserved FROM materials WHERE id=?",Long.class,m));
    assertEquals(1,db.queryForObject("SELECT COUNT(*) FROM material_reservations",Integer.class));
  }
  boolean reserveConcurrent(long id,java.util.concurrent.CountDownLatch gate)throws Exception{
    gate.await();var context=org.springframework.security.core.context.SecurityContextHolder.createEmptyContext();context.setAuthentication(new org.springframework.security.authentication.TestingAuthenticationToken("alice","", "ROLE_factoryAdmin"));org.springframework.security.core.context.SecurityContextHolder.setContext(context);
    try{inventory.reserve(id,1);return true;}catch(org.springframework.web.server.ResponseStatusException ex){assertEquals(409,ex.getStatusCode().value());return false;}finally{org.springframework.security.core.context.SecurityContextHolder.clearContext();}
  }
  ResultActions patchAs(String path,String body,String name)throws Exception{return mvc.perform(patch(path).with(user(name)).with(csrf()).contentType("application/json").content(body));}

 @Test void startConsumesReservedSnapshotExactlyOnceAcrossPauseAndResume()throws Exception{
   long m=material("M1",10);bom(m);long id=accepted(),d=device("alice","Factory A");
   mvc.perform(put("/orders/"+id+"/plan").with(user("alice")).with(csrf()).contentType("application/json").content("{\"deviceId\":"+d+",\"version\":1,\"plannedStart\":\"2027-01-01T08:00:00\",\"plannedEnd\":\"2027-01-01T09:00:00\"}")).andExpect(status().isOk());
   patchAs("/orders/"+id+"/status","{\"status\":\"PRODUCING\",\"version\":2}","alice").andExpect(status().isBadRequest());
   postAs("/inventory/orders/"+id+"/reserve","{\"version\":2}","alice").andExpect(status().isOk());
   patchAs("/orders/"+id+"/status","{\"status\":\"PRODUCING\",\"version\":3}","alice").andExpect(status().isOk());
   assertEquals(8L,db.queryForObject("SELECT onHand FROM materials WHERE id=?",Long.class,m));assertEquals(0L,db.queryForObject("SELECT reserved FROM materials WHERE id=?",Long.class,m));
   patchAs("/orders/"+id+"/status","{\"status\":\"PAUSED\",\"version\":4,\"note\":\"Tool check\"}","alice").andExpect(status().isOk());
   patchAs("/orders/"+id+"/status","{\"status\":\"PRODUCING\",\"version\":5}","alice").andExpect(status().isOk());
   assertEquals(1,db.queryForObject("SELECT COUNT(*) FROM material_ledger WHERE kind='ISSUE'",Integer.class));
   postAs("/inventory/orders/"+id+"/release","{\"version\":6}","alice").andExpect(status().isBadRequest());
 }

 @Test void reconciliationChecksAllLedgerRowsAndActiveReservations()throws Exception{
   long m=material("RECON",0);postAs("/inventory/materials/"+m+"/receipts","{\"quantity\":10,\"requestId\":\"reconcile-opening-001\"}","alice").andExpect(status().isOk());bom(m);long id=accepted();
   postAs("/inventory/orders/"+id+"/reserve","{\"version\":1}","alice").andExpect(status().isOk());
   mvc.perform(get("/inventory/reconciliation").with(user("alice")))
     .andExpect(status().isOk()).andExpect(jsonPath("$.consistent").value(true))
     .andExpect(jsonPath("$.materials[0].activeReserved").value(2));
   db.update("UPDATE materials SET onHand=onHand+1 WHERE id=?",m);
   mvc.perform(get("/inventory/reconciliation").with(user("alice")))
     .andExpect(jsonPath("$.consistent").value(false))
     .andExpect(jsonPath("$.materials[0].issues[0]").value("STOCK_LEDGER_MISMATCH"));
   assertEquals(11L,db.queryForObject("SELECT onHand FROM materials WHERE id=?",Long.class,m));
 }
 @Test void reconciliationEnforcesFactoryBoundaryAndFindsReservationDrift()throws Exception{
   long m=material("RECON",0);postAs("/inventory/materials/"+m+"/receipts","{\"quantity\":10,\"requestId\":\"reconcile-opening-001\"}","alice").andExpect(status().isOk());bom(m);long id=accepted();
   postAs("/inventory/orders/"+id+"/reserve","{\"version\":1}","alice").andExpect(status().isOk());
   db.update("UPDATE reservation_lines SET quantity=quantity+1 WHERE orderId=?",id);
   mvc.perform(get("/inventory/reconciliation").with(user("alice")))
     .andExpect(jsonPath("$.materials[0].issues[0]").value("ACTIVE_RESERVATION_MISMATCH"));
   mvc.perform(get("/inventory/reconciliation?factoryName=Factory A").with(user("bob"))).andExpect(status().isForbidden());
   mvc.perform(get("/inventory/reconciliation").with(user("dealer1"))).andExpect(status().isForbidden());
   mvc.perform(get("/inventory/reconciliation").with(user("bob"))).andExpect(jsonPath("$.checkedMaterials").value(0));
 }
}
