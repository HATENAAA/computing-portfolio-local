<template>
        <!-- 总容器 -->
        <div class="wrapper">
        <header>
            <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
            <p>确认您的订单</p>
            <div></div>
        </header>
        <div class="top-ban"></div>

        <section>
            <div class="title">
                <p>体检人信息</p>
            </div>
            <table>
                <tr>
                    <td>姓名:</td>
                    <td>{{ users.realName}}</td>
                </tr>
                <tr>
                    <td>证件号码:</td>
                    <td>{{ users.identityCard}}</td>
                </tr>
                <tr>
                    <td>出生日期:</td>
                    <td>{{ formattedSelectDay(users.birthday) }}</td>
                </tr>
                <tr>
                    <td>手机号码:</td>
                    <td>{{ users.userID }}</td>
                </tr>
            </table>
            <div class="title">
                <p>体检日期</p>
            </div>
            <table>
                <tr>
                    <td>{{formattedSelectDay(selectDay) }}</td>
                </tr>
            </table>
            <div class="title">
                <p>体检机构</p>
            </div>
            <table>
                <tr>
                    <td colspan="2">{{hospital.name}}</td>
                </tr>
                <tr>
                    <td>营业时间:</td>
                    <td>{{hospital.businessHours}}</td>
                </tr>
                <tr>
                    <td>采血截止:</td>
                    <td>{{hospital.deadline}}</td>
                </tr>
                <tr>
                    <td>机构电话:</td>
                    <td>{{ hospital.telephone }}</td>
                </tr>
                <tr>
                    <td>机构地址:</td>
                    <td>{{ hospital.address }}</td>
                </tr>
            </table>
            <div class="title">
                <p>套餐类型</p>
            </div>
            <table>
                <tr>
                    <td>{{ setmeal.name }}</td>
                </tr>
            </table>
        </section>
        
        <p class="booking-error" role="status" v-if="error">{{ error }}</p>
        <div class="bottom-btn">
            <div class="first">套餐参考价： <span>￥{{ users.userType == 2 ? 0:setmeal.price }}</span></div>
            <button class="last" type="button" @click="toSuccess" v-if="flag == 1" :disabled="sending || !hospital.hpId || !setmeal.smId">{{ sending ? "提交中…" : "确认预约" }}</button>
        </div>

        <div class="bottom-ban"></div>
            <Footer></Footer>
    </div>
</template>

<script>
import Footer from '../components/Footer.vue';
import { reactive, toRefs} from "vue";
import { useRoute,useRouter } from "vue-router";
import service from '../request.js';
import { getSessionStorage } from '../common.js';
export default {
  setup() {
    const router = useRouter();
    const route = useRoute();

    const state = reactive({
       hpId: route.query.hpId,
       smId: route.query.smId,
       flag: route.query.flag,
       selectDay: route.query.selectDay,
       users: getSessionStorage('users'),
       hospital:{},
       setmeal:{},
       sending:false,
       error:"",
       
    });
  
    init();
    function init() {
        service
        .post('/hospital/getHospitalById',
        {hpId: state.hpId}, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {
            state.hospital = response.data;
        })
        .catch((error) => {
            console.log(error);
        });
        service
        .post('/setmeal/getSetmealById',
        {smId:state.smId}, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {
            state.setmeal = response.data;
        })
        .catch((error) => {
            console.log(error);
        });
    }
    function toSuccess(){
        state.sending = true;
        state.error = "";
        service
        .post('/orders/saveOrders',
        {
            orderDate :state.selectDay,
            userId: state.users.userID,
            hpId: state.hpId,
            smId: state.smId,
            state: 1
        }, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {
            if(response.data != null){
                router.push('/appointmentsuccess')
            }
            else{
                state.error = "生成订单失败。";
            }
        })
        .catch((error) => {
            state.error = error.response?.data?.message || "预约未能提交，请稍后重试。";
        })
        .finally(() => { state.sending = false; });
    }
    function formattedSelectDay(selectDay) {
        const date = new Date(selectDay);
        return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
    }
    return{
        ...toRefs(state),
        toSuccess,
        formattedSelectDay
    }
  },
  components: {
    Footer
  },
  
};
</script>

<style scoped>
/*********************** 总容器 ***********************/
.wrapper{
    width: 100%;
    height: 100%;
    background-color: #F9F9F9;
}

/*********************** header ***********************/
header{
    width: 100%;
    height: calc(var(--medical-vw) * 15.7);
    background-color: #FFF;

    position: fixed;
    left: 0;
    top: 0;

    display: flex;
    align-items: center;
    justify-content: space-between;

    box-sizing: border-box;
    padding: 0 calc(var(--medical-vw) * 3.6);
}
header .fa{
    font-size: calc(var(--medical-vw) * 8);
}

/*********************** common样式 ***********************/
.top-ban{
    width: 100%;
    height: calc(var(--medical-vw) * 15.7);
}
.bottom-ban{
    width: 100%;
    height: calc(var(--medical-vw) * 26.2);
}

/*********************** section ***********************/
section{
    width: calc(var(--medical-vw) * 86);
    margin: 0 auto;
}
section .title{
    width: 100%;
    height: calc(var(--medical-vw) * 12);
    border-bottom: solid 1px #EEE;

    display: flex;
    align-items: center;
}
section .title p{
    height: calc(var(--medical-vw) * 3.4);
    line-height: calc(var(--medical-vw) * 3.4);
    font-size: calc(var(--medical-vw) * 4.2);
    font-weight: 600;
    box-sizing: border-box;
    padding-left: calc(var(--medical-vw) * 3);
    border-left: solid 2px #127A90;
}
section table{
    font-size: calc(var(--medical-vw) * 3.6);
    color: #555;
    margin-top: calc(var(--medical-vw) * 2);
}
section table tr{
    line-height: calc(var(--medical-vw) * 8);
}
section table tr td:first-child{
    width: 22%;
}

/*********************** bottom-btn ***********************/
.bottom-btn{
    width: 100%;
    height: calc(var(--medical-vw) * 12);
    background-color: #FFF;

    position: fixed;
    left: 0;
    bottom: calc(var(--medical-vw) * 14.2);

    display: flex;
}
.bottom-btn .first{
    flex: 2;
    line-height: calc(var(--medical-vw) * 12);
    font-size: calc(var(--medical-vw) * 4.6);
    box-sizing: border-box;
    padding-left: calc(var(--medical-vw) * 6);
}
.bottom-btn .first span{
    color: #F77B2D;
}
.bottom-btn .last{
    flex: 1;
    background-color: #117C94;
    line-height: calc(var(--medical-vw) * 12);
    text-align: center;
    font-size: calc(var(--medical-vw) * 5);
    color: #FFF;

    user-select: none;
    cursor: pointer;
}
.booking-error { margin: 12px 16px; color: #8e2929; }
button.last { border: 0; cursor: pointer; }
button.last:disabled { opacity: .6; cursor: wait; }
</style>