from typing import Optional, Tuple, Any

import branca.colormap as cm
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.wkt
from sklearn.preprocessing import StandardScaler


class SocialRecommend:
    # Пути к файлам
    PATH_FISHNET_GEO = './data/fishnet_data_geo.csv'
    PATH_FISHNET = './data/fishnet_data_nogeo.csv'
    PATH_MATERS_GEO = './data/maters_data_geo.csv'
    PATH_MATERS = './data/maters_data_nogeo.csv'
    MAP_HTML = './templates/map.html'

    def __init__(self):
        self._load_data_()

    def _load_data_(self):
        # Читаем базовые файлы
        self.fishnet_base = pd.read_csv(self.PATH_FISHNET)
        self.fishnet_base_geo = pd.read_csv(self.PATH_FISHNET_GEO)
        self.fishnet_base_geo['geometry'] = self.fishnet_base_geo['geometry'].apply(lambda x: shapely.wkt.loads(x))
        self.maters_base = pd.read_csv(self.PATH_MATERS)
        self.maters_base_geo = pd.read_csv(self.PATH_MATERS_GEO)
        self.maters_base_geo['geometry'] = self.maters_base_geo['geometry'].apply(lambda x: shapely.wkt.loads(x))
        self.maters_cells = []
        for _, r in self.maters_base_geo.iterrows():
            cell = self.fishnet_base_geo[self.fishnet_base_geo['cell_zid'] == r.nearest_cell_zid].index[0]
            self.maters_cells.append(cell)

    def recount_data(self, new_cell_value) -> Tuple[Any, Any]:
        fishnet = self.fishnet_base.copy().drop(['nearest_mater', 'nearest_hosp'], axis=1)
        for cell_id in new_cell_value:
            fishnet.iloc[int(cell_id)] = fishnet.iloc[int(cell_id)].apply(
                lambda x: x * int(new_cell_value[cell_id]["value"]))
        fishnet['nearest_mater'] = self.fishnet_base['nearest_mater']
        fishnet['nearest_hosp'] = self.fishnet_base['nearest_hosp']
        return fishnet

    def get_normalization_data(self, fishnet) -> Tuple[Any, Any]:
        # Нормализует данные, кроме категориальных.
        # Возвращает 2 нормализованных DataFrame объекта. Информация по всем зонам и по роддомам
        # Нормализация происходит объектом StandartScaler из пакета sklearn, модуля preprocessing
        fishnet = fishnet.drop(['nearest_mater', 'nearest_hosp'], axis=1)
        maters = self.maters_base.drop(['nearest_mater', 'nearest_hosp'], axis=1)
        # create a scaler object
        std_scaler = StandardScaler()
        # fit and transform the data
        fishnet_std = pd.DataFrame(std_scaler.fit_transform(fishnet), columns=fishnet.columns)
        maters_std = pd.DataFrame(std_scaler.transform(maters), columns=maters.columns)
        maters_std['nearest_mater'] = self.maters_base.nearest_mater.apply(lambda x: self.nearest_mater(x))
        maters_std['nearest_hosp'] = self.maters_base.nearest_mater.apply(lambda x: self.nearest_hosp(x))
        fishnet_std['nearest_mater'] = self.fishnet_base.nearest_mater.apply(lambda x: self.nearest_mater(x))
        fishnet_std['nearest_hosp'] = self.fishnet_base.nearest_mater.apply(lambda x: self.nearest_hosp(x))
        return fishnet_std, maters_std

    def calculate_dist(self, cell_data, maters) -> Optional[int]:
        min_dist = None
        for _, row in maters.iterrows():
            min_dist = 10000
            mater_data = np.array(row.values)
            dist = np.linalg.norm(cell_data - mater_data)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def predict(self, new_cell_data: dict = {}) -> int:
        # Просчитывает метрику по всем ячейкам из fishnet по maters (родильные дома)
        # Возвращаем файл html с построенной картой
        if len(new_cell_data) > 0:
            fishnet = self.recount_data(new_cell_data)
            fishnet, maters = self.get_normalization_data(fishnet)
        else:
            fishnet, maters = self.get_normalization_data(self.fishnet_base)
        predictions = []
        for index, row in fishnet.iterrows():
            row_data = np.array(row.values)
            pred = self.calculate_dist(row_data, maters)
            predictions.append([pred, index])
        built_map = self.build_map(predictions)
        built_map.save(outfile=self.MAP_HTML)
        return open(self.MAP_HTML, 'a').write("""
        <script>
            function saveCellData(element) {
                console.log(312)
                let id = element.className
                let value = element.parentNode.children[3].value
                let cookies = document.cookie.split(";")
                let js_raw = null  
                for (index in cookies) {
                    if (cookies[index].indexOf("app_cookies=") >= 0){
                        let cookie = cookies[index]
                        js_raw = cookie.slice(cookie.indexOf("app_cookies=") + "app_cookies=".length)
                        break
                    }
                }
                let cookie_object = {}
                if (js_raw) {
                    cookie_object = JSON.parse(js_raw)
                }
                cookie_object[id] = {"value": value}
                document.cookie = "app_cookies=" + JSON.stringify(cookie_object) + ";"
            }
        </script>
        """)

    @staticmethod
    def nearest_hosp(x) -> int:
        if x <= 3:
            return 1
        return 0

    @staticmethod
    def nearest_mater(x) -> int:
        if x <= 4:
            return 1
        return 0

    def build_map(self, preds):
        # строим карту с окрашенными квадратами
        # Зелёный - рекомендовано, жёлтый - 50/50, красный - не рекомендовано
        # avg_mater_dist - среднее минимальное расстояние от роддомов друг к другу
        m_f = folium.Map(location=[55.7252, 37.6290], zoom_start=10, tiles='CartoDB positron')
        avg_mater_dist = 0.9079748864515159
        for item in preds:
            square_id = item[1]
            js_button_code = f'<button class="{square_id}" type="button" onclick="saveCellData(this);">Сохранить</button>'
            data = self.fishnet_base_geo.loc[square_id]
            data_geo = data.geometry
            if square_id in self.maters_cells:
                html = """
                    В данной области уже построен роддом Номер ячейки: {}
                    """.format(square_id)
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'blue', 'weight': 0.05,
                                                                 'fillOpacity': 0.2})
                geo_data = 'В данной области уже построен роддом<br>Номер области: {}<br>'.format(square_id)
                folium.Popup(geo_data, min_width=250, max_width=250).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 1.5 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'red', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Рекомендуем данную область для постройки<br>Номер области {}'.format(square_id)
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>' + js_button_code
                folium.Popup(geo_data, min_width=250, max_width=280).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 2.5 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': '#FF5500', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Данную область можно считать неплохой для постройки<br>Номер области: {}'.format(square_id)
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>' + js_button_code
                folium.Popup(geo_data, min_width=250, max_width=320).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 3 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'orange', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Слабо рекомендуем данную область для постройки<br>Номер области: {}'.format(square_id)
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>' + js_button_code
                folium.Popup(geo_data, min_width=250, max_width=300).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 4.5 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': '#C8FE2E', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Не рекомендуем данную область для постройки<br>Номер области: {}'.format(square_id)
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>' + js_button_code
                folium.Popup(geo_data, min_width=250, max_width=280).add_to(geo_j)
                geo_j.add_to(m_f)
            else:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'green', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Крайне не рекомендуем данную область для постройки<br>Номер области: {}'.format(square_id)
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>' + js_button_code
                folium.Popup(geo_data, min_width=250, max_width=320).add_to(geo_j)
                geo_j.add_to(m_f)
        colormap = cm.LinearColormap(colors=['green', '#C8FE2E', 'orange', 'red', '#FF5500'],
                                     index=[0, 0.25, 0.5, 0.75, 1], vmin=0, vmax=1)
        colormap.caption = 'Целесообразность постройки объекта'
        colormap.add_to(m_f)
        return m_f
