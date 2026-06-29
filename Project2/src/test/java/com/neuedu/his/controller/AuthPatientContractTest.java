package com.neuedu.his.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.neuedu.his.model.dto.LoginRequestDTO;
import com.neuedu.his.model.vo.LoginResponseVO;
import com.neuedu.his.service.AuthService;
import com.neuedu.his.service.PatientService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Map;

import static org.mockito.Mockito.mock;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class AuthPatientContractTest {

    private MockMvc mockMvc;

    private final ObjectMapper objectMapper = new ObjectMapper();

    private AuthService authService;

    private PatientService patientService;

    @BeforeEach
    void setUp() {
        authService = mock(AuthService.class);
        patientService = mock(PatientService.class);

        AuthController authController = new AuthController();
        PatientController patientController = new PatientController();
        inject(authController, "authService", authService);
        inject(patientController, "patientService", patientService);

        mockMvc = MockMvcBuilders.standaloneSetup(authController, patientController).build();
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

    @Test
    void authLoginByCodeReturnsJwtToken() throws Exception {
        LoginResponseVO response = new LoginResponseVO();
        response.setToken("jwt-token");
        response.setRoleType("DOCTOR");
        when(authService.loginByCode(any(LoginRequestDTO.class))).thenReturn(response);

        mockMvc.perform(post("/api/auth/login-by-code")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of(
                                "phone", "13800000000",
                                "verifyCode", "123456",
                                "loginType", "DOCTOR"
                        ))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("jwt-token"))
                .andExpect(jsonPath("$.roleType").value("DOCTOR"));
    }

    @Test
    void authSendCodeEndpointExists() throws Exception {
        mockMvc.perform(post("/api/auth/send-code")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of(
                                "phone", "13800000000",
                                "codeType", "DOCTOR_LOGIN"
                        ))))
                .andExpect(status().isOk());
    }

    @Test
    void patientSendCodeEndpointExists() throws Exception {
        mockMvc.perform(post("/api/patient/send-code")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of(
                                "phone", "13800000000",
                                "codeType", "REGISTER"
                        ))))
                .andExpect(status().isOk());
    }

    @Test
    void patientAuthRegisterReturnsJwtToken() throws Exception {
        LoginResponseVO response = new LoginResponseVO();
        response.setToken("patient-jwt-token");
        response.setRoleType("PATIENT");
        when(patientService.authRegister(any())).thenReturn(response);

        mockMvc.perform(post("/api/patient/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of(
                                "realName", "Test Patient",
                                "cardNumber", "110101199001011234",
                                "phone", "13800000000",
                                "code", "123456"
                        ))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("patient-jwt-token"))
                .andExpect(jsonPath("$.roleType").value("PATIENT"));
    }

    @Test
    void patientLogoutSwitchAndListEndpointsExist() throws Exception {
        mockMvc.perform(post("/api/patient/logout"))
                .andExpect(status().isOk());

        mockMvc.perform(post("/api/patient/switch")
                        .param("patientId", "1"))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/patient/list"))
                .andExpect(status().isOk());
    }
}
