"""Generate seed csv files from QAWeb"""
from pathlib import Path
import os
from modules.qaweb_data_extractor import QaWebDataExtractor
from modules.csv_converter import CsvConverter
from modules.comment_history_splitter import CommentHistroySplitter
from modules.comment_history_splitter import CommentHistroySplitterSetting


## preparetion
CURRENT_DIR = Path(__file__).parent
BASE_DIR_NAME = str(CURRENT_DIR.parent.resolve())
QAWEB_CONFIG_FILE_NAME = BASE_DIR_NAME + "/conf/QaWebDataExtractorConfig.yml"
COLUMN_MAP_CONFIG_FILE_NAME = BASE_DIR_NAME + "/conf/qaweb__incidents_column_map.yml"

RAW_QA_FILE_NAME = BASE_DIR_NAME + "/work/raw_qaweb__incidents.csv"
SEED_QA_FILE_NAME = BASE_DIR_NAME + "/seeds/seed_qaweb__incidents.csv"
SEED_COMMENT_HISTORY_FILE_NAME = BASE_DIR_NAME + "/seeds/seed_qaweb__incident_comments.csv"


## incident data
if os.path.exists(RAW_QA_FILE_NAME):
    os.remove(RAW_QA_FILE_NAME)

extractor = QaWebDataExtractor.build_from_file(QAWEB_CONFIG_FILE_NAME)
extractor.login()
extractor.get_all_qa_csv(RAW_QA_FILE_NAME)

if os.path.exists(SEED_QA_FILE_NAME):
    os.remove(SEED_QA_FILE_NAME)

CsvConverter.convert_csv(RAW_QA_FILE_NAME, SEED_QA_FILE_NAME, COLUMN_MAP_CONFIG_FILE_NAME)

## incident comment history data
if os.path.exists(SEED_COMMENT_HISTORY_FILE_NAME):
    os.remove(SEED_COMMENT_HISTORY_FILE_NAME)

settings = CommentHistroySplitterSetting(SEED_QA_FILE_NAME)
CommentHistroySplitter.get_comment_histroy_csv_from_file(settings,SEED_COMMENT_HISTORY_FILE_NAME)




## post execution process
os.remove(RAW_QA_FILE_NAME)
