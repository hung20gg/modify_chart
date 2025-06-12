The table `fake_tool` consists of 12 fields:

- PRD_ID (int): Date information in the format YYYYMMDD.
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

The primary key consists of 4 fields: `PRD_ID`, `OBJ_NAME`, `SERVICE_NAME`, and `CYCLE`. This means each record represents the data for a specific indicator in a province for a specific day/month/quarter/year.

Relationship between `PRD_ID` and `CYCLE`:
If `CYCLE = 'day'`, `PRD_ID` represents a specific date.
If `CYCLE IN ['month', 'quarter', 'year']`, `PRD_ID` represents the first day of that cycle. For example, if `CYCLE = 'month'` and `PRD_ID = 20240101`, the data pertains to January 2024.