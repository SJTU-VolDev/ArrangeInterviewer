## 安装依赖
```shell
pip install -r requirements.txt
```

## 运行
```shell
python main.py
```

## 功能
+ 面试时间段划分/教室划分 :heavy_check_mark:
+ 招募人员进行面试时间安排:heavy_check_mark:
+ 面试官安排::heavy_check_mark:
+ 时间调整:x:

## 输入数据
+ 面试官信息 `data/面试官信息.xlsx`
+ 面试者信息 `data/面试者信息.xlsx`
+ 面试时间段 `data/面试时间段.json`
+ 具体限制  `data/config.json`

## 数据格式
### `data/面试官信息.xlsx`
| 姓名 | 面试时间 | 场务时间 |
| --- | --- | --- |
|永雏小菲|	4月9号周二  20:00-22:00、4月10号周三  13:00-15:00 | 4月9号周二  20:00-22:00、4月10号周三  13:00-15:00|

### `data/面试者信息.xlsx`
| 姓名 | 学号 | 电话 | 邮箱 |
| --- | --- | --- | --- |
|永雏塔菲|  000000000000|	00000000000| Ace@Taffy.com

### 面试时间字段
`%m月%d号周%w  %H:%M-%H:%M`

## 输出数据
+ 面试官安排 `result/面试官安排.xlsx`
+ 面试者安排 `result/面试者安排.xlsx`

