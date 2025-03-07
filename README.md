# 面试时间安排系统

这是一个用于自动安排面试时间的系统，可以同时处理面试官、场务和一面面试者、二面面试者的时间安排。

- 老版的面试时间安排系统对原始数据文件格式要求较为严苛，需要手动调整，新版系统对格式要求较为宽松，可以自动识别并读取。
- 老版对于面试者和面试官的排版是在一起进行的，新版系统可以分开单独进行。
- 新版系统新增了面试官和场务的排班日志文件，可以查看每个面试官和场务的具体工作安排。
- 新版支持权重分配面试者的功能，解决了部分场次因为人员不足或者场地有限造成的面试者人数不均的问题。
- 新版在v4.0之后加入了二面排表功能，可以自动识别并读取二面面试者的可选时间段，能找到所有需要面试两轮的人员名单，且确保他们的面试场次一定相邻（上午的两场或者下午的两场）。
- 在v5,0之后，加入了makefile文件，可以直接使用make命令运行不同的程序，操作更简单（详情请见文档最后的Make方法）。

## 功能特点

1. 面试官和场务排表 (`schedule_manager.py`)
   - 自动识别并读取面试官和场务的可用时间
   - 确保每个地点都有足够的面试官和场务人员
   - 平衡每个人的工作量
   - 生成清晰的Excel格式排班表
   - 提供详细的分配日志

2. 面试者排表 (`interviewee_scheduler.py`)
   - 自动识别并读取面试者的可选时间段
   - 确保所有时间段都能被充分利用
   - 支持按权重分配面试者到不同时间段
   - 生成易读的Excel格式安排表，使用不同颜色区分时间段
   - 提供详细的分配情况报告

3. 二面排表 (`second_interview.py`)
    - 自动识别并读取二面面试者的可选时间段
    - 能够找到所有需要面试两轮的人员名单，且确保他们的面试场次一定相邻
    - 生成清晰的Excel格式安排表
    - 提供详细的分配情况报告

## 文件结构

```
.
├── tables/
│   ├── interviewer.xlsx    # 面试官和场务信息表
│   ├── interviewee.xlsx    # 面试者信息表
│   └── second_interviewee.xlsx    # 二面名单
├── output/
│   ├── schedule.xlsx       # 面试官和场务排班结果
│   ├── schedule_log.txt    # 面试官和场务排班日志
│   ├── interviewee_schedule.xlsx    # 面试者安排结果
│   ├── interviewee_schedule_log.txt # 面试者安排日志
│   ├── second_schedule.xlsx # 二面面试结果
│   ├── double_interviewee.txt    # 二面需要面试两轮的名单
│   └── second_interview_log.txt # 二面面试日志
├── .gitignore # Git忽略文件
├── README.md               # 项目说明文档
├── requirements.txt        # 依赖包列表
├── Makefile                # Makefile文件
├── config.json             # 配置文件
├── schedule_manager.py     # 面试官和场务排表程序   ——
├── interviewee_scheduler.py # 面试者排表程序         |  主要的脚本文件
└── second_interview.py # 二面排表程序              ——
```

## 配置文件说明（也可以选择使用make方法，在文档末端）

系统使用 `config.json` 文件进行配置，包含以下内容：

```json
{
    "interviewer_config": {
        "input_file": "tables/interviewer.xlsx",  // 面试官和场务信息表路径
        "time_locations": {                        // 每个时间段对应的地点列表
            "时间1": [                       // 时间段名称
                "接待室",                          // 第一个地点为场务地点
                "面试室A",                         // 后续地点为面试官地点
                "面试室B",
                "面试室C"
            ],
            "时间2": [
                "会议室1",
                "会议室2",
                "会议室3",
                "会议室4"
            ]
        }
    },
    "interviewee_config": {
        "input_file": "tables/interviewee.xlsx",  // 面试者信息表路径
        "slot_weights": [19, 26, 27, 28]          // 各时间段的权重（可选，默认是平均分配）
    },
    "second_interview_config": {
        "input_file": "tables/second_interviee.xlsx",   // 二面面试者信息表路径
        "times": [                                      //二面面试时间段
            "时间1",                  
            "时间2",
            "时间3",
            "时间4"
        ]
    }
}
```

