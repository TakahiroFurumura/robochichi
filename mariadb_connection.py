import json
import mariadb
import os
import decimal
import traceback
import datetime
import re
import typing


class MariadbConnection(object):

    @staticmethod
    def get_db_connection(
            host: str,
            user: str,
            password: str,
            database_name: str = None,
            port: int = 3306):

        connection = mariadb.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database_name)
        connection.auto_reconnect = True
        cursor = connection.cursor()

        return connection, cursor

    def __init__(self,
                 host: str,
                 user: str,
                 password: str,
                 database: str,
                 table: str,
                 port: int = 3306):
        self._connection, self._cursor = self.get_db_connection(
            host=host, port=port, user=user, password=password, database_name=database)

        self.host = host
        self.user = user
        self.dtabase = database
        self.table_name = table

    def __del__(self):
        """
        commitしてcloseしてからdestructします。
        :return:
        """
        self._connection.close()

    def batch_update(self):
        pass

    def insert_one(self, data):
        """
        基底クラスでは、引数が辞書型かどうかのValidationのみ提供します。dataが辞書型ではない場合は例外を出します。
        :param data: dict()
        :return: boolean, message
        """
        # data type validation
        if not (isinstance(data, dict)):
            raise TypeError('argument "data" must be dict, not ' + str(type(data)))

        return False, '基底クラスのinsert_oneは何もしません'

    def _match_valtype_to_table(self, data: dict, truncate_str: bool = False) -> None:
        """
        引数で与えられたDict{column:value}のvalueの型をTableに合わせます。Noneは放置します。引数を変更します。
        対応型：varchar, int, float, decimal, datetime
        if turuncate_str=True, truncate string if it exceed varchar field size. This truncate may break json str.
        :param data:
        :param truncate_str:
        :return:
        :rtype:
        """
        assert isinstance(data, dict)
        assert isinstance(truncate_str, bool)

        self._cursor.execute("SHOW COLUMNS FROM %s" % self.table_name)
        columns = {r[0]: r[1] for r in self._cursor.fetchall()}

        if not (set(list(data.keys())) <= set(columns.keys())):
            raise ValueError('data keys and table field names do not match: %s'
                             + str(set(list(data.keys())) - set(columns.keys())))

        for key in data.keys():
            if data[key] is not None:
                try:
                    # str column
                    if 'varchar' in columns[key]:
                        data[key] = str(data[key])
                        # truncate
                        if truncate_str:
                            length = re.search(r'\((\d+)\)', columns[key]).groups()[0]
                            data[key] = data[key][0:int(length)]

                    # numbers
                    elif 'int' in columns[key]:
                        data[key] = int(data[key])
                    elif 'float' in columns[key]:
                        data[key] = float(data[key])
                    elif 'decimal' in columns[key]:
                        data[key] = decimal.Decimal(data[key])

                    # datetime
                    elif 'datetime' in columns[key]:
                        if type(data[key]) not in (str, datetime.datetime):
                            raise TypeError('faild to convert value %s (type %s) to datetime.'
                                            % (data[key], type(data[key])))
                        data[key] = (datetime.datetime.fromisoformat(data[key])
                                     if isinstance(data[key], str) else data[key])

                except Exception as e:
                    raise TypeError(str(e)
                                    + 'cannot convert value=%s for key=%s into %s ' % (data[key], key, columns[key]))

        return

    @staticmethod
    def _conv_value_sqlstr(data: dict) -> dict:
        """
        convert value of given dict into sql convertible expression. add single quotations for str value, give NULL str
        without quotation for None.
        :param data: {database_column_field_name: value in str, int, float, decimal or None, }
        :return: new dict of {database_column_field_name: converted_value,}
        :rtype: dict
        """
        assert isinstance(data, dict)

        data_rev = {
            key: ('NULL' if data[key] is None
                  else "'" + str(data[key]) + "'" if type(data[key]) not in (int, float, decimal.Decimal) else str(data[key]))
            for key in data.keys()}

        return data_rev

    def _insert(self, data: dict, upsert: bool = False,
                update_fields: typing.Union[str, typing.List[str], set, tuple] = None) -> typing.Union[int, None]:
        """
        insert
        :param data: dict like {column_field_name:value, }. str and numeric type are allowed.
        :param upsert: False: do nothing when key duplicates. True: update undate_fields whe key duplicates
        :param update_fields: list of column field name to be updated on duplicated key
        :return: last insert row id if autoincrement primary key is available. else None.
        :rtype:
        """
        """
        insert a record from dict
        :return: boolean, message
        """
        assert isinstance(data, dict)
        assert isinstance(upsert, bool)
        assert (upsert and type(update_fields) in [str, list, set, tuple]) or (not upsert and update_fields is None)

        # convert data value into str and add quotations if original value was str
        data_r = self._conv_value_sqlstr(data)
        columns_agg = ','.join([col for col in data_r.keys()])
        values_agg = ','.join([data_r[key] for key in data_r.keys()])

        sql = ("INSERT INTO %s (%s) VALUES (%s)" % (self.table_name, columns_agg, values_agg))

        if upsert and update_fields is not None:
            update_fields = [update_fields] if isinstance(update_fields, str) else list(update_fields)
            update_key_val = [key + "=" + data_r[key] for key in update_fields]
            sql += " ON DUPLICATE KEY UPDATE " + ','.join(update_key_val)
        try:
            self._cursor.execute(sql)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            print(sql)
            print('return')
            return

        row_id = self._cursor.lastrowid
        self._connection.commit()

        return row_id

    def _replace(self, data: dict):
        """

        :param data:
        :return:
        :rtype:
        """
        assert isinstance(data, dict)

        # convert data value into str and add quotations if original value was str
        data_r = self._conv_value_sqlstr(data)
        columns_agg = ','.join([col for col in data_r.keys()])
        values_agg = ','.join([data_r[key] for key in data_r.keys()])

        self._cursor.execute("REPLACE INTO %s (%s) VALUES (%s)" % (self.table_name, columns_agg, values_agg))
        row_id = self._cursor.lastrowid
        self._connection.commit()

        return row_id

    def select_by_pkey(self, primary_key_values: typing.Union[dict, str, int, float, decimal.Decimal]):
        """
        select row by a given primary key and return dict.
        if 0 is given for varchar primary key field, raise exemption.
        :param primary_key_values: praimary key value or dict like {primary_key_name: value,}
        :return: dict like {column_field: value, } if record found. None if not found.
        :rtype:
        """
        assert type(primary_key_values) in [dict, str, int, float, decimal.Decimal]

        # get primary key name
        self._cursor.execute("SHOW COLUMNS FROM %s" % self.table_name)
        columns = self._cursor.fetchall()
        column_fields = [r[0] for r in columns]
        primary_key_names = [r[0] for r in columns if r[3] == 'PRI']
        primary_key_types = [r[1] for r in columns if r[3] == 'PRI']

        # 0 check for varchar field
        if not isinstance(primary_key_values, dict) and primary_key_values == 0 and 'varchar' in primary_key_types[0]:
            raise ValueError('0 is given for varchar filed %s.' % primary_key_names[0])

        # if dict is given
        if isinstance(primary_key_values, dict):
            if not (set(primary_key_values.keys()) == set(primary_key_names)):
                raise ValueError('argument pkey_field_names values %s does not match with table primary key fields %s.'
                                 % (str(primary_key_values), str(primary_key_names)))

            primary_key_values_ = self._conv_value_sqlstr(primary_key_values)
            where_str = ' AND '.join(
                [key + '=' + primary_key_values_[key] for key in primary_key_values_.keys()])

        # if a single value is given
        else:
            if len(primary_key_names) > 1:
                raise ValueError('argument pkey_field_names values %s does not match with table primary key fields %s.'
                                 % (str(primary_key_values), str(primary_key_names)))
            primary_key_values_ = self._conv_value_sqlstr({primary_key_names[0]: primary_key_values})
            where_str = '%s=%s' % (primary_key_names[0], primary_key_values_[primary_key_names[0]])
        self._cursor.execute("SELECT * FROM %s WHERE %s" % (self.table_name, where_str))

        rows = self._cursor.fetchall()
        if len(rows) > 1:
            raise ValueError('more than one rows are returned for pkey=' + str(primary_key_values))
        elif len(rows) == 0:
            response = None
        else:
            response = dict(zip(column_fields, rows[0]))

        return response

    def batch_update(self):
        """

        :return:
        :rtype:
        """

        return False, '基底クラスのbatch_updateは何もしません'

    def delete_obsolete_records(self):
        """

        :return:
        :rtype:
        """

        return False, '基底クラスのarchive_old_recordsは何もしません'