from flask import Flask, request, jsonify, render_template
import requests
import json
import re
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

tokenURL = "https://www.warcraftlogs.com/oauth/token"
publicURL = "https://www.warcraftlogs.com/api/v2/client"

def get_token(store: bool = True):
    data = {"grant_type": "client_credentials"}
    auth = ("9c9eb67d-e840-4f7f-92c4-354f8415c98e", "GrWvaJk8BNEDlEkCQohO5pUsbsjTHc4w6LlRF57X")
    with requests.Session() as session:
        response = session.post(tokenURL, data=data, auth=auth)
    
    if store and response.status_code == 200:
        store_token(response)
    return response

def store_token(response):
    try:
        with open(".credentials.json", mode="w+", encoding="utf-8") as file:
            json.dump(response.json(), file)
    except OSError as e:
        print(e)
        return None
    
def read_token():
    try:
        with open(".credentials.json", mode="r+", encoding="utf-8") as file:
            access_token = json.load(file)
        return access_token.get("access_token")
    except OSError as e:
        print(e)
        return None

def retrieve_headers() -> dict:
    return {"Authorization": f"Bearer {read_token()}"}

query = """query($code: String, $sourceID: Int, $fight: Int){
            reportData{
                report(code: $code){
                    casts: events(fightIDs: [$fight], dataType: Casts, sourceID: $sourceID){
                        data
                    }
                    buffs: events(fightIDs: [$fight], dataType: Buffs, sourceID: $sourceID){
                        data
                    }
                    fights(fightIDs: [$fight]){
                        startTime
                        endTime
                    }
                    cast_table: table(fightIDs: [$fight], dataType: Casts, sourceID: $sourceID)
                    buff_table: table(fightIDs: [$fight], dataType: Buffs, sourceID: $sourceID)
                }
            }
            }"""

graph_query = """query($code: String, $sourceID: Int, $dtype: GraphDataType, $fight: Int, $startTime: Float, $endTime: Float){
                reportData{
                    report(code: $code){
                        graph(sourceID: $sourceID, dataType: $dtype, fightIDs: [$fight], startTime: $startTime, endTime:$endTime)
                }
            }
            }"""

def get_data(query: str, **kwargs):
    """Fetch data from the Warcraft Logs API. Please provide a query and the parameters"""
    data = {"query": query, "variables": kwargs}
    with requests.Session() as session:
        session.headers = retrieve_headers()
        response = session.post(publicURL, json=data)
    return response.json()

def parse_warcraft_logs_url(url):
    # 올바른 URL 형식 확인
    if not url.startswith("https://www.warcraftlogs.com/reports/"):
        return "올바른 형식을 넣어주세요"

    # URL 파싱
    parsed_url = urlparse(url)
    path = parsed_url.path
    query = parsed_url.fragment

    # 보고서 번호 추출
    report_number = path.split('/')[2]

    # 쿼리 파라미터 추출
    query_params = parse_qs(query)

    fight = query_params.get('fight', [None])[0]
    report_type = query_params.get('type', [None])[0]
    source = query_params.get('source', [None])[0]

    return {
        "report_number": report_number,
        "fight": int(fight),
        "type": report_type[0].upper() + report_type[1:],
        "source": int(source)
    }

def make_icon_spell_dict(table, spellDict, tableType):
    if tableType == "cast":
        key = 'entries'
    else:
        key = 'auras'
    for entry in table[key]:
        if entry["guid"] not in spellDict:
            spellDict[entry["guid"]] = {'name': entry["name"], 'icon': entry["abilityIcon"]}
    return spellDict

