package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Employee;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Insert;
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

    @Select("SELECT * FROM employee WHERE delmark = TRUE ORDER BY role_type, realname")
    List<Employee> selectAllActive();

    List<Employee> selectByRole(@Param("roleType") String roleType, @Param("deptId") Integer deptId);

    Employee selectDetailById(Integer id);

    int updateById(Employee employee);

    @Insert("""
            INSERT INTO employee(deptment_id, regist_level_id, realname, role_type, title_level, password_hash, phone, delmark)
            VALUES(#{deptmentId}, #{registLevelId}, #{realname}, #{roleType}, #{titleLevel}, #{passwordHash}, #{phone}, TRUE)
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Employee employee);
}
