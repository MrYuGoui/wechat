import requests, os, time, json, random, itchat, re, pymongo
from itchat.content import *
from collections import Counter
from minio import Minio
from datetime import timedelta
from random import randint
from snapshot_phantomjs import snapshot
from pyecharts.render import make_snapshot
from pyecharts.charts import *
from pyecharts import options as opts

res_json = {
    "mongo": {
        "host": "49.232.159.40",
        "port": 27017,
        "database": "wechat",
        "username": "root",
        "password": "YuHaoWei0830!"
    },
    "minio": {
        "host": "49.232.159.40",
        "port": 9000,
        "username": "minioadmin",
        "password": "minioadmin"
    },
    "pyecharts": [
        "funnel",
        "pie",
        "wordcloud",
        "bar",
        "line"
    ],
    "ai_gen": 1,
    "dragon": [
        "无人能出其右",
        "我愿称你为最强",
        "感谢你为本群增加了活跃度",
        "已经仅次于我了",
        "隔着屏幕我都能闻到键盘在冒火星",
        "不会吧不会吧，居然有人像我一样无聊",
        "本数据纯属虚构，请勿核查，版权所有，翻版必究",
        "脱口秀大会没有你，我把电视砸了，老铁们我做的对么？",
        "干啥啥不行，水群第一名",
        "按照一个字一个砖头来算，够垒一座坟了",
        "贿赂我可以清空他/它的数据，你们考虑下？",
        "我怀疑你是群主请来的托",
        "你喜欢唱、跳、Rap和水群？",
        "舍得一身剐，敢把龙王拉下马！",
        "其他人都是哑巴么",
        "承包了10.24%的群聊消息",
        "战胜了95.27%群友",
        "前无古人后无来者",
        "累死你个鳖孙",
        "留给其他人的时间不多了",
        "难道你也是个聊天机器人？",
        "来人，掌嘴！",
        "不听不听王八念经",
        "我瞎编的，如有雷同，不胜荣幸",
        "和蜘蛛侠、死侍并称嘴炮三巨头",
        "荣升五代目嘴影",
        "拦都拦不住，TMD，我都烦死了",
        "明年年初，中美合拍西游记即将开机，我将出演龙王三太子，请大家多多支持",
        "给龙王来一杯卡布奇诺，开始你的脱口秀",
        "你们可能不知道几句话赢得龙王是什么概念，我们用两个字来形容：唠怪！",
        "你今天能蝉联一整天龙王，我~当~场~就把这个电脑屏幕吃掉！"
    ]
}


class MongoTool():
    '''
    数据库工具
    '''

    def __init__(self):
        self.info = get_key("mongo")
        self.client = pymongo.MongoClient(host=self.info["host"], port=self.info["port"],
                                          username=self.info["username"], password=self.info["password"])

    def insert_one(self, mg):
        '''
        插入一条数据
        :param mg: 整理后的数据格式
        :return: 无
        '''
        self.client["wechat"]["logs"].insert_one(mg)
        self.client.close()

    def search_all(self, mg):
        '''
        查询满足条件的多条数据
        :param mg: 判定条件
        :return:返回多条数据，mongo格式，需要list(res)转为列表
        '''
        res = self.client["wechat"]["logs"].find(mg)
        self.client.close()
        return res


