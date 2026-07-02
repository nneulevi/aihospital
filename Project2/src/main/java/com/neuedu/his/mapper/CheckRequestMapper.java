package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.CheckRequest;
import com.neuedu.his.model.vo.OrderListVO;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface CheckRequestMapper {

    // ==================== 原有方法 ====================

    @Insert("INSERT INTO check_request(register_id, medical_technology_id, check_info, check_position, creation_time, check_state) " +
            "VALUES(#{registerId}, #{medicalTechnologyId}, #{checkInfo}, #{checkPosition}, NOW(), 'CREATED')")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(CheckRequest checkRequest);

    @Select("SELECT * FROM check_request WHERE id = #{id}")
    CheckRequest selectById(Integer id);

    // 由 XML 实现
    List<CheckRequest> selectByRegisterId(Integer registerId);

    // 由 XML 实现
    int updateResult(@Param("id") Integer id,
                     @Param("checkResult") String checkResult,
                     @Param("checkEmployeeId") Integer checkEmployeeId);

    // XML 中新增的 updateState 方法，接口需要声明
    int updateState(@Param("id") Integer id,
                    @Param("checkState") String checkState);

    // ==================== 新增方法 ====================

    /**
     * 查询检查费订单 - 由 XML 实现
     */
    List<OrderListVO> selectCheckOrders(@Param("patientId") Integer patientId,
                                        @Param("orderState") String orderState,
                                        @Param("offset") Integer offset,
                                        @Param("limit") Integer limit);

    /**
     * 查询患者待预约的检查列表（医生开单、未预约、状态CREATED）- 由 XML 实现
     */
    List<com.neuedu.his.model.vo.PendingCheckRequestVO> selectPendingCheckRequests(@Param("patientId") Integer patientId);

    /**
     * 患者预约检查（更新预约时间和状态）- 由 XML 实现
     */
    int bookCheckRequest(@Param("id") Integer id,
                         @Param("bookedTime") java.time.LocalDateTime bookedTime);
}