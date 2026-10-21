# 这个主页怎么做的

一条数据管线 + 六张手画的 SVG。目标是把 GitHub 主页最缺的东西补上：**一眼能看懂的数据**，
而不是把自带的贡献图再抄一遍。

## 视觉方向

**紫 → 青渐变 + bento 网格。** 这是 2026 年 GitHub 个人主页的主流样式：一张渐变横幅打头，
下面用 HTML 表格拼出 2×2 + 通栏的 bento 布局，每张卡片圆角、带描边，明暗两套配色。

两条纪律：

- 页面上的每个数字都必须是真的（来自 GitHub API），没有占位符和装饰性数字。
- 不依赖第三方图片服务：没有 capsule-render、typing-svg、github-readme-stats。
  全部卡片由本仓库的 Python 画成 SVG 提交进仓库，Actions 每 6 小时重画一次。

## 颜色

| 用途 | 亮色 | 暗色 |
| --- | --- | --- |
| 卡片底 | `#ffffff` | `#161b22` |
| 描边 | `#d0d7de` | `#30363d` |
| 主文字 | `#1f2328` | `#e6edf3` |
| 次文字 | `#424a53` | `#c9d1d9` |
| 弱文字 | `#59636e` | `#9198a1` |
| 渐变 | `#7c3aed` → `#4e7fd4` → `#06b6d4` | 同左 |

语言色取 GitHub linguist 官方色，降饱和到 75%——两边主题都压得住。

### 明暗主题怎么做的

每张 SVG **只有一个文件**，主题写在 SVG 内部：

```css
:root { --card:#ffffff; --ink:#1f2328; ... }
@media (prefers-color-scheme: dark) {
  :root { --card:#161b22; --ink:#e6edf3; ... }
}
```

图元用 `fill="var(--card)"` 取色。这样同一个文件放进表格单元格里也能自动变色，
不用 `<picture>`、不用两套资源，也不会因为 GitHub 清洗 HTML 而失效。

## 字体

- 读数、标签、时间戳：`ui-monospace` / Cascadia Mono / SF Mono / Consolas——仪表的语气。
- 标题与句子：系统 UI 无衬线（含中文回退 `Microsoft YaHei` / `PingFang SC` / `Noto Sans SC`）。

SVG 里不能加载外部字体（作为 `<img>` 渲染时），所以性格来自字号对比和字距，而不是换字体。

## 版式

六张图，README 里用 HTML 表格拼成 bento：

| 卡片 | 尺寸 | 内容 |
| --- | --- | --- |
| **banner** | 1200×220 | 渐变横幅：呼号 + 最近一次计算时间 |
| **stats** | 600×236 | 2×2 读数：公开仓库 / 近一年贡献 / PR / Issue |
| **languages** | 600×236 | 主语言堆叠条 + 排名 |
| **heatmap** | 1200×250 | 全年 53 周 × 7 天贡献热力图 |
| **repos** | 600×330 | 最近更新的 6 个仓库 |
| **monthly** | 600×330 | 注册以来的月度活跃柱状图 |

排布：

```
banner
┌────────────┬────────────┐
│   stats    │ languages  │
├────────────┴────────────┤
│          heatmap        │
├────────────┬────────────┤
│   repos    │  monthly   │
└────────────┴────────────┘
```

`<td width="50%">` 用百分比宽度，移动端 GitHub 会横向滚动而不是压扁。

## 动效

只有一处：横幅时间戳旁的小灯呼吸（3.8s），并包在
`@media (prefers-reduced-motion: reduce)` 里——不支持动画的渲染器直接显示最终状态。

## 数据管线

```
GitHub GraphQL + 公开日历 HTML + 匿名搜索 API
        │  tools/fetch_data.py      → data/profile.json（提交进仓库，便于 diff）
        ▼
   tools/render.py                 → assets/*.svg（6 张）
```

- 每 6 小时由 `.github/workflows/profile.yml` 跑一次，有变化才提交。
- **只统计公开数据。** 账号与仓库查询一律带 `privacy: PUBLIC`；贡献只读
  `github.com/users/<login>/contributions` 的匿名 HTML——访客看到多少就是多少，
  token 只用来提额度，不会把私有贡献算进来。
- PR / Issue 计数走**匿名** search API（`public_rest`，不带 token）：带 token 会把私有仓库
  的 issue 也数进去，那就不是访客看到的数字了。
- **刷成就用的仓库不计入。** `profile.config.json` 的 `exclude_repos` 列出这类仓库，统计时
  把它们的仓库数、PR、Issue、提交、PR 事件全部扣掉——不然主页会挂着 1200 个一次性 PR 的
  数字，热力图也会变成一堵墙。账号本身照旧是那样，只有主页按"真实作品量"展示。
- 仓库数据优先 GraphQL；失败时退到 REST + 逐仓库 languages（REST 侧过滤 fork）。
- 任一数据源拉不到就报错退出，**不会**用空数据覆盖上一版图。

## 改东西

| 想改 | 改哪 |
| --- | --- |
| 呼号 | `profile.config.json` |
| 配色、渐变 | `tools/theme.py` 的 `LIGHT` / `DARK` / `GRADIENT` |
| 字号、间距、版式常量 | `tools/render.py` 顶部的常量与各卡片函数 |
| 图的顺序 / 增减 | `README.md` 的 `<table>`、`tools/render.py` 的 `CARDS` |
| 本地看一眼 | `python tools/light_preview.py`（浅色主题预览） |

本地刷新：

```powershell
powershell -File tools\update.ps1
# 然后看 .preview/bento.html
```
