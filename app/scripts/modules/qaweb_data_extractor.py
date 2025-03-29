"""Extract data from QAWeb"""
from typing import List
import os
import tempfile
import re
import requests
import yaml
import pandas as pd

class QaWebDataExtractor :
    """Class to extract QA data from QAWeb"""

    def __init__(self, **args):
        """Constructor"""

        # constants
        self.err_msg_no_session = "No session. Login first using login() method to get session."
        self.err_msg_file_already_exsists = "Output file already exists. file name: "
        self.err_msg_failed_to_get_max_no = "Failed to get the max QA from QAWeb"
        self.err_msg_invalid_args = "Invalid arguments"

        # Initialize variables from the arguments
        if not self._is_valid_args(args):
            raise ValueError(self.err_msg_invalid_args)

        self.qaweb_info = {
            'site': args.get('site'),
            'login_page': args.get('login_page'),
            'menu_page': args.get('menu_page'),
            'csv_page': args.get('csv_page'),
            'category_param': args.get('category_param'),
            'category': args.get('category'),
            'login_user': args.get('login_user'),
            'login_pass': args.get('login_pass')
        }

        self.script_settings = {
            'records_per_request': args.get('records_per_request'),
            'work_dir': args.get('work_dir')
        }

        self.has_work_dir_arg = False
        if self.script_settings['work_dir'] is not None:
            if not os.path.isdir(self.script_settings['work_dir']):
                raise ValueError('No such directory. work_dir: ' + self.script_settings['work_dir'])
            self.has_work_dir_arg = True

        # status flag represent if the class has been initialized
        self.has_session = False

        # Initialize a session object
        self.session = requests.Session()

    @classmethod
    def build_from_file(cls, config_file_name):
        """Initialize the class from a config file"""

        # Read the config file
        with open(config_file_name, 'r', encoding='cp932') as config_file:
            config = yaml.safe_load(config_file)

        return cls(
            site = config['QAWebInfo']['site'],
            login_page = config['QAWebInfo']['loginPage'],
            menu_page = config['QAWebInfo']['menuPage'],
            csv_page = config['QAWebInfo']['csvPage'],
            category_param = config['QAWebInfo']['categoryParam'],
            category = config['QAWebInfo']['category'],
            login_user = config['QAWebInfo']['authInfo']['user'],
            login_pass = config['QAWebInfo']['authInfo']['password'],
            records_per_request = config['scriptSettings']['recordsPerRequest']
        )

    def login(self):
        """Login to QAWeb and switch context to the specified category"""
        self._create_session()
        self.switch_context(self.qaweb_info['category'])

    def _is_valid_args(self, args):
        """Check if the arguments are valid"""
        required_keys = [
            'site', 
            'login_page', 
            'menu_page', 
            'csv_page', 
            'category_param', 
            'category', 
            'login_user', 
            'login_pass',
            'records_per_request'
        ]
        for key in required_keys:
            if key not in args or not args[key]:
                return False
        return True

    def _create_session(self):
        """Login to QAWeb and create a valid session(cookie)"""

        login_url = self.qaweb_info['site']+ self.qaweb_info['login_page']
        form_fields = {
            "usr": self.qaweb_info['login_user'],
            "pwd": self.qaweb_info['login_pass']
        }
        response = self.session.post(login_url, data=form_fields)

        if response.status_code != 200:
            raise ValueError("Failed to login. http status:" + str(response.status_code))

        self.has_session = True


    def switch_context(self, category):
        """Switch context to the specified category("FDP" for GX etc)"""

        # check if the class has been initialized
        if not self.has_session:
            raise AttributeError(self.err_msg_no_session)

        self.qaweb_info['category'] = category
        menu_url = self.qaweb_info['site'] + self.qaweb_info['menu_page'] + \
            '?' + self.qaweb_info['category_param'] + '=' + self.qaweb_info['category']
        response = self.session.get(menu_url)
        response.encoding = response.apparent_encoding

        # check http status
        if response.status_code != 200:
            raise ValueError('Failed to switch category. http status:' + str(response.status_code))

        # check if the category is correctly switched using string in the response.
        # see get_max_qa_no_in_int() for detail
        qa_no_digests_regex = self.qaweb_info['category'] + '-[0-9]{6},[0-9]{6}'
        qa_no_strings = re.findall(qa_no_digests_regex, response.text)

        if qa_no_strings is None or len(qa_no_strings) == 0:
            raise AttributeError('Failed to switch category. Category does not match.' )

    def get_max_qa_no_in_int(self):
        """
        get the max qa no of specified category.

        the response from the menu page contains text like following,
        and we can get max qa no from the commentouted parts.
        the max no is in the last part of the line. "015142" is the one.

        --------------
         <b>QA一覧</b><br>
        <!--
            15142,302,302,298,FDP-015101,015142
        -->
        ■ <a href="3table.pl?FDP-015101" target="FRAME2" title="昇順に表示" onclick="return chengchk()">FDP-015101～</a>
        <a href="3table2.pl?FDP-015101" target="FRAME2" title="降順に表示" onclick="return chengchk()">015142</a><br>
        <!--
            15142,301,302,298,FDP-015051,015100
        -->
        ■ <a href="3table.pl?FDP-015051" target="FRAME2" title="昇順に表示" onclick="return chengchk()">FDP-015051～</a>
        <a href="3table2.pl?FDP-015051" target="FRAME2" title="降順に表示" onclick="return chengchk()">015100</a><br>

        """

        if not self.has_session:
            raise AttributeError(self.err_msg_no_session)

        # get the menu page
        qa_no_url = self.qaweb_info['site'] + self.qaweb_info['menu_page']
        response = self.session.get(qa_no_url)

        if response.status_code != 200:
            raise ValueError('Failed to get the menu page. http status: ' + str(response.status_code))

        # extract the qa no part from the response using regex
        qa_no_digests_regex = self.qaweb_info['category'] + '-[0-9]{6},[0-9]{6}'
        qa_no_strings = re.findall(qa_no_digests_regex, response.text)

        if qa_no_strings is None or len(qa_no_strings) == 0:
            raise AttributeError(self.err_msg_failed_to_get_max_no)

        try :
            qa_max_no =  int(qa_no_strings[0].split(",")[-1])
        except ValueError as e:
            raise ValueError(self.err_msg_failed_to_get_max_no) from e


        return qa_max_no

    def get_qa_csv(self, qa_no_list: List[str], out_file_name):
        """Download a CSV from given QA no list using records_per_request as batch size"""

        # Check if the output file already exists
        if os.path.exists(out_file_name):
            raise ValueError(self.err_msg_file_already_exsists + out_file_name)

       # download the data in batches and add to the output file
        with open(out_file_name, 'w', encoding='cp932', errors='replace') as output_stream:

            # initialize the indexes and batch size
            idx_start = 0
            idx_end = 0
            batch_size = self.script_settings['records_per_request']

            # download the data by batch size and add to the output file
            while idx_start < len(qa_no_list):

                # donload the data by batch size
                idx_end = min(idx_start + batch_size , len(qa_no_list))
                tmp_out_file_name = tempfile.mktemp()
                self._get_qa_csv_single(qa_no_list[idx_start:idx_end], tmp_out_file_name)

                # add tmp file to the output file
                with open(tmp_out_file_name, 'r', encoding='cp932', errors='replace') as tmp_file:
                    lines = tmp_file.readlines()
                    # add only data part (without header) after second batch
                    if idx_start == 0:
                        start = 0
                    else:
                        start = 1
                    for line in lines[start:]:
                        output_stream.write(line)

                # remove the tmp file
                os.remove(tmp_out_file_name)

                # for next loop
                idx_start += batch_size

    def _get_qa_csv_single(self, qa_no_list: List[str], out_file_name):
        """Simply download a CSV from given QA no list"""

        if not self.has_session:
            raise AttributeError(self.err_msg_no_session)

        # Check if the output file already exists
        if os.path.exists(out_file_name):
            raise ValueError(self.err_msg_file_already_exsists + out_file_name)

        # Check if the QA number is valid
        qa_no_format = '^' + self.qaweb_info['category'] + '-[0-9]{6}'
        for qa_no in qa_no_list:
            if not re.match(qa_no_format, qa_no):
                raise ValueError("Invalid QA number: " + qa_no)

        # Prepare the request parameter
        qa_no_param = " ".join(qa_no_list)
        csv_request_params = {
            "TBLLIST": qa_no_param
        }

        # Download the QA data
        url = self.qaweb_info['site'] + self.qaweb_info['csv_page']
        response = self.session.post(url, data=csv_request_params)

        # Write the data to the output file
        with open(out_file_name, 'wb') as output_stream:
            output_stream.write(response.content)

    def get_all_qa_csv(self, out_file_name):
        """Download all the QA data from 1 to max_qa_no"""
        max_qa_no = self.get_max_qa_no_in_int()
        qa_no_list = [self.qaweb_info['category'] + '-' + str(i).zfill(6) for i in range(1, max_qa_no + 1)]
        self.get_qa_csv(qa_no_list, out_file_name)


    def get_work_file_name(self):
        """Get a work file name"""

        if self.has_work_dir_arg :
            return tempfile.mktemp(dir=self.script_settings['work_dir'])
        return tempfile.mktemp()

    def get_hosp_data_csv(self, out_file_name):
        None

    def get_qa_df(self, qa_no_list):
        """Get a DataFrame from QAWeb data""" 

        # Get QA data as a CSV file and return it as a DataFrame
        work_file_name = self.get_work_file_name()
        self.get_qa_csv(qa_no_list, work_file_name)
        result = pd.read_csv(work_file_name, encoding='cp932')
        os.remove(work_file_name)

        return result

    def get_all_qa_df(self):
        """Get a DataFrame from QAWeb data (all)""" 

        # Get QA data as a CSV file and return it as a DataFrame
        work_file_name = self.get_work_file_name()
        self.get_all_qa_csv(work_file_name)
        result = pd.read_csv(work_file_name, encoding='cp932')
        os.remove(work_file_name)

        return result

    def get_hosp_data_df(self):
        None
