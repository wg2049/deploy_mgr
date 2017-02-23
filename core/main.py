#!/usr/bin/env  python3
# author: wugong

import configparser
import time
import datetime
import paramiko
import os
import sys
import pymysql
import logging
import re
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# create logger
logger = logging.getLogger("inimgr")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')

# add formatter to ch and fh
ch.setFormatter(formatter)

# add ch and fh to logger
logger.addHandler(ch)

def ini_db(dbinfo):
    '''
    :param dbinfo example:{'port': '3306', 'user': 'mysql', 'ssh_user': 'root', 'ipaddr': '10.0.0.11', 'ssh_password': 'freedom', 'datadir': '/57data/data', 'cnf': 'C:\\0000\\inimgr\\tmp\\node1my.cnf201702211450', 'basedir': '/usr/local/mysql57'}
    setup the database db file and option file.
    '''
    print(dbinfo)
    t = paramiko.Transport(dbinfo["ipaddr"], 22)
    t.connect(username=dbinfo["ssh_user"], password=dbinfo["ssh_password"])
    sftp = paramiko.SFTPClient.from_transport(t)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(dbinfo["ipaddr"], 22, dbinfo["ssh_user"], dbinfo["ssh_password"])
    stdin, stdout, stderr = ssh.exec_command("adduser "+dbinfo["user"])
    db_data_arc_file=os.path.join(BASE_DIR,"db_data.tar.gz")
    upload_arc_file=os.path.dirname(dbinfo["datadir"])+"/db_data.tar.gz"
    sftp.put(db_data_arc_file,upload_arc_file)
    stdin, stdout, stderr=ssh.exec_command("cd "+os.path.dirname(dbinfo["datadir"])+" && tar -xf "+ upload_arc_file + " && rm -rf " + upload_arc_file+" && mv db_data "+os.path.basename(dbinfo["datadir"]))
    if stderr.read() != "":
        remote_cnf=dbinfo["datadir"]+"/my.cnf"
        sftp.put(dbinfo["cnf"],remote_cnf)
        ch_cmd = "chown -R " + dbinfo["user"] + ":" + dbinfo["user"] + " " + dbinfo["datadir"]+" && chmod -R 755 "+ dbinfo["datadir"]
        ssh.exec_command(ch_cmd)
    t.close()
    ssh.close()

def start_instance(dbinfo):   ##startup mysql instance 启动实例

    BASEDIR = dbinfo['basedir']
    DEFAU_FILES = dbinfo["datadir"]+"/my.cnf"
    CMD = "cd " + BASEDIR +" ; "+"bin/mysqld_safe " + " --defaults-file="+ DEFAU_FILES + " & "
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(dbinfo["ipaddr"], 22, dbinfo["ssh_user"], dbinfo["ssh_password"])
    ssh.exec_command(CMD)
    logger.info("The instance on "+ dbinfo["ipaddr"]+" port: "+dbinfo["port"]+" started.")
    #print("The instance on "+ dbinfo["ipaddr"]+" port: "+dbinfo["port"]+" started.")
    return 1

def start_up_mgr(dbinfo,mgrinfo,bootstrap_tag):##create user,change master,install plugin,start group_replication
    '''
    :param dbinfo: dbinfo is a dict.
    :param mgrinfo: mgrinfo is a dict.
    :param bootstrap_tag:  bootstrap_tag is a number.
    :return:
    '''
    mgr_user = mgrinfo['mgr_user']
    mgr_password = mgrinfo['mgr_password']
    USER = "root"
    PASS = "mysql"
    mysqlcon = pymysql.connect(user=USER,password=PASS,host=dbinfo["ipaddr"],port=int(dbinfo["port"]))
    cur = mysqlcon.cursor()
    CR_USER = "CREATE USER " + mgr_user + " IDENTIFIED BY " + "'" + mgr_password + "'"
    GR_USER = "GRANT REPLICATION SLAVE ON *.* TO " + mgr_user
    MASTER_USER=mgr_user.split("@")[0]
    CG_MASTER="CHANGE MASTER TO MASTER_USER="+MASTER_USER+", MASTER_PASSWORD='"+mgr_password+"'  FOR CHANNEL 'group_replication_recovery'"
    cur.execute("SET SQL_LOG_BIN=0")
    cur.execute(CR_USER)
    cur.execute(GR_USER)
    cur.execute(CG_MASTER)
    cur.execute("FLUSH PRIVILEGES")
    cur.execute("SET SQL_LOG_BIN=1")
    cur.execute("INSTALL PLUGIN group_replication SONAME 'group_replication.so'")
    if bootstrap_tag == 1:
        cur.execute("SET GLOBAL group_replication_bootstrap_group=ON ")
    cur.execute("START GROUP_REPLICATION")
    cur.execute("SET GLOBAL group_replication_bootstrap_group=off")
    cur.close()
    mysqlcon.close()
    logger.info("The MySQL group replication on "+dbinfo["ipaddr"]+" database port "+dbinfo["port"]+" online.")

