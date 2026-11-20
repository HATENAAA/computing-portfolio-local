package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.SetmealDetailed;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SetmealDetailedRepository extends JpaRepository<SetmealDetailed, Integer> {
    List<SetmealDetailed> findBySmId(Integer smId);
}
