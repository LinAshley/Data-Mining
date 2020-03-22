import pandas
import numpy as np

#查看并理解数据
files = ["ap_2010.csv", "class_size.csv", "demographics.csv", "graduation.csv", "hs_directory.csv", "math_test_results.csv", "sat_results.csv"]
data = {}
for f in files:
    d = pandas.read_csv("schools/{0}".format(f))
    data[f.replace(".csv", "")] = d

for k,v in data.items():
    print("\n" + k + "\n")
    print(v.head())
    
#合并数据集
data["demographics"]["DBN"].head()
data["class_size"].head()
data["class_size"]["DBN"] = data["class_size"].apply(lambda x: "{0:02d}{1}".format(x["CSD"], x["SCHOOL CODE"]), axis=1)
data["hs_directory"]["DBN"] = data["hs_directory"]["dbn"]

survey1=pandas.read_csv("schools/survey_all.txt",delimiter="\t",encoding='windows-1252')
survey2=pandas.read_csv("schools/survey_d75.txt",delimiter="\t",encoding='windows-1252')
survey1["d75"]=False
survey2["d75"]=True
survey=pandas.concat([survey1,survey2],axis=0)

survey.head()
#目前的数据属性过多


#把多余的属性去掉,整合进数据框data
survey["DBN"]=survey["dbn"]
survey_fields=["DBN","rr_s","rr_t","rr_p", "N_s", "N_t", "N_p", "saf_p_11", "com_p_11", "eng_p_11", "aca_p_11", "saf_t_11", "com_t_11", "eng_t_10", "aca_t_11", "saf_s_11", "com_s_11", "eng_s_11", "aca_s_11", "saf_tot_11", "com_tot_11", "eng_tot_11", "aca_tot_11",]
survey=survey.loc[:,survey_fields]
data["survey"]=survey
survey.shape


#压缩数据集
#观察每个数据集我们可以发现比如sat_results中每个学校的数据为一行，但是在class_size中每个学校的数据却有多行
class_size=data["class_size"]
class_size=class_size[class_size["GRADE"]=="09-12"]
class_size=class_size[class_size["PROGRAM TYPE"]=="GEN ED"]
class_size=class_size.groupby("DBN").agg(np.mean)
class_size.reset_index(inplace=True)#在所有的索引列重置索引
data["class_size"]=class_size


#接下来压缩demographics数据集，该数据集记录了每个学校多年的数据，我们选择最近的年份
demographics=data["demographics"]
demographics=demographics[demographics["schoolyear"]==20112012]
data["demographics"]=demographics

#压缩math_test_result数据集
data["math_test_results"]=data["math_test_results"][data["math_test_results"]["Year"]==2011]
data["math_test_results"] = data["math_test_results"][data["math_test_results"]["Grade"] == '8']

#graduation
data["graduation"]=data["graduation"][data["graduation"]["Cohort"]=="2006"]
data["graduation"]=data["graduation"][data["graduation"]["Demographic"]=="Total Cohort"]


#计算变量
#计算total SAT score
cols=['SAT Math Avg. Score','SAT Critical Reading Avg. Score','SAT Writing Avg. Score']
for c in cols:
    data["sat_results"][c]=data["sat_results"][c].convert_objects(convert_numeric=True)
    
data['sat_results']['sat_score']=data['sat_results'][cols[0]]+data['sat_result'][cols[1]]+data['sat_result'][cols[2]]
    
#接下来，把经纬度变换为数字
data["hs_directory"]['lat'] = data["hs_directory"]['Location 1'].apply(lambda x: x.split("\n")[-1].replace("(", "").replace(")", "").split(", ")[0])
data["hs_directory"]['lon'] = data["hs_directory"]['Location 1'].apply(lambda x: x.split("\n")[-1].replace("(", "").replace(")", "").split(", ")[1])
for c in ['lat', 'lon']:
    data["hs_directory"][c] = data["hs_directory"][c].convert_objects(convert_numeric=True)

#现在，打印看看数据集中的数据
for k,v in data.items():
    print(k)
    print(v.head())
    


#现在，我们已经完成了初步的数据整理工作
#接下来，将整合数据集
    
#当然，这些数据集中有缺失数据，我们采用外连接的方式确保不丢失数据
flat_data_names=[k for k,v in data.items()]
flat_data=[data[k] for k in flat_data_names]
full=flat_data[0]
for i,f in enumerate(flat_data[1:]):
    name=flat_data_names[i+1]
    print(name)
    print(len(f["DBN"])-len(f['DBN'].unique()))
    join_type="inner"
    if name in ['sat_results','ap_2010','graduation']:
        join_type='outer'
    if name not in ['math_test_results']:
        full=full.merge(f,on="DBN",how=join_type)
full.shape

#填补缺失值
#我们想要分析 Advanced Placement exam results 和 SAT scores直接的关系
#首先要把他们的类型全部转换为数字
cols=['AP Test Takers','Total Exams Taken','Number of Exams with scores 3 4 or 5']
for col in cols:
    full[col]=full[col].convert_objects(convert_numeric=True)
full[cols]=full[cols].fillna(value=0)
#接下来，我们计算学校所属的区域，以便绘图
full["school_dist"]=full["DBN"].apply(lambda x:x[:2])
#最后，我们要用均值填充所有缺失值
full=full.fillna(full.mean())

#计算相关系数
full.corr()['sat_score']
#从结果中分析得出相关性高的因素，每一个都是一个讲诉数据的角度



#营造语境
#一个好的方式是通过图表展现，让读者明白我们讨论的问题
import folium
from folium import plugins
schools_map=folium.Map(location=[full['lat'].mean(),full['lon'].mean()],zoom_start=10)
marker_cluster=folium.MarkerCluster().add_to(schools_map)
for name,row in full.iterrows():
    folium.Marker([row['lat'],row['lon']],popup="{0}:{1}".format(row['DBN'],row['school_name'])).add_to(marker_cluster)
schools_map.create_map('school.html')
schools_map

#上面绘制的地图有帮助，但是我们很难发现热门区域，我们将绘制如下的热度地图
schools_heatmap=folium.Map(location=[full['lat'].mean(),full['lon'].mean()],zoom_start=10)
schools_heatmap.add_children(plugins.HeatMap([[row['lat'],row['lon']] for name,row in full.iterrows()]))
schools_heatmap.save('heatmap.html')
schools_heatmap

#各个校区的分数分布地图
district_data=full.groupby('school_dist').agg(np.mean)
district_data.reset_index(inplace=True)
district_data['school_dist']=district_data['school_dist'].apply(lambda x:str(int(x)))
#现在我们读入GeoJSON从而确定每个校区的形状大小，并绘图
def show_district_map(col):
    geo_path='schools/districts.geojson'
    districts=folium.Map(location=[full['lat'].mean(),full['lon'].mean()],zoom_start=10)
    districts.geo_json(
            geo_path=geo_path,
            data=district_data,
            columns=['school_dist',col],
            key_on='feature.properties.school_dist',
            fill_color='YlGn',
            fill_opacity=0.7,
            line_opacity=0.2,
            )
    districts.save('districts.html')
    return districts
show_district_map('sat_score')




