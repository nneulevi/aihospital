package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.DrugInfo;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface DrugInfoMapper {

    @Select("SELECT * FROM drug_info WHERE id = #{id}")
    DrugInfo selectById(Integer id);

    @Update("UPDATE drug_info SET stock_num = #{stockNum} WHERE id = #{id}")
    int updateStock(@Param("id") Integer id, @Param("stockNum") Integer stockNum);

    List<DrugInfo> selectByCondition(@Param("drugName") String drugName, 
                                     @Param("drugType") String drugType, 
                                     @Param("stockAlert") Integer stockAlert);

    @Select("SELECT * FROM drug_info WHERE stock_num <= #{threshold} ORDER BY stock_num ASC, drug_name ASC")
    List<DrugInfo> selectLowStock(@Param("threshold") Integer threshold);

    @Insert("INSERT INTO drug_info(drug_code, drug_name, drug_format, drug_unit, stock_num, drug_price, manufacturer, drug_type) " +
            "VALUES(#{drugCode}, #{drugName}, #{drugFormat}, #{drugUnit}, #{stockNum}, #{drugPrice}, #{manufacturer}, #{drugType})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DrugInfo drugInfo);

    @Update("UPDATE drug_info SET drug_name = #{drugName}, drug_format = #{drugFormat}, drug_unit = #{drugUnit}, " +
            "drug_price = #{drugPrice}, manufacturer = #{manufacturer}, drug_type = #{drugType} WHERE id = #{id}")
    int updateById(DrugInfo drugInfo);
}
