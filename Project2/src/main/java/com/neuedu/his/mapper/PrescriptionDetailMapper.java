package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.PrescriptionDetail;
import com.neuedu.his.model.vo.PrescriptionDetailVO;
import com.neuedu.his.model.vo.PrescriptionListVO;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface PrescriptionDetailMapper {

    // ==================== 原有方法 ====================

    @Insert("INSERT INTO prescription_detail(prescription_id, drug_id, usage_route, frequency, single_dose, use_days, drug_number) " +
            "VALUES(#{prescriptionId}, #{drugId}, #{usageRoute}, #{frequency}, #{singleDose}, #{useDays}, #{drugNumber})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(PrescriptionDetail prescriptionDetail);

    @Select("SELECT * FROM prescription_detail WHERE prescription_id = #{prescriptionId}")
    List<PrescriptionDetail> selectByPrescriptionId(Integer prescriptionId);

    // 删除 @Insert 注解，让 XML 中的配置生效
    int batchInsert(@Param("details") List<PrescriptionDetail> details);

    @Delete("DELETE FROM prescription_detail WHERE prescription_id = #{prescriptionId}")
    int deleteByPrescriptionId(Integer prescriptionId);

    // ==================== 新增方法 ====================

    /**
     * 查询处方的药品摘要（仅药品名称）
     */
    @Select("SELECT pd.drug_id AS drugId, di.drug_name AS drugName " +
            "FROM prescription_detail pd LEFT JOIN drug_info di ON pd.drug_id = di.id " +
            "WHERE pd.prescription_id = #{prescriptionId}")
    List<PrescriptionListVO.PrescriptionDrugSummaryVO> selectDrugSummaryByPrescriptionId(
            @Param("prescriptionId") Integer prescriptionId);

    /**
     * 查询处方的药品详情（完整字段）
     */
    @Select("SELECT pd.drug_id AS drugId, di.drug_name AS drugName, " +
            "di.drug_format AS specification, pd.single_dose AS dosage, " +
            "pd.frequency AS frequency, pd.use_days AS days, " +
            "pd.drug_number AS quantity, di.drug_price AS price " +
            "FROM prescription_detail pd LEFT JOIN drug_info di ON pd.drug_id = di.id " +
            "WHERE pd.prescription_id = #{prescriptionId}")
    List<PrescriptionDetailVO.PrescriptionDrugDetailVO> selectDrugDetailByPrescriptionId(
            @Param("prescriptionId") Integer prescriptionId);
}