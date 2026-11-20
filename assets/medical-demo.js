/* Browser-only state for the fictional medical project walkthrough. */
const t = (english, chinese) => document.documentElement.lang.startsWith('zh') ? chinese : english;
const booking = document.getElementById('booking');
const fields = [...booking.querySelectorAll('select')];
const [clinic, packageChoice, slot] = fields;
const back = document.getElementById('back');
const advance = document.getElementById('advance');
const bookingMessage = document.getElementById('booking-message');
const bookingOrders = document.getElementById('booking-orders');
const orderList = document.getElementById('medical-orders');
const orderMessage = document.getElementById('medical-orders-message');
const doctor = document.getElementById('medical-doctor-order');
const saveReport = document.getElementById('medical-save-report');
const doctorMessage = document.getElementById('medical-doctor-message');
const doctorReport = document.getElementById('medical-doctor-report');
const report = document.getElementById('medical-report-order');
const reportDetails = document.getElementById('medical-report-details');
const reportCaption = document.getElementById('medical-report-caption');
const reportContent = document.getElementById('medical-report-content');
const reportTabs = [...document.querySelectorAll('[data-medical-report-tab]')];

function choiceText(select, key) {
  const option = [...select.options].find(item => item.value === key);
  return option.dataset.label ?? option.textContent;
}
const orders = [
  {id: 'DEMO-01', clinic: 'a', package: 'basic', slot: null, state: 'ready'},
  {id: 'DEMO-02', clinic: 'a', package: 'extended', slot: 'thu', state: 'pending'},
];
const stateNames = {
  pending: t('Awaiting examination', '待检'),
  ready: t('Report ready', '报告已出'),
  cancelled: t('Cancelled', '已取消'),
};
for (const option of slot.options) option.dataset.label = option.textContent;
let nextOrder = 3;
let step = 0;
let reportView = 'overview';

function updateBookingAdvance() {
  if (step === 2 && !hasCapacity(slot.value)) {
    advance.disabled = true;
    bookingMessage.textContent = t('No available slots. Go back and select another clinic.', '当前机构暂无号源，请返回并更换机构。');
  } else {
    advance.disabled = false;
  }
}

function showBooking(focus = false) {
  updateBookingAdvance();
  booking.querySelectorAll('[data-book]').forEach((element, index) => { element.hidden = index !== step; });
  back.hidden = step === 0 || step === 4;
  bookingOrders.hidden = step !== 4;
  advance.textContent = step === 4 ? t('Make another booking', '再预约一次')
    : step === 3 ? t('Confirm sample', '确认示例预约') : t('Continue', '继续');
  document.getElementById('booking-summary').textContent = fields.map(field => choiceText(field, field.value)).join(' / ');
  if (focus && step < fields.length) fields[step].focus();
}

function makeTable(headers) {
  const wrapper = document.createElement('div');
  wrapper.className = 'table-scroll';
  const table = document.createElement('table');
  table.className = 'medical-order-grid';
  const header = table.createTHead().insertRow();
  for (const title of headers) {
    const cell = document.createElement('th');
    cell.scope = 'col';
    cell.textContent = title;
    header.append(cell);
  }
  wrapper.append(table);
  return {wrapper, body: table.createTBody()};
}

function appendRow(body, values) {
  const row = body.insertRow();
  for (const value of values) row.insertCell().textContent = value;
  return row;
}

function fillOrderSelect(select, records, fallback) {
  const previous = select.value;
  select.replaceChildren(...records.map(order => new Option(order.id, order.id)));
  if (!records.length) select.add(new Option(fallback, ''));
  if (records.some(order => order.id === previous)) select.value = previous;
}

function renderReport() {
  const selected = orders.find(order => order.id === report.value && order.state === 'ready');
  reportCaption.textContent = selected ? selected.id + ' · ' + choiceText(clinic, selected.clinic) : '';
  for (const button of reportTabs) {
    button.setAttribute('aria-pressed', String(button.dataset.medicalReportTab === reportView));
  }
  const {wrapper, body} = makeTable([t('Report field', '报告字段'), t('Sample value', '示例信息')]);
  if (reportView === 'overview') {
    appendRow(body, [t('Record', '记录编号'), selected?.id || '']);
    appendRow(body, [t('Overview', '总检结论'), t('Sample A · reviewed', '示例项目 A · 已审核')]);
    appendRow(body, [t('Check items recorded', '已录入检查项'), '2']);
  } else {
    appendRow(body, [t('Sample item A', '示例检查项 A'), t('Recorded', '已录入')]);
    appendRow(body, [t('Sample item B', '示例检查项 B'), t('Flagged for review', '标记为需复核')]);
  }
  reportContent.replaceChildren(wrapper);
}

