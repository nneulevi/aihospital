package com.neuedu.his.service;

import com.neuedu.his.model.vo.AdminDashboardSummaryVO;
import com.neuedu.his.model.vo.DoctorDashboardSummaryVO;
import com.neuedu.his.model.vo.PatientDashboardSummaryVO;

public interface DashboardService {
    AdminDashboardSummaryVO getAdminSummary();
    DoctorDashboardSummaryVO getDoctorSummary(Integer doctorId);
    PatientDashboardSummaryVO getPatientSummary(Integer patientId);
}
