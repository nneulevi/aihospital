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

    @Select("""
            SELECT p.*
            FROM prescription p
            JOIN register r ON p.register_id = r.id
             JOIN patient pa ON r.patient_id = pa.id
             LEFT JOIN employee doc ON p.doctor_id = doc.id
            WHERE p.prescription_status = #{status}
              AND NOT EXISTS (
                  SELECT 1
                  FROM prescription_detail pd
                           JOIN drug_info d ON pd.drug_id = d.id
                  WHERE pd.prescription_id = p.id
                    AND (
                        COALESCE(d.drug_name, '') LIKE 'Extended%'
                        OR COALESCE(d.drug_name, '') LIKE 'User Logic%'
                        OR COALESCE(d.drug_name, '') LIKE '%E2E%'
                        OR COALESCE(d.drug_name, '') LIKE '%项目验收%'
                        OR COALESCE(d.drug_name, '') LIKE '%验收%'
                        OR COALESCE(d.drug_name, '') LIKE '%测试%'
                        OR COALESCE(d.drug_name, '') LIKE '业务联动%'
                        OR COALESCE(d.drug_code, '') LIKE 'EXT-%'
                        OR COALESCE(d.drug_code, '') LIKE 'ULA-%'
                        OR COALESCE(d.drug_code, '') LIKE 'BIZFLOW-%'
                        OR COALESCE(d.manufacturer, '') LIKE '%E2E%'
                        OR COALESCE(d.manufacturer, '') LIKE '%User Logic%'
                        OR COALESCE(d.manufacturer, '') LIKE '%Extended%'
                        OR COALESCE(d.manufacturer, '') LIKE '%项目验收%'
                        OR COALESCE(d.manufacturer, '') LIKE '%验收%'
                        OR COALESCE(d.manufacturer, '') LIKE '%测试%'
                        OR COALESCE(d.manufacturer, '') LIKE '业务联动%'
                    )
              )
              AND COALESCE(pa.real_name, '') NOT LIKE '%E2E%'
              AND COALESCE(pa.real_name, '') NOT LIKE '%User Logic%'
              AND COALESCE(pa.real_name, '') NOT LIKE '%Extended%'
              AND COALESCE(pa.real_name, '') NOT LIKE '%项目验收%'
              AND COALESCE(pa.real_name, '') NOT LIKE '%验收%'
              AND COALESCE(pa.real_name, '') NOT LIKE '%测试%'
              AND COALESCE(pa.home_address, '') NOT LIKE '%E2E%'
              AND COALESCE(pa.home_address, '') NOT LIKE '%User Logic%'
              AND COALESCE(pa.home_address, '') NOT LIKE '%Extended%'
              AND COALESCE(pa.home_address, '') NOT LIKE '%项目验收%'
              AND COALESCE(pa.home_address, '') NOT LIKE '%验收%'
              AND COALESCE(pa.home_address, '') NOT LIKE '%测试%'
              AND COALESCE(doc.realname, '') NOT LIKE '%E2E%'
              AND COALESCE(doc.realname, '') NOT LIKE '%User Logic%'
              AND COALESCE(doc.realname, '') NOT LIKE '%Extended%'
              AND COALESCE(doc.realname, '') NOT LIKE '%项目验收%'
              AND COALESCE(doc.realname, '') NOT LIKE '%验收%'
              AND COALESCE(doc.realname, '') NOT LIKE '%测试%'
            ORDER BY p.creation_time DESC, p.id DESC
            """)
    List<Prescription> selectByStatus(String status);

    List<Prescription> selectByRegisterId(Integer registerId);

    int updateStatusAndAmount(@Param("id") Integer id,
                              @Param("prescriptionStatus") String prescriptionStatus,
                              @Param("totalAmount") BigDecimal totalAmount);

    int dispense(@Param("id") Integer id, @Param("pharmacistId") Integer pharmacistId);

    @Select("SELECT * FROM prescription WHERE register_id = #{registerId} AND prescription_status IN ('DISPENSED', 'PAID')")
    List<Prescription> selectRefundableByRegisterId(Integer registerId);
}