def mgr_status(dbinfo):   ##check the mgr status 检查MGR的状态，组成员、primary site.
    USER = "root"
    PASS = "mysql"
    mysqlcon = pymysql.connect(user=USER, password=PASS, host=dbinfo["ipaddr"], port=int(dbinfo["port"]))
    cur = mysqlcon.cursor()
    def exe_sql(sql_txt):
        cur.execute(sql_txt)
        index = cur.description
        col = []
        for i in index:
            col.append(i[0])
        print("SQL> ",sql_txt,"\n")
        print(" ", ', '.join(col), "\n ", "".center(len(str(col)), "-"))
        for i in cur:
            print(" ", re.findall('^\((.+)\)$', str(i))[0].replace("'", ""))
        print("\n")
    sql1="SELECT * FROM performance_schema.replication_group_members"
    sql2="select a.* from performance_schema.replication_group_members a,performance_schema.global_status b where a.member_id=b.VARIABLE_VALUE and b.VARIABLE_NAME= 'group_replication_primary_member'"
    print("Check the MGR current group members:\n")
    exe_sql(sql1)
    time.sleep(3)
    print("Check the MGR primary site:\n")
    exe_sql(sql2)
    cur.close()
    mysqlcon.close()

def user_rename(dbinfo):   #rename user 'root'@'%' to 'root'@'localhost'
    USER = "root"
    PASS = "mysql"
    mysqlcon = pymysql.connect(user=USER, password=PASS, host=dbinfo["ipaddr"], port=int(dbinfo["port"]))
    cur = mysqlcon.cursor()
    sql1="rename user 'root'@'%' to 'root'@'localhost'"
    sql2="flush privileges"
    cur.execute(sql1)
    cur.execute(sql2)
    cur.close()
    mysqlcon.close()

def run():
    mgrconf = configparser.RawConfigParser()
    mgrconf.read(BASE_DIR + "/conf/ini_mgr.conf")
    tmp_dir = os.path.join(BASE_DIR, "tmp")
    bootstrap_tag = 1
    for i in mgrconf.sections():
        if i not in ("mgr"):
            tmp_cnf = os.path.join(tmp_dir, i + "my.cnf" + datetime.datetime.now().strftime("%Y%m%d%H%M"))
            tcnf = configparser.RawConfigParser()
            tcnf.read(tmp_cnf)
            tcnf.add_section("mysqld")
            for j in mgrconf[i]:
                if j not in ("ipaddr", "ssh_user", "ssh_password"):
                    tcnf["mysqld"][j] = mgrconf[i][j]
            tcnf['mysqld']['gtid_mode'] = 'on'
            tcnf['mysqld']['enforce_gtid_consistency'] = 'ON'
            tcnf['mysqld']['master_info_repository'] = 'TABLE'
            tcnf['mysqld']['relay_log_info_repository'] = 'TABLE'
            tcnf['mysqld']['binlog_checksum'] = 'NONE'
            tcnf['mysqld']['log_slave_updates'] = 'ON'
            tcnf['mysqld']['log_bin'] = 'binlog'
            tcnf['mysqld']['binlog_format'] = 'ROW'
            tcnf['mysqld']['transaction_write_set_extraction'] = "XXHASH64"
            tcnf['mysqld']['loose-group_replication_group_name'] = mgrconf['mgr']['loose-group_replication_group_name']
            tcnf['mysqld']['loose-group_replication_start_on_boot'] = "off"
            tcnf['mysqld']['loose-group_replication_local_address'] = mgrconf[i]["ipaddr"] + ":" + mgrconf['mgr'][
                'mgr_port']
            tcnf['mysqld']['loose-group_replication_group_seeds'] = mgrconf['mgr'][
                'loose-group_replication_group_seeds']
            tcnf['mysqld']['loose-group_replication_bootstrap_group'] = "off"

            with open(tmp_cnf, "w") as f:
                tcnf.write(f)
            dbinf = {}
            dbinf["ipaddr"] = mgrconf[i]["ipaddr"]
            dbinf["ssh_user"] = mgrconf[i]["ssh_user"]
            dbinf["ssh_password"] = mgrconf[i]["ssh_password"]
            dbinf["basedir"] = mgrconf[i]["basedir"]
            dbinf["datadir"] = mgrconf[i]["datadir"]
            dbinf["cnf"] = tmp_cnf
            dbinf["user"] = mgrconf[i]["user"]
            dbinf["port"] = mgrconf[i]["port"]
            mgrinf = {}
            mgrinf["mgr_user"] = mgrconf["mgr"]["mgr_user"]
            mgrinf["mgr_password"] = mgrconf["mgr"]["mgr_password"]

            ini_db(dbinf)
            start_instance(dbinf)
            time.sleep(2)
            start_up_mgr(dbinf, mgrinf, bootstrap_tag)
            if bootstrap_tag == 1:
                renameinfo=dbinf
            bootstrap_tag += 1

    time.sleep(5)
    logger.info("Set up MySQL GROUP Replication node done, below is the detail:\n")
    mgr_status(dbinf)
    user_rename(renameinfo)
    logger.info("The user 'root'@'localhost' password on all node is: 'mysql',Please change the password ASAP!")
