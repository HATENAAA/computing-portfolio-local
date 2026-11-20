export const programs = [
  {
    id: "rhythm",
    title: "左右节奏",
    legacyTitle: "自由训练（旧版）",
    english: "ALTERNATE & SELECT",
    subtitle: "按提示交替击打左右悬靶",
    tag: "组合训练",
    color: "#b3d9e5",
    seconds: 120,
    description:
      "跟随发光靶心交替击打。桌面可点击靶心或按对应数字键，VR 中用同侧手柄瞄准并扣动扳机。",
    equipment: "无需实体器械",
    mechanic: "左右交替 · 连击组合",
    steps: [
      "站在或坐在舒适的位置，先看清左右提示。",
      "靶心出现在左靶时用左手，出现在右靶时用右手。",
      "桌面可点击，或按 1—5；VR 扳机使用提示对应的手。",
    ],
    caption: "建立左右交替与目标切换的节奏。",
    level: "入门友好",
  },
  {
    id: "focus",
    title: "稳定停留",
    legacyTitle: "专注训练（旧版）",
    english: "HOLD & SWITCH",
    subtitle: "保持指针停留，进度条填满后切换目标",
    tag: "停留训练",
    color: "#a9d9e1",
    seconds: 120,
    description:
      "将光标或手柄射线停在靶面亮条上，等进度条填满，再移向下一处。",
    equipment: "支持坐姿体验",
    mechanic: "持续停留 · 稳定切换",
    steps: [
      "选择舒适的活动范围，不必追求大幅度。",
      "将光标或控制器射线停留在带双竖线的亮条。",
      "进度条填满后移向下一处；键盘按住对应的 1—5。",
    ],
    caption: "练习连续停留与目标切换；记录光标或射线的稳定停留时间。",
    level: "低节奏",
  },
  {
    id: "flow",
    title: "反应与抑制",
    legacyTitle: "活力训练（旧版）",
    english: "REACT & RECOVER",
    subtitle: "双箭头时击打，叉号时等待",
    tag: "间歇训练",
    color: "#f1b297",
    seconds: 120,
    description:
      "击打双箭头之间的靶心，看到叉号时停手。每 20 秒练习后休息 5 秒，练习反应与抑制。",
    equipment: "无需实体器械",
    mechanic: "Go / No-Go · 20∶5 间歇",
    steps: [
      "双箭头提示击打，叉号提示停手。",
      "选择错误、漏过浅蓝色目标会分别记录。",
      "每 20 秒进入 5 秒休息；休息时不接受命中。",
    ],
    caption: "按 Go / No-Go 提示选择或等待，分段记录反应表现。",
    level: "渐进挑战",
  },
  {
    id: "sequence",
    title: "顺序记忆",
    legacyTitle: "顺序记忆",
    english: "WATCH & RECALL",
    subtitle: "先看亮起顺序，再按原顺序点回去",
    tag: "顺序训练",
    color: "#c5b8ef",
    seconds: 120,
    description: "先观察悬靶逐个亮起，提示结束后按原顺序选择目标。",
    equipment: "支持坐姿体验",
    mechanic: "观察顺序 · 依次复现",
    steps: [
      "观察阶段只看，不用点。记住每条亮条的顺序。",
      "进入复现后点击对应位置，或按亮条标过的数字键。VR 用手柄瞄准并扣动扳机。",
      "点错可继续尝试，答完或计时结束后会换一组。",
    ],
    caption: "舒适、标准、挑战难度分别记忆 3、4、5 个位置。",
    level: "分级记忆",
  },
];
export const programIds = programs.map(({ id }) => id);
export function getProgram(id) {
  return programs.find((p) => p.id === id);
}
