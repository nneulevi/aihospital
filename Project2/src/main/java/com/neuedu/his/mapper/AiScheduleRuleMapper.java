package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.AiScheduleRule;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface AiScheduleRuleMapper {

    @Insert("INSERT INTO ai_schedule_rule(rule_name, deptment_id, rule_config, constraint_json, is_active, ai_model_version) " +
            "VALUES(#{ruleName}, #{deptmentId}, #{ruleConfig}, #{constraintJson}, #{isActive}, #{aiModelVersion})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AiScheduleRule aiScheduleRule);

    @Select("SELECT * FROM ai_schedule_rule WHERE id = #{id}")
    AiScheduleRule selectById(Integer id);

    @Select("SELECT * FROM ai_schedule_rule WHERE deptment_id = #{deptId} AND is_active = TRUE")
    List<AiScheduleRule> selectActiveByDept(Integer deptId);

    @Update("UPDATE ai_schedule_rule SET rule_name = #{ruleName}, rule_config = #{ruleConfig}, " +
            "constraint_json = #{constraintJson}, is_active = #{isActive} WHERE id = #{id}")
    int updateById(AiScheduleRule aiScheduleRule);
}
