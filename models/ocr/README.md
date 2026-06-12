# OCR 模型目录

这里用于存放随软件一起打包的离线 OCR 模型文件。

推荐放置 RapidOCR ONNXRuntime 可用的模型：

- `ch_PP-OCRv4_det_infer.onnx`
- `ch_PP-OCRv4_rec_infer.onnx`
- `ch_ppocr_mobile_v2.0_cls_infer.onnx`

如果当前安装的 `rapidocr-onnxruntime` 包本身已经包含可用模型，程序会优先尝试使用本目录中的模型，找不到时再使用 RapidOCR 包内默认模型。最终发布给用户前，请务必在断网环境下运行打包后的 exe，确认不会发生运行时下载。
