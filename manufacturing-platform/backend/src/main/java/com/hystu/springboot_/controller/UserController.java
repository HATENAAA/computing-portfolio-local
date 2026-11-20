package com.hystu.springboot_.controller;

import com.hystu.springboot_.entity.*;
import com.hystu.springboot_.mapper.UserMapper;
import com.hystu.springboot_.service.*;
import java.util.*;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.*;

@RestController
public class UserController {

  private final UserService users;
  private final UserMapper mapper;
  private final FactoryService factories;
  private final Access access;

  public UserController(
    UserService u,
    UserMapper m,
    FactoryService f,
    Access a
  ) {
    users = u;
    mapper = m;
    factories = f;
    access = a;
  }

  @GetMapping("/auth/csrf")
  public Map<String, String> csrf(CsrfToken t) {
    return Map.of("token", t.getToken(), "headerName", t.getHeaderName());
  }

  @GetMapping("/users/me")
  public User me() {
    return access.actor();
  }

  @PostMapping("/users/registerUser")
  public User register(@RequestBody User u) {
    return users.register(u);
  }

  @GetMapping("/users/allUsers")
  public List<User> all() {
    access.role("superAdmin");
    return mapper.findAll();
  }

  @GetMapping("/users/allFactories")
  public List<Factory> factories() {
    return factories.all();
  }

  @GetMapping("/users/username/{name}")
  public User named(@PathVariable String name) {
    var actor = access.actor();
    if (!actor.getUsername().equals(name)) access.role("superAdmin");
    var u = mapper.findByUsername(name);
    Access.found(u);
    return u;
  }
}
