def sales_for_region(cursor, region):
    cursor.execute(f"SELECT * FROM sales WHERE region = '{region}'")
    return cursor.fetchall()
