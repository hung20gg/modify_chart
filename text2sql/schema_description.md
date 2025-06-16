The table `fake_tool` consists of 12 fields:

- DATE (int): Date information. Store as YYYY-MM-DD
- OBJ_NAME (str): Name of the province (one of - the 63 provinces/cities in Vietnam).
- SERVICE_NAME (str): Name of the statistical indicator (there are 13 distinct indicators).
- CYCLE (str): Time cycle, one of four values: ['day', 'month', 'quarter', 'year'].
- PLAN (float): Planned value for the indicator in the province.
- PLAN_ACC (float): Accumulated planned value for the indicator in the province.
- VAL (float): Actual value achieved for the indicator in the province.
- VAL_ACC (float): Accumulated actual value for the indicator in the province.
- P_PLAN (float): Percentage of completion for the indicator in the province.
- P_PLAN_ACC (float): Accumulated percentage of completion for the indicator in the province.
- LAST_VAL_YEAR (float): Actual value of the indicator for the province in the previous year.
- LAST_VAL_ACC_YEAR (float): Accumulated actual value of the indicator for the province in the previous year.
Notes:

The primary key consists of 4 fields: `DATE`, `OBJ_NAME`, `SERVICE_NAME`, and `CYCLE`. This means each record represents the data for a specific indicator in a province for a specific day/month/quarter/year.

Relationship between `DATE` and `CYCLE`:
If `CYCLE = 'day'`, `DATE` represents a specific date.
If `CYCLE IN ['month', 'quarter', 'year']`, `DATE` represents the first day of that cycle. For example, if `CYCLE = 'month'` and `DATE = 2024-01-01`, the data pertains to January 2024.


### Example queries
1. Average Completion Percentage for Each Indicator Across All Provinces and Cycles:
```sql
SELECT SERVICE_NAME, AVG(P_PLAN) as avg_completion_percentage
FROM fake_tool
GROUP BY SERVICE_NAME
order by avg_completion_percentage;
```

Result:

| SERVICE_NAME | AVG_COMPLETION_PERCENTAGE |
|--------------|---------------------------|
| Thuê bao 4G tăng thêm | 81.19 |
| DT dịch vụ nhóm DV của VTT | 109.44 |
| Tiêu dùng thực di động (TT+TS) | 113.41 |
| FTTx - TB thực tăng/giảm | 181.21 |
| DT dịch vụ nhóm DV của VDS | 327.99 |
| DT dịch vụ nhóm DV của VTS | 414.95 |
| Thuê bao thực tăng thêm | 780.57 |
| Thuê bao Register tăng thêm | 994.78 |
| Thuê bao 4G (LK toàn mạng) | - |
| Di động Lũy kế | - |
| Tổng TB thực lũy kế | - |
| FTTx - TB thực lũy kế | - |

Notice that these will be every avaliable field in SERVICE_NAME


2. Revenue of each data of Ha Noi in 12/2024 and in the same December of the preivous year
```sql
SELECT SUM(VAL) as total_value_2024, SUM(LAST_VAL_YEAR) as total_value_2023, DATE
FROM fake_tool
WHERE OBJ_NAME = 'Hà Nội'

AND DATE BETWEEN '2024-12-01' AND '2024-12-31'
group by OBJ_NAME, DATE
```

Reasoning step-by-step and generate SQL query

## Note:
- You must not change the object name in the SQL
- Avoid select *
- When asking for total revenue, or without any declare on revenue, assume asking for total revenue of all services (use groupby for this)
- You should make the columnn name easy to understand (val_accumulate instead of val_acc)
- TP HCM or Hồ Chí Minh should be TPHCM 
- Remember to use the columns ('LAST_VAL') when being asked to compare with last year, specially on comparision between current and last year. And do not change the DATE range in these question.
- Without referring date, assume the CYCLE is month