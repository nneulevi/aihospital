package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Patient;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface PatientMapper {

    // ==================== 原有方法 ====================

    @Insert("INSERT INTO patient(case_number, real_name, gender, card_number, birthdate, phone, home_address) " +
            "VALUES(#{caseNumber}, #{realName}, #{gender}, #{cardNumber}, #{birthdate}, #{phone}, #{homeAddress})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Patient patient);

    @Select("SELECT * FROM patient WHERE id = #{id}")
    Patient selectById(Integer id);

    @Select("SELECT * FROM patient WHERE case_number = #{caseNumber}")
    Patient selectByCaseNumber(String caseNumber);

    @Select("SELECT * FROM patient WHERE card_number = #{cardNumber}")
    Patient selectByCardNumber(String cardNumber);

    @Select("SELECT * FROM patient WHERE phone = #{phone}")
    Patient selectByPhone(String phone);

    // 删除 @Update 注解，让 XML 中的配置生效
    int updateById(Patient patient);

    // ==================== 新增方法 ====================

    @Select("SELECT * FROM patient WHERE card_number = #{cardNumber}")
    Patient findByCardNumber(String cardNumber);

    @Select("SELECT * FROM patient WHERE phone = #{phone}")
    Patient findByPhone(String phone);

    @Select("SELECT * FROM patient WHERE phone = #{phone} ORDER BY id")
    List<Patient> findPatientsByPhone(String phone);

    @Select("SELECT case_number FROM patient WHERE case_number LIKE CONCAT('HN', #{dateStr}, '%') ORDER BY case_number DESC LIMIT 1")
    String findMaxCaseNumberByDate(String dateStr);

    @Update("UPDATE patient SET phone_verified = TRUE WHERE id = #{id}")
    int verifyPhone(Integer id);

    /**
     * 查询就诊人列表（通过主账号ID）
     * 注意：如果 patient 表没有 master_patient_id 字段，请改为只查自身
     */
    @Select("SELECT * FROM patient WHERE id = #{masterId}")
    List<Patient> selectByMasterId(@Param("masterId") Integer masterId);
}