<script setup>
import { ref, computed, watch } from "vue";
import { useStore } from "vuex";
import axios from "axios";
import { ElMessage } from "element-plus";
import { errorMessage } from "../utils/operations";
const props = defineProps({ factories: Array }),
  store = useStore(),
  factory = ref(store.state.user.factoryName || ""),
  data = ref({ materials: [], boms: [], ledger: [] }),
  loading = ref(false),
  error = ref(""),
  busy = ref(false),
  tab = ref("stock"),
  materialOpen = ref(false),
  bomOpen = ref(false),
  receiptOpen = ref(false);
const material = ref({ sku: "", name: "", unit: "件" }),
  bom = ref({
    productName: "",
    version: 0,
    lines: [{ materialId: null, units: 1 }],
  }),
  receipt = ref({ id: 0, quantity: 1, requestId: "" });
const reconciliation = ref(null);
const ledgerSku = ref("");
const visibleLedger = computed(() => ledgerSku.value
  ? data.value.ledger.filter(entry => entry.sku === ledgerSku.value)
  : data.value.ledger);
function showLedger(sku) {
  ledgerSku.value = sku;
  tab.value = "ledger";
}
const auditLabels = {STOCK_BOUNDS:"库存数量约束异常",STOCK_LEDGER_MISMATCH:"余额与收发流水不一致",RESERVATION_LEDGER_MISMATCH:"预留与收发流水不一致",ACTIVE_RESERVATION_MISMATCH:"预留与有效订单不一致"};
async function reconcile() {
  if (!factory.value || busy.value || loading.value) return;
  busy.value = true; error.value = "";
  try { reconciliation.value = (await axios.get("/api/inventory/reconciliation", {params: {factoryName: factory.value}})).data; }
  catch(e) { error.value = errorMessage(e); }
  finally { busy.value = false; }
}
const kinds = {
  RECEIPT: "入库",
  RESERVE: "预留",
  RELEASE: "释放",
  ISSUE: "生产领料",
};
let inventoryRequest = 0;
async function load() {
  const name = factory.value;
  if (!name) return;
  const request = ++inventoryRequest;
  loading.value = true;
  reconciliation.value = null;
  error.value = "";
  try {
    const result = await axios.get("/api/inventory", { params: { factoryName: name } });
    if (request === inventoryRequest && name === factory.value) data.value = result.data;
  } catch (e) {
    if (request === inventoryRequest && name === factory.value) error.value = errorMessage(e);
  } finally {
    if (request === inventoryRequest) loading.value = false;
  }
}
watch(factory, () => {
  ledgerSku.value = "";
  data.value = { materials: [], boms: [], ledger: [] };
  load();
}, { immediate: true });
watch(
  () => props.factories,
  () => {
    if (!factory.value && props.factories?.length)
      factory.value = props.factories[0].factoryName;
  },
  { immediate: true },
);
async function run(fn) {
  if (busy.value) return false;
  busy.value = true;
  error.value = "";
  try {
    await fn();
    await load();
    ElMessage.success("已保存");
    return true;
  } catch (e) {
    error.value = errorMessage(e);
    return false;
  } finally {
    busy.value = false;
  }
}
async function saveMaterial() {
  if (
    await run(() =>
      axios.post("/api/inventory/materials", {
        ...material.value,
        factoryName: factory.value,
      }),
    )
  )
    materialOpen.value = false;
}
function receive(m) {
  receipt.value = { id: m.id, quantity: 1, requestId: crypto.randomUUID() };
  receiptOpen.value = true;
}
async function saveReceipt() {
  const r = receipt.value;
  if (
    await run(() =>
      axios.post("/api/inventory/materials/" + r.id + "/receipts", {
        quantity: r.quantity,
        requestId: r.requestId,
      }),
    )
  )
    receiptOpen.value = false;
}
async function editBom(h) {
  if (h) {
    try {
      const d = (await axios.get("/api/inventory/boms/" + h.id)).data;
      bom.value = {
        productName: d.productname,
        version: d.version,
        lines: d.lines.map((l) => ({
          materialId: l.materialid,
          units: l.units,
        })),
      };
    } catch (e) {
      error.value = errorMessage(e);
      return;
    }
  } else
    bom.value = {
      productName: "",
      version: 0,
      lines: [{ materialId: null, units: 1 }],
    };
  bomOpen.value = true;
}
async function saveBom() {
  if (
    await run(() =>
      axios.post("/api/inventory/boms", {
        ...bom.value,
        factoryName: factory.value,
      }),
    )
  )
    bomOpen.value = false;
}
</script>
<template>
  <section class="inventory-workspace">
    <div class="inventory-toolbar">
      <el-select
        v-model="factory"
        aria-label="物料所属工厂"
        style="width: 240px"
        :disabled="store.state.user.role === 'factoryAdmin' || busy || loading || materialOpen || bomOpen || receiptOpen"
        ><el-option
          v-for="f in factories"
          :key="f.factoryName"
          :value="f.factoryName"
          :label="f.factoryName" /></el-select
      ><span>整数基本单位 · 手工入库</span
      ><el-button @click="load" :loading="loading" :disabled="busy || !factory">刷新库存</el-button
      ><el-button
        @click="
          material = { sku: '', name: '', unit: '件' };
          materialOpen = true;
        "
        :disabled="busy || loading || !factory">新建物料</el-button
      ><el-button type="primary" :disabled="busy || loading || !factory" @click="editBom()">配置 BOM</el-button>
      <el-button :disabled="busy || loading || !factory" @click="reconcile">库存对账</el-button>
    </div>
    <section v-if="reconciliation" aria-label="库存对账结果"><h3>{{reconciliation.checkedMaterials === 0 ? "暂无物料可核对" : reconciliation.consistent ? "库存对账一致" : "发现库存差异"}}</h3><p>检查 {{reconciliation.checkedMaterials}} 种物料，{{reconciliation.inconsistentMaterials}} 种存在差异。核对全部流水与有效预留，不自动修改库存。</p><el-table :data="reconciliation.materials"><el-table-column prop="sku" label="物料"/><el-table-column prop="onHand" label="在库"/><el-table-column prop="ledgerStock" label="流水在库"/><el-table-column prop="reserved" label="预留"/><el-table-column prop="activeReserved" label="有效预留"/><el-table-column label="结果"><template #default="{row}">{{row.issues.length ? row.issues.map(code => auditLabels[code] || code).join("；") : "一致"}}</template></el-table-column></el-table></section>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
    /><el-tabs v-model="tab"
      ><el-tab-pane label="库存台账" name="stock"
        ><el-table
          :data="data.materials"
          stripe
          empty-text="暂无物料，请先新建物料并记录入库"
          ><el-table-column
            prop="sku"
            label="物料编号"
            min-width="130"
          /><el-table-column
            prop="name"
            label="名称"
            min-width="130"
          /><el-table-column prop="onhand" label="在库" /><el-table-column
            prop="reserved"
            label="已预留"
          /><el-table-column prop="available" label="可用" /><el-table-column
            prop="unit"
            label="基本单位"
          /><el-table-column label="操作"
            ><template #default="{ row }"
              ><el-button link type="primary" :disabled="loading || busy" @click="receive(row)"
                >入库</el-button>
              <el-button link type="primary" @click="showLedger(row.sku)">查流水</el-button>
            </template
            ></el-table-column
          ></el-table
        ></el-tab-pane
      ><el-tab-pane label="产品 BOM" name="bom"
        ><el-table
          :data="data.boms"
          empty-text="暂无 BOM；产品名称应与订单完全一致"
          ><el-table-column
            prop="productname"
            label="产品名称"
          /><el-table-column prop="version" label="修订号" /><el-table-column
            label="操作"
            ><template #default="{ row }"
              ><el-button link type="primary" :disabled="loading || busy" @click="editBom(row)"
                >查看 / 编辑</el-button
              ></template
            ></el-table-column
          ></el-table
        ></el-tab-pane
      ><el-tab-pane label="收发流水" name="ledger"
        ><p class="hint">最近 100 条，预留和释放不改变在库数量。</p>
        <p v-if="ledgerSku">物料 {{ ledgerSku }}
          <el-button link type="primary" @click="ledgerSku = ''">显示全部流水</el-button>
        </p>
        <el-table :data="visibleLedger" stripe empty-text="最近 100 条内没有此物料的流水"
          ><el-table-column
            prop="id"
            label="流水号"
            width="80" /><el-table-column
            prop="sku"
            label="物料" /><el-table-column label="业务类型"
            ><template #default="{ row }">{{
              kinds[row.kind]
            }}</template></el-table-column
          ><el-table-column prop="quantity" label="数量" /><el-table-column
            prop="orderid"
            label="订单" /><el-table-column
            prop="actor"
            label="操作人" /><el-table-column
            prop="createdat"
            label="时间"
            min-width="180" /></el-table></el-tab-pane
    ></el-tabs>
    <el-dialog v-model="materialOpen" title="新建物料" width="460px"
      ><form class="modal-form" @submit.prevent="saveMaterial">
        <label
          >物料编号<el-input
            v-model.trim="material.sku"
            required
            maxlength="64" /></label
        ><label
          >名称<el-input
            v-model.trim="material.name"
            required
            maxlength="100" /></label
        ><label
          >基本单位<el-input
            v-model.trim="material.unit"
            required
            maxlength="16" /></label
        ><el-button native-type="submit" type="primary" :loading="busy"
          >保存</el-button
        >
      </form></el-dialog
    >
    <el-dialog v-model="receiptOpen" title="物料入库" width="420px"
      ><form @submit.prevent="saveReceipt">
        <label
          >入库数量<el-input-number
            v-model="receipt.quantity"
            :min="1"
            :max="1000000000"
            :precision="0"
        /></label>
        <p class="hint">本次提交使用固定流水编号，重试不会重复入库。</p>
        <el-button native-type="submit" type="primary" :loading="busy"
          >确认入库</el-button
        >
      </form></el-dialog
    >
    <el-dialog v-model="bomOpen" title="产品物料清单" width="620px"
      ><form class="modal-form" @submit.prevent="saveBom">
        <label
          >产品名称（与订单一致）<el-input
            v-model.trim="bom.productName"
            required
            :disabled="bom.version > 0"
            maxlength="100"
        /></label>
        <div class="bom-line" v-for="(line, i) in bom.lines" :key="i">
          <el-select v-model="line.materialId" placeholder="选择物料" required
            ><el-option
              v-for="m in data.materials"
              :key="m.id"
              :label="m.sku + ' · ' + m.name + ' / ' + m.unit"
              :value="m.id" /></el-select
          ><el-input-number
            v-model="line.units"
            :min="1"
            :max="1000000"
            :precision="0"
            aria-label="每件产品用量"
          /><el-button
            :disabled="bom.lines.length === 1"
            @click="bom.lines.splice(i, 1)"
            >删除</el-button
          >
        </div>
        <div class="inventory-actions">
          <el-button
            :disabled="bom.lines.length >= 100"
            @click="bom.lines.push({ materialId: null, units: 1 })"
            >添加用料</el-button
          ><el-button native-type="submit" type="primary" :loading="busy"
            >保存修订 {{ bom.version + 1 }}</el-button
          >
        </div>
        <p class="hint">
          每件产品消耗的整数基本单位。保存时校验修订号，已有订单的预留快照保持独立。
        </p>
      </form></el-dialog
    >
  </section>
</template>
