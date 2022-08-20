import mysql.connector
import pandas as pd 
class Database:
    my_db = my_cursor = None

    def __init__(self):
        global my_db, my_cursor
        my_db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456789",
            database="fxhistory"
        )
        my_cursor = my_db.cursor()

    def __del__(self):
        my_db.commit()

    def insertmany(self, data, symbol,timeframe):
        symbol = symbol.replace("/", "_")

        for index, row in data.iterrows():           
            try:

                sql = "INSERT INTO fxhistory" \
                      "(date,timeframe,symbol,bidopen,bidclose,bidhigh,bidlow,askopen,askclose,askhigh,asklow,tickqty) " \
                      "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                val = (
                index,
                timeframe,
                symbol, 
                row.bidopen,
                row.bidclose,
                row.bidhigh,
                row.bidlow,
                row.askopen,
                row.askclose, 
                row.askhigh,
                row.asklow, 
                row.tickqty
                )
                my_cursor.execute(sql, val)
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
                    my_cursor.execute(sql)
                else:
                    print(e)

            finally:
                my_db.commit()
                #print(my_cursor.rowcount, "record(s) affected")
                
        return True
    
    def getData(self, timeframe):
        try:
            sql_select_Query = "SELECT * FROM fxhistory.fxhistory where timeframe = '" + timeframe + "'"
            return pd.read_sql(sql_select_Query,my_db)
        except mysql.connector.Error as e:
            print("Error reading data from MySQL table", e)
        finally:
                my_db.commit()
        