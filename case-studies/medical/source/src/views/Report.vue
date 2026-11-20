<template>
    <!-- 总容器 -->
    <div class="wrapper">
        <header>
            <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
            <p>{{convert(orders.orderDate)}}体检报告</p>
            <div></div>
        </header>

        <nav>
            <div :class="{ active: navFlag == 'general' }" @click="navEvent('general')">总检结论</div>
            <div :class="{ active: navFlag == 'detailed' }" @click="navEvent('detailed')">报告详情</div>
        </nav>

        <div class="top-ban"></div>

        <div class="nav-content-item" v-if="navFlag == 'general'">
            <div class="item">
                <div class="title">异常项</div>
                <ul>
                    <li v-for="(eci, index) in errorCheckItemArr" :key="index">
                        <div class="indications">
                            <div class="left">
                                <div>异</div>
                                <p>{{ eci.name }}</p>
                            </div>
                            <div class="right">
                                <p>{{ eci.value }} {{ eci.unit }}</p>
                                <p v-if="eci.normalValueString">正常值范围：{{ eci.normalValueString }}</p>
                            </div>
                        </div>
                    </li>
                </ul>
            </div>
            <div class="item">
                <div class="title">总检结果</div>
                <ul>
                    <li class="conclusion-content">
                        <p>
                            {{overallResult.title}}
                        </p>                     
                    </li>
                </ul>
            </div>
            <div class="item">
                <div class="title">总检结论</div>
                <ul>
                    <li class="conclusion-content">
                        <p>
                            {{ overallResult.content }}
                        </p>
                    </li>
                </ul>
            </div>

        </div>
        <div class="nav-content-item" v-else-if="navFlag === 'detailed'">
            <ul>
                <li v-for="(ci, index) in ciReportArr" :key="index">
                    <div class="item">
                        <div class="title">{{ ci.name }}</div>
                        <ul>
                            <li>
                                <div class="indications" v-if ="ci.type != 4">
                                    <div class="left">
                                        <div v-if="ci.isError == 1">异</div>
                                        <p>{{ ci.name }}</p>
                                    </div>
                                    <div class="right">
                                        <p>{{ ci.value }} {{ ci.unit }}</p>
                                        <p v-if="ci.normalValueString">正常值范围：{{ ci.normalValueString }}</p>
                                    </div>
                                </div>
                                 <div class="indications-type-4 " v-if ="ci.type == 4">
                                    <div>
                                        <p>{{ ci.name }}</p>
                                    </div>
                                    <div>
                                        <p>{{ ci.value }}</p>
                                    </div>
                                </div>
                            </li>
                        </ul>
                    </div>
                </li>
            </ul>
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
        users : getSessionStorage('users'),
        navFlag: 'general',
        orderId: route.query.orderId,
        orders: {},
        overallResult: [],
        ciReportArr: [],
        errorCheckItemArr: []
    })
    
    init();
    function init(){
      service
        .post('/orders/getOrdersByOrderId',
        {
            orderId: state.orderId,
        }, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {
           state.orders = response.data;
        })
        .catch((error) => {
            console.log(error);
        });
      service
        .post('/overallResult/listOverallResultByOrderId',
        {
            orderId: state.orderId,
        }, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {  
            state.overallResult = response.data;

        })
        .catch((error) => {
            console.log(error);
        });
      service
        .post('/ciDetailedReport/listCiDetailedReportByOrderId',
        {
            orderId: state.orderId,
        }, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {
            state.ciReportArr = response.data;

            for(let i = 0; i < state.ciReportArr.length; i++){
                if(state.ciReportArr[i].isError == 1){
                    state.errorCheckItemArr.push(state.ciReportArr[i]); 
                }
            }
        })
        .catch((error) => {
            console.log(error);
        });
    }
    function navEvent(flag) {
        state.navFlag = flag;
    }
    
    function convert(str){
        if(str!=null){
            let arr = str.split('-');
            return arr[0]+'年'+arr[1]+'月'+arr[2]+'日';
        }
    }
    return{
        ...toRefs(state),
        convert,
        navEvent
    }
  },
  components: {
    Footer
  },
  
};
</script>
<style scoped>
/*********************** 总容器 ***********************/
.wrapper {
    width: 100%;
    height: 100%;
    background-color: #F9F9F9;
}

