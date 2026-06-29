package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.SmsVerificationCodeMapper;
import com.neuedu.his.model.entity.SmsVerificationCode;
import com.neuedu.his.service.SmsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Random;

@Service
public class SmsServiceImpl implements SmsService {

    @Autowired
    private SmsVerificationCodeMapper smsCodeMapper;

    private static final int CODE_EXPIRE_MINUTES = 5;

    @Override
    public void sendCode(String phone, String codeType) {
        String code = String.format("%06d", new Random().nextInt(999999));

        SmsVerificationCode smsCode = new SmsVerificationCode();
        smsCode.setPhone(phone);
        smsCode.setCode(code);
        smsCode.setType(codeType);
        smsCode.setExpiredAt(LocalDateTime.now().plusMinutes(CODE_EXPIRE_MINUTES));
        smsCode.setUsed(false);
        smsCode.setCreatedAt(LocalDateTime.now());
        smsCodeMapper.insert(smsCode);

        System.out.println("【验证码】" + code + " 发送到 " + phone + "，类型：" + codeType);
    }

    @Override
    public boolean verifyCode(String phone, String code, String codeType) {
        SmsVerificationCode smsCode = smsCodeMapper.findLatestValidCode(phone, codeType);
        if (smsCode == null) return false;
        if (smsCode.getExpiredAt().isBefore(LocalDateTime.now())) return false;
        if (smsCode.getUsed()) return false;
        if (!smsCode.getCode().equals(code)) return false;

        smsCode.setUsed(true);
        smsCodeMapper.updateById(smsCode);
        return true;
    }
}