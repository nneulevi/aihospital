package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Prescription;
import com.neuedu.his.model.vo.OrderListVO;
import com.neuedu.his.model.vo.PrescriptionDetailVO;
import com.neuedu.his.model.vo.PrescriptionListVO;
import org.apache.ibatis.annotations.*;

import java.math.BigDecimal;
import java.util.List;

@Mapper
public interface PrescriptionMapper {

    // ==================== 原有方法 ====================

    @Insert("INSERT INTO prescription(register_id, doctor_id, prescription_no, total_amount, prescription_status) " +
            "VALUES(#{registerId}, #{doctorId}, #{prescriptionNo}, #{totalAmount}, #{prescriptionStatus})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Prescription prescription);

    @Select("SELECT * FROM prescription WHERE id = #{id}")
    Prescription selectById(Integer id);

    // 由 XML 实现
    List<Prescription> selectByRegisterId(Integer registerId);

    // 由 XML 实现
    int updateStatusAndAmount(@Param("id") Integer id,
                              @Param("prescriptionStatus") String prescriptionStatus,
                              @Param("totalAmount") BigDecimal totalAmount);

    // 由 XML 实现
    int dispense(@Param("id") Integer id, @Param("pharmacistId") Integer pharmacistId);

    @Select("SELECT * FROM prescription WHERE register_id = #{registerId} AND prescription_status IN ('DISPENSED', 'PAID')")
    List<Prescription> selectRefundableByRegisterId(Integer registerId);

    // ==================== 新增方法 ====================

    /**
     * 查询处方列表 - 由 XML 实现
     */
    List<PrescriptionListVO> selectPrescriptionList(@Param("patientId") Integer patientId,
                                                    @Param("status") String status,
                                                    @Param("offset") Integer offset,
                                                    @Param("limit") Integer limit);

    /**
     * 统计处方总数 - 由 XML 实现
     */
    Long countPrescriptionList(@Param("patientId") Integer patientId,
                               @Param("status") String status);

    /**
     * 查询处方详情
     */
    @Select("SELECT p.id AS id, p.prescription_no AS prescriptionNo, " +
            "d.dept_name AS deptName, e.realname AS doctorName, " +
            "pat.real_name AS patientName, p.prescription_status AS status, " +
            "p.total_amount AS totalAmount, p.creation_time AS creationTime " +
            "FROM prescription p " +
            "LEFT JOIN register r ON p.register_id = r.id " +
            "LEFT JOIN department d ON r.deptment_id = d.id " +
            "LEFT JOIN employee e ON p.doctor_id = e.id " +
            "LEFT JOIN patient pat ON r.patient_id = pat.id " +
            "WHERE p.id = #{id}")
    PrescriptionDetailVO selectPrescriptionDetail(@Param("id") Integer id);

    /**
     * 查询药费订单 - 由 XML 实现
     */
    List<OrderListVO> selectDrugOrders(@Param("patientId") Integer patientId,
                                       @Param("orderState") String orderState,
                                       @Param("offset") Integer offset,
                                       @Param("limit") Integer limit);
}