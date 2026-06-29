package com.neuedu.his.service;

import com.neuedu.his.model.dto.EmployeeCreateRequestDTO;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.vo.EmployeeListItemVO;

import java.util.List;

public interface EmployeeService {

    Integer createEmployee(EmployeeCreateRequestDTO request);

    List<EmployeeListItemVO> listAllEmployees();

    List<EmployeeListItemVO> listAllDoctors();

    Employee getById(Integer id);
}