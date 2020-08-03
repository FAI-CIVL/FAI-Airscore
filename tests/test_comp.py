# -*- coding: utf-8 -*-
"""Model unit tests."""
# import datetime as dt
# import pytest
# from comp import Comp, Database
# from .factories import CompetitionTableFactory
from unittest.mock import MagicMock, patch
# import myconn
import datetime
from obj_factories import DBFactory, CompFactory, DBFactory


class TestComp:
    """Competition tests."""
    comp_id = 1
    comp = CompFactory(comp_id=comp_id, comp_code='abc123', comp_class='PG', comp_name='test comp',
                       comp_site='somewhere over the rainbow', date_from=datetime.date(2020, 2, 29),
                       date_to=datetime.date(2020, 4, 1))

    @patch('comp.db_session', autospec=True, spec_set=True)
    def test_to_db(self, mock_db):
        """Get comp by ID."""
        self.comp.to_db()
        mock_db.assert_called()

    def test_start_date_str(self):
        assert self.comp.start_date_str == "2020-02-29"

    def test_end_date_str(self):
        assert self.comp.end_date_str == "2020-04-01"

    # @patch('comp.Database', autospec=True, spec_set=True)
    # @patch('comp.create_comp_path', autospec=True, spec_set=True)
    # def test_create_path(self, mock_db, mock_path):
    #     self.comp.create_path()
    #     assert self.comp.pa