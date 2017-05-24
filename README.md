# 一、说明
Weaknet-iptables脚本是为了解决弱网络使用过程中，有时会出现的在关闭弱网络之后，服务器iptables的mangle表内规则并没有完全删掉的问题。

# 二、环境搭建与运行

## 1.获取源码
<pre>
sudo git clone https://github.com/romebake/weaknet_iptables.git
</pre>

## 2.安装所需python库
<pre>
sudo pip install logging python-iptables ConcurrentLogHandler
</pre>

## 3.运行
### （1）直接运行
<pre>
cd weaknet_iptables/
sudo python server.py
</pre>

### （2）后台运行
<pre>
cd weaknet_iptables/
sudo nohup python server.py &
</pre>

### （3）Screen后台运行
<pre>
sudo screen -S weaknet_iptables
cd weaknet_iptables/
sudo python server.py
ctrl + a + d
</pre>