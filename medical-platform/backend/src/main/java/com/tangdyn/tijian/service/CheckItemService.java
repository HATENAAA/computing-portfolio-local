package com.tangdyn.tijian.service;

import com.tangdyn.tijian.model.CheckItem;
import com.tangdyn.tijian.model.SetmealDetailed;
import com.tangdyn.tijian.repository.CheckItemRepository;
import com.tangdyn.tijian.repository.SetmealDetailedRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class CheckItemService {

    @Autowired
    private SetmealDetailedRepository setmealDetailedRepository;

    @Autowired
    private CheckItemRepository checkItemRepository;

    public List<CheckItem> getCheckItemsBySmId(Integer smId) {
        List<SetmealDetailed> setmealDetaileds = setmealDetailedRepository.findBySmId(smId);
        List<Integer> ciIds = setmealDetaileds.stream()
                .map(SetmealDetailed::getCiId)
                .collect(Collectors.toList());
        return checkItemRepository.findByCiIdIn(ciIds);
    }

    public Optional<CheckItem> getCheckItemByCiId(Integer ciId) {
        return checkItemRepository.findByCiId(ciId);
    }
}
