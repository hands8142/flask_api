from flask import Flask
from flask_restful import Api, Resource
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import requests as rq
import re

app = Flask(__name__)
api = Api(app)

base_music = {
    "success": True
}
base_naver = {
    "success": True
}

class weather(Resource):
    def get(self, location):
        Finallocation = location + '날씨'
        LocationInfo = ""
        NowTemp = ""
        CheckDust = []
        url = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=' + Finallocation
        hdr = {'User-Agent': (
            'mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36')}
        req = rq.get(url, headers=hdr)
        html = req.text
        soup = bs(html, 'html.parser')

        # 오류 체크
        ErrorCheck = soup.find('span', {'class': 'btn_select'})

        if 'None' in str(ErrorCheck):
            return {
                "success": False,
                "error" : "오류"
                }, 400
        else:
            # 지역 정보
            for i in soup.select('span[class=btn_select]'):
                LocationInfo = i.text

            NowTemp = soup.find('span', {'class': 'todaytemp'}).text + soup.find('span', {'class': 'tempmark'}).text[2:]

            WeatherCast = soup.find('p', {'class': 'cast_txt'}).text

            TodayMorningTemp = soup.find('span', {'class': 'min'}).text
            TodayAfternoonTemp = soup.find('span', {'class': 'max'}).text
            TodayFeelTemp = soup.find('span', {'class': 'sensible'}).text[5:]

            TodayUV = soup.find('span', {'class': 'indicator'}).text[4:-2] + " " + soup.find('span', {
                'class': 'indicator'}).text[-2:]

            CheckDust1 = soup.find('div', {'class': 'sub_info'})
            CheckDust2 = CheckDust1.find('div', {'class': 'detail_box'})
            for i in CheckDust2.select('dd'):
                CheckDust.append(i.text)
            FineDust = CheckDust[0][:-2] + " " + CheckDust[0][-2:]
            UltraFineDust = CheckDust[1][:-2] + " " + CheckDust[1][-2:]
            Ozon = CheckDust[2][:-2] + " " + CheckDust[2][-2:]
            return {
                "success": True,
                "지역": LocationInfo,
                "현재온도": NowTemp,
                "체감온도": TodayFeelTemp,
                "정보": WeatherCast,
                "자외선": TodayUV,
                "최저최고온도" : f"{TodayMorningTemp}/{TodayAfternoonTemp}",
                "미세먼지": FineDust,
                "초미세먼지": UltraFineDust,
                "오존 지수": Ozon
                }

class music(Resource):
    def get(self):
        targetSite = 'https://www.melon.com/chart/index.htm'
        header = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        melonrqRetry = rq.get(targetSite, headers=header)
        melonht = melonrqRetry.text
        melonsp = bs(melonht, 'html.parser')
        artists = melonsp.findAll('span', {'class': 'checkEllipsis'})
        titles = melonsp.findAll('div', {'class': 'ellipsis rank01'})
        for i in range(len(titles)):
            artist = artists[i].text.strip()
            title = titles[i].text.strip()
            base_music[i + 1] = '{0} - {1}'.format(artist, title)
        return base_music

class naver(Resource):
    def get(self):
        targetSite = 'https://datalab.naver.com/keyword/realtimeList.naver?groupingLevel=3&where=main'
        header = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        source = rq.get(targetSite, headers=header).text
        soup = bs(source, "html.parser")
        hotKeys = soup.select("span.item_title")
        index = 0
        for key in hotKeys:
            index += 1
            base_naver[index] = key.text
        return base_naver

class corona(Resource):
    def get(self):
        covidSite = "http://ncov.mohw.go.kr/index.jsp"
        covidNotice = "http://ncov.mohw.go.kr"
        html = urlopen(covidSite)
        soup = bs(html, 'html.parser')
        latestupdateTime = soup.find('span', {'class': "livedate"}).text.split(',')[0][1:].split('.')
        statisticalNumbers = soup.findAll('span', {'class': 'num'})
        beforedayNumbers = soup.findAll('span', {'class': 'before'})

        briefTasks = []
        mainbrief = soup.findAll('a', {'href': re.compile('\/tcmBoardView\.do\?contSeq=[0-9]*')})
        for brf in mainbrief:
            container = []
            container.append(brf.text)
            container.append(covidNotice + brf['href'])
            briefTasks.append(container)

        statNum = []
        beforeNum = []
        for num in range(7):
            statNum.append(statisticalNumbers[num].text)
        for num in range(4):
            beforeNum.append(beforedayNumbers[num].text.split('(')[-1].split(')')[0])

        totalPeopletoInt = statNum[0].split(')')[-1].split(',')
        tpInt = ''.join(totalPeopletoInt)
        lethatRate = round((int(statNum[3]) / int(tpInt)) * 100, 2)
        return {
            "success": True,
            "time": latestupdateTime[0] + "월 " + latestupdateTime[1] + "일 " + latestupdateTime[2],
            "확진환자": statNum[0].split(')')[-1] + "(" + beforeNum[0] + ")",
            "완치환자": statNum[1] + "(" + beforeNum[1] + ")",
            "치료중": statNum[2] + "(" + beforeNum[2] + ")",
            "사망": statNum[3] + "(" + beforeNum[3] + ")",
            "누적확진률": statNum[6],
            "치사율": str(lethatRate) + " %"
        }

class home(Resource):
    def get(self):
        return {
            "list": {
                "music": "/music",
                "corona": "/corona",
                "naver": "/naver",
                "weather": "/weather/<location>"
                }
            }

api.add_resource(weather, "/weather/<location>")
api.add_resource(music, "/music")
api.add_resource(naver, "/naver")
api.add_resource(corona, "/corona")
api.add_resource(home, "/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)