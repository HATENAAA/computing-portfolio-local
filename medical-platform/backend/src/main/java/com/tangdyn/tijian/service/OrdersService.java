package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.Orders;
import com.tangdyn.tijian.repository.OrdersRepository;
import com.tangdyn.tijian.repository.HospitalRepository;
import com.tangdyn.tijian.repository.SetmealRepository;
import com.tangdyn.tijian.model.Hospital;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import java.time.LocalDate;
import java.time.ZoneId;
import jakarta.transaction.Transactional;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

@Component
public class OrdersService {

    private final OrdersRepository ordersRepository;

    private final HospitalRepository hospitals;
    private final SetmealRepository packages;
    private static final ZoneId ZONE = ZoneId.of("Asia/Shanghai");

    public OrdersService(OrdersRepository ordersRepository, HospitalRepository hospitals, SetmealRepository packages) {
        this.ordersRepository = ordersRepository;
        this.hospitals = hospitals;
        this.packages = packages;
    }

    public Orders requireOwnedOrder(Integer orderId, String patient) {
        if (orderId == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        return ordersRepository.findByOrderId(orderId).filter(order -> patient.equals(order.getUserId()))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }

    @Transactional
    public Orders book(Orders requested, String patient) {
        if (requested.getHpId() == null || requested.getSmId() == null || requested.getOrderDate() == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "请选择机构、套餐与日期。");
        }
        Hospital hospital = hospitals.lockByHpId(requested.getHpId()).filter(item -> item.getState() == 1)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "机构不可预约。"));
        if (!packages.existsById(requested.getSmId())) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "套餐不存在。");
        LocalDate day = java.time.Instant.ofEpochMilli(requested.getOrderDate().getTime()).atZone(ZONE).toLocalDate();
        if (day.isBefore(LocalDate.now(ZONE))) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "日期已经过去。");
        int capacity = Integer.parseInt(hospital.getRule().split(",")[day.getDayOfWeek().getValue() % 7]);
        if (ordersRepository.countByHospitalIdAndOrderDate(hospital.getHpId(), java.sql.Date.valueOf(day)) >= capacity) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "当日号源已满。");
        }
        Orders order = new Orders();
        order.setUserId(patient);
        order.setOrderDate(java.sql.Date.valueOf(day));
        order.setHpId(hospital.getHpId());
        order.setSmId(requested.getSmId());
        order.setState(1);
        return ordersRepository.save(order);
    }

    @Transactional
    public void cancel(Integer orderId, String patient) {
        if (orderId == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        Orders order = ordersRepository.lockById(orderId).filter(item -> patient.equals(item.getUserId()))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        if (order.getState() != 1) throw new ResponseStatusException(HttpStatus.CONFLICT, "报告已出，预约不能取消。");
        ordersRepository.delete(order);
    }

    public int getOrdersByUserId(String userId) {
        return ordersRepository.countByUserIdAndState(userId, 1);
    }

    public List<Orders> getOrdersByOrderId(Integer orderId) {
        return ordersRepository.findOrdersByOrderId(orderId);
    }

    public Orders saveOrders(Orders orders) {
        return ordersRepository.save(orders);
    }

    public List<Orders> listOrdersByUserId(String userId, Integer state) {
        return state == null ? ordersRepository.findByUserIdOrderByOrderDateDescOrderIdDesc(userId)
                : ordersRepository.findByUserIdAndState(userId, state);
    }

    @Transactional
    public void removeOrders(Integer orderId) {
        ordersRepository.deleteByOrderId(orderId);
    }

    public Orders getOrdersById(Integer orderId) {
        Optional<Orders> optionalOrders = ordersRepository.findByOrderId(orderId);
        return optionalOrders.orElse(null);
    }

    public List<Orders> listOrdersByState(Integer state) {
        return ordersRepository.findByState(state);
    }
}
