# 面试排班管理系统

这是一个用于自动安排面试官和场务人员排班的Python程序。

## 环境要求

- Python 3.7+
- pandas
- openpyxl

## 安装和设置

1. 首先确保系统安装了必要的包：
```bash
sudo apt install python3-full python3-venv
```

2. 创建并激活虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者在Windows上使用：
# venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 准备数据文件：
   - 在 `tables` 目录下放置名为 `raw.xlsx` 的Excel文件
   - 文件必须包含以下列（列名中需包含关键字）：
     - 姓名
     - 部门
     - 面试官时间选择
     - 场务时间选择

2. 确保虚拟环境已激活，然后运行程序：
```bash
python schedule_manager.py <场务地点> <面试官地点1> <面试官地点2> ...
```

例如：
```bash
python schedule_manager.py "接待室" "面试间1" "面试间2" "面试间3"
```

3. 输出：
   - 程序将在 `tables` 目录下生成 `schedule.xlsx` 文件
   - 输出文件包含以下列：
     - 时间（自动合并相同时间段）
     - 地点
     - 职务（面试官/场务）
     - 姓名

## 注意事项

- 每个时间段会安排2名场务人员
- 面试官会被均匀分配到各个面试地点（约3人/地点）
- 同一时间段内，一个人只能担任面试官或场务中的一个职务
- 程序会自动识别输入文件中的列名，只要包含关键字即可 