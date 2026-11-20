<template>
  <main class="workspace-page" v-loading="loading">
    <div class="page-heading">
      <div>
        <h1>{{ titles[section] }}</h1>
        <p>{{ subtitles[section] }}</p>
      </div>
      <div v-if="section !== 'materials'" class="heading-actions">
        <el-button
          @click="load"
          :disabled="busy || loading"
          aria-label="刷新当前页面数据" title="刷新数据"
          ><AppIcon name="refresh" /></el-button
        ><el-button v-if="section === 'orders'" @click="exportOrders"
          ><AppIcon name="download" />导出
          {{ selected.length ? "已选" : "筛选结果" }}</el-button
        ><el-button
          v-if="section === 'orders' && !operator"
          type="primary"
          @click="openOrderForm"
          ><AppIcon name="plus" />提交订单</el-button
        ><el-button
          v-if="section === 'equipment'"
          type="primary"
          @click="editDevice()"
          ><AppIcon name="plus" />添加设备</el-button
        ><el-button
          v-if="section === 'factories' && user.role === 'superAdmin'"
          type="primary"
          @click="editFactory()"
          ><AppIcon name="plus" />添加工厂</el-button
        >
      </div>
    </div>
    <el-alert
      v-if="loadError"
      :title="loadError"
      type="error"
      show-icon
      :closable="false"
      class="load-error"
    />
    <InventoryWorkspace v-if="section==='materials'" :factories="factories"/><template v-if="section === 'overview'">
      <div class="execution-flow">
        <div class="flow-label">
          <AppIcon name="factory" /><b>生产执行总览</b><span>当前授权范围</span>
        </div>
        <button
          v-for="s in [
            'PENDING',
            'ACCEPTED',
            'PRODUCING',
            'PAUSED',
            'COMPLETED',
          ]"
          :key="s"
          @click="goOrders(s)"
        >
          <i :class="s"></i><span>{{ label(s) }}</span
          ><strong>{{ orders.filter((o) => o.status === s).length }}</strong
          ><AppIcon name="arrow" />
        </button>
      </div>
      <div class="metric-strip">
        <div>
          <span>进行中的订单</span
          ><strong>{{ activeOrders.length }}<small>笔</small></strong>
          <p>{{ pending.length }} 笔等待接单</p>
        </div>
        <div>
          <span>累计合格产量</span
          ><strong>{{ number(good) }}<small>件</small></strong>
          <p>来自已保存的生产报工</p>
        </div>
        <div>
          <span>报工合格率</span
          ><strong
            >{{
              good + rejected
                ? ((good / (good + rejected)) * 100).toFixed(1)
                : "—"
            }}<small v-if="good + rejected">%</small></strong
          >
          <p>
            {{ number(rejected) }} 件不良 /
            {{ number(good + rejected) }} 件总报工
          </p>
        </div>
        <div>
          <span>需要关注</span
          ><strong :class="{ warning: alerts.length }"
            >{{ alerts.length }}<small>项</small></strong
          >
          <p>
            {{ lateOrders.length }} 笔逾期 ·
            {{ openIssues.length }} 项未处理异常
          </p>
        </div>
      </div>
      <div class="overview-grid">
        <section class="panel operations-panel">
          <div class="panel-heading">
            <div>
              <h2>{{ operator ? "设备与当前任务" : "我的生产进度" }}</h2>
              <p>
                {{
                  operator
                    ? "查看设备状态、占用情况和最近排程"
                    : "订单进度由工厂报工更新"
                }}
              </p>
            </div>
            <router-link
              v-if="operator"
              to="/workspace/equipment"
              >查看设备台账 →</router-link
            >
          </div>
          <template v-if="operator"
            ><div
              v-for="d in devices.slice(0, 5)"
              :key="d.id"
              class="workcenter-row"
            >
              <span class="machine-icon"><AppIcon name="device" /></span>
              <div class="workcenter-name">
                <b>{{ d.deviceName }}</b
                ><small
                  >{{ d.location || "未设置位置" }} · {{ d.category }}</small
                >
              </div>
              <div class="workcenter-task">
                <template v-if="running(d.id)"
                  ><b>{{ running(d.id).productname }}</b
                  ><small
                    >MO-{{ pad(running(d.id).orderid) }} · 正在执行</small
                  ></template
                ><template v-else
                  ><b>当前无生产任务</b
                  ><small>{{
                    nextPlan(d.id)
                      ? "下次排程 " + formatTime(nextPlan(d.id).plannedstart)
                      : "暂无后续排程"
                  }}</small></template
                >
              </div>
              <span class="status-badge" :class="d.status">{{
                label(d.status)
              }}</span
              ><button
                class="icon-button"
                @click="editDevice(d)"
                :aria-label="'查看' + d.deviceName"
              >
                <AppIcon name="arrow" />
              </button>
            </div>
            <div v-if="!devices.length" class="empty-state">
              <AppIcon name="device" />
              <h3>先建立设备档案</h3>
              <p>添加设备后，即可为已接订单安排生产时间。</p>
              <el-button type="primary" @click="editDevice()"
                >添加第一台设备</el-button
              >
            </div></template
          ><template v-else
            ><button
              v-for="o in activeOrders.slice(0, 5)"
              :key="o.id"
              class="order-progress-row"
              @click="openDetail(o.id)"
            >
              <div>
                <b>{{ o.productName }}</b
                ><small>MO-{{ pad(o.id) }} · {{ o.factoryName }}</small>
              </div>
              <div class="progress-cell">
                <el-progress
                  :percentage="progress(o)"
                  :stroke-width="5"
                  :show-text="false"
                /><small>{{ o.completedQuantity }} / {{ o.quantity }} 件</small>
              </div>
              <span class="status-badge" :class="o.status">{{
                label(o.status)
              }}</span>
            </button>
            <div v-if="!activeOrders.length" class="empty-state">
              <h3>暂无进行中的订单</h3>
              <p>向工厂提交产品需求，生产进度将在这里呈现。</p>
              <el-button type="primary" @click="openOrderForm"
                >提交订单</el-button
              >
            </div></template
          >
        </section>
        <section class="panel attention-panel">
          <div class="panel-heading">
            <h2>
              需要关注 <span class="count-label">{{ alerts.length }}</span>
            </h2>
          </div>
          <button
            v-for="a in alerts.slice(0, 5)"
            :key="a.key"
            class="attention-row"
            @click="a.orderId ? openDetail(a.orderId, a.tab) : editDevice(a.device)"
          >
            <span :class="['alert-dot', a.type]"></span>
            <div>
              <b>{{ a.title }}</b>
              <p>{{ a.text }}</p>
            </div>
            <AppIcon name="arrow" />
          </button>
          <div v-if="!alerts.length" class="empty-state small">
            <AppIcon name="check" />
            <h3>当前没有待处理提醒</h3>
            <p>逾期订单、异常与到期维护会显示在这里。</p>
          </div>
          <router-link
            v-if="openIssues.length"
            to="/workspace/quality"
            class="panel-footer-link"
            >前往异常中心 →</router-link
          >
        </section>
      </div>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>{{ operator ? "待处理订单" : "最近订单" }}</h2>
            <p>
              {{
                operator ? "接单后安排设备与生产时段" : "查看工厂接单与交付状态"
              }}
            </p>
          </div>
          <router-link to="/workspace/orders">订单中心 →</router-link>
        </div>
        <el-table
          :data="(operator ? pending : orders.slice().reverse()).slice(0, 5)"
          empty-text="暂无待处理订单"
          ><el-table-column label="订单" min-width="120"
            ><template #default="{ row }"
              ><el-button link type="primary" @click="openDetail(row.id)">MO-{{ pad(row.id) }}</el-button></template
            ></el-table-column
          ><el-table-column
            prop="productName"
            label="产品"
            min-width="180"
          /><el-table-column label="优先级" width="110"
            ><template #default="{ row }"
              ><span class="priority" :class="row.priority">{{
                label(row.priority)
              }}</span></template
            ></el-table-column
          ><el-table-column
            prop="quantity"
            label="数量 / 件"
            width="120"
          /><el-table-column prop="dueDate" label="交期" min-width="130"
            ><template #default="{ row }"
              ><span :class="{ overdue: overdue(row) }">{{
                row.dueDate || "未设置"
              }}</span></template
            ></el-table-column
          ><el-table-column label="状态" width="120"
            ><template #default="{ row }"
              ><span class="status-badge" :class="row.status">{{
                label(row.status)
              }}</span></template
            ></el-table-column
          ></el-table
        >
      </section>
    </template>
    <template v-else-if="section === 'orders'">
      <div class="status-tabs">
        <button
          v-for="s in ['ALL', ...statusKeys]"
          :key="s"
          :class="{ active: filters.status === s }" :aria-pressed="filters.status === s"
          @click="
            filters.status = s;
            page = 1;
            saveFilters();
          "
        >
          {{ s === "ALL" ? "全部订单" : label(s) }}
          <span>{{
            s === "ALL"
              ? orders.length
              : orders.filter((o) => o.status === s).length
          }}</span>
        </button>
      </div>
      <section class="panel order-panel">
        <div class="filter-toolbar">
          <el-input
            ref="searchInput"
            v-model="filters.search"
            aria-label="订单搜索"
            placeholder="搜索订单编号、产品或工厂"
            clearable
            @input="
              page = 1;
              saveFilters();
            "
            ><template #prefix><AppIcon name="search" /></template></el-input
          ><el-select
            v-model="filters.priority"
            placeholder="全部优先级"
            @change="
              page = 1;
              saveFilters();
            "
            aria-label="筛选优先级"
            ><el-option label="全部优先级" value="" /><el-option
              v-for="s in ['URGENT', 'HIGH', 'NORMAL']"
              :key="s"
              :label="label(s)"
              :value="s" /></el-select
          ><el-checkbox
            v-model="filters.late"
            @change="
              page = 1;
              saveFilters();
            "
            >仅逾期</el-checkbox
          >
          <div class="toolbar-spacer"></div>
          <el-select v-model="sort" aria-label="订单排序"
            ><el-option label="最新订单" value="new" /><el-option
              label="交期从近到远"
              value="due" /><el-option label="优先级优先" value="priority"
          /></el-select>
          <div class="segmented">
            <button
              :class="{ active: mode === 'table' }"
              :aria-pressed="mode === 'table'"
              @click="setMode('table')"
              aria-label="列表视图"
            >
              列表</button
            ><button
              :class="{ active: mode === 'board' }"
              :aria-pressed="mode === 'board'"
              @click="setMode('board')"
              aria-label="看板视图"
            >
              看板
            </button>
          </div>
        </div>
        <el-table
          v-if="mode === 'table'"
          :data="pagedOrders"
          @selection-change="selected = $event"
          row-key="id"
          empty-text="没有符合筛选条件的订单"
          ><el-table-column type="selection" width="42" /><el-table-column
            label="订单 / 产品"
            min-width="205"
            ><template #default="{ row }"
              ><b class="product-name">{{ row.productName }}</b
              ><small class="cell-secondary"
                >MO-{{ pad(row.id) }} ·
                {{ operator ? row.ownerUsername : row.factoryName }}</small
              ></template
            ></el-table-column
          ><el-table-column
            v-if="user.role === 'superAdmin'"
            prop="factoryName"
            label="工厂"
            min-width="140"
          /><el-table-column label="优先级" width="100"
            ><template #default="{ row }"
              ><span class="priority" :class="row.priority">{{
                label(row.priority)
              }}</span></template
            ></el-table-column
          ><el-table-column label="进度 / 件" min-width="150"
            ><template #default="{ row }"
              ><div class="table-progress">
                <span
                  >{{ number(row.completedQuantity) }}
                  <small>/ {{ number(row.quantity) }}</small></span
                ><el-progress
                  :percentage="progress(row)"
                  :show-text="false"
                  :stroke-width="4"
                /></div></template></el-table-column
          ><el-table-column label="交期" min-width="120"
            ><template #default="{ row }"
              ><span :class="{ overdue: overdue(row) }">{{
                row.dueDate || "未设置"
              }}</span
              ><small v-if="overdue(row)" class="cell-secondary overdue"
                >已逾期</small
              ></template
            ></el-table-column
          ><el-table-column label="状态" width="110"
            ><template #default="{ row }"
              ><span class="status-badge" :class="row.status">{{
                label(row.status)
              }}</span></template
            ></el-table-column
          ><el-table-column label="操作" width="110" fixed="right"
            ><template #default="{ row }"
              ><el-button link type="primary" @click="openDetail(row.id)"
                >查看详情 →</el-button
              ></template
            ></el-table-column
          ></el-table
        >
        <div v-else class="kanban">
          <div v-for="s in statusKeys" :key="s" class="kanban-column">
            <h3>
              <span class="status-dot" :class="s"></span>{{ label(s) }}
              <small>{{
                filteredOrders.filter((o) => o.status === s).length
              }}</small>
            </h3>
            <button
              v-for="o in filteredOrders.filter((o) => o.status === s)"
              :key="o.id"
              class="kanban-card"
              @click="openDetail(o.id)"
            >
              <span class="order-code">MO-{{ pad(o.id) }}</span
              ><span class="priority" :class="o.priority">{{
                label(o.priority)
              }}</span
              ><b>{{ o.productName }}</b>
              <p>{{ o.factoryName }}</p>
              <el-progress
                :percentage="progress(o)"
                :show-text="false"
                :stroke-width="4"
              />
              <div>
                <span>{{ o.completedQuantity }} / {{ o.quantity }} 件</span
                ><time :class="{ overdue: overdue(o) }">{{
                  o.dueDate || "无交期"
                }}</time>
              </div>
            </button>
            <p
              v-if="!filteredOrders.some((o) => o.status === s)"
              class="kanban-empty"
            >
              暂无订单
            </p>
          </div>
        </div>
        <div class="table-footer">
          <span
            >共 {{ filteredOrders.length }} 笔{{
              selected.length ? " · 已选 " + selected.length + " 笔" : ""
            }}</span
          ><el-pagination
            v-if="mode === 'table'"
            v-model:current-page="page"
            :page-size="10"
            layout="prev, pager, next"
            :total="filteredOrders.length"
          />
        </div>
      </section>
    </template>
    <template v-else-if="section === 'schedule'">
      <div class="schedule-info">
        <AppIcon name="schedule" />
        <p>
          同一设备的有效订单不能占用重叠时段。{{
            operator
              ? "点击订单查看或调整排程。"
              : "仅展示自己订单的生产安排。"
          }}所有时间为北京时间。
        </p>
        <el-button v-if="operator" @click="goOrders('ACCEPTED')"
          >安排已接订单 →</el-button
        >
      </div>
      <section class="panel schedule-panel">
        <div class="panel-heading">
          <div>
            <h2>设备生产日历</h2>
            <p>{{ weekStart }} 起的 7 日排程 · 已完成 / 已取消不占用预留时段</p>
          </div>
          <div class="calendar-controls">
            <el-button @click="moveWeek(-7)">← 上一周</el-button
            ><el-button @click="resetWeek">本周</el-button
            ><el-button @click="moveWeek(7)">下一周 →</el-button>
          </div>
        </div>
        <div class="gantt-scroll">
          <div class="gantt">
            <div class="gantt-header">
              <div>设备 / 工作中心</div>
              <div
                v-for="day in weekDays"
                :key="day.date"
                :class="{ today: day.date === today }"
              >
                <b>{{ day.short }}</b
                ><span>{{ day.weekday }}</span>
              </div>
            </div>
            <div v-for="d in calendarDevices" :key="d.id" class="gantt-row">
              <div class="gantt-device">
                <b>{{ d.deviceName }}</b
                ><span>{{ d.factoryName }}</span
                ><small
                  >{{ dayHours(d.id).toFixed(1) }} h 计划 /
                  {{
                    (((d.dailyCapacityMinutes || 480) * 7) / 60).toFixed(0)
                  }}
                  h 周参考产能</small
                >
              </div>
              <div
                class="gantt-track"
                :style="{
                  minHeight:
                    Math.max(
                      120,
                      26 * weekPlans.filter((p) => p.deviceid === d.id).length +
                        26,
                    ) + 'px',
                }"
              >
                <div
                  v-for="day in weekDays"
                  :key="day.date"
                  class="gantt-day"
                  :class="{ today: day.date === today }"
                ></div>
                <button
                  v-for="p in weekPlans.filter((p) => p.deviceid === d.id)"
                  :key="p.orderid"
                  class="gantt-bar"
                  :class="p.status"
                  :style="planStyle(p)"
                  @click="openDetail(p.orderid)"
                  :title="
                    p.productname +
                    ' · ' +
                    formatTime(p.plannedstart) +
                    ' — ' +
                    formatTime(p.plannedend)
                  "
                >
                  <span>MO-{{ pad(p.orderid) }} {{ p.productname }}</span>
                </button>
              </div>
            </div>
            <div v-if="!calendarDevices.length" class="empty-state">
              <h3>暂无设备排程</h3>
              <p>
                {{
                  operator
                    ? "先添加设备，再为已接订单安排时间。"
                    : "工厂完成排程后将在这里展示。"
                }}
              </p>
            </div>
          </div>
        </div>
        <div class="gantt-legend">
          <span><i class="ACCEPTED"></i>已安排</span
          ><span><i class="PRODUCING"></i>生产中</span
          ><span><i class="PAUSED"></i>已暂停</span
          ><span><i class="COMPLETED"></i>已完成</span>
        </div>
      </section>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>派工明细</h2>
            <p>当前七日窗口内的订单安排；点击订单查看执行记录。</p>
          </div>
        </div>
        <el-table
          :data="weekPlans"
          @row-click="(p) => openDetail(p.orderid)"
          class="clickable-table"
          empty-text="当前时间范围内没有排程"
          ><el-table-column label="订单 / 产品" min-width="220"
            ><template #default="{ row }"
              ><b>{{ row.productname }}</b
              ><small class="cell-secondary"
                >MO-{{ pad(row.orderid) }}</small
              ></template
            ></el-table-column
          ><el-table-column
            prop="devicename"
            label="生产设备"
            min-width="200"
          /><el-table-column label="计划开始" min-width="130"
            ><template #default="{ row }">{{
              formatTime(row.plannedstart)
            }}</template></el-table-column
          ><el-table-column label="计划结束" min-width="130"
            ><template #default="{ row }">{{
              formatTime(row.plannedend)
            }}</template></el-table-column
          ><el-table-column label="状态" width="115"
            ><template #default="{ row }"
              ><span class="status-badge" :class="row.status">{{
                label(row.status)
              }}</span></template
            ></el-table-column
          ></el-table
        >
      </section>
      <section class="panel" v-if="operator && unscheduled.length">
        <div class="panel-heading">
          <h2>
            等待排程 <span class="count-label">{{ unscheduled.length }}</span>
          </h2>
        </div>
        <div class="unscheduled-list">
          <button
            v-for="o in unscheduled"
            :key="o.id"
            @click="openDetail(o.id, 'plan')"
          >
            <span class="order-code">MO-{{ pad(o.id) }}</span
            ><b>{{ o.productName }}</b
            ><span>{{ o.quantity }} 件</span
            ><span :class="{ overdue: overdue(o) }"
              >交期 {{ o.dueDate || "未设置" }}</span
            ><AppIcon name="arrow" />
          </button>
        </div>
      </section>
    </template>
    <template v-else-if="section === 'equipment'">
      <div class="equipment-summary">
        <span
          ><i class="status-dot AVAILABLE"></i
          >{{
            devices.filter((d) => d.status === "AVAILABLE").length
          }}
          台可用</span
        ><span
          ><i class="status-dot MAINTENANCE"></i
          >{{
            devices.filter((d) => d.status === "MAINTENANCE").length
          }}
          台维护</span
        ><span
          ><i class="status-dot OFFLINE"></i
          >{{
            devices.filter((d) => d.status === "OFFLINE").length
          }}
          台停机</span
        ><el-input
          v-model="deviceSearch"
          aria-label="设备搜索"
          placeholder="搜索设备、类别或工位"
          clearable
          ><template #prefix><AppIcon name="search" /></template
        ></el-input>
      </div>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>设备台账</h2>
            <p>设备状态由维护记录更新，生产任务由订单执行状态确定。</p>
          </div>
          <span class="muted">{{ filteredDevices.length }} 台设备</span>
        </div>
        <el-table
          :data="filteredDevices"
          empty-text="暂无设备，请添加生产设备"
          ><el-table-column label="设备 / 编号" min-width="240"
            ><template #default="{ row }"
              ><div class="asset-cell">
                <span class="machine-icon"><AppIcon name="device" /></span>
                <div>
                  <b>{{ row.deviceName }}</b
                  ><small class="cell-secondary"
                    >EQ-{{ pad(row.id) }} · {{ row.category }}</small
                  >
                </div>
              </div></template
            ></el-table-column
          ><el-table-column
            prop="location"
            label="车间 / 工位"
            min-width="150"
          /><el-table-column label="可用状态" width="110"
            ><template #default="{ row }"
              ><span class="status-badge" :class="row.status">{{
                label(row.status)
              }}</span></template
            ></el-table-column
          ><el-table-column label="当前任务" min-width="185"
            ><template #default="{ row }"
              ><span v-if="running(row.id)" class="live-task"
                ><i></i>{{ running(row.id).productname }}</span
              ><span v-else class="muted">—</span></template
            ></el-table-column
          ><el-table-column label="参考日产能" width="115"
            ><template #default="{ row }"
              >{{ (row.dailyCapacityMinutes / 60).toFixed(1) }} h</template
            ></el-table-column
          ><el-table-column label="维护日期" width="125"
            ><template #default="{ row }"
              ><span
                :class="{
                  overdue: row.serviceDueDate && row.serviceDueDate <= today,
                }"
                >{{ row.serviceDueDate || "未设置" }}</span
              ></template
            ></el-table-column
          ><el-table-column label="操作" width="220" fixed="right"
            ><template #default="{ row }"
              ><el-button link type="primary" @click="editDevice(row)"
                >编辑档案</el-button
              ><el-button link type="primary" @click.stop="deviceHistory(row)"
                >维护记录</el-button
              ><el-button
                link
                type="danger"
                @click.stop="deleteDevice(row)"
                :disabled="busy"
                >删除</el-button
              ></template
            ></el-table-column
          ></el-table
        >
      </section>
    </template>
    <template v-else-if="section === 'quality'"
      ><div class="status-tabs">
        <button
          v-for="s in ['ALL', 'OPEN', 'RESOLVED']"
          :key="s"
          :class="{ active: issueFilter === s }"
          :aria-pressed="issueFilter === s"
          @click="issueFilter = s"
        >
          {{ s === "ALL" ? "全部异常" : label(s) }}
          <span>{{
            issues.filter((i) => s === "ALL" || i.status === s).length
          }}</span>
        </button>
      </div>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>生产异常台账</h2>
            <p>
              高严重度异常处理后，订单才可继续生产或完成。
            </p>
          </div>
          <el-button v-if="operator" @click="goOrders('ALL')"
            >前往订单登记异常 →</el-button
          >
        </div>
        <el-table
          :data="
            issues.filter(
              (i) => issueFilter === 'ALL' || i.status === issueFilter,
            )
          "
          empty-text="暂无异常记录"
          ><el-table-column label="异常 / 描述" min-width="260"
            ><template #default="{ row }"
              ><b>{{ label(row.type) }} · {{ row.description }}</b
              ><small class="cell-secondary"
                >ISS-{{ pad(row.id) }} · {{ formatTime(row.createdat) }}</small
              ></template
            ></el-table-column
          ><el-table-column label="关联订单" min-width="160"
            ><template #default="{ row }"
              >{{ row.productname
              }}<small class="cell-secondary"
                >MO-{{ pad(row.orderid) }}</small
              ></template
            ></el-table-column
          ><el-table-column label="严重度" width="100"
            ><template #default="{ row }"
              ><span class="priority" :class="row.severity">{{
                label(row.severity)
              }}</span></template
            ></el-table-column
          ><el-table-column label="状态" width="110"
            ><template #default="{ row }"
              ><span class="status-badge" :class="row.status">{{
                label(row.status)
              }}</span></template
            ></el-table-column
          ><el-table-column
            prop="actor"
            label="登记人"
            width="130"
          /><el-table-column label="操作" width="100"
            ><template #default="{ row }"
              ><el-button link type="primary" @click="openDetail(row.orderid, 'issues')">查看异常</el-button></template
            ></el-table-column
          ></el-table
        >
      </section></template
    >
    <template v-else-if="section === 'factories'"
      ><div class="factory-grid">
        <section v-for="f in factories" :key="f.id" class="panel factory-card">
          <div class="factory-card-top">
            <span class="factory-avatar"><AppIcon name="factory" /></span
            ><small>F-{{ pad(f.id) }}</small>
          </div>
          <h2>{{ f.factoryName }}</h2>
          <p>{{ f.factoryDescription || "暂无工厂介绍" }}</p>
          <div class="factory-contact">
            <span>联系邮箱</span
            ><a v-if="f.contactEmail" :href="'mailto:' + f.contactEmail">{{
              f.contactEmail
            }}</a
            ><b v-else>未填写</b>
          </div>
          <footer>
            <el-button
              v-if="!operator"
              type="primary"
              @click="openOrderForm(f.factoryName)"
              >向此工厂下单 <AppIcon name="arrow" /></el-button
            ><el-button
              v-if="
                user.role === 'superAdmin' || user.factoryName === f.factoryName
              "
              @click="editFactory(f)"
              >编辑工厂资料</el-button
            >
          </footer>
        </section>
      </div>
      <div v-if="!factories.length" class="empty-state panel">
        <h3>暂无已注册工厂</h3>
        <p>工厂管理员注册后，将自动建立工厂档案。</p>
      </div></template
    >
    <template v-else-if="section === 'users'"
      ><section class="panel">
        <div class="filter-toolbar">
          <el-input
            v-model="userSearch"
            clearable
            placeholder="搜索账号、姓名或工厂"
            ><template #prefix><AppIcon name="search" /></template></el-input
          ><span class="muted">只展示账号目录，不返回密码。</span>
        </div>
        <el-table
          :data="
            users.filter((u) =>
              [u.username, u.realName, u.factoryName]
                .join(' ')
                .toLowerCase()
                .includes(userSearch.toLowerCase()),
            )
          "
          empty-text="没有匹配的账号"
          ><el-table-column prop="username" label="账号" /><el-table-column
            prop="realName"
            label="姓名" /><el-table-column label="角色"
            ><template #default="{ row }">{{
              roleLabel[row.role]
            }}</template></el-table-column
          ><el-table-column
            prop="factoryName"
            label="所属工厂" /><el-table-column
            prop="contactEmail"
            label="联系邮箱"
        /></el-table></section
    ></template>
    <!-- Order detail: one place for actual work, not separate CRUD pages. -->
    <el-drawer
      v-model="detailOpen"
      :size="drawerSize"
      title="订单详情"
      @close="clearDetail"
      ><div v-loading="detailLoading" class="detail-content">
        <template v-if="detail"
          ><div class="detail-header">
            <div>
              <span class="order-code">MO-{{ pad(detail.order.id) }}</span>
              <h2>{{ detail.order.productName }}</h2>
              <p>
                {{ detail.order.factoryName }}
                <span>· 经销商 {{ detail.order.ownerUsername }}</span>
              </p>
            </div>
          </div>
          <div class="detail-summary">
            <span class="status-badge" :class="detail.order.status">{{
              label(detail.order.status)
            }}</span
            ><span class="priority" :class="detail.order.priority"
              >{{ label(detail.order.priority) }}优先级</span
            ><span :class="{ overdue: overdue(detail.order) }"
              >交期 {{ detail.order.dueDate || "未设置" }}</span
            >
          </div>
          <div class="detail-production">
            <div>
              <span>合格产量</span
              ><b
                >{{ number(detail.order.completedQuantity)
                }}<small> / {{ number(detail.order.quantity) }} 件</small></b
              >
            </div>
            <div>
              <span>累计不良</span
              ><b
                >{{ number(detail.order.rejectedQuantity)
                }}<small> 件</small></b
              >
            </div>
            <el-progress
              :percentage="progress(detail.order)"
              :show-text="false"
              :stroke-width="6"
            />
          </div>
          <p v-if="detail.order.notes" class="order-notes">
            {{ detail.order.notes }}
          </p>
          <div class="detail-actions">
            <template v-if="operator"
              ><el-button
                v-if="detail.order.status === 'PENDING'"
                type="primary"
                :loading="busy"
                @click="transition('ACCEPTED')"
                >接单</el-button
              ><el-button
                v-if="detail.plan && ['ACCEPTED', 'PAUSED'].includes(detail.order.status)"
                type="primary"
                :loading="busy"
                @click="transition('PRODUCING')"
                >{{
                  detail.order.status === "PAUSED" ? "恢复生产" : "开始生产"
                }}</el-button
              ><el-button
                v-if="!detail.plan && detail.order.status === 'ACCEPTED' && detailTab !== 'plan'"
                type="primary"
                @click="detailTab = 'plan'"
                >安排生产</el-button
              ><template v-if="detail.order.status === 'PRODUCING'"
                ><el-button type="primary" @click="detailTab = 'reports'"
                  >登记报工</el-button
                ><el-button @click="pause" :disabled="busy">暂停生产</el-button
                ><el-button @click="complete" :disabled="busy"
                  >完成订单</el-button
                ></template
              ></template
            ><el-button
              v-if="
                detail.order.status === 'PENDING' &&
                (!operator || user.role === 'superAdmin')
              "
              type="danger"
              plain
              @click="cancel"
              :disabled="busy"
              >取消订单</el-button
            ><span
              v-if="['COMPLETED', 'CANCELLED'].includes(detail.order.status)"
              class="muted"
              >订单已关闭，记录保留供追溯。</span
            >
          </div>
          <el-tabs v-model="detailTab"
            ><el-tab-pane label="物料" name="materials" v-if="operator"><OrderMaterials :order="detail.order" @changed="materialChanged"/></el-tab-pane><el-tab-pane label="生产排程" name="plan"
              ><div v-if="detail.plan" class="plan-summary">
                <span class="eyebrow">当前生产安排</span>
                <h3>{{ deviceName(detail.plan.deviceId) }}</h3>
                <p>
                  {{ formatTime(detail.plan.plannedStart) }} →
                  {{ formatTime(detail.plan.plannedEnd) }}
                </p>
                <p v-if="detail.plan.notes">{{ detail.plan.notes }}</p>
              </div>
              <div v-else class="empty-state small">
                <AppIcon name="schedule" />
                <h3>尚未安排生产</h3>
                <p>
                  {{
                    detail.order.status === "PENDING"
                      ? "工厂接单后即可安排设备与时间。"
                      : "需要先完成排程才能开始生产。"
                  }}
                </p>
              </div>
              <form
                v-if="operator && detail.order.status === 'ACCEPTED'"
                @submit.prevent="scheduleOrder"
                class="detail-form"
              >
                <h3>{{ detail.plan ? "调整生产安排" : "安排生产" }}</h3>
                <label
                  >生产设备<el-select
                    v-model="planForm.deviceId"
                    placeholder="选择本工厂可用设备"
                    style="width: 100%"
                    ><el-option
                      v-for="d in devices.filter(
                        (d) => d.factoryName === detail.order.factoryName,
                      )"
                      :key="d.id"
                      :label="d.deviceName + ' · ' + label(d.status)"
                      :value="d.id"
                      :disabled="d.status !== 'AVAILABLE'" /></el-select
                ></label>
                <div class="form-two">
                  <label
                    >计划开始（北京时间）<input
                      v-model="planForm.plannedStart"
                      type="datetime-local"
                      required /></label
                  ><label
                    >计划结束（北京时间）<input
                      v-model="planForm.plannedEnd"
                      type="datetime-local"
                      required
                  /></label>
                </div>
                <label
                  >排程备注<el-input
                    v-model="planForm.notes"
                    type="textarea"
                    maxlength="1000"
                    :rows="2"
                    placeholder="工艺要求、准备事项等" /></label
                ><el-button native-type="submit" type="primary" :loading="busy"
                  >检查冲突并保存排程</el-button
                >
              </form>
              <p class="hint" v-if="operator">
                设备故障或需要调整生产时，先暂停订单。已开始的排程保留为生产依据；请根据设备与交期手动安排生产时间。
              </p></el-tab-pane
            >
            <el-tab-pane
              :label="
                '生产报工' +
                (detail.reports.length ? ' · ' + detail.reports.length : '')
              "
              name="reports"
              ><form
                v-if="operator && detail.order.status === 'PRODUCING'"
                @submit.prevent="submitReport"
                class="detail-form report-form"
              >
                <h3>记录本批次产出</h3>
                <p class="muted">
                  剩余合格数量
                  {{
                    detail.order.quantity - detail.order.completedQuantity
                  }}
                  件。不良数量单独统计，不计入交付进度。
                </p>
                <div class="form-two">
                  <label
                    >本批合格数量<el-input-number
                      v-model="reportForm.goodQuantity"
                      :min="0"
                      :max="
                        detail.order.quantity - detail.order.completedQuantity
                      "
                      :precision="0"
                      controls-position="right" /></label
                  ><label
                    >本批不良数量<el-input-number
                      v-model="reportForm.rejectedQuantity"
                      :min="0"
                      :max="1000000"
                      :precision="0"
                      controls-position="right"
                  /></label>
                </div>
                <label
                  >批次备注<el-input
                    v-model="reportForm.notes"
                    placeholder="例如批次编号、检验说明"
                    maxlength="1000" /></label
                ><el-button type="primary" native-type="submit" :loading="busy"
                  >提交本次报工</el-button
                >
              </form>
              <div
                v-for="r in detail.reports"
                :key="r.id"
                class="report-record"
              >
                <div>
                  <b>合格 {{ r.goodQuantity }} 件</b
                  ><span :class="{ overdue: r.rejectedQuantity }"
                    >不良 {{ r.rejectedQuantity }} 件</span
                  >
                </div>
                <p v-if="r.notes">{{ r.notes }}</p>
                <small>{{ r.actor }} · {{ formatTime(r.createdAt) }}</small>
              </div>
              <div v-if="!detail.reports.length" class="empty-state small">
                <h3>还没有报工记录</h3>
                <p>开始生产后，工厂可分批登记实际产出。</p>
              </div></el-tab-pane
            >
            <el-tab-pane
              :label="
                '异常处理' +
                (detail.issues.filter((i) => i.status === 'OPEN').length
                  ? ' · ' +
                    detail.issues.filter((i) => i.status === 'OPEN').length
                  : '')
              "
              name="issues"
              ><div v-for="i in detail.issues" :key="i.id" class="issue-record">
                <div>
                  <span class="priority" :class="i.severity"
                    >{{ label(i.severity) }}严重度</span
                  ><span class="status-badge" :class="i.status">{{
                    label(i.status)
                  }}</span>
                </div>
                <h3>{{ label(i.type) }} · {{ i.description }}</h3>
                <small>{{ i.actor }} · {{ formatTime(i.createdAt) }}</small>
                <p v-if="i.resolution" class="resolution">
                  处理结果：{{ i.resolution
                  }}<small
                    >{{ i.resolvedBy }} · {{ formatTime(i.resolvedAt) }}</small
                  >
                </p>
                <el-button
                  v-if="operator && i.status === 'OPEN'"
                  size="small"
                  @click="resolveIssue(i)"
                  :disabled="busy"
                  >记录处理结果</el-button
                >
              </div>
              <div v-if="!detail.issues.length" class="empty-state small">
                <h3>暂无异常记录</h3>
                <p>设备、质量、物料与工艺问题都可在此登记。</p>
              </div>
              <form
                v-if="
                  operator &&
                  !['COMPLETED', 'CANCELLED'].includes(detail.order.status)
                "
                class="detail-form"
                @submit.prevent="submitIssue"
              >
                <h3>登记新异常</h3>
                <div class="form-two">
                  <label
                    >异常类型<el-select v-model="issueForm.type"
                      ><el-option
                        v-for="v in [
                          'QUALITY',
                          'EQUIPMENT',
                          'MATERIAL',
                          'PROCESS',
                        ]"
                        :key="v"
                        :label="label(v)"
                        :value="v" /></el-select></label
                  ><label
                    >严重程度<el-select v-model="issueForm.severity"
                      ><el-option
                        v-for="v in ['LOW', 'MEDIUM', 'HIGH']"
                        :key="v"
                        :label="label(v)"
                        :value="v" /></el-select
                  ></label>
                </div>
                <label
                  >问题描述<el-input
                    v-model.trim="issueForm.description"
                    type="textarea"
                    required
                    maxlength="2000"
                    :rows="3"
                /></label>
                <p class="hint">
                  高严重度异常会阻止开始 /
                  恢复生产和完成订单。如需立即停产，请使用“暂停生产”。
                </p>
                <el-button native-type="submit" type="primary" :loading="busy"
                  >保存异常记录</el-button
                >
              </form></el-tab-pane
            >
            <el-tab-pane label="操作记录" name="history"
              ><ol class="activity-timeline">
                <li v-for="h in detail.history.slice().reverse()" :key="h.id">
                  <i></i>
                  <div>
                    <b>{{ eventTitle(h) }}</b
                    ><small
                      >{{ formatTime(h.createdat) }} · {{ h.actor }}</small
                    >
                    <p v-if="h.note">{{ h.note }}</p>
                  </div>
                </li>
              </ol></el-tab-pane
            ></el-tabs
          ></template
        >
        <div v-else-if="!detailLoading" class="empty-state">
          <h3>无法读取订单</h3>
          <p>请关闭后重试，或刷新数据。</p>
        </div>
      </div></el-drawer
    >
    <el-dialog
      v-model="orderFormOpen"
      title="提交生产订单"
      width="540px"
      :close-on-click-modal="false"
      ><form class="modal-form" @submit.prevent="createOrder">
        <label
          >合作工厂<el-select
            v-model="orderForm.factoryName"
            placeholder="选择工厂"
            ><el-option
              v-for="f in factories"
              :key="f.id"
              :label="f.factoryName"
              :value="f.factoryName" /></el-select></label
        ><label
          >产品名称<el-input
            v-model.trim="orderForm.productName"
            required
            maxlength="100"
            placeholder="例如：铝合金精密连接件"
        /></label>
        <div class="form-two">
          <label
            >数量 / 件<el-input-number
              v-model="orderForm.quantity"
              :min="1"
              :max="1000000"
              :precision="0"
              controls-position="right" /></label
          ><label
            >交期<el-date-picker
              v-model="orderForm.dueDate"
              type="date"
              value-format="YYYY-MM-DD"
              :disabled-date="pastDate"
              placeholder="选择日期"
          /></label>
        </div>
        <label
          >优先级<el-select v-model="orderForm.priority"
            ><el-option
              v-for="v in ['NORMAL', 'HIGH', 'URGENT']"
              :key="v"
              :label="label(v)"
              :value="v" /></el-select></label
        ><label
          >生产要求（选填）<el-input
            v-model="orderForm.notes"
            type="textarea"
            :rows="3"
            maxlength="2000"
            show-word-limit
        /></label>
        <div class="modal-footer">
          <el-button @click="orderFormOpen = false" :disabled="busy"
            >返回</el-button
          ><el-button type="primary" native-type="submit" :loading="busy"
            >提交订单</el-button
          >
        </div>
      </form></el-dialog
    >
    <el-dialog
      v-model="deviceFormOpen"
      :title="deviceForm.id ? '编辑设备档案' : '添加生产设备'"
      width="600px"
      :close-on-click-modal="false"
      ><form class="modal-form" @submit.prevent="saveDevice">
        <label v-if="user.role === 'superAdmin'"
          >所属工厂<el-select
            v-model="deviceForm.factoryName"
            :disabled="!!deviceForm.id"
            ><el-option
              v-for="f in factories"
              :key="f.id"
              :label="f.factoryName"
              :value="f.factoryName" /></el-select></label
        ><label
          >设备名称<el-input
            v-model.trim="deviceForm.deviceName"
            required
            maxlength="100"
        /></label>
        <div class="form-two">
          <label
            >设备类别<el-input
              v-model.trim="deviceForm.category"
              required
              maxlength="100" /></label
          ><label
            >位置 / 工位<el-input
              v-model="deviceForm.location"
              maxlength="100"
              placeholder="例如 A 车间 · 03 工位"
          /></label>
        </div>
        <div class="form-two">
          <label
            >状态<el-select v-model="deviceForm.status"
              ><el-option
                v-for="v in ['AVAILABLE', 'MAINTENANCE', 'OFFLINE']"
                :key="v"
                :label="label(v)"
                :value="v" /></el-select></label
          ><label
            >参考日产能 / 分钟<el-input-number
              v-model="deviceForm.dailyCapacityMinutes"
              :min="30"
              :max="1440"
              :step="30"
              :precision="0"
              controls-position="right"
          /></label>
        </div>
        <label
          >下次维护日期<el-date-picker
            v-model="deviceForm.serviceDueDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            clearable /></label
        ><label
          >{{
            deviceForm.status === "AVAILABLE"
              ? "维护 / 变更说明（选填）"
              : "维护或停机原因（必填）"
          }}<el-input
            v-model.trim="deviceForm.maintenanceNote"
            :required="deviceForm.status !== 'AVAILABLE'"
            maxlength="1000" /></label
        ><label
          >设备说明<el-input
            v-model="deviceForm.deviceDescription"
            type="textarea"
            maxlength="1000"
            :rows="2"
        /></label>
        <div class="modal-footer">
          <el-button @click="deviceFormOpen = false" :disabled="busy"
            >返回</el-button
          ><el-button type="primary" native-type="submit" :loading="busy"
            >保存设备</el-button
          >
        </div>
      </form></el-dialog
    >
    <el-dialog v-model="historyOpen" title="设备状态与维护记录" width="620px"
      ><div
        v-for="h in maintenanceHistory"
        :key="h.deviceversion"
        class="report-record"
      >
        <b>{{ label(h.status) }}</b>
        <p>{{ h.note || "更新设备档案" }}</p>
        <small>{{ h.actor }} · {{ formatTime(h.createdat) }}</small>
      </div>
      <el-empty
        v-if="!maintenanceHistory.length"
        description="该设备暂无状态记录"
    /></el-dialog>
    <el-dialog
      v-model="factoryFormOpen"
      :title="factoryForm.id ? '编辑工厂资料' : '添加工厂'"
      width="520px"
      :close-on-click-modal="false"
      ><form class="modal-form" @submit.prevent="saveFactory">
        <label
          >工厂名称<el-input
            v-model.trim="factoryForm.factoryName"
            required
            maxlength="100"
            :disabled="!!factoryForm.id" /></label
        ><label
          >工厂简介<el-input
            v-model="factoryForm.factoryDescription"
            type="textarea"
            maxlength="1000"
            :rows="4" /></label
        ><label
          >联系邮箱<el-input
            v-model="factoryForm.contactEmail"
            type="email"
            maxlength="200"
        /></label>
        <div class="modal-footer">
          <el-button @click="factoryFormOpen = false" :disabled="busy"
            >返回</el-button
          ><el-button type="primary" native-type="submit" :loading="busy"
            >保存工厂资料</el-button
          >
        </div>
      </form></el-dialog
    >
  </main>
