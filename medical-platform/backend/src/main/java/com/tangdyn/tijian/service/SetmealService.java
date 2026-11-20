package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.Setmeal;
import com.tangdyn.tijian.repository.SetmealRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

@Component
public class SetmealService {

    private final SetmealRepository setmealRepository;

    @Autowired
    public SetmealService(SetmealRepository setmealRepository) {
        this.setmealRepository = setmealRepository;
    }

    public List<Setmeal> listSetmealByType(Integer type) {
        return setmealRepository.findByType(type);
    }

    public Setmeal getSetmealById(Integer id) {
        Optional<Setmeal> optionalSetmeal = setmealRepository.findBySmId(id);
        return optionalSetmeal.orElse(null);
    }

    public List<Setmeal> listSetmeal() {
        return setmealRepository.findAll();
    }

    public Object getSetmealBySmId(Integer smId) {
        return setmealRepository.findBySmId(smId);
    }
}
