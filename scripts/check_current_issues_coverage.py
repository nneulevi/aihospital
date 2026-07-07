import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def remote_frontend_missing() -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "remotes/aihospital/master", "frontend"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    return [path for path in output.splitlines() if not (ROOT / path).exists()]


def main() -> None:
    current_issues = read("目前存在问题.md")
    acceptance = read("统一验收标准.md")
    patient_layout = read("frontend/src/views/layouts/PatientLayout.vue")
    mini_layout = read("frontend/src/views/mini-patient/MiniPatientLayout.vue")
    admin_layout = read("frontend/src/views/layouts/AdminBusinessLayout.vue")
    patient_home = read("frontend/src/views/patient/Home.vue")
    patient_services = read("frontend/src/views/patient/Services.vue")
    appointment = read("frontend/src/views/patient/Appointment.vue")
    appointment_success = read("frontend/src/views/patient/AppointmentSuccess.vue")
    orders = read("frontend/src/views/patient/Orders.vue")
    records = read("frontend/src/views/patient/Records.vue")
    profile = read("frontend/src/views/patient/Profile.vue")
    login = read("frontend/src/views/patient/Login.vue")
    mini_appointment = read("frontend/src/views/mini-patient/Appointment.vue")
    ai_inquiry = read("frontend/src/views/patient/AIInquiry.vue")
    booking_shell = read("frontend/src/views/patient/_BookingShell.vue")
    lab = read("frontend/src/views/patient/LabBooking.vue")
    exam = read("frontend/src/views/patient/ExamBooking.vue")
    ai_schedule = read("frontend/src/views/admin/AISchedule.vue")
    schedule_service = read("Project2/src/main/java/com/neuedu/his/service/impl/ScheduleServiceImpl.java")
    register_mapper = read("Project2/src/main/java/com/neuedu/his/mapper/RegisterMapper.java")
    patient_service = read("Project2/src/main/java/com/neuedu/his/service/impl/PatientServiceImpl.java")
    patient_visit = read("frontend/src/views/doctor/PatientVisit.vue")
    request_util = read("frontend/src/utils/request.ts")
    doctor_controller = read("Project2/src/main/java/com/neuedu/his/controller/DoctorController.java")
    doctor_service = read("Project2/src/main/java/com/neuedu/his/service/impl/DoctorServiceImpl.java")
    doctor_vo = read("Project2/src/main/java/com/neuedu/his/model/vo/DoctorListVO.java")
    drug_mapper = read("Project2/src/main/resources/mapper/DrugInfoMapper.xml")

    assert_true("统一验收标准.md" in current_issues, "问题文档必须显式绑定统一验收标准")
    assert_true("前后端的接口都能一一匹配" in acceptance, "统一验收标准缺少接口匹配要求")

    missing = remote_frontend_missing()
    assert_true(not missing, f"远端master前端文件仍缺失: {missing[:10]}")

    assert_true("<keep-alive>" not in patient_layout, "患者Web端不应全局缓存页面导致旧数据")
    assert_true("<keep-alive>" not in mini_layout, "小程序端不应全局缓存页面导致旧数据")

    assert_true("to=\"/admin\"" in admin_layout, "管理员底部首页路由必须存在")
    assert_true("v-model=" not in admin_layout, "管理员底部导航 route 模式不应再混用数字 v-model")
    assert_true("goAdminHome" not in admin_layout, "管理员顶部不应再放风格不统一的首页标签按钮")
    assert_true("const navigate = (path: string)" in admin_layout and "router.replace(path)" in admin_layout, "管理员底部导航必须具备显式路由兜底")
    assert_true("handleLogout" in admin_layout, "管理员端必须有退出登录入口")
    assert_true("v-model=" not in patient_layout, "患者底部导航 route 模式不应再混用数字 v-model")
    assert_true("const navigate = (path: string)" in patient_layout and "router.replace(path)" in patient_layout, "患者底部导航必须具备显式路由兜底")

    assert_true("/patient/customer-service" in patient_home, "患者首页必须暴露联系客服入口")
    assert_true("/patient/customer-service" in patient_services, "全部服务必须暴露联系客服入口")

    assert_true("dedupeDepartments" in appointment, "患者挂号科室列表必须去重")
    assert_true("dedupeDepartments" in mini_appointment, "小程序挂号科室列表必须去重")
    assert_true("friendlyError" in appointment and "error?.userMessage" in appointment, "患者挂号失败必须显示用户可理解错误")
    assert_true(r"\d{17}" in appointment and r"^1[3-9]\d{9}$" in appointment, "患者挂号必须在前端校验身份证号和手机号")
    assert_true(r"\d{17}" in mini_appointment and r"^1[3-9]\d{9}$" in mini_appointment, "小程序挂号必须在前端校验身份证号和手机号")
    assert_true("error?.userMessage" in mini_appointment, "小程序挂号失败必须显示用户可理解错误")
    assert_true("error.userMessage" in request_util, "请求层必须把后端错误转换为页面可读消息")
    assert_true("gender: 'M'" in mini_appointment, "小程序挂号性别字段必须与后端 M/F 对齐")
    assert_true("loadDoctorFromRoute" in appointment, "AI推荐跳转挂号必须回查真实医生号源")
    assert_true("doctorName: '张敏'" not in appointment, "挂号页不能硬编码医生")
    assert_true("'张敏'" not in ai_inquiry and "'李华'" not in ai_inquiry, "智能问诊不能硬编码推荐医生")
    assert_true("loadAvailableDoctors" in ai_inquiry and "getDoctors" in ai_inquiry, "智能问诊推荐医生必须来自真实号源接口")
    assert_true("private String specialty" in doctor_vo, "患者可预约医生接口必须返回真实擅长方向")
    assert_true("doctor.specialty" in ai_inquiry, "智能问诊医生卡片必须使用后端医生擅长方向")
    assert_true("streamedConclusion" in ai_inquiry, "智能问诊结果页必须保留流式自然语言结论")
    patient_style_sources = "\n".join([appointment, appointment_success, orders, records, profile, login])
    for stale_token in ["#FFF9F0", "#F4A261", "#FAF3E8", "#E8DCC8", "#8B7A6B", "#5C4B3A", "#C4B8A8"]:
        assert_true(stale_token not in patient_style_sources, f"患者端核心页面仍残留旧橙色风格: {stale_token}")
    assert_true("getRecordDetail" in appointment_success, "挂号成功页必须基于后端挂号详情展示")
    assert_true("张敏" not in appointment_success and "呼吸内科" not in appointment_success, "挂号成功页不能显示硬编码假医生/科室")

    assert_true("selectedIds" in booking_shell and "submitBooking" in booking_shell, "检查/检验预约项目必须可选并可提交")
    assert_true("createPatientInspectionRequest" in lab, "检验预约必须提交真实检验申请")
    assert_true("createPatientCheckRequest" in exam, "检查预约必须提交真实检查申请")

    assert_true("getAdminDepartments" in ai_schedule, "AI排班科室必须来自后端真实科室")
    assert_true("new Set<string>()" in ai_schedule and "devMarkers" in ai_schedule, "AI排班科室下拉必须按名称去重并过滤测试痕迹")
    assert_true("startDate = ref(dayjs().format('YYYY-MM-DD'))" in ai_schedule, "AI排班必须默认开始日期，不能让历史查询无条件失败")
    assert_true("endDate = ref(dayjs().add(6, 'day').format('YYYY-MM-DD'))" in ai_schedule, "AI排班必须默认结束日期")
    assert_true("selectedDeptId.value = deptColumns.value[0].value" in ai_schedule, "AI排班必须在加载后默认选中首个真实科室")
    assert_true("hasQueriedHistory" in ai_schedule, "AI排班历史查询必须有可见空态反馈")
    assert_true("syncGeneratedScheduleToSource" in schedule_service, "AI排班生成结果必须同步为真实号源")
    assert_true("schedulingMapper.insert" in schedule_service, "AI排班必须写入 scheduling 表")

    assert_true("countActiveByPatientSchedule" in register_mapper, "挂号必须防止同一患者重复预约同一医生时段")
    assert_true("号源已满" in patient_service, "挂号必须防满号")
    assert_true("register.setQueueNo(usedQuota + 1)" in patient_service, "排队号必须基于真实已用号源")
    assert_true("return-waiting" in doctor_controller, "医生端必须提供退回候诊接口")
    assert_true("returnToWaiting" in doctor_service and '"REGISTERED"' in doctor_service, "医生接诊后必须能退回待诊状态")
    assert_true("returnPatientToWaiting" in patient_visit and "退回候诊" in patient_visit, "医生接诊页必须暴露退回候诊按钮")

    assert_true("uploadImageFile" in patient_visit and "analyzeImage" in patient_visit and "generateAiReport" in patient_visit, "医生工作台必须有头部CT上传、分析、报告业务入口")
    assert_true("NOT LIKE 'Extended%'" in drug_mapper and "NOT LIKE '%验收%'" in drug_mapper, "药品库存列表必须过滤开发/验收痕迹数据")

    print("current_issues_coverage=PASS")


if __name__ == "__main__":
    main()
