# MySQL group replication 搭建工具
程序名：deploy_mgr

### 程序结构：
```
deploy_mgr/
|-- bin/
|   |-- __init__.py
|   |-- run.py
|
|-- core/
|   |-- __init__.py
|   |-- main.py  
|-- conf/
|   |-- ini_mgr.conf   		  ##deploy_mgr配置文件
|   |-- example_ini_mgr.conf  ##参考配置文件
|-- db_data.tar.gz    ##一个MySQL数据库datadir压缩包，可替换。数据库目录名为"db_data"。库中用户'root'@'%'密码为'mysql'，程序最后会将该用户rename为'root'@'localhost'.
|-- README.txt

```

### 运行环境：
Python3.0或以上版本环境均可。


### 执行方法：
python3 run.py
	
### 使用方法：
1) 编辑配置文件conf/ini_mgr.conf，以下为配置文件参数解析:
  
##[mgr]必须存在
[mgr]
##该部分主要有以下四个参数,
##mgr_user为MySQL group replication内部通讯用户，也就是change master时需要用到的用户
##mgr_password为该用户的密码
##mgr_port为MySQL group replication内部通讯端口。
##用户需要根据自己实际情况更改
loose-group_replication_group_name = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
loose-group_replication_group_seeds = "10.0.0.11:33072,10.0.0.13:33072,10.0.0.14:33072"
mgr_user = 'rpl_user'@'%'
mgr_password = rpl_pass
mgr_port=33072

###以下为每个节点的主要信息，
##以[node1]为例，其中除ipaddr,ssh_user,ssh_password三个参数外，其他参数都要出现在MySQL参数文件的[mysqld]部分
##ipaddr为服务器的ip地址，ssh_user为ssh登陆用户名，ssh_password为ssh登陆时的用户密码。
##以下几个参数为参数文件中必须有的，其他需要出现在mysql参数文件[mysqld]中的用户可加在对应节点下
[node1]
basedir = /usr/local/mysql57
datadir = /57data/data
user = mysql
port = 3306
server_id = 1
socket = /tmp/mysql.sock

ipaddr =10.0.0.11
ssh_user = root
ssh_password = freedom

[node2]
basedir = /usr/local/mysql57
datadir = /57data/data
user = mysql
port = 3306
server_id = 1
socket = /tmp/mysql.sock

ipaddr =10.0.0.13
ssh_user = root
ssh_password = freedom	  

[node3]
basedir = /usr/local/mysql57
datadir = /57data/data
user = mysql
port = 3306
server_id = 1
socket = /tmp/mysql.sock

ipaddr =10.0.0.14
ssh_user = root

2)所有MySQL节点的'root'@'localhost'初始密码为'mysql',用户需要自己更改。


