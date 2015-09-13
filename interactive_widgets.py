from IPython.html import widgets
from IPython.html.widgets import interact
from IPython.display import display

class StormdbAccess():

    def __init__(self, db=None):
        self.db = db
        self.info = dict(subj_id='', modality='MEG', study='---', series=0)

        self.subj_dd  = widgets.Dropdown(options=['']+self.db.get_subjects(), description='Subject ID')
        self.modality = widgets.RadioButtons(options=['MEG','MR'], description='Modality', visible=True)
        self.study_dd = widgets.Dropdown(options=['---'], description='Study date', visible=True)
        self.series_dd = widgets.Dropdown(options=dict([['---','0']]), description='Series name', visible=True)
        self.files_list = widgets.Textarea(description="Files", disabled=True, visible=True)

        self.subj_i  = widgets.interactive(self.get_studies, subj_id=self.subj_dd, modality=self.modality)
        self.study_i = widgets.interactive(self.get_series, study=self.study_dd)
        self.series_i = widgets.interactive(self.get_files, series=self.series_dd)


    def get_studies(self, subj_id, modality):
        if len(subj_id) > 0:
            # These need to be up-front, since study_dd and series_dd .options
            # get set below, WHICH TRIGGERS THEIR CALLBACKS!!
            self.info['subj_id'] = subj_id
            self.info['modality'] = modality

            studs = self.db.get_studies(subj_id, modality=modality, unique=False)
            if len(studs) > 0:
                if type(studs) is str:
                    studs = [studs,]
                self.study_dd.options = ['---'] + studs
                self.series_dd.options = dict([['---','0']])
            else:
                self.study_dd.options = ['---',]

            self.files_list.value = ''

    def get_series(self, study):
        if not study == '---':
            series_dict = self.db.get_series(self.info['subj_id'], study, self.info['modality'])
            series_dict.update({'---': '0'})
            self.series_dd.options = sorted(series_dict.items(), key=lambda t: t[1])
            self.info['study'] = study
        else:
            self.series_dd.options = {'---': '0'}
            self.files_list.value = ''

    def get_files(self, series):
        if int(series) > 0:
            rawfiles = self.db.get_files(self.info['subj_id'], self.info['study'], 
                                    self.info['modality'], series)
            self.files_list.value = "\n".join(rawfiles) if type(rawfiles) is list else ''
            self.info['series'] = int(series)
        else:
            self.files_list.value = ''


    def display_StormDB_access(self):
        display(self.subj_i)
        display(self.study_i)
        display(self.series_i)
        display(self.files_list)