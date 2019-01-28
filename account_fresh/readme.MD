1. ac_tb_group 科目余额表
2. account_invoice 发票里面添加源发票，同时复写action_invoice_open_invoice，action_move_create_invoice，_prepare_invoice_line_from_po_line
3. account_move 添加在选择现金及银行时，必须选择现金流量表行
4. account_payment 添加现金流量表行，更改传递函数，将cash_id添加进去
5. account_tax 修改保留的位数，为8位
6. actual_invoice 真实发票管理：新增一个发票的录入界面，和系统的发票界面类似，只是字段有些许差异
                  在发票行上面，添加两个按钮，一个核销，一个查看
                  核销 cancel_after_verify
                  查看 view_after_verify
                  验证 verify_valid
                  核销 verify_final
7. fleet_vehicle 车辆上面添加供应商，同时，相同公司，不同创建相同的车牌
8. hr_employee 修改为当前公司，不能创建相同的员工
9. hr_expense 添加不含税单价，修改含税单价，不含税单价由含税单价计算得来
10. hr_expense_payment 添加现金流量表行
11. models 复写_onchange_eval，修改if not res or res == [None]
12. product_uom 修改精度
13. purchase  添加负责人和订单号，添加含税价格，重写不含税价格，不含税价格改为计算字段
              price_unit = contain_tax_price / ((taxes_id.amount / 100.0) + 1.0)
              添加车牌号
14. res_company 添加公司允许在仓库里面扫描操作时，可以将数量，在点击的时候补全
15. res_partner 当前公司下，不能创建相同的客户
16. sale 添加含税价格，车牌号，订单分类，共配专车字段
        不含税价格更改为计算字段
        复写 _prepare_invoice_line ，主要因为添加了车牌号等字段
17. stock 添加产品所属者
18. stock_pack_operation 在使用条码枪扫描的时候，当公司里面设置的允许确认所有数量，即可在点击的时候出现全部按钮
