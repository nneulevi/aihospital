package com.neuedu.his.service.impl;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.mapper.PatientMapper;
import com.neuedu.his.model.dto.LoginRequestDTO;
import com.neuedu.his.model.dto.PatientAuthRegisterRequestDTO;
import com.neuedu.his.model.dto.SendCodeRequestDTO;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.entity.Patient;
import com.neuedu.his.model.vo.LoginResponseVO;
import com.neuedu.his.service.AuthService;
import com.neuedu.his.util.JwtUtil;
import com.neuedu.his.util.SnowflakeIdUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthServiceImpl implements AuthService {

    private static final String DEMO_VERIFY_CODE = "123456";

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private PatientMapper patientMapper;

    @Override
    public LoginResponseVO login(LoginRequestDTO request) {
        if ("PATIENT".equals(request.getLoginType())) {
            return loginPatient(request);
        }

        Employee employee = employeeMapper.selectByLogin(request.getUsername(), request.getPassword());
        return buildEmployeeLoginResponse(employee, request.getLoginType());
    }

    @Override
    public LoginResponseVO loginByCode(LoginRequestDTO request) {
        validateCode(request.getVerifyCode());

        if ("PATIENT".equals(request.getLoginType())) {
            Patient patient = patientMapper.selectByPhone(request.getPhone());
            return buildPatientLoginResponse(patient, request.getPhone(), false);
        }

        Employee employee = employeeMapper.selectByPhone(request.getPhone());
        return buildEmployeeLoginResponse(employee, request.getLoginType());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public LoginResponseVO patientAuthRegister(PatientAuthRegisterRequestDTO request) {
        validateCode(request.getCode());

        Patient patient = patientMapper.selectByCardNumber(request.getCardNumber());
        boolean isNewPatient = false;
        if (patient == null) {
            patient = new Patient();
            patient.setCaseNumber(String.valueOf(SnowflakeIdUtil.nextId()));
            patient.setRealName(request.getRealName());
            patient.setGender(request.getGender());
            patient.setCardNumber(request.getCardNumber());
            patient.setBirthdate(request.getBirthdate());
            patient.setPhone(request.getPhone());
            patient.setHomeAddress(request.getHomeAddress());
            patientMapper.insert(patient);
            isNewPatient = true;
        } else {
            patient.setRealName(request.getRealName());
            patient.setPhone(request.getPhone());
            if (request.getGender() != null) patient.setGender(request.getGender());
            if (request.getBirthdate() != null) patient.setBirthdate(request.getBirthdate());
            if (request.getHomeAddress() != null) patient.setHomeAddress(request.getHomeAddress());
            patientMapper.updateById(patient);
        }

        return buildPatientLoginResponse(patient, request.getPhone(), isNewPatient);
    }

    @Override
    public void sendCode(SendCodeRequestDTO request) {
        // Demo mode: the accepted verification code is 123456.
    }

    @Override
    public void logout(String token) {
        // JWT is stateless; clients clear the token locally.
    }

    private LoginResponseVO loginPatient(LoginRequestDTO request) {
        if (request.getVerifyCode() != null && !request.getVerifyCode().isBlank()) {
            validateCode(request.getVerifyCode());
            Patient patient = patientMapper.selectByPhone(request.getPhone());
            return buildPatientLoginResponse(requirePatient(patient), request.getPhone(), false);
        }

        if (!DEMO_VERIFY_CODE.equals(request.getPassword())) {
            throw new BusinessException("username or password is invalid");
        }

        String account = request.getUsername();
        Patient patient = null;
        if (account != null && account.matches("^1[3-9]\\d{9}$")) {
            patient = patientMapper.selectByPhone(account);
        }
        if (patient == null && account != null && !account.isBlank()) {
            patient = patientMapper.selectByCaseNumber(account);
        }
        return buildPatientLoginResponse(requirePatient(patient), patient.getPhone(), false);
    }

    private Patient requirePatient(Patient patient) {
        if (patient == null) {
            throw new BusinessException("patient does not exist");
        }
        return patient;
    }

    private void validateCode(String code) {
        if (!DEMO_VERIFY_CODE.equals(code)) {
            throw new BusinessException("verification code is invalid");
        }
    }

    private LoginResponseVO buildEmployeeLoginResponse(Employee employee, String loginType) {
        if (employee == null) {
            throw new BusinessException("username or password is invalid");
        }
        String expectedRole = loginType == null ? "" : loginType.trim();
        String actualRole = employee.getRoleType() == null ? "" : employee.getRoleType().trim();
        if (!expectedRole.equals(actualRole)) {
            throw new BusinessException("employee has no " + expectedRole + " permission");
        }

        LoginResponseVO vo = new LoginResponseVO();
        vo.setToken(JwtUtil.generateToken(employee.getId(), employee.getRealname(), employee.getRoleType()));
        vo.setEmployeeId(employee.getId());
        vo.setRealname(employee.getRealname());
        vo.setRoleType(employee.getRoleType());
        vo.setDeptId(employee.getDeptmentId());
        return vo;
    }

    private LoginResponseVO buildPatientLoginResponse(Patient patient, String phone, boolean isNewPatient) {
        LoginResponseVO vo = new LoginResponseVO();
        vo.setRoleType("PATIENT");
        vo.setPhone(phone);
        vo.setIsNewPatient(isNewPatient);

        if (patient != null) {
            vo.setPatientId(patient.getId());
            vo.setRealName(patient.getRealName());
            vo.setCaseNumber(patient.getCaseNumber());
            vo.setToken(JwtUtil.generatePatientToken(patient.getId(), patient.getPhone(), patient.getCaseNumber()));
        } else {
            vo.setToken(JwtUtil.generatePatientToken(phone));
        }
        return vo;
    }
}
