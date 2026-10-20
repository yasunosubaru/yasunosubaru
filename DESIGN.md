# 这个主页怎么做的

一条数据管线 + 一套手画的图。目标不是把 GitHub 自带的热力图再抄一遍，而是画 GitHub
不显示的东西：每天的工作节奏、峰值、连续天数、按主语言聚类的仓库构成。

## 视觉方向

**野外台站的仪表盘。** 这个人的仓库是 GNSS 信号分析仪、C/N₀ 分析仪、野外台站智能体——
测量、读数、记录是这批项目共同的语汇。所以主页做成一块仪表：等宽字体读数、发丝分隔线、
一条琥珀色的信号线，而不是渐变卡片和霓虹光。

两条纪律：

- 页面上的每个数字都必须是真的（来自 GitHub API），没有占位符和装饰性数字。
- 只留一个记忆点：琥珀色。其余全部是墨色、灰阶和留白。

## 颜色

| 用途 | 亮色 | 暗色 |
| --- | --- | --- |
| 纸面 / 底板 | `#F6F8F9` | `#0C1218` |
| 主文字 | `#101A21` | `#E8EFF4` |
| 次文字 | `#465862` | `#A6B6C2` |
| 弱文字 | `#66787F` | `#8093A0` |
| 发丝线 | `#D7E0E5` / `#E6EDF0` | `#22303B` / `#1A2732` |
| 强调（唯一） | `#A96D12` | `#E3A93F` |

语言色取 GitHub linguist 的官方色，降饱和 45% 再向底色混 14%，保留辨识度但不抢戏。

## 字体

- 读数、标签、时间戳：`ui-monospace` / Cascadia Mono / SF Mono / Consolas——仪表的语气。
- 标题与句子：系统 UI 无衬线（含中文回退 `Microsoft YaHei` / `PingFang SC` / `Noto Sans SC`）。

SVG 里不能加载外部字体（作为 `<img>` 渲染时），所以性格来自字号对比和字距，而不是换字体。

## 版式

三块图，全部 1000 宽：

1. **hero**（1000×272）：台站铭牌。呼号 44px、一句话、四个读数、发丝分隔。
2. **rhythm**（1000×330）：近 6 周每日贡献（灰柱）+ 7 日均线（琥珀）+ 峰值标注；
   下方一排是近一年的活跃天 / 最长连续 / 活跃日均。
3. **languages**（1000×272）：按主语言统计的堆叠条 + 排名列表。

README 里不放任何正文：三张图上下排开，数据本身就是全部内容。

数据面板不加底色、不加边框，直接落在 GitHub 的页面底色上；只有 hero 是一块板。
这样在亮色和暗色主题里都不会出现"贴上去的卡片"。

## 明暗双主题

每张图生成两份，README 用 `<picture>` + `prefers-color-scheme` 选：

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <img src="assets/hero-light.svg" width="1000" alt="...">
</picture>
```

## 动效

只有一处：hero 里名字下方的琥珀短线用 `stroke-dashoffset` 画出来，时间戳旁的小灯呼吸
（3.8s）。全部包在 `@media (prefers-reduced-motion: no-preference)` 里——不支持动画的渲染器
直接显示最终状态，不会出现"线不见了"。

## 数据管线

```
GitHub GraphQL + 公开日历 HTML
        │  tools/fetch_data.py      → data/profile.json（提交进仓库，便于 diff）
        ▼
   tools/render.py                 → assets/*-{light,dark}.svg
```

- 每 6 小时由 `.github/workflows/profile.yml` 跑一次，有变化才提交。
- **只统计公开数据。** 账号与仓库查询一律带 `privacy: PUBLIC`；贡献只读
  `github.com/users/<login>/contributions` 的匿名 HTML——访客看到多少就是多少，
  token 只用来提额度，不会把私有贡献算进来。
- 仓库数据优先 GraphQL；失败时退到 REST + 逐仓库 languages（REST 侧过滤 fork）。
- 任一数据源拉不到就报错退出，**不会**用空数据覆盖上一版图。

## 改东西

| 想改 | 改哪 |
| --- | --- |
| 呼号、学校、一句话 | `profile.config.json` |
| 配色、字号 | `tools/theme.py`，`tools/render.py` 顶部的版式常量 |
| 图的顺序 / 增减 | `README.md` 的 `<picture>` 区块，`tools/render.py` 的 `render_all()` |

本地刷新：

```powershell
powershell -File tools\update.ps1
# 然后看 .preview/preview-light.html 和 preview-dark.html
```
