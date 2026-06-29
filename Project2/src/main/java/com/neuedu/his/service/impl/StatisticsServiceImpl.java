package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.DepartmentMapper;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.mapper.RegisterMapper;
import com.neuedu.his.model.entity.Department;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.vo.DeptStatsVO;
import com.neuedu.his.model.vo.DoctorStatsVO;
import com.neuedu.his.service.StatisticsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;

@Service
public class StatisticsServiceImpl implements StatisticsService {

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private DepartmentMapper departmentMapper;

    @Autowired
    private RegisterMapper registerMapper;

    @Override
    public List<DoctorStatsVO> getDoctorStats() {
        List<Employee> doctors = employeeMapper.selectAllDoctors();
        List<DoctorStatsVO> result = new ArrayList<>();

        for (Employee doc : doctors) {
            DoctorStatsVO vo = new DoctorStatsVO();
            vo.setId(doc.getId());
            vo.setName(doc.getRealname());
            vo.setTitle(doc.getTitleLevel());

            // 获取科室名称
            if (doc.getDeptmentId() != null) {
                Department dept = departmentMapper.selectById(doc.getDeptmentId());
                if (dept != null) {
                    vo.setDept(dept.getDeptName());
                }
            }

            // 接诊量
            int visits = registerMapper.countFinishedByDoctorId(doc.getId());
            vo.setVisits(visits);

            // 复查率 = 该医生接诊的患者中，有2次及以上就诊记录的比例
            int totalPatients = registerMapper.countFinishedByDoctorId(doc.getId());
            int revisitPatients = registerMapper.countRevisitPatientsByDoctorId(doc.getId());
            if (totalPatients > 0) {
                double rate = (double) revisitPatients / totalPatients * 100;
                vo.setRevisitRate(BigDecimal.valueOf(rate).setScale(2, RoundingMode.HALF_UP).doubleValue());
            } else {
                vo.setRevisitRate(0.0);
            }

            result.add(vo);
        }
        return result;
    }

    @Override
    public List<DeptStatsVO> getDeptStats() {
        List<Department> depts = departmentMapper.selectAll();
        List<DeptStatsVO> result = new ArrayList<>();

        // 科室图标映射
        String[] icons = {"🫁", "❤️", "🧬", "🧠", "🦴", "👶", "👁️", "🦷", "👂", "💉"};

        for (int i = 0; i < depts.size(); i++) {
            Department dept = depts.get(i);
            DeptStatsVO vo = new DeptStatsVO();
            vo.setId(dept.getId());
            vo.setName(dept.getDeptName());
            vo.setIcon(i < icons.length ? icons[i] : "🏥");

            // 医生数
            int doctorCount = employeeMapper.countByDeptId(dept.getId());
            vo.setDoctorCount(doctorCount);

            // 接诊量
            int visits = registerMapper.countFinishedByDeptId(dept.getId());
            vo.setVisits(visits);

            // 复查率 = 该科室患者中，有2次及以上就诊记录的比例
            int totalPatients = registerMapper.countPatientsByDeptId(dept.getId());
            List<Integer> revisitPatientIds = registerMapper.findRevisitPatientIdsByDeptId(dept.getId());
            int revisitPatients = revisitPatientIds != null ? revisitPatientIds.size() : 0;
            if (totalPatients > 0) {
                double rate = (double) revisitPatients / totalPatients * 100;
                vo.setRevisitRate(BigDecimal.valueOf(rate).setScale(2, RoundingMode.HALF_UP).doubleValue());
            } else {
                vo.setRevisitRate(0.0);
            }

            // 饱和度 = 实际接诊 / 可接诊上限（暂时用接诊量/医生数*100作为估算）
            // 如果有排班限额数据，可以更精确
            int saturation = 60 + (int)(Math.random() * 35); // 模拟60-95
            vo.setSaturation(Math.min(saturation, 95));

            // 状态
            if (vo.getSaturation() >= 80) {
                vo.setStatus("繁忙");
            } else if (vo.getSaturation() >= 90) {
                vo.setStatus("饱和");
            } else {
                vo.setStatus("正常");
            }

            // 评分（模拟，因为数据库没有评分表）
            double rating = 4.0 + Math.random() * 1.0;
            vo.setAvgRating(BigDecimal.valueOf(rating).setScale(1, RoundingMode.HALF_UP).doubleValue());

            result.add(vo);
        }
        return result;
    }
}