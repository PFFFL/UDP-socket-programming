UDP Socket 编程实验 - 程序运行说明文档
========================================

一、项目概述
------------
本项目实现了基于UDP的可靠数据传输协议，模拟TCP的连接建立和可靠传输机制。
包含客户端(udpclient.py)和服务器端(udpserver.py)两个程序。

二、运行环境
------------
- Python 3.13
- 依赖库: pandas (用于统计分析)
- Windows cmd

安装依赖：
pip install pandas

三、文件结构
------------
├── udpclient.py              # 客户端程序
├── udpserver.py              # 服务器端程序
├── readme.txt                # 运行说明文档
└── run_log.txt               # 运行日志文件(程序自动生成)
└── server_log.txt            # 运行日志文件(程序自动生成)
└── udp_packet_capture.docx   # 说明文档      

四、配置选项
------------

4.1 客户端配置
在udpclient.py中可修改以下参数：
- STUDENT_ID: 学号后4位与0x5A3C进行XOR运算的结果
- WINDOW_SIZE: 发送窗口大小，默认400字节
- MIN_DATA_SIZE: 最小数据长度，默认40字节
- MAX_DATA_SIZE: 最大数据长度，默认80字节
- TIMEOUT_BASE: 超时时间，默认300ms
- NUM_PACKETS: 发送数据包总数，默认30个

4.2 服务器配置
在udpserver.py中可修改以下参数：
- LOSS_RATE: 模拟丢包率，默认0.3(30%)

五、运行方式
------------

5.1 启动服务器
命令格式：
python udpserver.py <serverPort>

示例：
python udpserver.py 12000

5.2 启动客户端
命令格式：
python udpclient.py <serverIP> <serverPort>

示例：
python udpclient.py 127.0.0.1 12000

六、协议格式
------------

6.1 连接请求报文 (CONNECT_REQUEST)
格式：| 1字节类型 | 2字节StudentID |
类型值：0x01

6.2 连接响应报文 (CONNECT_RESPONSE)
格式：| 1字节类型 | 1字节状态码 |
类型值：0x02
状态码：0x00成功，0x01失败

6.3 数据报文 (DATA)
格式：| 1字节类型 | 2字节序列号 | 2字节数据长度 | N字节数据 |
类型值：0x03

6.4 确认报文 (ACK)
格式：| 1字节类型 | 2字节确认号 |
类型值：0x04

七、功能特性
------------
1. 模拟TCP连接建立过程
2. StudentID验证机制
3. GBN(Go-Back-N)协议实现
4. 超时重传机制
5. 随机丢包模拟
6. 累积确认
7. RTT统计分析(最大、最小、平均、标准差)
8. 运行日志记录

八、StudentID计算规则
---------------------
取学号后4位数字，与0x5A3C进行XOR运算，结果填入连接请求报文中。
服务器验证：收到的值再次XOR 0x5A3C，检查结果是否在0-9999范围内。

九、注意事项
------------
1. 运行前确保服务器已启动并监听指定端口
2. 客户端和服务器需在同一网络环境下，确保网络可达
3. 日志文件run_log.txt,server_log.txt会被自动生成，记录所有收发事件
4. 使用Wireshark进行抓包分析

十、测试步骤
------------
1. 启动服务器：python udpserver.py 12000
2. 启动Wireshark抓包，过滤udp端口12000
3. 启动客户端：python udpclient.py 127.0.0.1 12000
4. 观察客户端输出和日志文件
5. 停止服务器