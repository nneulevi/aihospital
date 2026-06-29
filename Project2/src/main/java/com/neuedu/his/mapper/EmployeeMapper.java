package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Employee;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface EmployeeMapper {

    @Select("SELECT * FROM employee WHERE id = #{id} AND delmark = TRUE")
    Employee selectById(Integer id);

    @Select("SELECT * FROM employee WHERE realname = #{realname} AND password_hash = #{passwordHash} AND delmark = TRUE")
    Employee selectByLogin(@Param("realname") String realname, @Param("passwordHash") String passwordHash);

    @Select("SELECT * FROM employee WHERE phone = #{phone} AND delmark = TRUE")
    Employee selectByPhone(String phone);

    // 在 EmployeeMapper 接口中添加

    @Select("SELECT * FROM employee WHERE delmark = TRUE ORDER BY realname")
    List<Employee> selectAllEnabled();

    @Select("SELECT * FROM employee WHERE delmark = TRUE AND role_type = 'DOCTOR' ORDER BY realname")
    List<Employee> selectAllDoctors();

    @Select("SELECT COUNT(*) FROM employee WHERE deptment_id = #{deptId} AND delmark = TRUE AND role_type = 'DOCTOR'")
    int countByDeptId(Integer deptId);

    @Insert("INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark, create_time, update_time) " +
            "VALUES(#{deptmentId}, #{realname}, #{roleType}, #{titleLevel}, #{passwordHash}, #{phone}, #{delmark}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Employee employee);

    List<Employee> selectByRole(@Param("roleType") String roleType, @Param("deptId") Integer deptId);

    Employee selectDetailById(Integer id);

    int updateById(Employee employee);
}