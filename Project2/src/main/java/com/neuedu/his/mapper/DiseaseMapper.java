package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Disease;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface DiseaseMapper {

    @Select("SELECT * FROM disease WHERE id = #{id}")
    Disease selectById(Integer id);

    @Select("SELECT * FROM disease WHERE disease_name LIKE CONCAT('%', #{diseaseName}, '%')")
    List<Disease> selectByName(String diseaseName);

    @Select("SELECT * FROM disease WHERE disease_code = #{diseaseCode}")
    Disease selectByCode(String diseaseCode);

    @Insert("INSERT INTO disease(disease_code, disease_name, disease_type, icd_code) " +
            "VALUES(#{diseaseCode}, #{diseaseName}, #{diseaseType}, #{icdCode})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Disease disease);

    @Update("UPDATE disease SET disease_name = #{diseaseName}, disease_type = #{diseaseType}, icd_code = #{icdCode} WHERE id = #{id}")
    int updateById(Disease disease);
}