.PHONY: setup run clean

# 创建虚拟环境并安装依赖
setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Windows 环境 setup
setup-win:
	python -m venv .venv
	.venv\Scripts\pip install -r requirements.txt

# 运行排表程序
run:
	python main.py

# 清理输出文件
clean:
	rm -rf output/*
