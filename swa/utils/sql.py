import sqlite3
import numpy as np
import pandas as pd
import math

class StdevFunc:
    """SQLITE aggregate stdev"""
    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 1

    def step(self, value):
        if value is None:
            return
        tM = self.M
        self.M += (value - tM) / self.k
        self.S += (value - tM) * (value - self.M)
        self.k += 1

    def finalize(self):
        if self.k < 3:
            return None
        return math.sqrt(self.S / (self.k-1))

class SQL:
    """Handle an SQLite database"""
    def __init__(self, database):

        self._con = database
        self._connect(name=self._con)

        self._con.create_aggregate("STDEV", 1, StdevFunc)

    # %% Basic interaction
    def _connect(self,name = 'name.db'):
        """Create a connection to a SQL database"""
        self._con = sqlite3.connect(name)

    def _disconnect(self):
        """Close the connection to a SQL database"""
        self._con.close()

    def _create_table(self, name, columns, types):
        """Create a sql table"""

        ncols = len(columns)
        ntypes = len(types)

        if ncols != ntypes:
            raise ValueError('Number of column names and types are not the same. %d != %d' % (ncols,ntypes))

        sql = ['CREATE TABLE %s (' % name]
        for i in range(ncols):
            if i < (ncols-1):
                sql.append('%s %s, ' % (columns[i], types[i]))
            else:
                sql.append('%s %s); ' % (columns[i], types[i]))

        self._con.execute(''.join(sql))

    def to_sql(self, df, name, if_exists='fail', **kwargs):
        """Write data stored in a DataFrame to a SQL database"""
        df.to_sql(name=name, con=self._con, if_exists=if_exists, **kwargs)

    def read_sql(self, sql):
        """Write SQL query or table into DataFrame"""
        return pd.read_sql(sql,con=self._con)

    def get_table(self,name):
        """Return a table form the database as DataFrame"""
        return self.read_sql("""SELECT * FROM %s""" % name)

    def drop_table(self, name):
        """Drop table"""
        self._con.execute("""DROP TABLE IF EXISTS {name}""")

    def show_tables(self):
        """Show tables"""
        table_names = self.get_tables()
        print('Tables in project: ', end='')
        for i,name in enumerate(table_names):
            if i < len(table_names)-1:
                end = ', '
            else:
                end = '\n'
            print(name,end = end)

    def get_tables(self):
        """Get all table names"""
        table_names = self._con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

        table_list = [name[0] for name in table_names]

        return table_list

    # %% Interaction with the geometry information
    def read_geometry(self,geometry_file):
        """read formikoj geometry file and add to database"""

        geom = pd.read_csv(geometry_file,delimiter=',',header=None,
                           names=['x', 'y', 'z',
                          'geophone', 'shots',
                          'first_geophone', 'num_geophones'])
        geom = geom.astype({'shots':str})
        geom.insert(0, 'station_id', np.arange(len(geom)) + 1)

        shots = pd.DataFrame(geom.loc[geom.shots != '-1', ['station_id','shots']])
        shots.insert(1, 'sin', np.arange(len(shots)) + 1)

        # split repeated shots at the same source location and add as new line
        shots['shots'] = shots['shots'].str.split(';')
        shots = shots.explode('shots')
        shots.insert(2,'rep', shots.groupby('station_id').cumcount()+1)

        # geophone indices
        recs = pd.DataFrame(geom[geom.geophone > 0]['station_id'])
        recs.insert(0, 'rin', np.arange(len(recs)) + 1)
        recs.astype({'rin':int, 'station_id':int})

        # add to database
        self.to_sql(geom,'geom', if_exists='replace')
        self.to_sql(shots, 'shots', if_exists='replace')
        self.to_sql(recs, 'recs', if_exists='replace')

    def get_geometry(self, sin, rep = 1):
        """Return the geometry information (source and receiver coordinates) for one source location and shot index
           as DataFrames"""

        sql = """SELECT s.sin, s.rep, g.x sx, g.y sy, g.z sz, g.first_geophone fg, g.num_geophones ng
                 FROM geom g
                 INNER JOIN shots s ON s.station_id == g.station_id
                 WHERE s.rep==%d AND s.sin==%d""" % (rep,sin)
        sht = self.read_sql(sql)

        if len(sht) != 1:
            raise ValueError

        rec = pd.DataFrame(columns=['rin', 'rx', 'ry','rz'])
        for i,rin in enumerate(np.arange(sht.fg.item(),sht.ng.item()+sht.fg.item())):
            sql = """SELECT r.rin, g.x rx, g.y ry, g.z rz
                     FROM geom g
                     INNER JOIN recs r ON r.station_id == g.station_id
                     WHERE r.rin==%d""" % rin
            tmp = self.read_sql(sql)
            rec = pd.concat([rec,tmp])

        return sht.reset_index(), rec.reset_index()

    def get_shotfile(self, sin, rep = 1):
        """Return the name of one shot file"""
        sql = """SELECT s.shots
                 FROM shots s
                 WHERE s.rep==%d AND s.sin==%d""" % (rep,sin)
        sht = self.read_sql(sql)

        return sht

    # %% Interaction with settings
    def read_setting(self, settings):
        """Read settings and add to database"""
        self.to_sql(settings, 'settings', if_exists='replace')

    def get_settings(self):
        """Return the settings DataFrame"""
        return self.get_table('settings')

    # %% Interact with seismic data
    def get_proc_labels(self):
        sql = """SELECT DISTINCT procset
                 FROM amps"""
        labels = self.read_sql(sql)['procset'].values
        return labels

    def check_data(self,table, params):
        """Check if entry in database"""

        sql = """SELECT procset, sin, rep
                  FROM %s
                  WHERE """ % table

        npar = len(params)
        for i,key in enumerate(params.keys()):

            if i < npar-1:
                sql += f"{key}=={params[key]} AND "
            else:
                sql += f"{key}=={params[key]}"

        df = self.read_sql(sql)

        return df.empty

    def delete_data(self,table, params):
        """delete entry from database"""
        sql = """DELETE FROM %s WHERE """ % table

        npar = len(params)

        for i,key in enumerate(params.keys()):
            if i < npar-1:
                sql += f"{key}=={params[key]} AND "
            else:
                sql += f"{key}=={params[key]}"
        self._con.execute(sql)

    def write_data(self, data, sin, rep, procset, wid = -1):
        """write processed data to database"""

        # TABLE amps
        # table column names
        recs = self.get_table('recs')
        columns = ['procset', 'wid', 'sin', 'rep']
        for i in recs.rin:
            columns.append('rin%d'%i)

        # table column types
        types = ['TEXT', 'INT', 'INT', 'INT'] + ['FLOAT'] * len(recs)

        # create the table if it does not exist
        # (TODO: necessary?? or better to create the tables when initializing the db??)
        if 'amps' not in self.get_tables():
            self._create_table('amps',columns,types)

        # create DataFrame
        df = pd.DataFrame(columns=columns)

        # current data to be added to table
        cur_sht_geom, cur_rec_geom = self.get_geometry(sin, rep)

        cur_stream = data
        cur_dt = cur_stream.dt  # sampling interval in s
        cur_delay = cur_stream.delay  # pre trigger
        cur_sampling_rate = cur_stream.sampling_rate # sampling rate
        cur_rec = cur_stream.receiver  # receiver positions
        cur_amps = cur_stream.st2amps()  # amplitudes (trace, amps)
        cur_amps_transpose = cur_amps.transpose()
        cur_npts = cur_stream.npts

        rin = np.zeros(len(cur_rec))
        for i, rec in enumerate(cur_rec):
            rin[i] = cur_rec_geom['rin'].loc[cur_rec_geom['rx'] == rec].item()

        amps_hdr = ['rin%d'%(int(i)) for i in rin]

        amps_df = pd.DataFrame(cur_amps_transpose, columns=amps_hdr)
        amps_df.insert(0, 'procset', procset)
        amps_df.insert(1, 'wid', wid)
        amps_df.insert(2, 'sin', sin)
        amps_df.insert(3, 'rep', rep)

        df = pd.concat([df, amps_df])

        # TABLE par
        # table column names
        columns = ['procset', 'wid', 'sin', 'rep', 'npts', 'dt', 'delay', 'sampling_rate']

        # table column types
        types = ['TEXT', 'INT', 'INT', 'INT', 'INT', 'FLOAT', 'FLOAT', 'FLOAT']

        if 'par' not in self.get_tables():
            self._create_table('par',columns,types)

        # create DataFrame
        par = [procset, wid, sin, rep, cur_npts, cur_dt, cur_delay, cur_sampling_rate]
        par_df = pd.DataFrame([par],columns=columns)

        # TABLE pid
        # table column types
        columns = ['procset', 'wid', 'sin', 'rep', 'rin']
        # table column types
        types = ['TEXT', 'INT', 'INT', 'INT', 'INT']

        # create the table if it does not exist
        # (TODO: necessary?? or better to create the tables when initializing the db??)
        if 'pid' not in self.get_tables():
            self._create_table('pid',columns,types)

        # create DataFrame
        pid = np.c_[np.full(len(rin),sin),
                        np.full(len(rin),rep),
                        rin]
        pid_df = pd.DataFrame(pid,columns=columns[2:])
        pid_df.insert(0,'procset',procset)
        pid_df.insert(1, 'wid', wid)

        params = {'sin':sin, 'rep':rep, 'procset': "'%s'" % procset, 'wid':wid}
        # add tables to database or replace if exists
        if self.check_data('amps',params):
            self.to_sql(df,name = 'amps', if_exists = 'append', index = False)
            self.to_sql(par_df, name='par', if_exists='append', index=False)
            self.to_sql(pid_df, name='pid', if_exists='append', index=False)
        # TODO: better way to update??
        else:
            if procset != 'raw':
                self.delete_data('amps',params)
                self.delete_data('par', params)
                self.delete_data('pid',params)
                #if self.check_data('amps', params):
                self.to_sql(df,name = 'amps', if_exists = 'append', index = False)
                self.to_sql(par_df, name='par', if_exists='append', index=False)
                self.to_sql(pid_df, name='pid', if_exists='append', index=False)

    def read_data(self,sin,rep, procset = 'proc1', wid = -1):
        """get processed data from database"""

        sql = """SELECT r.rin, g.x rx, g.y ry, g.z rz
                 FROM geom g
                 INNER JOIN recs r ON r.station_id == g.station_id
                 INNER JOIN pid p ON r.rin == p.rin
                 WHERE p.procset=='%s' AND p.wid==%d AND p.sin==%d AND p.rep==%d""" % (procset,wid,sin,rep)
        recs = self.read_sql(sql)

        sql = """SELECT s.sin, s.rep, g.x sx, g.y sy, g.z sz, g.first_geophone fg, g.num_geophones ng
                 FROM geom g
                 INNER JOIN shots s ON s.station_id == g.station_id
                 WHERE s.rep==%d AND s.sin==%d""" % (rep, sin)
        sht = self.read_sql(sql)

        sql = """SELECT procset, sin, rep, npts, dt, delay, sampling_rate
                 FROM par
                 WHERE procset=='%s' AND wid==%d AND sin==%d AND rep==%d""" % (procset, wid, sin, rep)
        par = self.read_sql(sql)

        # check if query was successful and select data
        if (not recs.empty) & (not sht.empty) & (not par.empty):
            columns = []
            for i in recs.rin:
                columns.append('rin%d'%i)
            sql = f"""SELECT {', '.join(columns)}
                     FROM amps
                     WHERE procset=='%s' AND wid==%d AND sin==%d AND rep==%d""" % (procset, wid, sin,rep)
            amps = self.read_sql(sql)

            return par, amps, recs, sht
        else:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def write_FV(self, data, sin, rep, procset = 'proc1', wid = -1):
        """write dispersion image data to database"""

        cur_stream = data
        cur_FV = cur_stream.dispersive_energy  # FV spectrum (vels, freq)
        cur_freq = cur_stream.frequency  # frequency range
        cur_vel = cur_stream.velocity  # testing phase velocity
        cur_ks = cur_stream.wavenumber  # wavenumber
        method = cur_stream.trafo_type

        # %% table for FV
        # table name
        tn = 'FV'

        # table column names
        columns = ['procset', 'wid', 'method', 'sin', 'rep', 'velocity', 'wavenumber']
        for i,f in enumerate(cur_freq):
            columns.append('f%d'%i)

        # table column types
        types = ['TEXT', 'INT', 'TEXT', 'INT', 'INT', 'FLOAT', 'FLOAT'] + ['TEXT'] * len(cur_freq)

        # create DataFrame
        df2 = pd.DataFrame(cur_FV,columns=columns[7:])
        for col in columns[7:]:
            df2[col] = df2[col].astype(str)

        df1 = pd.DataFrame({'procset':procset,
                            'wid': wid,
                            'method':method,
                            'sin': sin,
                            'rep': rep,
                            'velocity':cur_vel,
                            'wavenumber':cur_ks})

        df = pd.concat([df1,df2], axis=1)

        # create the table if it does not exist
        if tn not in self.get_tables():
            self._create_table(tn, columns, types)

        params = {'sin': sin, 'rep': rep, 'procset': "'%s'" % procset, 'wid': wid, 'method': "'%s'" % method}
        # append to table or replace if exists
        if self.check_data(tn, params):
            self.to_sql(df, name=tn, if_exists='append', index=False)
        else:
            self.delete_data(tn, params)
            self.to_sql(df, name=tn, if_exists='append', index=False)

        # %% Table for frequency
        tn = 'freq'
        # table column names
        columns = ['procset', 'wid', 'method', 'sin', 'rep', 'frequency']

        # table column types
        types = ['TEXT', 'INT', 'TEXT', 'INT', 'INT', 'FLOAT']

        # create DataFrame
        df = pd.DataFrame({'procset':procset,
                            'wid': wid,
                            'method': method,
                            'sin': sin,
                            'rep': rep,
                            'frequency':cur_freq})

        # create the table if it does not exist
        if tn not in self.get_tables():
            self._create_table(tn, columns, types)

        # append to table or replace if exists
        if self.check_data(tn,params):
            self.to_sql(df,name = tn, if_exists = 'append', index = False)
        else:
            self.delete_data(tn,params)
            self.to_sql(df, name = tn, if_exists = 'append', index = False)

    # def stack()

    def read_FV(self, sin, rep, procset='proc1', method='phaseshift', wid = -1):
        """get data from table FV for a certain wave-field transformation method"""

        if 'FV' in self.get_tables():
            sql = ("""SELECT *
                     FROM FV
                     WHERE procset=='%s' AND wid==%d AND sin==%d AND rep==%d AND method=='%s'"""
                   % (procset, wid, sin, rep, method))
            FV = self.read_sql(sql)

            sql = ("""SELECT frequency
                     FROM freq
                     WHERE procset=='%s' AND wid==%d AND sin==%d AND rep==%d AND method=='%s'"""
                   % (procset, wid, sin, rep, method))
            freq = self.read_sql(sql)

            if not FV.empty:
                freq = freq.frequency.values
                vel = FV.velocity.values
                kw = FV.wavenumber.values
                FV = FV.iloc[:, 7:7 + len(freq)].astype(complex).values
                return vel, kw, freq, FV
            else:
                return None, None, None, None

    def get_wids(self, sin, rep, procset):
        """return the window ids for a sin/rep pair"""

        sql = ("""SELECT DISTINCT wid
                 FROM amps
                 WHERE procset=='%s' AND sin==%d AND rep==%d AND wid!=-1""" % (procset, sin, rep))
        df = self.read_sql(sql)
        if not df.empty:
            return df.wid.to_list()
        else:
            return []

    def write_pd(self, df, sin, rep, procset = 'proc1'):
        """write phase differences to database"""

        # TABLE pd
        # table column names
        recs = self.get_table('recs')
        columns = ['procset', 'calc', 'sin', 'rep', 'wid', 'fids', 'frequency']
        for i in recs.rin.iloc[:-1]:
            columns.append('pd%d'%i)

        # table column types
        types = ['TEXT', 'TEXT', 'INT', 'INT', 'INT', 'INT', 'FLOAT'] + ['FLOAT'] * (len(recs)-1)

        # create the table if it does not exist
        if 'pd' not in self.get_tables():
            self._create_table('pd',columns,types)

        params = {'sin': sin, 'rep': rep, 'procset': "'%s'" % procset, 'wid': -1, 'calc': "'NONE'"}
        # append to table or replace if exists
        if self.check_data('pd',params):
            self.to_sql(df,name = 'pd', if_exists = 'append', index = False)
        else:
            self.delete_data('pd',params)
            #if self.check_data('pd', params):
            self.to_sql(df, name = 'pd', if_exists = 'append', index = False)

    def group_pd(self, sin, procset='proc1', by = 'AVG'):
        """Group phase difference data in case of repeated shots"""

        recs = self.get_table('recs')
        columns = ['procset', 'calc', 'sin', 'rep', 'wid', 'fids', 'frequency']
        for i in recs.rin.iloc[:-1]:
            columns.append('%s(pd%d) as pd%d' % (by,i,i))

        sql = "SELECT "
        for i,col in enumerate(columns):
            if i < len(columns)-1:
                sql+= col + ', '
            else:
                sql+= col + (" FROM pd WHERE procset=='%s' AND sin==%d "
                             "GROUP BY fids") % (procset, sin)

        df = self.read_sql(sql).replace({None: np.nan})
        df['calc'] = by

        params = {'sin': sin, 'procset': "'%s'" % procset, 'wid': -1, 'calc': "'%s'" % by}
        # append to table or replace if exists
        if self.check_data('pd',params):
            self.to_sql(df,name = 'pd', if_exists = 'append', index = False)
        else:
            self.delete_data('pd',params)
            #if self.check_data('pd', params):
            self.to_sql(df, name = 'pd', if_exists = 'append', index = False)

    def read_pd(self, sin, procset='proc1', calc='NONE', columns = ['*']):
        """get phase differences for a certain sin/procset pair"""

        if 'pd' in self.get_tables():

            sql = (f"""SELECT {', '.join(columns)}
                     FROM pd
                     WHERE procset=='%s'AND sin==%d AND calc=='%s'"""
                   % (procset, sin, calc))

            phase_diff = self.read_sql(sql).replace({None: np.nan})
            return phase_diff
        else:
            return pd.DataFrame()

    def write_curve(self, data, sin, rep, procset = 'proc1', wid = -1, xmid = 0):
        """write dispersion image data to database"""

        # %% table curve
        # table name
        tn = 'curve'

        # table column names
        columns = ['procset', 'wid', 'sin', 'rep', 'xmid', 'method', 'dc_mode', 'frequency', 'velocity', 'error']

        # table column types
        types = ['TEXT', 'INT', 'INT', 'INT', 'FLOAT', 'TEXT', 'INT', 'FLOAT', 'FLOAT', 'FLOAT']

        # create the table if it does not exist
        if tn not in self.get_tables():
            self._create_table(tn, columns, types)

        df = pd.DataFrame({'procset':procset,
                            'wid': wid,
                            'sin': sin,
                            'rep': rep,
                            'xmid': data['xmid'],
                            'method': data['method'],
                            'dc_mode': data['dc_mode'],
                            'frequency': data['f'],
                            'velocity': data['v'],
                            'error': data['err']})

        #params = {'sin': sin, 'rep': rep, 'procset': "'%s'" % procset, 'wid': wid, 'xmid': data['xmid']}
        #if params is None:
        params = {'procset': "'%s'" % procset, 'method': "'%s'" % data['method'], 'dc_mode': "%d" % data['dc_mode'],
                  'sin': sin, 'rep': rep, 'wid': wid, 'xmid': xmid}

        # append to table or replace if exists
        if self.check_data(tn,params):
            self.to_sql(df,name = tn, if_exists = 'append', index = False)
        else:
            self.delete_data(tn,params)
            self.to_sql(df, name = tn, if_exists = 'append', index = False)

    def read_curve(self, params):
        """get data from table FV for a certain wave-field transformation method"""

        if 'curve' in self.get_tables():

            sql = """SELECT *
                      FROM curve
                      WHERE """

            npar = len(params)
            for i, key in enumerate(params.keys()):

                if i < npar - 1:
                    sql += f"{key}=={params[key]} AND "
                else:
                    sql += f"{key}=={params[key]}"

            curve = self.read_sql(sql)
            return curve
        else:
            return pd.DataFrame()

