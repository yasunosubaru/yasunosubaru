<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <img src="assets/hero-light.svg" alt="yasunosubaru——武汉大学地空学院，做仪器、桌面工具和 AI 智能体" width="1000">
</picture>

我把测量、运维和安全里反复出现的问题做成工具：GNSS 信号分析、Windows 控制台、离线维基 U 盘、
会自己复现漏洞的 AI 智能体。仓库大多下载就能跑。

这些数字每 6 小时重新算一次，不是截图。

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/rhythm-dark.svg">
  <img src="assets/rhythm-light.svg" alt="近 6 周的每日贡献柱状图与 7 日均线，峰值日已标注" width="1000">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/languages-dark.svg">
  <img src="assets/languages-light.svg" alt="按主语言统计的仓库分布" width="1000">
</picture>

## 项目

<!-- projects:start -->
- **[field-station-agent](https://github.com/yasunosubaru/field-station-agent)** `Python`
  武汉大学地空学院 2026 大创：多智能体 AI 野外台站管理系统 —— 监测/质控/研判/派单/归档闭环。
- **[wsa-dashboard](https://github.com/yasunosubaru/wsa-dashboard)** `Rust`
  Windows Subsystem for Android 的桌面控制台：状态 / 应用 / 存储 / 端口 / 计划任务一个界面管完。
- **[YinHuGuard](https://github.com/yasunosubaru/YinHuGuard)** `Dart`
  只读的 Windows 银狐（ValleyRAT）木马排查工具：一次扫描七个面，GUI/CLI/日志/报告四渠道同源输出；不修改系统、无网络请求。
- **[Strata-Console](https://github.com/yasunosubaru/Strata-Console)** `TypeScript`
  Desktop console for the local Strata inference engine (Qwen3.8-Flash-Next IQ2\_XS): chat, live monitor, context switching…
- **[crowbar](https://github.com/yasunosubaru/crowbar)** `TypeScript`
  Local file force-teardown tool for Windows - diagnose first, tiered delete (L1/L2/L3), LOTO confirm tag, portable single exe
- **[CyberStrike](https://github.com/yasunosubaru/CyberStrike)** `TypeScript`
  Open-source AI-powered offensive security harness for automated penetration testing.
<!-- projects:end -->

想聊哪个仓库，直接开 issue 就行。

---

<sub>数据由 [GitHub Actions](.github/workflows/profile.yml) 每 6 小时重算，SVG 在本仓库里生成
（[`tools/`](tools)），没有用第三方卡片服务。贡献窗口为最近 12 个月，语言统计不含 fork；
文案在 [`profile.config.json`](profile.config.json)。</sub>
