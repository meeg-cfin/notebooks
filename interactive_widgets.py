from IPython.html import widgets
from IPython.html.widgets import interact
from IPython.display import display

class FakeDatabaseQuery():
    def __init__(self):
        raise NotImplementedError('Would be usefull for debugging, though...')

class InteractiveQuery():

    def __init__(self, query=None):
        if query is None:
            self.query = FakeDatabaseQuery()
        else:
            self.query = query
            
        self.info = dict(subj_id=None, modality=None, study=None, 
                         series=None, series_name=None, files=None)

        self.subj_dd  = widgets.Dropdown(options=['']+self.query.get_subjects(), description='Subject ID')
        self.modality = widgets.RadioButtons(options=['MEG','MR'], description='Modality', visible=True)
        self.study_dd = widgets.Dropdown(options=['---'], description='Study date', visible=True)
        self.series_dd = widgets.Dropdown(options=dict([['---','0']]), description='Series name', visible=True)
        self.files_list = widgets.Textarea(description="Files", disabled=True, visible=True)

        self.subj_i  = widgets.interactive(self._get_studies, subj_id=self.subj_dd, modality=self.modality)
        self.study_i = widgets.interactive(self._get_series, study=self.study_dd)
        self.series_i = widgets.interactive(self._get_files, series=self.series_dd)


    def _get_studies(self, subj_id, modality):
        if len(subj_id) > 0:
            # These need to be up-front, since study_dd and series_dd .options
            # get set below, WHICH TRIGGERS THEIR CALLBACKS!!
            self.info['subj_id'] = subj_id
            self.info['modality'] = modality

            studs = self.query.get_studies(subj_id, modality=modality, unique=False)
            if len(studs) > 0:
                if type(studs) is str:
                    studs = [studs,]
                self.study_dd.options = ['---'] + studs
                self.series_dd.options = dict([['---','0']])
            else:
                self.study_dd.options = ['---',]

            self.files_list.value = ''

    def _get_series(self, study):
        if not study == '---':
            series_dict = self.query.get_series(self.info['subj_id'], study, self.info['modality'])
            series_dict.update({'---': '0'})
            self.series_dd.options = sorted(series_dict.items(), key=lambda t: t[1])
            self.info['study'] = study
        else:
            self.series_dd.options = {'---': '0'}
            self.files_list.value = ''

    def _get_files(self, series):
        if int(series) > 0:
            rawfiles = self.query.get_files(self.info['subj_id'], self.info['study'], 
                                    self.info['modality'], series)
            self.files_list.value = "\n".join(rawfiles) if type(rawfiles) is list else ''
            self.info['series'] = int(series)
            self.info['files'] = rawfiles
            # Some extra spice here: get the series name too
            inverted_mapping = dict((v,k) for k, v in dict(self.series_dd.options).items())
            self.info['series_name'] = inverted_mapping[series]
        else:
            self.files_list.value = ''


    def display(self):
        display(self.subj_i)
        display(self.study_i)
        display(self.series_i)
        display(self.files_list)
        
        
