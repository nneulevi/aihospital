package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.DashboardMapper;
import com.neuedu.his.model.vo.AdminDashboardSummaryVO;
import com.neuedu.his.model.vo.DoctorDashboardSummaryVO;
import com.neuedu.his.model.vo.PatientDashboardSummaryVO;
import com.neuedu.his.service.DashboardService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;

@Service
public class DashboardServiceImpl implements DashboardService {

    @Autowired
    private DashboardMapper dashboardMapper;

    @Override
    public AdminDashboardSummaryVO getAdminSummary() {
        AdminDashboardSummaryVO vo = new AdminDashboardSummaryVO();
        vo.setTodayRegistrations(nonNull(dashboardMapper.countTodayRegistrations()));
        vo.setActivePatients(nonNull(dashboardMapper.countActivePatients()));
        vo.setPendingChargeAmount(nonNull(dashboardMapper.sumPendingChargeAmount()));
        vo.setStockAlertCount(nonNull(dashboardMapper.countStockAlerts()));
        vo.setTodayAiAnalysisCount(nonNull(dashboardMapper.countTodayAiAnalyses()));
        vo.setPendingReportCount(nonNull(dashboardMapper.countPendingReports()));
        return vo;
    }

    @Override
    public DoctorDashboardSummaryVO getDoctorSummary(Integer doctorId) {
        DoctorDashboardSummaryVO vo = new DoctorDashboardSummaryVO();
        vo.setDoctorId(doctorId);
        vo.setPendingCount(nonNull(dashboardMapper.countDoctorPending(doctorId)));
        vo.setConsultingCount(nonNull(dashboardMapper.countDoctorConsulting(doctorId)));
        vo.setFinishedToday(nonNull(dashboardMapper.countDoctorFinishedToday(doctorId)));
        vo.setPendingCheckCount(nonNull(dashboardMapper.countDoctorPendingChecks(doctorId)));
        return vo;
    }

    @Override
    public PatientDashboardSummaryVO getPatientSummary(Integer patientId) {
        PatientDashboardSummaryVO vo = new PatientDashboardSummaryVO();
        vo.setPatientId(patientId);
        vo.setRecordCount(nonNull(dashboardMapper.countPatientRecords(patientId)));
        vo.setUnpaidOrderCount(nonNull(dashboardMapper.countPatientUnpaidOrders(patientId)));
        vo.setUnpaidAmount(nonNull(dashboardMapper.sumPatientUnpaidAmount(patientId)));
        vo.setLatestVisitState(dashboardMapper.selectPatientLatestVisitState(patientId));
        return vo;
    }

    private Long nonNull(Long value) {
        return value == null ? 0L : value;
    }

    private BigDecimal nonNull(BigDecimal value) {
        return value == null ? BigDecimal.ZERO : value;
    }
}
