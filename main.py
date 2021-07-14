from typing import Optional, List

import pandas as pd
import numpy as np
import brightway2 as bw

SS_Columns = pd.Index([
    "from activity name",
    "from reference product",
    "from location",
    "from categories",
    "from database",
    "from key",
    "to activity name",
    "to reference product",
    "to location",
    "to categories",
    "to database",
    "to key",
],dtype='object')


class Superstructure():
    def __init__(self):
        self.dataframe = pd.DataFrame()
        self.scenario_difference_file = pd.DataFrame()

    def import_from_databases(self, databases:[str]):
        #TODO
        """given a list of database names create a superstructure """
        assert len(databases) >= 1
        assert len(databases) == len(set(databases))
        assert all(db in bw.databases for db in databases)
    def import_from_excel(self,path):
        self.dataframe = pd.read_excel(path)

    def create_superstructure(self):
        #TODO
        # In this function we create a superstructure format according to SS_Format.xlsx
        return 0

    def create_scenario_difference_file(self, scenarios: List[pd.DataFrame]):
        #TODO
        # in this function we create a scenario difference file according to the SDF_Format.xlsx
        if len(self.dataframe.columns) > len(SS_Columns)+1:
            print("removing duplicates")
            df = ss.dataframe
            for scenario in scenarios:
                self.get_subset(scenario)
                print("Getting values from %s"%scenario.columns[len(SS_Columns)])

            self.filter_scenarios()
            return(df)
        return False

    def get_subset(self,scenario):
        print(scenario.columns)

    def export_superstructure_to_excel(self):
        #TODO
        # in this function we export the superstructure dataframe to excel format

        return 0
    def export_scenario_difference_to_excel(self):
        #TODO
        # in this function we export the scenario diffrence file to an excel format
        self.scenario_difference_file.to_excel("sdf.xlsx")

    def export_superstructure_to_brightway(self):
        # in this function we export the superstructure dataframe to brightway
        column_list = list(self.dataframe.columns)
        versions_list = []
        for name in column_list:
            if "ecoinvent" in name:
                versions_list.append(name)
        selection_rule = lambda s1, s2: s1 if s1 == s2 else (s1 if np.isnan(s2) else (s2 if np.isnan(s1) else "!"))
        self.dataframe["superstructure"] = self.dataframe[versions_list[0]].combine(self.dataframe[versions_list[1]],
                                                                                    selection_rule)

    def filter_scenarios(self):
        # in this function we add the filter the entries with different values over multiple scenario's
        df = self.dataframe
       # df_subset = df[df.apply(lambda x: any(e != x[11] for e in x.iloc[12:14]), axis=0)]

        df1 = self.dataframe.stack().reset_index().drop(columns='ecoinvent_SSP2_2025').drop_duplicates()

        df1['col'] = df1.groupby('ecoinvent_SSP2_2020').cumcount()
        df1 = (df1.pivot(index='ecoinvent_SSP2_2020', columns='col', values=0).rename_axis(index=None, columns=None))

        return df

    def add_scenario(self, scenario):
        # in this function we add a scenario column to the dataframe, if it exists, else it gets added below.

        if self.compare_columns(scenario):
            self.dataframe = self.dataframe.merge(scenario, how = 'outer')
        else:
            print("The following column(s) are missing in the database: ",
                  SS_Columns.difference(scenario.columns).tolist())
            return False

    def add_multiple_scenario(self, scenarios: List[pd.DataFrame]):
        # in this function we add multiple scenarios from a dataframe list
        for scenario in scenarios:
            self.add_scenario(scenario)

    def compare_columns(self,df):
        if SS_Columns.intersection(df.columns).equals(SS_Columns):
            return True
        else:
            print("The following column(s) are missing in the database: ", SS_Columns.difference(df.columns).tolist())
            return False



path_to_excel = r'/Users/vosm4/PycharmProjects/AB_SS/Excel/SS_Example.xlsx'
ss = Superstructure()
ss.import_from_excel(path_to_excel)

#ss.dataframe = ss.filter_scenarios()
#print(ss.dataframe)
#print(ss.compare_columns())
#ss.compare_columns().to_excel("output.xlsx")
eco2025 = pd.read_excel(r'/Users/vosm4/PycharmProjects/AB_SS/Excel/SS_Example_2.xlsx')
eco2030 = pd.read_excel(r'/Users/vosm4/PycharmProjects/AB_SS/Excel/SS_Example_scenario_3.xlsx')
dflist = [eco2025,eco2030]
ss.add_multiple_scenario(dflist)
ss.filter_scenarios()
#test = ss.create_scenario_difference_file(dflist)
ss.export_scenario_difference_to_excel()
#print(ss.dataframe)