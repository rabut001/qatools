'''Test the class CommentHistroySplitter'''
import os
import tempfile
import pytest
import pandas as pd
from app.scripts.modules.comment_history_splitter import CommentHistroySplitter
from app.scripts.modules.comment_history_splitter import CommentHistroySplitterSetting

class TestCommentHistroySplitter:
    '''test class for CommentHistroySplitter class'''

    def setup_method(self):
        """common setup"""

        input_data = {
            'incident_id': ['QA-000001', 'QA-000002'],
            'registered_by': ['UserX', 'UserY'],
            'registered_date': ['2001/01/01', '2001/02/01'],
            'description': ['Description1', 'Description2'],
            'comment_history': [
                "Comment11(Div11:User11 2001/01/02)\nComment12(Div12:User12 2001/01/03)",
                "Comment21(Div21:User21 2001/02/02)"
            ]
        }
        self.basic_input_df = pd.DataFrame(input_data)

        expected_data = {
            'incident_id':['QA-000001','QA-000001','QA-000001','QA-000002','QA-000002'],
            'comment_seq':[0,1,2,0,1],
            'comment_div':['新規登録','Div11','Div12','新規登録','Div21'],
            'comment_by': ['UserX', 'User11','User12','UserY','User21'],
            'comment_date': ['2001/01/01','2001/01/02','2001/01/03','2001/02/01','2001/02/02'],
            'comment': ['Description1','Comment11', 'Comment12','Description2','Comment21']
        }
        self.basic_output_df = pd.DataFrame(expected_data)

    def test_devide_comment_string_success(self):
        '''test the basic pattern of devide_comment_string mtehod. '''
        interaction_string = 'This is a comment.(Division:Team)User 2023/10/10)'
        expected_date = "2023/10/10"
        expected_div = "Division"
        expected_user = "Team)User"
        expected_comment = "This is a comment."

        date, div, user, comment = CommentHistroySplitter.devide_comment_string(interaction_string)

        assert date == expected_date
        assert div == expected_div
        assert user == expected_user
        assert comment == expected_comment

    def test_get_comment_history_df_success_basic(self):
        '''test the basic pattern of get_comment_history_df method'''

        # Arrange
        input_df = self.basic_input_df.copy()
        expected_df = self.basic_output_df.copy()

        # Act
        result_df = CommentHistroySplitter.get_comment_history_df(input_df)

        # Assert
        pd.testing.assert_frame_equal(result_df, expected_df)

    def test_get_comment_history_df_success_blank_history(self):
        '''
        test of get_comment_history_df for the blank comment_history column
        input
          incieent_no, registered_by, registered_date, description, comment_history 
          QA-000001,   UserX,         2001/01/01       description1  (None)
        output
          incieent_no, domment_seq, comment_div, comment_by, comment_date, commenty 
          QA-000001,   0,           新規登録,     UserX,      2001/01/01.  description1
        '''

        # Arrange
        # arrange input data which has blank(None) in comment.
        input_df = self.basic_input_df.loc[[0]]
        input_df.at[0, 'comment_history'] = None

        # arrange output data 
        expected_df = self.basic_output_df.loc[[0]]

        # Act
        result_df = CommentHistroySplitter.get_comment_history_df(input_df)

        # Assert
        pd.testing.assert_frame_equal(result_df, expected_df)

    def test_get_comment_histroy_csv_success(self):
        """test the basic pattern of get_comment_history_csv method"""

        # Arrange
        input_df = self.basic_input_df.copy()
        expected_data_df = self.basic_output_df.copy()

        # prepare output csv
        output_file_name = tempfile.mktemp()
        expected_data_file_name = tempfile.mktemp()
        expected_data_df.to_csv(expected_data_file_name, header=True, index=False, encoding='utf-8_sig')

        # Act & Assert
        try:
            CommentHistroySplitter.get_comment_histroy_csv(input_df, output_file_name)

            with open(output_file_name, 'r', encoding='utf-8_sig') as output_file:
                output_content = output_file.read()

                with open(expected_data_file_name, 'r', encoding='utf-8_sig') as expected_data_file:
                    expected_content = expected_data_file.read()
                    assert output_content == expected_content
        finally:
            os.remove(output_file_name)
            os.remove(expected_data_file_name)

    def test_get_comment_histroy_csv_faiure_file_exists(self):
        """test the basic pattern of get_comment_history_csv method"""

        # Arrange
        input_df = self.basic_input_df.copy()

        # prepare output csv
        output_file_name = tempfile.mktemp()

        # Act & Assert
        try:
            with open(output_file_name, 'w', encoding='utf-8_sig') as output_file:
                None            
            with pytest.raises(ValueError, match="Output file already exists. file name: "+ output_file_name):
                CommentHistroySplitter.get_comment_histroy_csv(input_df, output_file_name)
        finally:
            os.remove(output_file_name)

    def test_get_comment_histroy_csv_from_file_success(self):
        """test the basic pattern of get_comment_history_csv method"""

        # Arrange
        input_df = self.basic_input_df
        expected_data_df = self.basic_output_df

        # prepare output csv
        input_file_name = tempfile.mktemp()
        output_file_name = tempfile.mktemp()
        expected_data_file_name = tempfile.mktemp()

        input_df.to_csv(input_file_name, header=True, index=False, encoding='utf-8_sig')
        expected_data_df.to_csv(expected_data_file_name, header=True, index=False, encoding='utf-8_sig')

        # Act & Assert
        try:
            settings = CommentHistroySplitterSetting(input_file_name)
            CommentHistroySplitter.get_comment_histroy_csv_from_file(settings, output_file_name)

            with open(output_file_name, 'r', encoding='utf-8_sig') as output_file:
                output_content = output_file.read()

                with open(expected_data_file_name, 'r', encoding='utf-8_sig') as expected_data_file:
                    expected_content = expected_data_file.read()
                    assert output_content == expected_content
        finally:
            os.remove(input_file_name)
            os.remove(output_file_name)
            os.remove(expected_data_file_name)
