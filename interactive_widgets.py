from IPython.html import widgets
from IPython.html.widgets import interact
from IPython.display import display
import warnings

from mne.io import Raw


class FakeDatabaseQuery():
    def __init__(self):
        raise NotImplementedError('Would be usefull for debugging, though...')


class InteractiveQuery():

    def __init__(self, query=None):
        if query is None:
            self.query = FakeDatabaseQuery()
        else:
            self.query = query

        self.info = dict(proj_code=query.proj_code,
                         subj_id=None, modality=None, study=None,
                         series=None, series_name=None, files=None)

        self.subj_dd = widgets.Dropdown(
                        options=['']+self.query.get_subjects(),
                        description='Subject ID')
        self.modality = widgets.RadioButtons(
                        options=['MEG', 'MR'], description='Modality',
                        visible=True)
        self.study_dd = widgets.Dropdown(
                        options=['---'], description='Study date',
                        visible=True)
        self.series_dd = widgets.Dropdown(
                        options=dict([['---', '0']]),
                        description='Series name', visible=True)
        self.files_list = widgets.Textarea(
                        description="Files", disabled=True, visible=True)

        self.subj_i = widgets.interactive(
                        self._get_studies, subj_id=self.subj_dd,
                        modality=self.modality)
        self.study_i = widgets.interactive(
                        self._get_series, study=self.study_dd)
        self.series_i = widgets.interactive(
                        self._get_files, series=self.series_dd)

    def _get_studies(self, subj_id, modality):
        if len(subj_id) > 0:
            # These need to be up-front, since study_dd and series_dd .options
            # get set below, WHICH TRIGGERS THEIR CALLBACKS!!
            self.info['subj_id'] = subj_id
            self.info['modality'] = modality

            studs = self.query.get_studies(
                            subj_id, modality=modality, unique=False)
            if len(studs) > 0:
                if type(studs) is str:
                    studs = [studs, ]
                self.study_dd.options = ['---'] + studs
                self.series_dd.options = dict([['---', '0']])
            else:
                self.study_dd.options = ['---', ]

            self.files_list.value = ''

    def _get_series(self, study):
        if not study == '---':
            series_dict = self.query.get_series(
                    self.info['subj_id'], study, self.info['modality'])
            series_dict.update({'---': '0'})
            self.series_dd.options = sorted(
                    series_dict.items(), key=lambda t: t[1])
            self.info['study'] = study
        else:
            self.series_dd.options = {'---': '0'}
            self.files_list.value = ''

    def _get_files(self, series):
        if int(series) > 0:
            rawfiles = self.query.get_files(
                    self.info['subj_id'], self.info['study'],
                    self.info['modality'], series)
            self.files_list.value = "\n".join(rawfiles) \
                                    if type(rawfiles) is list else ''
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