</template>
<script>
import axios from "axios";
import InventoryWorkspace from "../components/InventoryWorkspace.vue";
import OrderMaterials from "../components/OrderMaterials.vue";
import AppIcon from "../components/AppIcon.vue";
import {
  label,
  statusKeys,
  formatTime,
  parseTime,
  beijingDate,
  beijingWeekStart,
  progress,
  overdue,
  hours,
  errorMessage,
  downloadCsv,
} from "../utils/operations";
export default {
  components: { InventoryWorkspace, OrderMaterials, AppIcon },
  data() {
    let mode = "table";
    try {
      mode =
        localStorage.getItem("manu-view-" + this.$store.state.user?.username) ||
        "table";
    } catch {}
    return {
      titles: { materials:"物料与 BOM",
        overview: "运营概览",
        orders: "订单中心",
        schedule: "生产排程",
        equipment: "设备资产",
        quality: "异常与质量",
        factories: "工厂网络",
        users: "账号目录",
      },
      subtitles: { materials:"库存、产品用料与生产领料流水",
        overview: "从订单、设备与现场记录，了解当前生产情况。",
        orders: "查询订单、接单状态、生产进度与交期。",
        schedule: "把订单安排到合适的设备与时间。",
        equipment: "维护设备档案、可用状态与维护计划。",
        quality: "记录问题、跟进处理，保留生产依据。",
        factories: "找到合作工厂，维护协作资料。",
        users: "查看平台账号、角色与工厂归属。",
      },
      roleLabel: {
        superAdmin: "平台管理员",
        factoryAdmin: "工厂管理员",
        distributor: "经销商",
      },
      statusKeys,
      orders: [],
      factories: [],
      devices: [],
      plans: [],
      issues: [],
      users: [],
      loading: false,
      busy: false,
      loadError: "",
      filters: { search: "", status: "ALL", priority: "", late: false },
      sort: "new",
      page: 1,
      selected: [],
      mode,
      deviceSearch: "",
      userSearch: "",
      issueFilter: "ALL",
      weekStart: beijingWeekStart(),
      detail: null,
      detailOpen: false,
      detailLoading: false,
      detailTab: "plan",
      planForm: {},
      reportForm: { goodQuantity: 0, rejectedQuantity: 0, notes: "" },
      issueForm: { type: "QUALITY", severity: "MEDIUM", description: "" },
      orderFormOpen: false,
      orderForm: {},
      deviceFormOpen: false,
      deviceForm: {},
      factoryFormOpen: false,
      factoryForm: {},
      historyOpen: false,
      maintenanceHistory: [],
      drawerSize: Math.min(680, window.innerWidth) + "px",
      detailRequest: 0,
    };
  },
  computed: {
    user() {
      return this.$store.state.user || { role: "distributor", username: "" };
    },
    section() {
      return this.$route.params.section || "overview";
    },
    operator() {
      return this.user?.role !== "distributor";
    },
    today() {
      return beijingDate();
    },
    pending() {
      return this.orders.filter((o) => o.status === "PENDING");
    },
    activeOrders() {
      return this.orders.filter(
        (o) => !["COMPLETED", "CANCELLED"].includes(o.status),
      );
    },
    lateOrders() {
      return this.orders.filter((o) => overdue(o));
    },
    good() {
      return this.orders.reduce((s, o) => s + (o.completedQuantity || 0), 0);
    },
    rejected() {
      return this.orders.reduce((s, o) => s + (o.rejectedQuantity || 0), 0);
    },
    openIssues() {
      return this.issues.filter((i) => i.status === "OPEN");
    },
    unscheduled() {
      return this.orders.filter(
        (o) =>
          o.status === "ACCEPTED" &&
          !this.plans.some((p) => p.orderid === o.id),
      );
    },
    filteredOrders() {
      const q = this.filters.search.toLowerCase().trim();
      return this.orders
        .filter(
          (o) =>
            (this.filters.status === "ALL" ||
              o.status === this.filters.status) &&
            (!this.filters.priority || o.priority === this.filters.priority) &&
            (!this.filters.late || overdue(o)) &&
            (!q ||
              [
                o.productName,
                o.factoryName,
                o.ownerUsername,
                "MO-" + this.pad(o.id),
                String(o.id),
              ]
                .join(" ")
                .toLowerCase()
                .includes(q)),
        )
        .sort((a, b) =>
          this.sort === "due"
            ? (a.dueDate || "9999").localeCompare(b.dueDate || "9999") ||
              b.id - a.id
            : this.sort === "priority"
              ? ["URGENT", "HIGH", "NORMAL"].indexOf(a.priority) -
                  ["URGENT", "HIGH", "NORMAL"].indexOf(b.priority) ||
                b.id - a.id
              : b.id - a.id,
        );
    },
    pagedOrders() {
      return this.filteredOrders.slice((this.page - 1) * 10, this.page * 10);
    },
    filteredDevices() {
      return this.devices.filter((d) =>
        [d.deviceName, d.category, d.location, d.factoryName]
          .join(" ")
          .toLowerCase()
          .includes(this.deviceSearch.toLowerCase()),
      );
    },
    alerts() {
      return [
        ...this.lateOrders.map((o) => ({
          key: "o" + o.id,
          type: "danger",
          title: "交期已逾期 · " + o.productName,
          text: "MO-" + this.pad(o.id) + " · 约定 " + o.dueDate,
          orderId: o.id,
        })),
        ...this.openIssues.map((i) => ({
          key: "i" + i.id,
          type: i.severity === "HIGH" ? "danger" : "warn",
          title: label(i.type) + "异常 · " + i.productname,
          text: i.description,
          orderId: i.orderid,
          tab: "issues",
        })),
        ...this.devices
          .filter((d) => d.serviceDueDate && d.serviceDueDate <= this.today)
          .map((d) => ({
            key: "d" + d.id,
            type: "warn",
            title: "维护已到期 · " + d.deviceName,
            text: "计划维护日期 " + d.serviceDueDate,
            device: d,
          })),
      ];
    },
    weekDays() {
      const a = parseTime(this.weekStart + "T00:00:00");
      return Array.from({ length: 7 }, (_, i) => {
        const d = new Date(a + i * 86400000);
        const date = beijingDate(d);
        return {
          date,
          short: date.slice(5).replace("-", "/"),
          weekday: new Intl.DateTimeFormat("zh-CN", {
            timeZone: "Asia/Shanghai",
            weekday: "short",
          }).format(d),
        };
      });
    },
    weekPlans() {
      const a = parseTime(this.weekStart + "T00:00:00");
      return this.plans.filter(
        (p) =>
          parseTime(p.plannedstart) < a + 7 * 86400000 &&
          parseTime(p.plannedend) > a,
      );
    },
    calendarDevices() {
      if (this.operator) return this.devices;
      const map = new Map();
      this.plans.forEach((p) =>
        map.set(p.deviceid, {
          id: p.deviceid,
          deviceName: p.devicename,
          factoryName: p.factoryname,
          dailyCapacityMinutes: 480,
        }),
      );
      return [...map.values()];
    },
  },
  watch: {
    "filteredOrders.length"(count) {
      this.page = Math.min(this.page, Math.max(1, Math.ceil(count / 10)));
    },
    "$route.params.section"() {
      this.selected = [];
      this.page = 1;
      this.readFilters();
    },
    "$route.query"() {
      this.readFilters();
    },
  },
  mounted() {
    this.readFilters();
    this.load();
    window.addEventListener("keydown", this.shortcut);
    window.addEventListener("resize", this.resize);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.shortcut);
    window.removeEventListener("resize", this.resize);
    this.detailRequest++;
  },
  methods: { async materialChanged(){await this.fetchDetail(this.detail.order.id);await this.load();},
    label,
    formatTime,
    progress,
    overdue,
    number: (n) => Number(n || 0).toLocaleString("zh-CN"),
    pad: (n) => String(n).padStart(4, "0"),
    resize() {
      this.drawerSize = Math.min(680, window.innerWidth) + "px";
    },
    shortcut(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (this.section !== "orders")
          this.$router
            .push("/workspace/orders")
            .then(() => this.$nextTick(() => this.$refs.searchInput?.focus()));
        else this.$refs.searchInput?.focus();
      }
    },
    async load() {
      if (this.loading) return;
      this.loading = true;
      this.loadError = "";
      try {
        const requests = [
          ["orders", "/orders"],
          ["factories", "/factories"],
          ["plans", "/operations/plans"],
          ["issues", "/operations/issues"],
        ];
        if (this.operator) requests.push(["devices", "/devices/allDevices"]);
        if (this.user.role === "superAdmin")
          requests.push(["users", "/users/allUsers"]);
        const results = await Promise.allSettled(
          requests.map(([, p]) => axios.get("/api" + p)),
        );
        const failed = [];
        results.forEach((r, i) => {
          if (r.status === "fulfilled") this[requests[i][0]] = r.value.data;
          else failed.push(requests[i][0]);
        });
        if (failed.length)
          this.loadError =
            "部分数据未能刷新，显示的可能是上次结果。请检查服务后点击刷新。";

      } finally {
        this.loading = false;
      }
    },
    readFilters() {
      if (this.section !== "orders") return;
      const q = this.$route.query;
      this.filters = {
        search: String(q.q || ""),
        status: statusKeys.includes(q.status) ? q.status : "ALL",
        priority: ["NORMAL", "HIGH", "URGENT"].includes(q.priority)
          ? q.priority
          : "",
        late: q.late === "1",
      };
    },
    saveFilters() {
      const f = this.filters;
      this.$router.replace({
        query: {
          ...(f.search ? { q: f.search } : {}),
          ...(f.status !== "ALL" ? { status: f.status } : {}),
          ...(f.priority ? { priority: f.priority } : {}),
          ...(f.late ? { late: "1" } : {}),
        },
      });
    },
    setMode(value) {
      this.mode = value;
      this.selected = [];
      try {
        localStorage.setItem("manu-view-" + this.user.username, value);
      } catch {}
    },
    goOrders(status) {
      this.$router.push({
        path: "/workspace/orders",
        query: status === "ALL" ? {} : { status },
      });
    },
    async perform(fn, success) {
      if (this.busy) return false;
      this.busy = true;
      try {
        await fn();
        this.$message.success(success);
        await this.load();
        if (this.detailOpen && this.detail)
          await this.fetchDetail(this.detail.order.id);
        return true;
      } catch (e) {
        this.$message.error(errorMessage(e));
        if (e.response?.status === 409) {
          await this.load();
          if (this.detailOpen && this.detail)
            await this.fetchDetail(this.detail.order.id);
        }
        return false;
      } finally {
        this.busy = false;
      }
    },
    async fetchDetail(id) {
      const token = ++this.detailRequest;
      this.detailLoading = true;
      try {
        const { data } = await axios.get("/api/orders/" + id);
        if (token === this.detailRequest) {
          this.detail = data;
          this.planForm = data.plan
            ? { ...data.plan }
            : { deviceId: null, plannedStart: "", plannedEnd: "", notes: "" };
        }
      } catch (e) {
        if (token === this.detailRequest) {
          this.detail = null;
          this.$message.error(errorMessage(e));
        }
      } finally {
        if (token === this.detailRequest) this.detailLoading = false;
      }
    },
    clearDetail() {
      this.detailRequest++;
      this.detailLoading = false;
      this.detail = null;
    },
    async openDetail(id, tab = "plan") {
      this.detail = null;
      this.detailTab = tab;
      this.detailOpen = true;
      this.reportForm = { goodQuantity: 0, rejectedQuantity: 0, notes: "" };
      this.issueForm = { type: "QUALITY", severity: "MEDIUM", description: "" };
      await this.fetchDetail(id);
    },
    deviceName(id) {
      return (
        this.devices.find((d) => d.id === id)?.deviceName ||
        this.plans.find((p) => p.deviceid === id)?.devicename ||
        "设备 #" + id
      );
    },
    running(id) {
      return this.plans.find(
        (p) => p.deviceid === id && p.status === "PRODUCING",
      );
    },
    nextPlan(id) {
      return this.plans.find(
        (p) =>
          p.deviceid === id &&
          p.status === "ACCEPTED" &&
          parseTime(p.plannedend) > Date.now(),
      );
    },
    dayHours(id) {
      const a = parseTime(this.weekStart + "T00:00:00");
      return this.weekPlans
        .filter(
          (p) =>
            p.deviceid === id && !["CANCELLED", "COMPLETED"].includes(p.status),
        )
        .reduce((n, p) => n + hours(p, a, a + 7 * 86400000), 0);
    },
    planStyle(p) {
      const a = parseTime(this.weekStart + "T00:00:00"),
        span = 7 * 86400000;
      const left = Math.max(0, ((parseTime(p.plannedstart) - a) / span) * 100),
        right = Math.min(100, ((parseTime(p.plannedend) - a) / span) * 100);
      const list = this.weekPlans.filter((q) => q.deviceid === p.deviceid),
        index = list.findIndex((q) => q.orderid === p.orderid);
      return {
        left: left + "%",
        width: Math.max(0.35, right - left) + "%",
        top: 16 + index * 26 + "px",
      };
    },
    moveWeek(days) {
      this.weekStart = beijingDate(
        new Date(parseTime(this.weekStart + "T00:00:00") + days * 86400000),
      );
    },
    resetWeek() {
      this.weekStart = beijingWeekStart();
    },
    async transition(status, note) {
      const o = this.detail.order;
      return this.perform(
        () =>
          axios.patch("/api/orders/" + o.id + "/status", {
            status,
            version: o.version,
            note,
          }),
        "订单已更新",
      );
    },
    async pause() {
      try {
        const { value } = await this.$prompt(
          "说明暂停原因，将保存到操作记录。",
          "暂停生产",
          {
            inputType: "textarea",
            inputValidator: (v) => !!v?.trim() || "请填写暂停原因",
            confirmButtonText: "暂停生产",
            cancelButtonText: "返回",
          },
        );
        await this.transition("PAUSED", value);
      } catch {}
    },
    async complete() {
      try {
        await this.$confirm(
          "确认合格产量已达到订单数量，并完成最终核对？",
          "完成订单",
          {
            confirmButtonText: "确认完成",
            cancelButtonText: "返回",
            type: "warning",
          },
        );
        await this.transition("COMPLETED");
      } catch {}
    },
    async cancel() {
      try {
        await this.$confirm(
          "取消后保留订单与操作记录，无法继续生产。",
          "取消订单",
          {
            confirmButtonText: "确认取消订单",
            cancelButtonText: "返回",
            type: "warning",
          },
        );
        await this.transition("CANCELLED");
      } catch {}
    },
    async scheduleOrder() {
      if (
        !this.planForm.deviceId ||
        !this.planForm.plannedStart ||
        !this.planForm.plannedEnd
      ) {
        this.$message.error("请选择设备并填写开始、结束时间");
        return;
      }
      const o = this.detail.order;
      await this.perform(
        () =>
          axios.put("/api/orders/" + o.id + "/plan", {
            ...this.planForm,
            version: o.version,
          }),
        "生产排程已保存",
      );
    },
    async submitReport() {
      const o = this.detail.order;
      if (
        await this.perform(
          () =>
            axios.post("/api/orders/" + o.id + "/reports", {
              ...this.reportForm,
              version: o.version,
            }),
          "本批次报工已保存",
        )
      )
        this.reportForm = { goodQuantity: 0, rejectedQuantity: 0, notes: "" };
    },
    async submitIssue() {
      const o = this.detail.order;
      if (
        await this.perform(
          () =>
            axios.post("/api/orders/" + o.id + "/issues", {
              ...this.issueForm,
              version: o.version,
            }),
          "异常已登记",
        )
      )
        this.issueForm.description = "";
    },
    async resolveIssue(i) {
      try {
        const { value } = await this.$prompt(
          "填写已采取的处理措施和结果。",
          "记录异常处理结果",
          {
            inputType: "textarea",
            inputValidator: (v) => !!v?.trim() || "请填写处理结果",
            confirmButtonText: "保存处理结果",
            cancelButtonText: "返回",
          },
        );
        await this.perform(
          () =>
            axios.patch("/api/operations/issues/" + i.id, {
              version: i.version,
              orderVersion: this.detail.order.version,
              resolution: value,
            }),
          "异常已处理",
        );
      } catch {}
    },
    eventTitle(h) {
      return (
        {
          SCHEDULE: "安排 / 调整生产",
          REPORT: "登记生产报工",
          ISSUE: "登记生产异常",
          RESOLVE: "记录异常处理", RESERVE:"预留物料", RELEASE:"释放物料",
        }[h.eventtype] ||
        (h.fromstatus
          ? label(h.fromstatus) + " → " + label(h.tostatus)
          : "创建订单")
      );
    },
    openOrderForm(factory) {
      this.orderForm = {
        factoryName: factory || "",
        productName: "",
        quantity: 1,
        priority: "NORMAL",
        dueDate: null,
        notes: "",
      };
      this.orderFormOpen = true;
    },
    pastDate(d) {
      return beijingDate(d) < this.today;
    },
    async createOrder() {
      if (!this.orderForm.factoryName) {
        this.$message.error("请选择合作工厂");
        return;
      }
      if (
        await this.perform(
          () => axios.post("/api/orders", this.orderForm),
          "订单已提交，等待工厂接单",
        )
      ) {
        this.orderFormOpen = false;
        this.$router.push("/workspace/orders");
      }
    },
    editDevice(d) {
      this.deviceForm = d
        ? { ...d }
        : {
            deviceName: "",
            deviceDescription: "",
            factoryName: this.user.factoryName || "",
            status: "AVAILABLE",
            category: "加工设备",
            location: "",
            dailyCapacityMinutes: 480,
            serviceDueDate: null,
            maintenanceNote: "",
            version: 0,
          };
      this.deviceFormOpen = true;
    },
    async saveDevice() {
      const d = this.deviceForm;
      if (!d.factoryName) {
        this.$message.error("请选择所属工厂");
        return;
      }
      if (
        await this.perform(
          () =>
            d.id
              ? axios.put("/api/devices/" + d.id, d)
              : axios.post("/api/devices", d),
          "设备档案已保存",
        )
      )
        this.deviceFormOpen = false;
    },
    async deleteDevice(d) {
      try {
        await this.$confirm(
          "删除设备“" +
            d.deviceName +
            "”？已被排程引用的设备无法删除，可将其设为停机。",
          "删除设备",
          {
            confirmButtonText: "确认删除",
            cancelButtonText: "返回",
            type: "warning",
          },
        );
        await this.perform(
          () => axios.delete("/api/devices/" + d.id),
          "设备已删除",
        );
      } catch {}
    },
    async deviceHistory(d) {
      try {
        const { data } = await axios.get("/api/devices/" + d.id + "/history");
        this.maintenanceHistory = data;
        this.historyOpen = true;
      } catch (e) {
        this.$message.error(errorMessage(e));
      }
    },
    editFactory(f) {
      this.factoryForm = f
        ? { ...f }
        : { factoryName: "", factoryDescription: "", contactEmail: "" };
      this.factoryFormOpen = true;
    },
    async saveFactory() {
      const f = this.factoryForm;
      if (
        await this.perform(
          () =>
            f.id
              ? axios.put("/api/factories/" + f.id, f)
              : axios.post("/api/factories", f),
          "工厂资料已保存",
        )
      )
        this.factoryFormOpen = false;
    },
    exportOrders() {
      const ids = new Set(this.filteredOrders.map((o) => o.id));
      const rows = this.selected.length
        ? this.selected.filter((o) => ids.has(o.id))
        : this.filteredOrders;
      if (!rows.length) {
        this.$message.info("当前没有可导出的订单");
        return;
      }
      downloadCsv(
        [
          [
            "订单编号",
            "产品",
            "工厂",
            "经销商",
            "状态",
            "优先级",
            "订单数量",
            "合格数量",
            "不良数量",
            "交期",
          ],
          ...rows.map((o) => [
            "MO-" + this.pad(o.id),
            o.productName,
            o.factoryName,
            o.ownerUsername,
            label(o.status),
            label(o.priority),
            o.quantity,
            o.completedQuantity,
            o.rejectedQuantity,
            o.dueDate,
          ]),
        ],
        "制造订单_" + this.today + ".csv",
      );
      this.$message.success("已导出 " + rows.length + " 笔订单");
    },
  },
};
</script>

<style scoped>.order-replay-controls{padding:12px;border-block:1px solid #ced6de}.order-replay-controls button,.order-replay-controls select{margin:4px;padding:6px}.order-replay-controls p{margin:6px 0}</style>