function renderRecords() {
  const {wrapper, body} = makeTable([t('Order', '订单'), t('Clinic and package', '机构与套餐'), t('Slot', '时段'),
                                     t('Status', '状态'), t('Action', '操作')]);
  for (const order of orders) {
    const row = appendRow(body, [order.id, choiceText(clinic, order.clinic) + ' · ' + choiceText(packageChoice, order.package),
                                  order.slot ? choiceText(slot, order.slot) : t('Previous sample', '既往样例'), stateNames[order.state]]);
    const action = row.insertCell();
    if (order.state === 'pending') {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = t('Cancel', '取消预约');
      button.setAttribute('aria-label', t('Cancel appointment ', '取消预约 ') + order.id);
      button.addEventListener('click', () => {
        order.state = 'cancelled';
        renderRecords();
        orderMessage.textContent = t('Sample appointment cancelled: ', '已取消示例预约 ') + order.id + ' ';
        const undo=document.createElement('button');
        undo.type='button';
        undo.textContent=t('Undo cancellation','撤销取消');
        undo.onclick=()=>{
          const occupied=orders.some(other=>other!==order && other.state!=='cancelled' && other.clinic===order.clinic && other.slot===order.slot);
          if(occupied){orderMessage.textContent=t('This slot has been rebooked.', '该时段已被重新预约。');return;}
          order.state='pending';renderRecords();
          orderMessage.textContent=t('Appointment restored: ', '已恢复预约 ')+order.id;
        };
        orderMessage.append(undo);undo.focus({preventScroll:true});
      });
      action.append(button);
    } else if (order.state === 'ready') {
      const link = document.createElement('a');
      link.href = '#report';
      link.textContent = t('Open report', '打开报告');
      link.addEventListener('click', () => {
        report.value = order.id;
        renderReport();
        reportDetails.open = true;
      });
      action.append(link);
    }
  }
  orderList.replaceChildren(wrapper);
  const pending = orders.filter(order => order.state === 'pending');
  fillOrderSelect(doctor, pending, t('No pending orders', '暂无待检订单'));
  saveReport.disabled = !pending.length;
  fillOrderSelect(report, orders.filter(order => order.state === 'ready'), '');
  renderReport();
  showAvailability();
}

function hasCapacity(value) {
  return Boolean(value) && value !== 'full' && !orders.some(order =>
    order.clinic === clinic.value && order.slot === value && order.state !== 'cancelled');
}

function showAvailability() {
  for (const option of slot.options) {
    const available = hasCapacity(option.value);
    option.disabled = !available;
    option.textContent = option.dataset.label.split(' · ')[0] + ' · ' +
      (available ? t('Available','有号') : t('Full','已满'));
  }
  if (!hasCapacity(slot.value)) {
    slot.value = Array.from(slot.options).find(option => !option.disabled)?.value ?? '';
  }
  updateBookingAdvance();
}

advance.addEventListener('click', () => {
  bookingMessage.textContent = '';
  if ((step === 2 || step === 3) && !hasCapacity(slot.value)) {
    step = 2;
    showBooking(true);
    bookingMessage.textContent = t('This slot is full. Choose another slot or clinic.', '当前号源已满，请改选时段或机构。');
    return;
  }
  if (step === 3) {
    const id = 'DEMO-' + String(nextOrder++).padStart(2, '0');
    orders.push({id, clinic: clinic.value, package: packageChoice.value, slot: slot.value, state: 'pending'});
    renderRecords();
    bookingMessage.textContent = t('Sample booking confirmed: ', '示例预约已确认：') + id;
    step = 4;
  } else if (step === 4) {
    booking.reset();
    showAvailability();
    step = 0;
  } else {
    step++;
  }
  showBooking(true);
});

back.addEventListener('click', () => {
  step--;
  bookingMessage.textContent = '';
  showBooking(true);
});
booking.addEventListener('submit', event => event.preventDefault());
clinic.addEventListener('change', showAvailability);
slot.addEventListener('change', updateBookingAdvance);

saveReport.addEventListener('click', () => {
  const order = orders.find(record => record.id === doctor.value && record.state === 'pending');
  if (!order) return;
  order.state = 'ready';
  renderRecords();
  report.value = order.id;
  reportView = 'overview';
  renderReport();
  doctorReport.hidden = false;
  doctorMessage.textContent = t('Sample report saved: ', '示例报告已保存：') + order.id;
});
report.addEventListener('change', renderReport);
for (const tab of reportTabs) {
  tab.addEventListener('click', () => {
    reportView = tab.dataset.medicalReportTab;
    renderReport();
  });
}

function openReportAnchor() {
  if (location.hash === '#report') reportDetails.open = true;
}
for (const link of document.querySelectorAll('.function-index a[href="#report"], #medical-doctor-report')) {
  link.addEventListener('click', () => { reportDetails.open = true; });
}
window.addEventListener('hashchange', openReportAnchor);
document.getElementById('booking-actions').hidden = false;
document.getElementById('medical-doctor-actions').hidden = false;
document.querySelector('.medical-report-tabs').hidden = false;
renderRecords();
showBooking();
openReportAnchor();
