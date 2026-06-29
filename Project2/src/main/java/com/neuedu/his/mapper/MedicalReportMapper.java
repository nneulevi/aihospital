package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.MedicalReport;
import com.neuedu.his.model.vo.ReportListVO;
import com.neuedu.his.model.vo.ReportDetailVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface MedicalReportMapper {

    MedicalReport selectById(@Param("id") Long id);

    int insert(MedicalReport report);

    int update(MedicalReport report);

    List<ReportListVO> selectReportList(@Param("patientId") Long patientId,
                                        @Param("requestType") String requestType,
                                        @Param("offset") Integer offset,
                                        @Param("limit") Integer limit);

    Long countReportList(@Param("patientId") Long patientId,
                         @Param("requestType") String requestType);

    ReportDetailVO selectReportDetail(@Param("id") Long id);

    int markAsRead(@Param("id") Long id,
                   @Param("viewedTime") LocalDateTime viewedTime);
}