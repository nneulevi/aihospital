from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    appointment = read("frontend/src/views/patient/Appointment.vue")
    ai_inquiry = read("frontend/src/views/patient/AIInquiry.vue")
    booking_shell = read("frontend/src/views/patient/_BookingShell.vue")
    lab = read("frontend/src/views/patient/LabBooking.vue")
    exam = read("frontend/src/views/patient/ExamBooking.vue")
    schedule = read("frontend/src/views/admin/ScheduleSourceManage.vue")

    assert_true("doctorName: '张敏'" not in appointment, "挂号页不能在路由跳转时硬编码医生信息")
    assert_true("loadDoctorFromRoute" in appointment, "挂号页需要从后端号源反查路由中的医生")
    assert_true("resolveResponseRecords" in appointment, "挂号页需要兼容统一响应并正确解析医生列表")
    assert_true("selectedDoctor.value!.doctorId" not in appointment, "挂号提交前需要显式校验医生选择")

    assert_true("'张敏'" not in ai_inquiry and "'李华'" not in ai_inquiry, "智能问诊不能硬编码推荐医生姓名")
    assert_true("id: 101" not in ai_inquiry and "id: 102" not in ai_inquiry, "智能问诊不能硬编码推荐医生ID")
    assert_true("loadAvailableDoctors" in ai_inquiry, "智能问诊推荐医生必须来自实时号源")
    assert_true("getDoctors" in ai_inquiry, "智能问诊需要调用患者医生号源接口")
    assert_true("doctorId: String(doctorId)" in ai_inquiry, "推荐医生跳转挂号需要携带真实医生ID")

    assert_true("selectedIds" in booking_shell, "检查/检验预约需要有选中态")
    assert_true("submitBooking" in booking_shell, "检查/检验预约需要提交申请")
    assert_true("@click=\"toggleItem(item)\"" in booking_shell, "检查/检验项目按钮需要可点击选择")
    assert_true("@submit=" in lab and "createPatientInspectionRequest" in lab, "检验预约需要提交到患者检验申请接口")
    assert_true("@submit=" in exam and "createPatientCheckRequest" in exam, "检查预约需要提交到患者检查申请接口")

    assert_true("getScheduleSources({" in schedule, "管理员号源页需要绑定后端查询接口")
    assert_true("query:" in schedule, "管理员号源查询需要使用统一 query 参数封装")

    print("patient_flow_integrity=PASS")


if __name__ == "__main__":
    main()
