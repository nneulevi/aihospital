package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.RegistLevel;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface RegistLevelMapper {

    @Select("SELECT * FROM regist_level WHERE id = #{id}")
    RegistLevel selectById(Integer id);

    @Select("SELECT * FROM regist_level WHERE delmark = TRUE ORDER BY sequence_no")
    List<RegistLevel> selectAll();
}
