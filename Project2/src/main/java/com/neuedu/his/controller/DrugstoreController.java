package com.neuedu.his.controller;

import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.DrugInventoryVO;
import com.neuedu.his.service.AdminService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/drugstore")
public class DrugstoreController {

    @Autowired
    private AdminService adminService;

    @GetMapping("/inventory")
    public PageResult<DrugInventoryVO> getInventory(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize) {
        return new PageResult<>();
    }
}