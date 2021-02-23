import datetime
import os
import csv
import configparser
import pandas as pd
import requests
import logging
import subprocess
from nature_remo import GetRemoData

#グローバル変数
global masterdate

######Nature Remoのデータ取得######
def getdata_remo(device, csvpath):
    #センサデータ値が得られないとき、最大device.Retry回スキャンを繰り返す
    for i in range(device.Retry):
        try:
            sensorValue = GetRemoData().get_sensor_data(device.Token, device.API_URL)
        #エラー出たらログ出力
        except:
            logging.warning(f'retry to get data [loop{str(i)}, date{str(masterdate)}, device{device.DeviceName}, sensor]')
            sensorValue = None
            continue
        else:
            break
    #エアコンデータ値が得られないとき、最大device.Retry回スキャンを繰り返す
    for i in range(device.Retry):
        try:
            airconValue = GetRemoData().get_aircon_data(device.Token, device.API_URL)
        #エラー出たらログ出力
        except:
            logging.warning(f'retry to get data [loop{str(i)}, date{str(masterdate)}, device{device.DeviceName}, aircon]')
            sensorValue = None
            continue
        else:
            break


######データのCSV出力######
def output_csv(data, csvpath):
    dvname = data['DeviceName']
    monthstr = masterdate.strftime('%Y%m')
    #出力先フォルダ名
    outdir = f'{csvpath}/{dvname}/{masterdate.year}'
    #出力先フォルダが存在しないとき、新規作成
    os.makedirs(outdir, exist_ok=True)
    #出力ファイルのパス
    outpath = f'{outdir}/{dvname}_{monthstr}.csv'

    #出力ファイル存在しないとき、新たに作成
    if not os.path.exists(outpath):        
        with open(outpath, 'w') as f:
            writer = csv.DictWriter(f, data.keys())
            writer.writeheader()
            writer.writerow(data)
    #出力ファイル存在するとき、1行追加
    else:
        with open(outpath, 'a') as f:
            writer = csv.DictWriter(f, data.keys())
            writer.writerow(data)


######メイン######
if __name__ == '__main__':    
    #開始時刻を取得
    masterdate = datetime.date.today()
    #開始時刻を分単位で丸める
    masterdate = startdate.replace(second=0, microsecond=0)   
    if startdate.second >= 30:
        masterdate += timedelta(minutes=1)

    #設定ファイルとデバイスリスト読込
    cfg = configparser.ConfigParser()
    cfg.read('./config.ini', encoding='utf-8')
    df_devicelist = pd.read_csv('./DeviceList.csv')
    #全センサ数とデータ取得成功数
    sensor_num = len(df_devicelist)
    success_num = 0

    #ログの初期化
    logname = f"/sensorlog_{str(masterdate.strftime('%y%m%d'))}.log"
    logging.basicConfig(filename=cfg['Path']['LogOutput'] + logname, level=logging.INFO)

    #取得した全データ保持用dict
    all_values_dict = None

    ######デバイスごとにデータ取得######
    for device in df_devicelist.itertuples():
        #remo
        if device.SensorType == 'Nature_Remo':
            data = getdata_remo(device, cfg['Path']['CSVOutput'])
        #上記以外
        else:
            data = None        

        #データが存在するとき、全データ保持用Dictに追加し、CSV出力
        if data is not None:
            #all_values_dictがNoneのとき、新たに辞書を作成
            if all_values_dict is None:
                all_values_dict = {data['DeviceName']: data}
            #all_values_dictがNoneでないとき、既存の辞書に追加
            else:
                all_values_dict[data['DeviceName']] = data

            #CSV出力
            output_csv(data, cfg['Path']['CSVOutput'])
            #成功数プラス
            success_num+=1

    ######Googleスプレッドシートにアップロードする処理######
#    output_spreadsheet(all_values_dict)

    #処理終了をログ出力
    logging.info(f'[masterdate{str(masterdate)} startdate{str(startdate)} enddate{str(datetime.date.today())} success{str(success_num)}/{str(sensor_num)}]')