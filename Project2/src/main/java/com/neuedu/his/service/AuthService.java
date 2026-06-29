package com.neuedu.his.service;

import com.neuedu.his.model.dto.LoginRequestDTO;
import com.neuedu.his.model.dto.PatientAuthRegisterRequestDTO;
import com.neuedu.his.model.dto.SendCodeRequestDTO;
import com.neuedu.his.model.vo.LoginResponseVO;

public interface AuthService {
    LoginResponseVO login(LoginRequestDTO request);
    LoginResponseVO loginByCode(LoginRequestDTO request);
    LoginResponseVO patientAuthRegister(PatientAuthRegisterRequestDTO request);
    void sendCode(SendCodeRequestDTO request);
    void logout(String token);
}
