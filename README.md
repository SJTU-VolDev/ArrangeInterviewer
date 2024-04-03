## 安装依赖
```shell
pip install -r requirements.txt
```

## 运行
```shell
python main.py
```

## 目标：
+ 面试时间段划分/教室划分 （已完成）
+ 招募人员进行面试时间安排（手动罢）
+ 面试官安排（已完成）
+ 时间调整（不知道啊）

## 输入数据
+ 面试官信息 data/面试官信息.xlsx
+ 面试时间段 data/面试时间段.json
+ 具体限制  data/config.json

## 数据格式
### data/面试官信息.xlsx
| 姓名 | 面试时间 | 场务时间 |
| --- | --- | --- |

### 面试时间字段:
> %m月%d号周%w  %H:%M-%H:%M

## 输出数据
+ 面试官安排 result/面试官安排.xlsx