class ProcessWord():
    '''
    语言处理
    '''

    def __init__(self, word, myname, group):
        '''
        初始化
        :param word: 需要处理的语言
        :param myname: AI在群组的昵称，用于判断语言是否@自己
        :param group: 语言所在的群组
        '''
        self.word = word
        self.myname = myname
        self.group = group

    def start_func(self):
        '''
        执行函数
        :return: 返回回复
        '''
        res = self.first_process(self.word, self.myname)
        if res != "no message":
            return self.second_process(res)
        else:
            pass

    def first_process(self, word, myname):
        '''
        一轮处理，过滤引用内容，过滤非提及AI内容
        :param word:语言
        :param myname:AI在群组的昵称
        :return:返回处理后的内容
        '''

        # 如果存在引用，筛选保留引用符号后的内容
        split_kw = r"- - - - - - - - - - - - - - -"
        if split_kw in word:
            let_msg = word.split(split_kw)[1]
        else:
            let_msg = word
        res_per = get_key("ai_gen")
        # 如果提及“我”，则处理回复，反之，有概率回复,回复概率5%。
        if myname in let_msg:
            let_msg = let_msg.replace(f"@{myname}", "").replace(myname, "")
            return let_msg
        elif randint(0, 100) <= res_per:
            return let_msg
        else:
            return "no message"

    def second_process(self, msg):
        '''
        二轮处理，判断语言中是否存在触发关键字
        :param msg:上一轮处理后的内容
        :return:返回处理后的内容
        '''

        # 轮询信息中是否存在接口的关键字，如果存在则调用接口，反之交给图灵机器人
        if "龙王" in msg:
            return self.api_func(self.group)
        else:
            res = requests.get(f"http://172.17.0.5:8080/kw?keyword={msg}")
            # print(type(res.text))
            return json.loads(res.text)["content"]

    def api_func(self, group_id):
        '''
        统计龙王数据
        :param group_id:群组名称
        :return:
        '''
        s = time.strftime('%Y%m%d', time.localtime(time.time() + 28800))
        # 查询聊天记录
        res = MongoTool().search_all({"group": group_id, "date": s, "type": "Text"})
        # 统计为{“player”:num}
        c_d = dict(Counter([each["player"] for each in list(res)]))
        # if "粗米且" in c_d:
        #     c_d["粗米且"]+=444
        # 转换为[("player",num)]
        res_sort = sorted(c_d.items(), key=lambda x: x[1], reverse=True)

        # gk = get_key("dragon")
        img = PyE(res_sort[:10]).start_func()
        return img


class PyE():
    def __init__(self, data_list):
        self.file_name = time.time()
        self.pyecharts = random.choice(get_key("pyecharts"))
        self.data_list = data_list
        self.title = f"{data_list[0][0]}今日发言{data_list[0][1]}次"
        self.subtitle = f"{random.choice(get_key('dragon'))}"
        self.fs1 = 25
        self.fs2 = 20

    def start_func(self):
        self.choose_func()
        return f"{self.file_name}.jpeg"

    def choose_func(self):
        if self.pyecharts == "funnel":
            res = self.funnel_func(self.data_list)
            print("funnel")
        elif self.pyecharts == "pie":
            res = self.pie_func(self.data_list)
            print("pie")
        elif self.pyecharts == "wordcloud":
            res = self.wordcloud_func(self.data_list)
            print("wordcloud")
        elif self.pyecharts == "bar":
            res = self.bar_func(self.data_list)
            print("bar")
        elif self.pyecharts == "effectscatter":
            res = self.effectscatter_func(self.data_list)
            print("effectscatter")
        elif self.pyecharts == "line":
            res = self.line_func(self.data_list)
            print("line")
        else:
            pass

        res.set_global_opts(title_opts=opts.TitleOpts(title=self.title,
                                                      subtitle=self.subtitle,
                                                      pos_left="center",
                                                      title_textstyle_opts=opts.TextStyleOpts(font_size=self.fs1),
                                                      subtitle_textstyle_opts=opts.TextStyleOpts(font_size=self.fs2)),
                            legend_opts=opts.LegendOpts(is_show=False))
        res.render(f"{self.file_name}.html")
        make_snapshot(snapshot, f"{self.file_name}.html", f"{self.file_name}.jpeg", is_remove_html=True, pixel_ratio=2,
                      delay=1)
        return

    def funnel_func(self, data_list):
        func_image = Funnel(init_opts=opts.InitOpts(bg_color="#ffffff"))
        func_image.add("龙王", data_pair=data_list, sort_=random.choice(["ascending", "descending", "none"]))
        func_image.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", position=random.choice(["inside"])))
        return func_image

    def pie_func(self, data_list):
        func_image = Pie(init_opts=opts.InitOpts(bg_color="#ffffff"))
        func_image.add("龙王", data_pair=data_list, rosetype=random.choice(["radius", "area", "none"]))
        func_image.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", position="outside"))
        return func_image

    def wordcloud_func(self, data_list):
        func_image = WordCloud(init_opts=opts.InitOpts(bg_color="#ffffff"))
        func_image.add("龙王", data_pair=data_list, word_size_range=[10, 80], shape=random.choice(
            ['circle', 'cardioid', 'diamond', 'triangle-forward', 'triangle', 'pentagon', 'star']))
        func_image.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", position="outside"))
        return func_image

    def bar_func(self, data_list):
        func_image = Bar(init_opts=opts.InitOpts(bg_color="#ffffff"))
        func_image.add_xaxis([each[0] for each in data_list])
        func_image.add_yaxis("龙王", [each[1] for each in data_list], category_gap="40%")
        func_image.set_series_opts(
            label_opts=opts.LabelOpts(formatter="{c}", position=random.choice(["inside", "outside"])))
        func_image.set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-20)))
        return func_image

    def effectscatter_func(self, data_list):
        func_image = EffectScatter(init_opts=opts.InitOpts(bg_color="#ffffff"))
        func_image.add_xaxis([each[0] for each in data_list])
        func_image.add_yaxis("龙王", [each[1] for each in data_list])
        func_image.set_series_opts(label_opts=opts.LabelOpts(position=random.choice(["outside"])))
        func_image.set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-20)))
        return func_image

    def line_func(self, data_list):
        func_image = Line(init_opts=opts.InitOpts(bg_color="#ffffff"))
        func_image.add_xaxis([each[0] for each in data_list])
        func_image.add_yaxis("龙王", [each[1] for each in data_list], is_smooth=random.choice([True, False]),
                             symbol_size=10,
                             symbol=random.choice(
                                 ['circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow']))
        func_image.set_series_opts(label_opts=opts.LabelOpts(position=random.choice(["outside"])))
        func_image.set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-20)))
        return func_image


