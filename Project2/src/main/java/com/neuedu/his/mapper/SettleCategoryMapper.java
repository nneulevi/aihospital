package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.SettleCategory;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface SettleCategoryMapper {

    @Select("SELECT * FROM settle_category WHERE id = #{id}")
    SettleCategory selectById(Integer id);

    @Select("SELECT * FROM settle_category WHERE delmark = 1 ORDER BY sequence_no")
    List<SettleCategory> selectAll();
}