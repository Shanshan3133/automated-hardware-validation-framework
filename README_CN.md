# 自动化硬件验证框架

这是一个“受保护5V降压电源板 + Python自动化测试台”的作品集项目。测试软件可以扫描输入电压和负载，测量输出纹波，定位UVLO、OVP和过流保护阈值，并生成CSV、JSON和CI风格HTML报告。

## 快速运行

模拟模式不需要第三方Python包：

```powershell
python -m validation.cli run --backend sim --output artifacts
python -m unittest discover -s tests -v
```

实机模式需要在树莓派上安装可选依赖，并填写电源、电子负载、示波器地址和ADC校准参数：

```powershell
pip install -e ".[raspberry-pi]"
python -m validation.cli run --backend real --config bench.json --output artifacts-real
```

## 文件入口

- `hardware/protected_buck.kicad_pro`：KiCad工程。
- `hardware/protected_buck.sch`：旧格式概念原理图；转换后仍需完成ERC清理，不能直接用于生产。
- `hardware/protected_buck.kicad_pcb`：器件布局、双面地平面和主功率路径。
- `hardware/protected_buck_3d.png`：PCB 3D预览。
- `hardware/BOM.csv`：初步物料表。
- `hardware/ROUTING_CHECKLIST_CN.md`：剩余PCB布线与审查事项。
- `validation/`：仿真和实机测试程序。
- `artifacts/report.html`：包含测量曲线的CI风格示例报告。

## 当前状态

5个软件单元测试和6个模拟验证流程已通过。实机纹波由SCPI示波器采集，MCP3008只负责直流及低频测量。KiCad 10.0.6可以解析PCB，几何DRC违规为0；在分离RTN/GND并加入受保护DAQ网络后有49个未连接项目，因此当前版本不能直接下单打板。请按照PCB完成清单布线，再做到DRC违规0、未连接0，并完成人工审查。
