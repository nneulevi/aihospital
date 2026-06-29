package com.neuedu.his.controller;

import com.neuedu.his.model.vo.AdminDashboardSummaryVO;
import com.neuedu.his.model.vo.DoctorDashboardSummaryVO;
import com.neuedu.his.model.vo.PatientDashboardSummaryVO;
import com.neuedu.his.service.DashboardService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class DashboardContractTest {

    private MockMvc mockMvc;
    private DashboardService dashboardService;

    @BeforeEach
    void setUp() {
        dashboardService = mock(DashboardService.class);

        AdminController adminController = new AdminController();
        DoctorController doctorController = new DoctorController();
        PatientController patientController = new PatientController();
        inject(adminController, "dashboardService", dashboardService);
        inject(doctorController, "dashboardService", dashboardService);
        inject(patientController, "dashboardService", dashboardService);

        mockMvc = MockMvcBuilders.standaloneSetup(adminController, doctorController, patientController).build();
    }

    private void inject(Object target, String fieldName, Object value) {
        try {
            java.lang.reflect.Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
    }

    @Test
    void adminDashboardSummaryIsExposedForFrontendHome() throws Exception {
        AdminDashboardSummaryVO response = new AdminDashboardSummaryVO();
        response.setTodayRegistrations(12L);
        response.setActivePatients(4L);
        response.setPendingChargeAmount(new BigDecimal("256.50"));
        response.setStockAlertCount(2L);
        response.setTodayAiAnalysisCount(3L);
        response.setPendingReportCount(1L);
        when(dashboardService.getAdminSummary()).thenReturn(response);

        mockMvc.perform(get("/api/admin/dashboard/summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.todayRegistrations").value(12))
                .andExpect(jsonPath("$.pendingChargeAmount").value(256.50))
                .andExpect(jsonPath("$.stockAlertCount").value(2));
    }

    @Test
    void doctorDashboardSummaryIsExposedForFrontendHome() throws Exception {
        DoctorDashboardSummaryVO response = new DoctorDashboardSummaryVO();
        response.setDoctorId(7);
        response.setPendingCount(5L);
        response.setConsultingCount(2L);
        response.setFinishedToday(9L);
        response.setPendingCheckCount(6L);
        when(dashboardService.getDoctorSummary(7)).thenReturn(response);

        mockMvc.perform(get("/api/doctor/dashboard/summary").param("doctorId", "7"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.doctorId").value(7))
                .andExpect(jsonPath("$.pendingCount").value(5))
                .andExpect(jsonPath("$.finishedToday").value(9));
    }

    @Test
    void patientDashboardSummaryIsExposedForFrontendProfile() throws Exception {
        PatientDashboardSummaryVO response = new PatientDashboardSummaryVO();
        response.setPatientId(9);
        response.setRecordCount(11L);
        response.setUnpaidOrderCount(3L);
        response.setUnpaidAmount(new BigDecimal("88.00"));
        response.setLatestVisitState("REGISTERED");
        when(dashboardService.getPatientSummary(9)).thenReturn(response);

        mockMvc.perform(get("/api/patient/dashboard/summary").param("patientId", "9"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.patientId").value(9))
                .andExpect(jsonPath("$.recordCount").value(11))
                .andExpect(jsonPath("$.unpaidAmount").value(88.00));
    }
}
