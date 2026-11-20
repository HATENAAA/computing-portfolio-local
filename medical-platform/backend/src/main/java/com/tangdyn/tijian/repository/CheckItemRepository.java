package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.CheckItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface CheckItemRepository extends JpaRepository<CheckItem, Integer> {
    List<CheckItem> findByCiIdIn(List<Integer> ciIds);
    Optional<CheckItem> findByCiId(Integer ciId);
}