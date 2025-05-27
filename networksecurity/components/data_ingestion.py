from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

## Configuration of the Data Ingestion Config
from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact

import os
import sys
import pandas as pd
import numpy as np 
import pymongo
from typing import List
from sklearn.model_selection import train_test_split

from dotenv import load_dotenv
load_dotenv()

MONGO_DB_URL=os.getenv("MONGO_DB_URL")

class DataIngestion:
    def __init__(self,data_ingestion_config:DataIngestionConfig):
        try:
            self.data_ingestion_config=data_ingestion_config
            print(f"DEBUG: DataIngestion initialized with config: {data_ingestion_config}")
        except Exception as e:
            raise NetworkSecurityException(e,sys)


    def export_collection_as_dataframe(self):
        """
        Read Data from MongoDB
        """
        try:
            database_name=self.data_ingestion_config.database_name
            collection_name=self.data_ingestion_config.collection_name
            
            # DEBUG: Check configuration values
            print(f"DEBUG: Database name: {database_name}")
            print(f"DEBUG: Collection name: {collection_name}")
            print(f"DEBUG: MongoDB URL: {MONGO_DB_URL[:20]}..." if MONGO_DB_URL else "DEBUG: MongoDB URL is None!")
            
            self.mongo_client=pymongo.MongoClient(MONGO_DB_URL)
            print(f"DEBUG: MongoDB client created successfully")
            
            # Test connection
            try:
                self.mongo_client.admin.command('ping')
                print("DEBUG: MongoDB connection successful")
            except Exception as ping_error:
                print(f"DEBUG: MongoDB connection failed: {ping_error}")
            
            collection=self.mongo_client[database_name][collection_name]
            print(f"DEBUG: Collection object created: {collection}")
            
            # Check if collection exists and count documents
            try:
                doc_count = collection.count_documents({})
                print(f"DEBUG: Number of documents in collection: {doc_count}")
            except Exception as count_error:
                print(f"DEBUG: Error counting documents: {count_error}")
            
            # Get a sample document to check structure
            try:
                sample_doc = collection.find_one()
                print(f"DEBUG: Sample document: {sample_doc}")
            except Exception as sample_error:
                print(f"DEBUG: Error getting sample document: {sample_error}")
            
            # Convert to dataframe
            cursor_data = list(collection.find())
            print(f"DEBUG: Number of documents retrieved: {len(cursor_data)}")
            
            df=pd.DataFrame(cursor_data)
            print(f"DEBUG: Initial dataframe shape: {df.shape}")
            print(f"DEBUG: Initial dataframe columns: {df.columns.tolist()}")
            
            if "_id" in df.columns.to_list():
                df=df.drop(columns=["_id"],axis=1)
                print(f"DEBUG: Dataframe shape after dropping _id: {df.shape}")

            df.replace({"na":np.nan},inplace=True)
            print(f"DEBUG: Final dataframe shape: {df.shape}")
            print(f"DEBUG: Final dataframe info:")
            print(df.info())
            
            return df
            
        except Exception as e:
            print(f"DEBUG: Error in export_collection_as_dataframe: {e}")
            raise NetworkSecurityException(error_message=e, error_details=sys) 

    def export_data_into_feature_store(self,dataframe: pd.DataFrame):
        try:
            print(f"DEBUG: export_data_into_feature_store called with dataframe shape: {dataframe.shape}")
            
            feature_store_file_path=self.data_ingestion_config.feature_store_file_path
            print(f"DEBUG: Feature store file path: {feature_store_file_path}")
            
            #creating folder
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path,exist_ok=True)
            print(f"DEBUG: Directory created: {dir_path}")
            
            dataframe.to_csv(feature_store_file_path,index=False,header=True)
            print(f"DEBUG: Dataframe saved to CSV successfully")
            
            return dataframe

        except Exception as e:
            print(f"DEBUG: Error in export_data_into_feature_store: {e}")
            raise NetworkSecurityException(e,sys)

    def split_data_as_train_test(self,dataframe: pd.DataFrame):
        try:
            print(f"DEBUG: split_data_as_train_test called with dataframe shape: {dataframe.shape}")
            
            if dataframe.empty:
                print("DEBUG: WARNING - Dataframe is empty! Cannot perform train-test split.")
                return
            
            train_set, test_set = train_test_split(
                dataframe, test_size=self.data_ingestion_config.train_test_split_ratio
            )
            
            print(f"DEBUG: Train set shape: {train_set.shape}")
            print(f"DEBUG: Test set shape: {test_set.shape}")
            
            logging.info("Performed train test split on the dataframe")
            logging.info("Exited split_data_as_train_test method of Data_Ingestion Class")

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)
            
            print(f"DEBUG: Training file path: {self.data_ingestion_config.training_file_path}")
            print(f"DEBUG: Testing file path: {self.data_ingestion_config.testing_file_path}")

            logging.info(f"Exporting train and test file path.")

            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )
            test_set.to_csv(
                self.data_ingestion_config.testing_file_path, index=False, header=True
            )
            logging.info(f"Exported train and test file path")

        except Exception as e:
            print(f"DEBUG: Error in split_data_as_train_test: {e}")
            raise NetworkSecurityException(e,sys)

    def initiate_data_ingestion(self):
        try:
            print("DEBUG: Starting data ingestion process...")
            
            dataframe=self.export_collection_as_dataframe()
            print(f"DEBUG: After export_collection_as_dataframe, shape: {dataframe.shape}")
            
            dataframe=self.export_data_into_feature_store(dataframe)
            print(f"DEBUG: After export_data_into_feature_store, shape: {dataframe.shape}")
            
            self.split_data_as_train_test(dataframe)
            print("DEBUG: Train-test split completed")
            
            dataingestionartifact=DataIngestionArtifact(
                trained_file_path=self.data_ingestion_config.training_file_path,
                test_file_path=self.data_ingestion_config.testing_file_path
            )
            
            print("DEBUG: Data ingestion process completed successfully")
            return dataingestionartifact

        except Exception as e:
            print(f"DEBUG: Error in initiate_data_ingestion: {e}")
            raise NetworkSecurityException(error_message=e, error_details=sys)