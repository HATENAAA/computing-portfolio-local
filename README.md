# 王嘉玮 · 本地作品集 / Jiawei Wang · Local Portfolio

八个可在本机运行的项目，涵盖计算成像、交互系统、信号分析和空间数据。仓库包含源码、示例数据和启动脚本。在线作品集提供中英文项目说明、交互演示和实验结果。

Eight projects you can run locally, covering computational imaging, interactive systems, signal analysis and spatial data. This repository includes source code, sample data and launch scripts. The online portfolio provides bilingual case studies, interactive demos and experimental results.

[查看中文作品集](https://hatenaaa.github.io/computing-portfolio-local/?lang=zh) · [View the English portfolio](https://hatenaaa.github.io/computing-portfolio-local/?lang=en)

## 项目 / Projects

| 中文项目 | English project |
| --- | --- |
| [基于深度学习的遥感影像超分辨率重建](https://hatenaaa.github.io/computing-portfolio-local/projects/review/hsi-zh.html) | [Remote Sensing Image Super-Resolution Reconstruction Based on Deep Learning](https://hatenaaa.github.io/computing-portfolio-local/projects/review/hsi-en.html) |
| [VRFitAI — VR健身指导与训练管理平台](https://hatenaaa.github.io/computing-portfolio-local/projects/review/vrfitai-zh.html) | [VRFitAI — VR Fitness Coaching and Training Management Platform](https://hatenaaa.github.io/computing-portfolio-local/projects/review/vrfitai-en.html) |
| [制造订单与库存管理系统](https://hatenaaa.github.io/computing-portfolio-local/projects/review/manufacturing-zh.html) | [Manufacturing Order and Inventory Management System](https://hatenaaa.github.io/computing-portfolio-local/projects/review/manufacturing-en.html) |
| [视觉火焰检测与事件分析系统](https://hatenaaa.github.io/computing-portfolio-local/projects/review/firewatch-zh.html) | [Visual Flame Detection and Event Analysis System](https://hatenaaa.github.io/computing-portfolio-local/projects/review/firewatch-en.html) |
| [虚拟仪器与信号分析系统](https://hatenaaa.github.io/computing-portfolio-local/projects/review/signal-zh.html) | [Virtual Instrumentation and Signal Analysis System](https://hatenaaa.github.io/computing-portfolio-local/projects/review/signal-en.html) |
| [上海红色文化地图](https://hatenaaa.github.io/computing-portfolio-local/projects/review/city-zh.html) | [Shanghai red heritage atlas](https://hatenaaa.github.io/computing-portfolio-local/projects/review/city-en.html) |
| [卫星测深回归](https://hatenaaa.github.io/computing-portfolio-local/projects/review/bathymetry-zh.html) | [Satellite bathymetry](https://hatenaaa.github.io/computing-portfolio-local/projects/review/bathymetry-en.html) |
| [熙心健康体检预约与报告系统](https://hatenaaa.github.io/computing-portfolio-local/projects/review/medical-zh.html) | [Xixin Health Screening Appointments and Reports](https://hatenaaa.github.io/computing-portfolio-local/projects/review/medical-en.html) |

## 在 macOS 上本地运行

1. 下载仓库 ZIP 并解压，或克隆仓库。准备 Python 3.12、Node.js 22.13 或更新版本、JDK 17 或更新版本，以及 Maven。
2. 首次运行时，双击仓库根目录的 `Install Dependencies.command`。
3. 双击 `Launch Portfolio.command`，待浏览器打开首页后选择项目。也可双击 `Launch Project.command` 单独启动一个项目。

VRFitAI 的可选 AI 助手可用 `Configure AI Assistant.command` 配置。示例账号和常见问题见[中文运行指南](https://hatenaaa.github.io/computing-portfolio-local/projects/guide.html)。

## Run locally on macOS

1. Download and extract the repository ZIP, or clone the repository. You need Python 3.12, Node.js 22.13 or newer, JDK 17 or newer, and Maven.
2. For first-time setup, double-click `Install Dependencies.command` in the repository root to install the dependencies.
3. Double-click `Launch Portfolio.command` to launch the portfolio, then choose a project in the browser. Use `Launch Project.command` to start a single project.

Use `Configure AI Assistant.command` to configure the optional VRFitAI assistant. See the [English setup guide](https://hatenaaa.github.io/computing-portfolio-local/projects/guide-en.html) for demo accounts and troubleshooting.

## 在 Windows 上本地运行（WSL 2）

在 WSL 2 的 Ubuntu 24.04 中安装依赖和启动项目，然后用 Windows 浏览器访问。

1. 在管理员 PowerShell 中安装 Ubuntu。

   ~~~powershell
   wsl --install -d Ubuntu-24.04
   ~~~

   按提示重启，打开 Ubuntu 24.04 完成首次设置。回到 PowerShell 运行 `wsl -l -v`，确认 Ubuntu 的 `VERSION` 为 `2`。 [Microsoft WSL 安装指南](https://learn.microsoft.com/zh-cn/windows/wsl/install)

2. 在 Ubuntu 终端中安装 Python 3.12、Java、Maven 和 C++ 构建工具。

   ~~~bash
   sudo apt update
   sudo apt install -y python3 python3-venv openjdk-17-jdk maven build-essential git curl ca-certificates lsof
   ~~~

   在同一个 Ubuntu 环境中安装 Node.js 22.13 或更高版本及 npm。按教程装好 nvm 后，运行 `nvm install 22`。 [Microsoft 的 WSL Node.js 指南](https://learn.microsoft.com/zh-cn/windows/dev-environment/javascript/nodejs-on-wsl)

3. 在 Ubuntu 的主目录克隆仓库，首次运行时安装项目依赖，然后启动完整作品集。

   ~~~bash
   cd ~
   git clone https://github.com/HATENAAA/computing-portfolio-local.git
   cd computing-portfolio-local
   python3 scripts/manage.py install all
   PORTFOLIO_NO_BROWSER=1 python3 scripts/manage.py run all
   ~~~

4. 终端显示「已就绪」后，在 Windows 浏览器中打开显示的网址。默认是 `http://127.0.0.1:8790/`。保持 Ubuntu 终端运行，按 `Ctrl+C` 停止本次启动的服务。

如需单独启动一个项目，可运行 `PORTFOLIO_NO_BROWSER=1 python3 scripts/manage.py run medical`，并将 `medical` 替换为所需的项目 ID。运行 `python3 scripts/manage.py --help` 可查看可用 ID。

## Run locally on Windows (WSL 2)

Install dependencies and run the projects in Ubuntu 24.04 on WSL 2. Open the portfolio in your Windows browser.

1. Install Ubuntu from an administrator PowerShell.

   ~~~powershell
   wsl --install -d Ubuntu-24.04
   ~~~

   Restart if prompted, then open Ubuntu 24.04 to complete first-time setup. In PowerShell, run `wsl -l -v` and check that Ubuntu shows `2` under `VERSION`. [Microsoft WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install)

2. In the Ubuntu terminal, install Python 3.12, Java, Maven and the C++ build tools.

   ~~~bash
   sudo apt update
   sudo apt install -y python3 python3-venv openjdk-17-jdk maven build-essential git curl ca-certificates lsof
   ~~~

   Install Node.js 22.13 or newer and npm inside Ubuntu. If you follow the guide to install nvm, run `nvm install 22` afterwards. [Microsoft guide to Node.js on WSL](https://learn.microsoft.com/en-us/windows/dev-environment/javascript/nodejs-on-wsl)

3. Clone the repository in your Ubuntu home directory. Install the project dependencies on the first run, then start the portfolio.

   ~~~bash
   cd ~
   git clone https://github.com/HATENAAA/computing-portfolio-local.git
   cd computing-portfolio-local
   python3 scripts/manage.py install all
   PORTFOLIO_NO_BROWSER=1 python3 scripts/manage.py run all
   ~~~

4. When the launcher reports that the services are ready, open the printed URL in your Windows browser. The default is `http://127.0.0.1:8790/`. Keep the Ubuntu terminal open and press `Ctrl+C` to stop the services started by that session.

To run a single project, use `PORTFOLIO_NO_BROWSER=1 python3 scripts/manage.py run medical` in the repository root and replace `medical` with the project ID you need. Run `python3 scripts/manage.py --help` to see the available IDs.

## 方法与资料 / Methods and sources

[方法引用、数据来源与软件许可 / References, data sources and software licences (Chinese)](https://hatenaaa.github.io/computing-portfolio-local/projects/credits.html)
