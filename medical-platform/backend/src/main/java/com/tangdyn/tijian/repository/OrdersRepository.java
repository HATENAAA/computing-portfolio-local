package com.tangdyn.tijian.repository;

import com.tangdyn.tijian.model.Orders;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.sql.Date;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface OrdersRepository extends JpaRepository<Orders, Integer> {
    int countByUserIdAndState(String userId, Integer state);
    List<Orders> findByUserIdAndState(String userId, Integer state);
    List<Orders> findByUserIdOrderByOrderDateDescOrderIdDesc(String userId);
    Optional<Orders> findByOrderId(Integer orderId);
    void deleteByOrderId(Integer orderId);
    @Query("SELECT COUNT(o) FROM Orders o WHERE o.hpId = :hospitalId AND o.orderDate = :orderDate")
    int countByHospitalIdAndOrderDate(@Param("hospitalId") Integer hospitalId, @Param("orderDate") Date orderDate);

    List<Orders> findByState(Integer state);

    interface AppointmentRow {
        Integer getOrderId();
        LocalDate getOrderDate();
        String getPhone();
        String getPatientName();
        Integer getSex();
        String getHospitalName();
        Integer getPackageId();
        String getPackageName();
        Integer getState();
    }

    @Query("""
        select o.orderId as orderId, cast(o.orderDate as LocalDate) as orderDate,
               u.userID as phone, u.realName as patientName, u.sex as sex,
               hospital.name as hospitalName, meal.smId as packageId, meal.name as packageName, o.state as state
        from Orders o
        join User u on u.userID = o.userId
        join Hospital hospital on hospital.hpId = o.hpId
        join Setmeal meal on meal.smId = o.smId
        where o.state in (1, 2)
        order by o.orderDate desc, o.orderId desc
        """)
    List<AppointmentRow> listForDoctor();

    List<Orders> findOrdersByOrderId(Integer orderId);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select o from Orders o where o.orderId = :id")
    Optional<Orders> lockById(@Param("id") Integer id);
}
