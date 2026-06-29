package com.neuedu.his.service;

import com.neuedu.his.model.vo.DeptStatsVO;
import com.neuedu.his.model.vo.DoctorStatsVO;

import java.util.List;

public interface StatisticsService {

    List<DoctorStatsVO> getDoctorStats();

    List<DeptStatsVO> getDeptStats();
}