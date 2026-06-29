package com.neuedu.his.service;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.mapper.PatientMapper;
import com.neuedu.his.model.dto.LoginRequestDTO;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.entity.Patient;
import com.neuedu.his.model.vo.LoginResponseVO;
import com.neuedu.his.service.impl.AuthServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class AuthServiceImplBehaviorTest {

    private AuthServiceImpl authService;
    private EmployeeMapper employeeMapper;
    private PatientMapper patientMapper;

    @BeforeEach
    void setUp() {
        authService = new AuthServiceImpl();
        employeeMapper = mock(EmployeeMapper.class);
        patientMapper = mock(PatientMapper.class);
        inject(authService, "employeeMapper", employeeMapper);
        inject(authService, "patientMapper", patientMapper);
    }

    @Test
    void patientPasswordLoginUsesPhoneAndDemoPassword() {
        Patient patient = new Patient();
        patient.setId(20);
        patient.setRealName("测试患者");
        patient.setPhone("13800001111");
        patient.setCaseNumber("CASE-20");
        when(patientMapper.selectByPhone("13800001111")).thenReturn(patient);

        LoginRequestDTO request = new LoginRequestDTO();
        request.setLoginType("PATIENT");
        request.setUsername("13800001111");
        request.setPassword("123456");

        LoginResponseVO response = authService.login(request);

        assertEquals("PATIENT", response.getRoleType());
        assertEquals(20, response.getPatientId());
        assertNotNull(response.getToken());
    }

    @Test
    void patientPasswordLoginRejectsWrongDemoPassword() {
        LoginRequestDTO request = new LoginRequestDTO();
        request.setLoginType("PATIENT");
        request.setUsername("13800001111");
        request.setPassword("wrongpass");

        assertThrows(BusinessException.class, () -> authService.login(request));
    }

    @Test
    void employeeCodeLoginReturnsJwt() {
        Employee employee = new Employee();
        employee.setId(15);
        employee.setRealname("doctor");
        employee.setRoleType("DOCTOR");
        when(employeeMapper.selectByPhone("13900000001")).thenReturn(employee);

        LoginRequestDTO request = new LoginRequestDTO();
        request.setLoginType("DOCTOR");
        request.setPhone("13900000001");
        request.setVerifyCode("123456");

        LoginResponseVO response = authService.loginByCode(request);

        assertEquals("DOCTOR", response.getRoleType());
        assertEquals(15, response.getEmployeeId());
        assertNotNull(response.getToken());
    }

    @Test
    void employeePasswordLoginRejectsMismatchedStaffRole() {
        Employee employee = new Employee();
        employee.setId(16);
        employee.setRealname("doctor");
        employee.setRoleType("DOCTOR");
        when(employeeMapper.selectByLogin("doctor", "123456")).thenReturn(employee);

        LoginRequestDTO request = new LoginRequestDTO();
        request.setLoginType("PHARMACIST");
        request.setUsername("doctor");
        request.setPassword("123456");

        assertThrows(BusinessException.class, () -> authService.login(request));
    }

    private void inject(Object target, String fieldName, Object value) {
        try {
            java.lang.reflect.Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
    }
}
