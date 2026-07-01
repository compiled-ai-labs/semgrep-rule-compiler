def sales_for_region(cursor, region):
    cursor.execute("SELECT * FROM sales WHERE region = %s", (region,))
    return cursor.fetchall()
