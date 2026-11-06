# SuperLoader 兼容样本集 v1（待审）

口径：MC 1.21.1，Modrinth 前 600 个 Fabric mod → 127 个只有 Fabric 构建 → 人工筛出下列；
排除 API/运行时库与 L3 渲染重写（见文末）。主指标只用「主样本集」。

主样本集 42 个；基础设施 8 个；内容组（阶段 2）6 个。

## 主样本集（90% 分母，42 个）

| # | mod | 版本 | 类型 | 必需前置（Fabric 版） | 抽查项 | 下载 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `modmenu` | 11.0.5 | 工具 | placeholder-api | 打开 Mods 列表，能看到全部 mod | 164,976,763 |
| 2 | `zoomify` | 2.15.2+1.21.1 | 工具 | yacl, fabric-language-kotlin | 按 C 缩放（含平滑过渡） | 74,414,182 |
| 3 | `krypton` | 0.2.8 | 优化 | — | 无感；进世界后网络正常（无断连） | 46,229,628 |
| 4 | `language-reload` | 1.7.6+1.21.1 | 优化 | — | F3+T 重载资源包后语言/字体仍正常 | 45,183,642 |
| 5 | `presence-footsteps` | 1.11.2+1.21 | 装饰 | — | 走路/跳跃有脚步声（需资源包） | 42,277,682 |
| 6 | `debugify` | 1.21.1+1.1 | 优化 | yacl | F3 调试屏出现 debugify 补充项；配置菜单可开 | 40,207,856 |
| 7 | `visuality` | 0.7.7+1.21 | 装饰 | cloth-config | 区块加载/方块破坏粒子出现 | 31,557,982 |
| 8 | `morechathistory` | 1.3.1 | 社交 | — | 聊天栏上滚超过 100 条 | 30,839,328 |
| 9 | `litematica` | 0.19.61 | 工具 | malilib | M 打开 Litematica 菜单，加载一次放置预览 | 28,990,071 |
| 10 | `fallingleaves` | 1.17.1+1.21.1 | 装饰 | cloth-config | 树林里树叶飘落粒子 | 28,633,523 |
| 11 | `optigui` | 2.3.0-beta.9+1.21 | 装饰 | fabric-language-kotlin | 装 CIT 资源包后容器界面贴图替换生效 | 28,386,639 |
| 12 | `better-mount-hud` | 1.2.4 | 工具 | — | 骑马/坐船时 HUD 正常 | 26,027,931 |
| 13 | `fastquit` | 3.0.0+1.20.6 | 优化 | cloth-config | 关闭游戏立即退出（无卡顿） | 25,654,196 |
| 14 | `fabrishot` | 1.14.1 | 工具 | — | F9 截图并保存 | 20,203,589 |
| 15 | `replaymod` | 1.21-2.6.28 | 工具 | — | 打开回放菜单，开始录制 | 19,729,159 |
| 16 | `paginatedadvancements` | 2.5.1 | 工具 | cloth-config | 进度界面翻页正常 | 19,083,152 |
| 17 | `main-menu-credits` | 1.2.0 | 装饰 | — | 主菜单右下角滚动字幕 | 18,736,324 |
| 18 | `tooltipfix` | 1.1.1-1.20 | 优化 | — | 长 tooltip 不超出屏幕 | 17,456,576 |
| 19 | `better-ping-display-fabric` | 1.21.1-1.1.1 | 工具 | — | 多人界面 ping 显示正常 | 14,520,785 |
| 20 | `beautify-refabricated` | 3.6.5-fabric+1.21.1 | 装饰 | cloth-config | 放置一件装饰方块 | 10,954,849 |
| 21 | `carpet` | 1.4.147 | 机制 | — | /carpet 命令有响应 | 12,041,082 |
| 22 | `no-resource-pack-warnings` | 1.3.1 | 工具 | — | 无资源包警告弹窗 | 9,910,559 |
| 23 | `stendhal` | 1.4.1-1.21 | 工具 | — | 书与笔界面出现新功能 | 9,470,776 |
| 24 | `forcecloseworldloadingscreen` | 2.2.3 | 工具 | — | 加载世界时关闭界面不崩 | 8,437,014 |
| 25 | `tweakeroo` | 0.21.61 | 工具 | malilib | M 打开 Tweakeroo 菜单，开关一项 | 8,210,932 |
| 26 | `status-effect-bars` | 1.0.6 | 装饰 | cloth-config | 状态效果条显示（吃一瓶药水） | 8,179,488 |
| 27 | `cave-dust` | 3.0.1 | 装饰 | — | 洞穴内看到尘埃粒子 | 7,744,875 |
| 28 | `wakes` | 0.4.1+1.21.1 | 装饰 | — | 水面/船尾迹粒子 | 7,543,089 |
| 29 | `better-selection` | 1.6.8 | 工具 | — | 方块选中框更贴合形状 | 7,483,088 |
| 30 | `chatpatches` | 8.0.0+1.21.1-fabric | 装饰 | yacl | 聊天栏复制/时间戳正常 | 7,448,321 |
| 31 | `custom-splash-screen` | 2.2.2 | 装饰 | — | 启动时自定义 splash | 6,943,415 |
| 32 | `held-item-info` | 1.7.0 | 装饰 | — | 手持物品信息 HUD | 6,304,969 |
| 33 | `hold-my-items` | 4.3 | 装饰 | modmenu, cloth-config | 手持物品位置/动画变化 | 6,237,410 |
| 34 | `connectiblechains` | 2.5.7+1.21.1 | 装饰 | cloth-config | 铁链连接方块正常渲染 | 5,736,974 |
| 35 | `lazy-language-loader` | 0.3.7 | 优化 | — | 切换语言不卡死 | 5,254,432 |
| 36 | `fpsdisplay` | 4.2.1+1.21.1 | 工具 | — | FPS 显示叠加层 | 5,061,029 |
| 37 | `reacharound` | 1.3.1 | 工具 | — | 远距离放置方块（reach 扩展） | 5,354,874 |
| 38 | `inmis` | 2.8.2-1.21.1 | 玩法 | cloth-config | 打开背包物品栏 | 5,490,236 |
| 39 | `universal-graves` | 3.4.4+1.21 | 机制 | polymer | 死亡后墓碑生成并取回物品 | 5,292,938 |
| 40 | `lenient-death` | 1.2.5+1.21.1 | 机制 | — | 死亡不掉落/惩罚可配置 | 5,147,352 |
| 41 | `totemcounter` | 1.6.1+mc1.21 | 工具 | ukulib | 图腾数量 HUD | 5,136,309 |
| 42 | `minihud` | 0.32.60 | 工具 | malilib | M 打开 Minihud 菜单，开一个信息行 | 7,064,484 |

