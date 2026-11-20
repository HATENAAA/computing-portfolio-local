export const modules = [
  { id: "overview", name: "运营概览", icon: "grid" },
  { id: "orders", name: "订单中心", icon: "orders" },
  { id: "materials", name: "物料与 BOM", icon: "orders", roles: ["factoryAdmin", "superAdmin"] },
  { id: "schedule", name: "生产排程", icon: "schedule" },
  { id: "equipment", name: "设备资产", icon: "device", roles: ["factoryAdmin", "superAdmin"] },
  { id: "quality", name: "异常与质量", icon: "quality" },
  { id: "factories", name: "工厂网络", icon: "factory" },
  { id: "users", name: "账号目录", icon: "users", roles: ["superAdmin"] },
];

export function visibleModules(role) {
  return modules.filter(module => !module.roles || module.roles.includes(role));
}
