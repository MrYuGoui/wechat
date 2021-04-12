import requests, os, time, json, random, itchat, re, pymongo, nacos
from itchat.content import *
from collections import Counter
from minio import Minio
from datetime import timedelta
from random import randint
from snapshot_phantomjs import snapshot
from pyecharts.render import make_snapshot
from pyecharts.charts import *
from pyecharts import options as opts


def get_key(x):
    '''
    获取各个组件的账号密码
    :param x: 组件名
    :return: 值
    '''
    client = nacos.NacosClient("49.232.159.40:8848", namespace="public")
    res = client.get_config("common.json", "DEFAULT_GROUP")
    return json.loads(res)[x]


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
        api_word = get_key("api_word")
        api_num = [each for each in api_word if each in msg]
        if len(api_num) != 0:
            cache = api_word[api_num[0]]
            if cache["类型"] == "接口0":
                return "我可以识别以下关键字：" + "，".join([each for each in api_word])
            elif cache["类型"] == "接口1":
                return self.api_func1(cache["链接"])
            elif cache["类型"] == "接口2":
                return self.api_func2(api_num[0])
            elif cache["类型"] == "接口3":
                return self.api_func3()
            elif cache["类型"] == "接口4":
                return self.api_func4(self.group)
            else:
                pass
        else:
            return self.tuling(msg)

    def api_func1(self, link):
        '''
        沙雕网站接口：https://shadiao.app/
        :param link:接口地址
        :return:
        '''
        res = requests.get(link).text
        return res

    def api_func2(self, kw):
        '''
        小破站接口：https://wangpinpin.com/
        :param kw:关键字
        :return:
        '''
        res = requests.get("https://api.wangpinpin.com/unAuth/findTypeList?t=DOG")
        cache = [each for each in json.loads(res.text)["data"] if each["name"] == kw]
        response = requests.get(f"https://api.wangpinpin.com/unAuth/getDoglickingDiary?typeId={cache[0]['id']}")
        return json.loads(response.text)["data"]

    def api_func3(self):
        '''
        小破站接口：https://wangpinpin.com/
        :return: 每日一文
        '''
        res = requests.get("https://api.wangpinpin.com/unAuth/getEveryDayText")
        res_data = json.loads(res.text)["data"]
        return f"{res_data['title']}\n作者：{res_data['author']}\n{res_data['content']}"

    def api_func4(self, group_id):
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
        # return f"{res_sort[0][0]}今日发言{res_sort[0][1]}次，{random.choice(gk)}"

    def tuling(self, words):
        '''
        智能问答
        :param words:对话内容
        :return:
        '''
        limit = 8
        api_key = "0d264fefe55c487255e8fc245ee5639c"
        api_secret = "mpdhgj5ni4qk"
        res = requests.get(
            url=f"http://i.itpk.cn/api.php?question={words}&limit={limit}&api_key={api_key}&api_secret={api_secret}")
        return res.text


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
        make_snapshot(snapshot, f"{self.file_name}.html", f"{self.file_name}.jpeg", is_remove_html=True, pixel_ratio=2, delay=1)
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
        func_image.add("龙王", data_pair=data_list, word_size_range=[10, 80], shape=random.choice(['circle', 'cardioid', 'diamond', 'triangle-forward', 'triangle', 'pentagon', 'star']))
        func_image.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", position="outside"))
        return func_image

    def bar_func(self, data_list):
        func_image = Bar(init_opts=opts.InitOpts(bg_color="#ffffff"))
        func_image.add_xaxis([each[0] for each in data_list])
        func_image.add_yaxis("龙王", [each[1] for each in data_list], category_gap="40%")
        func_image.set_series_opts(label_opts=opts.LabelOpts(formatter="{c}", position=random.choice(["inside", "outside"])))
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
        func_image.add_yaxis("龙王", [each[1] for each in data_list], is_smooth=random.choice([True, False]), symbol_size=10,
                             symbol=random.choice(['circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow']))
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
        Client = Minio(f"{res['host']}:{res['port']}", access_key=res['username'], secret_key=res['password'], secure=False)
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
                itchat.send_msg(msg=f"我拦截了{result['group']}群聊{result['player']}说的一句话：{result['info']}", toUserName=myself["UserName"])
                return
            elif result["type"] == "Picture":
                info = get_key("minio")
                Client = Minio(f"{info['host']}:{info['port']}", access_key=info['username'], secret_key=info['password'], secure=False)
                img_link = Client.presigned_get_object('wechat', result['file'], expires=timedelta(days=1))
                itchat.send_msg(msg=f"我拦截了{result['group']}群聊{result['player']}发的一张图：{img_link}", toUserName=myself["UserName"])
                return


if __name__ == '__main__':
    itchat.auto_login(hotReload=True, enableCmdQR=2, statusStorageDir="DK.pkl")
    friend_list = itchat.get_friends(update=True)
    myself = [each for each in friend_list if each["RemarkName"] == "MrYuGoui_Self"][0]
    itchat.run()
