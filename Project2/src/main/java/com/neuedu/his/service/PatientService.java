package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;

import java.util.List;

public interface PatientService {
    void sendCode(SendCodeRequestDTO request);
    LoginResponseVO authRegister(PatientAuthRegisterRequestDTO request);
    void logout();
    String switchPatient(Integer patientId);
    java.util.List<PatientListVO> listPatients();
    Integer register(PatientRegisterRequestDTO request);
    void cancelRegister(RegisterCancelRequestDTO request);
    PageResult<PatientRecordListVO> getRecords(PatientRecordsQueryDTO query);
    PatientRecordListVO getRecordDetail(Integer registerId);
    PageResult<DoctorListVO> getDoctors(DoctorListQueryDTO query);
    PageResult<OrderListVO> getOrders(PatientOrdersQueryDTO query);
    List<PatientDepartmentVO> getDepartments();
    PatientTodayRegisterVO getTodayRegister(Integer patientId);
    PatientCheckinResultVO submitCheckin(Integer patientId, Integer registerId);
    PatientQueueStatusVO getQueueStatus(Integer patientId, Integer registerId);
    java.util.List<DeptQueueVO> getQueueDepts(Integer patientId);
    QueueCountVO getQueueCount(Integer patientId);
    List<PatientMedicalTechnologyVO> getMedicalTechnologies(String techType, Integer deptId);
    void createCheckRequest(PatientCheckRequestDTO request);
    void createInspectionRequest(PatientInspectionRequestDTO request);
    PageResult<PatientMedicalRequestVO> getInspectionRequests(Integer patientId, Integer pageNum, Integer pageSize);
    PageResult<PatientMedicalRequestVO> getCheckRequests(Integer patientId, Integer pageNum, Integer pageSize);
    PageResult<PatientPrescriptionVO> getPrescriptions(Integer patientId, Integer pageNum, Integer pageSize);
    PrescriptionDetailVO getPrescriptionDetail(Integer prescriptionId);
    PageResult<PatientReportVO> getReports(Integer patientId, Integer pageNum, Integer pageSize);
    ReportDetailVO getReportDetail(String reportId);
    void markReportRead(String reportId);
    PatientCurrentVO getCurrentPatient(Integer patientId);
    void bookInspectionRequest(BookRequestDTO request);
    void bookCheckRequest(BookRequestDTO request);
}
