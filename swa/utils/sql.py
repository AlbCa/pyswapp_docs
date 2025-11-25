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

        self.database = database

    # %% Connection
    def get_connection(self):
        con = sqlite3.connect(self.database)
        con.create_aggregate("STDEV", 1, StdevFunc)
        return con

    def to_sql(self, df, name, if_exists='fail', **kwargs):
        """Write data stored in a DataFrame to a SQL database"""

        with self.get_connection() as con:
            df.to_sql(name=name, con=con, if_exists=if_exists, **kwargs)

    def read_sql(self, sql):
        """Write SQL query or table into DataFrame"""

        with self.get_connection() as con:
            return pd.read_sql(sql,con=con)

    # %% Table management
    def _create_table(self, name, columns, types):
        """Create a SQL table"""

        if len(columns) != len(types):
            raise ValueError(
                f"Number of column names and types do not match: "
                f"{len(columns)} != {len(types)}")

        def is_valid_identifier(identifier):
            return identifier.replace("_", "").isalnum()

        if not is_valid_identifier(name):
            raise ValueError(f"Invalid table name: {name}")

        for col in columns:
            if not is_valid_identifier(col):
                raise ValueError(f"Invalid column name: {col}")

        # Build column definitions
        column_defs = ", ".join(f"{col} {typ}" for col, typ in zip(columns, types))
        sql = f"CREATE TABLE {name} ({column_defs});"

        # Execute SQL
        with self.get_connection() as con:
            con.execute(sql)

    def _create_tables(self):
        """Create all database tables"""

        # AMPS table
        recs = self.get_table('recs')
        columns = ['procset', 'wid', 'sin', 'rep']
        types = ['TEXT', 'INT', 'INT', 'INT']
        amps_columns = [f"rin{i}" for i in recs.rin.iloc]
        amps_types = ['FLOAT'] * len(amps_columns)
        all_columns = columns + amps_columns
        all_types = types + amps_types

        self._create_table('amps', all_columns, all_types)

        # PAR table
        self._create_table('par',
                           ['procset', 'wid', 'sin', 'rep',
                            'npts', 'dt', 'delay', 'sampling_rate'],
                           ['TEXT', 'INT', 'INT', 'INT',
                            'INT', 'FLOAT', 'FLOAT', 'FLOAT'])

        # PID table
        self._create_table('pid',
                           ['procset', 'wid', 'sin', 'rep', 'rin'],
                           ['TEXT', 'INT', 'INT', 'INT', 'INT'])

        # FV table
        self._create_table(
            'FV',
            ['procset', 'wid', 'sin', 'rep', 'method',
             'velocity', 'wavenumber', 'f_id', 'f_value', 're', 'im'],
            ['TEXT', 'INT', 'INT', 'INT', 'TEXT',
             'FLOAT', 'FLOAT', 'INT', 'FLOAT', 'FLOAT', 'FLOAT']
        )

        # PD table
        columns = ['procset', 'calc', 'sin', 'rep', 'wid', 'fids', 'frequency']
        types = ['TEXT', 'TEXT', 'INT', 'INT', 'INT', 'INT', 'FLOAT']
        pd_columns = [f"pd{i}" for i in recs.rin.iloc[:-1]]
        pd_types = ['FLOAT'] * len(pd_columns)
        all_columns = columns + pd_columns
        all_types = types + pd_types
        self._create_table('pd', all_columns, all_types)

        # CURVE table
        self._create_table('curve',
                           ['procset', 'wid', 'sin', 'rep', 'xmid',
                            'method', 'dc_mode', 'frequency', 'velocity', 'error'],
                           ['TEXT', 'INT', 'INT', 'INT', 'FLOAT',
                            'TEXT', 'INT', 'FLOAT', 'FLOAT', 'FLOAT'])

        # FILTER table
        self._create_table('filter',
                           ['procset', 'wid', 'sin', 'rep','key','xp','yp','type'],
                           ['TEXT', 'INT', 'INT', 'INT', 'TEXT', 'FLOAT', 'FLOAT', 'TEXT'])

    def get_table(self,name):
        """Return a table form the database as DataFrame"""
        return self.read_sql("""SELECT * FROM %s""" % name)

    def drop_table(self, name):
        """Drop table"""

        with self.get_connection() as con:
            con.execute(f"""DROP TABLE IF EXISTS {name}""")

    def show_tables(self):
        """Print all table names in the database."""
        tables = self.get_tables()
        print("Tables in project: " + ", ".join(tables))

    def _fmt(self, value):
        """Helper to safely format values"""
        with self.get_connection() as con:
            return con.execute("SELECT quote(?)", (value,)).fetchone()[0]

    def check_data(self, table, params):
        """Check if entry in database"""

        if table not in self.get_tables():
            return pd.DataFrame().empty

        sql = """SELECT procset, sin, rep
                  FROM %s
                  WHERE """ % table

        npar = len(params)
        for i, key in enumerate(params.keys()):

            if i < npar - 1:
                sql += f"{key}=={params[key]} AND "
            else:
                sql += f"{key}=={params[key]}"

        df = self.read_sql(sql)

        return df.empty

    def delete_data(self, table, params):
        """delete entry from database"""

        with self.get_connection() as con:

            try:
                sql = """DELETE FROM %s WHERE """ % table
                npar = len(params)

                for i, key in enumerate(params.keys()):
                    if i < npar - 1:
                        sql += f"{key}=={params[key]} AND "
                    else:
                        sql += f"{key}=={params[key]}"
                con.execute(sql)

            except sqlite3.OperationalError:
                pass

    def get_tables(self):
        """Get all table names"""

        with self.get_connection() as con:
            table_names = con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            table_list = [name[0] for name in table_names]
            return table_list

    # %% Interaction with the geometry information
    # %% geometry information
    def read_geometry(self, geometry_file):
        """Read geometry CSV file and populate geom, shots, and recs tables"""

        # Read geometry file
        geom = pd.read_csv(geometry_file, delimiter=',', header=None,
                           names=['x', 'y', 'z', 'geophone', 'shots', 'first_geophone', 'num_geophones'])
        geom = geom.astype({'shots': str, 'first_geophone': str, 'num_geophones': str})
        geom.insert(0, 'station_id', np.arange(len(geom)) + 1)

        # Shots DataFrame
        shots = pd.DataFrame(geom.loc[geom.shots != '-1', ['station_id', 'shots']])
        shots['shots'] = shots['shots'].str.split(';')
        shots = shots.explode('shots')

        # Helper to append other columns
        def _append_shots_df(shots_df, geom_df, col_name):
            tmp = pd.DataFrame(geom_df.loc[geom_df.shots != '-1', [col_name]])
            tmp[col_name] = tmp[col_name].str.split(';')
            tmp = tmp.explode(col_name).astype(int)
            shots_df[col_name] = tmp
            return shots_df

        shots = _append_shots_df(shots, geom, 'first_geophone')
        shots = _append_shots_df(shots, geom, 'num_geophones')

        shots.insert(2, 'rep', shots.groupby(['station_id', 'first_geophone', 'num_geophones']).cumcount() + 1)
        shots.insert(1, 'sin', (shots.rep.values == 1).cumsum())

        # Geophone indices (receivers)
        recs = pd.DataFrame(geom[geom.geophone > 0]['station_id'])
        recs.insert(0, 'rin', np.arange(len(recs)) + 1)
        recs = recs.astype({'rin': int, 'station_id': int})

        # Create tables if not exists
        self._create_table('geom',
                           ['station_id', 'x', 'y', 'z', 'geophone', 'shots', 'first_geophone', 'num_geophones'],
                           ['INT', 'FLOAT', 'FLOAT', 'FLOAT', 'INT', 'INT', 'INT', 'INT'])
        self._create_table('shots', ['station_id', 'sin', 'rep', 'shots', 'first_geophone', 'num_geophones'],
                           ['INT', 'INT', 'INT', 'INT', 'INT', 'INT'])
        self._create_table('recs', ['rin', 'station_id'], ['INT', 'INT'])

        # Write to database
        self.to_sql(geom, 'geom', if_exists='replace')
        self.to_sql(shots, 'shots', if_exists='replace')
        self.to_sql(recs, 'recs', if_exists='replace')

        # create all tables
        self._create_tables()

    def get_geometry(self, sin, rep=1):
        """Return source/receiver coordinates for one source location and shot index"""

        if sin != '*':
            sql = f"""SELECT s.sin, s.rep, s.first_geophone fg, s.num_geophones ng, 
                      g.x sx, g.y sy, g.z sz
                      FROM geom g
                      INNER JOIN shots s ON s.station_id == g.station_id
                      WHERE s.rep=={rep} AND s.sin=={sin}"""
            sht = self.read_sql(sql)
            if len(sht) != 1:
                raise ValueError('Number of shots should be 1.')

            rec = pd.DataFrame(columns=['rin', 'rx', 'ry', 'rz'])
            for rin in range(sht.fg.item(), sht.fg.item() + sht.ng.item()):
                sql = f"""SELECT r.rin, g.x rx, g.y ry, g.z rz
                          FROM geom g
                          INNER JOIN recs r ON r.station_id == g.station_id
                          WHERE r.rin=={rin}"""
                rec = pd.concat([rec, self.read_sql(sql)])

        else:
            # Return all
            sql = """SELECT s.sin, s.rep, s.first_geophone fg, s.num_geophones ng, g.x sx, g.y sy, g.z sz
                     FROM geom g
                     INNER JOIN shots s ON s.station_id == g.station_id"""
            sht = self.read_sql(sql)
            rec = pd.DataFrame(columns=['rin', 'rx', 'ry', 'rz'])
            for j in range(len(sht)):
                for rin in range(sht.fg.iloc[j], sht.fg.iloc[j] + sht.ng.iloc[j]):
                    sql = f"""SELECT r.rin, g.x rx, g.y ry, g.z rz
                              FROM geom g
                              INNER JOIN recs r ON r.station_id == g.station_id
                              WHERE r.rin=={rin}"""
                    rec = pd.concat([rec, self.read_sql(sql)])
            rec.drop_duplicates(inplace=True, ignore_index=True)

        return sht.reset_index(drop=True), rec.reset_index(drop=True)

    def get_shotfile(self, sin, rep=1):
        """Return the name of one shot file"""
        sql = f"""SELECT s.shots
                  FROM shots s
                  WHERE s.rep=={rep} AND s.sin=={sin}"""
        return self.read_sql(sql)

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
        return self.read_sql(sql)['procset'].values

    def get_trafo_labels(self,procset, use_windows = False):

        if 'FV' in self.get_tables():

            if use_windows:
                sql = """SELECT DISTINCT method
                         FROM FV WHERE procset=='%s' AND wid != -1""" % procset
                labels = self.read_sql(sql)['method'].values
            else:
                sql = """SELECT DISTINCT method
                         FROM FV WHERE procset=='%s' AND wid == -1""" % procset
                labels = self.read_sql(sql)['method'].values
            return labels

        return []

    def duplicate_data(self,data, sin, rep, wid=-1):

        params = {'sin': sin, 'rep': rep, 'procset': "'%s'" % 'tmp', 'wid': wid}
        if self.check_data('amps', params):
            self.write_data(data, sin, rep, 'tmp', wid=wid)

    def write_data(self, data, sin, rep, procset, wid = -1):
        """write processed data to database"""

        # TABLE amps
        # table column names
        recs = self.get_table('recs')
        columns = ['procset', 'wid', 'sin', 'rep'] + [f"rin{i}" for i in recs.rin.iloc]

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

        # create DataFrame
        par = [procset, wid, sin, rep, cur_npts, cur_dt, cur_delay, cur_sampling_rate]
        par_df = pd.DataFrame([par],columns=columns)

        # TABLE pid
        # table column names
        columns = ['procset', 'wid', 'sin', 'rep', 'rin']

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
        else:
            if procset != 'raw':
                self.delete_data('amps',params)
                self.delete_data('par', params)
                self.delete_data('pid',params)

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

        sql = """SELECT s.sin, s.rep, s.first_geophone fg, s.num_geophones ng, g.x sx, g.y sy, g.z sz
                 FROM geom g
                 INNER JOIN shots s ON s.station_id == g.station_id
                 WHERE s.rep==%d AND s.sin==%d""" % (rep, sin)
        sht = self.read_sql(sql)

        sql = """SELECT procset, sin, rep, npts, dt, delay, sampling_rate
                 FROM par
                 WHERE procset=='%s' AND wid==%d AND sin==%d AND rep==%d""" % (procset, wid, sin, rep)
        par = self.read_sql(sql)

        # check if query was successful and select data
        if recs.empty or sht.empty or par.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        amp_cols = [f'rin{i}' for i in recs.rin]
        sql_amps = f"""
            SELECT {', '.join(amp_cols)}
            FROM amps
            WHERE procset=='%s' AND wid==%d AND sin==%d AND rep==%d""" % (procset, wid, sin,rep)

        amps = self.read_sql(sql_amps)
        return par, amps, recs, sht

    # %% FV data
    def write_FV(self, data, sin, rep, procset='proc1', wid=-1):
        """write dispersion image data to database"""

        cur_stream = data
        FV = cur_stream.dispersive_energy  # FV spectrum (vels, freq)
        freq = cur_stream.frequency  # frequency range
        cur_vel = cur_stream.velocity  # testing phase velocity
        cur_ks = cur_stream.wavenumber  # wavenumber
        method = cur_stream.trafo_type

        n_vel = len(cur_vel)
        n_freq = len(freq)

        rows = []
        for v in range(n_vel):
            for f in range(n_freq):
                rows.append({
                    'procset': procset,
                    'wid': wid,
                    'sin': sin,
                    'rep': rep,
                    'method': method,
                    'velocity': float(cur_vel[v]),
                    'wavenumber': float(cur_ks[v]),
                    'f_id': int(f),
                    'f_value': float(freq[f]),
                    're': float(FV[v, f].real),
                    'im': float(FV[v, f].imag),
                })

        df = pd.DataFrame(rows)

        params = {'sin': sin, 'rep': rep, 'procset': "'%s'" % procset, 'wid': wid, 'method': "'%s'" % method}
        if self.check_data('FV', params):
            self.to_sql(df, name='FV', if_exists='append', index=False)
        else:
            self.delete_data('FV', params)
            self.to_sql(df, name='FV', if_exists='append', index=False)

    def read_FV(self, sin, rep, procset='proc1', method='phaseshift', wid=-1):
        """get data from table FV for a certain wave-field transformation method"""

        if 'FV' not in self.get_tables():
            return None, None, None, None

        sql = f"""
                    SELECT * FROM FV
                    WHERE procset='{procset}'
                      AND wid={wid}
                      AND sin={sin}
                      AND rep={rep}
                      AND method='{method}'
                    ORDER BY velocity, f_id
                """

        df = self.read_sql(sql)
        if df.empty:
            return None, None, None, None

        velocities = df['velocity'].unique()
        freq_vals = df['f_value'].unique()

        n_vel = len(velocities)
        n_freq = len(freq_vals)

        # Reconstruct FV matrix
        FV = np.zeros((n_vel, n_freq), dtype=complex)

        for v_idx, vel in enumerate(velocities):
            block = df[df.velocity == vel]
            # sorted by f_id
            block = block.sort_values('f_id')
            FV[v_idx, :] = block['re'].values + 1j * block['im'].values

        wavenumbers = (
            df.groupby('velocity')['wavenumber']
            .first()
            .values
        )

        return velocities, wavenumbers, freq_vals, FV

    def get_wids(self, sin, rep, procset):
        """return the window ids for a sin/rep pair"""

        sql = ("""SELECT DISTINCT wid
                 FROM amps
                 WHERE procset=='%s' AND sin==%d AND rep==%d AND wid!=-1""" % (procset, sin, rep))

        df = self.read_sql(sql)
        return sorted(df["wid"].tolist()) if not df.empty else []

    def write_pd(self, df, sin, rep, procset = 'proc1'):
        """write phase differences to database"""

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

        # Static columns
        base_cols = ["procset", "calc", "sin", "rep", "wid", "fids", "frequency"]

        # Aggregated receiver columns
        pd_cols = [
            f"{by}(pd{rin}) AS pd{rin}"
            for rin in recs.rin.iloc[:-1]
        ]

        select_cols = ", ".join(base_cols + pd_cols)

        sql = f"""
            SELECT {select_cols}
            FROM pd
            WHERE procset = '{procset}' AND sin = {sin}
            GROUP BY fids
        """

        df = self.read_sql(sql).replace({None: np.nan})
        df["calc"] = by

        params = {
            "sin": sin,
            "procset": f"'{procset}'",
            "wid": -1,
            "calc": f"'{by}'"
        }

        # Insert or replace
        if self.check_data("pd", params):
            self.to_sql(df, name="pd", if_exists="append", index=False)
        else:
            self.delete_data("pd", params)
            self.to_sql(df, name="pd", if_exists="append", index=False)

    def read_pd(self, sin, procset='proc1', calc='NONE', columns = '*'):
        """get phase differences for a certain sin/procset pair"""

        if not isinstance(columns, list):
            columns = list(columns)

        sql = (f"""SELECT {', '.join(columns)}
                 FROM pd
                 WHERE procset=='%s'AND sin==%d AND calc=='%s'"""
               % (procset, sin, calc))

        phase_diff = self.read_sql(sql).replace({None: np.nan})
        return phase_diff

    def write_curve(self, data, sin, rep, procset = 'proc1', wid = -1, xmid = 0):
        """write dispersion curves to database"""

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
        if self.check_data('curve',params):
            self.to_sql(df,name = 'curve', if_exists = 'append', index = False)
        else:
            self.delete_data('curve',params)
            self.to_sql(df, name = 'curve', if_exists = 'append', index = False)

    def read_curve(self, params):
        """get data from table curve"""

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


    def write_filter(self, points, sin, rep, key = 't', procset = 'proc1', wid = -1, type = 'FK'):
        """write filter to data base"""

        x, y = zip(*sorted(points.items()))

        df = pd.DataFrame({'procset':procset,
                            'wid': wid,
                            'sin': sin,
                            'rep': rep,
                            'key': key,
                           'xp':x,
                           'yp':y,
                           'type':type})

        self.to_sql(df,name = 'filter', if_exists = 'append', index = False)

    def read_filter(self, params):
        """get data from table filter"""

        sql = """SELECT *
                  FROM filter
                  WHERE """

        npar = len(params)
        for i, key in enumerate(params.keys()):

            if i < npar - 1:
                sql += f"{key}=={params[key]} AND "
            else:
                sql += f"{key}=={params[key]}"

        filter = self.read_sql(sql)

        filter.sort_values(['key', 'xp'], ascending=[True, True],inplace=True)
        filter.reset_index(inplace = True, drop = True)

        return filter

