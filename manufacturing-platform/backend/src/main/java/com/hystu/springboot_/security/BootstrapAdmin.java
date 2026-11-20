package com.hystu.springboot_.security;

import com.hystu.springboot_.entity.User;
import com.hystu.springboot_.mapper.UserMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.*;
import org.springframework.context.annotation.*;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
public class BootstrapAdmin {

  @Bean
  ApplicationRunner admin(
    UserMapper users,
    PasswordEncoder passwords,
    @Value("${app.admin-password:}") String password
  ) {
    return args -> {
      if (!password.isBlank() && users.findByUsername("admin") == null) {
        if (password.length() < 12) throw new IllegalArgumentException(
          "ADMIN_PASSWORD must contain at least 12 characters"
        );
        User u = new User();
        u.setUsername("admin");
        u.setPassword(passwords.encode(password));
        u.setRole("superAdmin");
        users.insert(u);
      }
    };
  }
}
