package com.neuedu.his.service.impl;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.PatientMapper;
import com.neuedu.his.model.dto.PatientAuthRegisterRequestDTO;
import com.neuedu.his.model.entity.Patient;
import com.neuedu.his.model.vo.PatientListVO;
import com.neuedu.his.model.vo.PatientLoginResponseVO;
import com.neuedu.his.service.PatientAuthService;
import com.neuedu.his.service.SmsService;
import com.neuedu.his.util.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class PatientAuthServiceImpl implements PatientAuthService {

    @Autowired
    private PatientMapper patientMapper;

    @Autowired
    private SmsService smsService;

    @Autowired
    private JwtUtil jwtUtil;

    @Override
    public void sendCode(String phone, String codeType) {
        smsService.sendCode(phone, codeType);
    }

    @Override
    @Transactional
    public PatientLoginResponseVO register(PatientAuthRegisterRequestDTO request) {
        // 1. 验证验证码
        boolean valid = smsService.verifyCode(request.getPhone(), request.getCode(), "REGISTER");
        if (!valid) {
            throw new BusinessException("验证码错误或已过期");
        }

        // 2. 检查身份证是否已存在
        Patient existingPatient = patientMapper.findByCardNumber(request.getCardNumber());
        if (existingPatient != null) {
            if (!existingPatient.getPhone().equals(request.getPhone())) {
                throw new BusinessException("该身份证已绑定其他手机号");
            }
            return loginExistingPatient(existingPatient);
        }

        // 3. 检查手机号是否已被使用
        Patient phonePatient = patientMapper.findByPhone(request.getPhone());
        if (phonePatient != null) {
            throw new BusinessException("该手机号已被其他患者使用");
        }

        // 4. 创建新患者
        Patient newPatient = new Patient();
        newPatient.setRealName(request.getRealName());
        newPatient.setCardNumber(request.getCardNumber());
        newPatient.setPhone(request.getPhone());
        newPatient.setGender(request.getGender());
        // birthdate 是 String，需要解析
        if (request.getBirthdate() != null && !request.getBirthdate().isEmpty()) {
            newPatient.setBirthdate(LocalDate.parse(request.getBirthdate()));
        }
        newPatient.setHomeAddress(request.getHomeAddress());
        newPatient.setPhoneVerified(true);
        newPatient.setLastLoginTime(LocalDateTime.now());
        newPatient.setCaseNumber(generateCaseNumber());

        patientMapper.insert(newPatient);

        // 5. 生成Token
        String token = jwtUtil.generateToken(newPatient.getId(), "PATIENT");

        PatientLoginResponseVO response = new PatientLoginResponseVO();
        response.setToken(token);
        response.setPatientId(newPatient.getId());
        response.setCaseNumber(newPatient.getCaseNumber());
        response.setRealName(newPatient.getRealName());
        response.setIsNewPatient(true);
        return response;
    }

    @Override
    public List<PatientListVO> getPatientList(Integer currentPatientId) {
        Patient currentPatient = patientMapper.selectById(currentPatientId);
        if (currentPatient == null) {
            throw new BusinessException("患者不存在");
        }

        List<Patient> patients = patientMapper.findPatientsByPhone(currentPatient.getPhone());
        return patients.stream().map(p -> {
            PatientListVO vo = new PatientListVO();
            vo.setId(p.getId());
            vo.setCaseNumber(p.getCaseNumber());
            vo.setRealName(p.getRealName());
            vo.setGender(p.getGender());
            vo.setPhone(p.getPhone());
            vo.setIsDefault(p.getId().equals(currentPatientId));
            return vo;
        }).collect(Collectors.toList());
    }

    @Override
    public String switchPatient(Integer patientId, Integer currentPatientId) {
        Patient targetPatient = patientMapper.selectById(patientId);
        if (targetPatient == null) {
            throw new BusinessException("就诊人不存在");
        }

        Patient currentPatient = patientMapper.selectById(currentPatientId);
        if (!currentPatient.getPhone().equals(targetPatient.getPhone())) {
            throw new BusinessException("无权切换该就诊人");
        }

        return jwtUtil.generateToken(patientId, "PATIENT");
    }

    @Override
    public void logout(String token) {
        // 前端清除Token即可
    }

    private PatientLoginResponseVO loginExistingPatient(Patient patient) {
        patient.setLastLoginTime(LocalDateTime.now());
        patientMapper.updateById(patient);

        String token = jwtUtil.generateToken(patient.getId(), "PATIENT");

        PatientLoginResponseVO response = new PatientLoginResponseVO();
        response.setToken(token);
        response.setPatientId(patient.getId());
        response.setCaseNumber(patient.getCaseNumber());
        response.setRealName(patient.getRealName());
        response.setIsNewPatient(false);
        return response;
    }

    private String generateCaseNumber() {
        String dateStr = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String maxNumber = patientMapper.findMaxCaseNumberByDate(dateStr);
        int seq = 1;
        if (maxNumber != null && maxNumber.length() >= 12) {
            String seqStr = maxNumber.substring(10);
            seq = Integer.parseInt(seqStr) + 1;
        }
        return "HN" + dateStr + String.format("%04d", seq);
    }
}