@itchat.msg_register(INCOME_MSG, isGroupChat=True)
def listen_message(msg):
    # 提取需要保存的数据
    # print(msg)

    # 获取群成员头像
    # a=itchat.get_head_img(chatroomUserName=msg["FromUserName"],userName=msg["ActualUserName"])
    # with open("a.png","wb") as f:
    #     f.write(a)
    # f.close()
    # print(a)

    m = {
        "msgid": msg['MsgId'],
        "player": msg['ActualNickName'],
        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg['CreateTime'] + 28800)),
        "date": time.strftime('%Y%m%d', time.localtime(msg['CreateTime'] + 28800)),
        "type": msg['Type'],
        "info": msg['Text'],
        "group": msg["User"]["NickName"],
        "file": msg["FileName"],
        "myname": msg['User']['Self']['DisplayName']
    }

    # msginfo类型为函数无法写入mongo
    if type(m["info"]) != str and m["type"] == "Picture":
        m["info"] = "原创表情"

    MongoTool().insert_one(m)

    if m["type"] == "Text":
        pw = ProcessWord(m["info"], myname=m["myname"], group=m["group"])
        res = pw.start_func()
        if res == None:
            pass
        elif ".jpeg" in res:
            itchat.send_image(fileDir=res, toUserName=msg["FromUserName"])
            os.remove(res)
            return
        else:
            return res

    # 图片类型，判断是否为非原创标签，若是则下载并上传到minio，并删除本地图片
    elif m["type"] == "Picture" and msg["Content"] != "":
        msg.download(msg["FileName"])
        res = get_key("minio")
        Client = Minio(f"{res['host']}:{res['port']}", access_key=res['username'], secret_key=res['password'],
                       secure=False)
        Client.fput_object("wechat", msg["FileName"], msg["FileName"])
        os.remove(msg["FileName"])
        return

    # 拦截撤回信息（文字、图片）
    elif m["type"] == "Note":
        revoke_info = msg["Content"]
        p = re.match(".*?<msgid>(.*?)</msgid>.*?", revoke_info)
        if p:
            search_id = p.group(1)
            res = MongoTool().search_all({"msgid": search_id})
            result = res[0]
            if result["type"] == "Text":
                itchat.send_msg(msg=f"我拦截了{result['group']}群聊{result['player']}说的一句话：{result['info']}",
                                toUserName=myself["UserName"])
                return
            elif result["type"] == "Picture":
                info = get_key("minio")
                Client = Minio(f"{info['host']}:{info['port']}", access_key=info['username'],
                               secret_key=info['password'], secure=False)
                img_link = Client.presigned_get_object('wechat', result['file'], expires=timedelta(days=1))
                itchat.send_msg(msg=f"我拦截了{result['group']}群聊{result['player']}发的一张图：{img_link}",
                                toUserName=myself["UserName"])
                return


if __name__ == '__main__':
    itchat.auto_login(hotReload=True, enableCmdQR=2, statusStorageDir="DK.pkl")
    friend_list = itchat.get_friends(update=True)
    myself = [each for each in friend_list if each["RemarkName"] == "MrYuGoui_Self"][0]
    itchat.run()
