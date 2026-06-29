package com.neuedu.his.controller;

import com.neuedu.his.model.dto.LoginRequestDTO;
import com.neuedu.his.model.dto.SendCodeRequestDTO;
import com.neuedu.his.model.vo.LoginResponseVO;
import com.neuedu.his.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private AuthService authService;

    @PostMapping("/login")
    public LoginResponseVO login(@RequestBody @Valid LoginRequestDTO request) {
        return authService.login(request);
    }

    @PostMapping("/login-by-code")
    public LoginResponseVO loginByCode(@RequestBody @Valid LoginRequestDTO request) {
        return authService.loginByCode(request);
    }

    @PostMapping("/send-code")
    public void sendCode(@RequestBody @Valid SendCodeRequestDTO request) {
        authService.sendCode(request);
    }

    @PostMapping("/logout")
    public void logout(@RequestHeader(value = "Authorization", required = false) String token) {
        authService.logout(token);
    }
}
