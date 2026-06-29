package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.PrescriptionDetail;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface PrescriptionDetailMapper {

    @Insert("INSERT INTO prescription_detail(prescription_id, drug_id, usage_route, frequency, single_dose, use_days, drug_number) " +
            "VALUES(#{prescriptionId}, #{drugId}, #{usageRoute}, #{frequency}, #{singleDose}, #{useDays}, #{drugNumber})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(PrescriptionDetail prescriptionDetail);

    @Select("SELECT * FROM prescription_detail WHERE prescription_id = #{prescriptionId}")
    List<PrescriptionDetail> selectByPrescriptionId(Integer prescriptionId);

    int batchInsert(@Param("details") List<PrescriptionDetail> details);

    @Delete("DELETE FROM prescription_detail WHERE prescription_id = #{prescriptionId}")
    int deleteByPrescriptionId(Integer prescriptionId);
}