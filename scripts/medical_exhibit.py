"""Bilingual presentation of the medical team project and its offline walkthrough."""


def demo(page):
    t = page.t
    clinics = page.select('clinic', [
        ('a', t('Harbour Clinic', '海港示例机构')),
        ('b', t('Riverside Clinic', '滨河示例机构')),
    ])
    packages = page.select('package', [
        ('basic', t('Basic screening', '基础套餐')),
        ('extended', t('Extended screening', '扩展套餐')),
    ])
    dates = page.select('slot', [
        ('full', t('Tuesday morning · full', '周二上午 · 已满')),
        ('wed', t('Wednesday morning', '周三上午')),
        ('thu', t('Thursday afternoon', '周四下午')),
    ])
    fields = [(t('Institution', '机构'), clinics), (t('Package', '套餐'), packages),
              (t('Appointment slot', '预约时段'), dates)]
    steps = ''.join(f'<div data-book="{i}"><label><b>{i+1} / 4 · {title}</b><br>{field}</label></div>'
                    for i, (title,field) in enumerate(fields))
    return f'''
    <p class="medical-demo-note">{t("Offline demo with fictional records. Changes apply to this page and reset on refresh.", "静态演示使用虚构记录。操作只影响当前页面，刷新后重置。")}</p>

    <div class="flow medical-flow">
      <form id="booking">
        {steps}
        <div data-book="3"><h3>{t("4 / 4 · Confirm selection", "4 / 4 · 确认所选信息")}</h3><output id="booking-summary"></output></div>
        <p id="booking-message" role="status"></p>
        <div class="actions" id="booking-actions" hidden>
          <button id="back" type="button">{t("Back", "上一步")}</button>
          <button class="primary" id="advance" type="button">{t("Continue", "继续")}</button>
          <a id="booking-orders" href="#appointments" hidden>{t("View my appointments", "查看我的预约")}</a>
        </div>
      </form>
    </div>

    <section class="medical-module" id="appointments">
      <h3>{t("My appointments", "我的预约")}</h3>
      <p>{t("Review the booking, then cancel it or continue to the doctor view.", "查看订单，可取消待检预约，或进入医生端示例。")}</p>
      <div id="medical-orders"></div>
      <p id="medical-orders-message" role="status"></p>
    </section>

    <section class="medical-module" id="doctor-demo">
      <h3>{t("Doctor view · offline simulation", "医生端 · 静态模拟")}</h3>
      <p>{t("Select a pending order and save a preset fictional result. The original backend has order lookup and report-writing endpoints.", "选择待检订单并保存预设的虚构结果。原项目后端实现了订单查询与报告录入接口。")}</p>
      <div class="actions" id="medical-doctor-actions" hidden>
        <label>{t("Pending order", "待检订单")} <select id="medical-doctor-order"><option value="">{t("No pending orders", "暂无待检订单")}</option></select></label>
        <button type="button" id="medical-save-report">{t("Save sample report", "保存示例报告")}</button>
        <a href="#report" id="medical-doctor-report" hidden>{t("View the saved report", "查看已保存报告")}</a>
      </div>
      <p id="medical-doctor-message" role="status"></p>
    </section>

    <section class="medical-module" id="report">
      <h3>{t("Report centre", "报告中心")}</h3>
      <p>{t("Completed sample reports include an overview and individual check items.", "已完成的示例报告可查看总检结论和检查明细。")}</p>
      <details id="medical-report-details">
        <summary>{t("Open a fictional report", "查看虚构报告")}</summary>
        <label>{t("Report order", "报告订单")} <select id="medical-report-order"><option value="DEMO-01">DEMO-01</option></select></label>
        <p id="medical-report-caption"></p>
        <div class="actions medical-report-tabs" aria-label="{t("Report views", "报告视图")}" hidden>
          <button type="button" data-medical-report-tab="overview" aria-pressed="true">{t("Overview", "总检结论")}</button>
          <button type="button" data-medical-report-tab="details" aria-pressed="false">{t("Check items", "检查明细")}</button>
        </div>
        <div id="medical-report-content" aria-live="polite"></div>
      </details>
    </section>'''


def architecture(page, table):
    t = page.t
    rows = [
        (t('Patient app', '用户端'), t('Account and profile, clinic and package browsing, dates, confirmation, appointments and reports.',
                                      '注册登录、个人中心、医院和套餐浏览、预约日期、确认、预约记录与报告。')),
        (t('Appointment services', '预约服务'), t('Spring Boot controllers connect the calendar, clinic, package and order services. The calendar reports configured capacity, booked counts and remaining slots.',
                                               'Spring Boot 控制器衔接日历、医院、套餐和订单服务。日历查询配置号源、已预约数量与可约余量。')),
        (t('Doctor and reporting services', '医生与报告服务'), t('The backend provides order lookup, check-item entry, detailed results and an overall result. The patient app reads reports by order ID.',
                                                       '后端提供订单查询、检查项目和明细录入、总检结果保存。用户端按订单 ID 读取报告。')),
        (t('Persistence', '数据层'), t('JPA repositories use MySQL. An order links the user, clinic, package and appointment date; report records reference the order.',
                                     '通过 JPA 仓储访问 MySQL。订单关联用户、医院、套餐与预约日期，报告记录通过订单 ID 关联。')),
    ]
    body = table([t('Area', '模块'), t('Original implementation', '原工程实现')], rows)
    role = t('The practicum report lists my responsibilities as frontend implementation, sourcing interface assets, and integrating content. The backend, database and doctor workflow are presented as team work.',
             '实训报告记载的个人分工为前端制作、素材查找、内容整合。后端、数据库与医生端业务作为团队成果展示。')
    images = page.img('case-studies/medical/images/patient-runtime.jpg', t('Patient report in the running app', '本地用户端 · 总检报告'))
    images += page.img('case-studies/medical/images/doctor-runtime.jpg', t('Doctor report form in the running app', '本地医生端 · 报告录入'))
    runtime = t('The local edition uses the original patient app and backend, with a doctor workspace rebuilt from the practicum report and team APIs. Doctors can filter appointments by patient, package, date and report status, enter results and read archived reports. Both interfaces use fictional records.',
                '本地版沿用原用户端和后端，参照实训报告与团队接口补建医生工作台。医生可按体检人、套餐、日期和报告状态筛选，录入结果并查阅归档报告。两端均使用虚构记录。')
    return (f'<h3>{t("My contribution", "个人责任范围")}</h3><p>{role}</p>'
            f'<h3>{t("Team system architecture", "团队项目架构")}</h3>{body}'
            f'<h3>{t("Running application", "本地运行画面")}</h3><p>{runtime}</p><div class="thumbs">{images}</div>')
