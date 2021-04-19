# 一、前言
## 1.说明
本项目本质上是使用的腾讯官方提供的网页微信接口，将一个微信号长期挂在网页微信上充当机器人。
采用python的itchat库实现。
## 2.功能
功能主要分为两部分。
第一个是识别出对话信息中包含的关键字，按关键字返回相应的对话。
第二个是非关键字的智能对话。
## 3.准备
准备一个微信号，如果是新申请的账号，可以到网页微信那里试试看是否可以正常登录。
貌似新注册的账号会被禁止登录网页微信。自行百度查查如何解决。
“为了你的帐号安全，此微信号不能登录网页微信。你可以使用Windows微信或Mac微信在电脑端登录”

# 二、组件
## 1.Docker
架构上采用Nacos、Minio、Mongo、Python几个组件实现。
Nacos用来存储所有的配置信息， Minio用来保存图片文档，Monog保存聊天数据，Python提供接口服务。
在服务器中采用docker部署。
其中，我使用了selenium镜像代替python镜像，因为在设计中用到了图片处理，而在python镜像中缺少相应的依赖环境，无法进行截图，故采用在selenium镜像中安装python来实现。

```shell
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
mkdir -p /etc/docker
tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://otv9pb9m.mirror.aliyuncs.com"]
}
EOF
systemctl daemon-reload
systemctl restart docker
#开机自启动
systemctl enable docker
```

```shell
docker pull nacos/nacos-server
docker pull minio/minio
docker pull mongo
docker pull selenium/standalone-chrome
```

```shell
docker run -itd --name=mongo -p 27017:27017 mongo --bind_ip_all
docker run -itd --name=minio -p 9000:9000 -e MINIO_ACCESS_KEY=root-e MINIO_SECRET_KEY=mima minio/minio server /data
docker run -itd --name=nacos -p 8848:8848 -e MODE=standalone nacos/nacos-server
docker run -itd --name=wechat selenium/standalone-chrome
```

## 2.Nacos
登录http://IP:8848/nacos
默认账户密码nacos/nacos
在默认命名空间public导入nacos_config.zip配置文件。

## 3.Minio
登录http://IP:9000
账号密码参考docker创建时的环境参数，即上文的root/mima。
右下角创建文件桶，命名wechat，编辑策略为可读写。

## 4.Selenium
进入wechat容器
```shell
echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ bionic main restricted universe multiverse" >/etc/apt/sources.list &&
echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ bionic-updates main restricted universe multiverse" >>/etc/apt/sources.list &&
echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ bionic-backports main restricted universe multiverse" >>/etc/apt/sources.list &&
echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ bionic-security main restricted universe multiverse" >>/etc/apt/sources.list

gpg --keyserver keyserver.ubuntu.com --recv 3B4FE6ACC0B21F32 && gpg --export --armor 3B4FE6ACC0B21F32 | apt-key add -

apt-get update&&apt-get upgrade

apt install python3-pip git

pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple setuptools requests pymongo itchat minio pyecharts nacos-sdk-python snapshot_phantomjs

mkdir /home/wechat && cd /home/wechat
git init && git remote add origin https://gitee.com/MrYuGoui/wechat.git && git pull origin master

tar -xvf phantomjs-2.1.1-linux-x86_64.tar.bz2 -C /usr/local/

mv /usr/local/phantomjs-2.1.1-linux-x86_64/ /usr/local/phantomjs

ln -s /usr/local/phantomjs/bin/phantomjs /usr/bin/

修改源码中get_key函数下的Nacos组件地址为相应组件IP

python3 wechat.py
```
