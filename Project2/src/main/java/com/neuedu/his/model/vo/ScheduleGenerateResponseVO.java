package com.neuedu.his.model.vo;

import lombok.Data;

import java.util.List;

@Data
public class ScheduleGenerateResponseVO {
    private Integer scheduleRuleId;
    private List<DailySchedule> results;

    @Data
    public static class DailySchedule {
        private String date;
        private List<ShiftInfo> morning;
        private List<ShiftInfo> afternoon;

        @Data
        public static class ShiftInfo {
            private Integer employeeId;
            private String employeeName;
            private Integer quota;
            private String shiftType;
        }
    }
}