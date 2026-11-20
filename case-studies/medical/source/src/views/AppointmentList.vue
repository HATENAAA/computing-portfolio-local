<template>
  <!-- 总容器 -->
  <div class="wrapper">
    <header>
      <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
      <p>我的预约</p>
      <div></div>
    </header>
    <div class="top-ban"></div>

    <p v-if="notice" role="status">{{ notice }}</p>
    <p v-if="loaded && !ordersArr.length" class="empty">暂无预约记录。<RouterLink to="/hospital">预约体检 →</RouterLink></p>
    <ul>
      <li v-for="order in ordersArr" :key="order.orderId">
        <button type="button" class="left" @click="toConfirmOrder(order)">
          <span>{{ order.orderDate }} {{ order.hospitalName }}</span>
          <span>{{ order.setMealName }} · {{ order.state === 2 ? '报告已出' : '待检' }}</span>
        </button>
        <div class="right">
          <RouterLink v-if="order.state === 2" :to="{path:'/report', query:{orderId:order.orderId}}">查看报告 →</RouterLink>
          <template v-else-if="pendingId===order.orderId"><button :disabled="sending" @click="cancel(order.orderId)">确认取消</button><button :disabled="sending" @click="pendingId=null">保留预约</button></template>
          <button v-else-if="curDate < order.orderDate" @click="pendingId=order.orderId;notice=''">
            取消预约
          </button>
          <p v-else>预约日期已到</p>
        </div>
      </li>
    </ul>

    <div class="bottom-ban"></div>
    <Footer></Footer>
  </div>
</template>

<script>
import Footer from "../components/Footer.vue";
import { reactive, toRefs } from "vue";
import { useRouter } from "vue-router";
import service from "../request.js";
import { getCurDate, getSessionStorage } from "../common.js";

export default {
  setup() {
    const router = useRouter();

    const state = reactive({
      users: getSessionStorage("users"),
      ordersArr: [], pendingId:null, sending:false, notice:'', loaded:false,
      curDate: getCurDate(),
    });

    init();

    function init() {
      service
        .post(
          "/orders/listOrdersByUserId",
          {},
          { headers: { Authorization: `Bearer ${getSessionStorage("token")}` } }
        )
        .then((response) => {
          state.ordersArr = response.data;

          state.ordersArr.forEach((order) => {
            getSetMealName(order);
            getHospitalName(order);
          });
        })
        .catch(() => {
          state.notice = "预约记录加载失败，请刷新重试。";
        })
        .finally(() => { state.loaded = true; });
    }

    function getSetMealName(order) {
      service
        .post(
          "/setmeal/getSetmealById",
          {
            smId: order.smId,
          },
          { headers: { Authorization: `Bearer ${getSessionStorage("token")}` } }
        )
        .then((response) => {
          order.setMealName = response.data.name;
        })
        .catch((error) => {
          console.log(error);
        });
    }

    function getHospitalName(order) {
      service
        .post(
          "/hospital/getHospitalById",
          {
            hpId: order.hpId,
          },
          { headers: { Authorization: `Bearer ${getSessionStorage("token")}` } }
        )
        .then((response) => {
          order.hospitalName = response.data.name;
        })
        .catch((error) => {
          console.log(error);
        });
    }

    async function cancel(orderId) {
      if(state.sending || state.pendingId!==orderId)return;
      state.sending=true;
      try {
        await service.post("/orders/removeOrders",{orderId},{headers:{Authorization:'Bearer '+getSessionStorage("token")}});
        state.ordersArr=state.ordersArr.filter(order=>order.orderId!==orderId);
        state.pendingId=null;state.notice="预约已取消。";
      } catch {state.notice="取消请求未确认，请刷新订单核对状态。";}
      finally {state.sending=false;}
    }

    function toConfirmOrder(order) {
      router.push({
        path: "/confirmorder",
        query: {
          hpId: order.hpId,
          smId: order.smId,
          selectDay: order.orderDate,
        },
      });
    }

    return {
      ...toRefs(state),
      cancel,
      toConfirmOrder,
    };
  },
  components: {
    Footer,
  },
};
</script>

<style scoped>
/*********************** 总容器 ***********************/
.wrapper {
  width: 100%;
  height: 100%;
  background-color: #f9f9f9;
}

/*********************** header ***********************/
header {
  width: 100%;
  height: calc(var(--medical-vw) * 15.7);
  background-color: #fff;

  position: fixed;
  left: 0;
  top: 0;

  display: flex;
  align-items: center;
  justify-content: space-between;

  box-sizing: border-box;
  padding: 0 calc(var(--medical-vw) * 3.6);
}
header .fa {
  font-size: calc(var(--medical-vw) * 8);
}

/*********************** common样式 ***********************/
.top-ban {
  width: 100%;
  height: calc(var(--medical-vw) * 15.7);
}
.bottom-ban {
  width: 100%;
  height: calc(var(--medical-vw) * 14.2);
}

/*********************** ul ***********************/
ul {
  width: calc(var(--medical-vw) * 86);
  margin: 0 auto;
}
ul li {
  width: 100%;
  height: calc(var(--medical-vw) * 14);
  border-bottom: solid 1px #eee;

  display: flex;
  justify-content: space-between;
  align-items: center;
}
ul li .left {
  user-select: none;
  cursor: pointer;
}
ul li .left p:first-child {
  color: #555;
  font-size: calc(var(--medical-vw) * 3.3);
}
ul li .left p:last-child {
  color: #333;
  font-size: calc(var(--medical-vw) * 4.2);
  font-weight: 600;
}
ul li .right {
  font-size: calc(var(--medical-vw) * 4);
  color: #e6a23c;
}
button.left { border:0; background:none; text-align:left; cursor:pointer; }
button.left span { display:block; }
button.left span + span { margin-top:5px; color:#53687b; }
.right a { color:#225b87; white-space:nowrap; }
.empty, [role="status"] { margin:12px; color:#435b71; }
</style>
