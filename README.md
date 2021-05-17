# Desafio final do Bootcamp Engenheiro de Dados do IGTI

## Proposta

O desafio consiste em criar um pipeline utilizando o Airflow, o qual deve extrair dados do PNAD armazenados no MongoDB da IGTI, extrair dados da API do IBGE, depois salvar os dados em um Data Lake e por fim salvar os dados tratados em um DW com a finalidade de realizar consultas para responder às questões do desafio. Todo o pipeline deve ser implementado utilizando Cloud Computing.

## Tecnologias utilizadas

Para a implementação do pipeline de dados foram utilizados dois players em Cloud Computing: o [Google Cloud Platform](https://cloud.google.com) o qual foi criada uma instância de VM do Debian com o Airflow em execução e a [Microsoft Azure](https://azure.microsoft.com/pt-br/) executando o Azure Blob Storage como Data Lake e o PostgreSQL como DW.

Segue um diagrama com a representação das tecnologias utilizadas no pipeline:

![](/images/01_diagrama_pipeline_desafio_igti.png "pipeline de dados")

## Provisionamento de instância de VM no Google Cloud Platform

Após criar uma conta gratuita no GCP, basta acessar a opção **Compute Engine - Instâncias de VM**

A criação da VM é bastante intuitiva, bastando preencher todos os campos obrigatórios. No fim da criação da VM é importante definir um IP estático para que seja possível conectar via SSH.

![](/images/02_vm_gcp.png "VM GCP")

### Configurações da VM

Inicialmente será necessário acessar via SSH pelo navegador para conectar na VM.

![](/images/03_vm_gcp_acesso_ssh_browser_.png "Acesso SSH pelo browser")

Com o acesso à VM o próximo passo é fazer alterações no arquivo sshd_config para descomentar os parâmetros necessários para permitir o acesso na porta 22, após as configurações é só reiniciar o serviço SSH.

Um passo também importante visando um pouco de segurança é a criação de um usuário para que o mesmo faça o acesso via SSH sem ser o usuário root.

A próxima etapa é fazer a configuração no Firewall para liberar a porta 8080, pois é através dela que vamos acessar a interface do Airflow.

Vamos acessar a opção **Rede VPC - Firewall** para definir uma regra de Firewall.

A seguir como ficou a regra de Firewall para permitir o acesso à porta 8080.

![](/images/04_vm_gcp_firewall.png "Regra de Firewall")

Agora precisamos editar a VM para liberar o acesso remoto. No campo **Tags de rede** basta adicionar a tag criada no passo anterior. Conforme a imagem a seguir, observe que foi adionada a tag **access-http**

![](/images/05_vm_gcp_tags_rede.png "Tags de rede")

## Criar conta de armazenamento e banco de dados na Azure

Assim como o GCP a Microsoft Azure permite utilizar uma conta gratuita por 30 dias com um valor creditado a ser gasto durante o período de uso.

O Azure possui uma interface mais intuitiva que o GCP. Qualquer tecnologia a ser implantada pode ser encontrada em **Todos os serviços**.  

Sendo assim o que precisa ser criado é um Grupo de recursos. Após a criação do grupo de recursos é preciso criar uma Conta de armazenamento a qual servirá como Data Lake. Por fim criar um banco de dados PostgreSQL. Ambos devem ser associados ao Grupo de recursos.

![](/images/06_azure_recursos.png "Recursos Azure")

### Configurações do PostgreSQL

Para permitir o acesso de uma ferramenta cliente e da aplicação com o Airflow ao banco de dados é preciso criar uma regra de Firewall com os IPs da máquina local e da VM do GCP.

Basta clicar no recurso criado do PostgreSQL e depois em **Segurança de conexão** adicionar os IPs e Salvar.

![](/images/07_azure_regras_firewall_postgresql.png "Regras de Firewall PostgreSQL")


Após as configurações do Firewall, já é possível conectar com uma ferramenta cliente ao banco de dados, basta utilizar as credenciais de acesso informadas na criação do banco de dados. Ao conectar é necessário criar um banco de dados para que o mesmo seja o DW do pipeline de dados. Para o desafio o nome do banco de dados criado foi **db_desafio_igti**.

A ferramenta cliente utilizada para conectar no PostgreSQL da Azure foi o [DBeaver](https://dbeaver.io/)

## Instalação do Python e Airflow na VM do GCP e outras configurações

O repositório contém o arquivo [requirements.txt](https://github.com/andersonnrc/bootcamp-igti-ed-desafio-final/blob/main/requirements.txt) com todas as dependências que necessitam ser instaladas. Apesar disso vou demonstrar passo a passo o que precisa ser instalado.

1) No terminal, conectar via SSH à VM do GCP.

```
$ ssh [user]@[ip-vm]
```

2) Fazer download do Anaconda para instalar o Python

```
$ wget https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh
```

3) Instalar Anaconda

