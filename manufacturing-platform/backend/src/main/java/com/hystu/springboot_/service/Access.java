package com.hystu.springboot_.service;

import com.hystu.springboot_.entity.User;
import com.hystu.springboot_.mapper.UserMapper;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;

@Component
public class Access {

  private final UserMapper users;

  public Access(UserMapper users) {
    this.users = users;
  }

  public User actor() {
    var auth = SecurityContextHolder.getContext().getAuthentication();
    var u = auth == null ? null : users.findByUsername(auth.getName());
    if (u == null) throw new AccessDeniedException("Login required");
    return u;
  }

  public User role(String... roles) {
    var u = actor();
    for (String r : roles) if (r.equals(u.getRole())) return u;
    throw new AccessDeniedException("Role not permitted");
  }

  public void factory(String name) {
    var u = role("superAdmin", "factoryAdmin");
    if (
      !u.getRole().equals("superAdmin") &&
      !java.util.Objects.equals(name, u.getFactoryName())
    ) throw new AccessDeniedException("Factory not permitted");
  }

  public static void require(boolean condition, String message) {
    if (!condition) throw new ResponseStatusException(
      HttpStatus.BAD_REQUEST,
      message
    );
  }

  public static void found(Object value) {
    if (value == null) throw new ResponseStatusException(
      HttpStatus.NOT_FOUND,
      "Resource not found"
    );
  }

  public static void label(String value, int limit, String field) {
    require(
      value != null && !value.isBlank() && value.length() <= limit,
      field + " is required and must fit its limit"
    );
  }
}
