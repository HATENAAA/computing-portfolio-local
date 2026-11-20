package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.CheckItemDetailed;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CheckItemDetailedRepository extends JpaRepository<CheckItemDetailed, Integer> {

    List<CheckItemDetailed> findByCiId(Integer ciId);
}
