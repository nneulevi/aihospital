package com.neuedu.his.service;

public interface SmsService {
    void sendCode(String phone, String codeType);
    boolean verifyCode(String phone, String code, String codeType);
}