```
$ bash Anaconda3-2021.05-Linux-x86_64.sh
```

4) Criar um ambiente virtual

```
$ conda create -n airflow-igti python=3.8
```

5) Ativar ambiente virtual

```
$ conda activate airflow-igti
```

6) Instalar Airflow

```
$ pip install apache-airflow
```

7) Configurar Airflow

```
$ airflow db init
```

8) Criar usuário

```
$ airflow users create --username airflow --firstname Anderson --lastname Ribeiro --role Admin --email ar.andersonribeiro@gmail.com
```
Será pedido para digitar uma senha. Basta digitar e depois confirmar.

Mais alguns pacotes serão necessários instalar para conectar no MongoDB, no PostgreSQL e para o Azure Blob Storage.

9) Instalar dependência para conectar no MongoDB

```
$ pip install pymongo
```

10) Instalar dependência para acessar o Azure Blob Storage

```
$ pip install azure-storage-blob==2.1.0
```

11) Instalar dependência para conectar no PostgreSQL

```
$ pip install psycopg2-binary
```

12) Agora basta observar no diretório home do usuário que há uma pasta criada com o nome **airflow**. Basta entrar na pasta. Será necessário criar uma pasta com o nome **dags**. Entre nessa pasta e crie um arquivo com o nome [desafio_final_igti.py](https://github.com/andersonnrc/bootcamp-igti-ed-desafio-final/blob/main/dags/desafio_final_igti.py) e copiar e colar o respectivo código.

13) Criação de arquivo de shell script para inicializar servidor web do Airflow juntamente com o scheduler. Voltar ao diretório anterior e criar um arquivo com o nome **start.sh** e informar o conteúdo a seguir:

```
#!/bin/bash

airflow webserver -p 8080

airflow scheduler
```

Para dar permissão de execução ao arquivo basta digitar:

```
chmod +x start.sh
```

14) Execução do arquivo shell script em segundo plano para acessar a interface do airflow

```
nohup ./start.sh &
```

15) Acesso pelo browser.

Agora é só digitar o IP da VM do GCP seguido da porta 8080. Vai aparecer a tela de login. É só informar as credenciais de acesso fornecidas no passo 8.

![](/images/08_gcp_airflow_login.png "Tela login Airflow")

16) Criar variáveis no Airflow.

Para evitar informar no código da aplicação dados sensíveis relacionados a usuários, senhas e chaves, dados de conexão ao banco de dados etc, é possível cadastrar no Airflow, para isso é só acessar o menu **Admin - Variables**. Confira a seguir todas as variáveis cadastradas:

![](/images/09_gcp_airflow_variables.png "Variáveis Airflow")

## Execução da aplicação

Executar a aplicação é bem simples, necessitando apenas acessar a Dag na interface do Airflow e clicar em **Trigger DAG**

![](/images/10_gcp_airflow_trigger.png "Executar pipeline")

Após a execução o pipeline apresentará o resultado a seguir:

![](/images/11_gcp_airflow_pipeline_execution.png "Pipeline executado")

## Resultado

Vamos conferir os dados gravados no Azure Blob Storage:

![](/images/12_azure_blob_container.png "Contêiner criado na Azure com arquivos")

E vamos verificar os dados no PostgreSQL:

![](/images/13_azure_postgresql.png "Dados no PostgreSQL da Azure")

## Referências:

* [Google Cloud Platform](https://cloud.google.com)

* [Microsoft Azure](https://azure.microsoft.com/pt-br/)

* [Apache Airflow](https://airflow.apache.org/)

* [Gerenciar Blobs com SDK do Python](https://docs.microsoft.com/pt-br/azure/storage/blobs/storage-quickstart-blobs-python-legacy)

* [Configuração para conexão remota no GCP (criar tags de rede)](https://docs.microsoft.com/pt-br/azure/storage/blobs/storage-quickstart-blobs-python-legacy)

### Contato

[Linkedin](https://www.linkedin.com/in/anderson-ribeiro-carvalho)


