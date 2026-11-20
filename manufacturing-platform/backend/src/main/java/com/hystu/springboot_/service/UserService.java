package com.hystu.springboot_.service;

import com.hystu.springboot_.entity.*;
import com.hystu.springboot_.mapper.*;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserService {

  private final UserMapper users;
  private final FactoryMapper factories;
  private final PasswordEncoder passwords;

  public UserService(UserMapper u, FactoryMapper f, PasswordEncoder p) {
    users = u;
    factories = f;
    passwords = p;
  }

  @Transactional
  public User register(User u) {
    Access.label(u.getUsername(), 64, "Username");
    Access.require(
      u.getUsername().matches("[a-z0-9_-]{3,64}"),
      "Use 3–64 lowercase letters, digits, underscore or hyphen"
    );
    Access.require(
      u.getPassword() != null &&
        u
          .getPassword()
          .getBytes(java.nio.charset.StandardCharsets.UTF_8)
          .length >= 10 &&
        u
          .getPassword()
          .getBytes(java.nio.charset.StandardCharsets.UTF_8)
          .length <= 72,
      "Password must contain 10–72 UTF-8 bytes"
    );
    Access.require(
      "factoryAdmin".equals(u.getRole()) || "distributor".equals(u.getRole()),
      "Public registration cannot grant administrator privileges"
    );
    if ("factoryAdmin".equals(u.getRole())) {
      Access.label(u.getFactoryName(), 100, "Factory");
      Access.label(u.getFactoryDescription(), 1000, "Description");
      Factory f = new Factory();
      f.setFactoryName(u.getFactoryName());
      f.setFactoryDescription(u.getFactoryDescription());
      f.setContactEmail(u.getContactEmail());
      factories.insertFactory(f);
    } else {
      u.setFactoryName(null);
      u.setFactoryDescription(null);
    }
    u.setId(null);
    u.setPassword(passwords.encode(u.getPassword()));
    users.insert(u);
    return u;
  }
}
