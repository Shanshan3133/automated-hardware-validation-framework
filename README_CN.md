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
- `hardware/protected_buck.kicad_sch`：完整的KiCad 10原理图，ERC为0。
- `hardware/protected_buck.kicad_pcb`：已完成布线的双层PCB，DRC和未连接均为0。
- `hardware/protected_buck.dsn` / `.ses`：可复现的Specctra布线交换文件。
- `hardware/protected_buck_3d.png`：PCB 3D预览。
- `hardware/protected_buck_schematic.pdf`：原理图审查PDF。
- `hardware/BOM.csv`：初步物料表。
- `hardware/ROUTING_CHECKLIST_CN.md`：剩余PCB布线与审查事项。
- `validation/`：仿真和实机测试程序。
- `artifacts/report.html`：包含测量曲线的CI风格示例报告。

## 当前状态

5个软件单元测试和6个模拟验证流程已通过。实机纹波由SCPI示波器采集，MCP3008只负责直流及低频测量。KiCad 10.0.6检查结果为：原理图ERC 0错误/0警告，PCB DRC 0违规/0未连接。当前版本仍不是量产或直接下单版本；打板前还需核对封装、散热过孔、环路稳定性、器件降额、安装孔/外壳尺寸，并完成原理图与PCB一致性和人工审查。
