package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Prescription;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.math.BigDecimal;
import java.util.List;

@Mapper
public interface PrescriptionMapper {

    @Insert("INSERT INTO prescription(register_id, doctor_id, prescription_no, total_amount, prescription_status) " +
            "VALUES(#{registerId}, #{doctorId}, #{prescriptionNo}, #{totalAmount}, #{prescriptionStatus})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Prescription prescription);

    @Select("SELECT * FROM prescription WHERE id = #{id}")
    Prescription selectById(Integer id);

    List<Prescription> selectByRegisterId(Integer registerId);

    int updateStatusAndAmount(@Param("id") Integer id,
                              @Param("prescriptionStatus") String prescriptionStatus,
                              @Param("totalAmount") BigDecimal totalAmount);

    int dispense(@Param("id") Integer id, @Param("pharmacistId") Integer pharmacistId);

    @Select("SELECT * FROM prescription WHERE register_id = #{registerId} AND prescription_status IN ('DISPENSED', 'PAID')")
    List<Prescription> selectRefundableByRegisterId(Integer registerId);
}