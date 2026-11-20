export async function deviceCapabilities(nav=globalThis.navigator,secure=globalThis.isSecureContext) {
 if(!secure)return {available:false,label:'当前连接不支持 VR',reason:'请使用 HTTPS 或 localhost 安全环境。'};
 if(!nav?.xr)return {available:false,label:'当前浏览器不提供 WebXR',reason:'可以使用桌面交互；进入 VR 需要支持 WebXR 的浏览器与头显。'};
 try {const available=await nav.xr.isSessionSupported('immersive-vr');return {available,label:available?'浏览器报告支持 VR 会话':'当前设备无法进入 VR',reason:available?'进入场景后点击 VR 按钮；仍需检查控制器权限与双手追踪。':'可继续使用桌面模式；此结果不代表任何头显实测。'};}
 catch{return {available:false,label:'无法确认 VR 能力',reason:'请检查浏览器权限或选择桌面模式。'};}
}
