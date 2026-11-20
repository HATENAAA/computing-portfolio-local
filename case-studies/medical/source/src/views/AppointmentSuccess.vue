<template>
     <!-- 总容器 -->
     <div class="wrapper">
        <header>
            <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
            <p>预约成功</p>
            <div></div>
        </header>
        <div class="top-ban"></div>

        <section>
            <div class="success">
                <div class="icon-box">
                    <div class="icon">
                        <i class="fa fa-check"></i>
                    </div>
                </div>
                <h1>恭喜预约成功！</h1>
                <p>请体检用户携带本人身份证到店认证</p>
            </div>
            <button type="button" class="order-btn" @click="toAppointmentList">查看订单</button>
            <button type="button" class="continue" @click="toAppointment">再次预约</button>
            <div class="info">
                <p>您的信息已经发送至体检机构</p>
                <p>可在预约记录中查看体检机构和日期。</p>
                <p>客服电话<span>4008-XXX-XXX</span></p>
            </div>
        </section>
        
        <div class="bottom-ban"></div>
        <Footer></Footer>
    </div>
</template>

<script>
import Footer from '../components/Footer.vue';
import { useRouter } from "vue-router";
export default {
  setup() {

    const router = useRouter();
    function toAppointmentList(){
        router.push('/appointmentlist')
    }
    function toAppointment(){
        router.push('/appointment')
    }
    return{
        toAppointmentList,
        toAppointment
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
section .success{
    width: 100%;
    height: calc(var(--medical-vw) * 62);
    border-bottom: solid 1px #EEE;
    background-color: #FFF;
}
section .success .icon-box{
    width: 100%;
    height: calc(var(--medical-vw) * 30);
    background-image: linear-gradient(135deg,#4585bc,#2588b3,#2588b3);
    position: relative;
}
section .success .icon-box .icon{
    width: calc(var(--medical-vw) * 16);
    height: calc(var(--medical-vw) * 16);
    border-radius: calc(var(--medical-vw) * 8);
    background-color: #FFF;

    position: absolute;
    left: calc(var(--medical-vw) * 42);
    bottom: -8vw;

    font-size: calc(var(--medical-vw) * 8);
    color: #2588b3;

    text-align: center;
    line-height: calc(var(--medical-vw) * 16);
}
section .success h1{
    text-align: center;
    font-size: calc(var(--medical-vw) * 5.2);
    font-weight: 500;
    color: #2588b3;
    margin-top: calc(var(--medical-vw) * 10);
}
section .success p{
    text-align: center;
    font-size: calc(var(--medical-vw) * 3.4);
    color: #555;
    margin-top: calc(var(--medical-vw) * 3);
}

section .order-btn{
    width: 100%;
    height: calc(var(--medical-vw) * 14);
    text-align: center;
    line-height: calc(var(--medical-vw) * 14);
    font-size: calc(var(--medical-vw) * 4);
    color: #2588b3;
    background-color: #FFF;
    user-select: none;
    cursor: pointer;
}
section .continue{
    width: calc(var(--medical-vw) * 88);
    height: calc(var(--medical-vw) * 13);
    margin: 0 auto;
    background-image: linear-gradient(135deg,#4585bc,#2588b3,#2588b3);
    border-radius: calc(var(--medical-vw) * 1);
    text-align: center;
    line-height: calc(var(--medical-vw) * 13);
    margin-top: calc(var(--medical-vw) * 5);
    font-size: calc(var(--medical-vw) * 4);
    color: #FFF;
    user-select: none;
    cursor: pointer;
}
section .info{
    width: 100%;
    margin-top: calc(var(--medical-vw) * 16);
}
section .info p{
    text-align: center;
    font-size: calc(var(--medical-vw) * 3.2);
    color: #999;
    margin-top: calc(var(--medical-vw) * 1);
}
section .info p span{
    font-size: calc(var(--medical-vw) * 3.6);
    color: #555;
    margin-left: calc(var(--medical-vw) * 1);
}

</style>
