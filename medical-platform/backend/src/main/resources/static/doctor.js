const element = id => document.getElementById(id);
const login = element('login');
const report = element('report');
const notice = element('notice');
const filters = element('filters');
const archive = element('archive');
let appointments = [];
let activeFilter = {};
let detailRequest = 0;
let token = '';
let activeOrder = null;

async function request(path, data) {
  const headers = data === undefined ? {} : {'Content-Type': 'application/json'};
  if (token) headers.Authorization = 'Bearer ' + token;
  const response = await fetch('/doctor/' + path, {
    method: data === undefined ? 'GET' : 'POST', headers,
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  if (response.status === 204) return;
  if (!response.ok) {
    if (response.status === 401) {
      reset();
      throw Error('请检查登录信息，或重新登录。');
    }
    const error = await response.json().catch(() => ({}));
    throw Error(error.message || '操作失败，请稍后重试。');
  }
  return response.json();
}
function reset() {
  token = '';
  activeOrder = null;
  detailRequest++;
  appointments = [];
  activeFilter = {};
  filters.reset();
  archive.hidden = true;
  login.hidden = false;
  element('workspace').hidden = true;
  report.hidden = true;
  report.reset();
  login.reset();
}
async function refreshAppointments() {
  const session = token;
  const appointmentsRequest = await request('appointments');
  if (session !== token) return;
  appointments = appointmentsRequest;
  const packageField = filters.elements.package;
  const selected = packageField.value;
  const plans = new Map(appointments.map(row => [row.packageId, row.packageName]));
  packageField.replaceChildren(new Option('全部', ''), ...[...plans.entries()].map(([id, name]) => new Option(name, id)));
  packageField.value = plans.has(Number(selected)) ? selected : '';
  if (!plans.has(Number(activeFilter.package))) activeFilter.package = '';
  renderAppointments();
}

function renderAppointments() {
  const table = element('queue');
  table.replaceChildren();
  const matches = appointments.filter(row =>
    (!activeFilter.phone || row.phone.includes(activeFilter.phone)) &&
    (!activeFilter.patient || row.patientName.includes(activeFilter.patient)) &&
    (!activeFilter.sex || String(row.sex) === activeFilter.sex) &&
    (!activeFilter.package || String(row.packageId) === activeFilter.package) &&
    (!activeFilter.date || row.orderDate === activeFilter.date) &&
    (!activeFilter.state || String(row.state) === activeFilter.state)
  );
  element('queue-count').textContent = `${matches.length} 条记录`;
  if (!matches.length) {
    const empty = table.insertRow().insertCell();
    empty.colSpan = 6;
    empty.textContent = appointments.length ? '没有符合条件的预约。' : '暂无预约，可先在用户端预约体检。';
  }
  for (const order of matches) {
    const row = table.insertRow();
    row.insertCell().textContent = order.orderId;
    const patient = row.insertCell();
    const phone = document.createElement('span');
    phone.className = 'patient-phone';
    phone.textContent = order.phone;
    patient.append(order.patientName, phone);
    row.insertCell().textContent = order.orderDate;
    row.insertCell().textContent = order.hospitalName + ' / ' + order.packageName;
    const published = order.state === 2;
    row.insertCell().textContent = published ? '已归档' : '待检';
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = published ? '查看报告' : '录入报告';
    button.addEventListener('click', async () => {
      const current = ++detailRequest;
      button.disabled = true;
      try {
        const result = await request(published ? 'reports/' + order.orderId : 'orders/' + order.orderId + '/items');
        if (current !== detailRequest) return;
        notice.textContent = '';
        if (published) showArchive(order, result);
        else showEditor(order, result);
      } catch (error) {
        if (current === detailRequest) notice.textContent = error.message;
      } finally { button.disabled = false; }
    });
    row.insertCell().append(button);
  }
}

function showEditor(order, items) {
  activeOrder = order;
  archive.hidden = true;
  report.reset();
  element('readings').replaceChildren(...items.map(item => {
    const row = document.createElement('div');
    row.className = 'reading';
    row.dataset.item = item.cdId;
    const label = document.createElement('label');
    label.textContent = item.name + (item.unit ? ' / ' + item.unit : '');
    const value = document.createElement('input');
    value.required = true;
    value.maxLength = 100;
    label.append(value);
    const flag = document.createElement('label');
    flag.className = 'flag';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    flag.append(checkbox, ' 标记异常');
    row.append(label, flag);
    return row;
  }));
  element('report-title').textContent = '录入报告 · 订单 ' + order.orderId;
  report.hidden = false;
  report.querySelector('input').focus();
}

function showArchive(order, result) {
  activeOrder = null;
  report.hidden = true;
  element('archive-title').textContent = '归档报告 · 订单 ' + order.orderId;
  element('archive-summary').textContent = result.summary.title;
  element('archive-content').textContent = result.summary.content;
  const readings = element('archive-readings');
  readings.replaceChildren();
  for (const reading of result.readings) {
    const row = readings.insertRow();
    row.insertCell().textContent = reading.name;
    row.insertCell().textContent = [reading.value, reading.unit].filter(Boolean).join(' ');
    row.insertCell().textContent = reading.isError === 1 ? '异常' : '—';
  }
  archive.hidden = false;
  archive.focus();
}

filters.addEventListener('submit', event => {
  event.preventDefault();
  activeFilter = Object.fromEntries([...new FormData(filters)].map(([key, value]) => [key, value.trim()]));
  renderAppointments();
});
filters.addEventListener('reset', () => {
  activeFilter = {};
  renderAppointments();
});
element('refresh').onclick = async () => {
  try { await refreshAppointments(); }
  catch (error) { notice.textContent = error.message; }
};
element('close-archive').onclick = () => { archive.hidden = true; element('refresh').focus(); };
login.onsubmit = async event => {
  event.preventDefault();
  const submit = login.querySelector('[type=submit]');
  submit.disabled = true;
  try {
    const identity = await request('getDoctorByCodeByPass', Object.fromEntries(new FormData(login)));
    token = identity.token;
    element('doctor-name').textContent = identity.name;
    await refreshAppointments();
    login.hidden = true;
    element('workspace').hidden = false;
    notice.textContent = '';
  } catch (error) { notice.textContent = error.message; }
  finally { submit.disabled = false; }
};
element('demo').onclick = () => {
  login.elements.docCode.value = 'DEMO-01';
  login.elements.password.value = 'Doctor-demo';
  login.requestSubmit();
};
element('logout').onclick = () => { reset(); notice.textContent = '已退出。'; };
report.onsubmit = async event => {
  event.preventDefault();
  if (!activeOrder) return;
  const publishingOrder = activeOrder;
  const submit = report.querySelector('[type=submit]');
  submit.disabled = true;
  const readings = [...element('readings').children].map(row => ({
    itemId: Number(row.dataset.item),
    value: row.querySelector('input:not([type])').value,
    flagged: row.querySelector('[type=checkbox]').checked,
  }));
  try {
    await request('reports', {
      orderId: publishingOrder.orderId, title: report.elements.title.value,
      content: report.elements.content.value, readings,
    });
    if (activeOrder === publishingOrder) {
      report.hidden = true;
      activeOrder = null;
    }
    notice.textContent = '报告已发布，用户可按预约订单查看。';
    await refreshAppointments();
  } catch (error) { notice.textContent = error.message; }
  finally { submit.disabled = false; }
};
