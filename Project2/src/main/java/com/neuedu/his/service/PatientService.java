package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;

import java.util.List;

public interface PatientService {

    // ==================== 原有方法 ====================

    Integer register(PatientRegisterRequestDTO request);

    void cancelRegister(RegisterCancelRequestDTO request);

    PageResult<PatientRecordListVO> getRecords(PatientRecordsQueryDTO query);

    PatientRecordListVO getRecordDetail(Integer registerId);

    PageResult<DoctorListVO> getDoctors(DoctorListQueryDTO query);

    PageResult<OrderListVO> getOrders(PatientOrdersQueryDTO query);

    // ==================== 新增方法 ====================

    /** 科室列表（患者端） */
    List<DeptListVO> listDepartments();

    /** 今日可报到列表 */
    List<TodayRegisterVO> getTodayRegisters(Integer patientId);

    /** 报到提交 */
    CheckinResultVO submitCheckin(CheckinRequestDTO request);

    /** 候诊状态 */
    QueueStatusVO getQueueStatus(Integer registerId);

    /** 候诊科室列表 */
    List<DeptQueueVO> getQueueDepts(Integer patientId);

    /** 检验项目列表 */
    List<MedicalTechVO> getInspectionList();

    /** 检查项目列表 */
    List<MedicalTechVO> getCheckList();

    /** 检验预约提交（患者端） */
    void createInspectionRequest(PatientInspectionRequestDTO request);

    /** 检查预约提交（患者端） */
    void createCheckRequest(PatientCheckRequestDTO request);

    /** 处方列表 */
    PageResult<PrescriptionListVO> getPrescriptions(PrescriptionQueryDTO query);

    /** 处方详情 */
    PrescriptionDetailVO getPrescriptionDetail(Integer id);

    /** 报告列表 */
    PageResult<ReportListVO> getReports(ReportQueryDTO query);

    /** 报告详情 */
    ReportDetailVO getReportDetail(Long id);

    /** 标记报告已读 */
    void markReportRead(Long id);

    /** 当前患者信息 */
    PatientCurrentVO getCurrentPatient(Integer patientId);

    /** 候诊角标 */
    QueueCountVO getQueueCount(Integer patientId);
}