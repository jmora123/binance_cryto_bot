#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 07:31:10 2022

@author: user
"""

import requests
import asyncio
from binance import Client, AsyncClient, BinanceSocketManager
import time
from datetime import datetime as dt
import numpy as np
import math
import os.path
import json
from binance.exceptions import BinanceAPIException


def get_updated_rsi(last_closing_price, current_closing_price,
                    last_avg_gain, last_avg_loss):

    candles_closings = np.concatenate([last_closing_price,
                                       current_closing_price.reshape(-1)])

    # Inicializar vectores
    diffs = np.zeros(len(current_closing_price), dtype=np.float64)
    diffs_pos = np.zeros(len(current_closing_price), dtype=np.float64)
    diffs_neg = np.zeros(len(current_closing_price), dtype=np.float64)

    avg_gain = np.zeros(len(candles_closings), dtype=np.float64)


    # print('¡¡¡¡¡AQUI!!!!!')
    # print(avg_gain)


    avg_loss = np.zeros(len(candles_closings), dtype=np.float64)
    RS = np.zeros(len(current_closing_price), dtype=np.float64)
    RSI = np.zeros(len(current_closing_price), dtype=np.float64)

    # Obtener los vectores de ganancias y pérdidas
    for i in range(1, len(candles_closings)):
        diffs[i - 1] = candles_closings[i] - candles_closings[i - 1]

        if diffs[i - 1] > 0:
            diffs_pos[i - 1] = diffs[i - 1]

        else:
            diffs_neg[i - 1] = np.absolute(diffs[i - 1])

    # Calcular el promedio inicial de ganancias y pérdidas
    # con la media móvil simple (SMA)
    avg_gain[0] = last_avg_gain
    avg_loss[0] = last_avg_loss

    # RS[0] = avg_gain[0] / avg_loss[0]
    # RSI[0] = 100 - (100 / (1 + RS[0]))


    # Calcular el resto de promedios de ganancias y pérdidas
    # con las medias móviles modificadas (MMA)
    for i in range(1, len(candles_closings)):
        
        avg_gain[i] = ((avg_gain[i - 1] * 13) + diffs_pos[i - 1]) / 14
        avg_loss[i] = ((avg_loss[i - 1] * 13) + diffs_neg[i - 1]) / 14

        RS[i - 1] = avg_gain[i] / avg_loss[i]

        RSI[i - 1] = 100 - (100 / (1 + RS[i - 1]))

    last_avg_gain = avg_gain[-1]
    last_avg_loss = avg_loss[-1]

    return [last_avg_gain, last_avg_loss, RSI]


def get_updated_rsi2(pairs, cycles_diff, np_total_data,
                     np_total_data_update, RSI_data):

    RSI_data_update = {}

    # Inicializar vectores
    diffs = np.zeros(cycles_diff, dtype=np.float64)
    diffs_pos = np.zeros(cycles_diff, dtype=np.float64)
    diffs_neg = np.zeros(cycles_diff, dtype=np.float64)
    avg_gain = np.zeros(cycles_diff + 1, dtype=np.float64)
    avg_loss = np.zeros(cycles_diff + 1, dtype=np.float64)
    RS = np.zeros(cycles_diff, dtype=np.float64)
    RSI = np.zeros(cycles_diff, dtype=np.float64)

    for pair in pairs:
        last_closing_price = np_total_data[pair][-1, [4]]
        current_closing_price = np_total_data_update[pair][:, [4]]
        # last_closing_price = np_total_data[pair]
        # current_closing_price = np_total_data_update[pair][:, [4]]
        last_avg_gain = RSI_data[pair][0]
        last_avg_loss = RSI_data[pair][1]

        candles_closings = np.concatenate([last_closing_price,
                                           current_closing_price.reshape(-1)])
        # candles_closings = np.concatenate([last_closing_price,
        # current_closing_price.reshape(-1)])

        # Obtener los vectores de ganancias y pérdidas
        for i in range(1, cycles_diff + 1):
            diffs[i - 1] = candles_closings[i] - candles_closings[i - 1]
    
            if diffs[i - 1] > 0:
                diffs_pos[i - 1] = diffs[i - 1]
    
            else:
                diffs_neg[i - 1] = np.absolute(diffs[i - 1])
    
        # Calcular el promedio inicial de ganancias y pérdidas
        # con la media móvil simple (SMA)
        avg_gain[0] = last_avg_gain
        avg_loss[0] = last_avg_loss
    
        # Calcular el resto de promedios de ganancias y pérdidas
        # con las medias móviles modificadas (MMA)
        for i in range(1, cycles_diff + 1):
            
            avg_gain[i] = ((avg_gain[i - 1] * 13) + diffs_pos[i - 1]) / 14
            avg_loss[i] = ((avg_loss[i - 1] * 13) + diffs_neg[i - 1]) / 14
    
            RS[i - 1] = avg_gain[i] / avg_loss[i]
    
            RSI[i - 1] = 100 - (100 / (1 + RS[i - 1]))
    
        last_avg_gain = avg_gain[-1]
        last_avg_loss = avg_loss[-1]

        RSI_data_update[pair] = [last_avg_gain, last_avg_loss, RSI]

    return RSI_data_update


def get_updated_rsi_live(last_closing_price, current_closing_price, RSI_data):

    # Inicializar vectores
    diffs_pos = 0
    diffs_neg = 0
    avg_gain = np.zeros(1 + 1, dtype=np.float64)
    avg_loss = np.zeros(1 + 1, dtype=np.float64)

    last_avg_gain = RSI_data[0]
    last_avg_loss = RSI_data[1]

    candles_closings = np.concatenate([last_closing_price,
                                       current_closing_price])

    # Obtener los vectores de ganancias y pérdidas
    diffs = candles_closings[1] - candles_closings[0]

    if diffs > 0:
        diffs_pos = diffs

    else:
        diffs_neg = np.absolute(diffs)

    # Calcular el promedio inicial de ganancias y pérdidas
    # con la media móvil simple (SMA)
    avg_gain[0] = last_avg_gain
    avg_loss[0] = last_avg_loss

    # Calcular el resto de promedios de ganancias y pérdidas
    # con las medias móviles modificadas (MMA)
    avg_gain[1] = ((avg_gain[0] * 13) + diffs_pos) / 14
    avg_loss[1] = ((avg_loss[0] * 13) + diffs_neg) / 14

    RS = avg_gain[1] / avg_loss[1]

    RSI = 100 - (100 / (1 + RS))

    # last_avg_gain = avg_gain[-1]
    # last_avg_loss = avg_loss[-1]

    # RSI_data_update = [last_avg_gain, last_avg_loss, RSI]

    # print('RS: ', RS)
    # print('RSI: ', RSI)
    # print('RSI_data_update: ', RSI_data_update)

    # return RSI_data_update
    return RSI


def get_initial_rsi(candles_closings):
    
    # Inicializar vectores
    diffs = np.zeros(len(candles_closings) - 1, dtype=np.float64)
    diffs_pos = np.zeros(len(candles_closings) - 1, dtype=np.float64)
    diffs_neg = np.zeros(len(candles_closings) - 1, dtype=np.float64)

    avg_gain = np.zeros(len(candles_closings) - 14, dtype=np.float64)
    avg_loss = np.zeros(len(candles_closings) - 14, dtype=np.float64)
    RS = np.zeros(len(candles_closings) - 14, dtype=np.float64)
    RSI = np.zeros(len(candles_closings) - 14, dtype=np.float64)





    # for pair in valid_pairs:
    #     RSI_data[pair] = get_initial_rsi(np_total_data[pair][:, [4]])
    #     RSI_data_update[pair] = get_updated_rsi(np_total_data[pair][-1, [4]],
    #                             np_total_data_update[pair][:, [4]],
    #                             RSI_data[pair][0],
    #                             RSI_data[pair][1])





    # Obtener los vectores de ganancias y pérdidas
    for i in range(1, len(candles_closings)):
        diffs[i - 1] = candles_closings[i] - candles_closings[i - 1]

        if diffs[i - 1] > 0:
            diffs_pos[i - 1] = diffs[i - 1]

        else:
            diffs_neg[i - 1] = np.absolute(diffs[i - 1])

    # Calcular el promedio inicial de ganancias y pérdidas
    # con la media móvil simple (SMA)
    avg_gain[0] = np.mean(diffs_pos[0:14], dtype=np.float64)
    avg_loss[0] = np.mean(diffs_neg[0:14], dtype=np.float64)

    RS[0] = avg_gain[0] / avg_loss[0]
    RSI[0] = 100 - (100 / (1 + RS[0]))


    # Calcular el resto de promedios de ganancias y pérdidas
    # con las medias móviles modificadas (MMA)
    for counter, i in enumerate(range(1, len(candles_closings) - 14)):
        
        avg_gain[i] = ((avg_gain[i - 1] * 13) + diffs_pos[i + 13]) / 14
        avg_loss[i] = ((avg_loss[i - 1] * 13) + diffs_neg[i + 13]) / 14

        RS[i] = avg_gain[i] / avg_loss[i]

        RSI[i] = 100 - (100 / (1 + RS[i]))


    # last_rsi = RSI[-1]
    last_avg_gain = avg_gain[-1]
    last_avg_loss = avg_loss[-1]

    return [last_avg_gain, last_avg_loss, RSI]


def get_initial_rsi2(pairs, np_total_data):
    
    RSI_data_update = {}
    for pair in pairs:
        candles_closings = np_total_data[pair][:, [4]]

        # print(candles_closings)

        # Inicializar vectores
        diffs = np.zeros(len(candles_closings) - 1, dtype=np.float64)
        diffs_pos = np.zeros(len(candles_closings) - 1, dtype=np.float64)
        diffs_neg = np.zeros(len(candles_closings) - 1, dtype=np.float64)
        avg_gain = np.zeros(len(candles_closings) - 14, dtype=np.float64)
        avg_loss = np.zeros(len(candles_closings) - 14, dtype=np.float64)
        RS = np.zeros(len(candles_closings) - 14, dtype=np.float64)
        RSI = np.zeros(len(candles_closings) - 14, dtype=np.float64)

        # Obtener los vectores de ganancias y pérdidas
        for i in range(1, len(candles_closings)):
            diffs[i - 1] = candles_closings[i] - candles_closings[i - 1]
    
            if diffs[i - 1] > 0:
                diffs_pos[i - 1] = diffs[i - 1]
    
            else:
                diffs_neg[i - 1] = np.absolute(diffs[i - 1])
    
        # Calcular el promedio inicial de ganancias y pérdidas
        # con la media móvil simple (SMA)
        avg_gain[0] = np.mean(diffs_pos[0:14], dtype=np.float64)
        avg_loss[0] = np.mean(diffs_neg[0:14], dtype=np.float64)
    
        RS[0] = avg_gain[0] / avg_loss[0]
        RSI[0] = 100 - (100 / (1 + RS[0]))
    

        # Calcular el resto de promedios de ganancias y pérdidas
        # con las medias móviles modificadas (MMA)
        for counter, i in enumerate(range(1, len(candles_closings) - 14)):
            avg_gain[i] = ((avg_gain[i - 1] * 13) + diffs_pos[i + 13]) / 14
            avg_loss[i] = ((avg_loss[i - 1] * 13) + diffs_neg[i + 13]) / 14
            RS[i] = avg_gain[i] / avg_loss[i]
            RSI[i] = 100 - (100 / (1 + RS[i]))

        RSI_data_update[pair] = [avg_gain[-1], avg_loss[-1], RSI]

    return RSI_data_update


def get_initial_rsi3(pairs, np_total_data):

    RSI_data_update = {}
    for pair in pairs:
        candles_closings = np_total_data[pair][:, [4]]

        # print(candles_closings)

        # Inicializar vectores
        diffs = np.zeros(len(candles_closings) - 1, dtype=np.float64)
        diffs_pos = np.zeros(len(candles_closings) - 1, dtype=np.float64)
        diffs_neg = np.zeros(len(candles_closings) - 1, dtype=np.float64)
        avg_gain = np.zeros(len(candles_closings) - 14, dtype=np.float64)
        avg_loss = np.zeros(len(candles_closings) - 14, dtype=np.float64)
        RS = np.zeros(len(candles_closings) - 14, dtype=np.float64)
        RSI = np.zeros(len(candles_closings) - 14, dtype=np.float64)

        # Obtener los vectores de ganancias y pérdidas
        for i in range(1, len(candles_closings)):
            diffs[i - 1] = candles_closings[i] - candles_closings[i - 1]
    
            if diffs[i - 1] > 0:
                diffs_pos[i - 1] = diffs[i - 1]
    
            else:
                diffs_neg[i - 1] = np.absolute(diffs[i - 1])
    
        # Calcular el promedio de ganancias y pérdidas
        # con la media móvil simple (SMA)
        for i in range(14, len(candles_closings)):
            avg_gain[i - 14] = np.mean(diffs_pos[i - 14 : i], dtype=np.float64)
            avg_loss[i - 14] = np.mean(diffs_neg[i - 14 : i], dtype=np.float64)
            RS[i - 14] = avg_gain[i - 14] / avg_loss[i - 14]
            RSI[i - 14] = 100 - (100 / (1 + RS[i - 14]))

        RSI_data_update[pair] = [avg_gain[-1], avg_loss[-1], RSI]

    return RSI_data_update


def get_updated_bb(pairs, cycles_diff, np_total_data,
                   np_total_data_update, factor):

# def get_updated_rsi2(pairs, cycles_diff, np_total_data,
#                      np_total_data_update, RSI_data):
    # # Inicializar vectores
    # diffs = np.zeros(cycles_diff, dtype=np.float64)
    # diffs_pos = np.zeros(cycles_diff, dtype=np.float64)
    # diffs_neg = np.zeros(cycles_diff, dtype=np.float64)
    # avg_gain = np.zeros(cycles_diff + 1, dtype=np.float64)
    # avg_loss = np.zeros(cycles_diff + 1, dtype=np.float64)
    # RS = np.zeros(cycles_diff, dtype=np.float64)
    # RSI = np.zeros(cycles_diff, dtype=np.float64)

    # for pair in pairs:
    #     last_closing_price = np_total_data[pair][-1, [4]]
    #     current_closing_price = np_total_data_update[pair][:, [4]]
    #     last_avg_gain = RSI_data[pair][0]
    #     last_avg_loss = RSI_data[pair][1]

    #     candles_closings = np.concatenate([last_closing_price,
                            # current_closing_price.reshape(-1)])


    BB_data_update = {}

    for pair in pairs:
        last_closing_prices = np_total_data[pair][-19:, [4]]
        current_closing_prices = np_total_data_update[pair][:, [4]]

        candles_closings = np.concatenate([last_closing_prices,
                                           current_closing_prices.reshape(-1)])

        # Inicializar vectores
        sma20 = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
        ubb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
        lbb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)

        # print('\n' + 'sma20 size:' + '\n', len(sma20))

        for j, i in enumerate(range(19, len(candles_closings))):
    
            # Inicializar la desviaciòn estándar poblacional
            pstd = 0
            
            # Calcular el promedio con la media móvil simple (SMA)
            sma20[j] = np.mean(candles_closings[i-19 : i+1], dtype=np.float64)
            
    
            # print('\n' + 'candles_closings[i-19 : i+1]:' + '\n',
            # candles_closings[i-19 : i+1])
            # print('\n' + 'sma20:' + '\n', sma20)
            # print('\n' + 'j:' + '\n', j)
            # print('\n' + 'i:' + '\n', i)
    
    
            # Calcular la desviaciòn estándar poblacional
            pstd = np.std(candles_closings[i-19 : i+1], ddof = 0)
    
            # Calcular la banda de bollinger superior
            ubb[j] = sma20[j] + (factor * pstd)
    
            # Calcular la banda de bollinger inferior
            lbb[j] = sma20[j] - (factor * pstd)
    
    
        # print('\n' + 'sma20:' + '\n', sma20)
        # print('\n' + 'ubb:' + '\n', ubb)
        # print('\n' + 'lbb:' + '\n', lbb)


        BB_data_update[pair] = [lbb, ubb]

    return BB_data_update


def get_updated_bb2(pairs, np_total_data, np_total_data_update, factor):

# def get_updated_rsi2(pairs, cycles_diff, np_total_data,
#                      np_total_data_update, RSI_data):
    # # Inicializar vectores
    # diffs = np.zeros(cycles_diff, dtype=np.float64)
    # diffs_pos = np.zeros(cycles_diff, dtype=np.float64)
    # diffs_neg = np.zeros(cycles_diff, dtype=np.float64)
    # avg_gain = np.zeros(cycles_diff + 1, dtype=np.float64)
    # avg_loss = np.zeros(cycles_diff + 1, dtype=np.float64)
    # RS = np.zeros(cycles_diff, dtype=np.float64)
    # RSI = np.zeros(cycles_diff, dtype=np.float64)

    # for pair in pairs:
    #     last_closing_price = np_total_data[pair][-1, [4]]
    #     current_closing_price = np_total_data_update[pair][:, [4]]
    #     last_avg_gain = RSI_data[pair][0]
    #     last_avg_loss = RSI_data[pair][1]

    #     candles_closings = np.concatenate([last_closing_price,
    # current_closing_price.reshape(-1)])


    BB_data_update = {}

    for pair in pairs:
        last_closing_prices = np_total_data[pair][-19:, [4]]
        # print('last_closing_prices: ', last_closing_prices)
        current_closing_prices = np_total_data_update[pair][:, [4]]
        # print('current_closing_prices: ', current_closing_prices)

        candles_closings = np.concatenate([last_closing_prices.reshape(-1),
                                           current_closing_prices.reshape(-1)])

        # Inicializar vectores
        sma20 = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
        ubb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
        lbb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)

        # print('\n' + 'sma20 size:' + '\n', len(sma20))

        for j, i in enumerate(range(19, len(candles_closings))):
    
            # Inicializar la desviaciòn estándar poblacional
            pstd = 0
            
            # Calcular el promedio con la media móvil simple (SMA)
            sma20[j] = np.mean(candles_closings[i-19 : i+1], dtype=np.float64)
            
    
            # print('\n' + 'candles_closings[i-19 : i+1]:' + '\n',
            # candles_closings[i-19 : i+1])
            # print('\n' + 'sma20:' + '\n', sma20)
            # print('\n' + 'j:' + '\n', j)
            # print('\n' + 'i:' + '\n', i)
    
    
            # Calcular la desviaciòn estándar poblacional
            pstd = np.std(candles_closings[i-19 : i+1], ddof = 0)
    
            # Calcular la banda de bollinger superior
            ubb[j] = sma20[j] + (factor * pstd)
    
            # Calcular la banda de bollinger inferior
            lbb[j] = sma20[j] - (factor * pstd)
    
    
        # print('\n' + 'sma20:' + '\n', sma20)
        # print('\n' + 'ubb:' + '\n', ubb)
        # print('\n' + 'lbb:' + '\n', lbb)


        BB_data_update[pair] = [lbb, ubb]

    return BB_data_update


def get_updated_bb_live(last_closing_prices, current_closing_prices, factor):

    candles_closings = np.concatenate([last_closing_prices,
                                       current_closing_prices])

    # Inicializar vectores
    sma20 = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
    ubb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
    lbb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)

    # print('len(candles_closings:', len(candles_closings))
    # print('sma20.size:', sma20.size)
    # print('ubb.size:', ubb.size)
    # print('lbb.size:', lbb.size)

    for j, i in enumerate(range(19, len(candles_closings))):

        # Inicializar la desviaciòn estándar poblacional
        pstd = 0
        
        # Calcular el promedio con la media móvil simple (SMA)
        sma20[j] = np.mean(candles_closings[i-19 : i+1], dtype=np.float64)

        # Calcular la desviaciòn estándar poblacional
        pstd = np.std(candles_closings[i-19 : i+1], ddof = 0)

        # Calcular la banda de bollinger superior
        ubb[j] = sma20[j] + (factor * pstd)

        # Calcular la banda de bollinger inferior
        lbb[j] = sma20[j] - (factor * pstd)

    BB_data_update = [lbb[-1], ubb[-1]]

    return BB_data_update


def get_initial_bb(pairs, np_total_data, factor):

    BB_data = {}

    for pair in pairs:
        candles_closings = np_total_data[pair][:, [4]]

        # Inicializar vectores
        sma20 = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
        ubb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)
        lbb = np.zeros(len(candles_closings) - 20 + 1, dtype=np.float64)

        # print('\n' + 'sma20 size:' + '\n', len(sma20))

        for j, i in enumerate(range(19, len(candles_closings))):
    
            # Inicializar la desviaciòn estándar poblacional
            pstd = 0
            
            # Calcular el promedio con la media móvil simple (SMA)
            sma20[j] = np.mean(candles_closings[i-19 : i+1], dtype=np.float64)
            
    
            # print('\n' + 'candles_closings[i-19 : i+1]:' + '\n',
            # candles_closings[i-19 : i+1])
            # print('\n' + 'sma20:' + '\n', sma20)
            # print('\n' + 'j:' + '\n', j)
            # print('\n' + 'i:' + '\n', i)
    
    
            # Calcular la desviaciòn estándar poblacional
            pstd = np.std(candles_closings[i-19 : i+1], ddof = 0)
    
            # Calcular la banda de bollinger superior
            ubb[j] = sma20[j] + (factor * pstd)
    
            # Calcular la banda de bollinger inferior
            lbb[j] = sma20[j] - (factor * pstd)
    
    
        # print('\n' + 'sma20:' + '\n', sma20)
        # print('\n' + 'ubb:' + '\n', ubb)
        # print('\n' + 'lbb:' + '\n', lbb)


        BB_data[pair] = [lbb, ubb]

    return BB_data


async def obtain_data(aclient, pairs, interval, limit, folder_path,
                      rest_of_filename):

    np_total_data = {}
    pairs_list = []
    # total_pairs_list = []
    weight = 0

    for pair in pairs:

        pairs_list.append(pair)
        # total_pairs_list.append(pair)

        if limit < 100:
            weight = weight + 1
    
        elif limit < 500:
            weight = weight + 2
    
        elif limit < 1000:
            weight = weight + 5
    
        else:
            weight = weight + 10

        if weight >= 1189:
            weight = 0

            tasks = [get_kline(aclient, pair_2, interval, limit)               \
                     for pair_2 in pairs_list]
            klines = await asyncio.gather(*tasks)

            for c, v in enumerate(klines):
                np_total_data[pairs_list[c]] =                                 \
                np.delete(np.array(v, dtype=np.float64), -1, 0)

            print('Límite de peticiones por minuto excedido, ' +               \
                  'esperando 61 segundos...')
            time.sleep(61)
            pairs_list.clear()

    if len(pairs_list) > 0:

        tasks = [get_kline(aclient, pair_2, interval, limit)                   \
                 for pair_2 in pairs_list]
        klines = await asyncio.gather(*tasks)

        for c, v in enumerate(klines):

            v_npa = np.array(v)
            print('\n', 'c: ', c, '\n')
            # print('\n', 'v: ', v, '\n')
            print('\n', 'v_ndim: ', v_npa.ndim, '\n')
            print('\n', 'v_shape: ', v_npa.shape, '\n')
            print('\n', 'v_size: ', v_npa.size, '\n')

            np_total_data[pairs_list[c]] =                                     \
            np.delete(np.array(v, dtype=np.float64), -1, 0)

    return np_total_data


async def obtain_data_10(aclient, pairs, interval, limit, folder_path,
                      rest_of_filename):

    np_total_data = {}
    pairs_list = []
    # total_pairs_list = []
    weight = 0

    for pair in pairs:

        pairs_list.append(pair)
        # total_pairs_list.append(pair)

        if limit < 100:
            weight = weight + 1
    
        elif limit < 500:
            weight = weight + 2
    
        elif limit < 1000:
            weight = weight + 5
    
        else:
            weight = weight + 10

        if weight >= 1189:
            weight = 0

            tasks = [get_kline(aclient, pair_2, interval, limit)               \
                     for pair_2 in pairs_list]


            print('Justo antes de generar los klines')
            klines = await asyncio.gather(*tasks)


            with open('klines_test_2.txt', 'w') as f:
                print('Escribiendo klines_test_2.txt...')
                print(json.dumps(klines, sort_keys=True, indent=4,
                                 separators=(',', ': ')), file=f)


            print('Justo despues de generar los klines')

            for c, v in enumerate(klines):
                np_total_data[pairs_list[c]] =                                 \
                np.delete(np.array(v, dtype=np.float64), -1, 0)

            print('Límite de peticiones por minuto excedido, ' +               \
                  'esperando 61 segundos...')
            time.sleep(61)
            pairs_list.clear()

    if len(pairs_list) > 0:

        tasks = [get_kline(aclient, pair_2, interval, limit)                   \
                 for pair_2 in pairs_list]
        klines = await asyncio.gather(*tasks)

        for c, v in enumerate(klines):

            v_npa = np.array(v)
            print('\n', 'c: ', c, '\n')
            # print('\n', 'v: ', v, '\n')
            print('\n', 'v_ndim: ', v_npa.ndim, '\n')
            print('\n', 'v_shape: ', v_npa.shape, '\n')
            print('\n', 'v_size: ', v_npa.size, '\n')

            np_total_data[pairs_list[c]] =                                     \
            np.delete(np.array(v, dtype=np.float64), -1, 0)

    return np_total_data


def obtain_data_sync(client, pairs, interval, limit, folder_path,
                      rest_of_filename):

    np_total_data = {}
    pairs_list = []
    # total_pairs_list = []
    weight = 0

    for pair in pairs:

        pairs_list.append(pair)
        # total_pairs_list.append(pair)

        if limit < 100:
            weight = weight + 1
    
        elif limit < 500:
            weight = weight + 2
    
        elif limit < 1000:
            weight = weight + 5
    
        else:
            weight = weight + 10

        if weight >= 1189:
            weight = 0


            print('Justo antes de generar los klines_1')

            klines = [get_kline_sync(client, pair_2, interval, limit)               \
                     for pair_2 in pairs_list]

            with open('klines_test_2.txt', 'w') as f:
                print('Escribiendo klines_test_2.txt...')
                print(json.dumps(klines, sort_keys=True, indent=4,
                                 separators=(',', ': ')), file=f)

            print('Justo despues de generar los klines_1')


            for c, v in enumerate(klines):
                np_total_data[pairs_list[c]] =                                 \
                np.delete(np.array(v, dtype=np.float64), -1, 0)

            print('Límite de peticiones por minuto excedido, ' +               \
                  'esperando 61 segundos...')
            time.sleep(61)
            pairs_list.clear()

    if len(pairs_list) > 0:

        print('Justo antes de generar los klines_2')

        klines = [get_kline_sync(client, pair_2, interval, limit)               \
                 for pair_2 in pairs_list]

        with open('klines_test_2.txt', 'a') as f:
            print('Escribiendo klines_test_2.txt...')
            print(json.dumps(klines, sort_keys=True, indent=4,
                             separators=(',', ': ')), file=f)

        print('Justo despues de generar los klines_2')



        for c, v in enumerate(klines):

            v_npa = np.array(v)
            print('\n', 'c: ', c, '\n')
            # print('\n', 'v: ', v, '\n')
            print('\n', 'v_ndim: ', v_npa.ndim, '\n')
            print('\n', 'v_shape: ', v_npa.shape, '\n')
            print('\n', 'v_size: ', v_npa.size, '\n')

            np_total_data[pairs_list[c]] =                                     \
            np.delete(np.array(v, dtype=np.float64), -1, 0)

    return np_total_data


async def obtain_data2(aclient, pairs, interval, limit, folder_path,
                       rest_of_filename, mode, timestamp):

    np_total_data = {}
    pairs_list = []
    weight = 0

    same = True
    intentos = 0

    print('Total de pares a actualizar: ', len(pairs), '\n')
    while same:

        if mode == 'update':

            intentos = intentos + 1
            print('Intentos de actualizacion: ', intentos)

            pairs_list = []
            same = False
            sin_actualizar = []

        for pair in pairs:
    
            pairs_list.append(pair)
    
            if limit < 100:
                weight = weight + 1
        
            elif limit < 500:
                weight = weight + 2
        
            elif limit < 1000:
                weight = weight + 5
        
            else:
                weight = weight + 10
    
            if weight >= 1189:
                weight = 0
    
                tasks = [get_kline(aclient, pair_2, interval, limit)           \
                         for pair_2 in pairs_list]
                klines = await asyncio.gather(*tasks)
    
                if mode == 'update':

                    flag1 = True
                    flag2 = True

                    for c, v in enumerate(klines):
                        np_total_data[pairs_list[c]] =                         \
                        np.delete(np.array(v, dtype=np.float64), -1, 0)
    
                        if flag1:
                            flag1 = False
                            print('Timestamp de referencia 1: ', timestamp)
                            print('Timestamp a comparar 1: ',
                            int(np_total_data[pairs_list[c]][0, [0]] / 1e3))

 
                        if int(np_total_data[pairs_list[c]][0, [0]] / 1e3) !=  \
                        timestamp:

                            sin_actualizar.append(pairs_list[c])

                            if flag2:
                                flag2 = False
                                print('same = True 1')
                                print('La actualizacion no pudo completarse'   \
                                      + '\n')

                            same = True

                else:

                    for c, v in enumerate(klines):
                        np_total_data[pairs_list[c]] =                         \
                        np.delete(np.array(v, dtype=np.float64), -1, 0)

                print('Límite de peticiones por minuto excedido, '             \
                      + 'esperando 61 segundos...')
                time.sleep(61)
                pairs_list.clear()

        if len(pairs_list) > 0:
    
            tasks = [get_kline(aclient, pair_2, interval, limit)               \
                     for pair_2 in pairs_list]
            klines = await asyncio.gather(*tasks)
    
            if mode == 'update':

                flag1 = True
                flag2 = True

                for c, v in enumerate(klines):
                    np_total_data[pairs_list[c]] =                             \
                    np.delete(np.array(v, dtype=np.float64), -1, 0)

                    if flag1:
                        flag1 = False
                        print('Timestamp de referencia 2: ', timestamp)
                        print('Timestamp a comparar 2: ',
                              int(np_total_data[pairs_list[c]][0, [0]] / 1e3))

                    if int(np_total_data[pairs_list[c]][0, [0]] / 1e3) !=      \
                       timestamp:

                        sin_actualizar.append(pairs_list[c])

                        if flag2:
                            flag2 = False
                            print('same = True 2')
                            print('La actualizacion no pudo completarse'       \
                                  + '\n')

                        same = True

            else:

                for c, v in enumerate(klines):
                    np_total_data[pairs_list[c]] =                             \
                    np.delete(np.array(v, dtype=np.float64), -1, 0)

        if mode == 'update':
            pairs = sin_actualizar
            print('Total de pares sin actualizar: ', len(sin_actualizar), '\n')

    return np_total_data


def obtain_data_sync_2(client, pairs, interval, limit, folder_path,
                       rest_of_filename, mode, timestamp):

    np_total_data = {}
    pairs_list = []
    weight = 0

    same = True
    intentos = 0

    print('Total de pares a actualizar: ', len(pairs), '\n')
    while same:

        if mode == 'update':

            intentos = intentos + 1
            print('Intentos de actualizacion: ', intentos)

            pairs_list = []
            same = False
            sin_actualizar = []

        for pair in pairs:
    
            pairs_list.append(pair)
    
            if limit < 100:
                weight = weight + 1
        
            elif limit < 500:
                weight = weight + 2
        
            elif limit < 1000:
                weight = weight + 5
        
            else:
                weight = weight + 10
    
            if weight >= 1189:
                weight = 0
    





                print('Justo antes de generar los klines_3.1')
    
                klines = [get_kline_sync(client, pair_2, interval, limit)               \
                         for pair_2 in pairs_list]
    
                with open('klines_test_3.txt', 'w') as f:
                    print('Escribiendo klines_test_2.txt...')
                    print(json.dumps(klines, sort_keys=True, indent=4,
                                     separators=(',', ': ')), file=f)
    
                print('Justo despues de generar los klines_3.1')

    




                if mode == 'update':

                    flag1 = True
                    flag2 = True

                    for c, v in enumerate(klines):
                        np_total_data[pairs_list[c]] =                         \
                        np.delete(np.array(v, dtype=np.float64), -1, 0)
    
                        if flag1:
                            flag1 = False
                            print('Timestamp de referencia 1: ', timestamp)
                            print('Timestamp a comparar 1: ',
                            int(np_total_data[pairs_list[c]][0, [0]] / 1e3))

 
                        if int(np_total_data[pairs_list[c]][0, [0]] / 1e3) !=  \
                        timestamp:

                            sin_actualizar.append(pairs_list[c])

                            if flag2:
                                flag2 = False
                                print('same = True 1')
                                print('La actualizacion no pudo completarse'   \
                                      + '\n')

                            same = True

                else:

                    for c, v in enumerate(klines):
                        np_total_data[pairs_list[c]] =                         \
                        np.delete(np.array(v, dtype=np.float64), -1, 0)

                print('Límite de peticiones por minuto excedido, '             \
                      + 'esperando 61 segundos...')
                time.sleep(61)
                pairs_list.clear()

        if len(pairs_list) > 0:






            print('Justo antes de generar los klines_3.2')

            klines = [get_kline_sync(client, pair_2, interval, limit)               \
                     for pair_2 in pairs_list]

            with open('klines_test_3.txt', 'a') as f:
                print('Escribiendo klines_test_2.txt...')
                print(json.dumps(klines, sort_keys=True, indent=4,
                                 separators=(',', ': ')), file=f)

            print('Justo despues de generar los klines_3.2')
    





            if mode == 'update':

                flag1 = True
                flag2 = True

                for c, v in enumerate(klines):
                    np_total_data[pairs_list[c]] =                             \
                    np.delete(np.array(v, dtype=np.float64), -1, 0)

                    if flag1:
                        flag1 = False
                        print('Timestamp de referencia 2: ', timestamp)
                        print('Timestamp a comparar 2: ',
                              int(np_total_data[pairs_list[c]][0, [0]] / 1e3))

                    if int(np_total_data[pairs_list[c]][0, [0]] / 1e3) !=      \
                       timestamp:

                        sin_actualizar.append(pairs_list[c])

                        if flag2:
                            flag2 = False
                            print('same = True 2')
                            print('La actualizacion no pudo completarse'       \
                                  + '\n')

                        same = True

            else:

                for c, v in enumerate(klines):
                    np_total_data[pairs_list[c]] =                             \
                    np.delete(np.array(v, dtype=np.float64), -1, 0)

        if mode == 'update':
            pairs = sin_actualizar
            print('Total de pares sin actualizar: ', len(sin_actualizar), '\n')

    return np_total_data


def create_folder_main(base_dir):

    os.mkdir(base_dir)
    print('Directorio base creado')


def create_folder_GENERAL(base_dir):

    # os.mkdir(base_dir)
    os.mkdir(base_dir + '/GENERAL')
    print('Directorio de datos GENERAL creado')


def create_folder_RSI(base_dir):

    os.mkdir(base_dir + '/RSI')
    print('Directorio de datos RSI creado')


def create_folder_BB(base_dir):

    os.mkdir(base_dir + '/BB')
    print('Directorio de datos BB creado')


def write_headers_main(pairs, interval, limit, folder_path,
                       rest_of_filename_main):

    for c, v in enumerate(pairs):
        encabezado = 'Número de ciclos: ' + str(limit) +'\n' + \
                      'Intervalo de tiempo: ' + interval +'\n\n' + \
                      '{:*^24}'.format('Fecha y hora de apertura') + ' | ' + \
                      '{:>16}'.format('Precio de apertura') + ' | ' + \
                      '{:*^24}'.format('Fecha y hora de cierre') + ' | ' + \
                      '{:>16}'.format('Precio de cierre') + ' | ' + \
                      '{:>15}'.format('Precio más bajo') + ' | ' + \
                      '{:>15}'.format('Precio más alto') + ' | ' + \
                      '{:>16}'.format('Tiempo de apertura') + ' | ' + \
                      '{:>16}'.format('Tiempo de cierre')

        with open(folder_path + v + rest_of_filename_main, 'w') as f:
            print(encabezado, file = f)


def write_headers_main_backup(pairs, interval, limit, folder_path,
                              rest_of_filename_main):

    for c, v in enumerate(pairs):
        encabezado = 'Número de ciclos: ' + str(limit) +'\n' +                 \
                      'Intervalo de tiempo: ' + interval +'\n\n' +             \
                      '{:*^24}'.format('Fecha y hora de apertura') + ' | ' +   \
                      '{:>16}'.format('Precio de apertura') + ' | ' +          \
                      '{:*^24}'.format('Fecha y hora de cierre') + ' | ' +     \
                      '{:>16}'.format('Precio de cierre') + ' | ' +            \
                      '{:>15}'.format('Precio más bajo') + ' | ' +             \
                      '{:>15}'.format('Precio más alto') + ' | ' +             \
                      '{:>16}'.format('Tiempo de apertura') + ' | ' +          \
                      '{:>16}'.format('Tiempo de cierre') + ' | ' +            \
                      '{:>12}'.format('RSI') + ' | ' +                         \
                      '{:>16}'.format('Banda de Bollinger inferior') + ' | ' + \
                      '{:>16}'.format('Banda de Bollinger superior') + '\n' +  \
                      '{:>23}'.format('dd-mm-aaaa  hh:mm:ss.ms') + '  | ' +    \
                      '{:>18}'.format('(' + v[:-4] + '/' + v[-4:]  + ')')      \
                      + ' | ' +                                                \
                      '{:>23}'.format('dd-mm-aaaa  hh:mm:ss.ms') + '  | ' +    \
                      '{:>16}'.format('(' + v[:-4] + '/' + v[-4:]  + ')')      \
                      + ' | ' +                                                \
                      '{:>15}'.format('(' + v[:-4] + '/' + v[-4:]  + ')')      \
                      + ' | ' +                                                \
                      '{:>15}'.format('(' + v[:-4] + '/' + v[-4:]  + ')')      \
                      + ' | ' +                                                \
                      '{:>18}'.format('(ms)') + ' | '                          \
                      '{:>16}'.format('(ms)') + ' | '                          \
                      '{:>12}'.format('(adim)') + ' | '                        \
                      '{:>27}'.format('(' + v[:-4] + '/' + v[-4:]  + ')')      \
                      + ' | ' +                                                \
                      '{:>27}'.format('(' + v[:-4] + '/' + v[-4:]  + ')')

        with open(folder_path + v + rest_of_filename_main, 'w') as f:
            print(encabezado, file = f)


def write_headers_RSI(pairs, interval, limit, folder_path_RSI,
                      rest_of_filename_RSI, RSI_min, RSI_max,
                      RSI_points_min_max):

    for c, v in enumerate(pairs):
        encabezado_RSI = 'Número de ciclos: ' + str(limit) +'\n' +             \
                      'Intervalo de tiempo: ' + interval +'\n' +               \
                      'RSI minimo: ' + str(RSI_min) +'\n' +                    \
                      'RSI maximo: ' + str(RSI_max) +'\n' +                    \
                      'Numero de ciclos menores que ' + str(RSI_min) + ': ' +  \
                       str(RSI_points_min_max[v][0]) + '\n' +                  \
                      'Numero de ciclos mayores que ' + str(RSI_max) + ': ' +  \
                       str(RSI_points_min_max[v][1]) + '\n\n' +                \
                      '{:*^24}'.format('Fecha y hora de apertura') + ' | ' +   \
                      '{:>16}'.format('Precio de apertura') + ' | ' +          \
                      '{:*^24}'.format('Fecha y hora de cierre') + ' | ' +     \
                      '{:>16}'.format('Precio de cierre') + ' | ' +            \
                      '{:>15}'.format('Precio más bajo') + ' | ' +             \
                      '{:>15}'.format('Precio más alto') + ' | ' +             \
                      '{:>12}'.format('RSI')

        with open(folder_path_RSI + v + rest_of_filename_RSI, 'w') as f:
            print(encabezado_RSI, file = f)


def write_headers_BB(pairs, interval, limit, folder_path_BB,
                     rest_of_filename_BB, mgn_pct,
                     BB_points_passed, BB_points_near):

    for c, v in enumerate(pairs):
        encabezado_BB = 'Número de ciclos: ' + str(limit) +'\n' +              \
                      'Intervalo de tiempo: ' + interval +'\n' +               \
                      'Numero de ciclos cercanos a la ' +                      \
                      'Banda de Bollinger inferior: ' +                        \
                       str(np.count_nonzero(BB_points_near[v][0])) + '\n' +    \
                      'Numero de ciclos cercanos a la ' +                      \
                      'Banda de Bollinger superior: ' +                        \
                       str(np.count_nonzero(BB_points_near[v][1])) + '\n' +    \
                      'Numero de ciclos menores que la ' +                     \
                      'Banda de Bollinger inferior: ' +                        \
                       str(np.count_nonzero(BB_points_passed[v][0])) + '\n' +  \
                      'Numero de ciclos mayores que la ' +                     \
                      'Banda de Bollinger superior: ' +                        \
                       str(np.count_nonzero(BB_points_passed[v][1])) + '\n' +  \
                      'Margen (%): ' + str(mgn_pct) +'\n\n' +                  \
                      '{:*^24}'.format('Fecha y hora de apertura') + ' | ' +   \
                      '{:>16}'.format('Precio de apertura') + ' | ' +          \
                      '{:*^24}'.format('Fecha y hora de cierre') + ' | ' +     \
                      '{:>16}'.format('Precio de cierre') + ' | ' +            \
                      '{:>15}'.format('Precio más bajo') + ' | ' +             \
                      '{:>15}'.format('Precio más alto') + ' | ' +             \
                      '{:>16}'.format('Banda de Bollinger inferior') + ' | ' + \
                      '{:>16}'.format('Banda de Bollinger superior')

        with open(folder_path_BB + v + rest_of_filename_BB, 'w') as f:
            print(encabezado_BB, file = f)


def write_to_files_main(pairs, folder_path, rest_of_filename, np_total_data,
                        precisions):

    for pair in pairs:
        with open(folder_path + pair + rest_of_filename, 'a') as f:
            for c, _ in enumerate(np_total_data[pair][:, [0]]):
                open_time_stamp =                                              \
                dt.fromtimestamp(int(np_total_data[pair][c, [0]]) / 1e3)
                close_time_stamp =                                             \
                dt.fromtimestamp(int(np_total_data[pair][c, [6]]) / 1e3)

    # Fecha y hora de apertura
                print(open_time_stamp.strftime('%d-%m-%Y  %H:%M:%S') +         \
                      '.{:03.0f}'.format(open_time_stamp.microsecond / 1e3),

    # Precio de apertura
                      ('{:>20.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [1]])),

    # Fecha y hora de cierre
                      close_time_stamp.strftime('  %d-%m-%Y  %H:%M:%S') +      \
                      '.{:03.0f}'.format(close_time_stamp.microsecond / 1e3),

    # Precio de cierre
                      ('{:>18.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [4]])),

    # Precio más bajo
                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [3]])),

    # Precio más alto
                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [2]])),

    # Tiempo de apertura
                      '{:>20.0f}'.format(float(np_total_data[pair][c, [0]])),

    # Tiempo de cierre
                      '{:>18.0f}'.format(float(np_total_data[pair][c, [6]])),

                      file = f)


def write_to_files_main_backup(pairs, folder_path, rest_of_filename,
                               np_total_data, precisions, RSI, BB):

    for pair in pairs:
        with open(folder_path + pair + rest_of_filename, 'a') as f:
            for c, _ in enumerate(np_total_data[pair][:, [0]]):
                open_time_stamp =                                              \
                dt.fromtimestamp(int(np_total_data[pair][c, [0]]) / 1e3)
                close_time_stamp =                                             \
                dt.fromtimestamp(int(np_total_data[pair][c, [6]]) / 1e3)

                print(open_time_stamp.strftime('%d-%m-%Y  %H:%M:%S') +         \
                      '.{:03.0f}'.format(open_time_stamp.microsecond / 1e3),

                      ('{:>20.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [1]])),

                      close_time_stamp.strftime('  %d-%m-%Y  %H:%M:%S') +      \
                      '.{:03.0f}'.format(close_time_stamp.microsecond / 1e3),

                      ('{:>18.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [4]])),

                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [3]])),
                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [2]])),

                      '{:>20.0f}'.format(float(np_total_data[pair][c, [0]])),
                      '{:>18.0f}'.format(float(np_total_data[pair][c, [6]])),

                      '{:>14.8f}'.format(float(RSI[pair][2][c])),

                      ('{:>29.' + str(precisions[pair]) + 'f}')                \
                      .format(float(BB[pair][0][c])),
                      ('{:>29.' + str(precisions[pair]) + 'f}')                \
                      .format(float(BB[pair][1][c])),

                      file = f)


def write_to_files_RSI(pairs, folder_path_RSI, rest_of_filename_RSI,
                       np_total_data, precisions, RSI):

    for pair in pairs:
        with open(folder_path_RSI + pair + rest_of_filename_RSI, 'a') as f:
            for c, _ in enumerate(np_total_data[pair][:, [0]]):
                open_time_stamp =                                              \
                dt.fromtimestamp(int(np_total_data[pair][c, [0]]) / 1e3)
                close_time_stamp =                                             \
                dt.fromtimestamp(int(np_total_data[pair][c, [6]]) / 1e3)

    # Fecha y hora de apertura
                print(open_time_stamp.strftime('%d-%m-%Y  %H:%M:%S') +         \
                      '.{:03.0f}'.format(open_time_stamp.microsecond / 1e3),

    # Precio de apertura
                      ('{:>20.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [1]])),

    # Fecha y hora de cierre
                      close_time_stamp.strftime('  %d-%m-%Y  %H:%M:%S') +      \
                      '.{:03.0f}'.format(close_time_stamp.microsecond / 1e3),

    # Precio de cierre
                      ('{:>18.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [4]])),

    # Precio más bajo
                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [3]])),

    # Precio más alto
                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [2]])),

    # RSI de cierre
                      '{:>14.8f}'.format(float(RSI[pair][2][c])),

                      file = f)


def write_to_files_BB(pairs, folder_path_BB, rest_of_filename_BB,
                      np_total_data, precisions, BB):

    for pair in pairs:
        with open(folder_path_BB + pair + rest_of_filename_BB, 'a') as f:
            for c, _ in enumerate(np_total_data[pair][:, [0]]):
                open_time_stamp =                                              \
                dt.fromtimestamp(int(np_total_data[pair][c, [0]]) / 1e3)
                close_time_stamp =                                             \
                dt.fromtimestamp(int(np_total_data[pair][c, [6]]) / 1e3)

    # Fecha y hora de apertura
                print(open_time_stamp.strftime('%d-%m-%Y  %H:%M:%S') +         \
                      '.{:03.0f}'.format(open_time_stamp.microsecond / 1e3),

    # Precio de apertura
                      ('{:>20.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [1]])),

    # Fecha y hora de cierre
                      close_time_stamp.strftime('  %d-%m-%Y  %H:%M:%S') +      \
                      '.{:03.0f}'.format(close_time_stamp.microsecond / 1e3),

    # Precio de cierre
                      ('{:>18.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [4]])),

    # Precio más bajo
                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [3]])),

    # Precio más alto
                      ('{:>17.' + str(precisions[pair]) + 'f}')                \
                      .format(float(np_total_data[pair][c, [2]])),

    # Banda de Bollinger inferior
                      ('{:>29.' + str(precisions[pair]) + 'f}')                \
                      .format(float(BB[pair][0][c])),

    # Banda de Bollinger superior
                      ('{:>29.' + str(precisions[pair]) + 'f}')                \
                      .format(float(BB[pair][1][c])),

                      file = f)


def get_cycles_diff_vec(old_ts, current_ts, interval):

    old_date=dt.fromtimestamp(old_ts)
    current_date=dt.fromtimestamp(current_ts)
    date_diff=current_date - old_date
    minutes = (date_diff.days * 24 * 60) + (date_diff.seconds / 60)

    if interval == '5m':
        cycles_diff = math.trunc(minutes / 5)

    elif interval == '15m':
        cycles_diff = math.trunc(minutes / 15)

    elif interval == '30m':
        cycles_diff = math.trunc(minutes / 30)

    elif interval == '1h':
        cycles_diff = math.trunc(minutes / 60)

    elif interval == '4h':
        cycles_diff = math.trunc(minutes / 240)

    elif interval == '1d':
        cycles_diff = date_diff.days

    return cycles_diff


def get_min_quant_e(info, symbols):

    precisions = {}
    for symbol in symbols:
        for item in info['symbols']:
            if item['symbol'] == symbol:
                for f in item['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        precisions[symbol] =                                   \
                        int(round(-math.log(float(f['tickSize']), 10), 0))

    return precisions


def get_valid_pairs_without_settling(info, symbols):

    for symbol in symbols:
        for item in info['symbols']:
            if item['symbol'] == symbol:
                if item['status'] == 'SETTLING':
                    symbols.remove(symbol)

    return symbols


async def get_kline(aclient, symbol, interval, limit):

    kline = await aclient.futures_klines(symbol=symbol,
                                          interval=interval, limit=limit)
    # kline = await aclient.futures_historical_klines(symbol=symbol,
    #                                                 interval=interval,
    #                                                 limit=limit)
    # kline = await aclient.futures_historical_klines(symbol=symbol,
    #                                                 interval=interval,
    #                                                 start_str='1 day ago')
    # kline = await aclient.futures_historical_klines_generator(symbol,
    # interval, start_str)
    return kline


def get_kline_sync(client, symbol, interval, limit):

    kline = client.futures_klines(symbol=symbol,
                                          interval=interval, limit=limit)

    print('Generando kline para el simbolo ' + symbol)

    # kline = await aclient.futures_historical_klines(symbol=symbol,
    #                                                 interval=interval,
    #                                                 limit=limit)
    # kline = await aclient.futures_historical_klines(symbol=symbol,
    #                                                 interval=interval,
    #                                                 start_str='1 day ago')
    # kline = await aclient.futures_historical_klines_generator(symbol,
    # interval, start_str)
    return kline


def get_cmclist(symbols_max, symbols_limit):

    symbols = []
    url = 'https://web-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    
    for start in range(1, symbols_max, symbols_limit):
        params = {'start': start, 'limit': symbols_limit}
        r = requests.get(url, params=params)
        data = r.json()
        
        for item in data['data']:
            symbols.append(item['symbol'])

    return symbols


def get_valid_pairs(symbols, trading_pairs, to_exclude):

    valid_pairs = []
    to_exclude = ['BTC', 'ETH', 'AVAX']
    # to_exclude = ['ETH', 'AVAX']
    for symbol in symbols:
        if symbol not in to_exclude:
            for pair in trading_pairs:
                if pair.startswith(symbol) and pair.endswith('USDT') and       \
                   (len(pair) == len(symbol) + len('USDT')) and                \
                   (pair not in valid_pairs):
                   valid_pairs.append(pair)

    return valid_pairs
    # return valid_pairs[:1]


def get_client():

    api_key =                                                                  \
    'yIDw0R7fFzKkf3JC9WpY8duSWb93ccsdxDqrFIOyELmmnyvFkWIUiTgc7jmGJa94'
    api_secret =                                                               \
    'r6XzixDm5jjVnLLtSei0zJJtEpCcb8tlGSL45PHcX2AYE3lS8k8AqbQnlMPq1jV7'
    client = Client(api_key, api_secret, testnet=False)
   
    return client


def bot_send_text(bot_message):
    
    bot_token = '5331264103:AAE5O67MCxY4L3I0GVyjMPnbyt4y4b8Xr9M'
    bot_chatID = '794171785'
    send_text = 'https://api.telegram.org/bot' + bot_token                     \
    + '/sendMessage?chat_id=' + bot_chatID                                     \
    + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response


async def main():

    start = time.time()

    # retrieve_mode = 'sync'
    retrieve_mode = 'async'
    if retrieve_mode == 'sync':
        print('Modo de obtencion de datos: secuencial')
    else:
        print('Modo de obtencion de datos: asincrono')

    fixed_valid_pairs = True
    if fixed_valid_pairs == True:
        print('Modo de obtencion de pares validos: archivo de texto'           \
              + ' (fixed_valid_pairs.txt)')
    else:
        print('Modo de obtencion de pares validos: coinmarketcap')

    client = get_client()
    aclient = await AsyncClient.create()

    symbols_max = 20000
    symbols_limit = 5000

    futures_exchange_info = await aclient.futures_exchange_info()
    with open('futures_exchange_info.txt', 'w') as f:
        print('Escribiendo futures_exchange_info.txt...')
        print(json.dumps(futures_exchange_info, sort_keys=True, indent=4,
                         separators=(',', ': ')), file=f)

    if fixed_valid_pairs == True:
        valid_pairs = []
        with open('fixed_valid_pairs.txt', 'r') as f:
            print('Leyendo fixed_valid_pairs.txt...')
            for line in f:
                valid_pairs.append(line.rstrip())
        print('valid_pairs', valid_pairs)
    else:
        symbols = get_cmclist(symbols_max, symbols_limit)
        with open('symbols.txt', 'w') as f:
            print('Escribiendo symbols.txt...')
            for counter, value in enumerate(symbols):
                print('{:>6}'.format(counter + 1) + '  ', value, file=f)
    
        trading_pairs =                                                            \
        [info['symbol'] for info in futures_exchange_info['symbols']]
        with open('trading_pairs.txt', 'w') as f:
            print('Escribiendo trading_pairs.txt...')
            for counter, value in enumerate(trading_pairs):
                print('{:>6}'.format(counter + 1) + '  ', value, file=f)
    
        to_exclude = ['BTC', 'ETH', 'AVAX']
        valid_pairs = get_valid_pairs(symbols, trading_pairs, to_exclude)
        with open('valid_pairs.txt', 'w') as f:
            print('Escribiendo valid_pairs.txt...')
            for counter, value in enumerate(valid_pairs):
                print('{:>6}'.format(counter + 1) + '  ', value, file=f)
    
        valid_pairs_without_settling =                                             \
        get_valid_pairs_without_settling(futures_exchange_info, valid_pairs)
        with open('valid_pairs_without_settling.txt', 'w') as f:
            print('Escribiendo valid_pairs_without_settling.txt...')
            for counter, value in enumerate(valid_pairs_without_settling):
                print('{:>6}'.format(counter + 1) + '  ', value, file=f)
    
        valid_pairs = valid_pairs_without_settling


    # print('Esperando 120 segundos...')
    # time.sleep(120)


    factor = 3
    interval = '5m'
    # interval = '4h'
    limit = 1500
    RSI_min = 30
    RSI_max = 70

    now = dt.now()
    print('\n', now, '\n')

    base_dir = 'db__' + now.strftime('%Y-%m-%d__%H-%M-%S')
    create_folder_main(base_dir)
    create_folder_GENERAL(base_dir)
    create_folder_RSI(base_dir)
    create_folder_BB(base_dir)
    folder_path_main = 'db__' + now.strftime('%Y-%m-%d__%H-%M-%S') + '/'
    folder_path_GENERAL = 'db__' + now.strftime('%Y-%m-%d__%H-%M-%S')          \
                          + '/GENERAL/'
    folder_path_RSI = 'db__' + now.strftime('%Y-%m-%d__%H-%M-%S') + '/RSI/'
    folder_path_BB = 'db__' + now.strftime('%Y-%m-%d__%H-%M-%S') + '/BB/'
    rest_of_filename_main = '__' + '__' + interval + '.txt'
    rest_of_filename_RSI = '__' + '__' + interval + '__RSI' + '.txt'
    rest_of_filename_BB = '__' + '__' + interval + '__BB' + '.txt'

    precisions = get_min_quant_e(futures_exchange_info, valid_pairs)
    # np_total_data = await obtain_data(aclient, valid_pairs, interval, limit,
    #                                   folder_path_main, rest_of_filename_main)


    loop = True
    while loop is True:

        try:
            if retrieve_mode == 'sync':
                np_total_data = obtain_data_sync(client, valid_pairs, interval,
                                                 limit, folder_path_main,
                                                 rest_of_filename_main)
            else:
                np_total_data = await obtain_data(aclient, valid_pairs,
                                                  interval, limit,
                                                  folder_path_main,
                                                  rest_of_filename_main)
            loop = False
            print('Datos obtenidos con exito!')

        # except BinanceAPIException as e:
        #     print(e)

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")

            print('Cerrando la conexion...')
            await aclient.close_connection()

            # Esperando 61 segundos antes de abrir nuevamente la conexion para reintentar
            print('Esperando 61 segundos antes de abrir nuevamente la conexion para reintentar...')
            time.sleep(60)  # wait a minute before restarting

            print('Abriendo la conexion...')
            aclient = await AsyncClient.create()

        # except Exception as err:
        #     print(f"Unexpected {err=}, {type(err)=}")
        #     print('Reintentando...')

    # except Exception as err:
    #     print(f"Unexpected {err=}, {type(err)=}")
    #     raise

    # except:
    #     print('Cerrando la conexion...')
    #     await aclient.close_connection()


    for pair in valid_pairs:
        if np_total_data[pair].shape[0] < 100:
            valid_pairs.remove(pair)
            np_total_data.pop(pair)

    RSI_points_min_max = {}
    BB_points_passed = {}
    BB_points_near = {}
    nans_RSI = np.empty(14)
    nans_BB = np.empty(19)
    nans_RSI.fill(np.nan)
    nans_BB.fill(np.nan)

    RSI_data = get_initial_rsi3(valid_pairs, np_total_data)
    BB_data = get_initial_bb(valid_pairs, np_total_data, factor)

    with open(folder_path_main + 'BB_points_passed_near_common'                \
              + rest_of_filename_main, 'w') as f:

        print('Número de ciclos: ' + str(limit) + '\n' + \
              'Intervalo de tiempo: ' + interval, file = f)

        for pair in valid_pairs:
            RSI_data[pair][2] = np.concatenate([nans_RSI, RSI_data[pair][2]])

            mgn_pct = 0.1
            margin = mgn_pct / 100

            BB_data[pair][0] = np.concatenate([nans_BB, BB_data[pair][0]])
            BB_data[pair][1] = np.concatenate([nans_BB, BB_data[pair][1]])

            BB_points_near[pair] =                                             \
            [(np_total_data[pair][:, [3]].reshape(-1) >                        \
              BB_data[pair][0].reshape(-1)) &                                  \
             (np_total_data[pair][:, [3]].reshape(-1) <=                       \
              (BB_data[pair][0].reshape(-1) * (1 + margin))),

            (np_total_data[pair][:, [2]].reshape(-1) <                         \
             BB_data[pair][1].reshape(-1)) &                                   \
            (np_total_data[pair][:, [2]].reshape(-1) >=                        \
             (BB_data[pair][1].reshape(-1) * (1 - margin)))]

            BB_points_passed[pair] =                                           \
            [np_total_data[pair][:, [3]].reshape(-1) <=                        \
             BB_data[pair][0].reshape(-1),
             np_total_data[pair][:, [2]].reshape(-1) >=                        \
            BB_data[pair][1].reshape(-1)]

            commons = np.count_nonzero(np.count_nonzero(np.transpose(          \
                      np.array(BB_points_near[pair])), axis = 1) == 2)

            print('\n' + '\n' + 'Par: ', pair, file = f)
            print('Ciclos: ', np_total_data[pair].shape[0], file = f)
            first_date_time =                                                  \
            dt.fromtimestamp(int(np_total_data[pair][0, [0]]) / 1e3)
            last_date_time =                                                   \
            dt.fromtimestamp(int(np_total_data[pair][-1, [6]]) / 1e3)
            print('Periodo total de datos analizados: ' + '\n'                 \
                  + 'Inicio: '                                                 \
                  + first_date_time.strftime('%d-%m-%Y  %H:%M:%S')             \
                  + '.{:03.0f}'.format(first_date_time.microsecond / 1e3)      \
                  + '\n' + 'Fin: '                                             \
                  + last_date_time.strftime('%d-%m-%Y  %H:%M:%S')              \
                  + '.{:03.0f}'.format(last_date_time.microsecond / 1e3),      \
                  file = f)

            BB_str_points_passed_1 = 'El par ' + pair                          \
            + ' no tiene puntos '
            BB_str_points_passed_2 = ' la banda '
            BB_str_points_passed_3 = ' de Bollinger ' + '\n'                   \
            + 'en el periodo de tiempo analizado'
            BB_str_points_passed_4 = ', por lo tanto, no existe un indice'     \
            + '\n' + 'para el ultimo punto que haya '                          \
            + 'cumplido con esta condicion.'
            BB_str_points_passed_5 = 'que puedan considerarse comunes a las '  \
            + 'bandas superior e inferior de Bollinger' + '\n'                 \
            + 'en el periodo de tiempo analizado.'

            try:
                print('BB_points_passed_low: ',
                      np.count_nonzero(BB_points_passed[pair][0]), file = f)
            except:
                print(BB_str_points_passed_1 + 'que hayan excedido'            \
                      + BB_str_points_passed_2 + 'inferior'                    \
                      + BB_str_points_passed_3 + '.', file = f)

            try:
                print('BB_points_passed_high: ',
                      np.count_nonzero(BB_points_passed[pair][1]), file = f)
            except:
                print(BB_str_points_passed_1 + 'que hayan excedido'            \
                      + BB_str_points_passed_2 + 'superior'                    \
                      + BB_str_points_passed_3 + '.', file = f)

            try:
                print('BB_points_passed_low_last_index: ',
                      np.transpose(BB_points_passed[pair][0].nonzero())[-1][0],
                      file = f)
            except:
                print(BB_str_points_passed_1 + 'que hayan excedido'            \
                      + BB_str_points_passed_2 + 'inferior'                    \
                      + BB_str_points_passed_3 + BB_str_points_passed_4 + '.',
                      file = f)

            try:
                print('BB_points_passed_high_last_index: ',
                      np.transpose(BB_points_passed[pair][1].nonzero())[-1][0],
                      file = f)
            except:
                print(BB_str_points_passed_1 + 'que hayan excedido'            \
                      + BB_str_points_passed_2 + 'superior'                    \
                      + BB_str_points_passed_3 + BB_str_points_passed_4 + '.',
                      file = f)

            try:
                print('BB_points_near_low: ',
                      np.count_nonzero(BB_points_near[pair][0]), file = f)
            except:
                print(BB_str_points_passed_1 + 'cercanos a'                    \
                      + BB_str_points_passed_2 + 'inferior'                    \
                      + BB_str_points_passed_3 + '.', file = f)

            try:
                print('BB_points_near_high: ',
                      np.count_nonzero(BB_points_near[pair][1]), file = f)
            except:
                print(BB_str_points_passed_1 + 'cercanos a'                    \
                      + BB_str_points_passed_2 + 'superior'                    \
                      + BB_str_points_passed_3 + '.', file = f)

            try:
                print('BB_points_near_low_last_index: ',
                      np.transpose(BB_points_near[pair][0].nonzero())[-1][0],
                      file = f)
            except:
                print(BB_str_points_passed_1 + 'cercanos a'                    \
                      + BB_str_points_passed_2 + 'inferior'                    \
                      + BB_str_points_passed_3 + BB_str_points_passed_4 + '.',
                      file = f)

            try:
                print('BB_points_near_high_last_index: ',
                      np.transpose(BB_points_near[pair][1].nonzero())[-1][0],
                      file = f)
            except:
                print(BB_str_points_passed_1 + 'cercanos a'                    \
                      + BB_str_points_passed_2 + 'superior'                    \
                      + BB_str_points_passed_3 + BB_str_points_passed_4 + '.',
                      file = f)

            try:
                print('BB_points_near_in_common: ', commons, file = f)
            except:
                print(BB_str_points_passed_1 + BB_str_points_passed_5,
                      file = f)

            RSI_points_min_max[pair] =                                         \
            [np.count_nonzero(RSI_data[pair][2][:].reshape(-1) <= RSI_min),
             np.count_nonzero(RSI_data[pair][2][:].reshape(-1) >= RSI_max)]

    write_headers_main(valid_pairs, interval, limit, folder_path_GENERAL,
                        rest_of_filename_main)
    write_headers_RSI(valid_pairs, interval, limit, folder_path_RSI,
                      rest_of_filename_RSI, RSI_min, RSI_max,
                      RSI_points_min_max)
    write_headers_BB(valid_pairs, interval, limit, folder_path_BB,
                     rest_of_filename_BB, mgn_pct,
                     BB_points_passed, BB_points_near)

    write_to_files_main(valid_pairs, folder_path_GENERAL,
                        rest_of_filename_main, np_total_data, precisions)
    write_to_files_RSI(valid_pairs, folder_path_RSI, rest_of_filename_RSI,
                        np_total_data, precisions, RSI_data)
    write_to_files_BB(valid_pairs, folder_path_BB, rest_of_filename_BB,
                        np_total_data, precisions, BB_data)

    bm = BinanceSocketManager(aclient)
    amps = bm.all_mark_price_socket()

    mark_price = {}
    RSI_data_update = {}
    BB_data_update = {}
    symbol_index = {}
    time_stamp = {}
    active_cycle_ordered_pairs = []
    active_order = False

    made_updates = 0
    with open(folder_path_main + 'RSI_alerts'                                  \
              + rest_of_filename_main, 'w') as RSI_alerts_f,                   \
    open(folder_path_main + 'BB_alerts'                                        \
         + rest_of_filename_main, 'w') as BB_alerts_f,                         \
    open(folder_path_main + 'BB_alerts_passed_high'                            \
         + rest_of_filename_main, 'w') as BB_alerts_passed_high_f,             \
    open(folder_path_main + 'BB_alerts_passed_low'                             \
         + rest_of_filename_main, 'w') as BB_alerts_passed_low_f,              \
    open(folder_path_main + 'BB_alerts_near_high'                              \
         + rest_of_filename_main, 'w') as BB_alerts_near_high_f,               \
    open(folder_path_main + 'BB_alerts_near_low'                               \
         + rest_of_filename_main, 'w') as BB_alerts_near_low_f,                \
    open(folder_path_main + 'RSI_alerts_under_30'                              \
         + rest_of_filename_main, 'w') as RSI_alerts_under_30_f,               \
    open(folder_path_main + 'RSI_alerts_under_20'                              \
         + rest_of_filename_main, 'w') as RSI_alerts_under_20_f,               \
    open(folder_path_main + 'RSI_alerts_under_10'                              \
         + rest_of_filename_main, 'w') as RSI_alerts_under_10_f,               \
    open(folder_path_main + 'RSI_alerts_over_70'                               \
         + rest_of_filename_main, 'w') as RSI_alerts_over_70_f,                \
    open(folder_path_main + 'RSI_alerts_over_80'                               \
         + rest_of_filename_main, 'w') as RSI_alerts_over_80_f,                \
    open(folder_path_main + 'RSI_alerts_over_90'                               \
         + rest_of_filename_main, 'w') as RSI_alerts_over_90_f:

        async with amps as tscm:

            while True:

                res = await tscm.recv()

                cycles_diff = {}
                for pair in valid_pairs:
                    symbol_index[pair] = next((index for (index, item) in      \
                                          enumerate(res['data'])               \
                                          if item['s'] == pair), None)

                    time_stamp[pair] =                                         \
                    int(res['data'][symbol_index[pair]]['E'] / 1e3)

                    cycles_diff[pair] = get_cycles_diff_vec(
                                  int(np_total_data[pair][-1, [6]] / 1e3) + 1,
                                                      time_stamp[pair],
                                                      interval)

                if any(val > 0 for val in cycles_diff.values()):
                    active_cycle_ordered_pairs = []
                    made_updates = made_updates + 1
                    print('Llevando a cabo actualizacion de datos...')
                    print('Actualizaciones llevadas a cabo: ',
                          made_updates)
                    print('\n', dt.now(), '\n')

                    if retrieve_mode == 'sync':
                        np_total_data_update =                                     \
                        obtain_data_sync_2(client, valid_pairs, interval,
                                            [v for k, v in cycles_diff.items()      \
                                            if v > 0][0] + 1, folder_path_main,
                                            rest_of_filename_main,
                                            mode = 'update', timestamp =            \
                                            int(np_total_data[[k                    \
                                            for k, v in cycles_diff.items()         \
                                            if v > 0][0]][-1, [6]] / 1e3) + 1)
                    else:
                        np_total_data_update =                                     \
                        await obtain_data2(aclient, valid_pairs, interval,
                                            [v for k, v in cycles_diff.items()      \
                                            if v > 0][0] + 1, folder_path_main,
                                            rest_of_filename_main,
                                            mode = 'update', timestamp =            \
                                            int(np_total_data[[k                    \
                                            for k, v in cycles_diff.items()         \
                                            if v > 0][0]][-1, [6]] / 1e3) + 1)

                    RSI_data_update =                                          \
                    get_updated_rsi2(valid_pairs,
                                     [v for k, v in cycles_diff.items()        \
                                     if v > 0][0], np_total_data,
                                     np_total_data_update, RSI_data)

                    BB_data_update =                                           \
                    get_updated_bb2(valid_pairs, np_total_data,
                                    np_total_data_update, factor)

                    for pair2 in valid_pairs:
                        np_total_data[pair2] =                                 \
                        np.append(np_total_data[pair2],
                                  np_total_data_update[pair2], axis=0)

                    for pair3 in valid_pairs:
                        RSI_data[pair3][0] = RSI_data_update[pair3][0]
                        RSI_data[pair3][1] = RSI_data_update[pair3][1]
                        RSI_data[pair3][2] = np.append(RSI_data[pair3][2],
                                             RSI_data_update[pair3][2])

                        BB_data[pair3][0] = np.append(BB_data[pair3][0],
                                            BB_data_update[pair3][0])
                        BB_data[pair3][1] = np.append(BB_data[pair3][1],
                                            BB_data_update[pair3][1])

                    write_to_files_main(valid_pairs, folder_path_GENERAL,
                                        rest_of_filename_main,
                                        np_total_data_update,
                                        precisions)

                    write_to_files_RSI(valid_pairs, folder_path_RSI,
                                       rest_of_filename_RSI,
                                       np_total_data_update,
                                       precisions, RSI_data_update)

                    write_to_files_BB(valid_pairs, folder_path_BB,
                                      rest_of_filename_BB,
                                      np_total_data_update,
                                      precisions, BB_data_update)

                else:

                    for pair in valid_pairs:

                        mark_price[pair] =                                     \
                        float(res['data'][symbol_index[pair]]['p'])
    
                        RSI_data_update[pair] =                                \
                        get_updated_rsi_live(np_total_data[pair][-1, [4]]      \
                                             .reshape(-1),
                        np.atleast_1d(mark_price[pair]), RSI_data[pair])
    
                        BB_data_update[pair] =                                 \
                        get_updated_bb_live(np_total_data[pair][-19:, [4]]     \
                                            .reshape(-1),
                        np.atleast_1d(mark_price[pair]), factor)





                    ts_int_values_list = [int(ts) for ts in time_stamp.values()]
    
                    different_time_stamps = np.unique(ts_int_values_list)
    
                    # Create lists of valid pairs for each unique timestamp
                    ts_keys_pairs_list_dict = {}
    
                    for ts in different_time_stamps:
                        ts_keys_pairs_list_dict[ts] = []
    
                        for pair in valid_pairs:
                            if ts == time_stamp[pair]:
                                ts_keys_pairs_list_dict[ts].append(pair)
    
                    ts_dict = {}
                    for ts in different_time_stamps:
                        ts_dict[ts] = {}
    
                        ts_dict[ts]['RSI_under_10'] = {}
                        ts_dict[ts]['RSI_under_20'] = {}
                        ts_dict[ts]['RSI_under_30'] = {}
                        ts_dict[ts]['RSI_over_90'] = {}
                        ts_dict[ts]['RSI_over_80'] = {}
                        ts_dict[ts]['RSI_over_70'] = {}
    
                        ts_dict[ts]['BB_passed_low_pcts'] = {}
                        ts_dict[ts]['BB_near_low_pcts'] = {}
                        ts_dict[ts]['BB_passed_high_pcts'] = {}
                        ts_dict[ts]['BB_near_high_pcts'] = {}
    
                        for pair in ts_keys_pairs_list_dict[ts]:
                            
                            if RSI_data_update[pair] < 10:
                                ts_dict[ts]['RSI_under_10'][pair] =                \
                                RSI_data_update[pair]
    
                            elif RSI_data_update[pair] < 20:
                                ts_dict[ts]['RSI_under_20'][pair] =                \
                                RSI_data_update[pair]
    
                            elif RSI_data_update[pair] < 30:
                                ts_dict[ts]['RSI_under_30'][pair] =                \
                                RSI_data_update[pair]
    
                            elif RSI_data_update[pair] > 90:
                                ts_dict[ts]['RSI_over_90'][pair] =                 \
                                RSI_data_update[pair]
    
                            elif RSI_data_update[pair] > 80:
                                ts_dict[ts]['RSI_over_80'][pair] =                 \
                                RSI_data_update[pair]
    
                            elif RSI_data_update[pair] > 70:
                                ts_dict[ts]['RSI_over_70'][pair] =                 \
                                RSI_data_update[pair]
    
                        ts_dict[ts]['RSI_under_10'] =                              \
                        dict(sorted(ts_dict[ts]['RSI_under_10'].items(),
                               key=lambda x:x[1]))
                        ts_dict[ts]['RSI_under_20'] =                              \
                        dict(sorted(ts_dict[ts]['RSI_under_20'].items(),
                               key=lambda x:x[1]))
                        ts_dict[ts]['RSI_under_30'] =                              \
                        dict(sorted(ts_dict[ts]['RSI_under_30'].items(),
                               key=lambda x:x[1]))
                        ts_dict[ts]['RSI_over_90'] =                               \
                        dict(sorted(ts_dict[ts]['RSI_over_90'].items(),
                               key=lambda x:x[1], reverse=True))
                        ts_dict[ts]['RSI_over_80'] =                               \
                        dict(sorted(ts_dict[ts]['RSI_over_80'].items(),
                               key=lambda x:x[1], reverse=True))
                        ts_dict[ts]['RSI_over_70'] =                               \
                        dict(sorted(ts_dict[ts]['RSI_over_70'].items(),
                               key=lambda x:x[1], reverse=True))
    
                        for pair in ts_keys_pairs_list_dict[ts]:
    
                            if  mark_price[pair] <= BB_data_update[pair][0]:
    
                                ts_dict[ts]['BB_passed_low_pcts'][pair] =          \
                                (abs(mark_price[pair] - BB_data_update[pair][0]) / \
                                 BB_data_update[pair][0]) * 100
    
                            elif (mark_price[pair] > BB_data_update[pair][0])                  \
                            & (mark_price[pair] <=                                 \
                            BB_data_update[pair][0] * (1 + margin)):
    
                                ts_dict[ts]['BB_near_low_pcts'][pair] =            \
                                (abs(mark_price[pair] - BB_data_update[pair][0]) / \
                                 BB_data_update[pair][0]) * 100
    
                            elif  mark_price[pair] >= BB_data_update[pair][1]:
    
                                ts_dict[ts]['BB_passed_high_pcts'][pair] =         \
                                (abs(mark_price[pair] - BB_data_update[pair][1]) / \
                                 BB_data_update[pair][1]) * 100
    
                            elif (mark_price[pair] < BB_data_update[pair][1])                  \
                            & (mark_price[pair] >=                                 \
                            BB_data_update[pair][1] * (1 - margin)):
    
                                ts_dict[ts]['BB_near_high_pcts'][pair] =           \
                                (abs(mark_price[pair] - BB_data_update[pair][1]) / \
                                 BB_data_update[pair][1]) * 100
    
                        ts_dict[ts]['BB_passed_low_pcts'] =                        \
                        dict(sorted(ts_dict[ts]['BB_passed_low_pcts'].items(),
                                key=lambda x:x[1], reverse=True))
                        ts_dict[ts]['BB_near_low_pcts'] =                          \
                        dict(sorted(ts_dict[ts]['BB_near_low_pcts'].items(),
                                key=lambda x:x[1]))
                        ts_dict[ts]['BB_passed_high_pcts'] =                       \
                        dict(sorted(ts_dict[ts]['BB_passed_high_pcts'].items(),
                                key=lambda x:x[1], reverse=True))
                        ts_dict[ts]['BB_near_high_pcts'] =                         \
                        dict(sorted(ts_dict[ts]['BB_near_high_pcts'].items(),
                                key=lambda x:x[1]))

                    RSI_str_sp_1 = 'El par '
                    RSI_str_sp_lt = ' tiene un valor de RSI menor que '
                    RSI_str_sp_gt = ' tiene un valor de RSI mayor que '
                    RSI_str_mp_1 = 'Los pares:' + '\n'
                    RSI_str_mp_lt =  '\n' + 'Tienen valores de RSI menores que '
                    RSI_str_mp_gt = '\n' + 'Tienen valores de RSI mayores que '
    
                    for ts in different_time_stamps:
    
                        date_time = dt.fromtimestamp(ts)
                        date_time_string = '\n' + 'Fecha y hora: '                 \
                        + date_time.strftime('%d-%m-%Y  %H:%M:%S')                 \
                        + '.{:03.0f}'.format(date_time.microsecond / 1e3) + '\n'
    
                        if len(ts_dict[ts]['RSI_under_10']) > 0:
                            if len(ts_dict[ts]['RSI_under_10']) == 1:
                                RSI_under_10_str_sp = RSI_str_sp_1                 \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_under_10'].keys())])         \
                                + RSI_str_sp_lt + '10.' + date_time_string
                                print(RSI_under_10_str_sp,
                                      file = RSI_alerts_under_10_f)
                                print(RSI_under_10_str_sp,
                                      file = RSI_alerts_f)
                            elif len(ts_dict[ts]['RSI_under_10']) > 1:
                                RSI_under_10_str_mp = RSI_str_mp_1                 \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_under_10'].keys())])         \
                                + RSI_str_mp_lt + '10.' + date_time_string
                                print(RSI_under_10_str_mp,
                                      file = RSI_alerts_under_10_f)
                                print(RSI_under_10_str_mp,
                                      file = RSI_alerts_f)
    
                        if len(ts_dict[ts]['RSI_under_20']) > 0:
                            if len(ts_dict[ts]['RSI_under_20']) == 1:
                                RSI_under_20_str_sp = RSI_str_sp_1                 \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_under_20'].keys())])         \
                                + RSI_str_sp_lt + '20.' + date_time_string
                                print(RSI_under_20_str_sp,
                                      file = RSI_alerts_under_20_f)
                                print(RSI_under_20_str_sp,
                                      file = RSI_alerts_f)
                            elif len(ts_dict[ts]['RSI_under_20']) > 1:
                                RSI_under_20_str_mp = RSI_str_mp_1                 \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_under_20'].keys())])         \
                                + RSI_str_mp_lt + '20.' + date_time_string
                                print(RSI_under_20_str_mp,
                                      file = RSI_alerts_under_20_f)
                                print(RSI_under_20_str_mp,
                                      file = RSI_alerts_f)
    
                        if len(ts_dict[ts]['RSI_under_30']) > 0:
                            if len(ts_dict[ts]['RSI_under_30']) == 1:
                                RSI_under_30_str_sp = RSI_str_sp_1                 \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_under_30'].keys())])         \
                                + RSI_str_sp_lt + '30.' + date_time_string
                                print(RSI_under_30_str_sp,
                                      file = RSI_alerts_under_30_f)
                                print(RSI_under_30_str_sp,
                                      file = RSI_alerts_f)
                            elif len(ts_dict[ts]['RSI_under_30']) > 1:
                                RSI_under_30_str_mp = RSI_str_mp_1                 \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_under_30'].keys())])         \
                                + RSI_str_mp_lt + '30.' + date_time_string
                                print(RSI_under_30_str_mp,
                                      file = RSI_alerts_under_30_f)
                                print(RSI_under_30_str_mp,
                                      file = RSI_alerts_f)
    
                        if len(ts_dict[ts]['RSI_over_90']) > 0:
                            if len(ts_dict[ts]['RSI_over_90']) == 1:
                                RSI_over_90_str_sp = RSI_str_sp_1                  \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_over_90'].keys())])          \
                                + RSI_str_sp_gt + '90.' + date_time_string
                                print(RSI_over_90_str_sp,
                                      file = RSI_alerts_over_90_f)
                                print(RSI_over_90_str_sp,
                                      file = RSI_alerts_f)
                            elif len(ts_dict[ts]['RSI_over_90']) > 1:
                                RSI_over_90_str_mp = RSI_str_mp_1                  \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_over_90'].keys())])          \
                                + RSI_str_mp_gt + '90.' + date_time_string
                                print(RSI_over_90_str_mp,
                                      file = RSI_alerts_over_90_f)
                                print(RSI_over_90_str_mp,
                                      file = RSI_alerts_f)
    
                        if len(ts_dict[ts]['RSI_over_80']) > 0:
                            if len(ts_dict[ts]['RSI_over_80']) == 1:
                                RSI_over_80_str_sp = RSI_str_sp_1                  \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_over_80'].keys())])          \
                                + RSI_str_sp_gt + '80.' + date_time_string
                                print(RSI_over_80_str_sp,
                                      file = RSI_alerts_over_80_f)
                                print(RSI_over_80_str_sp,
                                      file = RSI_alerts_f)
                            elif len(ts_dict[ts]['RSI_over_80']) > 1:
                                RSI_over_80_str_mp = RSI_str_mp_1                  \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_over_80'].keys())])          \
                                + RSI_str_mp_gt + '80.' + date_time_string
                                print(RSI_over_80_str_mp,
                                      file = RSI_alerts_over_80_f)
                                print(RSI_over_80_str_mp,
                                      file = RSI_alerts_f)
    
                        if len(ts_dict[ts]['RSI_over_70']) > 0:
                            if len(ts_dict[ts]['RSI_over_70']) == 1:
                                RSI_over_70_str_sp = RSI_str_sp_1                  \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_over_70'].keys())])          \
                                + RSI_str_sp_gt + '70.' + date_time_string
                                print(RSI_over_70_str_sp,
                                      file = RSI_alerts_over_70_f)
                                print(RSI_over_70_str_sp,
                                      file = RSI_alerts_f)
                            elif len(ts_dict[ts]['RSI_over_70']) > 1:
                                RSI_over_70_str_mp = RSI_str_mp_1                  \
                                + '\n'.join([pair + ' ('                           \
                                + str(RSI_data_update[pair]) + ')' for pair in     \
                                list(ts_dict[ts]['RSI_over_70'].keys())])          \
                                + RSI_str_mp_gt + '70.' + date_time_string
                                print(RSI_over_70_str_mp,
                                      file = RSI_alerts_over_70_f)
                                print(RSI_over_70_str_mp,
                                      file = RSI_alerts_f)
    
                    BB_str_lt = 'menor'
                    BB_str_gt = 'mayor'
                    BB_str_near = 'cercano'
                    BB_str_sp_pair = 'El par '
                    BB_str_mp_pair = 'Los pares:' + '\n'
                    BB_str_sp_price = ' tiene un precio '
                    BB_str_mp_price = '\n' + 'Tienen un precio '
                    BB_str_lbb = 'la banda inferior de Bollinger'
                    BB_str_ubb = 'la banda superior de Bollinger'
                    BB_str_sp_mgn = ' por el margen especificado.'
                    BB_str_mp_mgn = ' por los margenes especificados.'
    
                    for ts in different_time_stamps:
    
                        date_time = dt.fromtimestamp(ts)
                        date_time_string = '\n' + 'Fecha y hora: '                 \
                        + date_time.strftime('%d-%m-%Y  %H:%M:%S')                 \
                        + '.{:03.0f}'.format(date_time.microsecond / 1e3) + '\n'
    
                        if len(ts_dict[ts]['BB_passed_low_pcts']) > 0:
                            if len(ts_dict[ts]['BB_passed_low_pcts']) == 1:
                                BB_passed_low_pcts_str_sp = BB_str_sp_pair         \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_passed_low_pcts'][pair])     \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_passed_low_pcts'].keys())])   \
                                + BB_str_sp_price + BB_str_lt + ' que '            \
                                + BB_str_lbb + BB_str_sp_mgn + date_time_string
                                print(BB_passed_low_pcts_str_sp,
                                      file = BB_alerts_passed_low_f)
                                print(BB_passed_low_pcts_str_sp,
                                      file = BB_alerts_f)
                            elif len(ts_dict[ts]['BB_passed_low_pcts']) > 1:
                                BB_passed_low_pcts_str_mp = BB_str_mp_pair         \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_passed_low_pcts'][pair])     \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_passed_low_pcts'].keys())])   \
                                + BB_str_mp_price + BB_str_lt + ' que '            \
                                + BB_str_lbb + BB_str_mp_mgn + date_time_string
                                print(BB_passed_low_pcts_str_mp,
                                      file = BB_alerts_passed_low_f)
                                print(BB_passed_low_pcts_str_mp,
                                      file = BB_alerts_f)
    
                        if len(ts_dict[ts]['BB_near_low_pcts']) > 0:
                            if len(ts_dict[ts]['BB_near_low_pcts']) == 1:
                                BB_near_low_pcts_str_sp = BB_str_sp_pair           \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_near_low_pcts'][pair])       \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_near_low_pcts'].keys())])     \
                                + BB_str_sp_price + BB_str_near + ' a '            \
                                + BB_str_lbb + BB_str_sp_mgn + date_time_string
                                print(BB_near_low_pcts_str_sp,
                                      file = BB_alerts_near_low_f)
                                print(BB_near_low_pcts_str_sp,
                                      file = BB_alerts_f)
                            elif len(ts_dict[ts]['BB_near_low_pcts']) > 1:
                                BB_near_low_pcts_str_mp = BB_str_mp_pair           \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_near_low_pcts'][pair])       \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_near_low_pcts'].keys())])     \
                                + BB_str_mp_price + BB_str_near + ' a '            \
                                + BB_str_lbb + BB_str_mp_mgn + date_time_string
                                print(BB_near_low_pcts_str_mp,
                                      file = BB_alerts_near_low_f)
                                print(BB_near_low_pcts_str_mp,
                                      file = BB_alerts_f)
    
                        if len(ts_dict[ts]['BB_passed_high_pcts']) > 0:
                            if len(ts_dict[ts]['BB_passed_high_pcts']) == 1:
                                BB_passed_high_pcts_str_sp = BB_str_sp_pair        \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_passed_high_pcts'][pair])    \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_passed_high_pcts'].keys())])  \
                                + BB_str_sp_price + BB_str_gt + ' que '            \
                                + BB_str_ubb + BB_str_sp_mgn + date_time_string
                                print(BB_passed_high_pcts_str_sp,
                                      file = BB_alerts_passed_high_f)
                                print(BB_passed_high_pcts_str_sp,
                                      file = BB_alerts_f)
                            elif len(ts_dict[ts]['BB_passed_high_pcts']) > 1:
                                BB_passed_high_pcts_str_mp = BB_str_mp_pair        \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_passed_high_pcts'][pair])    \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_passed_high_pcts'].keys())])  \
                                + BB_str_mp_price + BB_str_gt + ' que '            \
                                + BB_str_ubb + BB_str_mp_mgn + date_time_string
                                print(BB_passed_high_pcts_str_mp,
                                      file = BB_alerts_passed_high_f)
                                print(BB_passed_high_pcts_str_mp,
                                      file = BB_alerts_f)
    
                        if len(ts_dict[ts]['BB_near_high_pcts']) > 0:
                            if len(ts_dict[ts]['BB_near_high_pcts']) == 1:
                                BB_near_high_pcts_str_sp = BB_str_sp_pair          \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_near_high_pcts'][pair])      \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_near_high_pcts'].keys())])    \
                                + BB_str_sp_price + BB_str_near + ' a '            \
                                + BB_str_ubb + BB_str_sp_mgn + date_time_string
                                print(BB_near_high_pcts_str_sp,
                                      file = BB_alerts_near_high_f)
                                print(BB_near_high_pcts_str_sp,
                                      file = BB_alerts_f)
                            elif len(ts_dict[ts]['BB_near_high_pcts']) > 1:
                                BB_near_high_pcts_str_mp = BB_str_mp_pair          \
                                + '\n'.join([pair + ' ('                           \
                                + str(ts_dict[ts]['BB_near_high_pcts'][pair])      \
                                + '%)'                                             \
                                for pair in                                        \
                                list(ts_dict[ts]['BB_near_high_pcts'].keys())])    \
                                + BB_str_mp_price + BB_str_near + ' a '            \
                                + BB_str_ubb + BB_str_mp_mgn + date_time_string
                                print(BB_near_high_pcts_str_mp,
                                      file = BB_alerts_near_high_f)
                                print(BB_near_high_pcts_str_mp,
                                      file = BB_alerts_f)

                    # Verificar que no haya una orden activa
                    if active_order == False:


                        BB_passed_high_pcts_all_ts_merged =                    \
                        ts_dict[different_time_stamps[0]]                      \
                        ['BB_passed_high_pcts'].copy()
                        BB_passed_low_pcts_all_ts_merged =                     \
                        ts_dict[different_time_stamps[0]]                      \
                        ['BB_passed_low_pcts'].copy()
                        RSI_over_70_all_ts_merged =                            \
                        ts_dict[different_time_stamps[0]]                      \
                        ['RSI_over_70'].copy()
                        RSI_over_80_all_ts_merged =                            \
                        ts_dict[different_time_stamps[0]]                      \
                        ['RSI_over_80'].copy()
                        RSI_over_90_all_ts_merged =                            \
                        ts_dict[different_time_stamps[0]]                      \
                        ['RSI_over_90'].copy()
                        RSI_under_30_all_ts_merged =                           \
                        ts_dict[different_time_stamps[0]]                      \
                        ['RSI_under_30'].copy()
                        RSI_under_20_all_ts_merged =                           \
                        ts_dict[different_time_stamps[0]]                      \
                        ['RSI_under_20'].copy()
                        RSI_under_10_all_ts_merged =                           \
                        ts_dict[different_time_stamps[0]]                      \
                        ['RSI_under_10'].copy()

                        if len(different_time_stamps) > 1:
                            for ts in range(1, len(different_time_stamps) + 1):
                                BB_passed_high_pcts_all_ts_merged              \
                                .update(ts_dict[ts]['BB_passed_high_pcts'])
                                BB_passed_low_pcts_all_ts_merged               \
                                .update(ts_dict[ts]['BB_passed_low_pcts'])
                                RSI_over_70_all_ts_merged                      \
                                .update(ts_dict[ts]['RSI_over_70'])
                                RSI_over_80_all_ts_merged                      \
                                .update(ts_dict[ts]['RSI_over_80'])
                                RSI_over_90_all_ts_merged                      \
                                .update(ts_dict[ts]['RSI_over_90'])
                                RSI_under_30_all_ts_merged                     \
                                .update(ts_dict[ts]['RSI_under_30'])
                                RSI_under_20_all_ts_merged                     \
                                .update(ts_dict[ts]['RSI_under_20'])
                                RSI_under_10_all_ts_merged                     \
                                .update(ts_dict[ts]['RSI_under_10'])
    
                        BB_passed_high_pcts_all_ts_merged =                    \
                        dict(sorted(BB_passed_high_pcts_all_ts_merged.items(),
                                key=lambda x:x[1], reverse=True))
                        BB_passed_low_pcts_all_ts_merged =                     \
                        dict(sorted(BB_passed_low_pcts_all_ts_merged.items(),
                                key=lambda x:x[1], reverse=True))
                        RSI_over_70_all_ts_merged =                            \
                        dict(sorted(RSI_over_70_all_ts_merged.items(),
                                key=lambda x:x[1], reverse=True))
                        RSI_over_80_all_ts_merged =                            \
                        dict(sorted(RSI_over_80_all_ts_merged.items(),
                                key=lambda x:x[1], reverse=True))
                        RSI_over_90_all_ts_merged =                            \
                        dict(sorted(RSI_over_90_all_ts_merged.items(),
                                key=lambda x:x[1], reverse=True))
                        RSI_under_30_all_ts_merged =                           \
                        dict(sorted(RSI_under_30_all_ts_merged.items(),
                                key=lambda x:x[1]))
                        RSI_under_20_all_ts_merged =                           \
                        dict(sorted(RSI_under_20_all_ts_merged.items(),
                                key=lambda x:x[1]))
                        RSI_under_10_all_ts_merged =                           \
                        dict(sorted(RSI_under_10_all_ts_merged.items(),
                                key=lambda x:x[1]))
    
                        RSI_over_all_ts_merged =                               \
                        RSI_over_90_all_ts_merged.copy()
                        RSI_over_all_ts_merged                                 \
                        .update(RSI_over_80_all_ts_merged)
                        RSI_over_all_ts_merged                                 \
                        .update(RSI_over_70_all_ts_merged)
                        RSI_under_all_ts_merged =                              \
                        RSI_under_10_all_ts_merged.copy()
                        RSI_under_all_ts_merged                                \
                        .update(RSI_under_20_all_ts_merged)
                        RSI_under_all_ts_merged                                \
                        .update(RSI_under_30_all_ts_merged)
    
                        selected_pair = {}
                        only_one = False
                        high_and_low = False
                        if ((len(BB_passed_high_pcts_all_ts_merged) > 0) and   \
                        (len(RSI_over_all_ts_merged) > 0)) and                 \
                        ((len(BB_passed_low_pcts_all_ts_merged) > 0) and       \
                        (len(RSI_under_all_ts_merged) > 0)):
    
                            high_and_low = True
    
                            if list(BB_passed_high_pcts_all_ts_merged          \
                            .values())[0] >                                    \
                            list(BB_passed_low_pcts_all_ts_merged.values())[0]:
                                # selected_pair[list(                                \
                                # BB_passed_high_pcts_all_ts_merged.keys())[0]] =    \
                                # list(BB_passed_high_pcts_all_ts_merged.values())[0]
                                selected_pair['pair'] =                        \
                                list(BB_passed_high_pcts_all_ts_merged         \
                                     .keys())[0]





                                # print('\n', '1_selected_pair: ', selected_pair, '\n')
                                # print('\n', '1_list(selected_pair.keys())[0]: ', list(selected_pair.keys())[0], '\n')

                                # print('\n', 'list(BB_passed_low_pcts_all_ts_merged.keys()): ',
                                #       list(BB_passed_low_pcts_all_ts_merged.keys()), '\n')

                                print('\n', '1_selected_pair: ', selected_pair, '\n')

                                print('\n', '1_BB_passed_high_pcts_all_ts_merged: ',
                                      BB_passed_high_pcts_all_ts_merged, '\n')
                                print('\n', '1_BB_passed_low_pcts_all_ts_merged: ',
                                      BB_passed_low_pcts_all_ts_merged, '\n')
                                print('\n', '1_RSI_over_all_ts_merged: ',
                                      RSI_over_all_ts_merged, '\n')
                                print('\n', '1_RSI_under_all_ts_merged: ',
                                      RSI_under_all_ts_merged, '\n')





                                # selected_pair['price'] =                       \
                                # mark_price[list(selected_pair.keys())[0]]

                                selected_pair['price'] =                       \
                                mark_price[selected_pair['pair']]

                                selected_pair['side'] = 'sell'
    
                            else:
                                # selected_pair[list(                                \
                                # BB_passed_low_pcts_all_ts_merged.keys())[0]] =     \
                                # list(BB_passed_low_pcts_all_ts_merged.values())[0]
                                selected_pair['pair'] =                        \
                                list(BB_passed_low_pcts_all_ts_merged          \
                                     .keys())[0]

                                # print('\n', '2_selected_pair: ', selected_pair, '\n')
                                # print('\n', '2_list(selected_pair.keys())[0]: ', list(selected_pair.keys())[0], '\n')





                                print('\n', '2_selected_pair: ', selected_pair, '\n')

                                print('\n', '2_BB_passed_high_pcts_all_ts_merged: ',
                                      BB_passed_high_pcts_all_ts_merged, '\n')
                                print('\n', '2_BB_passed_low_pcts_all_ts_merged: ',
                                      BB_passed_low_pcts_all_ts_merged, '\n')
                                print('\n', '2_RSI_over_all_ts_merged: ',
                                      RSI_over_all_ts_merged, '\n')
                                print('\n', '2_RSI_under_all_ts_merged: ',
                                      RSI_under_all_ts_merged, '\n')





                                # selected_pair['price'] =                       \
                                # mark_price[list(selected_pair.keys())[0]]

                                selected_pair['price'] =                       \
                                mark_price[selected_pair['pair']]

                                selected_pair['side'] = 'buy'
    
                        elif ((len(BB_passed_high_pcts_all_ts_merged) > 0) and \
                        (len(RSI_over_all_ts_merged) > 0)) or                  \
                        ((len(BB_passed_low_pcts_all_ts_merged) > 0) and       \
                        (len(RSI_under_all_ts_merged) > 0)):
    
                            only_one = True
    
                            if ((len(BB_passed_high_pcts_all_ts_merged) > 0)   \
                                and (len(RSI_over_all_ts_merged) > 0)):
                                # selected_pair[list(                                \
                                # BB_passed_high_pcts_all_ts_merged.keys())[0]] =    \
                                # list(BB_passed_high_pcts_all_ts_merged.values())[0]
                                selected_pair['pair'] =                        \
                                list(BB_passed_high_pcts_all_ts_merged         \
                                     .keys())[0]

                                # print('\n', '3_selected_pair: ', selected_pair, '\n')
                                # print('\n', '3_list(selected_pair.keys())[0]: ', list(selected_pair.keys())[0], '\n')





                                print('\n', '3_selected_pair: ', selected_pair, '\n')

                                print('\n', '3_BB_passed_high_pcts_all_ts_merged: ',
                                      BB_passed_high_pcts_all_ts_merged, '\n')
                                print('\n', '3_BB_passed_low_pcts_all_ts_merged: ',
                                      BB_passed_low_pcts_all_ts_merged, '\n')
                                print('\n', '3_RSI_over_all_ts_merged: ',
                                      RSI_over_all_ts_merged, '\n')
                                print('\n', '3_RSI_under_all_ts_merged: ',
                                      RSI_under_all_ts_merged, '\n')





                                # selected_pair['price'] =                       \
                                # mark_price[list(selected_pair.keys())[0]]

                                selected_pair['price'] =                       \
                                mark_price[selected_pair['pair']]

                                selected_pair['side'] = 'sell'
    
                            else:
                                # selected_pair[list(                                \
                                # BB_passed_low_pcts_all_ts_merged.keys())[0]] =     \
                                # list(BB_passed_low_pcts_all_ts_merged.values())[0]
                                selected_pair['pair'] =                        \
                                list(BB_passed_low_pcts_all_ts_merged          \
                                     .keys())[0]

                                # print('\n', '4_selected_pair: ', selected_pair, '\n')
                                # # print('\n', '4_list(selected_pair.keys())[0]: ', list(selected_pair.keys())[0], '\n')
                                # print('\n', '4_list(selected_pair.keys())[0]: ', selected_pair['pair'], '\n')

                                # print('\n', 'list(BB_passed_low_pcts_all_ts_merged.keys()): ',
                                #       list(BB_passed_low_pcts_all_ts_merged.keys()), '\n')
 




                                print('\n', '3_selected_pair: ', selected_pair, '\n')

                                print('\n', '3_BB_passed_high_pcts_all_ts_merged: ',
                                      BB_passed_high_pcts_all_ts_merged, '\n')
                                print('\n', '3_BB_passed_low_pcts_all_ts_merged: ',
                                      BB_passed_low_pcts_all_ts_merged, '\n')
                                print('\n', '3_RSI_over_all_ts_merged: ',
                                      RSI_over_all_ts_merged, '\n')
                                print('\n', '3_RSI_under_all_ts_merged: ',
                                      RSI_under_all_ts_merged, '\n')





                               # list(BB_passed_low_pcts_all_ts_merged.keys())

                                # selected_pair['price'] =                       \
                                # mark_price[list(selected_pair.keys())[0]]

                                selected_pair['price'] =                       \
                                mark_price[selected_pair['pair']]

                                selected_pair['side'] = 'buy'

                        if high_and_low or only_one:

                            if high_and_low:
                                print('high_and_low = true')

                            if only_one:
                                print('only_one = true')


                            active_order = True
                            print('Colocando orden para el par ' +             \
                                  selected_pair['pair'] + ' al precio: ' +     \
                                  str(selected_pair['price']))
                            active_cycle_ordered_pairs                         \
                            .append(selected_pair['pair'])







    # usdt = 5
    # price = 101

    # quantity = usdt / price
    
    # limit_order_long = client.futures_create_order(
    # symbol='bnbusdt',
    # side='BUY',
    # type='LIMIT',
    # quantity=quantity,
    # timeInForce='GTC',
    # price=price)



    # take_profit_price = 120

    # sell_gain_market_long = client.futures_create_order(
    # symbol='bnbusdt',
    # side='SELL',
    # type='TAKE_PROFIT_MARKET',
    # stopPrice=take_profit_price,
    # closePosition=True)



    # stop_loss_price = 800

    # sell_loss_market_long = client.futures_create_order(
    # symbol='BNBUSDT',
    # side='SELL',
    # type='STOP_MARKET',
    # # positionSide='LONG',
    # # quantity=quantity,
    # stopPrice=stop_loss_price,
    # closePosition=True)







    print('Tiempo: ' + str((time.time() - start)) )

    print('\n', 'Hora de finalización: ', dt.now())

    await aclient.close_connection()



if __name__ == "__main__":

    asyncio.create_task(main())
