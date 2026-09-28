# SAI wake-word model

The desktop engine supports a dedicated models/shiva.onnx OpenWakeWord model.

The repository does not commit a large binary model. Put your trained model at models/shiva.onnx.

When that file exists, SAI uses OpenWakeWord for the always-on wake stage. If it is absent, SAI uses a functional local faster-whisper fallback that listens in short chunks and detects Shiva, Siva, Shi va, or Telugu Sh...iva.

OpenWakeWord supports custom wake-word models and streaming local inference. Train the dedicated Shiva model separately and keep private recordings out of Git.
