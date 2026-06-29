package com.neuedu.his.service;

import com.neuedu.his.model.dto.LoginRequestDTO;
import com.neuedu.his.model.vo.LoginResponseVO;

public interface AuthService {
    LoginResponseVO login(LoginRequestDTO request);
    LoginResponseVO loginByCode(LoginRequestDTO request);
    void sendCode(String phone, String codeType);
    void logout(String token);
}