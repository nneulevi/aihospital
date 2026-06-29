package com.neuedu.his.controller;

import com.neuedu.his.model.dto.PatientAuthRegisterRequestDTO;
import com.neuedu.his.model.dto.SendCodeRequestDTO;
import com.neuedu.his.model.vo.PatientListVO;
import com.neuedu.his.model.vo.PatientLoginResponseVO;
import com.neuedu.his.service.PatientAuthService;
import com.neuedu.his.util.JwtUtil;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/patient")
public class PatientAuthController {

    @Autowired
    private PatientAuthService patientAuthService;

    @Autowired
    private JwtUtil jwtUtil;

    /**
     * 发送验证码
     */
    @PostMapping("/send-code")
    public void sendCode(@RequestBody @Valid SendCodeRequestDTO request) {
        patientAuthService.sendCode(request.getPhone(), request.getCodeType());
    }

    /**
     * 添加就诊人（注册 + 自动登录）
     * 路径改成 /auth/register，避免和挂号接口冲突
     */
    @PostMapping("/auth/register")  // ← 改这里！
    public PatientLoginResponseVO register(@RequestBody @Valid PatientAuthRegisterRequestDTO request) {
        return patientAuthService.register(request);
    }

    /**
     * 获取就诊人列表
     */
    @GetMapping("/list")
    public List<PatientListVO> list(@RequestHeader("Authorization") String token) {
        Integer patientId = jwtUtil.getUserIdFromToken(token.replace("Bearer ", ""));
        return patientAuthService.getPatientList(patientId);
    }

    /**
     * 切换就诊人
     */
    @PostMapping("/switch")
    public String switchPatient(
            @RequestHeader("Authorization") String token,
            @RequestParam Integer patientId) {
        Integer currentPatientId = jwtUtil.getUserIdFromToken(token.replace("Bearer ", ""));
        return patientAuthService.switchPatient(patientId, currentPatientId);
    }

    /**
     * 退出登录
     */
    @PostMapping("/logout")
    public void logout(@RequestHeader("Authorization") String token) {
        patientAuthService.logout(token);
    }
}