import multiprocessing
import sys
import os
import sqlite3
import requests
import glob
import logging

from tqdm import tqdm
from biomart import BiomartServer
from agfusion import utils
import pandas

def split_into_n_lists(seq, n):
  avg = len(seq) / float(n)
  out = []
  last = 0.0

  while last < len(seq):
    out.append(seq[int(last):int(last + avg)])
    last += avg

  return out

def _chunker(seq, n):
    """
    From a list return chunks of size n
    """

    return (seq[pos:pos + n] for pos in xrange(0, len(seq), n))

def _collect_results(result):

    if result is None:
        logging.error(' Could not fetch some data for some reason...')
        sys.exit()

    results.extend(result)

def _query_job(index,filters,attributes,ntries,ensembl,return_dict):

    data = []

    try:

        r=ensembl.search({
            'filters':filters,
            'attributes':attributes[0]
        })

        for line in r.iter_lines():
            line = line.decode('utf-8').split('\t')
            data.append(line)

        return_dict[index]=data

    except requests.HTTPError:
        if ntries==3:
            logging.error(' Max number of retries on this chunk!')
            raise
        else:
            logging.debug(' Chunk too large, splitting into two chunk and retrying...')
            for f in split_into_n_lists(filters[filters.keys()[0]],2):
                filter_sub = {filters.keys()[0]:f}
                _query_job(
                    index,
                    filter_sub,
                    attributes,
                    ntries+1,
                    ensembl,
                    return_dict
                )
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

    return

class AGFusionDB(object):
    """
    Class to handle methods around interacting with the AGFusion SQLite3
    database

    name: name of the database
    reference_name
    """

    def __init__(self,database):

        self.database=os.path.abspath(database)
        self.fastas = {}

        self.logger = logging.getLogger('AGFusion')
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        assert os.path.exists(self.database), "database does not exist!"

        self.conn = sqlite3.connect(
            self.database
        )
        self.c = self.conn.cursor()
        self.conn.commit()

    def _check_table(self,table):
        """
        Check if table exists
        """

        self.c.execute("SELECT * FROM sqlite_master WHERE name = \'" + table + "\' and type='table';")

        if len(self.c.fetchall())==0:
            return False
        else:
            return True

    def close(self):
        """
        Close the connection to the database
        """

        self.conn.close()

class AGFusionDBBManager(AGFusionDB):
    """
    Class to handle methods managing the SQLite3 database

    name: name of the database
    reference
    """

    def __init__(self,database,genome):

        if not os.path.exists(database):
            fout = open(os.path.abspath(database),'a')
            fout.close()

        super(AGFusionDBBManager,self).__init__(database)

        self.genome=genome

        if self.genome=='GRCh38' or self.genome=='GRCh37':
            self.ensembl_dataset='hsapiens_gene_ensembl'
            self.ensembl_server='http://useast.ensembl.org/biomart'
        elif self.genome=='GRCm38':
            self.ensembl_dataset='mmusculus_gene_ensembl'
            self.ensembl_server='http://useast.ensembl.org/biomart'

        self._ensembl=None
        self._biomart=None

        self._check_for_tables()

    def _check_for_tables(self):

        for i in utils.PROTEIN_DOMAIN:
            if not self._check_table(i[0]):
                self.c.execute(
                    "CREATE TABLE " + self.genome + '_' + i[0] +" (" + \
                    "ensembl_transcript_id text," +
                    i[0] + " text," + \
                    i[1] + " text," + \
                    i[2] + " text" + \
                    ")"
                )
                self.conn.commit()

    def _fetch(self,ids,filters,attributes,p,batch_size):
        """
        Abstract method for fetching data in batches from the biomart server.
        The data is fetched in batches because the biomart python package does
        not seem to like having to fetch data in too large of chunks
        """

        #setup multiprocessing

        pool = multiprocessing.Pool(p)
        manager = multiprocessing.Manager()
        return_dict = manager.dict()

        #chunk the data

        chunks = [i for i in _chunker(ids,batch_size)]
        sub_chunks = [i for i in _chunker(chunks,p)]

        index=0

        #fetch the data

        for chunk in tqdm(sub_chunks):
            jobs = []
            for id_set in chunk:
                p = multiprocessing.Process(target=_query_job,args=(index,{filters:id_set},[attributes],0,self._ensembl,return_dict,))
                jobs.append(p)
                p.start()
                index+=1

            for j in jobs:
                j.join()

        return return_dict

    def _fetch_protein_level_info(self,transcripts,p,columns,table):

        data = self._fetch(
            ids=transcripts,
            filters='ensembl_transcript_id',
            attributes=['ensembl_transcript_id'] + columns,
            p=p,
            batch_size=100
        )

        #process data

        self.logger.info(' Adding Biomart information to the database...')

        #format the data correctly so it can be put into the database

        data_into_db = []
        for index, chunk in data.items():
            for r in chunk:
                if str(r[1])!='':
                    data_into_db.append([
                        str(r[0]),
                        str(r[1]),
                        str(r[2]),
                        str(r[3])
                    ])

        self.c.execute('DELETE FROM ' + table)
        self.conn.commit()

        self.c.executemany('INSERT INTO ' + table + ' VALUES (?,?,?,?)', data_into_db)
        self.conn.commit()

    def add_pfam(self,pfam_file='pdb_pfam_mapping.txt'):
        data = pandas.read_table(pfam_file,sep='\t')

        def clean_name(x):
            return x.split('.')[0]

        data = dict(zip(data['PFAM_ACC'].map(clean_name),data['PFAM_Name']))
        data = map(lambda x: [x[0],x[1]],data.items())

        self.c.execute('drop table if exists PFAMMAP')

        self.c.execute(
            "CREATE TABLE PFAMMAP (" + \
            "pfam_acc text," + \
            "pfam_name text" + \
            ")"
        )
        self.conn.commit()

        self.c.executemany('INSERT INTO PFAMMAP VALUES (?,?)', data)
        self.conn.commit()


    def fetch_data(self,pyensembl_data,p):

        self._biomart = BiomartServer(self.ensembl_server)
        self._ensembl = self._biomart.datasets[self.ensembl_dataset]

        self._fetch_protein_level_info(
            pyensembl_data.transcript_ids(),
            p,
            utils.PFAM_DOMAIN,
            self.genome + '_pfam'
        )
