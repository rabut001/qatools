'''module to make comment history data'''
import os
from dataclasses import dataclass
import re
import pandas as pd
from pandas import DataFrame

@dataclass
class CommentHistroySplitterSetting:
    '''a class which has load settings'''
    load_file_name: str
    encoding: str = 'utf-8_sig'
    incident_id_col_name: str = "incident_id"
    register_user_col_name: str = "registered_by"
    register_date_col_name: str = "registered_date"
    desctiption_col_name: str = "description"
    comment_histroy_col_name: str = "comment_history"

class CommentHistroySplitter:
    '''class to make comment histroy data.'''

    INCIDENT_ID_COL_POS: int = 1
    REGISTER_USER_COL_POS: int = 2
    REGISTER_DATE_COL_POS: int = 3
    DESCRIPTION_COL_POS: int = 4
    COMMENT_HIST_COL_POS: int = 5

    COMMENT_DIV_REGISTER = "新規登録"

    @classmethod
    def get_comment_histroy_csv_from_file(cls, load_settings: CommentHistroySplitterSetting, out_file_name, out_file_encoding="utf-8_sig" ):
        '''output comment history csv file from the incidents csv file. '''

        qa_data_df = pd.read_csv(
            load_settings.load_file_name,
            usecols=[
                load_settings.incident_id_col_name,
                load_settings.register_user_col_name,
                load_settings.register_date_col_name,
                load_settings.desctiption_col_name,
                load_settings.comment_histroy_col_name
            ],
            encoding=load_settings.encoding,
            encoding_errors='replace'
        )

        cls.get_comment_histroy_csv(qa_data_df, out_file_name, out_file_encoding)

    @classmethod
    def get_comment_histroy_csv(cls, qa_data_df, out_file_name, out_file_encoding='utf-8_sig'):
        '''output csv file of comment history'''

        # Check if the output file already exists
        if os.path.exists(out_file_name):
            raise ValueError("Output file already exists. file name: " + out_file_name)

        comment_histroy_df = cls.get_comment_history_df(qa_data_df)
        comment_histroy_df.to_csv(out_file_name, header=True, index=False, encoding=out_file_encoding)


    @classmethod
    def get_comment_history_df(cls, qa_data_df: DataFrame):
        '''get comment history dataframe'''

        # Make the lists first, and append data to them,
        # and finaly make a dataframe from the lists.
        # (for better performance)
        list_incident_id = []
        list_comment_seq = []
        list_comment_div = []
        list_comment_user = []
        list_comment_date = []
        list_comment = []

        for  row in qa_data_df.itertuples() :
            # add the properties of the incident detail as a first comment.(seq = 0)
            list_incident_id.append(row[cls.INCIDENT_ID_COL_POS])
            list_comment_seq.append(0)
            list_comment_div.append(cls.COMMENT_DIV_REGISTER)
            list_comment_user.append(row[cls.REGISTER_USER_COL_POS])
            list_comment_date.append(row[cls.REGISTER_DATE_COL_POS])
            list_comment.append(row[cls.DESCRIPTION_COL_POS])

            # When comment history is blank,
            # the type is judged as int and splitline() will cause an error.
            # To avoid this case, check the type first.
            if isinstance(row[cls.COMMENT_HIST_COL_POS], str):

                # In the comment history column, each comment mekes only one line.
                # So using splitline(), we can extract the comments one by one.
                i = 1
                comment_str_carry_over: str = ""
                for comment_str in row[cls.COMMENT_HIST_COL_POS].splitlines():

                    try:
                        comment_date, comment_div, comment_user, comment = cls.devide_comment_string(comment_str)
                    except AttributeError:
                        # this error means that comment_string dose not have the pattern
                        # like "(Close:User 2023/10/10)" on its end.
                        # this also means that the comment does not end here and sill continues.
                        # so carry over the comment_string to next loop as comment_str_carry_over.
                        comment_str_carry_over = comment_str_carry_over + comment_str
                    except Exception as e:
                        # skip any data that causes errors.
                        print("skipping the error on comment history splitting. incident id: " + row[cls.INCIDENT_ID_COL_POS] + " / error: " + str(e))
                    else:
                        comment = comment_str_carry_over + comment
                        # add data to lists
                        list_incident_id.append(row[cls.INCIDENT_ID_COL_POS])
                        list_comment_seq.append(i)
                        list_comment_div.append(comment_div)
                        list_comment_user.append(comment_user)
                        list_comment_date.append(comment_date)
                        list_comment.append(comment)

                        comment_str_carry_over = ""
                        i=i+1



        comment_history_df = pd.DataFrame({
            "incident_id": list_incident_id,
            "comment_seq": list_comment_seq,
            "comment_div": list_comment_div,
            "comment_by": list_comment_user,
            "comment_date":list_comment_date,
            "comment":list_comment
        })

        return comment_history_df


    @classmethod
    def devide_comment_string(cls, comment_string):
        '''
        Divide comment string to its date, division, user, comment.

        input comment string
            This incident has been closed.(Close:Team)User 2023/10/10)
        output 
            comment_date = "2023/10/10"
            comment_div = "Close"
            comment_user = "Team)User"
            comment = "This incident has been closed."
        '''
        # device input using regrex
        comment_meta_string = re.search(r"\([^:\(\)]+?:[^:]+ [0-9]{4}\/[0-9]{1,2}/[0-9]{1,2}\)$", comment_string).group()
        comment_date = comment_meta_string[-11:-1]
        comment_div = comment_meta_string[1:comment_meta_string.find(":")]
        comment_user = comment_meta_string[len(comment_div)+2:len(comment_meta_string)-12]
        comment = comment_string[0:len(comment_string) - len(comment_meta_string)]
        return comment_date, comment_div, comment_user, comment
