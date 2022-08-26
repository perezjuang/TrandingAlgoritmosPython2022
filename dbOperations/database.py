from sqlalchemy import create_engine

import pandas as pd 
class Database:
    engine  = None

    def __init__(self):
        global engine 
        engine  = create_engine("mysql+mysqldb://root:123456789@localhost/fxhistory")

    def insertmany(self, data, symbol,timeframe):
        symbol = symbol.replace("/", "_")

        for index, row in data.iterrows():           
            try:

                sql = "INSERT INTO fxhistory" \
                      "(date,timeframe,symbol,bidopen,bidclose,bidhigh,bidlow,askopen,askclose,askhigh,asklow,tickqty) " \
                      "VALUES ('" + str(index) + "','" + str(timeframe) + "'," \
                      "'" + str(symbol) + "',"  \
                      "'" + str(row.bidopen) + "'," \
                      "'" + str(row.bidclose) + "'," \
                      "'" + str(row.bidhigh) + "'," \
                      "'" + str(row.bidlow) + "',"\
                      "'" + str(row.askopen) + "'," \
                      "'" + str(row.askclose) + "'," \
                      "'" + str(row.askhigh) + "'," \
                      "'" + str(row.asklow) + "'," \
                      "'" + str(row.tickqty) + "')"

                from sqlalchemy import text


                result = engine.execute(
                    text(sql)
                )

            except Exception as e:                
                if "Duplicate entry" in str(e):
                    sql = "UPDATE fxhistory SET " \
                        "bidopen = " + str(row.bidopen) + ", " \
                        "bidclose = " + str(row.bidclose) + ", " \
                        "bidhigh = " + str(row.bidhigh) + ", " \
                        "bidlow = " + str(row.bidlow) + ", " \
                        "askopen = " + str(row.askopen) + ", " \
                        "askclose = " + str(row.askclose) + ", " \
                        "askhigh = " + str(row.askhigh) + ", " \
                        "asklow = " + str(row.asklow) + ", " \
                        "tickqty = " + str(row.tickqty) + " " \
                        "WHERE date = '" + str(index) + "' "
                    result = engine.execute(
                    text(sql) )
                else:
                    print(e)
        return True
    
    def getData(self, timeframe, limit=1000):
        sql_select_Query = "SELECT * FROM fxhistory.fxhistory where timeframe = '" + timeframe + "' ORDER BY date desc limit " + str(limit)
        sql_df = pd.read_sql(
            sql_select_Query,
            con=engine
        )

        sql_df_sort = sql_df.sort_values(by=['date'],ascending=True)

        return sql_df_sort

        