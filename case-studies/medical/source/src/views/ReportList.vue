<template>
    <!-- 总容器 -->
    <div class="wrapper">
        <header>
            <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
            <p>健康档案</p>
            <div></div>
        </header>
        <div class="top-ban"></div>

        <section>
            <img src="../assets/img/report.png">
            <p v-if="!reportList.length" class="empty">暂无已发布的报告。</p>
            <ul>
                <li v-for="(item,index) in reportList" :key="index">
                    <div class="left">
                        <i class="fa fa-file-text-o"></i>
                        <div>
                            <p>{{ convert(item.orderDate) }} 体检报告</p>
                            <p>{{ item.hpName }}</p>
                        </div>
                    </div>
                    <button type="button" class="right" @click="toReport(item.orderId)">查看报告 →</button>
                </li>
            </ul>
        </section>
        
        <div class="bottom-ban"></div>
        <Footer></Footer>
    </div>
</template>

<script>

import Footer from '../components/Footer.vue';
import { reactive, toRefs} from "vue";
import { useRouter } from "vue-router";
import service from '../request.js';
import { getSessionStorage } from '../common.js';
export default {
  setup() {
    const router = useRouter();

    const state = reactive({
        users : getSessionStorage('users'),
        reportList:[]
    });
  
    init();
    function init() {
        service
        .post('/orders/listOrdersByUserId',
        {
            userId: state.users.userID,
            state: 2
        }, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {

           state.reportList = response.data;
        })
        .catch((error) => {
            console.log(error);
        });
    }
    function convert(str){
        if(str!=null){
            let arr = str.split('-');
            return arr[0]+'年'+arr[1]+'月'+arr[2]+'日';
        }
    }
    function toReport(orderId){
        router.push({path:'/report',query:{orderId:orderId}})
    }
    return{
        ...toRefs(state),
        convert,
        toReport
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
    height: calc(var(--medical-vw) * 14.2);
}

/*********************** section ***********************/
section{
    width: 100%;
}
section img{
    width: 100%;
    display: block;
}
section ul{
    width: calc(var(--medical-vw) * 86);
    margin: 0 auto;
}
section ul li{
    width: 100%;
    height: calc(var(--medical-vw) * 18);
    border-bottom: solid 1px #EEE;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
section ul li .left{
    display: flex;
    align-items: center;
}
section ul li .left i{
    font-size: calc(var(--medical-vw) * 8);
    color: #397faa;
    margin-right: calc(var(--medical-vw) * 3);
}
section ul li .left p:first-child{
    color: #555;
    font-size: calc(var(--medical-vw) * 4.2);
    font-weight: 600;
}
section ul li .left p:last-child{
    color: #999;
    font-size: calc(var(--medical-vw) * 3.2);
    font-weight: 600;
    margin-top: calc(var(--medical-vw) * 1);
}
section ul li .right{
    user-select: none;
    cursor: pointer;
}
section ul li .right i{
    color: #999;
    font-size: calc(var(--medical-vw) * 6);
}
button.right { border:0; cursor:pointer; color:#225b87; background:none; white-space:nowrap; }
.empty { padding:20px; color:#536979; }
</style>