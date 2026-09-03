# W12 — IPA 更新线程序列图（私有学习笔记）

## 路径 A：后台线程（BackgroundIPAUpdateThreadController::UpdateValueIPA L856-913）
```
[UI 线程]                  [BackgroundIPAUpdateThreadController]       [GPU]
   | 改 InThresholdT            |                                        |
   |--------------------------->|  请求更新(信号/队列)                     |
   |                            | ① is_stop_thread_ ? return             |
   |                            | ② unique_lock(SafeDicom)               |
   |                            | ③ m_ipa_analysed_result.Reset()        |
   |                            |     + malloc 6 路输出 (L879-884)        |
   |                            | ④ VGPU_UpdateValueIPA(line_ipa_miu,     |
   |                            |     frames, alines, px, vivo, mode,     |
   |                            |     threshold, L, RangeMean, A, T, cb)  |----> 统计+上色
   |                            |                                        |----> return
   |                            | ⑤ emit UpdateIpaValueSignal() (L896)    |
   |<---- UpdateIpaValueSignal --|                                        |
   |  渲染线程重绘(消费结果)       | ⑥ UpdatePostResultData() (L903)        |
   |__except("BP") ←任何异常统一收口 |
```

## 路径 B：同步短路径（IPAZoneController L104-162）
```
轮廓变化 → UpdateWhileICAContourChange(frameList) [只重算该帧 μ, W11]
        └→ UpdateWhileThresholdChange()
              ├ Reset + malloc
              ├ VGPU_UpdateValueIPA(..., threshold, ...)
              └ return true（渲染随帧）
```

## 取消/同步图例
- is_stop_thread_（每次调点检查）— 线程退出
- is_ipa_update_in_backgroud_thread_quit_（IPAAlgorithmController L249）— 算法内感知取消
- SafeDicom unique_lock — 模型写保护
- UpdateIpaValueSignal — 结果就绪通知（渲染侧消费）
- __except ExceptionFilter "BP"/"PBL" — 结构化异常收口
