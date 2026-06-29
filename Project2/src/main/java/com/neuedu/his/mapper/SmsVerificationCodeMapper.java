package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.SmsVerificationCode;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface SmsVerificationCodeMapper {
    void insert(SmsVerificationCode smsCode);

    void updateById(SmsVerificationCode smsCode);

    SmsVerificationCode findLatestValidCode(
            @Param("phone") String phone,
            @Param("type") String codeType
    );
}