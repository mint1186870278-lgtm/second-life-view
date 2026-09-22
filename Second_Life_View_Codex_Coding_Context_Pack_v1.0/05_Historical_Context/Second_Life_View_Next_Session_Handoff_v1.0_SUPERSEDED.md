# Second Life View｜Next Session Handoff v1.0

## Current exact position

当前产品结构已经基本收口，正在 W02 Prototype 的最后阶段。

最新 Prototype candidate：

```text
Second_Life_View_W02_Dual_View_Project_Review_Prototype_v2.2
```

它实现了最新 v0.4 双视图边界，但尚未经过用户视觉验收。

## Next task

先做：

```text
打开 v2.2
→ 对照 W02-A 第二张高保真参考
→ 对照 W02-B 第三张高保真参考
```

重点检查：

### W02-A

- PathwayIconMap 是否真的和旧成熟稿一样清楚；
- `当前路径` cell 是否仍太重 / 太弱；
- `待核实` 数字列对齐；
- Material Section 是否破坏旧表格视觉节奏；
- Summary card active 是否太黄；
- Attention Rail 比例；
- row height / thumbnail / typography。

### W02-B

- Material Accordion 是否像任务队列而不是数据库表；
- Material header hierarchy；
- 展开 / 收起；
- Batch / field / question / status / discovered / action 对齐；
- Summary 是否清楚；
- 与 W02-A 视觉是否属于同一系统；
- D01 exact field focus；
- Back 是否恢复 tab。

## Do not touch yet

除非发现明确冲突，不要同时改：

```text
C01
C02
C03
W01
D01
```

先把 W02 收口。

## After W02

全量 regression：

```text
C01
→ C02
→ C03
→ W01
→ D01
→ W02-A
→ W02-B
→ D01
→ Back
```

然后再进入 backend / SDK payload alignment。
