package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;

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
}
