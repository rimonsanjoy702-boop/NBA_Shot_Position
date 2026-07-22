# _pending — 待定文件

此文件夹存放从活跃代码库中移出的文件，不参与项目编译。每个文件保留完整原始内容，以备后续参考或恢复。

---

## 文件清单

| 文件 | 原始路径 | 移出原因 |
|------|----------|----------|
| `DemoPage.vue` | `src/pages/DemoPage.vue` | 桑基图演示页面，与 NBA 投篮可视化项目无关 |
| `ConnectionGraph.vue` | `src/components/ConnectionGraph.vue` | 桑基图演示组件（随机散点图），与 NBA 项目无关 |
| `UserConnectionGraph.vue` | `src/components/UserConnectionGraph.vue` | 桑基图演示组件，与 NBA 项目无关 |
| `UserDistributionPieChart.vue` | `src/components/UserDistributionPieChart.vue` | 桑基图演示组件（饼图），与 NBA 项目无关 |
| `data.ts` | `src/data.ts` | 桑基图数据加载器，与 NBA 项目无关 |
| `colors.ts` | `src/util/colors.ts` | 桑基图兴趣分类色板，仅被桑基图组件引用 |
| `models.ts` | `src/models.ts` | 原始共享类型文件。已被拆分：Hexbin 类型迁移至 `src/charts/hexbin/types.ts`，桑基图类型随桑基图代码一同移出。此文件保留原貌备查 |
| `vue.svg` | `src/assets/vue.svg` | Vite 脚手架残留文件，项目中未引用 |
| `demo-data/` | `public/demo-data/` | 桑基图演示数据（`user_stat_nodes.json`、`user_stat_links.json`），与 NBA 项目无关 |

---

## 相关路由

- `router.ts` 中的 `/demo` 路由已删除，因为其指向的 `DemoPage.vue` 已移至此文件夹。
