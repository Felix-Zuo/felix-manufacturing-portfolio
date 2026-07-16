# Real Asset Matrix

> 项目：SUM-v5-cinematic  
> 角色：工业资产总监  
> 调研冻结日期：2026-07-16  
> 状态：采购与导入前评审稿；本轮没有下载任何第三方模型，也没有把用户现场照片写入仓库。

## 1. 目标与硬性边界

本矩阵用于把现有程序化白模替换为可支撑最终影片的真实工业资产，同时保证制造逻辑、来源许可和公开发布边界可追溯。优先级依次为：

1. 已有明确开源许可的 ROS-Industrial 资产；
2. 以 Fab Standard License 正式获取的 Blender / FBX / GLB 资产；
3. CC0 材质与 HDRI；
4. 官方 CAD 只在许可明确覆盖影视改编、渲染和公开发布时进入最终资产；
5. 只有产品照片、尺寸图或许可不清晰的官方 CAD，一律只作技术参考，不下载、不提交、不直接转为影片模型。

### 结论标记

- **采用**：许可路径和技术用途清楚，可进入制作。
- **有条件采用**：必须先完成登录获取、价格确认、许可快照或书面授权。
- **参考后自建**：只读取技术结构和比例，最终几何、UV、材质由项目自行制作。
- **拒绝**：许可、格式、制造逻辑或质量不适合当前 Blender 影片管线。

### 许可红线

