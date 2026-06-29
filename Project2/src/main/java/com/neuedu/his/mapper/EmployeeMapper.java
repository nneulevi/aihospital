package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Employee;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface EmployeeMapper {

    @Select("SELECT * FROM employee WHERE id = #{id} AND delmark = TRUE")
    Employee selectById(Integer id);

    @Select("SELECT * FROM employee WHERE realname = #{realname} AND password_hash = #{passwordHash} AND delmark = TRUE")
    Employee selectByLogin(@Param("realname") String realname, @Param("passwordHash") String passwordHash);

    @Select("SELECT * FROM employee WHERE phone = #{phone} AND delmark = TRUE ORDER BY id DESC LIMIT 1")
    Employee selectByPhone(String phone);

    List<Employee> selectByRole(@Param("roleType") String roleType, @Param("deptId") Integer deptId);

    Employee selectDetailById(Integer id);

    int updateById(Employee employee);
}
