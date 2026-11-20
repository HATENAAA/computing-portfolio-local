package com.tangdyn.tijian.controller;

import com.tangdyn.tijian.model.CheckItem;
import com.tangdyn.tijian.model.Setmeal;
import com.tangdyn.tijian.service.CheckItemService;
import com.tangdyn.tijian.service.SetmealService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/setmeal")
public class SetmealController {

    private final SetmealService setmealService;

    private final CheckItemService checkItemService;
    @Autowired
    public SetmealController(SetmealService setmealService, CheckItemService checkItemService) {
        this.setmealService = setmealService;
        this.checkItemService = checkItemService;
    }

    @PostMapping("/listSetmealByType")
    public List<Setmeal> listSetmealByType(@RequestBody Setmeal setmeal) {
        return setmealService.listSetmealByType(setmeal.getType());
    }

    @PostMapping("/getSetmealById")
    public Setmeal getSetmealById(@RequestBody Setmeal setmeal) {
        return setmealService.getSetmealById(setmeal.getSmId());
    }

    @PostMapping("/getCheckItem")
    public List<CheckItem> listCheckItemBySmId(@RequestBody Setmeal setmeal) {
        return checkItemService.getCheckItemsBySmId(setmeal.getSmId());
    }
}
