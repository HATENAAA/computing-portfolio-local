package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.Setmeal;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SetmealRepository extends JpaRepository<Setmeal, Integer> {
    List<Setmeal> findByType(Integer type);
    Optional<Setmeal> findBySmId(Integer smId);
}
