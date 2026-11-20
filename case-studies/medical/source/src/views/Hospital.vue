<template>
  <div class="wrapper">
    <header>
      <i class="fa fa-angle-left" onclick="history.go(-1)"> </i>
      <p>请您选择体检机构</p>
      <div></div>
    </header>
    <div class="top-ban"></div>
    <ul class="hospital">
      <li v-for="hospital in hospitalList" :key="hospital.hpId">
        <h3><button class="hospital-choice" type="button" @click="toSetMeal(hospital.hpId)">
          {{ hospital.name }}
          <i class="fa fa-angle-right"></i>
        </button></h3>
        <div class="hospita-info">
          <img :src="hospital.picture" />
          <table>
            <tr>
              <td>营业时间</td>
              <td>{{ hospital.businessHours }}</td>
            </tr>
            <tr>
              <td>采血截止</td>
              <td>{{ hospital.deadline }}</td>
            </tr>
            <tr>
              <td>电话</td>
              <td>{{ hospital.telephone }}</td>
            </tr>
            <tr>
              <td>地址</td>
              <td>{{ hospital.address }}</td>
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
import Footer from "../components/Footer.vue";
import { reactive, toRef, toRefs } from "vue";
import { useRouter } from "vue-router";
import service from "../request.js";
import { getSessionStorage } from "../common";

export default {
  setup() {
    const router = useRouter();
    const state = reactive({
      hospitalList: [],
    });

    init();
    function init() {
      service
        .post(
          "/hospital/listHospital",
          { state: 1 },
          { headers: { Authorization: `Bearer ${getSessionStorage("token")}` } }
        )
        .then((response) => {
          state.hospitalList = response.data;
        })
        .catch((error) => {
          console.log(error);
        });
    }

    function toSetMeal(hpId) {
      router.push({ path: "/setmeal", query: { hpId: hpId } });
    }

    return {
      ...toRefs(state),
      toSetMeal,
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

/*********************** hospital ***********************/
.hospital {
  width: 100%;
  margin-top: calc(var(--medical-vw) * 3.6);
}
.hospital li {
  width: calc(var(--medical-vw) * 92.8);
  margin: 0 auto;
  border: solid 1px #eee;
  border-radius: calc(var(--medical-vw) * 1);
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.08);
  background-color: #fff;
  margin-bottom: calc(var(--medical-vw) * 3.6);
  box-sizing: border-box;
  padding: calc(var(--medical-vw) * 4);
}
.hospital li h3 {
  box-sizing: border-box;
  padding-left: calc(var(--medical-vw) * 2.4);
  border-left: solid 3px #157999;
  font-size: calc(var(--medical-vw) * 4.3);
  display: flex;
  justify-content: space-between;
  user-select: none;
  cursor: pointer;
}
.hospital li h3 i {
  font-size: calc(var(--medical-vw) * 5);
}
.hospital li .hospita-info {
  width: 100%;
  margin-top: calc(var(--medical-vw) * 3);
  display: flex;
  justify-content: space-between;
}
.hospital li .hospita-info img {
  width: calc(var(--medical-vw) * 22);
  height: calc(var(--medical-vw) * 22);
}
.hospital li .hospita-info table {
  width: calc(var(--medical-vw) * 59);
  font-size: calc(var(--medical-vw) * 3.5);
  color: #666;
}
.hospital li .hospita-info table tr {
  height: calc(var(--medical-vw) * 6);
}
.hospital li .hospita-info table tr td {
  vertical-align: top;
}
.hospital li .hospita-info table tr td:first-child {
  width: calc(var(--medical-vw) * 15);
}
.hospital li .about {
  display: flex;
  justify-content: flex-end;
  margin-top: calc(var(--medical-vw) * 2);
}
.hospital li .about p {
  width: calc(var(--medical-vw) * 30);
  height: calc(var(--medical-vw) * 8);
  border: solid 1px #157999;
  border-radius: calc(var(--medical-vw) * 2);
  text-align: center;
  line-height: calc(var(--medical-vw) * 8);
  margin-left: calc(var(--medical-vw) * 2);
  font-size: calc(var(--medical-vw) * 4);
  color: #157999;
  user-select: none;
  cursor: pointer;
}
.hospital li .about p i {
  color: #555;
  margin-right: calc(var(--medical-vw) * 1);
}
.hospital-choice { border:0; background:none; font:inherit; color:inherit; text-align:left; cursor:pointer; padding:6px 0; }
</style>
