package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Patient;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface PatientMapper {

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

    @Select("SELECT * FROM patient WHERE phone = #{phone} ORDER BY id DESC LIMIT 1")
    Patient selectByPhone(String phone);

    @Select("SELECT * FROM patient ORDER BY id DESC LIMIT 100")
    List<Patient> selectAll();

    int updateById(Patient patient);
}
