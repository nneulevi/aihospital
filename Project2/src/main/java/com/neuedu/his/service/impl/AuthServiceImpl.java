package com.neuedu.his.service.impl;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.model.dto.LoginRequestDTO;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.vo.LoginResponseVO;
import com.neuedu.his.service.AuthService;
import com.neuedu.his.service.SmsService;
import com.neuedu.his.util.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class AuthServiceImpl implements AuthService {

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private SmsService smsService;

    @Override
    public LoginResponseVO login(LoginRequestDTO request) {
        Employee employee;

        if ("PATIENT".equals(request.getLoginType())) {
            if (!"123456".equals(request.getVerifyCode())) {
                throw new BusinessException("验证码错误");
            }
            LoginResponseVO vo = new LoginResponseVO();
            vo.setToken(JwtUtil.generatePatientToken(request.getPhone()));
            return vo;
        } else {
            employee = employeeMapper.selectByLogin(request.getUsername(), request.getPassword());
            if (employee == null) {
                throw new BusinessException("用户名或密码错误");
            }

            if ("DOCTOR".equals(request.getLoginType()) && !employee.getRoleType().contains("DOCTOR")) {
                throw new BusinessException("该用户无医生权限");
            }
            if ("ADMIN".equals(request.getLoginType()) && !"ADMIN".equals(employee.getRoleType())) {
                throw new BusinessException("该用户无管理员权限");
            }

            String token = JwtUtil.generateToken(employee.getId(), employee.getRealname(), employee.getRoleType());
            LoginResponseVO vo = new LoginResponseVO();
            vo.setToken(token);
            vo.setEmployeeId(employee.getId());
            vo.setRealname(employee.getRealname());
            vo.setRoleType(employee.getRoleType());
            vo.setDeptId(employee.getDeptmentId());
            return vo;
        }
    }

    @Override
    public LoginResponseVO loginByCode(LoginRequestDTO request) {
        // 1. 校验参数
        if (request.getPhone() == null || request.getPhone().isEmpty()) {
            throw new BusinessException("手机号不能为空");
        }
        if (request.getVerifyCode() == null || request.getVerifyCode().isEmpty()) {
            throw new BusinessException("验证码不能为空");
        }

        // 2. 校验验证码（codeType 要匹配发送时的 DOCTOR_LOGIN / ADMIN_LOGIN）
        String verifyCodeType = request.getLoginType() + "_LOGIN";
        boolean valid = smsService.verifyCode(request.getPhone(), request.getVerifyCode(), verifyCodeType);
        if (!valid) {
            throw new BusinessException("验证码错误或已过期");
        }

        // 3. 根据手机号查员工
        Employee employee = employeeMapper.selectByPhone(request.getPhone());
        if (employee == null) {
            throw new BusinessException("该手机号未注册");
        }

        // 4. 校验角色权限
        if ("DOCTOR".equals(request.getLoginType()) && !employee.getRoleType().contains("DOCTOR")) {
            throw new BusinessException("该用户无医生权限");
        }
        if ("ADMIN".equals(request.getLoginType()) && !"ADMIN".equals(employee.getRoleType())) {
            throw new BusinessException("该用户无管理员权限");
        }

        // 5. 生成Token
        String token = JwtUtil.generateToken(employee.getId(), employee.getRealname(), employee.getRoleType());
        LoginResponseVO vo = new LoginResponseVO();
        vo.setToken(token);
        vo.setEmployeeId(employee.getId());
        vo.setRealname(employee.getRealname());
        vo.setRoleType(employee.getRoleType());
        vo.setDeptId(employee.getDeptmentId());
        return vo;
    }

    @Override
    public void sendCode(String phone, String codeType) {
        // 校验 codeType
        if (!"DOCTOR_LOGIN".equals(codeType) && !"ADMIN_LOGIN".equals(codeType)) {
            throw new BusinessException("验证码类型错误");
        }

        // 校验手机号是否存在于 employee 表
        Employee employee = employeeMapper.selectByPhone(phone);
        if (employee == null) {
            throw new BusinessException("该手机号未注册");
        }

        // 发送验证码（数据库版）
        smsService.sendCode(phone, codeType);
    }

    @Override
    public void logout(String token) {
        // JWT无状态，客户端清除token即可
    }
}