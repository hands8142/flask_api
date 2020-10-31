from flask import Flask
from flask_restful import Api, Resource
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import quote
import requests as rq
import re
import json
import pokepy

app = Flask(__name__)
api = Api(app)

client_id = "YeOVJk0bK59ryYiRDIiY"
client_secret = "ZBHDeMCaMe"

base_music = {
    "success": True
}
base_naver = {
    "success": True
}

@app.errorhandler(404)
def error(e):
    return {
        "success": False,
        "message": "페이지를 찾을수 없습니다.: " + str(e)
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
                "error" : "지역의 날씨를 찾을수 없습니다."
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
        try:
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
        except:
            return {
                "success": False,
                "message": "음악 차트를 가지고 올수 없습니다."
            }

class naver(Resource):
    def get(self):
        try:
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
        except:
            return {
                "success": False,
                "message": "실시간 검색어를 가지고 올수 없습니다."
            }

class corona(Resource):
    def get(self):
        try:
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
        except:
            return {
                "success": False,
                "message": "코로나 정보를 가지고 올수 없습니다."
            }

class translation(Resource):
    def get(self, source, target, trsText):
        baseurl = "https://openapi.naver.com/v1/papago/n2mt"
        try:
            if len(trsText) == 1:
                return {
                    "success": False,
                    "message": "단어 혹은 문장이 입력되지 않았어요. 다시한번 확인해주세요."
                    }
            else:
                combineword = ""
                for word in trsText:
                    combineword += "" + word
                # if entered value is sentence, assemble again and strip blank at both side
                savedCombineword = combineword.strip()
                combineword = quote(savedCombineword)
                print(combineword)
                # Make Query String.
                dataParmas = "source=" + source +"&target=" + target + "&text=" + combineword
                # Make a Request Instance
                request = Request(baseurl)
                # add header to packet
                request.add_header("X-Naver-Client-Id", client_id)
                request.add_header("X-Naver-Client-Secret", client_secret)
                response = urlopen(request, data=dataParmas.encode("utf-8"))

                responsedCode = response.getcode()
                if (responsedCode == 200):
                    response_body = response.read()
                    # response_body -> byte string : decode to utf-8
                    api_callResult = response_body.decode('utf-8')
                    # JSON data will be printed as string type. So need to make it back to type JSON(like dictionary)
                    api_callResult = json.loads(api_callResult)
                    # Final Result
                    translatedText = api_callResult['message']['result']["translatedText"]
                    return {
                        "success": True,
                        "before": savedCombineword,
                        "after": translatedText
                    }
                else:
                    return {
                        "success": False,
                        "message": "Error Code : " + responsedCode
                        }
        except HTTPError as e:
            return {
                "success": False,
                "message": "Translate Failed. HTTPError Occured."
            }

class pokemon(Resource):
    def get(self, pokename):
        try:
            if len(pokename) == 1:
                return {
                    "success": False,
                    "message": "포켓몬 이름이 입력되지 않았습니다!"
                }
            client = pokepy.V2Client()
            poke = client.get_pokemon(str(pokename))
            return {
                "success": True,
                "url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{poke.id}.png",
                "채력": poke.stats[0].base_stat,
                "공격력": poke.stats[1].base_stat,
                "방어력": poke.stats[2].base_stat,
                "특수 공격": poke.stats[3].base_stat,
                "특수 방어": poke.stats[4].base_stat,
                "스피드": poke.stats[5].base_stat,
                "타입": ", ".join(ty.type.name for ty in poke.types)
            }
        except:
            return {
                "success": False,
                "message": "포켓몬 정보를 불러오는데 실패했습니다."
            }

class home(Resource):
    def get(self):
        return {
            "list": {
                "music": "/music",
                "corona": "/corona",
                "naver": "/naver",
                "weather": "/weather/<location>",
                "translation": "/translation/<source>/<target>/<trsText>",
                "pokemon": "/pokemon/<pokename>"
                }
            }

api.add_resource(weather, "/weather/<location>")
api.add_resource(music, "/music")
api.add_resource(naver, "/naver")
api.add_resource(corona, "/corona")
api.add_resource(translation, "/translation/<source>/<target>/<trsText>")
api.add_resource(pokemon, "/pokemon/<pokename>")
api.add_resource(home, "/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)