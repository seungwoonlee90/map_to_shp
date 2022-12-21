import os
import time
import simplejson
import json
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import traceback
import geopandas as gpd


def main(O: str, D:str, TIME=5):
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get('###') #URL을 변경해주세요
    
    # find OD
    try:
        o_el = WebDriverWait(driver, TIME).until(
            EC.presence_of_element_located((By.ID, "directionStart0"))
            )
        o_el.send_keys(O)
        o_el.send_keys(Keys.ENTER)
        time.sleep(2)
        
        d_el = WebDriverWait(driver, TIME).until(
            EC.presence_of_element_located((By.ID, "directionGoal1"))
            )
        d_el.send_keys(D)
        d_el.send_keys(Keys.ENTER)
        time.sleep(1)
        
        driver.find_element(By.XPATH, "//directions-search/div[@class='btn_box']/button[2]").click()
        time.sleep(2)
        
        logs = driver.execute_script(
            "var performance = window.performance || window.mozPerformance || window.msPerformance || window.webketPerformance || {}; var network = performance.getEntries() || {}; return network;"
        )
        
        for log in logs :
            if "name" in log :
                if log["name"].find("/transit/directions") > -1 :
                    url = log["name"]
        
        res = requests.get(url)
        res = res.json()["paths"][0]
        route = {"type": "FeatureCollection", "features": []}
        def CollectRoute(json) -> simplejson :
            if len(json['legs'][0]['steps']) > 1:
                for i in range(len(json['legs'][0]['steps'])) :
                    features = {"type": "Feature", "geometry": {"type":"LineString",
                                                                "coordinates" : [[round(float(j['x']), 4), round(float(j['y']), 4)] for j in json['legs'][0]['steps'][i]["points"]]},
                                "properties": {
                                "total_duration": json['duration'],
                                "total_distance": json['distance'],
                                "fare": json['fare'],
                                "type": json['legs'][0]['steps'][i]['type'],
                                "type_distance": json['legs'][0]['steps'][i]['distance'],
                                "type_duration": json['legs'][0]['steps'][i]['duration'],
                                }}
                    route['features'].append(features)
            return route
        
        lines = CollectRoute(res)
        os.makedirs('./result', exist_ok=True)
        with open(f"./result/{O}_{D}_routes.geojson", 'w') as f :
            json.dump(lines, f)
        shp_lines = gpd.GeoDataFrame.from_features(lines).set_crs('epsg:4326')
        shp_lines.to_file(f'./result/{O}_{D}_routes.shp')
        time.sleep(2)
        driver.quit()
        
    except Exception as e:
        def ErrorLog(error: str):
            current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
            with open("Log.txt", "a") as f:
                f.write(f"[{current_time}] - {error}\n")
        err = traceback.format_exc()
        ErrorLog(str(err))
        driver.quit()
        
if __name__ == "__main__" :
    ods = [["###", "###"],
            ["###", "###"]]

    for od in ods :
        main(O=od[0], D=od[1])
        time.sleep(2)