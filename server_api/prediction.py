import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from sklearn.preprocessing import StandardScaler
import ast
import folium
from shapely.geometry import Point, Polygon
import shapely.wkt
import geopandas as gpd


class SocialRecommend():
    # Пути к файлам
    PATH_FISHNET_GEO = './data/fishnet_data_geo.csv'
    PATH_FISHNET = './data/fishnet_data_nogeo.csv'
    PATH_MATERS_GEO = './data/maters_data_geo.csv'
    PATH_MATERS = './data/maters_data_nogeo.csv'
    def __init__(self):
        self.load_data()

    def load_data(self):
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

    def get_normalization_data(self):
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
        raise('Not Implemented')

    def calculate_dist(self,cell_data,maters):
        for _, row in maters.iterrows():
            min_dist = 10000
            mater_data = np.array(row.values)
            dist =  np.linalg.norm(cell_data - mater_data)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def get_data(self,row,index):
        new_row = self.fishnet_base_geo.iloc[index]
        cell_zid = new_row.cell_zid
        if cell_zid not in self.maters_cells:
            building_type = 'cell'
        else:
            building_type = 'mater'
        geo = new_row.geometry
        return cell_zid, building_type, geo


    def predict(self, migration):
        # Просчитывает метрику по всем ячейкам из fishnet по maters (родильные дома)
        # Возвращаем файл html с построенной картой
        predictions = []
        if migration == '0':
            fishnet, maters = self.get_normalization_data()
            for index,row in fishnet.iterrows():
                row_data = np.array(row.values)
                pred = self.calculate_dist(row_data,maters)
                #preds_list.append(pred)
                cell, building_type, geo = self.get_data(row,index)
                #data = {'cell_zid': int(cell),'type':building_type,'geometry':geo,'prediction':float(pred)}
                predictions.append([pred,index])
        else:
            raise('Not Implemented')
        map = self.build_map(predictions)
        map.save(outfile='./templates/map.html')
        string_map = open('./templates/map.html','r').read()
        return string_map

    @staticmethod
    def nearest_hosp(x):
        if x <= 3:
            return 1
        return 0

    @staticmethod
    def nearest_mater(x):
        if x <= 4:
            return 1
        return 0

    def build_map(self,preds):
        # строим карту с окрашенными квадратами
        # Зелёный - рекомендовано, жёлтый - 50/50, красный - не рекомендовано
        # avg_mater_dist - среднее минимальное расстояние от роддомов друг к другу
        m_f = folium.Map(location=[55.7252, 37.6290], zoom_start=10, tiles='CartoDB positron')
        avg_mater_dist = 0.9079748864515159
        for item in preds:
            data = self.fishnet_base_geo.loc[item[1]]
            data_geo = data.geometry
            if item[1] in self.maters_cells:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'blue', 'weight': 0.05,
                                                                 'fillOpacity': 0.2})
                #geo_data = 'cellzid: {}, coef: {}'.format(item[1], item[0])
                #folium.Popup(geo_data).add_to(geo_j)
            elif item[0] < 1.5 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'green', 'weight': 0.05,
                                                                 'fillOpacity': 0.2})
                folium.Popup(item[0]).add_to(geo_j)
            elif item[0] < 3 * avg_mater_dist:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'orange', 'weight': 0.05,
                                                                 'fillOpacity': 0.2})
                folium.Popup(item[0]).add_to(geo_j)
            else:
                sim_geo = gpd.GeoSeries(data_geo).simplify(tolerance=0.001)
                geo_j = sim_geo.to_json()
                geo_j = folium.GeoJson(data=geo_j,
                                       style_function=lambda x: {'fillColor': 'red', 'weight': 0.05,
                                                                 'fillOpacity': 0.2})
                folium.Popup(item[0]).add_to(geo_j)
            geo_j.add_to(m_f)
        return m_f
#a = SocialRecommend()
#print(a.predict('0'))