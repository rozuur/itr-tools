import re
import argparse

import pandas as pd

from collections import namedtuple

Transaction = namedtuple('Transaction', 'name, isin, family, id units purchase_date purchase_value acquisition_value grandfather_value redemption_date gains stcg ltcg')

def parse_transactions(rows):
    # First line is fund with ISIN
    fund = rows[0][0]
    isin = _isin(fund)
    if not isin:
        return
    # Second line is Folio
    _ = rows[1][0]
    name, isin, family = re.match(r'(.+)\[ISIN: ([\w\s]+)\W+(\w+)', fund).groups()
    # Skip last transaction as it's fund total
    for transaction in rows[2:-1]:
        yield Transaction(name.strip(), isin, family, *transaction.to_list())


def _isin(fund):
    try:
        return 'ISIN' in fund
    except TypeError:
        return False

def parse_gains(filename):
    sheet = pd.read_excel(filename, sheet_name='Sheet1')
    transactions = []
    rows = []
    for pd_row in sheet.iterrows():
        row = pd_row[1]
        # if row contains [ISIN: *] then it's a start
        isin = _isin(row[0])
        if isin:
            transactions.extend(parse_transactions(rows))
            rows = []
        rows.append(row)
    return transactions

def main():
    parser = argparse.ArgumentParser("Kuvera capital gains excel")
    parser.add_argument('--file', help="Excel file")
    args = parser.parse_args()
    transactions = parse_gains(args.file)



if __name__ == '__main__':
    main()