/*********************** header ***********************/
header {
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

header .fa {
    font-size: calc(var(--medical-vw) * 8);
}

/*********************** common样式 ***********************/
.top-ban {
    width: 100%;
    height: calc(var(--medical-vw) * 31.7);
}

.bottom-ban {
    width: 100%;
    height: calc(var(--medical-vw) * 14.2);
}

/*********************** nav ***********************/
nav {
    width: 100%;
    height: calc(var(--medical-vw) * 16);
    display: flex;
    background-color: #F9F9F9;

    position: fixed;
    left: 0;
    top: calc(var(--medical-vw) * 15.7);
}

nav div {
    flex: 1;
    height: calc(var(--medical-vw) * 14);
    box-sizing: border-box;

    text-align: center;
    line-height: calc(var(--medical-vw) * 14);
    font-size: calc(var(--medical-vw) * 4.2);
    font-weight: 600;
    color: #555;
}

.active {
    border-bottom: solid 2px #137E92;
    color: #137E92;
}

/*********************** nav-content-item ***********************/
.nav-content-item .item {
    width: calc(var(--medical-vw) * 92);
    margin: 0 auto;
    margin-top: calc(var(--medical-vw) * 3);
    margin-bottom: calc(var(--medical-vw) * 3);
    overflow: hidden;
    border-radius: calc(var(--medical-vw) * 3);
    background-color: #FFF;
}

.nav-content-item .item .title {
    width: 100%;
    height: calc(var(--medical-vw) * 10);
    background-color: #7BAFD7;
    line-height: calc(var(--medical-vw) * 10);
    box-sizing: border-box;
    padding-left: calc(var(--medical-vw) * 4);
    font-size: calc(var(--medical-vw) * 4.2);
    color: #FFF;
}

.nav-content-item .item ul {
    width: 100%;
}

/****** 数值型检查项样式 ******/
.nav-content-item .item ul li {
    border-bottom: solid 1px #EEE;
}

.nav-content-item .item ul li:last-child {
    border-bottom: none;
}

.nav-content-item .item ul li .indications {
    width: 100%;
    height: calc(var(--medical-vw) * 14);
    padding: 0 calc(var(--medical-vw) * 3);
    display: flex;
    align-items: center;
    font-size: calc(var(--medical-vw) * 3.2);
    color: #333;
}

.nav-content-item .item ul li .indications .left {
    flex: 1;
    display: flex;
}

.nav-content-item .item ul li .indications .left div {
    background-color: #BA634E;
    color: #FFF;
    padding: calc(var(--medical-vw) * 0.2) calc(var(--medical-vw) * 0.6);
    border-radius: calc(var(--medical-vw) * 0.6);
}

.nav-content-item .item ul li .indications .left p {
    font-weight: 600;
    margin-left: calc(var(--medical-vw) * 2);
}

.nav-content-item .item ul li .indications .right {
    flex: 1;
}

.nav-content-item .item ul li .indications .right p:last-child {
    color: #999;
}

/****** 数值型检查项样式 ******/

/****** 描述型检查项样式 ******/
.nav-content-item .item ul li .indications-type-4 {
    width: 100%;
    box-sizing: border-box;
    padding: 0 calc(var(--medical-vw) * 3);

    font-size: calc(var(--medical-vw) * 3.2);
    color: #333;
}

.nav-content-item .item ul li .indications-type-4 div {
    margin: calc(var(--medical-vw) * 5) 0;
}

.nav-content-item .item ul li .indications-type-4 div:first-child {
    font-weight: 600;
}

.nav-content-item .item ul li .indications-type-4 div:last-child {
    color: #999;
}

/****** 描述型检查项样式 ******/

.nav-content-item .item ul .conclusion-title {
    width: 100%;
    height: calc(var(--medical-vw) * 12);
    box-sizing: border-box;
    border-bottom: solid 1px #EEE;
    padding: 0 calc(var(--medical-vw) * 3);

    display: flex;
    align-items: center;
    font-size: calc(var(--medical-vw) * 4);
    color: #555;
}

.nav-content-item .item ul .conclusion-title:last-child {
    border-bottom: none;
}

.nav-content-item .item ul .conclusion-content {
    width: 100%;
    box-sizing: border-box;
    border-bottom: solid 1px #EEE;
    padding: calc(var(--medical-vw) * 4) calc(var(--medical-vw) * 3);
    font-size: calc(var(--medical-vw) * 3.6);
    color: #555;
}

.nav-content-item .item ul .conclusion-content:last-child {
    border-bottom: none;
}

.nav-content-item .item ul .conclusion-content h3 {
    font-size: calc(var(--medical-vw) * 4);
    font-weight: 600;
    margin-bottom: calc(var(--medical-vw) * 2);
}

.nav-content-item .item ul .conclusion-content p {
    text-indent: calc(var(--medical-vw) * 8);
}
</style>