<template>
    <!-- 总容器 -->
    <div class="wrapper">
        <header>
            <i class="fa fa-angle-left" onclick="history.go(-1)"></i>
            <p>选择体检日期</p>
            <div></div>
        </header>
        <div class="top-ban"></div>
        <section>
            <div class="date-box">
                <i class="fa fa-caret-left" @click="prevMonth"></i>
                <p>{{ year }}年{{ month }}月</p>
                <i class="fa fa-caret-right" @click="nextMonth"></i>
            </div>
            <table>
                <tr>
                    <th>日</th>
                    <th>一</th>
                    <th>二</th>
                    <th>三</th>
                    <th>四</th>
                    <th>五</th>
                    <th>六</th>
                </tr>
            </table>
                <ul>
                    <li v-for="(calendar, index) in calendarArr" :key="index">
                        <button v-if="calendar.day" type="button" :disabled="!calendar.open" :aria-pressed="calendar.selectDay == 1" :class="[
                                { fontcolor: calendar.open },
                                { pselect: calendar.selectDay == 1 }
                            ]"
                            @click="selectDay(index)"
                        >
                            {{ calendar.day }}
                        </button>
                        <p>
                            {{calendar.open ? "余"+calendar.remainder : '' }}
                        </p>
                    </li>
                </ul>
        </section>

        <div class="bottom-btn">
            <div></div>
            <div @click="toConfirmOrder">下一步</div>
        </div>

        <div class="bottom-ban"></div>
        <Footer></Footer>
    </div>
</template>

<script>
import Footer from '../components/Footer.vue';
import service from '../request.js';
import { getSessionStorage } from '../common.js';
import { reactive, toRefs} from "vue";
import { useRoute,useRouter } from "vue-router";

export default {
    
  setup() {
    const router = useRouter();
    const route = useRoute();
    const curDate = new Date();

    const state = reactive({
       hpId: route.query.hpId,
       smId: route.query.smId,
       year: curDate.getFullYear(),
       month: curDate.getMonth() + 1,
       calendarArr: [],
       selectDay : '',
    });
  
    getCalendar();
    function getCalendar() {
    service
    .post('/calendar/listAppointmentCalendar',{
        hpId : state.hpId,
        year : state.year,
        month : state.month}, {headers:{'Authorization':`Bearer ${getSessionStorage('token')}`}})
    .then((response) => {
        let calendarData = response.data;
        let firstDay = new Date(state.year, state.month - 1, 1).getDay();

        let blankDays = [];
        for(let i = 0; i < firstDay; i++) {
            blankDays.push({ day: '', remainder: null, selectDay: 0 });
        }

        let adjustedCalendarArr = blankDays.concat(calendarData.map(calendar => {
            if (calendar.ymd != null) {
                calendar.day = Number(calendar.ymd.slice(-2));
                const today = new Intl.DateTimeFormat("en-CA", {timeZone:"Asia/Shanghai", year:"numeric", month:"2-digit", day:"2-digit"}).format(new Date());
                calendar.open = calendar.ymd >= today && calendar.remainder > 0;
                calendar.selectDay = (calendar.ymd == state.selectDay) ? 1 : 0;
            }
            return calendar;
        }));

        state.calendarArr = adjustedCalendarArr;
    })
    .catch((error) => {
        console.log(error);
    });
    }

    function prevMonth(){
        state.selectDay = "";
        if(state.month == 1){
            state.year = state.year - 1;
            state.month = 12;
        }
        else{
            state.month = state.month - 1;
        }
        getCalendar();
    }
    function nextMonth(){
        state.selectDay = "";
        if(state.month == 12){
            state.year = state.year + 1;
            state.month = 1;
        }
        else{
            state.month = state.month + 1;
        }
        getCalendar();
    }
    function selectDay(index){
        if(state.calendarArr[index].remainder == null || state.calendarArr[index].remainder == 0){
            return;
        }
        for(let i = 0; i < state.calendarArr.length; i++){
            state.calendarArr[i].selectDay = 0;
        }
        state.calendarArr[index].selectDay = 1;
        state.selectDay = state.calendarArr[index].ymd;
    }
    function toConfirmOrder(){
        if(state.selectDay == ''){
            alert('请选择体检日期');
            return;
        }
        router.push({path:'/confirmOrder',query:{hpId:state.hpId, smId:state.smId, selectDay:state.selectDay,flag:1}})
    }
    return{
        ...toRefs(state),
        prevMonth,
        nextMonth,
        selectDay,
        toConfirmOrder
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

/*********************** section ***********************/
section {
    width: calc(var(--medical-vw) * 82);
    margin: 0 auto;
    margin-top: calc(var(--medical-vw) * 12);
}

section .date-box {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: calc(var(--medical-vw) * 4.5);
    font-weight: 600;
}

section .date-box p {
    color: #000;
}

section .date-box i {
    color: #999;
    user-select: none;
    cursor: pointer;
}

section table {
    width: 100%;
    font-size: calc(var(--medical-vw) * 3.8);
}

section table tr th {
    text-align: center;
    font-weight: 600;
    line-height: calc(var(--medical-vw) * 12);
}

section ul {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
}

section ul li {
    width: 14.28%;
    height: calc(var(--medical-vw) * 12);
    font-weight: 600;
    color: #999;
}

section ul li :is(p, button):first-child {
    width: calc(var(--medical-vw) * 6);
    height: calc(var(--medical-vw) * 6);
    margin: 0 auto;
    border-radius: calc(var(--medical-vw) * 3);

    display: flex;
    justify-content: center;
    align-items: center;

    font-size: calc(var(--medical-vw) * 4.2);

    user-select: none;
    cursor: pointer;
}

section ul li :is(p, button):last-child {
    font-size: calc(var(--medical-vw) * 3);
    font-weight: 300;
    text-align: center;
    user-select: none;
}

.fontcolor {
    color: #333;
}

.pselect {
    background-color: #FB902B;
    color: #FFF;
}

/*********************** bottom-btn ***********************/
.bottom-btn {
    width: 100%;
    height: calc(var(--medical-vw) * 12);
    background-color: #FFF;

    position: fixed;
    left: 0;
    bottom: calc(var(--medical-vw) * 14.2);

    display: flex;
}

.bottom-btn div:first-child {
    flex: 2;
}

.bottom-btn div:last-child {
    flex: 1;
    background-color: #117C94;
    text-align: center;
    line-height: calc(var(--medical-vw) * 12);
    font-size: calc(var(--medical-vw) * 5);
    color: #FFF;

    user-select: none;
    cursor: pointer;
}
.fontcolor{
    color: #333;
}
.pselect{
    background-color: #FB902B;
    color:#FFF
}
li button { border:0; font:inherit; background:none; padding:0; cursor:pointer; }
li button:disabled { cursor:default; }
</style>