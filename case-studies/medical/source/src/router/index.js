import { createRouter, createWebHashHistory } from "vue-router"

const routes = [
    {
        path: "/",
        name: "Home",
        component: () => import("../views/Login.vue")
    },
    {
        path: "/login",
        name: "Login",
        component: () => import("../views/Login.vue")
    },
    {
        path: "/register",
        name: "Register",
        component: () => import("../views/Register.vue")
    },
    {
        path: '/index',
        name: 'Index',
        component: () => import('../views/Index.vue')
    },
    {
        path: '/appointment',
        name: 'Appointment',
        component: () => import('../views/Appointment.vue')
    },
    {
        path: '/personal',
        name: 'Personal',
        component: () => import('../views/Personal.vue')
    },
    {
        path: '/hospital',
        name: 'Hospital',
        component: () => import('../views/Hospital.vue')
    },
    {
        path: '/setmeal',
        name: 'SetMeal',
        component: () => import('../views/SetMeal.vue')
    },
    {
        path: '/selectdate',
        name: 'SelectDate',
        component: () => import('../views/SelectDate.vue')
    },
    {
        path: '/confirmorder',
        name: 'ConfirmOrder',
        component: () => import('../views/ConfirmOrder.vue')
    },
    {
        path: '/appointmentsuccess',
        name: 'AppointmentSuccess',
        component: () => import('../views/AppointmentSuccess.vue')
    },
    {
        path: '/appointmentlist',
        name: 'AppointmentList',
        component: () => import('../views/AppointmentList.vue')
    },
    {
        path: '/reportlist',
        name: 'ReportList',
        component: () => import('../views/ReportList.vue')
    },
    {
        path: '/report',
        name: 'Report',
        component: () => import('../views/Report.vue')
    }
]
const router = createRouter({
    history: createWebHashHistory(),
    routes
})
export default router
