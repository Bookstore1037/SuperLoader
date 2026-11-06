# SuperLoader 兼容样本集 v1（待审）

口径：MC 1.21.1、只有 Fabric 构建（Modrinth 前 600 个 Fabric mod 筛选）、排除 API/运行时库与 L3 渲染重写；
按下载量排序。主指标只算 `candidate`。

| # | mod | 下载量 | 版本 | 类型 | 必需前置 | 抽查项 |
| --- | --- | ---: | --- | --- | --- | --- |
| 1 | `modmenu` | 164,976,763 | 11.0.5 | 工具 | placeholder-api | 进世界 + 触发主功能 |
| 2 | `zoomify` | 74,414,182 | 2.15.2+1.21.1 | 工具 | yacl, fabric-language-kotlin | 按 C 缩放（含平滑过渡） |
| 3 | `krypton` | 46,229,628 | 0.2.8 | 优化 | — | 无感；进世界后网络包正常（无断连） |
| 4 | `language-reload` | 45,183,642 | 1.7.6+1.21.1 | 优化 | — | F3+T 重载资源包后语言仍正常 |
| 5 | `presence-footsteps` | 42,277,682 | 1.11.2+1.21 | 装饰 | — | 走路/跳跃有脚步声（需资源包） |
| 6 | `debugify` | 40,207,856 | 1.21.1+1.1 | 优化 | yacl | F3 调试屏出现 debugify 补充项；配置菜单可开 |
| 7 | `visuality` | 31,557,982 | 0.7.7+1.21 | 装饰 | cloth-config | 进世界看区块加载粒子/方块破坏粒子 |
| 8 | `morechathistory` | 30,839,328 | 1.3.1 | 社交 | — | 聊天栏上滚超过 100 条 |
| 9 | `litematica` | 28,990,071 | 0.19.61 | 工具 | malilib | 打开 Litematica 菜单（M），加载一次放置预览 |
| 10 | `fallingleaves` | 28,633,523 | 1.17.1+1.21.1 | 装饰 | cloth-config | 进森林看树叶飘落粒子 |
| 11 | `optigui` | 28,386,639 | 2.3.0-beta.9+1.21 | 装饰 | fabric-language-kotlin | 装一个 CIT 资源包后容器界面贴图替换生效 |
| 12 | `better-mount-hud` | 26,027,931 | 1.2.4 | 工具 | — | 骑马/坐船时 HUD 正常 |
| 13 | `fastquit` | 25,654,196 | 3.0.0+1.20.6 | 优化 | cloth-config | 关闭游戏立即退出（无卡顿） |
| 14 | `fabrishot` | 20,203,589 | 1.14.1 | 工具 | — | F9 截图并保存 |
| 15 | `replaymod` | 19,729,159 | 1.21-2.6.28 | 工具 | — | 打开回放菜单，开始录制 |
| 16 | `paginatedadvancements` | 19,083,152 | 2.5.1 | 工具 | cloth-config | 打开进度界面，翻页正常 |
| 17 | `main-menu-credits` | 18,736,324 | 1.2.0 | 库 | — | 主菜单右下角出现滚动字幕 |
| 18 | `tooltipfix` | 17,456,576 | 1.1.1-1.20 | 优化 | — | 长 tooltip 不超出屏幕 |
| 19 | `farmers-delight-refabricated` | 17,430,264 | 1.21.1-3.3.6 | 装饰 | — | 种植/烹饪一件食物 |
| 20 | `betterend` | 16,271,197 | 21.0.11 | 装饰 | worldweaver, bclib | 创建/进入 BetterEnd 群系（或看创造物品栏） |
| 21 | `repurposed-structures-fabric` | 15,176,193 | 7.5.22+1.21.1-fabric | 世界生成 | midnightlib | 新世界生成后结构出现 |
| 22 | `better-ping-display-fabric` | 14,520,785 | 1.21.1-1.1.1 | 工具 | — | 多人界面 ping 显示（可离线看 GUI） |
| 23 | `sophisticated-core-unofficial-fabric-port` | 14,146,633 | 1.21.1-1.2.9.21.168 | 库 | forge-config-api-port | 打开背包升级界面 |
| 24 | `betternether` | 13,968,279 | 21.0.11 | 装饰 | worldweaver, bclib | 进入下界看 Nether 群系 |
| 25 | `friends-and-foes` | 12,536,666 | fabric-5.0.4+mc1.21.1 | 玩法 | resourceful-lib | 创造物品栏出现新生物蛋 |
| 26 | `sophisticated-backpacks-unoffical-fabric-port` | 12,099,072 | 1.21.1-3.23.4.3.106 | 装备 | sophisticated-core-unofficial-fabric-port | 合成背包并打开 |
| 27 | `carpet` | 12,041,082 | 1.4.147 | 机制 | — | 输入 /carpet 命令能响应 |
| 28 | `beautify-refabricated` | 10,954,849 | 3.6.5-fabric+1.21.1 | 装饰 | cloth-config | 放置装饰方块 |
| 29 | `cobblemon-additions` | 10,884,433 | 4.3.0 | 玩法 | cobbledollars, cobblemon | 进世界 + 触发主功能 |
| 30 | `ukus-armor-hud` | 10,595,011 | 0.5.1+mc1.21 | 装备 | ukulib | 进世界 + 触发主功能 |
| 31 | `sophisticated-storage-unofficial-fabric-port` | 10,170,345 | 1.21.1-1.3.7.9.139 | 存储 | sophisticated-core-unofficial-fabric-port | 进世界 + 触发主功能 |
| 32 | `fabric-seasons` | 10,111,298 | 2.4.2-BETA+1.21 | 玩法 | — | 进世界 + 触发主功能 |
| 33 | `the-bumblezone-fabric` | 10,058,521 | 7.17.3+1.21.1-fabric | 生物 | midnightlib, resourceful-lib | 进世界 + 触发主功能 |
| 34 | `no-resource-pack-warnings` | 9,910,559 | 1.3.1 | 工具 | — | 进世界 + 触发主功能 |
| 35 | `stendhal` | 9,470,776 | 1.4.1-1.21 | 工具 | — | 进世界 + 触发主功能 |
| 36 | `noxesium` | 8,851,254 | 2.3.3 | 工具 | — | 进世界 + 触发主功能 |
| 37 | `coolrain` | 8,612,646 | 1.4.0-1.21.1 | 玩法 | — | 进世界 + 触发主功能 |
| 38 | `viafabricplus` | 8,572,897 | 3.4.9 | 趣味 | — | 进世界 + 触发主功能 |
| 39 | `forcecloseworldloadingscreen` | 8,437,014 | 2.2.3 | 趣味 | — | 进世界 + 触发主功能 |
| 40 | `tweakeroo` | 8,210,932 | 0.21.61 | 工具 | malilib | 进世界 + 触发主功能 |
| 41 | `bosses-of-mass-destruction` | 8,207,387 | 1.10.2-1.21.1 | 玩法 | cardinal-components-api, fabric-language-kotlin, geckolib, cloth-config | 进世界 + 触发主功能 |
| 42 | `status-effect-bars` | 8,179,488 | 1.0.6 | 装饰 | cloth-config | 进世界 + 触发主功能 |
| 43 | `stackdeobf` | 8,072,254 | 1.4.3 | 管理 | — | 进世界 + 触发主功能 |
| 44 | `cull-less-leaves` | 7,889,350 | 1.4.2+1.21-fabric | 优化 | sodium, yacl | 进世界 + 触发主功能 |
| 45 | `cave-dust` | 7,744,875 | 3.0.1 | 装饰 | — | 进世界 + 触发主功能 |
| 46 | `nvidium` | 7,684,630 | 0.4.1-beta10-1.21-1.21.1 | 优化 | sodium | 进世界 + 触发主功能 |
| 47 | `adventurez` | 7,585,525 | 1.5.2+1.21.1 | 玩法 | cloth-config | 进世界 + 触发主功能 |
| 48 | `wakes` | 7,543,089 | 0.4.1+1.21.1 | 装饰 | — | 进世界 + 触发主功能 |
| 49 | `better-selection` | 7,483,088 | 1.6.8 | 工具 | — | 进世界 + 触发主功能 |
| 50 | `chatpatches` | 7,448,321 | 8.0.0+1.21.1-fabric | 装饰 | yacl | 进世界 + 触发主功能 |
| 51 | `faster-random` | 7,411,206 | 5.1.0 | 魔法 | — | 进世界 + 触发主功能 |
| 52 | `cobblethemes` | 7,397,250 | 1.0.0 | 机制 | — | 进世界 + 触发主功能 |
| 53 | `dcwa` | 7,365,682 | 6.0 | 工具 | — | 进世界 + 触发主功能 |
| 54 | `show-me-your-skin` | 7,297,600 | 1.11.3+1.21 | 装备 | — | 进世界 + 触发主功能 |
| 55 | `explosive-enhancement` | 7,261,041 | 1.3.2-1.21-1.21.1 | 玩法 | — | 进世界 + 触发主功能 |
| 56 | `pokeblocks` | 7,172,299 | 1.5.0-1.21.1 | 玩法 | — | 进世界 + 触发主功能 |
| 57 | `minihud` | 7,064,484 | 0.32.60 | 工具 | — | 进世界 + 触发主功能 |
| 58 | `you-shall-not-spawn` | 7,041,930 | 1.0.6 | 管理 | — | 进世界 + 触发主功能 |
| 59 | `custom-splash-screen` | 6,943,415 | 2.2.2 | 装饰 | — | 进世界 + 触发主功能 |
| 60 | `cobblemon-trainer-battle` | 6,909,851 | 1.11.13+1.8.4 | 小游戏 | — | 进世界 + 触发主功能 |
| 61 | `walksylib` | 6,809,234 | 2.0.5+1.21-1.21.1 | 装饰 | — | 进世界 + 触发主功能 |
| 62 | `true-ending` | 6,721,633 | 1.1.2d | 魔法 | — | 进世界 + 触发主功能 |
| 63 | `fabric-seasons-extras` | 6,717,863 | 1.3.3-BETA+1.21 | 科技 | — | 进世界 + 触发主功能 |
| 64 | `cape-provider` | 6,560,131 | 5.0.0.0-legacy+1.21.1 | 装饰 | — | 进世界 + 触发主功能 |
| 65 | `fabric-seasons-delight-compat` | 6,444,695 | 1.0 | 工具 | — | 进世界 + 触发主功能 |
| 66 | `exordium` | 6,409,998 | 1.4.2 | 优化 | — | 进世界 + 触发主功能 |
| 67 | `held-item-info` | 6,304,969 | 1.7.0 | 装饰 | — | 进世界 + 触发主功能 |
| 68 | `grass-overhaul` | 6,274,197 | 1.0.0 | 装饰 | — | 进世界 + 触发主功能 |
| 69 | `hold-my-items` | 6,237,410 | 4.3 | 装饰 | — | 进世界 + 触发主功能 |
| 70 | `camera-utils` | 6,216,625 | fabric-1.21.1-1.0.16 | 玩法 | — | 进世界 + 触发主功能 |
| 71 | `satin-free-wakes` | 6,148,261 | 0.2.2-1.21 | 装饰 | — | 进世界 + 触发主功能 |
| 72 | `infinite-music` | 6,145,410 | 0.4.6 | 工具 | — | 进世界 + 触发主功能 |
| 73 | `from-the-fog` | 6,105,686 | 1.9.4 | 玩法 | — | 进世界 + 触发主功能 |
| 74 | `brb` | 5,826,416 | 1.10.0-rc5+1.21 | 工具 | — | 进世界 + 触发主功能 |
| 75 | `tmcraft` | 5,789,078 | 1.4.19+1.8.4 | 玩法 | — | 进世界 + 触发主功能 |
| 76 | `cobblecuisine` | 5,737,947 | 2.2.0-alpha1 | 食物 | — | 进世界 + 触发主功能 |
| 77 | `connectiblechains` | 5,736,974 | 2.5.7+1.21.1 | 装饰 | — | 进世界 + 触发主功能 |
| 78 | `guard-villagers-fabricquilt` | 5,668,174 | 2.1.2-1.21.1 | 装备 | — | 进世界 + 触发主功能 |
| 79 | `silk` | 5,648,116 | 1.10.7 | 库 | — | 进世界 + 触发主功能 |
| 80 | `dragonloot` | 5,624,646 | 1.1.10+1.21.1 | 装备 | — | 进世界 + 触发主功能 |
| 81 | `fwaystones` | 5,596,054 | 3.3.4+mc1.21.1 | 玩法 | — | 进世界 + 触发主功能 |
| 82 | `vulkanmod` | 5,494,615 | 0.6.7+1.21.1 | 优化 | — | 进世界 + 触发主功能 |
| 83 | `inmis` | 5,490,236 | 2.8.2-1.21.1 | 玩法 | — | 进世界 + 触发主功能 |
| 84 | `reacharound` | 5,354,874 | 1.3.1 | 工具 | — | 进世界 + 触发主功能 |
| 85 | `bedrockify` | 5,311,625 | 1.10.1+mc1.21 | 机制 | — | 进世界 + 触发主功能 |
| 86 | `universal-graves` | 5,292,938 | 3.4.4+1.21 | 机制 | — | 进世界 + 触发主功能 |
| 87 | `better-nether-map` | 5,279,065 | 4.0.0-1.21.1 | 玩法 | — | 进世界 + 触发主功能 |
| 88 | `deuf-refabricated` | 5,255,959 | 1.1.0 | fabric | — | 进世界 + 触发主功能 |
| 89 | `lazy-language-loader` | 5,254,432 | 0.3.7 | 优化 | — | 进世界 + 触发主功能 |
| 90 | `skyblocker-liap` | 5,248,797 | v1.23.0-beta.1+1.21.1 | 工具 | — | 进世界 + 触发主功能 |
| 91 | `inmisaddon` | 5,190,822 | 1.0.6+1.21.1 | 装饰 | — | 进世界 + 触发主功能 |
| 92 | `cozy-home` | 5,153,524 | 1.1.20 | 玩法 | — | 进世界 + 触发主功能 |
| 93 | `lenient-death` | 5,147,352 | 1.2.5+1.21.1 | 机制 | — | 进世界 + 触发主功能 |
| 94 | `totemcounter` | 5,136,309 | 1.6.1+mc1.21 | 工具 | — | 进世界 + 触发主功能 |
| 95 | `betterend-crashed-ships-tweaks` | 5,068,207 | 1.1.0 | 趣味 | — | 进世界 + 触发主功能 |
| 96 | `fpsdisplay` | 5,061,029 | 4.2.1+1.21.1 | 工具 | — | 进世界 + 触发主功能 |
| 97 | `minecells` | 5,049,269 | 2.0.3 | 玩法 | — | 进世界 + 触发主功能 |
| 98 | `numismatic-overhaul` | 5,049,214 | 0.3.5+1.21 | 玩法 | — | 进世界 + 触发主功能 |
| 99 | `niftycarts` | 4,996,536 | 21.1.1 | 存储 | — | 进世界 + 触发主功能 |
| 100 | `lumymon` | 4,983,901 | 0.6.6 | 玩法 | — | 进世界 + 触发主功能 |

## 排除项

- API/库：
- L3 边界（不做，仅记录）：
