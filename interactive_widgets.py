from IPython.html import widgets
from IPython.html.widgets import interact
from IPython.display import display

subj_dd  = widgets.Dropdown(options=['']+db.get_subjects(), description='Subject ID')
modality = widgets.RadioButtons(options=['MEG','MR'], description='Modality', visible=True)
study_dd = widgets.Dropdown(options=['---'], description='Study date', visible=True)
series_dd = widgets.Dropdown(options=dict([['---','0']]), description='Series name', visible=True)
files_list = widgets.Textarea(description="Files", disabled=True, visible=True)

info = dict(subj_id='', modality='MEG', study='---', series=0)

def get_studies(subj_id, modality):
    if len(subj_id) > 0:
        # These need to be up-front, since study_dd and series_dd .options
        # get set below, WHICH TRIGGERS THEIR CALLBACKS!!
        info['subj_id'] = subj_id
        info['modality'] = modality

        studs = db.get_studies(subj_id, modality=modality, unique=False)
        if len(studs) > 0:
            if type(studs) is str:
                studs = [studs,]
            study_dd.options = ['---'] + studs
            series_dd.options = dict([['---','0']])
        else:
            study_dd.options = ['---',]

        files_list.value = ''
            
def get_series(study):
    if not study == '---':
        series_dict = db.get_series(info['subj_id'], study, info['modality'])
        series_dict.update({'---': '0'})
        series_dd.options = sorted(series_dict.items(), key=lambda t: t[1])
        info['study'] = study
    else:
        series_dd.options = {'---': '0'}
        files_list.value = ''

def get_files(series):
    if int(series) > 0:
        rawfiles = db.get_files(info['subj_id'], info['study'], 
                                info['modality'], series)
        files_list.value = "\n".join(rawfiles) if type(rawfiles) is list else ''
        info['series'] = int(series)
    else:
        files_list.value = ''

subj_i  = widgets.interactive(get_studies, subj_id=subj_dd, modality=modality)
study_i = widgets.interactive(get_series, study=study_dd)
series_i = widgets.interactive(get_files, series=series_dd)

def display_StormDB_access():
    display(subj_i)
    display(study_i)
    display(series_i)
    display(files_list)