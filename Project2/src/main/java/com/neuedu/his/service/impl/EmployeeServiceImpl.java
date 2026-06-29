package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.DepartmentMapper;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.model.dto.EmployeeCreateRequestDTO;
import com.neuedu.his.model.entity.Department;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.vo.EmployeeListItemVO;
import com.neuedu.his.service.EmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.DigestUtils;

import java.util.ArrayList;
import java.util.List;

@Service
public class EmployeeServiceImpl implements EmployeeService {

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private DepartmentMapper departmentMapper;

    @Override
    public Integer createEmployee(EmployeeCreateRequestDTO request) {
        Employee employee = new Employee();
        employee.setDeptmentId(request.getDeptmentId());
        employee.setRealname(request.getRealname());
        employee.setRoleType(request.getRoleType());
        employee.setTitleLevel(request.getTitleLevel());
        employee.setPhone(request.getPhone());

        // 密码加密
        String password = request.getPassword() != null ? request.getPassword() : "123456";
        employee.setPasswordHash(DigestUtils.md5DigestAsHex(password.getBytes()));

        // delmark: true=启用, false=禁用
        employee.setDelmark(request.getEnabled() != null ? request.getEnabled() : true);

        employeeMapper.insert(employee);
        return employee.getId();
    }

    @Override
    public List<EmployeeListItemVO> listAllEmployees() {
        List<Employee> employees = employeeMapper.selectAllEnabled();
        return convertToVO(employees);
    }

    @Override
    public List<EmployeeListItemVO> listAllDoctors() {
        List<Employee> employees = employeeMapper.selectAllDoctors();
        return convertToVO(employees);
    }

    @Override
    public Employee getById(Integer id) {
        return employeeMapper.selectById(id);
    }

    private List<EmployeeListItemVO> convertToVO(List<Employee> employees) {
        List<EmployeeListItemVO> result = new ArrayList<>();
        for (Employee e : employees) {
            EmployeeListItemVO vo = new EmployeeListItemVO();
            vo.setId(e.getId());
            vo.setRealname(e.getRealname());
            vo.setRoleType(e.getRoleType());
            vo.setTitleLevel(e.getTitleLevel());
            vo.setPhone(e.getPhone());
            vo.setDeptmentId(e.getDeptmentId());
            vo.setDelmark(e.getDelmark());
            if (e.getCreateTime() != null) {
                vo.setCreateTime(e.getCreateTime().toString());
            }
            // 获取科室名称
            if (e.getDeptmentId() != null) {
                Department dept = departmentMapper.selectById(e.getDeptmentId());
                if (dept != null) {
                    vo.setDeptName(dept.getDeptName());
                }
            }
            result.add(vo);
        }
        return result;
    }
}