package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.Hospital;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import jakarta.persistence.LockModeType;

import java.util.List;
import java.util.Optional;

public interface HospitalRepository extends JpaRepository<Hospital, Integer> {
    List<Hospital> findByState(Integer state);

    Optional<Hospital> findByHpId(Integer hospitalId);


    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select h from Hospital h where h.hpId = :id")
    Optional<Hospital> lockByHpId(@Param("id") Integer id);
}
