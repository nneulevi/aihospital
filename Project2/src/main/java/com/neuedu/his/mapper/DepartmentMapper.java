package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Department;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface DepartmentMapper {

    @Select("SELECT * FROM department WHERE id = #{id}")
    Department selectById(Integer id);

    @Select("SELECT * FROM department WHERE delmark = TRUE")
    List<Department> selectAll();

    @Select("SELECT * FROM department WHERE dept_type = #{deptType} AND delmark = TRUE")
    List<Department> selectByType(String deptType);
}
