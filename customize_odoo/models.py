#-*- coding: utf-8 -*-
from odoo import models, api
import datetime
import dateutil
import pytz
from collections import defaultdict
from odoo.tools import groupby
from odoo import SUPERUSER_ID
import logging
from odoo.tools import OrderedSet, Collector
from operator import attrgetter, itemgetter
from psycopg2.extensions import AsIs
from . import pycompat
from collections import defaultdict, MutableMapping, OrderedDict
from inspect import getmembers, currentframe
from .misc import clean_context
from odoo.fields import Field, Many2many, One2many

LOG_ACCESS_COLUMNS = ['create_uid', 'create_date', 'write_uid', 'write_date']
MAGIC_COLUMNS = ['id'] + LOG_ACCESS_COLUMNS

_logger = logging.getLogger(__name__)


def _parent_store_create(self):
    # _logger.info({'patched': '_parent_store_create_multi'})
    """ Set the parent_path field on ``self`` after its creation. """
    if not self._parent_store:
        return

    query = """
        UPDATE {0} node
        SET parent_path=concat((SELECT parent.parent_path FROM {0} parent
                                WHERE parent.id=node.{1}), node.id, '/')
        WHERE node.id IN %s
    """.format(self._table, self._parent_name)
    self._cr.execute(query, [tuple(self.ids)])

@api.model
def _read_group_process_groupby(self, gb, query):
    """
        修改display_formats中格式
    """
    split = gb.split(':')
    field_type = self._fields[split[0]].type
    gb_function = split[1] if len(split) == 2 else None
    temporal = field_type in ('date', 'datetime')
    tz_convert = field_type == 'datetime' and self._context.get('tz') in pytz.all_timezones
    qualified_field = self._inherits_join_calc(self._table, split[0], query)
    if temporal:
        display_formats = {
            # Careful with week/year formats:
            #  - yyyy (lower) must always be used, *except* for week+year formats
            #  - YYYY (upper) must always be used for week+year format
            #         e.g. 2006-01-01 is W52 2005 in some locales (de_DE),
            #                         and W1 2006 for others
            #
            # Mixing both formats, e.g. 'MMM YYYY' would yield wrong results,
            # such as 2006-01-01 being formatted as "January 2005" in some locales.
            # Cfr: http://babel.pocoo.org/docs/dates/#date-fields
            'day': 'yyyy-MM-dd', # yyyy = normal year
            'week': "YYYY 'W'w",  # w YYYY = ISO week-year
            'month': 'yyyy MMMM',
            'quarter': 'yyyy QQQ',
            'year': 'yyyy',
        }
        time_intervals = {
            'day': dateutil.relativedelta.relativedelta(days=1),
            'week': datetime.timedelta(days=7),
            'month': dateutil.relativedelta.relativedelta(months=1),
            'quarter': dateutil.relativedelta.relativedelta(months=3),
            'year': dateutil.relativedelta.relativedelta(years=1)
        }
        if tz_convert:
            qualified_field = "timezone('%s', timezone('UTC',%s))" % (self._context.get('tz', 'UTC'), qualified_field)
        qualified_field = "date_trunc('%s', %s)" % (gb_function or 'month', qualified_field)
    if field_type == 'boolean':
        qualified_field = "coalesce(%s,false)" % qualified_field
    return {
        'field': split[0],
        'groupby': gb,
        'type': field_type, 
        'display_format': display_formats[gb_function or 'month'] if temporal else None,
        'interval': time_intervals[gb_function or 'month'] if temporal else None,                
        'tz_convert': tz_convert,
        'qualified_field': qualified_field
    }

# models.BaseModel._onchange_eval = _onchange_eval
# models.BaseModel._setup_base = _setup_base
models.BaseModel._read_group_process_groupby = _read_group_process_groupby
models.BaseModel._parent_store_create = _parent_store_create


