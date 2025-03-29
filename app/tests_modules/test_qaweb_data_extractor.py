"""QaWebDataExtractorのテストコード"""
import re
import os
import tempfile
import pytest
import pandas as pd
from unittest.mock import Mock, patch, call

from app.scripts.modules.qaweb_data_extractor import QaWebDataExtractor

class TestQaWebDataExtractor:
    """QaWebDataExtractorのテストコード"""

    def setup_method(self):
        """Set up common arguments"""
        self.args = {
            "site": "https://example.com",
            "login_page": "/login",
            "menu_page": "/menu",
            "csv_page": "/data.csv",
            "category_param": "category",
            "category": "example_category",
            "login_user": "username",
            "login_pass": "password",
            "records_per_request": 100
        }

    def test_constructor_success(self):
        """Test for successful constructor"""

        # Act
        extractor = QaWebDataExtractor(**self.args)

        # Assert
        assert extractor.qaweb_info['site'] == "https://example.com"
        assert extractor.qaweb_info['login_page'] == "/login"
        assert extractor.qaweb_info['menu_page'] == "/menu"
        assert extractor.qaweb_info['csv_page'] == "/data.csv"
        assert extractor.qaweb_info['category_param'] == "category"
        assert extractor.qaweb_info['category'] == "example_category"
        assert extractor.qaweb_info['login_user'] == "username"
        assert extractor.qaweb_info['login_pass'] == "password"

    def test_constructor_failure_invalid_args(self):
        """Test for failed constructor with invalid arguments"""

        # Arrange
        args = self.args.copy()
        del args["login_user"]
        del args["login_pass"]

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid arguments"):
            QaWebDataExtractor(**args)

    def test_constructor_failure_invalid_work_dir(self):
        """Test for failed constructor with invalid arguments"""

        # Arrange
        args = self.args.copy()
        args["work_dir"] = '/\\//\\/'

        # Act & Assert
        with pytest.raises(ValueError, match=re.escape('No such directory. work_dir: /\\//\\/')):
            QaWebDataExtractor(**args)

    def test_get_work_file_name_success_with_arg_value(self):
        """Test for get_work_file with work_dir"""

        # Arrange
        args = self.args.copy()
        work_dir = tempfile.gettempdir()
        args['work_dir'] = work_dir

        # Act
        extractor = QaWebDataExtractor(**args)
        work_file_name = extractor.get_work_file_name()

        # Assert
        assert work_file_name.startswith(work_dir)

    def test_get_work_file_name_success_without_arg_value(self):
        """Test for get_work_file without work_dir"""

        # Arrange
        mock_mktemp = Mock()
        mock_mktemp.return_value = '/test_mock/xxx'

        args = self.args.copy()
        args['work_dir'] = None

        # Act & Assert
        extractor = QaWebDataExtractor(**args)
        with patch('tempfile.mktemp', mock_mktemp):
            work_file_name = extractor.get_work_file_name()
            assert work_file_name == '/test_mock/xxx'

    def test_login_success(self):
        """Test for successful login"""

        # Arrange
        mock_post = Mock()
        mock_post.return_value.status_code = 200
        mock_get = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '    3,302,302,298,example_category-000001,000003'

        # Act
        with patch('requests.Session.post', mock_post), patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**self.args)
            extractor.login()

        # Assert
        mock_post.assert_called_once_with(
            "https://example.com/login",
            data={"usr": "username", "pwd": "password"}
        )
        mock_get.assert_called_once_with(
            "https://example.com/menu?category=example_category"
        )

    def test_login_failure_http_error(self):
        """Test for failed login by http error"""

        # Arrange
        mock_post = Mock()
        mock_post.return_value.status_code = 401

        # Act & Assert
        with patch('requests.Session.post', mock_post):
            extractor = QaWebDataExtractor(**self.args)
            with pytest.raises(ValueError, match="Failed to login. http status:401"):
                extractor.login()

    def test_switch_context_success(self):
        """Test for successful context switch"""

        # Arrange
        mock_post = Mock()
        mock_post.return_value.status_code = 200
        mock_get = Mock()
        mock_get.side_effect = [
            Mock(status_code=200, text='    3,302,302,298,example_category-000001,000003'),
            Mock(status_code=200, text='    3,302,302,298,new_category-000001,000003')
        ]

        # Act
        with patch('requests.Session.post', mock_post), patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**self.args)
            extractor.login()
            extractor.switch_context("new_category")

        # Assert
        assert mock_get.call_count == 2
        mock_get.assert_has_calls([
            call("https://example.com/menu?category=example_category"),
            call("https://example.com/menu?category=new_category")
        ])

    def test_switch_context_failure_no_session(self):
        """Test for failed context switch"""

        # Arrange
        mock_get = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '    3,302,302,298,example_category-000001,000003'

        # Act & Assert
        with patch('requests.Session.post', mock_get), patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**self.args)
            with pytest.raises(AttributeError, match=re.escape("No session. Login first using login() method to get session.")):
                extractor.switch_context("new_category")

    def test_switch_context_failure_http_error(self):
        """Test for failed context switch"""

        # Arrange
        mock_get = Mock()
        mock_get.return_value.status_code = 401

        # Act & Assert
        with patch('requests.Session.post', mock_get), patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**self.args)
            with patch.object(extractor, 'has_session', True):
                with pytest.raises(ValueError, match="Failed to switch category. http status:401"):
                    extractor.switch_context("new_category")

    def test_switch_context_failure_category_unmatch(self):
        """Test for failed context switch due to category mismatch"""

        # Arrange
        mock_post = Mock()
        mock_post.return_value.status_code = 200
        mock_get = Mock()
        mock_get.side_effect = [
            Mock(status_code=200, text='    3,302,302,298,example_category-000001,000003'),
            Mock(status_code=200, text='xxx')
        ]

        # Act & Assert
        with patch('requests.Session.post', mock_post), patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**self.args)
            extractor.login()
            with pytest.raises(AttributeError, match="Failed to switch category. Category does not match."):
                extractor.switch_context("new_category")

    def test_get_qa_csv_single_success(self):
        """Test for successful CSV download"""

        # Arrange
        mock_post = Mock()
        mock_post.side_effect = [
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n".encode('cp932')
            ),
        ]

        qa_no_list = ["example_category-000001", "example_category-000002"]
        out_file_name = tempfile.mktemp()

        # Act
        with patch('requests.Session.post', mock_post):
            extractor = QaWebDataExtractor(**self.args)
            with patch.object(extractor, 'has_session', True):
                extractor._get_qa_csv_single(qa_no_list, out_file_name)

        # Assert
        mock_post.assert_called_once_with(
            "https://example.com/data.csv",
            data={"TBLLIST": "example_category-000001 example_category-000002"}
        )

        with open(out_file_name, 'r', encoding='cp932') as file:
            content = file.read()
            assert content == "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n"

        os.remove(out_file_name)

    def test_get_qa_csv_single_failure_invalid_qa_no(self):
        """Test for invalid QA number"""

        # Arrange
        qa_no_list = ["invalid_category-000001"]
        out_file_name = "test_output.csv"

        # Act & Assert
        extractor = QaWebDataExtractor(**self.args)
        with patch.object(extractor, 'has_session', True):
            with pytest.raises(ValueError, match="Invalid QA number: invalid_category-000001"):
                extractor._get_qa_csv_single(qa_no_list, out_file_name)

    def test_get_qa_csv_single_failure_file_exists(self):
        """Test for existing output file"""

        # Arrange
        qa_no_list = ["example_category-000001"]
        out_file_name = tempfile.mktemp()

        # Act & Assert
        extractor= QaWebDataExtractor(**self.args)
        with patch.object(extractor, 'has_session', True):
            with open(out_file_name, 'w', encoding='cp932') as file:
                file.write("dummy content")

            with pytest.raises(ValueError, match="Output file already exists. file name: "+out_file_name):
                extractor._get_qa_csv_single(qa_no_list, out_file_name)

            os.remove(out_file_name)

    def test_get_qa_csv_success(self):
        """Test for successful CSV download in batches"""

        # Arrange
        mock_post = Mock()
        mock_post.side_effect = [
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n".encode('cp932')
            ),
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ31\",\"QAデータ32\"\n".encode('cp932')
            )
        ]

        args = self.args.copy()
        args['records_per_request'] = 2

        qa_no_list = ["example_category-000001", "example_category-000002", "example_category-000003"]
        out_file_name = tempfile.mktemp()

        # Act
        with patch('requests.Session.post', mock_post):
            extractor = QaWebDataExtractor(**args)
            with patch.object(extractor, 'has_session', True):
                extractor.get_qa_csv(qa_no_list, out_file_name)

        # Assert
        mock_post.assert_has_calls([
            call("https://example.com/data.csv", data={"TBLLIST": "example_category-000001 example_category-000002"}),
            call("https://example.com/data.csv", data={"TBLLIST": "example_category-000003"})
        ])

        with open(out_file_name, 'r', encoding='cp932') as file:
            content = file.read()
            assert content == "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n\"QAデータ31\",\"QAデータ32\"\n"

        os.remove(out_file_name)

    def test_get_qa_csv_failure_no_session(self):
        """Test for existing output file"""

        # Arrange
        qa_no_list = ["example_category-000001", "example_category-000002"]
        out_file_name = tempfile.mktemp()

        # Act & Assert
        with pytest.raises(AttributeError, match=re.escape("No session. Login first using login() method to get session.")):
            QaWebDataExtractor(**self.args).get_qa_csv(qa_no_list, out_file_name)

        os.remove(out_file_name)

    def test_get_qa_csv_failure_file_exists(self):
        """Test for existing output file"""

        # Arrange
        qa_no_list = ["example_category-000001", "example_category-000002"]
        out_file_name = tempfile.mktemp()

        # Act & Assert
        extractor = QaWebDataExtractor(**self.args)
        with patch.object(extractor, 'has_session', True):
            with open(out_file_name, 'w') as file:
                file.write("dummy content")

            with pytest.raises(ValueError, match="Output file already exists. file name: "+out_file_name):
                extractor.get_qa_csv(qa_no_list, out_file_name)

            os.remove(out_file_name)

    def test_get_max_qa_no_in_int_success(self):
        """Test for successful retrieval of max QA number"""

        # Arrange
        mock_get = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
                <b>QA一覧</b><br>
                <!--
                    15142,302,302,298,FDP-015101,015142
                -->
                ■ <a href="3table.pl?FDP-015101" target="FRAME2" title="昇順に表示" onclick="return chengchk()">FDP-015101～</a>
                <a href="3table2.pl?FDP-015101" target="FRAME2" title="降順に表示" onclick="return chengchk()">015142</a><br>
                <!--
                    15142,301,302,298,FDP-015051,015100
                -->
            """

        args = self.args.copy()
        args["category"] = "FDP"

        # Act
        with patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**args)
            with patch.object(extractor, 'has_session', True):
                max_qa_no = extractor.get_max_qa_no_in_int()

        # Assert
        mock_get.assert_called_once_with("https://example.com/menu")
        assert max_qa_no == 15142

    def test_get_max_qa_no_in_int_failure_http_error(self):
        """Test for failed retrieval of max QA number due to HTTP error"""

        # Arrange
        mock_get = Mock()
        mock_get.return_value.status_code = 401

        # Act & Assert
        with patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**self.args)
            with patch.object(extractor, 'has_session', True):
                with pytest.raises(ValueError, match="Failed to get the menu page. http status: 401"):
                    extractor.get_max_qa_no_in_int()

    def test_get_max_qa_no_in_int_failure_no_match(self):
        """Test for failed retrieval of max QA number due to no match"""

        # Arrange
        mock_get = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
        <b>QA一覧</b><br>
        <!--
            No matching QA number
        -->
        """

        # Act & Assert
        with patch('requests.Session.get', mock_get):
            extractor = QaWebDataExtractor(**self.args)
            with patch.object(extractor, 'has_session', True):
                with pytest.raises(AttributeError, match="Failed to get the max QA from QAWeb"):
                    extractor.get_max_qa_no_in_int()

    def test_get_max_qa_no_in_int_failure_no_session(self):
        """Test for failed retrieval of max QA number due to no session"""

        # Act & Assert
        with pytest.raises(AttributeError, match=re.escape("No session. Login first using login() method to get session.")):
            QaWebDataExtractor(**self.args).get_max_qa_no_in_int()

    def test_get_all_qa_csv_success(self):
        """Test for successful download of all QA data"""

        # Arrange
        mock_get = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
                <b>QA一覧</b><br>
                <!--
                    3,302,302,298,FDP-000001,000003
                -->
            """
        mock_post = Mock()
        mock_post.side_effect = [
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n".encode('cp932')
            ),
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ31\",\"QAデータ32\"\n".encode('cp932')
            )
        ]

        args = self.args.copy()
        args["category"] = "FDP"
        args["records_per_request"] = 2

        out_file_name = tempfile.mktemp()

        # Act
        with patch('requests.Session.get', mock_get), patch('requests.Session.post', mock_post):
            extractor = QaWebDataExtractor(**args)
            with patch.object(extractor, 'has_session', True):
                extractor.get_all_qa_csv(out_file_name)

        # Assert
        mock_get.assert_called_once_with("https://example.com/menu")
        mock_post.assert_has_calls([
            call("https://example.com/data.csv", data={"TBLLIST": "FDP-000001 FDP-000002"}),
            call("https://example.com/data.csv", data={"TBLLIST": "FDP-000003"})
        ])

        with open(out_file_name, 'r', encoding='cp932') as file:
            content = file.read()
            assert content == "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n\"QAデータ31\",\"QAデータ32\"\n"

        os.remove(out_file_name)

    def test_get_qa_df_success(self):
        """Test for successful retrieval of QA data as DataFrame"""

        # Arrange
        mock_post = Mock()
        mock_post.side_effect = [
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n".encode('cp932')
            ),
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ31\",\"QAデータ32\"\n".encode('cp932')
            )
        ]

        args = self.args.copy()
        args["category"] = "FDP"
        args["records_per_request"] = 2

        qa_no_list = ["FDP-000001", "FDP-000002", "FDP-000003"]

        # Act
        with patch('requests.Session.post', mock_post):
            extractor = QaWebDataExtractor(**args)
            with patch.object(extractor, 'has_session', True):
                df = extractor.get_qa_df(qa_no_list)

        # Assert
        mock_post.assert_has_calls([
            call("https://example.com/data.csv", data={"TBLLIST": "FDP-000001 FDP-000002"}),
            call("https://example.com/data.csv", data={"TBLLIST": "FDP-000003"})
        ])

        expected_df = pd.DataFrame({
            "タイトル1": ["QAデータ11", "QAデータ21", "QAデータ31"],
            "タイトル2": ["QAデータ12", "QAデータ22", "QAデータ32"]
        })
        pd.testing.assert_frame_equal(df, expected_df)

    def test_get_all_qa_df_success(self):
        """Test for successful retrieval of all QA data as DataFrame"""

        # Arrange
        mock_get = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
                <b>QA一覧</b><br>
                <!--
                    3,302,302,298,FDP-000001,000003
                -->
            """
        mock_post = Mock()
        mock_post.side_effect = [
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ11\",\"QAデータ12\"\n\"QAデータ21\",\"QAデータ22\"\n".encode('cp932')
            ),
            Mock(
                status_code=200,
                content= "\"タイトル1\",\"タイトル2\"\n\"QAデータ31\",\"QAデータ32\"\n".encode('cp932')
            )
        ]

        args = self.args.copy()
        args["category"] = "FDP"
        args["records_per_request"] = 2

        # Act
        with patch('requests.Session.get', mock_get), patch('requests.Session.post', mock_post):
            extractor = QaWebDataExtractor(**args)
            with patch.object(extractor, 'has_session', True):
                df = extractor.get_all_qa_df()

        # Assert
        mock_get.assert_called_once_with("https://example.com/menu")
        mock_post.assert_has_calls([
            call("https://example.com/data.csv", data={"TBLLIST": "FDP-000001 FDP-000002"}),
            call("https://example.com/data.csv", data={"TBLLIST": "FDP-000003"})
        ])

        expected_df = pd.DataFrame({
            "タイトル1": ["QAデータ11", "QAデータ21", "QAデータ31"],
            "タイトル2": ["QAデータ12", "QAデータ22", "QAデータ32"]
        })
        pd.testing.assert_frame_equal(df, expected_df)