## 基础设施集（单独统计，8 个）

| # | mod | 版本 | 类型 | 必需前置（Fabric 版） | 抽查项 | 下载 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `fabric-language-kotlin` | 1.14.2+kotlin.2.4.21 | 库 | — | 依赖它的 mod（zoomify/optigui）能起来 | 134,987,064 |
| 2 | `malilib` | 0.21.10 | 库 | — | 依赖它的 mod（litematica/tweakeroo/minihud）能起来 | 40,373,141 |
| 3 | `cardinal-components-api` | 6.1.3 | 库 | — | 依赖它的 mod 能起来 | 16,255,729 |
| 4 | `cloth-config` | 15.0.140+fabric | 库（原生版） | — | 配置界面能打开 | 189,907,387 |
| 5 | `yacl` | 3.8.2+1.21.1-fabric | 库（原生版） | — | 配置界面能打开 | 138,638,186 |
| 6 | `resourceful-lib` | 3.0.12 | 库 | — | 依赖它的 mod 能起来 | 38,229,302 |
| 7 | `placeholder-api` | 2.4.2+1.21 | 库 | — | modmenu 依赖 | 77,903,506 |
| 8 | `ukulib` | 1.4.1+1.21 | 库 | — | totemcounter 依赖 | 15,392,583 |

## 内容组（阶段 2，单独统计，6 个）

| # | mod | 版本 | 类型 | 必需前置（Fabric 版） | 抽查项 | 下载 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `farmers-delight-refabricated` | 1.21.1-3.3.6 | 内容 | — | 种植/烹饪一件食物 | 17,430,264 |
| 2 | `betterend` | 21.0.11 | 内容 | worldweaver, bclib | 创造物品栏出现 BetterEnd 方块 | 16,271,197 |
| 3 | `betternether` | 21.0.11 | 内容 | worldweaver, bclib | 进入下界看新群系 | 13,968,279 |
| 4 | `friends-and-foes` | fabric-5.0.4+mc1.21.1 | 内容 | resourceful-lib | 创造物品栏出现新生物蛋 | 12,536,666 |
| 5 | `the-bumblezone-fabric` | 7.17.3+1.21.1-fabric | 内容 | midnightlib, resourceful-lib | 进入 Bumblezone 维度 | 10,058,521 |
| 6 | `repurposed-structures-fabric` | 7.5.22+1.21.1-fabric | 内容 | midnightlib | 新世界生成后结构出现 | 15,176,193 |

## 排除：L3 渲染/内核重写（不做，仅记录）

`vulkanmod`, `exordium`, `nvidium`, `cull-less-leaves`, `indium`, `c2me-fabric`, `ebe`, `animatica`, `skyboxify`, `flashback`, `threadtweak`, `bobby`, `axiom`, `cit-resewn`, `particular`, `eating-animation`, `capes`, `gamma-utils`, `sodium-extra`, `iris`, `sodium`, `distancetransform`

## 测试方法要点

1. 每个样本单独一次 launch：基础前置集（FFAPI/Connector + 该样本所需前置）+ 1 个候选，跑完恢复 `mods/`；
2. 判定：无 FATAL + 无 crash report + 进入「新的世界」+ 抽查项通过；
3. 前置有原生版（cloth-config / yacl）时装原生；Fabric-only 前置（FLK / malilib / cardinal-components / resourceful-lib）装 Fabric 版，失败会连坐，归因时先看前置；
4. 单 mod 跑是硬要求：坏 jar 会让 Connector early remap 整轮跳过（HANDOFF 决策 28）。
