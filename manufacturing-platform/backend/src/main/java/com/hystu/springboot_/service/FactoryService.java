package com.hystu.springboot_.service;

import com.hystu.springboot_.entity.*;
import com.hystu.springboot_.mapper.*;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class FactoryService {

  private final FactoryMapper factories;
  private final Access access;

  public FactoryService(FactoryMapper f, Access a) {
    factories = f;
    access = a;
  }

  public List<Factory> all() {
    return factories.findAllFactories();
  }

  public Factory byId(Long id) {
    var f = factories.findFactoryById(id);
    Access.found(f);
    return f;
  }

  public Factory byName(String name) {
    var f = factories.getFactoryByFactoryName(name);
    Access.found(f);
    return f;
  }

  public void add(Factory f) {
    access.role("superAdmin");
    Access.label(f.getFactoryName(), 100, "Factory");
    f.setId(null);
    factories.insertFactory(f);
  }

  public void update(Long id, Factory f) {
    var old = byId(id);
    access.factory(old.getFactoryName());
    Access.require(f.getFactoryDescription()==null || f.getFactoryDescription().length()<=1000,"Description exceeds limit");
    Access.require(f.getContactEmail()==null || f.getContactEmail().length()<=200,"Email exceeds limit");
    Access.require(
      old.getFactoryName().equals(f.getFactoryName()),
      "Factory names are immutable; update description or email instead"
    );
    f.setId(id);
    factories.updateFactory(f);
  }

  public void delete(Long id) {
    access.role("superAdmin");
    byId(id);
    factories.deleteFactory(id);
  }
}
