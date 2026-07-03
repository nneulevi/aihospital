package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.Prescription;
import com.neuedu.his.model.vo.*;

import java.util.List;

public interface DoctorService {
    PageResult<DoctorPatientListVO> getPatients(DoctorPatientsQueryDTO query);
    void saveMedicalRecord(MedicalRecordSaveRequestDTO request);
    void createCheckRequest(CheckRequestCreateDTO request);
    void createInspectionRequest(InspectionRequestCreateDTO request);
    void createDisposalRequest(DisposalRequestCreateDTO request);
    Integer createPrescription(PrescriptionCreateDTO request);
    void confirmDiagnosis(DiagnosisConfirmRequestDTO request);
    void receiveDiagnosis(DiagnosisReceiveRequestDTO request);
    CheckResultVO getCheckResults(Integer registerId);
    DoctorProfileVO getProfile(Integer doctorId);
    DoctorStatisticsVO getStatistics(Integer doctorId);
    CheckResultDetailVO getCheckResultDetail(Integer id);
    MedicalRecordSaveRequestDTO getMedicalRecord(Integer registerId);
    CheckResultVO getOrders(Integer registerId);
    List<Prescription> getPrescriptionsByRegisterId(Integer registerId);
    DiagnosisConfirmRequestDTO getDiagnosis(Integer registerId);
}