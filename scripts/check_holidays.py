from backend.routes.schedule import is_holiday

check_dates = [
    '2026-01-03',  # 元旦-节假日
    '2026-01-04',  # 元旦后补班
    '2026-02-14',  # 春节前补班
    '2026-02-15',  # 春节
    '2026-02-28',  # 春节后补班
    '2026-05-09',  # 劳动节后补班
    '2026-10-10',  # 国庆后补班
    '2026-04-04',  # 清明节
    '2026-07-04',  # 非节假日示例
]

for d in check_dates:
    print(d, is_holiday(d))