def get_total_data(URL):
    code, fight, dType, source = parse_warcraft_logs_url(URL).values()
    response = get_data(query, code=code, sourceID=source, fight=fight)
    startTime = response.get("data", {}).get("reportData", {}).get("report", {}).get("fights", [{}])[0].get("startTime")
    endTime = response.get("data", {}).get("reportData", {}).get("report", {}).get("fights", [{}])[0].get("endTime")
    graph_response = get_data(graph_query, code=code, sourceID=source, fight=fight, dtype= dType, startTime=startTime, endTime=endTime)
    print(startTime, endTime)
    graphData = graph_response.get("data", {}).get("reportData", {}).get("report", {}).get("graph", {})
    timeLength = endTime - startTime
    series = graphData['data']['series']
    totalData = next((item for item in series if item['name'] == 'Total'), None)
    castEvent = response.get("data", {}).get("reportData", {}).get("report", {}).get("casts", {}).get("data", {})
    buffEvent = response.get("data", {}).get("reportData", {}).get("report", {}).get("buffs", {}).get("data", {})
    castTable = response.get("data", {}).get("reportData", {}).get("report", {}).get("cast_table", {}).get("data", [])
    buffTable = response.get("data", {}).get("reportData", {}).get("report", {}).get("buff_table", {}).get("data", [])
    return totalData, dType,timeLength, castEvent, buffEvent, castTable, buffTable, startTime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare_data', methods=['POST'])
def compare_data():
    MyURL = request.form.get('MyURL')
    OtherURL = request.form.get('OtherURL')
    MyData, dType, MyTimeLength, MyCastEvent, MyBuffEvent, MyCastTable, MyBuffTable, MyStartTime = get_total_data(MyURL)
    OtherData, _, OtherTimeLength, OtherCastEvent, OtherBuffEvent, OtherCastTable, OtherBuffTable, OtherStartTime = get_total_data(OtherURL)
    if(MyTimeLength > OtherTimeLength):
        TimeLength = MyTimeLength
    else:
        TimeLength = OtherTimeLength
    spellDict = {}
    spellDict = make_icon_spell_dict(MyCastTable, spellDict, "cast")
    spellDict = make_icon_spell_dict(MyBuffTable, spellDict, "buff")
    spellDict = make_icon_spell_dict(OtherCastTable, spellDict, "cast")
    spellDict = make_icon_spell_dict(OtherBuffTable, spellDict, "buff")
    return render_template('compare_data.html', MyGraphData = MyData, OtherGraphData = OtherData, dType = dType, TimeLength = TimeLength,
                           MyCastEvent = MyCastEvent, MyBuffEvent = MyBuffEvent, OtherCastEvent = OtherCastEvent, OtherBuffEvent = OtherBuffEvent, 
                           spellDict = spellDict, MyStartTime = MyStartTime, OtherStartTime = OtherStartTime)

if __name__ == '__main__':
    '''
    URL = "https://www.warcraftlogs.com/reports/JAjWZM1xHPyVd8g9#fight=6&type=healing&source=18"
    code, fight, dtype, source = parse_warcraft_logs_url(URL).values()
    response = get_data(query, code=code, sourceID=source, fight=fight)
    healEvent = response.get("data", {}).get("reportData", {}).get("report", {}).get("heal", {}).get("data", {})
    startTime = response.get("data", {}).get("reportData", {}).get("report", {}).get("fights", [{}])[0].get("startTime")
    endTime = response.get("data", {}).get("reportData", {}).get("report", {}).get("fights", [{}])[0].get("endTime")
    healTable = response.get("data", {}).get("reportData", {}).get("report", {}).get("heal_table", {}).get("data", [])
    castEvent = response.get("data", {}).get("reportData", {}).get("report", {}).get("casts", {}).get("data", {})
    castTable = response.get("data", {}).get("reportData", {}).get("report", {}).get("cast_table", {}).get("data", [])
    graph_response = get_data(graph_query, code=code, sourceID=source, fight=fight, dtype= dtype, startTime=startTime, endTime=endTime)
    graphData = graph_response.get("data", {}).get("reportData", {}).get("report", {}).get("graph", {})
    series = graphData['data']['series']
    totalData = next((item for item in series if item['name'] == 'Total'), None)
    print(castEvent)
    '''
    
    app.run(debug=True)