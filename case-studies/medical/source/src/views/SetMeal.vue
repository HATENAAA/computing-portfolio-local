<template>
    <!-- 总容器 -->
    <div class="wrapper">
        <header>
            <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
            <p>选择体检套餐</p>
            <div></div>
        </header>
        <div class="top-ban"></div>

        <ul class="setmeal">
            <li v-for="(setmeal, index) in SetMealList" :key="setmeal.smId">
                
                <div class="item">
                    <div class="item-left" @click="selectdate(setmeal.smId)">  
                        <h3>{{ setmeal.type == 0 ? '女士套餐' : '男士套餐' }}</h3>
                        <p>{{setmeal.name}}</p>
                    </div>
                    <div class="item-right" @click="toggleContent(index)">
                        <p>详情</p>
                        <i class="fa fa-angle-down"></i>
                    </div>
                </div>
                <div class="item-content" v-if="setmeal.showContent">
                    <table>
                        <tr>
                            <th>检查项目</th>
                            <th>检查内容</th>
                            <th>检查意义</th>
                        </tr>
                        <tr v-for="checkItem in setmeal.checkItems" :key="checkItem.ciId">
                            <td>{{ checkItem.ciName }}</td>
                            <td>{{ checkItem.ciContent }}</td>
                            <td>{{ checkItem.meaning }}</td>
                        </tr>
                    </table>
                </div>
            </li>
        </ul>

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
        SetMealList : []
    });
  
    init();
    function init() {
        service
        .post('/setmeal/listSetmealByType',
        {type : getSessionStorage('users').sex}, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
        .then((response) => {       
            let arr = response.data;   
            for(let i = 0; i < arr.length; i++) {
                arr[i].showContent = false;
                arr[i].checkItems = null;
            }
            state.SetMealList = arr;
        })
        .catch((error) => {
            console.log(error);
        });
    }
    function toggleContent(index) {
        const setmeal = state.SetMealList[index];
        setmeal.showContent = !setmeal.showContent;
        if (!setmeal.showContent || setmeal.checkItems) return;
        service
          .post('/setmeal/getCheckItem',
          {smId:setmeal.smId}, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
          .then((response) => {
            setmeal.checkItems = response.data;
          })
          .catch((error) => {
            console.log(error);
        });
    }

    function selectdate(smId) {
        router.push({path:'/selectDate', query:{hpId:route.query.hpId, smId:smId}})
    }

    return{
        ...toRefs(state),
        toggleContent,
        selectdate
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
    height: calc(var(--medical-vw) * 15.7);
}

.bottom-ban {
    width: 100%;
    height: calc(var(--medical-vw) * 14.2);
}

/*********************** setmeal ***********************/
.setmeal {
    width: 100%;
    margin-top: calc(var(--medical-vw) * 10);
}

.setmeal li {
    width: calc(var(--medical-vw) * 92.8);
    margin: 0 auto;
    border: solid 1px #EEE;
    border-radius: calc(var(--medical-vw) * 1);
    box-shadow: 2px 2px 5px rgba(0, 0, 0, .08);
    background-color: #FFF;
    margin-bottom: calc(var(--medical-vw) * 3.6);
}

.setmeal li .item {
    width: 100%;
    height: calc(var(--medical-vw) * 20);
    color: #555;

    display: flex;
    align-items: center;
}

.setmeal li .item .item-left {
    flex: 0 0 calc(var(--medical-vw) * 72);
    height: calc(var(--medical-vw) * 20);
    border-right: solid 1px #EEE;
    box-sizing: border-box;
    padding-left: calc(var(--medical-vw) * 12);

    display: flex;
    flex-direction: column;
    justify-content: center;

    user-select: none;
    cursor: pointer;
}

.setmeal li .item .item-left h3 {
    font-size: calc(var(--medical-vw) * 4.3);
    font-weight: 600;
}

.setmeal li .item .item-left p {
    font-size: calc(var(--medical-vw) * 4);
    margin-top: calc(var(--medical-vw) * 1);
}

.setmeal li .item .item-right {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;

    user-select: none;
    cursor: pointer;
}

.setmeal li .item .item-right p {
    font-size: calc(var(--medical-vw) * 4);
    margin-right: calc(var(--medical-vw) * 2);
}

.setmeal li .item-content {
    /*display: none;*/
    width: 100%;
    background-color: #FFF;
}

.setmeal li .item-content table {
    width: 100%;
    border-collapse: collapse;
    font-size: calc(var(--medical-vw) * 4);
    color: #555;
}

.setmeal li .item-content table tr {
    display: flex;
}

.setmeal li .item-content table tr td,
.setmeal li .item-content table tr th {
    flex: 1;
}

.setmeal li .item-content table tr th {
    text-align: center;
    background-color: #EEE;
    height: calc(var(--medical-vw) * 10);
    line-height: calc(var(--medical-vw) * 10);
}

.setmeal li .item-content table tr td {
    border: solid 1px #EFEFEF;
    box-sizing: border-box;
    padding: calc(var(--medical-vw) * 2);
}
</style>