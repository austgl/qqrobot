# -*- coding: utf-8 -*-
import urllib2, re
class HTML_Tool:
    # 用非 贪婪模式 匹配 \t 或者 \n 或者 空格 或者 超链接 或者 图片
    BgnCharToNoneRex = re.compile("(\t|\n| |<a.*?>|<img.*?>)")

    # 用非 贪婪模式 匹配 任意<>标签
    EndCharToNoneRex = re.compile("<.*?>")

    # 用非 贪婪模式 匹配 任意<p>标签
    BgnPartRex = re.compile("<p.*?>")
    CharToNewLineRex = re.compile("(<br>|</p>|<tr>|<div>|</div>)")
    CharToNextTabRex = re.compile("<td>")

    # 将一些html的符号实体转变为原始符号
    replaceTab = [("&lt;","<"),("&gt;",">"),("&amp;","&"),("&amp;","\""),("&nbsp;"," ")]

    def Replace_Char(self,x):
        x = self.BgnCharToNoneRex.sub("",x)
        x = self.BgnPartRex.sub("\n    ",x)
        x = self.CharToNewLineRex.sub("\n",x)
        x = self.CharToNextTabRex.sub("\t",x)
        x = self.EndCharToNoneRex.sub("",x)

        for t in self.replaceTab:
            x = x.replace(t[0],t[1])
        return x

def qiubai():
    page = 1
    total = []
    tool = HTML_Tool()
    while len(total)<20:
        myUrl = "http://m.qiushibaike.com/hot/page/" + str(page)
        request = urllib2.Request(myUrl)
        request.add_header('User-Agent', 'fake-client')
        response = urllib2.urlopen(request)
        myPage = response.read()
        unicodePage = myPage.decode("utf-8")
        myItems = re.findall('<div.*?class="content".*?title="(.*?)">(.*?)<div class="stats clearfix">',unicodePage,re.S)

        items = []
        for item in myItems:
            items.append([item[1].replace("\n","")])
        for i in range(len(items)):
            string = items[i][0].encode("utf-8")
            if not string.endswith('</a></div>'):
                each = tool.Replace_Char(items[i][0][:-6])
                total.append(each)
        page = page+1
    return total
