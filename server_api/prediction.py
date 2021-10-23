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

    def get_normalization_data(self) -> Tuple[Any, Any]:
        # Нормализует данные, кроме категориальных.
        # Возвращает 2 нормализованных DataFrame объекта. Информация по всем зонам и по роддомам
        # Нормализация происходит объектом StandartScaler из пакета sklearn, модуля preprocessing
        fishnet = self.fishnet_base.drop(['nearest_mater', 'nearest_hosp'], axis=1)
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

    def migration_calc(self):
        # Перерасчитывает данные self.maters_base и self.fishnet_base с учётом миграции.
        # Нормализовать только после пересчёта миграции.
        raise NotImplementedError

    def calculate_dist(self, cell_data, maters) -> Optional[int]:
        min_dist = None
        for _, row in maters.iterrows():
            min_dist = 10000
            mater_data = np.array(row.values)
            dist = np.linalg.norm(cell_data - mater_data)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def predict(self, migration) -> str:
        # Просчитывает метрику по всем ячейкам из fishnet по maters (родильные дома)
        # Возвращаем файл html с построенной картой
        if migration != '0':
            raise NotImplementedError
        predictions = []
        fishnet, maters = self.get_normalization_data()
        for index, row in fishnet.iterrows():
            row_data = np.array(row.values)
            pred = self.calculate_dist(row_data, maters)
            predictions.append([pred, index])
        built_map = self.build_map(predictions)
        built_map.save(outfile=self.MAP_HTML)
        string_map = open(self.MAP_HTML, 'r').read()
        return string_map

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
            data = self.fishnet_base_geo.loc[item[1]]
            data_geo = data.geometry
            if item[1] in self.maters_cells:
                html = """
                    В данной области уже построен роддом Номер ячейки: {}
                    """.format(item[1])
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'blue', 'weight': 0.05,
                                                                 'fillOpacity': 0.2})
                geo_data = 'В данной области уже построен роддом<br>Номер области: {}<br>'.format(item[1])
                folium.Popup(geo_data, min_width=250, max_width=250).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 1.5 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'red', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Рекомендуем данную область для постройки<br>Номер области {}'.format(item[1])
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>'
                folium.Popup(geo_data, min_width=250, max_width=280).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 2.5 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': '#FF5500', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Данную область можно считать неплохой для постройки<br>Номер области: {}'.format(item[1])
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>'
                folium.Popup(geo_data, min_width=250, max_width=320).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 3 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'orange', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Слабо рекомендуем данную область для постройки<br>Номер области: {}'.format(item[1])
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>'
                folium.Popup(geo_data, min_width=250, max_width=300).add_to(geo_j)
                geo_j.add_to(m_f)
            elif item[0] < 4.5 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': '#C8FE2E', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Не рекомендуем данную область для постройки<br>Номер области: {}'.format(item[1])
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>'
                folium.Popup(geo_data, min_width=250, max_width=280).add_to(geo_j)
                geo_j.add_to(m_f)
            else:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'green', 'weight': 0.05,
                                                                 'fillOpacity': 0.3})
                geo_data = 'Крайне не рекомендуем данную область для постройки<br>Номер области: {}'.format(item[1])
                geo_data += '<br>Коэффициент миграционного прироста<br> <input name="cell_param" type="number" value="1"' \
                            'min="0" max="100" style="width: 5em"/>'
                folium.Popup(geo_data, min_width=250, max_width=320).add_to(geo_j)
                geo_j.add_to(m_f)
        colormap = cm.LinearColormap(colors=['green','#C8FE2E','orange','red', '#FF5500'],
                                     index=[0, 0.25, 0.5, 0.75, 1], vmin=0, vmax=1)
        colormap.caption = 'Целесообразность постройки объекта'
        colormap.add_to(m_f)
        return m_f
