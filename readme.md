# NBA 1997-2020投篮数据可视分析系统
## 运行环境
- Node.js版本： 24.18.0
- 包管理器：pnpm
- 技术栈：vite + vue3 + typeScript + pinia + vue-echarts

## 原始数据集
1. `NBA Shot Locations 1997 - 2020.csv`：全联盟历年球员每一次出手的原始点位、命中、时间、球队基础数据
2. `nba_team_standings.csv`：各球队赛季战绩排名配套数据

## Python数据预处理文件说明
### 图表数据生成脚本
- `build_kde_data.py`：生成KDE双峰相变分布图所需聚合数据
- `build_sankey_data.py`：生成历年投篮流量桑基图结构化数据
- `build_three_point_data.py`：统计球队三分出手数据，生成球队分层分析数据集
- `build_time_fg_data.py`：计算剩余时间-投篮命中率衰减曲线数据
- `fetch_team_standings.py`：读取球队战绩榜单数据，关联球队打法与战绩表现
- `patch_agg_extra_seasons.py`：补齐多赛季数据，完成全时段数据合并聚合

### 数据质量校验文件
- `data_quality_check.py`：统一校验两份原始数据的缺失值、异常值、重复数据
- 各类`quality_report`文件：输出文本+JSON格式的数据清洗质检报告，记录脏数据剔除明细、数据修正记录

## 目录结构
```tree
├── public
│   ├── data           # Python脚本输出的正式可视化JSON数据文件
│   ├── demo-data      # 演示用测试数据
│   └── 各类图片资源（背景图、球星卡片、NBA标识、图标素材）
├── src
│   ├── charts         # Hexbin热力图、KDE、桑基图、命中率曲线等图表封装
│   ├── components     # 页面通用UI组件、筛选控制面板
│   ├── pages          # 系统主展示页面
│   ├── stores         # Pinia全局状态仓库，统一管理筛选联动参数
│   ├── styles         # 全局公共样式文件
│   ├── util           # 通用工具函数
│   ├── App.vue
│   ├── main.ts        # 项目入口文件
│   └── router.ts      # 路由配置
├── python_process     # 全部数据处理脚本 + 数据质检报告文件
│   ├── 各类build_*.py  # 分模块生成对应图表数据
│   ├── fetch_team_standings.py、patch_agg_extra_seasons.py
│   ├── data_quality_check.py
│   └── 所有quality_report质检输出文件
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── vite.config.ts
├── tsconfig系列配置文件
├── setup.bat          # Windows一键部署批处理脚本
└── .gitignore
```
## 系统核心功能

1. 可视化视图：球场 Hexbin 出手热力图、KDE 投篮密度曲线、赛季投篮分布桑基图、出手命中率衰减曲线、球队三分转型分层对比图；
2. 跨视图联动：基于 Pinia 全局状态管理，赛季筛选、球队筛选、图表点击事件可同步刷新全部可视化视图，实现双向交互；
3. 视觉美化：内置球星素材、NBA 主题背景、悬浮 Tooltip 展示出手频次、命中率详细指标。

## 项目启动方式
### 方式1：命令行启动
```bash
用VS Code打开NBA_Shot_Position-main文件夹，调出终端
# 安装项目依赖
pnpm install
# 运行本地开发服务
pnpm dev
运行后会弹出http://localhost:5173/，打开此网页即可
```
### 方式 2：Windows 快捷启动
```bash

直接双击根目录下 `setup.bat` 文件，等待脚本自动完成依赖安装并启动服务，
窗口中会弹出：“Network: http://xx.xxx.xxx.xx:5173/”，打开此网页即可
```