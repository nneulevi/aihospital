package com.neuedu.his.service;

import com.neuedu.his.model.dto.PatientAuthRegisterRequestDTO;  // ← 改这里
import com.neuedu.his.model.vo.PatientListVO;
import com.neuedu.his.model.vo.PatientLoginResponseVO;

import java.util.List;

public interface PatientAuthService {

    void sendCode(String phone, String codeType);

    PatientLoginResponseVO register(PatientAuthRegisterRequestDTO request);  // ← 改这里

    List<PatientListVO> getPatientList(Integer currentPatientId);

    String switchPatient(Integer patientId, Integer currentPatientId);

    void logout(String token);
}