- [Fab Standard License](https://www.fab.com/eula) 允许商业使用、修改并把资产嵌入项目成品，但禁止把源资产作为独立文件再分发。所有 Fab 源文件必须放在 Git 外的私有资产缓存；公开仓库只保留项目代码、许可证记录和不可逆的最终渲染成品。
- Fab 的 Personal 与 Professional 档授权范围相同；**Reference-Only** 档不提供源格式，不用于本项目。购买或免费领取时必须登录 Epic/Fab，并保存商品页、订单记录、所选许可档和获取日期的截图。
- 官方提供“CAD 下载”不等于允许公开影视改编。没有明确媒体再利用条款时，CAD 只作测量参考。
- 厂商商标、铭牌和 UI 品牌不随模型许可自动授权。最终影片使用无品牌外观；KUKA 仅在事实性说明处保留名称，不放大 Logo。
- 用户提供的真实磨床内部照片仅作为私有工艺参考，不复制到仓库，不在文档中记录本地路径，不对外分发。

## 2. 当前场景替换地图

| 现有对象族 | 当前问题 | 目标处理 |
|---|---|---|
| `SUM_ASSET_MatureFactory`、`SUM_MatureFactory_*` | 厂房结构与材质为程序化近似，空间填充不足 | 用模块化真实厂房壳体、门、灯具和 CC0 PBR 重建；保留现有镜头尺度与路径 |
| `SUM_ASSET_KUKA_KR210_L150` | 已使用真实 ROS 网格，但许可记录存在仓库根 Apache-2.0 与包内 BSD 双重信息 | 保留真实机械臂；完成双层许可记录、材质、软管和末端执行器升级 |
| `SUM_ASSET_Robot_6Axis` | 旧代理模型 | 删除出最终可见层，只保留调试用途 |
| `SUM_MatureFactory_AGV07`、`SUM_AGV07_*` | 自建外形过于概念化，轮组与传感器细节不足 | 由 Fab 中性品牌移动机器人替换；重新绑定轮组与车体动画 |
| `SUM_ASSET_Enclosed_InternalGrindingCell`、`SUM_GrindingCell_*` | 外壳、主轴、轴头、夹具、管路和内腔都不够真实；三爪卡盘不符合英雄镜头工艺 | 外壳可沿用项目尺寸重建；内部按真实鞋式无心支承、磁性驱动盘、内圆砂轮主轴和湿式冷却逻辑完全重做 |
| `SUM_ASSET_V7_FactorySystems`、`SUM_V7_Gantry_*` | 输送、上料和龙门机构偏白模 | 引入模块化输送/厂务资产；夹持机构按真实气缸、导轨、拖链和传感器补齐 |
| `SUM_MatureFactory_CommandScreenBay`、`SUM_CommandBay_*`、`SUM_ASSET_ScreenStation_*` | 屏幕与实体控制柜脱节 | 用真实控制箱外壳承载项目自己的屏幕媒体与交互特效 |
| `SUM_MatureFactory_RobotCellFence`、`SUM_RobotCell_*` | 护栏网片、立柱、门锁和脚座过简 | 用真实比例模块化护栏替换，重新核对安全间距与镜头遮挡 |
| `SUM_MatureFactory_SegmentedLuminaire*` | 灯具结构和配光单一 | 使用真实灯具网格或免费厂房自带灯具；照明仍由项目灯光系统控制 |

## 3. 可直接进入最终影片的资产候选

价格会随地区、促销和账户变化；表中不虚构金额，所有付费项在采购当天登录确认。

| 优先级 / 类别 | 候选与主源 URL | 格式 | 许可、价格、登录 | 适配风险 | 结论 | 替换当前对象 |
|---|---|---|---|---|---|---|
| P0 / KUKA 机器人 | [ROS-Industrial `kuka_experimental`](https://github.com/ros-industrial/kuka_experimental) | URDF、DAE | 仓库根为 Apache-2.0；`kuka_kr210_support/package.xml` 声明 BSD；免费、无需登录。Apache-2.0 不授予商标权 | 网格与关节极限仍需逐轴核验；双层许可信息必须同时保留，去除/弱化品牌标识 | **有条件采用（本地已有）**：许可审计通过后继续使用真实 KR210 L150 网格 | 保留 `SUM_ASSET_KUKA_KR210_L150`；替代 `SUM_ASSET_Robot_6Axis` 的最终可见用途 |
| P0 / 明亮厂房免费壳体 | [Industrial Warehouse - Animated Sectional Doors & Control Panel](https://www.fab.com/listings/e27b7526-a1a1-470a-b807-fe01871deae2) | Blender、FBX | Fab Standard License；免费；需 Epic/Fab 登录领取 | 木构屋顶和花纹地面不符合目标；仅取墙体、门、控制面板、部分灯具，重做钢屋架与环氧地坪 | **采用**，作为免费开工壳体 | `SUM_ASSET_MatureFactory` 的围护、卷帘门和部分设施 |
| P0 / 工业控制箱 | [Control Panel](https://www.fab.com/listings/8dc3b82f-54ec-43aa-b30b-c2a27a4293b3) | FBX、GLB | Fab Standard License；免费；需登录领取 | 通用控制箱不是项目 HMI；屏幕、按钮标签和材质需重做 | **采用**，只用箱体、按钮、急停和五金；屏幕内容由项目生成 | `SUM_MatureFactory_CommandScreenBay`、`SUM_ASSET_ScreenStation_*` 的实体载体 |
| P0 / 上下料附件 | [FREE Handling Accessory KITBASH](https://www.fab.com/listings/b78db94f-eb56-4ef1-af87-3938aff84a23) | Blender、FBX、OBJ | Fab Standard License；免费；需登录领取 | 偏吊装/搬运附件，不可冒充精密轴承夹具 | **采用**，用于吊钩、支架、连接件和背景工装；不用于英雄末端夹具 | `SUM_V7_Gantry_*` 周边附件、背景上料工装 |
| P0 / 环境材质与 HDRI | [Poly Haven License](https://polyhaven.com/license) | HDRI、EXR、JPG/PNG、PBR 贴图、部分模型 | CC0；免费；无需登录 | 要筛掉脏旧、住宅化材质；统一 texel density 与色彩空间 | **采用** | 环氧地坪、镀锌钢、拉丝不锈钢、橡胶、玻璃和日光环境 |
| P0 / 环境材质 | [ambientCG](https://ambientcg.com/) | JPG/PNG、EXR、PBR 贴图、部分模型 | CC0；免费；无需登录 | 同上；下载前记录资产 ID 与版本 | **采用** | 所有程序化单色材质，尤其机床喷粉钢板、地坪、墙面和管线 |
| P1 / AGV | [Mobile Robot and Pallet Station](https://www.fab.com/listings/7b4298af-89d4-4d02-b7d9-bedd6717a69e) | Blender、FBX、OBJ | Fab Standard License；付费、价格动态；需登录 | 4 个网格，需要自行拆分/绑定驱动轮、脚轮和悬架；核对外形尺寸与当前通道宽度 | **有条件采用**：优先采购，使用中性标签 | `SUM_MatureFactory_AGV07`、`SUM_AGV07_*` |
| P1 / 输送与厂务设备 | [Industrial Factory Equipment](https://www.fab.com/listings/ffd2da94-cf2d-4ee7-9dcc-501a92ecb0a6) | Blender、FBX、OBJ、GLB，另有 UE 版本 | Fab Standard License；付费、价格动态；需登录；商品页列 68 个模块化网格、LOD、碰撞与动画/声音 | 购买前必须检查完整 mesh list、枢轴、输送带拓扑和贴图是否能脱离 UE；不可假定包含磨床内部件 | **有条件采用**，作为付费设备基础包 | `SUM_ASSET_V7_FactorySystems`、程序化输送段、背景设备和厂务填充物 |
| P1 / 现代厂房高配壳体 | [Large modern warehouse for Blender Eevee and Cycles](https://www.fab.com/listings/4606e18d-16cd-498a-9a7c-9fa7ad5ab942?lang=en) | Blender 3.3 原生 | Fab Standard License；付费、价格动态；需登录；商品页标注模块化 3.6 m 网格与约 129.85 万三角面 | 烘焙光需拆除，重新建立 Cycles 灯光；面数较高，需镜头分层和实例化 | **有条件采用**：免费壳体达不到镜头要求时升级 | 整体替换 `SUM_ASSET_MatureFactory` 的建筑包络、屋架、天窗和通道空间 |
| P2 / 厂房备选 | [Industrial factory building 25i28](https://www.fab.com/listings/e240639f-bd33-4855-9fb8-d35d3a2d879b) | Blender、FBX、OBJ、GLB/glTF、USDZ | Fab Standard License；付费、价格动态；需登录 | 缺少充分评价和技术统计；商品图不能证明近景质量 | **有条件采用 / 备选**：只在下载预览确认 UV、屋架和天窗后使用 | `SUM_ASSET_MatureFactory` 建筑壳体 |
| P1 / 安全护栏 | [Industrial Safety Fence](https://www.fab.com/listings/101cbf5f-99b3-4733-b354-48b321184c4c) | FBX、OBJ | Fab Standard License；付费、价格动态；需登录；商品页标注真实比例与 PBR | 需核对门锁、立柱间距、脚座和网孔；镜头路径可能被网片遮挡 | **有条件采用** | `SUM_MatureFactory_RobotCellFence`、`SUM_RobotCell_*` |
| P2 / 灯具 | [Warehouse Lamp](https://www.fab.com/listings/10068650-9f19-4923-a407-930ff95f4e1a) | Blender、FBX、OBJ、GLB | Fab Standard License；付费、价格动态；需登录；4K PBR、真实比例 | 只使用 clean 版本；发光网格不能替代真实 Area Light/IES 配光 | **有条件采用** | `SUM_MatureFactory_SegmentedLuminaire*` 近景灯体 |
| P2 / 厂务管道 | [Modular Industrial Pipe Set](https://www.fab.com/listings/597a65be-10b6-4176-9fa7-95dc86e154bb) | Blender、FBX、GLB | Fab Standard License；付费、价格动态；需登录；4K PBR、模块化 | 要统一管径系列、法兰标准和支吊架；避免无意义堆管 | **有条件采用**，只按 P&ID 逻辑布置 | 屋顶与机床间程序化管网、`SUM_V7_UtilityTray_*` 周边主管 |
| P3 / 单件管道补景 | [Industrial Pipe](https://www.fab.com/listings/b97df116-8aad-4c0e-b395-f0723434f072) | FBX、GLB | Fab Standard License；免费；需登录 | 单一网格、造型简单，不适合英雄近景 | **采用（有限）**，只作远景或辅助件 | 远景程序化管件，不替换英雄机床软管 |

## 4. 官方 CAD 与技术主源：参考或授权后使用

以下主源适合确定真实尺寸、结构和运动关系，但当前未发现明确覆盖“修改 CAD 后用于公开商业影片”的授权。除 ROS 项外，本轮均不下载。若未来取得书面许可，才可把相应行提升为“采用”。

| 类别 | 官方主源 URL | 可得格式 / 信息 | 许可、价格、登录 | 适配风险 | 结论 | 替换或指导的当前对象 |
|---|---|---|---|---|---|---|
| 磨床整机与工艺 | [UVA LIDKÖPING SSB 320](https://www.uvalidkoping.com/machine/lidkoping-ssb-320/)、[SSB 62](https://www.uvalidkoping.com/machine/ssb-62/)、[SUU 320](https://www.uvalidkoping.com/machine/lidkoping-suu320/) | 官方机型图、能力与工艺说明；未提供可公开复用 CAD | 公开浏览；版权保留；无明确影视再利用授权 | 不能复制整机外观、Logo 或宣传图；必须抽象成无品牌通用磨床 | **参考后自建** | 完整指导 `SUM_ASSET_Enclosed_InternalGrindingCell`、鞋式无心支承、磁性驱动与测量单元 |
| 磨削主轴 / 轴头 | [GMN High-speed integrated motor spindles](https://www.gmn.de/en/spindles/spindle-groups/tool-spindles-manual/types-of-spindles/high-speed-integrated-motor/)、[GMN spindle downloads](https://www.gmn.de/en/spindles/service-desk/download/) | 官方尺寸与 CAD 下载入口；具体格式依型号 | 免费技术资料；是否需表单依型号；公开影视改编许可未确认 | 真实 spindle cartridge 可用，但不可照搬品牌铭牌；轴端、砂轮接杆必须按磨削轮尺寸重新设计 | **参考后自建**；取得书面许可后可导入 CAD | `SUM_GrindingCell_HighSpeedSpindleMotor`、`WheelArborNose`、`PrecisionTaperArbor` |
| 磨削主轴备选 | [FISCHER - The world of grinding](https://www.fischerspindle.com/en/products/the-world-of-grinding) | 内圆磨削电主轴、锥柄/套筒式结构和产品图 | 公开浏览；CAD 与媒体再利用授权未确认 | 产品范围宽，不能凭宣传图猜内部轴承和冷却结构 | **参考后自建** | 同上；用于校正壳体直径、鼻端长度和安装法兰比例 |
| 磁性驱动夹具 | [SwissChuck magnetic chucks](https://www.swisschuck.com/en/products/magnetspannfutter) | 面向环件、法兰和轴承座的圆形磁力卡盘产品资料 | 公开浏览；无明确可复用 CAD/影视许可 | 是驱动/夹持参考，不等同鞋式无心定位本身 | **参考后自建** | 替换英雄镜头的 `SUM_GrindingCell_ThreeJawChuck` 与 `SoftJaw_*` |
| 径向极磁盘备选 | [Spreitzer SPRS](https://shop.spreitzer.de/en/Permanent-magnetic-chuck-SPRS/B900500459M) | 圆形径向极磁盘；可请求 CAD | 需询价/请求；影视许可未确认 | 产品偏通用硬车/磨削，需要与工件头和支承靴共同设计 | **参考后自建**；未经书面许可不下载 | 同上 |
| 机器人三指夹爪 | [SCHUNK PZN-plus 100-1](https://schunk.com/ca/en/gripping-systems/centric-grippers/pzn-plus/pzn-plus-100-1/p/000000000000303312) | 官方 CAD；10 mm/爪，闭合力约 1800 N | CAD 可下载；地区账户要求可能不同；媒体再利用许可未确认 | 夹爪适合机器人搬环，不适合充当磨床工件主夹具；需自制软爪与法兰 | **参考后自建 / 授权后采用** | `SUM_KUKA_KR210_PrecisionBearingGripper` |
| 机器人三指夹爪备选 | [Zimmer GPD5010 robot set](https://www.zimmer-group.com/en-us/products/components/robotics/robot-sets/robot-independent/products/rsb-00-38-00002-a) | 官方 CAD；三指同心夹爪、适配板、爪和接头 | 官方下载；影视许可未确认 | 套件与 KR210 法兰、负载和轴承直径要重新核算 | **参考后自建 / 授权后采用** | 同上 |
| 三爪动力卡盘 | [SCHUNK ROTA NCE 260](https://schunk.com/us/en/workpiece-clamping-technology/lathe-chucks/power-lathe-chucks-with-through-hole/rota-nce/rota-nce-260-81-a6-sv90-/p/000000000000808031) | 官方 CAD、三爪动力卡盘 | 官方下载；影视许可未确认 | 与鞋式无心内圆磨削英雄工艺不符 | **拒绝用于英雄磨床**；只可作为背景车床参考 | 不替换 `SUM_GrindingCell_ThreeJawChuck`；可指导未来背景车床 |
| 紧凑气缸 | [SMC CQ2/CDQ2](https://www.smcworld.com/webcatalog/api/en-au/guide/?id=CQ2-CDQ2-Z-E)、[SMC CAD Library Help](https://www.smcworld.com/cadlib/en/help.jsp) | 多种 2D/3D CAD 输出 | 下载通常免费；地区站可能需注册；[SMC Copyright](https://www.smc.eu/en-ce/copyright) 将 CAD 使用限制在明确预定的项目/用途，其他使用或修改需书面批准 | 直接导入可能违反用途边界；软管口、磁性开关和安装脚还需配置 | **拒绝直接用于最终影片，除非书面授权**；只看尺寸和安装逻辑 | `SUM_V7_Gantry_*` 气缸、门缸、夹爪执行器 |
| 标准气缸 | [Festo DSBC](https://www.festo.com/us/en/a/1383370/)、[Festo CAD/catalog](https://www.festo.com/media/catalog/202904_documentation.pdf) | 官方产品资料与 CAD 入口 | 官方资料免费；[Festo Terms of Use](https://www.festo.com/us/en/e/legal/terms-of-use-id_65609) 对内容复制、修改、公开展示和下载用途有严格限制 | 许可不覆盖当前影视改编假设 | **拒绝直接用于最终影片，除非书面授权**；参考后制作无品牌 ISO 气缸 | 所有程序化气缸、拉料手、自动门执行器 |
| 线性导轨 | [THK CAD download help](https://tech.thk.com/en/help/help_2dcad_en.html)、[THK membership](https://www.thk.com/opm/us/en/online_service/explanation/member/) | 2D/3D，STEP/DWG 等；通常需会员 | 免费账户；影视改编许可未确认 | 细节密度高且导轨长度要按设备配置；品牌标记需移除 | **参考后自建 / 授权后采用** | `SUM_GrindingCell_XSlide_LinearRails`、`LinearBlocks`、龙门轴 |
| 线性导轨备选 | [HIWIN CAD configurator](https://www.hiwin.de/en/cad-konfigurator) | 线性导轨、轴系 CAD 配置 | 官方工具；账户/格式依配置；影视许可未确认 | 同上 | **参考后自建 / 授权后采用** | 同上 |
| 电缆拖链 | [igus E2 two-piece CAD](https://www.igus.com/cable-carriers/small-sized-cable-carriers/energy-chains-e2-two-piece)、[igus E4.28](https://www.igus.com/product/series-E4-28) | 官方 3D CAD，多格式；页面称 CAD 库可免注册使用 | 免费；不一定需登录；影视再利用条款未确认 | 选型必须匹配弯曲半径、行程、线缆填充率和安装方向 | **参考后自建 / 许可确认后采用** | 机械臂 dress pack、机床滑台和 `SUM_V7_Gantry_*` 拖链 |
| 输送系统 | [FlexLink Engineering Tools](https://www.flexlink.com/en/support/engineering-tools) | 设计工具，可生成 STEP/SAT；CADENAS/PartCommunity | 通常需注册；影视许可未确认 | 系统级 CAD 很重，且品牌化明显；需要简化和无品牌材质 | **参考后自建 / 授权后采用** | `SUM_ASSET_V7_FactorySystems` 输送和上下料段 |
| 滚筒输送 | [Interroll tools and downloads](https://www.interroll.com/tools-downloads/downloads/) | 3D CAD 标准格式、配置工具 | 条件依配置器；受网站使用条件约束 | 组件正确但系统布局仍需工程设计 | **参考后自建 / 授权后采用** | 滚筒、驱动滚筒、支腿和侧导向 |
| 皮带输送 | [Dorner CAD Configurator](https://tools.dornerconveyors.com/) | 配置后 CAD | 需登录/注册；影视许可未确认 | 直接配置件可能带品牌和过多制造细节 | **参考后自建 / 授权后采用** | 机床进出料短输送 |
| 铝型材与转运系统 | [Bosch Rexroth MTpro](https://www.boschrexroth.com/en/au/c/planning-software-mtpro/) | Windows 规划软件、CAD 模型；页面列出约 2.2 GB 安装包 | 工具免费；下载/账户依地区；影视许可未确认 | 软件和资产体量大，不应为少量背景件污染制作链 | **暂缓**；只在输送工程需要精确选型时使用 | 型材机架、转运系统、工位支架 |
| AGV 官方比例参考 | [OMRON HD-1500 CAD](https://www.omron-ap.com/products/family/3952/download/cad.html) | 官方 3D CAD；地区页面可见 STEP、IGES、Parasolid、SolidWorks 等 | 需登录/注册；影视许可未确认 | HD-1500 为 1500 kg 级平台，远大于当前小型轴承物流车；不可直接套比例 | **参考后自建，不直接采用** | 仅校正传感器、保险杠、驱动和安全灯逻辑；不替换当前 AGV 外形 |
| 工业 HMI | [Siemens SIMATIC HMI Panels](https://www.siemens.com/en-us/products/simatic-hmi/panels/)、[MTP700 product/CAD](https://mall.industry.siemens.com/mall/de/de/Catalog/Product?SiepCountryCode=DE&mlfb=6AV2128-3GB06-0AX1) | 产品图、尺寸、M-CAD/E-CAD | 公开资料/下载条件依地区；影视许可未确认 | 品牌外观和 UI 不适合直接复制；屏幕画面必须用项目自己的内容 | **参考后自建** | `SUM_CommandBay_*`、磨床 `OperatorConsole*` 的尺寸、边框和安装方式 |
| 机器护栏 | [Troax Machine Guarding](https://www.troax.com/products/machine-guarding/) | 官方护栏系统、CAD package | 可下载入口；账户/许可细则需确认 | 网片、门锁和安全距离需按布局配置；品牌组件不可无审计直接发布 | **参考后自建 / 授权后采用** | `SUM_MatureFactory_RobotCellFence`、`SUM_RobotCell_*` |
| 机器灯具 | [LED2WORK downloads](https://www.us.led2work.com/downloads/)、[LEANLED II](https://www.us.led2work.com/products/led-machine-lights/led-surface-mounted-lights/leanled-ii/) | 官方 CAD 与尺寸资料 | 官方下载；影视许可未确认 | 只适用于机床内/工位照明，不是厂房高棚灯；仍需独立光源 | **参考后自建 / 授权后采用** | 磨床内腔灯、工位线性灯 |

## 5. 明确拒绝的候选

| 候选 | URL / 格式 | 拒绝原因 | 可能的未来用途 |
|---|---|---|---|
| Factory Environment Collection | [Fab listing](https://www.fab.com/listings/2ee66462-8c2b-4303-892c-83f7fc0d9b3e)，Unreal `.uasset` | 虽然免费、内容丰富且评价较高，但仅适配 Unreal；当前影片资产、动画和导出链以 Blender 为核心，迁移成本会破坏本轮交付边界 | 只有项目正式切换 Unreal 时再评估 |
| Warehouse AGV Mobile Robot 05 | [Fab listing](https://www.fab.com/listings/5042c843-c539-4f7b-b8ea-f1a3df7f10ca)，UE 5.7/5.8 `.uasset` | Unreal-only、静态且无绑定，不适合当前 Blender 动画 | Unreal 版本的远景车 |
| CNC Lathe | [Fab listing](https://www.fab.com/listings/efdbdb36-9e85-4228-be3c-f4cd2b9f020a)，FBX/GLB | 低模车床，不是封闭式轴承内圆磨床；英雄近景会暴露结构错误 | 最远景背景道具，非本轮优先项 |
| Lathe Machine | [Fab listing](https://www.fab.com/listings/82c310e9-ec9b-4e8d-a45b-cf364bcef1b6)，FBX | 硬表面细节可用，但工艺和外壳类型仍是车床，不能替代磨床 | 仅作为非英雄背景机床，且需另行采购 |
| 破旧、锈蚀、科幻管道/控制台资产 | Fab 同类商品 | 与明亮、整洁、可信的现代轴承工厂冲突；会造成无意义元素堆积 | 不采用 |
| 未附许可文本的网盘、模型聚合站与转载 CAD | 非主源 | 无法证明权利链，禁止下载和提交 | 无 |

## 6. 英雄磨床的工艺纠偏与资产方案

### 6.1 必须纠正的结构

现有 `SUM_GrindingCell_ThreeJawChuck` 与 `SUM_GrindingCell_SoftJaw_*` 不应继续作为英雄磨削镜头的工件定位方式。UVA LIDKÖPING 的官方资料明确给出轴承套圈内圆磨削可采用 **shoe-centerless（鞋式无心）** 工件夹持/定位，并在 SUU 320 上描述工件头可包含驱动盘、磁性夹盘与测量单元。结合用户私有现场照片，英雄工位应采用以下可解释结构：

1. 套圈由两个支承靴确定径向位置，端面靠定位基准；
2. 圆形磁性驱动盘或无品牌等效驱动头带动套圈旋转，不用可见三爪夹紧内/外圆；
3. 右侧高速磨削电主轴通过短而刚性的轴头、锥形接杆和小直径内圆砂轮进入沟道；
4. 主轴、砂轮、工件旋转方向在动画中必须可读，砂轮接触点只出现少量、短寿命火星；
5. 多路冷却喷嘴在接触区形成连续射流，碰撞砂轮/工件后产生定向飞溅、雾化和回流，不使用静态透明圆柱冒充流体；
6. 内腔补齐主轴座、滑台、导轨块、测量指、拉料手、气缸、阀岛、硬管、软管、接头、拖链、刮屑结构、灯具和维护面板，但每个物件必须服务于加工或维护逻辑。

### 6.2 最终建模边界

- **整机外壳**：项目自有无品牌设计，参考 UVA 的封闭、防飞溅、滑门和操作侧布局，但不复制其外观比例、Logo 或宣传图。
- **核心内部组件**：以用户私有照片和 GMN/FISCHER、SwissChuck/Spreitzer、THK/HIWIN 等官方尺寸逻辑为参考，由项目自建英雄级模型。
- **可采购标准件**：只有当官方 CAD 的影视改编许可得到书面确认时，才允许替换自建气缸、导轨、拖链或夹爪；否则保持无品牌自建版本。
- **材质**：喷粉钢板、发黑钢、研磨不锈钢、冷却液湿膜、磨料颗粒、橡胶软管和油污必须分别建材，不能共用一套“工业灰”。

## 7. 导入前验收门槛

每个实际获取的资产必须在进入主场景前通过以下检查：

- 许可：保存来源 URL、商品 ID、获取日期、所选许可档、订单/免费领取凭证和原始许可文本；不接受只有商品截图的资产。
- 格式：优先 Blender 原生，其次 FBX/GLB；OBJ 只接受静态无动画件；UE `.uasset` 不进入当前管线。
- 比例：以米为 Blender 场景单位，核对门高、机器人基座、AGV 轮径、护栏高度和操作屏视线。
- 拓扑：英雄近景无非流形、穿模、明显法线错误和烘焙阴影；远景资产需要 LOD 或实例化。
- 材质：PBR 通道命名清楚，色彩空间正确；移除错误磨损、随机污渍、Logo 和不可解释发光。
- 动画：枢轴位于真实关节/铰链/轮轴，机械臂、门、轮组、夹爪、输送带和拖链的运动范围可验证。
- 工艺：任何运动必须能回答“由什么驱动、约束在哪里、物料如何进入和离开、是否会碰撞”。
- 仓库边界：Fab 和受限 CAD 的源文件不进入公开 Git；只有许可证记录、项目自建文件和最终渲染进入版本控制。

## 8. “免费即可开工”的最小资产包

### 获取顺序

1. **保留本地 ROS-Industrial KUKA KR210 L150**：先核对上游 commit、根 Apache-2.0 与包内 BSD 声明，建立归属记录；不重新下载，不使用旧六轴代理模型。
2. **领取 Fab 免费厂房壳体**：获取 `Industrial Warehouse - Animated Sectional Doors & Control Panel` 的 Standard License 源格式；只导入墙体、门、控制面板和可用灯体。
3. **领取 Fab 免费控制箱**：获取 `Control Panel`，替换悬浮屏幕的实体载体；项目页面继续作为自有动态屏幕内容。
4. **领取 Fab 免费上下料附件包**：获取 `FREE Handling Accessory KITBASH`，只填充有明确功能的吊装/连接附件。
5. **领取 Fab 免费单管件**：`Industrial Pipe` 仅用于远景补景，不进入英雄机床内部。
6. **下载 CC0 材质与 HDRI**：从 Poly Haven 和 ambientCG 获取明亮天光、洁净环氧地坪、镀锌钢、喷粉钢板、拉丝金属、橡胶和玻璃；逐项记录资产 ID。
7. **自建真实磨床英雄资产**：依据私有照片与 UVA/GMN/FISCHER 等官方技术资料重做外壳、鞋式无心夹持、磁性驱动盘、主轴轴头、砂轮、冷却喷嘴、测量和管线；不下载许可不清晰的 CAD。
8. **暂留程序化 AGV 作为替身**：免费阶段只用于镜头节奏和碰撞预演，不进入最终近景；待采购真实中性品牌 AGV 后一对一替换。

这一最小包足以开始镜头、照明、材质和交互制作，但不等于最终英雄资产已达标。免费阶段最重要的产出是正确的空间、工艺和动画接口，而不是继续给白模堆装饰。

### 第一批付费升级顺序

1. `Mobile Robot and Pallet Station`：解决开场跟车与轮组近景的最大质量短板。
2. `Industrial Factory Equipment`：一次性补齐输送、设备和厂务背景，降低重复自建成本。
3. `Large modern warehouse for Blender Eevee and Cycles`：免费壳体无法通过屋架、天窗和长运镜验收时再升级。
4. `Industrial Safety Fence`：机器人单元进入中近景前采购。
5. `Warehouse Lamp` 与 `Modular Industrial Pipe Set`：只在镜头确实靠近相应资产时购买，避免无目的堆积。

## 9. 采购与制作停止条件

出现下列任一情况，资产不得进入主场景：

- 商品只提供 Reference-Only 档或无法下载源格式；
- 未能保存许可/订单证据，或条款禁止修改、公开展示、商业发布；
- 只能通过转载站、网盘或来源不明的模型包获得；
- 资产宣称“工业”但没有真实尺度、关节枢轴、合理的制造结构或近景拓扑；
- 需要通过穿模、错误夹持、虚假加工方向或无物理依据的动画才能配合镜头；
- 引入的细节没有叙事、工艺或空间功能，只会增加噪声和渲染成本。

## 10. 执行摘要

- 当前最可靠的现成真实资产是已经入库的 ROS-Industrial KUKA，但必须完成 Apache-2.0/BSD 归属审计。
- 最终磨床不能靠通用 CNC/车床模型替换；英雄内腔必须围绕鞋式无心定位、磁性驱动、右侧内圆磨削主轴和真实湿式冷却重新建模。
- 免费 Fab 壳体、控制箱、搬运附件与 CC0 材质可以立即启动场景升级；AGV 和综合厂务设备是最值得优先购买的两项。
- 厂商 CAD 本轮全部保持“参考或授权后采用”，没有下载或提交许可不清晰文件。
