# 一、说明
Weaknet-iptables脚本是为了解决弱网络使用过程中，有时会出现的在关闭弱网络之后，服务器iptables的mangle表内规则并没有完全删掉的问题。

# 二、环境搭建与运行

## 1.获取源码
<pre>
git clone http://10.20.108.107:3000/mayabin/weaknet_iptables.git
</pre>

## 2.安装所需python库
<pre>
pip install logging python-iptables ConcurrentLogHandler
</pre>

## 3.运行
### （1）直接运行
<pre>
cd weaknet_iptables/
python server.py
</pre>

### （2）后台运行
<pre>
cd weaknet_iptables/
nohup python server.py &
</pre>