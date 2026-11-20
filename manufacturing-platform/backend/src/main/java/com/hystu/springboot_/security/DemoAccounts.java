package com.hystu.springboot_.security;
import com.hystu.springboot_.entity.User;
import com.hystu.springboot_.mapper.UserMapper;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;
@Component
public class DemoAccounts implements ApplicationRunner {
 private final JdbcTemplate db; private final UserMapper users; private final PasswordEncoder passwords; private final boolean enabled;
 public DemoAccounts(JdbcTemplate db,UserMapper users,PasswordEncoder passwords,@Value("${app.demo-enabled:true}") boolean enabled){this.db=db;this.users=users;this.passwords=passwords;this.enabled=enabled;}
 private static final String FACTORY="远川精密制造";
 private static final String[][] ACCOUNTS={{"demo_factory","Demo-Factory-2026","factoryAdmin"},{"demo_dealer","Demo-Dealer-2026","distributor"},{"demo_partner","Demo-Partner-2026","factoryAdmin"}};
 @Override @Transactional public void run(ApplicationArguments args){if(!enabled)return;
   if(db.queryForObject("SELECT COUNT(*) FROM factories WHERE factoryName=?",Integer.class,FACTORY)==0)db.update("INSERT INTO factories(factoryName,factoryDescription) VALUES(?,?)",FACTORY,"本机演示工厂");
   for(var a:ACCOUNTS)if(users.findByUsername(a[0])==null){var u=new User();u.setUsername(a[0]);u.setPassword(passwords.encode(a[1]));u.setRole(a[2]);if(a[2].equals("factoryAdmin")){String f=a[0].equals("demo_partner")?"锐丰精工":FACTORY;if(db.queryForObject("SELECT COUNT(*) FROM factories WHERE factoryName=?",Integer.class,f)==0)db.update("INSERT INTO factories(factoryName,factoryDescription) VALUES(?,?)",f,"本机演示工厂");u.setFactoryName(f);}users.insert(u);}
 }
 public Map<String,Object> status(){var ready=new LinkedHashMap<String,Boolean>();for(var a:ACCOUNTS){var u=users.findByUsername(a[0]);ready.put(a[0],enabled&&u!=null&&a[2].equals(u.getRole())&&passwords.matches(a[1],u.getPassword()));}return Map.of("enabled",enabled,"accounts",ready);}
}
