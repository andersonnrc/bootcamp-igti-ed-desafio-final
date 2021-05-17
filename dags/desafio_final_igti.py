from airflow.decorators import dag, task
from airflow.models import Variable
from datetime import datetime
import requests as req
import pandas as pd
import sqlalchemy
from pymongo import MongoClient
from azure.storage.blob import BlockBlobService, PublicAccess

# Constantes

# Azure Blob
data_path = '/tmp/'
account_name = Variable.get('account_name_azure')
account_key = Variable.get('account_key_azure')
container_name = Variable.get('container_name_azure')
path_azure = Variable.get('path_azure')

# MongoDB (IGTI)
mongo_user = Variable.get('mongo_user')
mongo_pass = Variable.get('mongo_pass')
mongo_host = Variable.get('mongo_host')
mongo_database = Variable.get('mongo_database')
mongo_collection = Variable.get('mongo_collection')

# PostgreSQL (Azure)
postgres_user = Variable.get('postgres_user')
postgres_password = Variable.get('postgres_password')
postgres_host = Variable.get('postgres_host')
postgres_port = Variable.get('postgres_port')
postgres_database = Variable.get('postgres_database')

default_args = {
    'owner': 'Anderson',
    'depends_on_past': False,
    'start_date': datetime(2021, 5, 14),
    'email': ['ar.andersonribeiro@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
}

@dag(default_args = default_args, schedule_interval = None, 
     description = 'ETL de dados do MongoDB e IBGE para o PostgreSQL e Azure Blob Storage')
def desafio_final_igti():

    @task
    def get_api():
        r = req.get('https://servicodados.ibge.gov.br/api/v1/localidades/estados/MG/mesorregioes')
        result = r.json()
        df = pd.DataFrame(result)[['id','nome']]
        file = df.to_csv(data_path + 'mesorregioes_mg.csv', sep = ';', index = False, encoding = 'utf-8')
        return '/tmp/mesorregioes_mg.csv'

    @task
    def get_mongodb():
        cliente = MongoClient(f'mongodb+srv://{mongo_user}:{mongo_pass}@{mongo_host}/{mongo_database}?retryWrites=true&w=majority')
        db = cliente[f'{mongo_database}']
        collection = db[f'{mongo_collection}']
        df = pd.DataFrame(list(collection.find()))
        file = df.to_csv(data_path + 'pnadc2020.csv', sep = ';', index = False, encoding = 'utf-8')
        return '/tmp/pnadc2020.csv'

    @task
    def upload_files_to_azure(file):

        blob_service_client = BlockBlobService(
            account_name,
            account_key
        )

        # Criar container
        blob_service_client.create_container(container_name)

        # Setar permissão para que os blobs sejam públicos
        blob_service_client.set_container_acl(
            container_name, 
            public_access=PublicAccess.Container
        )

        #Upload arquivo para Azure
        blob_service_client.create_blob_from_path(
            container_name, 
            file[5:], 
            file
        )

    @task
    def insert_data_postgres(path):
        con = sqlalchemy.create_engine(
            f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_database}"
        )
        df = pd.read_csv(path, sep = ';')
        if path[5:-4] == 'pnadc2020':
            df = df.loc[(df.idade >= 20) & (df.idade <= 40) & (df.sexo == 'Mulher')]
        df['dt_inclusao_registro'] = datetime.today()
        df.to_sql(path[5:-4], con, index = False, if_exists = 'replace', method = 'multi', chunksize = 1000)

    api = get_api()
    mongodb = get_mongodb()
    upload_data_api_azure = upload_files_to_azure(api)
    upload_data_mongodb_azure = upload_files_to_azure(mongodb)
    write_data_api_postgres = insert_data_postgres(api)
    write_data_mongodb_postgres = insert_data_postgres(mongodb)

desafio = desafio_final_igti()

