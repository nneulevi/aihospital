package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.InspectionRequest;
import com.neuedu.his.model.vo.OrderListVO;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface InspectionRequestMapper {

    // ==================== 原有方法 ====================

    @Insert("INSERT INTO inspection_request(register_id, medical_technology_id, inspection_info, inspection_position, creation_time, inspection_state) " +
            "VALUES(#{registerId}, #{medicalTechnologyId}, #{inspectionInfo}, #{inspectionPosition}, NOW(), 'CREATED')")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(InspectionRequest inspectionRequest);

    @Select("SELECT * FROM inspection_request WHERE id = #{id}")
    InspectionRequest selectById(Integer id);

    // 由 XML 实现
    List<InspectionRequest> selectByRegisterId(Integer registerId);

    // 由 XML 实现
    int updateResult(@Param("id") Integer id,
                     @Param("inspectionResult") String inspectionResult,
                     @Param("inspectionEmployeeId") Integer inspectionEmployeeId);

    // 由 XML 实现
    int updateState(@Param("id") Integer id, @Param("inspectionState") String inspectionState);

    // ==================== 新增方法 ====================

    /**
     * 查询检验费订单 - 由 XML 实现
     */
    List<OrderListVO> selectInspectionOrders(@Param("patientId") Integer patientId,
                                             @Param("orderState") String orderState,
                                             @Param("offset") Integer offset,
                                             @Param("limit") Integer limit);

    /**
     * 查询患者待预约的检验列表（医生开单、未预约、状态CREATED）- 由 XML 实现
     */
    List<com.neuedu.his.model.vo.PendingInspectionRequestVO> selectPendingInspectionRequests(@Param("patientId") Integer patientId);

    /**
     * 患者预约检验（更新预约时间和状态）- 由 XML 实现
     */
    int bookInspectionRequest(@Param("id") Integer id,
                              @Param("bookedTime") java.time.LocalDateTime bookedTime);
}