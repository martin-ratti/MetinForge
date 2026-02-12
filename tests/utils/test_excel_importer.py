import pytest
import os
import csv
import tempfile
from unittest.mock import patch, MagicMock


class TestParseAccountFileRouting:
    """Tests para la función principal parse_account_file y su routing."""

    def test_unsupported_format_raises_error(self):
        from app.utils.excel_importer import parse_account_file
        with pytest.raises(ValueError, match="Formato no soportado"):
            parse_account_file("archivo.txt")

    def test_csv_extension_routes_to_csv_parser(self):
        from app.utils.excel_importer import parse_account_file
        with patch('app.utils.excel_importer._parse_csv', return_value={"email": "", "characters": []}) as mock:
            parse_account_file("test.csv")
            mock.assert_called_once_with("test.csv")

    def test_xlsx_without_openpyxl_raises_import_error(self):
        from app.utils.excel_importer import parse_account_file
        with patch('app.utils.excel_importer.HAS_OPENPYXL', False):
            with pytest.raises(ImportError, match="openpyxl"):
                parse_account_file("test.xlsx")

    def test_xlsx_extension_routes_to_xlsx_parser(self):
        from app.utils.excel_importer import parse_account_file
        with patch('app.utils.excel_importer.HAS_OPENPYXL', True), \
             patch('app.utils.excel_importer._parse_xlsx', return_value={"email": "", "characters": []}) as mock:
            parse_account_file("test.xlsx")
            mock.assert_called_once_with("test.xlsx")


class TestParseCsv:
    """Tests para el parser CSV."""

    def _create_csv(self, rows):
        """Helper: crea un CSV temporal con las filas dadas."""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, 
                                          newline='', encoding='utf-8')
        writer = csv.writer(tmp)
        for row in rows:
            writer.writerow(row)
        tmp.close()
        return tmp.name

    def test_parse_csv_valid(self):
        from app.utils.excel_importer import _parse_csv
        path = self._create_csv([
            ["test@mail.com"],
            ["Cuenta", "Slots", "PJ"],
            ["Cuenta1", "5", "Guerrero"],
            ["Cuenta2", "3", "Mago"],
        ])
        try:
            data = _parse_csv(path)
            assert data["email"] == "test@mail.com"
            assert len(data["characters"]) == 2
            assert data["characters"][0]["name"] == "Guerrero"
            assert data["characters"][0]["slots"] == 5
            assert data["characters"][0]["account_name"] == "Cuenta1"
            assert data["characters"][1]["name"] == "Mago"
            assert data["characters"][1]["slots"] == 3
        finally:
            os.unlink(path)

    def test_parse_csv_empty_file(self):
        from app.utils.excel_importer import _parse_csv
        path = self._create_csv([])
        try:
            data = _parse_csv(path)
            assert data["email"] == ""
            assert data["characters"] == []
        finally:
            os.unlink(path)

    def test_parse_csv_no_at_adds_gmail(self):
        from app.utils.excel_importer import _parse_csv
        path = self._create_csv([
            ["fragmetin1"],
            ["Cuenta", "Slots", "PJ"],
            ["Cuenta1", "5", "Guerrero"],
        ])
        try:
            data = _parse_csv(path)
            assert data["email"] == "fragmetin1@gmail.com"
        finally:
            os.unlink(path)

    def test_parse_csv_with_at_keeps_email(self):
        from app.utils.excel_importer import _parse_csv
        path = self._create_csv([
            ["user@custom.com"],
            ["Cuenta", "Slots", "PJ"],
            ["Cuenta1", "5", "Guerrero"],
        ])
        try:
            data = _parse_csv(path)
            assert data["email"] == "user@custom.com"
        finally:
            os.unlink(path)

    def test_parse_csv_invalid_slots_skipped(self):
        from app.utils.excel_importer import _parse_csv
        path = self._create_csv([
            ["test@mail.com"],
            ["Cuenta", "Slots", "PJ"],
            ["Cuenta1", "abc", "Guerrero"],
            ["Cuenta2", "3", "Mago"],
        ])
        try:
            data = _parse_csv(path)
            assert len(data["characters"]) == 1
            assert data["characters"][0]["name"] == "Mago"
        finally:
            os.unlink(path)

    def test_parse_csv_short_rows_skipped(self):
        from app.utils.excel_importer import _parse_csv
        path = self._create_csv([
            ["test@mail.com"],
            ["Header"],
            ["solo_cuenta"],
            ["Cuenta2", "3", "Mago"],
        ])
        try:
            data = _parse_csv(path)
            assert len(data["characters"]) == 1
        finally:
            os.unlink(path)

    def test_parse_csv_empty_name_skipped(self):
        from app.utils.excel_importer import _parse_csv
        path = self._create_csv([
            ["test@mail.com"],
            ["Cuenta", "Slots", "PJ"],
            ["Cuenta1", "5", ""],
            ["Cuenta2", "3", "Mago"],
        ])
        try:
            data = _parse_csv(path)
            assert len(data["characters"]) == 1
        finally:
            os.unlink(path)
