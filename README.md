# 王嘉玮 · 本地作品集 / Jiawei Wang · Local Portfolio

八个可在本机运行的项目，涵盖计算成像、交互系统、信号分析和空间数据。仓库包含源码、示例数据和启动脚本。在线作品集提供中英文项目说明、交互演示和实验结果。

Eight projects you can run locally, covering computational imaging, interactive systems, signal analysis and spatial data. This repository includes source code, sample data and launch scripts. The online portfolio provides bilingual case studies, interactive demos and experimental results.

[查看中文作品集](https://hatenaaa.github.io/computing-portfolio-local/?lang=zh) · [View the English portfolio](https://hatenaaa.github.io/computing-portfolio-local/?lang=en)

## 下载 / Downloads

[Windows x64 ZIP](https://github.com/HATENAAA/computing-portfolio-local/releases/latest/download/portfolio-windows-x64.zip) · [macOS ZIP](https://github.com/HATENAAA/computing-portfolio-local/releases/latest/download/portfolio-macos.zip)

解压后双击 `index.html` 即可浏览中英文静态作品集。要运行完整应用，按下面对应系统的步骤安装依赖并启动。

After extracting either ZIP, double-click `index.html` to browse the bilingual portfolio. Follow the instructions for your operating system to run the full applications.


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

1. 下载仓库 ZIP 并解压，或克隆仓库。准备 Python 3.12、Node.js 22.13 或更新版本、JDK 17 或更新版本，以及 Maven。火焰检测需要可用的 C++ 编译器，可通过 Xcode Command Line Tools 安装。
2. 首次运行时，双击仓库根目录的 `Install Dependencies.command`。
3. 双击 `Launch Portfolio.command`，待浏览器打开首页后选择项目。也可双击 `Launch Project.command` 单独启动一个项目。

VRFitAI 的可选 AI 助手可用 `Configure AI Assistant.command` 配置。示例账号和常见问题见[中文运行指南](https://hatenaaa.github.io/computing-portfolio-local/projects/guide.html)。

## Run locally on macOS

1. Download and extract the repository ZIP, or clone the repository. You need Python 3.12, Node.js 22.13 or newer, JDK 17 or newer, and Maven. Flame detection needs a C++ compiler, available through Xcode Command Line Tools.
2. For first-time setup, double-click `Install Dependencies.command` in the repository root to install the dependencies.
3. Double-click `Launch Portfolio.command` to launch the portfolio, then choose a project in the browser. Use `Launch Project.command` to start a single project.

Use `Configure AI Assistant.command` to configure the optional VRFitAI assistant. See the [English setup guide](https://hatenaaa.github.io/computing-portfolio-local/projects/guide-en.html) for demo accounts and troubleshooting.

## 在 Windows 上原生运行（x64）

1. 下载 **Windows x64 ZIP** 并完整解压。在 Windows 中安装 Python 3.12 x64（含 Python Launcher）、Node.js 22.13 或更新版本（含 npm）、JDK 17 或更新版本，以及 Maven。将 Node.js、Java 和 Maven 加到 PATH，并将 JAVA_HOME 指向 JDK。
2. 首次运行时双击 `Install Dependencies.cmd`。Windows ZIP 内含火焰检测的 x64 DLL。若从源码克隆，则在安装了 C++ 工具的 Visual Studio x64 Native Tools Command Prompt 中运行该脚本以编译 DLL。
3. 双击 `Launch Portfolio.cmd` 启动八个项目，或用 `Launch Project.cmd` 选择单个项目。浏览器默认打开 `http://127.0.0.1:8790/`。按 `Ctrl+C` 停止本次启动的服务。

可用 `Configure AI Assistant.cmd` 配置 VRFitAI 的可选 AI 助手。

## Run natively on Windows (x64)

1. Download and fully extract the **Windows x64 ZIP**. On Windows, install Python 3.12 x64 with the Python Launcher, Node.js 22.13 or newer with npm, JDK 17 or newer, and Maven. Add Node.js, Java and Maven to PATH and set JAVA_HOME to the JDK.
2. Double-click `Install Dependencies.cmd` on the first run. The Windows ZIP includes the x64 DLL for flame detection. For a source checkout, run the installer from Visual Studio's x64 Native Tools Command Prompt with the C++ build tools installed.
3. Double-click `Launch Portfolio.cmd` to start all eight projects, or `Launch Project.cmd` to select one project. The browser opens `http://127.0.0.1:8790/` by default. Press `Ctrl+C` to stop the services launched in that session.

Use `Configure AI Assistant.cmd` to configure the optional VRFitAI assistant.

## 方法与资料 / Methods and sources

[方法引用、数据来源与软件许可 / References, data sources and software licences (Chinese)](https://hatenaaa.github.io/computing-portfolio-local/projects/credits.html)
