import mysql.connector


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

    def insertmany(self, data, symbol):
        symbol = symbol.replace("/", "_").lower()
        for index, row in data.iterrows():
            try:
                sql = "INSERT INTO fxhistory.m15" + symbol + "" \
                      "(date,bidopen,bidclose,bidhigh,bidlow,askopen,askclose,askhigh,asklow,tickqty)" \
                      "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                val = (
                index, row.bidopen, row.bidclose, row.bidhigh, row.bidlow, row.askopen, row.askclose, row.askhigh,
                row.asklow, row.tickqty)
                my_cursor.execute(sql, val)
            except Exception as e:
                print(e)
        my_db.commit()
        return True