### 配置项说明

1. interviewer_config:
   - input_file: 面试官和场务信息表的路径
   - time_locations: 时间段与地点的映射关系
     - 键：时间段名称（必须与Excel表中的时间段名称完全匹配）
     - 值：地点列表
       - 每个时间段的第一个地点为场务地点
       - 其余地点为面试官地点
       - 不同时间段可以使用不同的地点列表

2. interviewee_config:
   - input_file: 面试者信息表的路径
   - slot_weights: 各时间段的权重列表（可选）
     - 如果提供，数量必须与实际时间段数量相匹配
     - 如果不提供，则平均分配面试者到各时间段
     - 权重值必须为正整数

3. second_interview_config:
    - input_file: 二面面试者信息表的路径
    - times: 二面时间段列表
      - 每个时间段的名称必须与Excel表中的时间段名称完全匹配

## 环境配置

### 系统要求
- Python 3.7 或更高版本
- pip 包管理器

### 安装依赖
1. 克隆或下载本项目到本地

2. 在项目根目录下安装所需依赖：
```bash
pip install -r requirements.txt
```

所需的主要依赖包括：
- pandas >= 1.5.0：用于数据处理和Excel文件操作
- openpyxl >= 3.0.10：用于Excel文件的读写
- xlsxwriter >= 1.3.7：用于生成Excel文件

### 推荐的开发环境
- Visual Studio Code
- PyCharm
- 或其他支持Python的IDE

## 使用方法

1. 准备配置文件
   - 复制示例配置文件或创建新的 `config.json`
   - 根据实际需求修改配置项

2. 运行面试官和场务排表程序：
```bash
python schedule_manager.py
```

3. 运行一面面试者排表程序：
```bash
python interviewee_scheduler.py
```

4. 运行二面面试者排表程序：
```bash
python second_interview.py
```

## 输入文件格式要求

### 1. interviewer.xlsx
- 必须包含带有"姓名"、"部门"、"面试官"、"场务"等关键字的列
- 时间段之间使用全角顿号（、）分隔

### 2. interviewee.xlsx
- 必须包含带有"姓名"、"学号"、"面试时间"等关键字的列
- 时间段之间使用全角顿号（、）分隔

### 3. second_interviewee.xlsx
- 标题（第一行）必须是“人资”、“外联”、“策划”、“宣传”

## 输出文件说明

### 1. 面试官和场务排班 (schedule.xlsx)
- 包含时间、地点、职务、姓名、部门等信息
- 相同时间和地点的单元格自动合并
- 提供详细的日志文件，包含工作量统计和警告信息

### 2. 面试者安排 (interviewee_schedule.xlsx)
- 包含时间、姓名、学号等信息
- 相同时间段的行使用相同的浅色背景
- 不同时间段使用不同颜色区分
- 提供详细的日志文件，包含分配情况和未分配学生信息

### 3. 二面面试者安排 (second_schedule.xlsx)
- 只包含姓名、时间、部门等信息
- 提供详细的日志文件，包括分配的结果和需要面试两轮的名单

## 注意事项

1. 确保输入文件放在正确的位置（tables目录下）
2. 输入文件中的时间格式必须统一
3. 配置文件中出现的时间段数据与原始表格中的时间段必须完全吻合
4. 学号会以文本格式保存，避免出现科学计数法
5. 如果有未能分配的学生，会在日志文件中列出详细信息
6. 程序会自动创建output目录（如果不存在）
7. 配置文件必须使用UTF-8编码保存 

## Make方法（v5.0之后新增功能）

为了方便用户使用，我们在v5.0之后加入了makefile文件，可以直接使用make命令运行不同的程序，以实现不同的功能。

 1. 配置虚拟环境和相关依赖

```bash
make setup
```

 2. 运行面试官和场务排表程序

```bash
make interviewer
```

 3. 运行一面面试者排表程序

```bash
make interviewee_1
```

 4. 运行二面面试者排表程序

```bash
make interviewee_2
```

利用Makefile文件，可以更方便地运行程序，提高工作效率。