class InteractiveMaxfilter():

    def __init__(self, input_info, mf_object):

        self.output_dir = '/projects/' + input_info['proj_code'] + '/scratch/maxfilter'
        self.info = input_info
        self.mf = mf_object
        self.raw_file = None

        self.initialise_mf_params()
        # self.show_cmd = widgets.Textarea(description="Command", disabled=True, visible=True)

        self.buildcmdbut = widgets.Button(description='Build command')
        self.buildcmdbut.on_click(self.on_buildcmdbut_clicked)

        self.bccont = widgets.Box(description='Bad chans')
        self.autobad  = widgets.Dropdown(options=['on','off'], description='Autobad')
        self.badchans = widgets.Textarea(description="Bad channels")
        self.bccont.children = [self.autobad, self.badchans]

        self.ssscont = widgets.Box(description='(t)SSS')
        self.st = widgets.Checkbox(description='Use temporal SSS (tSSS)')
        self.stcorr = widgets.FloatSlider(value=0.96, min=0.5, max=0.99, step=0.01,
                                     description='Correlation limit')
        self.stbuflen = widgets.IntSlider(value=16, min=4, max=30, description='Buffer length')
        self.sssframe = widgets.Dropdown(options=['head','device'], description='SSS frame')
        self.ssscont.children = [self.sssframe, self.st, self.stcorr, self.stbuflen]

        self.mccont = widgets.HBox(description='Movement compensation')
        self.mc = widgets.Checkbox(description='Active')
        self.mctarget = widgets.Dropdown(options=['initial'] + self.info['files'],
                                    description='Compensate to')
        self.mccont.children = [self.mc, self.mctarget]

        self.hscont = widgets.Box(description='Head shape (fit)')

        self.fitbut = widgets.Button(description='Fit sphere to head shape')
        self.fitylim = widgets.FloatRangeSlider(value=(-120., 120.), min=-120., max=120., step=2.,
                                          description="y-limit of head shape points")
        self.fitzlim = widgets.FloatRangeSlider(value=(-60., 120.), min=-60., max=120., step=2.,
                                          description="z-limit of head shape points")
        self.fitorigin = widgets.Text(value='', description='Origin', width=250)
        self.hscont.children = [self.fitbut, self.fitylim, self.fitzlim, self.fitorigin]

        # self. = widgets.HBox(description='')
        self.mc = widgets.Checkbox(description='Active')
        self.mctarget = widgets.Dropdown(
                    options={'initial': '', 'default': 'default'},
                    description='Compensate to')
        self.mccont.children = [self.mc, self.mctarget]
        # Event handlers
        self.sssframe.on_trait_change(self.on_frame_changed)
        self.fitbut.on_click(self.on_fitbut_clicked)


        self.accordion = widgets.Accordion(children=[self.bccont, self.ssscont,
                                                     self.mccont, self.hscont])
        self.accordion.set_title(0, 'Bad channels')
        self.accordion.set_title(1, '(t)SSS parameters')
        self.accordion.set_title(2, 'Movement compensation')
        self.accordion.set_title(3, 'Head origin')

    def on_frame_changed(self):
        self.fitorigin.value = 'None'

    def on_fitbut_clicked(self, b):

        if self.raw_file is None:
            # To temporarily suppress the stupid MNE warning about
            # "wrong" file name suffixes (irritating!) while reading Raw
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.raw_file = Raw(self.info['files'][0], verbose=False)

        limits_y_m = tuple(val/1000. for val in self.fitylim.value)
        limits_z_m = tuple(val/1000. for val in self.fitzlim.value)
        r, o_head, o_dev = \
            self.mf.fit_sphere_to_headshape(self.raw_file.info,
                                            ylim=limits_y_m,
                                            zlim=limits_z_m)

        if self.sssframe.value == 'head':
            self.fitorigin.value = "{:.1f} {:.1f} {:.1f}".format(*o_head)
        elif self.sssframe.value == 'device':
            self.fitorigin.value = "{:.1f} {:.1f} {:.1f}".format(*o_dev)

    def on_buildcmdbut_clicked(self, b):
        self.collect_mf_params()
        self.mf.build_maxfilter_cmd('foo','bar', **self.mf_params)
        print(self.mf.cmd)

    def collect_mf_params(self):
        self.mf_params['origin'] = self.fitorigin.value
        self.mf_params['frame'] = self.sssframe.value
        self.mf_params['bad'] = self.badchans.value
        self.mf_params['autobad'] = self.autobad.value
        self.mf_params['st'] = self.ssscont.value
        self.mf_params['st_buflen'] = self.stbuflen.value
        self.mf_params['st_corr'] = self.stcorr.value
        self.mf_params['movecomp'] = self.mc.value
        self.mf_params['mv_trans'] = if self.mctarget.value

    def initialise_mf_params(self):
        self.mf_params = dict(origin='0 0 40', frame='head',
                              bad=None, autobad='off', skip=None, force=False,
                              st=False, st_buflen=16.0, st_corr=0.96,
                              mv_trans=None, movecomp=False, mv_headpos=False,
                              mv_hp=None, mv_hpistep=None, mv_hpisubt=None,
                              hpicons=True, linefreq=None, cal=None, ctc=None,
                              mx_args='', maxfilter_bin='maxfilter',
                              logfile=None, n_threads=None)

    def display(self):
        display(self.accordion)
        display(self.buildcmdbut)
