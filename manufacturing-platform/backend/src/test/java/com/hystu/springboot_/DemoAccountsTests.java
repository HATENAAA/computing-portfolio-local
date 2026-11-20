package com.hystu.springboot_;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.jdbc.core.JdbcTemplate;
import com.hystu.springboot_.security.DemoAccounts;
@SpringBootTest(properties={"spring.datasource.url=jdbc:h2:mem:demoaccounts;MODE=MySQL;DB_CLOSE_DELAY=-1","app.demo-enabled=true"})
@AutoConfigureMockMvc
class DemoAccountsTests {
 @Autowired MockMvc mvc; @Autowired DemoAccounts demo; @Autowired JdbcTemplate db;
 @Test void freshStartupAllowsDirectDemoLoginWithoutRegistration()throws Exception{
  mvc.perform(get("/auth/demo")).andExpect(status().isOk()).andExpect(jsonPath("$.accounts.demo_factory").value(true));
  mvc.perform(post("/users/login").with(csrf()).param("username","demo_factory").param("password","Demo-Factory-2026")).andExpect(status().isOk()).andExpect(jsonPath("$.role").value("factoryAdmin"));
  mvc.perform(post("/users/login").with(csrf()).param("username","demo_dealer").param("password","Demo-Dealer-2026")).andExpect(status().isOk());
 }
 @Test void repeatedStartupPreservesExistingPasswordAndFactory()throws Exception{
  String old=db.queryForObject("SELECT password FROM users WHERE username='demo_partner'",String.class);
  try{db.update("UPDATE users SET password='changed-by-owner' WHERE username='demo_partner'");demo.run(null);demo.run(null);
   assertEquals("changed-by-owner",db.queryForObject("SELECT password FROM users WHERE username='demo_partner'",String.class));
   assertEquals(3,db.queryForObject("SELECT COUNT(*) FROM users",Integer.class));
   mvc.perform(get("/auth/demo")).andExpect(jsonPath("$.accounts.demo_partner").value(false));
  }finally{db.update("UPDATE users SET password=? WHERE username='demo_partner'",old);}
 }
}
