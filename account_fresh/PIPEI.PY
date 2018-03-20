#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import csv

res1 = []
res2 = []

res_render1 = csv.reader(open('/home/jx/Desktop/need_update.csv', encoding='utf-8'))

res_render2 = csv.reader(open('/home/jx/Desktop/account.csv', encoding='utf-8'))

for row in res_render1:
    res1.append(row)
# print(res1)
for row in res_render2:
    res2.append(row)

for i,j in enumerate(res1[1:]):
    for x,y in enumerate(res2[1:]):
        if j[1] in y[2]:
            y[1] = j[0]
            if y[1] == '运输费-外部X_阳平直配（运营)':
                y[3] = '主营业务成本_运输费-外部X_阳平直配'
            else:
                y[3] = '主营业务成本_运输费-外部X_阳平转运'
        else:
            if y[1] == '运输费-外部X_阳平直配（运营)':
                y[3] = '主营业务成本_运输费-外部X_阳平直配'
            else:
                y[3] = '主营业务成本_运输费-外部X_阳平转运'

csvfile = open('/home/jx/Desktop/new.csv','w',newline='')
writer = csv.writer(csvfile)
for i in range(len(res2)):
    writer.writerow(res2[i])

csvfile.close()