class BaseModelExtend(models.AbstractModel):
    _name = 'base.model.extend'

    @api.model_cr
    def _register_hook(self):

        @api.model_create_multi
        @api.returns('self', lambda value: value.id)
        def create_multi(self, vals_list):
            """ create(vals_list) -> records

            Creates new records for the model.

            The new records are initialized using the values from the list of dicts
            ``vals_list``, and if necessary those from :meth:`~.default_get`.

            :param list vals_list:
                values for the model's fields, as a list of dictionaries::

                    [{'field_name': field_value, ...}, ...]

                For backward compatibility, ``vals_list`` may be a dictionary.
                It is treated as a singleton list ``[vals]``, and a single record
                is returned.

                see :meth:`~.write` for details

            :return: the created records
            :raise AccessError: * if user has no create rights on the requested object
                                * if user tries to bypass access rules for create on the requested object
            :raise ValidateError: if user tries to enter invalid value for a field that is not in selection
            :raise UserError: if a loop would be created in a hierarchy of objects a result of the operation (such as setting an object as its own parent)
            """
            # _logger.info('patched!!! create_multi')
            if not vals_list:
                return self.browse()

            self = self.browse()
            self.check_access_rights('create')

            bad_names = {'id', 'parent_path'}
            if self._log_access:
                # the superuser can set log_access fields while loading registry
                if not (self.env.uid == SUPERUSER_ID and not self.pool.ready):
                    bad_names.update(LOG_ACCESS_COLUMNS)
            unknown_names = set()

            # classify fields for each record
            data_list = []
            inversed_fields = set()

            for vals in vals_list:
                # add missing defaults
                vals = self._add_missing_default_values(vals)

                # distribute fields into sets for various purposes
                data = {}
                data['stored'] = stored = {}
                data['inversed'] = inversed = {}
                data['inherited'] = inherited = defaultdict(dict)
                data['protected'] = protected = set()
                for key, val in vals.items():
                    if key in bad_names:
                        continue
                    field = self._fields.get(key)
                    if not field:
                        unknown_names.add(key)
                        continue
                    if field.store:
                        stored[key] = val
                    if field.inherited:
                        inherited[field.related_field.model_name][key] = val
                    elif field.inverse:
                        inversed[key] = val
                        inversed_fields.add(field)
                        protected.update(self._field_computed.get(field, [field]))

                data_list.append(data)

            if unknown_names:
                _logger.warning("%s.create() with unknown fields: %s",
                                self._name, ', '.join(sorted(unknown_names)))

            # create or update parent records
            for model_name, parent_name in self._inherits.items():
                parent_data_list = []
                for data in data_list:
                    if not data['stored'].get(parent_name):
                        parent_data_list.append(data)
                    elif data['inherited'][model_name]:
                        parent = self.env[model_name].browse(data['stored'][parent_name])
                        parent.write(data['inherited'][model_name])

                if parent_data_list:
                    parents = self.env[model_name].create([
                        data['inherited'][model_name]
                        for data in parent_data_list
                    ])
                    for parent, data in pycompat.izip(parents, parent_data_list):
                        data['stored'][parent_name] = parent.id

            # create records with stored fields
            records = self._create_multi(data_list)

            # determine which fields to protect on which records
            protected = [(data['protected'], data['record']) for data in data_list]
            with self.env.protecting_multi(protected):
                # group fields by inverse method (to call it once), and order groups
                # by dependence (in case they depend on each other)
                field_groups = sorted(
                    (fields for _inv, fields in groupby(inversed_fields, attrgetter('inverse'))),
                    key=lambda fields: min(pycompat.imap(self.pool.field_sequence, fields)),
                )
                for fields in field_groups:
                    # determine which records to inverse for those fields
                    inv_names = {field.name for field in fields}
                    rec_vals = [
                        (data['record'], {
                            name: data['inversed'][name]
                            for name in inv_names
                            if name in data['inversed']
                        })
                        for data in data_list
                        if not inv_names.isdisjoint(data['inversed'])
                    ]

                    # If a field is not stored, its inverse method will probably
                    # write on its dependencies, which will invalidate the field on
                    # all records. We therefore inverse the field record by record.
                    if all(field.store or field.company_dependent for field in fields):
                        batches = [rec_vals]
                    else:
                        batches = [[rec_data] for rec_data in rec_vals]

                    for batch in batches:
                        for record, vals in batch:
                            record._cache.update(record._convert_to_cache(vals))
                        batch_recs = self.concat(*(record for record, vals in batch))
                        fields[0].determine_inverse(batch_recs)

                    # trick: no need to mark non-stored fields as modified, thanks
                    # to the transitive closure made over non-stored dependencies

            # check Python constraints for non-stored inversed fields
            for data in data_list:
                data['record']._validate_fields(set(data['inversed']) - set(data['stored']))

            # recompute fields
            if self.env.recompute and self._context.get('recompute', True):
                self.recompute()

            return records

        @api.model
        def _create_multi(self, data_list):
            # _logger.info('patched!!! _create_multi')
            """ Create records from the stored field values in ``data_list``. """
            assert data_list
            cr = self.env.cr
            quote = '"{}"'.format

            # set boolean fields to False by default (avoid NULL in database)
            for name, field in self._fields.items():
                if field.type == 'boolean' and field.store:
                    for data in data_list:
                        data['stored'].setdefault(name, False)

            # insert rows
            ids = []  # ids of created records
            other_fields = set()  # non-column fields
            translated_fields = set()  # translated fields

            # column names, formats and values (for common fields)
            columns0 = [('id', "nextval(%s)", self._sequence)]
            if self._log_access:
                columns0.append(('create_uid', "%s", self._uid))
                columns0.append(('create_date', "%s", AsIs("(now() at time zone 'UTC')")))
                columns0.append(('write_uid', "%s", self._uid))
                columns0.append(('write_date', "%s", AsIs("(now() at time zone 'UTC')")))

            for data in data_list:
                # determine column values
                stored = data['stored']
                columns = [column for column in columns0 if column[0] not in stored]
                for name, val in sorted(stored.items()):
                    field = self._fields[name]
                    # _logger.info({field: type(field)})
                    assert field.store

                    if field.column_type:
                        # col_val = field.convert_to_column(val, self, stored)
                        col_val = field.convert_to_column_multi(val, self, stored)
                        # col_val = convert_to_column(val, self, stored)
                        columns.append((name, field.column_format, col_val))
                        if field.translate is True:
                            translated_fields.add(field)
                    else:
                        other_fields.add(field)

                # insert a row with the given columns
                query = "INSERT INTO {} ({}) VALUES ({}) RETURNING id".format(
                    quote(self._table),
                    ", ".join(quote(name) for name, fmt, val in columns),
                    ", ".join(fmt for name, fmt, val in columns),
                )
                params = [val for name, fmt, val in columns]
                cr.execute(query, params)
                ids.append(cr.fetchone()[0])

            # the new records
            records = self.browse(ids)
            for data, record in pycompat.izip(data_list, records):
                data['record'] = record

            # update parent_path
            records._parent_store_create()
            protected = [(data['protected'], data['record']) for data in data_list]
            with self.env.protecting_multi(protected):
                # mark fields to recompute; do this before setting other fields,
                # because the latter can require the value of computed fields, e.g.,
                # a one2many checking constraints on records
                records.modified(self._fields)

                if other_fields:
                    # discard default values from context for other fields
                    others = records.with_context(clean_context(self._context))
                    # for field in sorted(other_fields, key=attrgetter('_sequence')):
                    for field in other_fields:
                        if type(field) in [type(Many2many), type(One2many)]:
                            field.create([
                                (other, data['stored'][field.name])
                                for other, data in pycompat.izip(others, data_list)
                                if field.name in data['stored']
                            ])
                        else:
                            field.create_multi([
                                (other, data['stored'][field.name])
                                for other, data in pycompat.izip(others, data_list)
                                if field.name in data['stored']
                            ])

                    # mark fields to recompute
                    records.modified([field.name for field in other_fields])

                # check Python constraints for stored fields
                records._validate_fields(name for data in data_list for name in data['stored'])

            records.check_access_rule('create')

            # add translations
            if self.env.lang and self.env.lang != 'en_US':
                Translations = self.env['ir.translation']
                for field in translated_fields:
                    tname = "%s,%s" % (field.model_name, field.name)
                    for data in data_list:
                        if field.name in data['stored']:
                            record = data['record']
                            val = data['stored'][field.name]
                            Translations._set_ids(tname, 'model', self.env.lang, record.ids, val, val)

            return records

        models.AbstractModel._create_multi = _create_multi
        models.AbstractModel.create_multi = create_multi
        return super(BaseModelExtend, self)._register_hook()

