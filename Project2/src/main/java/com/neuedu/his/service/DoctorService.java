package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;

public interface DoctorService {
    PageResult<DoctorPatientListVO> getPatients(DoctorPatientsQueryDTO query);
    void saveMedicalRecord(MedicalRecordSaveRequestDTO request);
    void createCheckRequest(CheckRequestCreateDTO request);
    void createInspectionRequest(InspectionRequestCreateDTO request);
    void createDisposalRequest(DisposalRequestCreateDTO request);
    Integer createPrescription(PrescriptionCreateDTO request);
    void confirmDiagnosis(DiagnosisConfirmRequestDTO request);
    CheckResultVO getCheckResults(Integer registerId);
    DoctorProfileVO getProfile(Integer doctorId);
    DoctorStatisticsVO getStatistics(Integer doctorId);
    CheckResultDetailVO getCheckResultDetail(Integer id);



}